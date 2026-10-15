"""L13 -- a column that is not a feature is still not disposable.

``extract_features_cbfv.py:19-21``::

    object_cols = df_raw.select_dtypes(include='object').columns
    cols_to_drop = [col for col in object_cols if col != 'Composition']
    df_raw = df_raw.drop(columns=cols_to_drop)

Three lines, and ``Alloy_class`` stops existing. Every leak above this one makes a number
optimistic; this one deletes a **question** -- leave-one-alloy-class-out validation (AC-6),
the PRD's most important validation number, has no trace anywhere in the repository because
after this line there is nothing to fold on.

It is also the quietest of the thirteen. Nothing downstream fails, no metric moves, and the
line is locally reasonable: CBFV wants numbers, and those columns are not numbers.

Two properties, because losing a class has two shapes and only one of them is visible:

  - the **column** disappears, which is the archival defect, and
  - a **row's label** disappears while the column survives, which is what a join on the wrong
    key does. That is the tie to card #87: ``Ce1Mg12`` is ``MIC`` in the file and ``Mg12Ce1``
    is ``Mg``, so a class re-joined on the raw formula string gives one material two answers
    and a fold that holds out ``Mg`` holds out half of it.

The sentinel's subject is ``hydms.descriptors.featurize``. Card #87 wrote this sentinel
because it owns the key the class is re-joined on; card #20 created the subject on 2026-09-04,
which turned the sentinel ``unwired`` -- red, on purpose -- and card #12 wired it the same day.
The ``live`` hook now runs the real featuriser over 1,278 of the 1,279 curated rows and joins
its matrix back with :func:`hydms.data.metadata.with_features`, so what is asserted below in
miniature is asserted upstairs against the pipeline.

The miniatures stay. They are what proves the detector can still go red: a hook that runs on
clean data proves the pipeline is clean *today*, and says nothing about whether the check would
notice if it stopped being.

Card #71 (the suite), card #87 (this sentinel), card #12 (the hook).
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the L13 reproductions are pandas frames")

import pandas as pd  # noqa: E402  -- only importable once the skip above has passed
from hydms.qa import LeakDetected, assert_metadata_survives, audit, for_leak  # noqa: E402

ROWS = ("row-0", "row-1", "row-2", "row-3")


@pytest.fixture()
def raw() -> pd.DataFrame:
    """Four rows shaped like the raw file, two of them one material under two spellings."""
    return pd.DataFrame(
        {
            "Composition": ["Ce1Mg12", "Mg12Ce1", "LaNi5", "TiFe"],
            "Alloy_class": ["MIC", "Mg", "AB5", "AB"],
            "Dataset": ["HydPark", "HydPark", "Extracted", "Extracted"],
            "H2_W% (max)": [6.0, 6.0, 1.4, 1.9],
        },
        index=list(ROWS),
    )


def archival_featurisation(frame: pd.DataFrame) -> pd.DataFrame:
    """`extract_features_cbfv.py:19-21`, transcribed, then one feature computed."""
    object_columns = frame.select_dtypes(include="object").columns
    kept = frame.drop(columns=[name for name in object_columns if name != "Composition"])
    kept["n_elements"] = [2.0, 2.0, 2.0, 2.0]
    return kept


def honest_featurisation(frame: pd.DataFrame) -> pd.DataFrame:
    """The same stage, adding its features beside the metadata instead of instead of it."""
    featurised = frame.copy(deep=True)
    featurised["n_elements"] = [2.0, 2.0, 2.0, 2.0]
    return featurised


# --------------------------------------------------------------------------------------
# The column
# --------------------------------------------------------------------------------------


def test_dropping_every_object_column_is_red(raw: pd.DataFrame) -> None:
    with pytest.raises(LeakDetected) as failure:
        assert_metadata_survives(
            raw, archival_featurisation(raw), columns=("Alloy_class", "Dataset")
        )

    message = str(failure.value)
    assert "leak L13" in message
    assert "'Alloy_class'" in message and "'Dataset'" in message
    assert "extract_features_cbfv.py:19-21" in message


def test_carrying_the_metadata_through_is_green(raw: pd.DataFrame) -> None:
    assert_metadata_survives(
        raw, honest_featurisation(raw), columns=("Alloy_class", "Dataset")
    )


def test_the_features_the_stage_adds_are_not_a_finding(raw: pd.DataFrame) -> None:
    """A featuriser exists to add columns. Only losing one is the leak."""
    after = honest_featurisation(raw)
    assert "n_elements" in after.columns
    assert_metadata_survives(raw, after, columns=("Alloy_class",))


# --------------------------------------------------------------------------------------
# The row
# --------------------------------------------------------------------------------------


def test_a_row_that_does_not_survive_featurisation_is_red(raw: pd.DataFrame) -> None:
    """CBFV drops a composition it cannot parse into a `skipped` list nobody reads."""
    after = honest_featurisation(raw).drop(index=["row-2"])

    with pytest.raises(LeakDetected, match="did not survive the stage"):
        assert_metadata_survives(raw, after, columns=("Alloy_class",))


def test_a_relabelled_row_is_red(raw: pd.DataFrame) -> None:
    """The shape a re-join on the wrong key produces: the column is there, the answer moved."""
    after = honest_featurisation(raw)
    after.loc["row-0", "Alloy_class"] = "Mg"

    with pytest.raises(LeakDetected) as failure:
        assert_metadata_survives(raw, after, columns=("Alloy_class",))
    assert "'row-0'" in str(failure.value), "the message must name the row, not just count it"


def test_one_material_written_two_ways_keeps_two_labels_until_the_key_is_used(
    raw: pd.DataFrame,
) -> None:
    """Why card #87 owns this sentinel.

    `Ce1Mg12` and `Mg12Ce1` are one composition carrying two class labels in the file. A
    stage that re-joins the class on the raw formula string preserves both -- it passes this
    detector, correctly, because nothing was lost -- and still leaves a fold that holds out
    `Mg` holding out half a material. The class survives; the *identity* is what has to be
    canonical, which is `hydms.data.canonical.group_keys`.
    """
    assert_metadata_survives(raw, honest_featurisation(raw), columns=("Alloy_class",))
    assert raw.loc["row-0", "Alloy_class"] != raw.loc["row-1", "Alloy_class"]


# --------------------------------------------------------------------------------------
# Misuse is a ValueError, never a leak
# --------------------------------------------------------------------------------------


def test_checking_no_columns_is_a_caller_error(raw: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="no columns to check"):
        assert_metadata_survives(raw, raw, columns=())


def test_checking_a_column_the_stage_never_received_is_a_caller_error(
    raw: pd.DataFrame,
) -> None:
    """A vacuous pass here would report safety the detector never established."""
    with pytest.raises(ValueError, match="not in the frame entering the stage"):
        assert_metadata_survives(raw, honest_featurisation(raw), columns=("Citation",))


# --------------------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------------------


def test_l13_is_wired_to_the_real_featuriser() -> None:
    """The sentinel is pointed at the module the drop would come back to, and it is green.

    This test previously asserted `pending`, and its docstring said so: card #87 wrote the
    sentinel, card #20 created `hydms.descriptors.featurize`, which made it `unwired` and HG-1
    red, and card #12 gave it the `live` hook. The subject was never re-aimed to make the
    build green -- that would have been the leak, wearing the sentinel's name.
    """
    sentinel = for_leak("L13")
    assert sentinel is not None
    assert sentinel.subject == "hydms.descriptors.featurize"
    assert sentinel.detector == "hydms.qa.detectors.assert_metadata_survives"
    assert sentinel.live is not None, "an unwired sentinel guards its subject in name only"

    row = next(entry for entry in audit() if entry.leak == "L13")
    assert row.status == "green", row.detail
    assert row.owed_by == 12


def test_l13_goes_red_when_the_real_path_stops_carrying_the_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seen red, and against the real subject rather than a copy of it.

    `extract_features_cbfv.py:19-21` put back into the one function the hook actually calls. A
    `live` hook that silently exercised a local reimplementation would look identical to one
    that works, so this is the only thing that distinguishes them.

    The run is cached -- `audit()` fires on every gate invocation -- so the cache is cleared on
    both sides. A poisoned frame left behind would make every later audit in this process report
    a leak that is not there.
    """
    from hydms.qa import audit
    from hydms.qa.sentinels import _featurisation_run, for_leak

    def archival(record: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        object_columns = record.select_dtypes(include="object").columns
        kept = record.drop(columns=[n for n in object_columns if n != "Composition"])
        return pd.concat([kept, features], axis=1)

    monkeypatch.setattr("hydms.data.metadata.with_features", archival)
    _featurisation_run.cache_clear()
    try:
        sentinel = for_leak("L13")
        assert sentinel is not None and sentinel.live is not None
        with pytest.raises(LeakDetected):
            sentinel.live()

        row = next(entry for entry in audit() if entry.leak == "L13")
        assert row.status == "broken"
        assert "hydms.descriptors.featurize has leak L13" in row.detail
    finally:
        _featurisation_run.cache_clear()


def test_the_class_arrives_for_every_row_the_real_featuriser_accepts() -> None:
    """The whole path, written the way a caller writes it, over the real file.

    Not the hook -- the hook is what `audit()` runs, and `test_l13_is_wired_to_the_real_
    featuriser` above asserts its verdict. This is the same journey spelled out here so the
    numbers are readable: `with_metadata` in, `featurize` across, `with_features` back, and
    the class on the other side for every row.

    `featurize` refuses rather than dropping, so a row cannot be lost silently; what has to be
    proved is that the class **arrives**. 1,278 of the 1,279 curated rows are featurisable
    without `dev_Gordy_electonegativity` -- the one feature the citable Oliynyk edition cannot
    build for 21 of the dataset's 55 elements -- and the row that is not is `Eu1Ni5`, named by
    the contract's verdict rather than by a list in a test.
    """
    from hydms.config import load as load_config
    from hydms.data.load import load_hydride_data, parse_formula
    from hydms.data.metadata import metadata_columns, with_features, with_metadata
    from hydms.descriptors.contract import CONTRACT, FeatureContract
    from hydms.descriptors.featurize import featurize

    names = load_config().columns
    record = with_metadata(load_hydride_data())
    contract = FeatureContract.from_names(
        [n for n in CONTRACT.names if n != "dev_Gordy_electonegativity"]
    )
    keep = [
        label
        for label, formula in record[names.formula].items()
        if contract.computability(parse_formula(formula)).complete
    ]
    assert len(keep) == 1278 and len(record) == 1279
    refused = record.loc[[label for label in record.index if label not in set(keep)]]
    assert list(refused[names.formula]) == ["Eu1Ni5"]

    before = record.loc[keep]
    after = with_features(
        before, featurize(before[names.formula], before[names.temperature], contract=contract)
    )

    assert list(after.index) == list(before.index)
    for name in metadata_columns():
        assert name in after.columns, f"{name} did not survive featurisation"
    assert after["Alloy_class"].equals(before["Alloy_class"])
    assert set(contract.names) <= set(after.columns)
