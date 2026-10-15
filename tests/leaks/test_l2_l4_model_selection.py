"""L2 and L4 -- what model selection was allowed to see.

**L2** ``benchmark_model_selection.py:335-336``: the four ensemble members were chosen by
``nlargest(4, 'Val_Weighted_Orig')``, and REPORT.md then published Val R² 0.939 with a
bootstrap confidence interval on that same validation set. The number is the maximum of four
draws reported as if it were one.

**L4** ``:1156`` vs ``:1168``, and ``Catboostmodel.py:588`` vs ``:642-660``: one ``splits``
object both tunes and scores. There is no nesting anywhere in the protocol.

The sentinel reads a record rather than the training script, which is the point: card #88 must
emit one :class:`~hydms.qa.SelectionRecord` per model compared, and a protocol that cannot
produce that record cannot be checked at all.

Card #71.
"""

from __future__ import annotations

import pytest
from hydms.qa import (
    LeakDetected,
    SelectionRecord,
    assert_selection_is_nested,
    audit,
    for_leak,
)


def _record(
    model: str = "catboost",
    *,
    tuned_on: set[int] | None = None,
    scored_on: set[int] | None = None,
    **metrics: float,
) -> SelectionRecord:
    return SelectionRecord(
        model=model,
        tuned_on=frozenset(tuned_on if tuned_on is not None else {0, 1}),
        scored_on=frozenset(scored_on if scored_on is not None else {2}),
        metrics=metrics or {"train": 0.97, "val": 0.94},
    )


# --------------------------------------------------------------------------------------
# L2 -- a held-out metric in the room
# --------------------------------------------------------------------------------------


def test_l2_a_test_metric_in_the_selection_record_is_red() -> None:
    with pytest.raises(LeakDetected) as exc:
        assert_selection_is_nested([_record(train=0.97, val=0.94, test=0.89)])
    message = str(exc.value)
    assert "leak L2" in message
    assert "'test'" in message


def test_l2_a_record_without_a_held_out_metric_is_green() -> None:
    assert_selection_is_nested([_record(train=0.97, val=0.94)])


def test_l2_the_offending_model_is_named() -> None:
    """Four candidates, one carrying the test metric. The message must say which."""
    records = [
        _record("ridge", train=0.71, val=0.68),
        _record("catboost", train=0.97, val=0.94),
        _record("stacking", train=0.99, val=0.94, test=0.89),
        _record("xgboost", train=0.95, val=0.91),
    ]
    with pytest.raises(LeakDetected, match="'stacking'"):
        assert_selection_is_nested(records)


def test_l2_which_splits_count_as_held_out_is_the_callers_decision() -> None:
    """Validation is held out too during the search that *chooses* the protocol (PRD risk R4).

    Nothing here hard-codes "test". The archival ensemble was selected on validation and then
    reported on validation; a project that treats validation as held out for a given decision
    says so at the call site, and gets the same assertion.
    """
    assert_selection_is_nested([_record(train=0.97, val=0.94)])
    with pytest.raises(LeakDetected, match="'val'"):
        assert_selection_is_nested([_record(train=0.97, val=0.94)], holdout_splits=("test", "val"))


# --------------------------------------------------------------------------------------
# L4 -- nesting
# --------------------------------------------------------------------------------------


def test_l4_tuning_and_scoring_on_the_same_fold_is_red() -> None:
    with pytest.raises(LeakDetected) as exc:
        assert_selection_is_nested([_record(tuned_on={0, 1, 2}, scored_on={2})])
    message = str(exc.value)
    assert "leak L4" in message
    assert "2" in message, "the message must name the fold, not merely report an overlap"


def test_l4_an_outer_fold_the_tuner_never_saw_is_green() -> None:
    assert_selection_is_nested([_record(tuned_on={0, 1}, scored_on={2})])


def test_l4_a_full_nested_protocol_over_five_outer_folds_is_green() -> None:
    """Each outer fold is scored on itself and tuned on the other four -- the #88 shape."""
    folds = set(range(5))
    assert_selection_is_nested(
        [
            _record(f"catboost-outer-{held}", tuned_on=folds - {held}, scored_on={held})
            for held in sorted(folds)
        ]
    )


def test_l4_one_unnested_fold_among_four_nested_ones_is_red() -> None:
    folds = set(range(5))
    records = [
        _record(f"catboost-outer-{held}", tuned_on=folds - {held}, scored_on={held})
        for held in sorted(folds)
    ]
    records[3] = _record("catboost-outer-3", tuned_on=folds, scored_on={3})
    with pytest.raises(LeakDetected, match="'catboost-outer-3'"):
        assert_selection_is_nested(records)


# --------------------------------------------------------------------------------------
# Misuse is not a finding
# --------------------------------------------------------------------------------------


def test_an_empty_record_is_a_caller_error_not_a_clean_bill() -> None:
    """The failure mode this guards against is a protocol that emits no record at all.

    Passing an empty list must not read as "selection was clean". It reads as "nobody wrote
    down what selection did", which is the state the archival pipeline was actually in.
    """
    with pytest.raises(ValueError, match="a choice nobody wrote down"):
        assert_selection_is_nested([])


# --------------------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------------------


def test_l2_and_l4_are_wired_to_the_real_protocol() -> None:
    """Both sentinels are pointed at the module the leaks would come back to, and are green.

    They read `pending` from stage S1 until card #88 created
    `hydms/surrogate/validation.py`, which turned both `unwired` -- HG-1 red, on purpose --
    and the same card gave each a `live` hook against the real nested run. Neither subject was
    re-aimed to make the build green; that would have been the leak wearing the sentinel's
    name.
    """
    rows = {entry.leak: entry for entry in audit()}
    for leak in ("L2", "L4"):
        sentinel = for_leak(leak)
        assert sentinel is not None
        assert sentinel.subject == "hydms.surrogate.validation"
        assert sentinel.detector == "hydms.qa.detectors.assert_selection_is_nested"
        assert sentinel.live is not None, "an unwired sentinel guards its subject in name only"
        assert rows[leak].status == "green", rows[leak].detail
        assert rows[leak].owed_by == 88


def test_the_live_records_come_from_a_run_that_could_have_failed() -> None:
    """The nesting check is an intersection, so the ids have to be able to collide.

    A protocol numbering its inner and outer folds from two independent counters would satisfy
    `assert_selection_is_nested` no matter what it did with the data. The real run issues an id
    for the *set of compositions a fold holds out*, so an inner fold over an outer fold's
    materials collides with it -- which is what makes the green above worth having.
    """
    pytest.importorskip("pandas", reason="the live protocol is pandas frames end to end")
    from hydms.qa.sentinels import _validation_run

    _, evaluation = _validation_run()
    assert evaluation.records, "a run that emitted no record is not a checked one"
    for fold in evaluation.outer:
        assert evaluation.space.known(fold.held_out) == fold.id

    record = evaluation.records[0]
    assert record.tuned_on and record.scored_on
    assert not record.tuned_on & record.scored_on
    with pytest.raises(LeakDetected, match="the tuner also saw"):
        assert_selection_is_nested(
            [
                SelectionRecord(
                    model=record.model,
                    tuned_on=record.tuned_on | {next(iter(record.scored_on))},
                    scored_on=record.scored_on,
                    metrics=record.metrics,
                )
            ]
        )
