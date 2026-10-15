"""L6 -- feature selection must be blind to the rows it does not own.

``Boruta_FeatEng.py:57-113`` and ``Feature_selection.py:47-109`` fitted the variance filter,
the iterative VIF loop and Boruta on all 896 training rows *before* any cross-validation. The
selected set had therefore seen every fold it was later scored on, and the 22-feature contract
that REPORT.md reports against is itself a fitted object with no held-out data behind it.

The sentinel does not read the selector; it runs it twice and compares. That is the only form
of the check that survives card #24 choosing a different algorithm, and it is why the detector
takes a callable rather than a record: what matters is not which method selects, it is what the
method was allowed to look at.

Card #71.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest
from hydms.qa import LeakDetected, assert_selection_ignores_holdout

pd = pytest.importorskip("pandas", reason="pandas is not installed in this interpreter")

TRAIN = ["a", "b", "c", "d"]
HELD_OUT = ["e", "f"]


@pytest.fixture()
def frame() -> pd.DataFrame:
    """Three candidate features. Only `f1` survives on the training rows alone.

    `f2` sits exactly on the threshold across the whole frame, held there by its held-out
    values. A selector that reads all six rows is one nudge from a different answer, and the
    detector's perturbation is that nudge -- which is the whole mechanism by which fitting
    selection outside the folds changes what gets selected.
    """
    return pd.DataFrame(
        {
            "f1": [3.0, 3.0, 3.0, 3.0, 0.0, 0.0],
            "f2": [0.0, 0.0, 0.0, 0.0, 2.0, 4.0],
            "f3": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        },
        index=[*TRAIN, *HELD_OUT],
    )


def select_on_everything(frame: Any) -> Sequence[str]:
    """`Boruta_FeatEng.py:57` -- filter the whole frame, then cross-validate on the result."""
    return tuple(column for column in frame.columns if frame[column].mean() > 1.0)


def select_on_the_training_rows(frame: Any) -> Sequence[str]:
    """What card #24 must do: the selector sees the training fold and nothing else."""
    training = frame.loc[TRAIN]
    return tuple(column for column in training.columns if training[column].mean() > 1.0)


def test_l6_selection_fitted_on_the_whole_frame_is_red(frame: pd.DataFrame) -> None:
    with pytest.raises(LeakDetected) as exc:
        assert_selection_ignores_holdout(select_on_everything, frame, holdout=HELD_OUT)
    message = str(exc.value)
    assert "leak L6" in message
    assert "'f2'" in message, "the message must name the feature that moved"
    assert "gained" in message


def test_l6_selection_fitted_on_the_training_rows_is_green(frame: pd.DataFrame) -> None:
    """The two selectors differ in one line. Nothing else can explain the difference."""
    assert_selection_ignores_holdout(select_on_the_training_rows, frame, holdout=HELD_OUT)


def test_l6_the_two_selectors_agree_before_the_perturbation(frame: pd.DataFrame) -> None:
    """Without this, the sentinel could pass because the leaky selector is simply different.

    Both return `('f1',)` on the untouched frame. The leaky one changes its mind only when the
    held-out rows change, which is the property the detector measures and the only difference
    between them.
    """
    assert tuple(select_on_everything(frame)) == ("f1",)
    assert tuple(select_on_the_training_rows(frame)) == ("f1",)


def test_l6_a_reordering_of_the_selected_set_is_also_red(frame: pd.DataFrame) -> None:
    """Feature order is the column order of the design matrix, so it is part of the contract.

    Card #19's 22-feature contract and `docs/LIBRARY-APIS.md` on CatBoost both turn on position
    identifying a column. A selector that returns the same features in an order derived from
    held-out data has leaked into something that matters.
    """

    reference_total = 6.0  # the held-out target total, in the units the columns are measured in

    def order_by_holdout(inner: Any) -> Sequence[str]:
        """Same two features every time, ranked by a statistic of the held-out rows."""
        held = inner.loc[HELD_OUT]
        return tuple(
            sorted(("f1", "f2"), key=lambda column: abs(held[column].sum() - reference_total))
        )

    with pytest.raises(LeakDetected, match="different order"):
        assert_selection_ignores_holdout(order_by_holdout, frame, holdout=HELD_OUT)


def test_l6_the_perturbation_is_seeded_and_reproducible(frame: pd.DataFrame) -> None:
    """A failure a reviewer cannot reproduce is a failure that gets dismissed."""
    messages = set()
    for _ in range(3):
        with pytest.raises(LeakDetected) as exc:
            assert_selection_ignores_holdout(
                select_on_everything, frame, holdout=HELD_OUT, seed=7
            )
        messages.add(str(exc.value))
    assert len(messages) == 1


def test_l6_the_frame_the_selector_saw_is_not_mutated(frame: pd.DataFrame) -> None:
    """The detector perturbs a copy. A detector that damages its input is used once."""
    before = frame.copy(deep=True)
    assert_selection_ignores_holdout(select_on_the_training_rows, frame, holdout=HELD_OUT)
    assert frame.equals(before)


# --------------------------------------------------------------------------------------
# Misuse is not a finding
# --------------------------------------------------------------------------------------


def test_a_frame_with_no_numeric_column_is_a_caller_error() -> None:
    """Nothing could be perturbed, so the check would pass whatever the selector does."""
    formulae = pd.DataFrame({"Composition": ["LaNi5", "TiFe", "Mg2Ni"]}, index=["a", "b", "c"])
    with pytest.raises(ValueError, match="no numeric column"):
        assert_selection_ignores_holdout(lambda f: tuple(f.columns), formulae, holdout=["c"])
