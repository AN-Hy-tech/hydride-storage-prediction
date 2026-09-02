"""L1 and L5 -- the rows that stop training may not be the rows that score it.

**L1** ``Catboostmodel.py:604-606``: ``final_model.fit(combined_pool, eval_set=test_pool, ...)``.
The test set chose the stopping iteration and was then reported as held out at ``:684-686``,
under a plot legend reading "Test RMSE" at ``:612``.

**L5** ``Catboostmodel.py:576-582`` and ``:654-658``: every cross-validation fold early-stopped
on the fold it was scored on, so no fold's score is out-of-sample either.

One detector covers both, because they are one defect at two scopes: whatever chooses the
stopping iteration must be disjoint from whatever the resulting model is reported against.

Card #71.
"""

from __future__ import annotations

import pytest
from hydms.qa import LeakDetected, assert_early_stopping_is_honest

TRAIN = tuple(f"train-{i}" for i in range(6))
VAL = ("val-0", "val-1")
TEST = ("test-0", "test-1", "test-2")


# --------------------------------------------------------------------------------------
# L1 -- the final fit
# --------------------------------------------------------------------------------------


def test_l1_the_test_pool_as_eval_set_is_red() -> None:
    """The archival call, reintroduced. This is the demonstration section 5 requires."""
    with pytest.raises(LeakDetected) as exc:
        assert_early_stopping_is_honest(
            eval_rows=TEST, scored_rows=TEST, use_best_model=True, where="final fit"
        )
    message = str(exc.value)
    assert "leaks L1 and L5" in message
    assert "3 of 3 scored rows" in message, "the message must say how much of the score leaked"
    assert "'test-0'" in message, "and name the rows, or the next person re-runs the job to find them"


def test_l1_the_validation_split_as_eval_set_is_green() -> None:
    """The corrected call differs in one argument, so nothing else can explain the pass."""
    assert_early_stopping_is_honest(
        eval_rows=VAL, scored_rows=TEST, use_best_model=True, where="final fit"
    )


def test_l1_a_partial_overlap_is_still_red() -> None:
    """Half the test set is not half a leak. Card #26 must pass the validation split, whole."""
    with pytest.raises(LeakDetected, match="1 of 3 scored rows"):
        assert_early_stopping_is_honest(
            eval_rows=(*VAL, "test-1"),
            scored_rows=TEST,
            use_best_model=True,
            where="final fit",
        )


def test_l1_an_empty_eval_set_under_use_best_model_is_red() -> None:
    """CatBoost raises this at fit time; asserting it here moves the failure before the fit.

    It matters because it is the mechanical guard the runbook relies on (S4, card #26): the
    only ways to satisfy `use_best_model=True` are a real eval set or a leak, and the archival
    code took the second.
    """
    with pytest.raises(LeakDetected, match="empty eval_set"):
        assert_early_stopping_is_honest(
            eval_rows=(), scored_rows=TEST, use_best_model=True, where="final fit"
        )


def test_l1_an_empty_eval_set_without_use_best_model_is_not_this_leak() -> None:
    """Fitting to a fixed iteration count needs no eval set and steals nothing."""
    assert_early_stopping_is_honest(
        eval_rows=(), scored_rows=TEST, use_best_model=False, where="fixed-iteration fit"
    )


# --------------------------------------------------------------------------------------
# L5 -- the folds
# --------------------------------------------------------------------------------------


def test_l5_a_fold_that_early_stops_on_itself_is_red() -> None:
    fold = TRAIN[4:]
    with pytest.raises(LeakDetected, match="outer fold 3"):
        assert_early_stopping_is_honest(
            eval_rows=fold, scored_rows=fold, use_best_model=True, where="outer fold 3"
        )


def test_l5_a_fold_that_early_stops_on_an_inner_slice_is_green() -> None:
    assert_early_stopping_is_honest(
        eval_rows=TRAIN[2:4], scored_rows=TRAIN[4:], use_best_model=True, where="outer fold 3"
    )


def test_l5_one_bad_fold_among_honest_ones_is_still_red() -> None:
    """A protocol that is nested in every fold but one is not nested.

    The archival code was uniform about the defect; the failure mode that *reintroduces* it is
    not. It is one fold whose inner slice was left as the outer one during a refactor, which is
    why each fold is asserted on its own rather than the protocol being checked once.
    """
    folds = [TRAIN[i::3] for i in range(3)]
    for index, scored in enumerate(folds):
        inner = [row for row in TRAIN if row not in scored][:2]
        assert_early_stopping_is_honest(
            eval_rows=inner,
            scored_rows=scored,
            use_best_model=True,
            where=f"outer fold {index}",
        )

    with pytest.raises(LeakDetected, match="outer fold 1"):
        assert_early_stopping_is_honest(
            eval_rows=folds[1][:1],
            scored_rows=folds[1],
            use_best_model=True,
            where="outer fold 1",
        )


# --------------------------------------------------------------------------------------
# Misuse is not a finding
# --------------------------------------------------------------------------------------


def test_scoring_nothing_is_a_caller_error_not_a_leak() -> None:
    """A detector that cries leak when it was misused is a detector nobody will believe."""
    with pytest.raises(ValueError, match="no scored rows"):
        assert_early_stopping_is_honest(
            eval_rows=VAL, scored_rows=(), use_best_model=True, where="final fit"
        )
