"""L3 and L10 -- held-out data is read once, at the end, and is never written.

**L3** ``CleanLab.py:90``, applied through ``:96-97`` to validation and test:
``managed_df['target'] = np.where(mask, y_pred, y)``. Ground truth is replaced by the model's
own prediction, so every replaced point has a residual of exactly zero by construction.
``docs/FREEZE.md`` calls this out separately from the rest: it is inert today only because
nothing reads its output, and card #14 as originally written would have wired it in.

**L10** the recovered ``Ashghal/Outliers_Management.py:60-72``: validation and test *feature*
values clipped using their own residuals. Same defect, other side of the table -- which is why
one detector covers both, run once on ``y`` and once on ``X``.

Neither leak is in the PRD. Both were found by the Phase H audit.

Card #71.
"""

from __future__ import annotations

import pytest
from hydms.qa import LeakDetected, assert_holdout_unchanged

pd = pytest.importorskip("pandas", reason="pandas is not installed in this interpreter")

ROWS = ["a", "b", "c", "d", "e", "f"]
HELD_OUT = ["e", "f"]


@pytest.fixture()
def targets() -> pd.Series:
    """Six measured capacities, the last two held out."""
    return pd.Series([1.5, 2.0, 2.5, 3.0, 3.5, 4.0], index=ROWS, name="H2_W% (max)")


@pytest.fixture()
def features() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "avg_atomic_mass": [58.7, 47.9, 24.3, 91.2, 88.9, 140.1],
            "temperature(K)": [298.0, 303.0, 573.0, 323.0, 298.0, 598.0],
        },
        index=ROWS,
    )


# --------------------------------------------------------------------------------------
# L3 -- targets
# --------------------------------------------------------------------------------------


def test_l3_overwriting_a_held_out_target_is_red(targets: pd.Series) -> None:
    """`CleanLab.py:90`, reintroduced: the model's prediction written over the measurement."""
    after = targets.copy()
    after.loc["e"] = 3.52
    with pytest.raises(LeakDetected) as exc:
        assert_holdout_unchanged(targets, after, holdout=HELD_OUT)
    message = str(exc.value)
    assert "leaks L3 and L10" in message
    assert "'e'" in message
    assert "1 of 2" in message


def test_l3_dropping_a_training_row_is_green(targets: pd.Series) -> None:
    """Screening may drop or reweight training rows freely. That is what it is for."""
    assert_holdout_unchanged(targets, targets.drop(index=["b"]), holdout=HELD_OUT)


def test_l3_dropping_a_held_out_row_is_red(targets: pd.Series) -> None:
    """A row screened out of the test set is a test set the model chose the shape of."""
    with pytest.raises(LeakDetected, match="disappeared"):
        assert_holdout_unchanged(targets, targets.drop(index=["f"]), holdout=HELD_OUT)


def test_l3_a_change_far_below_reporting_precision_is_still_red(targets: pd.Series) -> None:
    """"Byte-identical" is the assertion, not "close enough".

    REPORT.md quotes capacities to two decimals. A rewrite in the twelfth would never show up
    in a metric and would still mean a held-out label came from the model.
    """
    after = targets.copy()
    after.loc["f"] = 4.0 + 1e-12
    with pytest.raises(LeakDetected, match="rewritten"):
        assert_holdout_unchanged(targets, after, holdout=HELD_OUT)


def test_l3_reordering_the_frame_is_not_a_finding(targets: pd.Series) -> None:
    """Row order is not data. The comparison is by label, or every shuffle would be a leak."""
    assert_holdout_unchanged(targets, targets.loc[list(reversed(ROWS))], holdout=HELD_OUT)


def test_l3_every_held_out_row_is_checked_not_just_the_first(targets: pd.Series) -> None:
    after = targets.copy()
    after.loc["f"] = 3.99
    with pytest.raises(LeakDetected, match="'f'"):
        assert_holdout_unchanged(targets, after, holdout=HELD_OUT)


# --------------------------------------------------------------------------------------
# L10 -- features
# --------------------------------------------------------------------------------------


def test_l10_clipping_a_held_out_feature_value_is_red(features: pd.DataFrame) -> None:
    after = features.copy()
    after.loc["f", "avg_atomic_mass"] = 100.0
    with pytest.raises(LeakDetected, match="held-out feature rows"):
        assert_holdout_unchanged(features, after, holdout=HELD_OUT, what="held-out feature rows")


def test_l10_clipping_a_training_feature_value_is_green(features: pd.DataFrame) -> None:
    after = features.copy()
    after.loc["c", "avg_atomic_mass"] = 100.0
    assert_holdout_unchanged(features, after, holdout=HELD_OUT, what="held-out feature rows")


def test_l10_a_change_in_any_column_is_caught(features: pd.DataFrame) -> None:
    """Temperature is a feature. Winsorising it on the test rows is the same leak."""
    after = features.copy()
    after.loc["f", "temperature(K)"] = 500.0
    with pytest.raises(LeakDetected, match="'f'"):
        assert_holdout_unchanged(features, after, holdout=HELD_OUT, what="held-out feature rows")


# --------------------------------------------------------------------------------------
# Misuse is not a finding
# --------------------------------------------------------------------------------------


def test_an_empty_holdout_is_a_caller_error(targets: pd.Series) -> None:
    """The vacuous pass is the exact shape of the leak, so it must not be reachable quietly."""
    with pytest.raises(ValueError, match="empty holdout"):
        assert_holdout_unchanged(targets, targets, holdout=[])


def test_a_duplicated_row_label_is_a_caller_error(targets: pd.Series) -> None:
    """Two rows under one label compare a different number of rows on each side.

    Worth failing on in its own right: it is also the shape leak L9 produces downstream, where
    a positional merge attaches one composition's features to another's label.
    """
    doubled = pd.concat([targets, targets.loc[["f"]]])
    with pytest.raises(ValueError, match="duplicate index labels"):
        assert_holdout_unchanged(doubled, doubled, holdout=HELD_OUT)
