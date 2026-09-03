"""L1 -- the split protocol, and the leak it exists to remove. Card #13.

Four questions:

  - **Is it the same protocol?** Stratification, rare-stratum merging and both
    ``StratifiedShuffleSplit`` calls are ported unchanged from ``split_data.py:63-135``; only
    the unit changes, from the formula string to the canonical composition. The row counts
    move as a result, and the size test asserts that they moved rather than that they match.
  - **Is L8 gone?** No canonical composition in two splits -- checked with the same detector
    gate HG-1 runs, over the real 1279 rows, plus the six collision pairs the audit found.
  - **Is it reproducible?** Same seed, same split; different seed, different split; and the
    row order of the input does not enter into it.
  - **The failure path.** A missing column, and a stratum that cannot be divided.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the data layer is pandas frames end to end")
pytest.importorskip("sklearn", reason="the split protocol is scikit-learn's")

import pandas as pd  # noqa: E402  -- only importable once the skips above have passed
from hydms.config import Split as SplitSettings  # noqa: E402
from hydms.config import load as load_config  # noqa: E402
from hydms.data.canonical import group_keys  # noqa: E402
from hydms.data.load import load_hydride_data  # noqa: E402
from hydms.data.splits import (  # noqa: E402
    SPLIT_NAMES,
    SplitError,
    assign_splits,
    split_summary,
    stratify,
)
from hydms.qa import assert_disjoint_groups  # noqa: E402

# Measured on the real data during card #13. The published counts are what the *raw-string*
# grouping produced; these are what the canonical key produces, and the difference is the
# 34 formula strings that turned out to be duplicate materials.
GROUPED_ROWS = (893, 131, 255)
PUBLISHED_ROWS = (896, 136, 247)


@pytest.fixture(scope="module")
def hydride() -> pd.DataFrame:
    """The curated dataset through card #9's loader. Read once; nothing here mutates it."""
    return load_hydride_data()


@pytest.fixture(scope="module")
def split(hydride: pd.DataFrame) -> pd.Series:
    return assign_splits(hydride)


@pytest.fixture(scope="module")
def keys(hydride: pd.DataFrame) -> pd.Series:
    return group_keys(hydride)


# --------------------------------------------------------------------------------------
# Shape
# --------------------------------------------------------------------------------------


def test_every_row_is_assigned_exactly_one_of_three_splits(hydride, split) -> None:
    assert len(split) == len(hydride) == 1279
    assert split.index.equals(hydride.index)
    assert set(split.unique()) == set(SPLIT_NAMES)
    assert split.name == "split"


def test_the_sizes_moved_off_the_published_ones_and_that_is_the_fix(hydride, split, keys) -> None:
    """896/136/247 was produced by grouping on the formula string. 1149 strings are 1115
    compositions, so the split has 34 fewer units and *cannot* reproduce those counts --
    matching exactly would mean the key had changed nothing."""
    table = split_summary(split, keys)
    sizes = tuple(int(table.loc[name, "rows"]) for name in SPLIT_NAMES)
    assert sizes == GROUPED_ROWS
    assert sizes != PUBLISHED_ROWS
    assert sum(sizes) == 1279
    assert int(table["compositions"].sum()) == 1115


def test_the_fractions_still_land_where_pipeline_yaml_asks(split, keys) -> None:
    rules = load_config().split
    table = split_summary(split, keys)
    assert float(table.loc["test", "fraction"]) == pytest.approx(rules.test_fraction, abs=0.01)
    assert float(table.loc["val", "fraction"]) == pytest.approx(rules.val_fraction, abs=0.01)


# --------------------------------------------------------------------------------------
# L8
# --------------------------------------------------------------------------------------


def test_no_canonical_composition_appears_in_two_splits(split, keys) -> None:
    """The property the archival assertion could not see. Same detector as gate HG-1."""
    assert_disjoint_groups({name: keys[split == name] for name in SPLIT_NAMES})


def test_the_archival_assertion_is_also_green_because_this_one_is_stronger(
    hydride, split
) -> None:
    """Grouping on the composition implies grouping on the string, never the other way round.
    Asserted so that the relationship between the two checks is on record rather than
    assumed: `split_data.py:126-129` passing says nothing, and it still passes here."""
    assert_disjoint_groups(
        {name: hydride.loc[split == name, "Composition"] for name in SPLIT_NAMES},
        key_name="formula string",
    )


def test_the_six_measured_collision_pairs_land_on_one_side(
    hydride, split, known_collisions
) -> None:
    """The regression fixture from the audit: `Ce1Mg12` sat in test while `Mg12Ce1` sat in
    validation. Two by element order, one by scale, two by whitespace, one by both."""
    for left, right in known_collisions:
        here = set(split[hydride["Composition"] == left])
        there = set(split[hydride["Composition"] == right])
        assert here and there, f"{left!r} or {right!r} is not in the dataset"
        assert here == there, (
            f"{left!r} is in {sorted(here)} and {right!r} in {sorted(there)}; they are the "
            f"same material and this is leak L8"
        )


def test_the_four_repeats_canonicalisation_created_share_a_split(hydride, split, keys) -> None:
    """Distinct (composition, temperature) pairs fall from 1272 to 1268 (#87): four pairs are
    one material measured twice at one temperature, made distinct only by spelling. Grouping
    places both rows together for free -- and neither row is dropped, because they are
    independent measurements."""
    table = pd.DataFrame(
        {
            "key": keys,
            "T": hydride["temperature(K)"],
            "split": split,
            "formula": hydride["Composition"],
        }
    )
    repeats = table[table.duplicated(subset=["key", "T"], keep=False)]
    made_by_key = repeats.groupby(["key", "T"]).filter(lambda g: len(set(g["formula"])) > 1)
    assert made_by_key.groupby(["key", "T"]).ngroups == 4
    for _, group in made_by_key.groupby(["key", "T"]):
        assert len(set(group["split"])) == 1
    assert len(table) == 1279


# --------------------------------------------------------------------------------------
# Reproducibility
# --------------------------------------------------------------------------------------


def test_the_same_seed_reproduces_the_same_split(hydride, split) -> None:
    assert assign_splits(hydride).equals(split)


def test_a_different_seed_produces_a_different_split(hydride, split) -> None:
    assert not assign_splits(hydride, seed=7).equals(split)


def test_the_seed_comes_from_config_not_from_a_literal(hydride, split) -> None:
    assert assign_splits(hydride, seed=load_config().seed).equals(split)


def test_the_row_order_of_the_input_does_not_change_anybodys_split(hydride, split) -> None:
    """The decision is made over groups, and `groupby` sorts, so the shuffle depends on the
    keys and the seed alone. The same invariance L9's merge has, for the same reason."""
    shuffled = hydride.sample(frac=1.0, random_state=1)
    reassigned = assign_splits(shuffled)
    assert reassigned.sort_index().equals(split.sort_index())


# --------------------------------------------------------------------------------------
# Stratification
# --------------------------------------------------------------------------------------


def test_every_stratum_is_large_enough_to_divide(hydride) -> None:
    rules = load_config().split
    strata = stratify(hydride)
    assert len(strata) == 1115
    assert int(strata.value_counts().min()) >= rules.min_stratum_size
    assert strata.nunique() == 23


def test_a_stratum_that_cannot_be_divided_refuses_rather_than_splitting_badly(hydride) -> None:
    rules = load_config().split
    impossible = SplitSettings(
        test_fraction=rules.test_fraction,
        val_fraction=rules.val_fraction,
        target_bins=rules.target_bins,
        temperature_bins=rules.temperature_bins,
        min_stratum_size=2000,
    )
    with pytest.raises(SplitError, match="fewer than 2000"):
        stratify(hydride, settings=impossible)


# --------------------------------------------------------------------------------------
# The failure path
# --------------------------------------------------------------------------------------


def test_a_missing_stratification_column_is_named(hydride) -> None:
    with pytest.raises(SplitError, match="temperature"):
        assign_splits(hydride.drop(columns=["temperature(K)"]))


def test_a_missing_target_is_named(hydride) -> None:
    with pytest.raises(SplitError, match="H2_W"):
        assign_splits(hydride.drop(columns=["H2_W% (max)"]))


def test_the_summary_reports_rows_and_compositions_separately(split, keys) -> None:
    table = split_summary(split, keys)
    assert list(table.index) == list(SPLIT_NAMES)
    assert int(table["rows"].sum()) == 1279
    assert (table["compositions"] < table["rows"]).all(), "a split with one row per material"
