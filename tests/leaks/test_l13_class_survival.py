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

The sentinel's subject is ``hydms.descriptors.featurize``, which does not exist yet. Card #87
wrote this sentinel because it owns the key the class is re-joined on; card #12 carries the
class through featurisation and must give the sentinel its ``live`` hook when it does. Until
then :func:`hydms.qa.audit` reports L13 ``pending`` and HG-1 stays short of green.

Card #71 (the suite), card #87 (this sentinel).
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


def test_l13_is_guarded_and_waits_on_the_featuriser() -> None:
    """The sentinel exists; its subject does not. That is `pending`, not `deferred`.

    Card #87 gave `Alloy_class` a composition to be re-joined on and wrote this sentinel;
    card #12 carries the class through featurisation, and the moment
    `hydms.descriptors.featurize` exists HG-1 goes red until #12 wires the `live` hook.
    """
    sentinel = for_leak("L13")
    assert sentinel is not None
    assert sentinel.subject == "hydms.descriptors.featurize"
    assert sentinel.detector == "hydms.qa.detectors.assert_metadata_survives"

    row = next(entry for entry in audit() if entry.leak == "L13")
    assert row.status == "pending"
    assert row.owed_by == 12
