"""L1 -- the keyed merge that replaces the positional concat. Card #10.

Four questions, and they are different:

  - **Alignment.** Reordering an input changes nothing. This is the property the archival
    ``pd.concat(axis=1)`` does not have, and ``test_reordered_input_still_aligns`` is the
    card's named runnable check.
  - **Coverage.** A key uncovered on either side raises with the keys listed. A spine row
    with no features is a featuriser that skipped a composition; a block row nothing asked
    for is a block built from different data.
  - **Shape.** The spine's rows, order and index survive the merge exactly. The guard that
    makes that true is block-key uniqueness, and the real dataset needs it: seven
    ``(Composition, temperature(K))`` pairs appear twice, so a block keyed that way and
    built row-wise would take 1279 rows to 1293.
  - **Collisions.** Two featurisers contributing the same column name raise.
    ``merge_datasets.py:49`` kept the first and discarded the rest in silence.

``docs/QA-PROTOCOL.md`` section 4.1: delete a line of the implementation in your head and
something here must go red. Each refusal is tested twice -- once that it fires, once that
its message names the offender, because a merge failure over 1279 rows is unreadable
otherwise.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the merge is pandas frames end to end")

import pandas as pd  # noqa: E402  -- only importable once the skip above has passed
from hydms.data.load import load_hydride_data, parse_formula  # noqa: E402
from hydms.data.merge import FeatureBlock, MergeError, merge_features  # noqa: E402

COMPOSITIONS = ["LaNi5", "TiFe", "Mg2Ni", "ZrV2"]


@pytest.fixture()
def spine() -> pd.DataFrame:
    """Five measurement rows over four compositions -- LaNi5 measured at two temperatures.

    The repeat is the point. A spine row is a *measurement*, not a material, so the join
    from a per-composition block is one-to-many and a merge that assumed one-to-one would
    pass on a fixture without one.
    """
    return pd.DataFrame(
        {
            "Composition": ["LaNi5", "TiFe", "Mg2Ni", "LaNi5", "ZrV2"],
            "temperature(K)": [298, 313, 573, 373, 298],
            "H2_W% (max)": [1.4, 1.9, 7.6, 1.3, 2.0],
        }
    )


@pytest.fixture()
def oliynyk() -> pd.DataFrame:
    """A per-composition descriptor block, keyed by its index."""
    return pd.DataFrame(
        {"oliynyk_0": [10.0, 20.0, 30.0, 40.0]},
        index=pd.Index(COMPOSITIONS, name="Composition"),
    )


@pytest.fixture()
def jarvis() -> pd.DataFrame:
    """A second block, so column order and collisions across blocks can be checked."""
    return pd.DataFrame(
        {"jarvis_0": [0.1, 0.2, 0.3, 0.4]},
        index=pd.Index(COMPOSITIONS, name="Composition"),
    )


def block(name: str, frame: pd.DataFrame) -> FeatureBlock:
    return FeatureBlock(name=name, frame=frame, key=("Composition",))


# --------------------------------------------------------------------------------------
# Alignment -- the card's runnable check
# --------------------------------------------------------------------------------------


def test_reordered_input_still_aligns(spine: pd.DataFrame, oliynyk: pd.DataFrame) -> None:
    """The card's named check: a deliberately reordered input must not change the answer.

    Note what is *not* asserted: that reordering raises. A keyed merge is supposed to
    survive a reordering -- joining by key is what makes row order irrelevant. The defect
    is producing a different answer and saying nothing, which is what the positional concat
    two tests below actually does.
    """
    expected = merge_features(spine, [block("oliynyk", oliynyk)])

    reordered = oliynyk.loc[["ZrV2", "Mg2Ni", "LaNi5", "TiFe"]]
    assert merge_features(spine, [block("oliynyk", reordered)]).equals(expected)

    reversed_spine = spine.iloc[::-1]
    from_reversed = merge_features(reversed_spine, [block("oliynyk", reordered)])
    assert from_reversed.sort_index().equals(expected)


def test_the_positional_concat_puts_features_on_the_wrong_composition(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """Name the damage in the units of the problem, not just the detection.

    ``merge_datasets.py:46``. With the block in a different order, LaNi5's 1.4 wt% ends up
    beside TiFe's descriptor and nothing raises. This is the failure the whole module exists
    to make impossible.
    """
    reordered = oliynyk.loc[["TiFe", "LaNi5", "Mg2Ni", "ZrV2"]]

    damaged = pd.concat(
        [spine.reset_index(drop=True), reordered.reset_index(drop=True)], axis=1
    )
    assert damaged.loc[0, "Composition"] == "LaNi5"
    assert damaged.loc[0, "oliynyk_0"] == 20.0  # ...which is TiFe's

    intact = merge_features(spine, [block("oliynyk", reordered)])
    assert intact.loc[0, "oliynyk_0"] == 10.0


# --------------------------------------------------------------------------------------
# Shape
# --------------------------------------------------------------------------------------


def test_the_spine_keeps_its_rows_order_index_and_column_order(
    spine: pd.DataFrame, oliynyk: pd.DataFrame, jarvis: pd.DataFrame
) -> None:
    merged = merge_features(spine, [block("oliynyk", oliynyk), block("jarvis", jarvis)])

    assert len(merged) == len(spine)
    assert merged.index.equals(spine.index)
    assert list(merged.columns) == [*spine.columns, "oliynyk_0", "jarvis_0"]
    assert merged[list(spine.columns)].equals(spine)


def test_one_composition_measured_twice_receives_the_same_features(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """The one-to-many half: LaNi5 at 298 K and at 373 K are two rows, one chemistry."""
    merged = merge_features(spine, [block("oliynyk", oliynyk)])
    lani5 = merged[merged["Composition"] == "LaNi5"]

    assert len(lani5) == 2
    assert set(lani5["temperature(K)"]) == {298, 373}
    assert list(lani5["oliynyk_0"]) == [10.0, 10.0]


def test_a_repeated_block_key_raises_rather_than_multiplying_rows(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """The guard the real data demands -- see the real-dataset test at the bottom.

    Without it the join is many-to-many for the repeated key and the spine silently grows,
    which means those measurements are counted twice in every fold and every metric after.
    """
    doubled = pd.concat([oliynyk, oliynyk.loc[["TiFe"]]])

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [block("oliynyk", doubled)])
    assert "repeated key" in str(exc.value)
    assert "'TiFe'" in str(exc.value)


def test_a_duplicated_spine_label_raises(spine: pd.DataFrame, oliynyk: pd.DataFrame) -> None:
    """The spine's label is a row's identity here, so a repeated one makes coverage vague."""
    ambiguous = pd.concat([spine, spine.iloc[:1]])

    with pytest.raises(MergeError) as exc:
        merge_features(ambiguous, [block("oliynyk", oliynyk)])
    assert "duplicated index label" in str(exc.value)
    assert "reset_index(drop=True)" in str(exc.value)


# --------------------------------------------------------------------------------------
# Coverage -- both directions
# --------------------------------------------------------------------------------------


def test_a_composition_the_block_never_featurised_raises_and_names_it(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """The L9 scenario. The archival concat pads the column with NaN and shifts nothing."""
    thinned = oliynyk.drop(index="Mg2Ni")

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [block("oliynyk", thinned)])
    message = str(exc.value)
    assert "'Mg2Ni'" in message
    assert "leak L9" in message


def test_a_block_row_the_spine_never_asked_for_raises_and_names_it(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """The reverse: a block built from a different dataset, or a stale copy of this one."""
    extra = pd.concat(
        [oliynyk, pd.DataFrame({"oliynyk_0": [50.0]}, index=pd.Index(["TiCr2"], name="Composition"))]
    )

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [block("oliynyk", extra)])
    message = str(exc.value)
    assert "'TiCr2'" in message
    assert "never asked for" in message


def test_an_inner_join_would_have_passed_both_of_those_silently(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """Why coverage is asserted rather than left to the join's own semantics.

    ``how='inner'`` drops the uncovered rows and reports nothing; ``how='left'`` fills them
    with NaN and reports nothing. Both are a smaller dataset, or a column of holes, that no
    downstream stage can distinguish from the truth.
    """
    thinned = oliynyk.drop(index="Mg2Ni")

    inner = spine.join(thinned, on="Composition", how="inner")
    assert len(inner) == 4, "a row vanished and pandas said nothing"

    left = spine.join(thinned, on="Composition", how="left")
    assert len(left) == 5
    assert left["oliynyk_0"].isna().sum() == 1


# --------------------------------------------------------------------------------------
# Collisions
# --------------------------------------------------------------------------------------


def test_two_blocks_contributing_the_same_column_name_raise(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """``merge_datasets.py:49`` kept whichever arrived first and discarded the rest."""
    twin = oliynyk.copy()

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [block("oliynyk", oliynyk), block("jarvis", twin)])
    message = str(exc.value)
    assert "'oliynyk_0'" in message
    assert "merge_datasets.py:49" in message


def test_a_block_column_shadowing_a_spine_column_raises(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """Including the target: a block that overwrote ``H2_W% (max)`` would be catastrophic."""
    shadowing = oliynyk.rename(columns={"oliynyk_0": "H2_W% (max)"})

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [block("oliynyk", shadowing)])
    assert "'H2_W% (max)'" in str(exc.value)


def test_the_key_column_itself_is_not_a_collision(spine: pd.DataFrame) -> None:
    """A block that carries its key as a column is the normal case, not a clash."""
    as_column = pd.DataFrame({"Composition": COMPOSITIONS, "oliynyk_0": [10.0, 20.0, 30.0, 40.0]})

    merged = merge_features(spine, [block("oliynyk", as_column)])
    assert list(merged.columns).count("Composition") == 1


# --------------------------------------------------------------------------------------
# How a block is addressed
# --------------------------------------------------------------------------------------


def test_the_key_may_be_a_column_or_the_index(spine: pd.DataFrame, oliynyk: pd.DataFrame) -> None:
    """A featuriser returns the key as a column, a groupby returns it as an index.

    Forcing one on the caller only moves the reshaping outside this module, where nothing
    checks that it was done right.
    """
    from_index = merge_features(spine, [block("oliynyk", oliynyk)])
    from_column = merge_features(spine, [block("oliynyk", oliynyk.reset_index())])
    assert from_index.equals(from_column)


def test_a_bare_string_key_is_read_as_one_column_not_as_its_characters(
    spine: pd.DataFrame, oliynyk: pd.DataFrame
) -> None:
    """``key=("Composition")`` is a missing comma away from a string. It must still work."""
    named = FeatureBlock(name="oliynyk", frame=oliynyk, key="Composition")
    assert named.key == ("Composition",)
    assert merge_features(spine, [named]).equals(merge_features(spine, [block("o", oliynyk)]))


def test_a_key_split_between_columns_and_the_index_raises(spine: pd.DataFrame) -> None:
    """Half in each is a reshaping mistake, and guessing which half was meant hides it."""
    half = pd.DataFrame(
        {"temperature(K)": [298, 313, 573, 298], "x": [1.0, 2.0, 3.0, 4.0]},
        index=pd.Index(COMPOSITIONS, name="Composition"),
    )

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [FeatureBlock("half", half, key=("Composition", "temperature(K)"))])
    assert "entirely columns or exactly the index" in str(exc.value)


def test_a_key_the_spine_does_not_have_raises(spine: pd.DataFrame, oliynyk: pd.DataFrame) -> None:
    renamed = oliynyk.rename_axis(index="canonical_composition")

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [FeatureBlock("o", renamed, key=("canonical_composition",))])
    assert "the spine has no column" in str(exc.value)


def test_a_block_keyed_on_row_labels_joins_on_labels_not_position(spine: pd.DataFrame) -> None:
    """``key=None``: one block row per spine row, addressed by the spine's own index.

    The shape a per-measurement stage produces. Shuffled, it must still land correctly --
    which is exactly what ``reset_index(drop=True)`` before a ``concat`` destroys.
    """
    per_row = pd.DataFrame({"pressure_atm": [1.0, 2.0, 3.0, 4.0, 5.0]}, index=spine.index)
    shuffled = per_row.loc[[3, 0, 4, 1, 2]]

    merged = merge_features(spine, [FeatureBlock("per-row", shuffled)])
    assert list(merged["pressure_atm"]) == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_a_row_labelled_block_with_a_missing_label_raises(spine: pd.DataFrame) -> None:
    per_row = pd.DataFrame({"pressure_atm": [1.0, 2.0, 3.0, 4.0]}, index=[0, 1, 2, 3])

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [FeatureBlock("per-row", per_row)])
    assert "no row in block 'per-row'" in str(exc.value)


def test_a_compound_key_joins_on_every_level(spine: pd.DataFrame) -> None:
    """A temperature-dependent block is legitimate -- if its key is unique within it."""
    conditioned = pd.DataFrame(
        {
            "Composition": ["LaNi5", "TiFe", "Mg2Ni", "LaNi5", "ZrV2"],
            "temperature(K)": [298, 313, 573, 373, 298],
            "plateau": [2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )

    merged = merge_features(
        spine, [FeatureBlock("pct", conditioned, key=("Composition", "temperature(K)"))]
    )
    assert list(merged["plateau"]) == [2.0, 3.0, 4.0, 5.0, 6.0]


# --------------------------------------------------------------------------------------
# Nulls, and misuse
# --------------------------------------------------------------------------------------


def test_a_null_block_key_raises(spine: pd.DataFrame, oliynyk: pd.DataFrame) -> None:
    holed = oliynyk.rename(index={"Mg2Ni": None})

    with pytest.raises(MergeError) as exc:
        merge_features(spine, [block("oliynyk", holed)])
    assert "null key value" in str(exc.value)


def test_a_null_spine_key_raises(spine: pd.DataFrame, oliynyk: pd.DataFrame) -> None:
    holed = spine.copy()
    holed.loc[2, "Composition"] = None

    with pytest.raises(MergeError) as exc:
        merge_features(holed, [block("oliynyk", oliynyk)])
    assert "null key value" in str(exc.value)


def test_a_null_inside_a_compound_key_is_seen(spine: pd.DataFrame) -> None:
    """``MultiIndex.isna()`` reads its values as tuples, and a tuple holding a NaN is not
    itself null. The compound key has to be asked level by level or this passes silently."""
    conditioned = pd.DataFrame(
        {
            "Composition": ["LaNi5", "TiFe", "Mg2Ni", "LaNi5", "ZrV2"],
            "temperature(K)": [298, 313, None, 373, 298],
            "plateau": [2.0, 3.0, 4.0, 5.0, 6.0],
        }
    )

    with pytest.raises(MergeError) as exc:
        merge_features(
            spine, [FeatureBlock("pct", conditioned, key=("Composition", "temperature(K)"))]
        )
    assert "null key value" in str(exc.value)


def test_merging_no_blocks_is_a_caller_error(spine: pd.DataFrame) -> None:
    with pytest.raises(MergeError, match="no blocks"):
        merge_features(spine, [])


def test_an_empty_key_is_a_caller_error(oliynyk: pd.DataFrame) -> None:
    with pytest.raises(MergeError, match="empty key"):
        FeatureBlock(name="oliynyk", frame=oliynyk, key=())


# --------------------------------------------------------------------------------------
# The real dataset
# --------------------------------------------------------------------------------------


@pytest.fixture()
def real_spine(raw_data_path: object) -> pd.DataFrame:
    """``hydride_data.csv`` through card #9's loader: 1279 measurement rows."""
    return load_hydride_data()


@pytest.fixture()
def real_block(real_spine: pd.DataFrame) -> pd.DataFrame:
    """One row per distinct formula string -- the shape every descriptor block has.

    Every selected feature is a composition statistic or the temperature (PRD section 2.3),
    so a descriptor block is per-composition and the join onto the measurement table is
    one-to-many: 1149 block rows, 1279 spine rows.
    """
    formulae = list(dict.fromkeys(real_spine["Composition"]))
    counts = [float(len(parse_formula(formula))) for formula in formulae]
    return pd.DataFrame({"n_elements": counts}, index=pd.Index(formulae, name="Composition"))


def test_the_real_dataset_joins_one_to_many_without_changing_its_row_count(
    real_spine: pd.DataFrame, real_block: pd.DataFrame
) -> None:
    assert len(real_spine) == 1279
    assert len(real_block) == 1149

    merged = merge_features(real_spine, [block("elements", real_block)])
    assert len(merged) == 1279
    assert merged.index.equals(real_spine.index)
    assert merged["n_elements"].notna().all()


def test_formula_and_temperature_is_not_a_unique_key_on_the_real_spine(
    real_spine: pd.DataFrame,
) -> None:
    """Card #10's own ``## Done when`` names a key the data does not support.

    "Merge joins on formula (and temperature where the row is a measurement)" reads as if
    ``(Composition, temperature(K))`` identified a spine row. It does not: 1279 rows carry
    1272 distinct pairs. Six of the seven repeats are independent replicates with different
    targets and different citations, and belong in the data; the seventh -- ``La0.9Ce0.1Ni5``
    at 373 K, rows 687 and 694 -- is byte-identical across all six columns, and is boxed on
    #14, which is the stage entitled to drop a row.
    """
    keys = real_spine[["Composition", "temperature(K)"]]
    repeated = keys[keys.duplicated(keep=False)]

    assert len(keys.drop_duplicates()) == 1272
    assert len(repeated) == 14
    assert len(repeated.drop_duplicates()) == 7
    assert int(real_spine.duplicated(keep=False).sum()) == 2


def test_a_block_keyed_on_formula_and_temperature_is_refused_not_inflated(
    real_spine: pd.DataFrame,
) -> None:
    """What the refusal above is worth, measured: the merge would grow by exactly 14 rows.

    Those seven measurements would then be counted twice in every fold, every metric and
    every conformal calibration downstream -- silently, because the table still looks like
    a table.
    """
    row_wise = real_spine[["Composition", "temperature(K)"]].copy()
    row_wise["fake_descriptor"] = 1.0

    inflated = real_spine.merge(row_wise, on=["Composition", "temperature(K)"], how="left")
    assert len(inflated) == 1293

    with pytest.raises(MergeError) as exc:
        merge_features(
            real_spine,
            [FeatureBlock("row-wise", row_wise, key=("Composition", "temperature(K)"))],
        )
    assert "7 repeated key value(s)" in str(exc.value)
