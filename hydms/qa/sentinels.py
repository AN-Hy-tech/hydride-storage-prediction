"""One sentinel per named leak, each carrying the counterexample that makes it mean something.

A detector nobody has watched fire is an assumption with a function's name on it. So every
sentinel here ships with at least one :class:`Reproduction`: a *leaky* case that recreates the
archival defect in miniature and must raise :class:`~hydms.qa.detectors.LeakDetected`, and a
*clean* twin, differing in as little as possible, that must not. :func:`audit` runs all of
them, which is how gate HG-1 can prove the sentinels are still capable of going red without
running the pipeline, and without anybody having to remember that they once did it by hand.

That is a deliberate move of ``docs/QA-PROTOCOL.md`` section 5's "make it red on purpose and
record that you did" from a ritual into a check. The record stays in the card's narrative; the
proof runs every build.

:func:`audit` places each of the thirteen leaks in one of six states. Three of them are red --
``broken`` (the detector stopped detecting), ``unwired`` (see below), ``uncovered`` (a leak
with neither a sentinel nor a recorded deferral). Two are honest incompleteness, ``pending``
and ``deferred``. One, ``green``, means the real subject was checked.

``unwired`` is the state that would otherwise rot quietly. A sentinel is written in stage S1
against a miniature of a defect, and only becomes a guard when it is pointed at the module the
defect could return to -- which does not exist yet. So the moment card #10 creates
``hydms/data/merge.py``, the L9 sentinel's subject appears while its ``live`` hook is still
``None``, and HG-1 goes **red** until somebody wires it. Nobody has to remember.

Card #71.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from .detectors import (
    LeakDetected,
    SelectionRecord,
    assert_disjoint_groups,
    assert_early_stopping_is_honest,
    assert_holdout_unchanged,
    assert_merge_is_keyed,
    assert_selection_ignores_holdout,
    assert_selection_is_nested,
)
from .leaks import INVENTORY, by_id

__all__ = [
    "DEFERRED",
    "SENTINELS",
    "Deferral",
    "Reproduction",
    "Sentinel",
    "SentinelReport",
    "audit",
    "for_leak",
]


def _pandas() -> Any:
    """Import pandas at call time, not at import time.

    ``hydms.gates`` scans this package to build its registry, and ``python -m hydms.gates
    list`` must stay answerable -- and fast -- on an interpreter where the scientific stack is
    not installed. Only four of the reproductions need a DataFrame at all.
    """
    import pandas as pd

    return pd


# --------------------------------------------------------------------------------------
# The shapes
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Reproduction:
    """A leak in miniature, beside the corrected version of the same thing.

    The two cases must differ only in the defect. A ``clean`` twin that also changes the shape
    of the data proves nothing about the detector: it would pass for the wrong reason, and the
    sentinel would be measuring its fixture rather than its subject.
    """

    label: str
    leaky: Callable[[], None]
    clean: Callable[[], None]


@dataclass(frozen=True)
class Sentinel:
    """The guard for one leak.

    Attributes:
        leak: The inventory id it guards. Everything else about the leak -- its site, its
            effect, the card that closes it -- is read from :data:`~hydms.qa.leaks.INVENTORY`
            rather than restated here.
        title: What the sentinel asserts, as a sentence.
        detector: The qualified name of the function doing the asserting, for the report.
        subject: The module the leak would reappear in. It is a *prediction* made in stage S1
            about a file stage S2--S4 will create; if the owning card names it differently,
            that card updates this string. ``tests/leaks/test_inventory.py`` checks that its
            parent package at least exists, so a typo is caught immediately rather than in six
            weeks when the sentinel silently never wires up.
        reproductions: At least one leaky/clean pair.
        live: The check against the real subject, once there is one. ``None`` means the
            subject has not been built yet -- and stops meaning that the moment it has.
    """

    leak: str
    title: str
    detector: str
    subject: str
    reproductions: tuple[Reproduction, ...]
    live: Callable[[], None] | None = None


@dataclass(frozen=True)
class Deferral:
    """A leak with no sentinel yet, and the card that owes one.

    Recorded rather than omitted. An inventory of thirteen and a suite of ten is a gap; a gap
    nobody wrote down is indistinguishable from coverage.
    """

    leak: str
    owed_by: int
    reason: str


#: The six states one leak can be in, worst last. ``broken``, ``unwired`` and ``uncovered``
#: are the three HG-1 goes red for; ``pending`` and ``deferred`` are honest incompleteness and
#: keep it at SKIPPED, which the harness already renders as loudly as a failure.
RED = ("broken", "unwired", "uncovered")


@dataclass(frozen=True)
class SentinelReport:
    """What :func:`audit` concluded about one leak. One row of gate HG-1's evidence.

    Attributes:
        status: One of ``green`` (the real subject is guarded and the guard holds),
            ``pending`` (demonstrated, but the module it guards has not been written yet),
            ``deferred`` (no sentinel, and a named card owes one), ``broken`` (the detector no
            longer fires on the leak, or rejects the fix), ``unwired`` (the subject exists and
            nobody pointed the sentinel at it) or ``uncovered`` (no sentinel, no deferral).
    """

    leak: str
    title: str
    status: str
    owed_by: int
    detail: str

    @property
    def ok(self) -> bool:
        """Whether this row is free of anything HG-1 must go red for."""
        return self.status not in RED


# --------------------------------------------------------------------------------------
# L1, L5 -- early stopping
# --------------------------------------------------------------------------------------

_TRAIN_ROWS = tuple(f"train-{i}" for i in range(6))
_VAL_ROWS = ("val-0", "val-1")
_TEST_ROWS = ("test-0", "test-1", "test-2")


def _l1_eval_set_is_the_test_pool() -> None:
    """`Catboostmodel.py:604-606` -- final_model.fit(..., eval_set=test_pool)."""
    assert_early_stopping_is_honest(
        eval_rows=_TEST_ROWS,
        scored_rows=_TEST_ROWS,
        use_best_model=True,
        where="final fit",
    )


def _l1_eval_set_is_the_validation_split() -> None:
    assert_early_stopping_is_honest(
        eval_rows=_VAL_ROWS,
        scored_rows=_TEST_ROWS,
        use_best_model=True,
        where="final fit",
    )


def _l1_empty_eval_set() -> None:
    """The failure CatBoost itself raises, asserted before the fit rather than during it."""
    assert_early_stopping_is_honest(
        eval_rows=(),
        scored_rows=_TEST_ROWS,
        use_best_model=True,
        where="final fit",
    )


def _l5_fold_stops_on_itself() -> None:
    """`Catboostmodel.py:576-582` -- the fold's own rows are its eval_set."""
    fold = _TRAIN_ROWS[4:]
    assert_early_stopping_is_honest(
        eval_rows=fold,
        scored_rows=fold,
        use_best_model=True,
        where="outer fold 3",
    )


def _l5_fold_stops_on_an_inner_slice() -> None:
    assert_early_stopping_is_honest(
        eval_rows=_TRAIN_ROWS[2:4],
        scored_rows=_TRAIN_ROWS[4:],
        use_best_model=True,
        where="outer fold 3",
    )


# --------------------------------------------------------------------------------------
# L2, L4 -- model selection
# --------------------------------------------------------------------------------------


def _l2_test_metric_in_the_record() -> None:
    """`benchmark_model_selection.py:335-336` -- members ranked while every metric was visible."""
    assert_selection_is_nested(
        [
            SelectionRecord(
                model="catboost",
                tuned_on=frozenset({0, 1}),
                scored_on=frozenset({2}),
                metrics={"train": 0.97, "val": 0.94, "test": 0.89},
            )
        ]
    )


def _l2_record_without_a_test_metric() -> None:
    assert_selection_is_nested(
        [
            SelectionRecord(
                model="catboost",
                tuned_on=frozenset({0, 1}),
                scored_on=frozenset({2}),
                metrics={"train": 0.97, "val": 0.94},
            )
        ]
    )


def _l4_tuned_and_scored_on_the_same_fold() -> None:
    """`benchmark_model_selection.py:1156` vs `:1168` -- one splits object does both jobs."""
    assert_selection_is_nested(
        [
            SelectionRecord(
                model="catboost",
                tuned_on=frozenset({0, 1, 2}),
                scored_on=frozenset({2}),
                metrics={"train": 0.97, "val": 0.94},
            )
        ]
    )


def _l4_nested_folds() -> None:
    assert_selection_is_nested(
        [
            SelectionRecord(
                model="catboost",
                tuned_on=frozenset({0, 1}),
                scored_on=frozenset({2}),
                metrics={"train": 0.97, "val": 0.94},
            )
        ]
    )


# --------------------------------------------------------------------------------------
# L3, L10 -- held-out data is immutable
# --------------------------------------------------------------------------------------

_ROW_LABELS = ("a", "b", "c", "d", "e", "f")
_HELD_OUT = ("e", "f")


def _targets() -> Any:
    pd = _pandas()
    return pd.Series(
        [1.5, 2.0, 2.5, 3.0, 3.5, 4.0], index=list(_ROW_LABELS), name="H2_W% (max)"
    )


def _l3_targets_overwritten() -> None:
    """`CleanLab.py:90` -- managed_df['target'] = np.where(mask, y_pred, y), on val and test."""
    before = _targets()
    after = before.copy()
    after.loc["e"] = 3.52  # the model's own prediction, so its residual is now ~zero
    assert_holdout_unchanged(before, after, holdout=_HELD_OUT)


def _l3_only_training_rows_dropped() -> None:
    before = _targets()
    after = before.drop(index=["b"])  # screening may drop a training row, and nothing else
    assert_holdout_unchanged(before, after, holdout=_HELD_OUT)


def _l3_held_out_row_dropped() -> None:
    before = _targets()
    after = before.drop(index=["f"])
    assert_holdout_unchanged(before, after, holdout=_HELD_OUT)


def _features() -> Any:
    pd = _pandas()
    return pd.DataFrame(
        {"avg_atomic_mass": [58.7, 47.9, 24.3, 91.2, 88.9, 140.1],
         "temperature(K)": [298.0, 303.0, 573.0, 323.0, 298.0, 598.0]},
        index=list(_ROW_LABELS),
    )


def _l10_held_out_features_clipped() -> None:
    """`Ashghal/Outliers_Management.py:60-72` -- val/test features clipped by their residuals."""
    before = _features()
    after = before.copy()
    after.loc["f", "avg_atomic_mass"] = 100.0
    assert_holdout_unchanged(before, after, holdout=_HELD_OUT, what="held-out feature rows")


def _l10_only_training_features_clipped() -> None:
    before = _features()
    after = before.copy()
    after.loc["c", "avg_atomic_mass"] = 100.0
    assert_holdout_unchanged(before, after, holdout=_HELD_OUT, what="held-out feature rows")


# --------------------------------------------------------------------------------------
# L6 -- feature selection
# --------------------------------------------------------------------------------------

_SELECTION_TRAIN = ["a", "b", "c", "d"]
_SELECTION_HOLDOUT = ["e", "f"]


def _selection_frame() -> Any:
    """Six rows, three candidate features. Only ``f1`` survives on the training rows alone.

    ``f2`` sits exactly on the threshold across the whole frame, held there by its held-out
    values. That is the point: a selector that reads all six rows is one nudge away from a
    different answer, and the perturbation is that nudge.
    """
    pd = _pandas()
    return pd.DataFrame(
        {
            "f1": [3.0, 3.0, 3.0, 3.0, 0.0, 0.0],
            "f2": [0.0, 0.0, 0.0, 0.0, 2.0, 4.0],
            "f3": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        },
        index=list(_ROW_LABELS),
    )


def _select_on_everything(frame: Any) -> Sequence[str]:
    """`Boruta_FeatEng.py:57` -- filter the whole frame, then cross-validate on the result."""
    return tuple(column for column in frame.columns if frame[column].mean() > 1.0)


def _select_on_the_training_rows(frame: Any) -> Sequence[str]:
    training = frame.loc[_SELECTION_TRAIN]
    return tuple(column for column in training.columns if training[column].mean() > 1.0)


def _l6_selection_reads_the_holdout() -> None:
    assert_selection_ignores_holdout(
        _select_on_everything, _selection_frame(), holdout=_SELECTION_HOLDOUT
    )


def _l6_selection_reads_the_training_rows_only() -> None:
    assert_selection_ignores_holdout(
        _select_on_the_training_rows, _selection_frame(), holdout=_SELECTION_HOLDOUT
    )


# --------------------------------------------------------------------------------------
# L7, L8 -- grouping
# --------------------------------------------------------------------------------------


def _l7_a_formula_in_two_folds() -> None:
    """`benchmark_model_selection.py:895` -- StratifiedKFold over rows, with no groups."""
    assert_disjoint_groups(
        {"fold-0": ["LaNi5", "TiFe", "Mg2Ni"], "fold-1": ["LaNi5", "ZrV2"]},
        what="cross-validation folds",
    )


def _l7_folds_grouped_by_composition() -> None:
    assert_disjoint_groups(
        {"fold-0": ["LaNi5", "TiFe", "Mg2Ni"], "fold-1": ["ZrV2", "TiCr2"]},
        what="cross-validation folds",
    )


# The four raw strings behind two of the sixteen collisions the audit measured. Written here
# as the canonical keys they normalise to, because that is the whole finding: under the raw
# string these are four identities and `split_data.py`'s assertion passes.
_COLLIDING = ("ce1mg12", "pr1co5")


def _l8_one_composition_in_two_splits() -> None:
    """`split_data.py:48,55` -- `Ce1Mg12` in test, `Mg12Ce1` in validation, one material."""
    assert_disjoint_groups({"test": [*_COLLIDING, "lani5"], "val": [*_COLLIDING, "tife"]})


def _l8_splits_grouped_by_composition() -> None:
    assert_disjoint_groups({"test": [*_COLLIDING, "lani5"], "val": ["tife", "zrv2"]})


# --------------------------------------------------------------------------------------
# L9 -- the merge
# --------------------------------------------------------------------------------------

_MERGE_KEYS = ["LaNi5", "TiFe", "Mg2Ni", "ZrV2"]


def _merge_inputs() -> tuple[Any, ...]:
    """A spine and two feature frames, keyed by composition -- the merge's real shape."""
    pd = _pandas()
    index = pd.Index(_MERGE_KEYS, name="Composition")
    return (
        pd.DataFrame({"target": [1.4, 1.9, 7.6, 2.0]}, index=index),
        pd.DataFrame({"oliynyk_0": [10.0, 20.0, 30.0, 40.0]}, index=index),
        pd.DataFrame({"jarvis_0": [0.1, 0.2, 0.3, 0.4]}, index=index),
    )


def _positional_concat(frames: Sequence[Any]) -> Any:
    """`merge_datasets.py:46` -- pd.concat(..., axis=1) after reset_index(drop=True)."""
    pd = _pandas()
    return pd.concat([frame.reset_index(drop=True) for frame in frames], axis=1)


def _keyed_join(frames: Sequence[Any]) -> Any:
    """What card #10 must build: join on the key, and assert the join covered the spine."""
    merged = frames[0]
    for right in frames[1:]:
        joined = merged.join(right, how="inner")
        if len(joined) != len(merged):
            raise ValueError(
                f"the join dropped {len(merged) - len(joined)} row(s) of the spine; every "
                f"composition must carry every feature block"
            )
        merged = joined
    return merged


def _l9_positional_merge() -> None:
    assert_merge_is_keyed(_positional_concat, _merge_inputs())


def _l9_keyed_merge() -> None:
    assert_merge_is_keyed(_keyed_join, _merge_inputs())


# --------------------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------------------

SENTINELS: tuple[Sentinel, ...] = (
    Sentinel(
        leak="L1",
        title="the eval_set is the validation split, and is never empty under use_best_model",
        detector="hydms.qa.detectors.assert_early_stopping_is_honest",
        subject="hydms.surrogate.model",
        reproductions=(
            Reproduction(
                "the test pool passed as eval_set",
                _l1_eval_set_is_the_test_pool,
                _l1_eval_set_is_the_validation_split,
            ),
            Reproduction(
                "use_best_model=True with an empty eval_set",
                _l1_empty_eval_set,
                _l1_eval_set_is_the_validation_split,
            ),
        ),
    ),
    Sentinel(
        leak="L2",
        title="the model-selection record carries no held-out metric",
        detector="hydms.qa.detectors.assert_selection_is_nested",
        subject="hydms.surrogate.validation",
        reproductions=(
            Reproduction(
                "a test metric visible while members were ranked",
                _l2_test_metric_in_the_record,
                _l2_record_without_a_test_metric,
            ),
        ),
    ),
    Sentinel(
        leak="L3",
        title="held-out targets are byte-identical before and after screening",
        detector="hydms.qa.detectors.assert_holdout_unchanged",
        subject="hydms.data.screening",
        reproductions=(
            Reproduction(
                "a held-out target replaced by the model's prediction",
                _l3_targets_overwritten,
                _l3_only_training_rows_dropped,
            ),
            Reproduction(
                "a held-out row dropped by screening",
                _l3_held_out_row_dropped,
                _l3_only_training_rows_dropped,
            ),
        ),
    ),
    Sentinel(
        leak="L4",
        title="the reported score comes from folds the tuner never saw",
        detector="hydms.qa.detectors.assert_selection_is_nested",
        subject="hydms.surrogate.validation",
        reproductions=(
            Reproduction(
                "one splits object tunes and then scores",
                _l4_tuned_and_scored_on_the_same_fold,
                _l4_nested_folds,
            ),
        ),
    ),
    Sentinel(
        leak="L5",
        title="no fold early-stops on the rows it is scored on",
        detector="hydms.qa.detectors.assert_early_stopping_is_honest",
        subject="hydms.surrogate.model",
        reproductions=(
            Reproduction(
                "the fold is its own eval_set",
                _l5_fold_stops_on_itself,
                _l5_fold_stops_on_an_inner_slice,
            ),
        ),
    ),
    Sentinel(
        leak="L6",
        title="perturbing held-out rows does not change the selected feature set",
        detector="hydms.qa.detectors.assert_selection_ignores_holdout",
        subject="hydms.surrogate.selection",
        reproductions=(
            Reproduction(
                "selection fitted on the whole frame before cross-validation",
                _l6_selection_reads_the_holdout,
                _l6_selection_reads_the_training_rows_only,
            ),
        ),
    ),
    Sentinel(
        leak="L7",
        title="no composition appears in two cross-validation folds",
        detector="hydms.qa.detectors.assert_disjoint_groups",
        subject="hydms.surrogate.validation",
        reproductions=(
            Reproduction(
                "row-level folds with no group key",
                _l7_a_formula_in_two_folds,
                _l7_folds_grouped_by_composition,
            ),
        ),
    ),
    Sentinel(
        leak="L8",
        title="no canonical composition appears in two splits",
        detector="hydms.qa.detectors.assert_disjoint_groups",
        subject="hydms.data.splits",
        reproductions=(
            Reproduction(
                "the same material in test and validation under two spellings",
                _l8_one_composition_in_two_splits,
                _l8_splits_grouped_by_composition,
            ),
        ),
    ),
    Sentinel(
        leak="L9",
        title="the merge joins on a key and refuses a row it cannot cover",
        detector="hydms.qa.detectors.assert_merge_is_keyed",
        subject="hydms.data.merge",
        reproductions=(
            Reproduction("positional concat", _l9_positional_merge, _l9_keyed_merge),
        ),
    ),
    Sentinel(
        leak="L10",
        title="held-out feature values are byte-identical before and after screening",
        detector="hydms.qa.detectors.assert_holdout_unchanged",
        subject="hydms.data.screening",
        reproductions=(
            Reproduction(
                "a held-out feature value clipped by its own residual",
                _l10_held_out_features_clipped,
                _l10_only_training_features_clipped,
            ),
        ),
    ),
)


DEFERRED: tuple[Deferral, ...] = (
    Deferral(
        leak="L11",
        owed_by=29,
        reason="the sentinel asserts that the explainability record names no held-out split, "
        "and there is no such record until #29 defines what SHAP and PDP are computed on",
    ),
    Deferral(
        leak="L12",
        owed_by=26,
        reason="the sentinel asserts that sample weights are a function of nothing but the "
        "training rows' own features; the weighting scheme is #26's decision to make",
    ),
    Deferral(
        leak="L13",
        owed_by=87,
        reason="the sentinel asserts that Alloy_class survives featurisation for every row, "
        "which needs the canonical key #87 re-joins it on",
    ),
)


def for_leak(leak_id: str) -> Sentinel | None:
    """The sentinel guarding one leak, or ``None`` if it is deferred."""
    for sentinel in SENTINELS:
        if sentinel.leak == leak_id:
            return sentinel
    return None


# --------------------------------------------------------------------------------------
# The audit
# --------------------------------------------------------------------------------------


def _module_exists(dotted: str) -> bool:
    """Whether ``dotted`` is importable, without importing it.

    A missing leaf under an existing package gives ``None``; a missing *parent* raises, which
    means the subject was misspelled. Both are "not built yet" as far as this is concerned --
    ``tests/leaks/test_inventory.py`` is what separates them, by asserting the parent package
    is real.
    """
    try:
        return importlib.util.find_spec(dotted) is not None
    except (ImportError, ValueError):
        return False


def _demonstrate(sentinel: Sentinel) -> tuple[bool, str]:
    """Run every reproduction. The leaky case must fire; the clean twin must not."""
    for case in sentinel.reproductions:
        try:
            case.leaky()
        except LeakDetected:
            pass
        except Exception as exc:  # the fixture broke, which is not the same as the leak firing
            return False, (
                f"reproduction {case.label!r} raised {type(exc).__name__} instead of "
                f"LeakDetected: {exc}"
            )
        else:
            return False, (
                f"reproduction {case.label!r} did not go red. {sentinel.detector} no longer "
                f"detects {sentinel.leak}, so nothing stops it being reintroduced."
            )

        try:
            case.clean()
        except Exception as exc:  # any failure here is the same finding
            return False, (
                f"the corrected twin of {case.label!r} also failed ({type(exc).__name__}: "
                f"{exc}). A detector that rejects the fix is a detector nobody can satisfy."
            )

    count = len(sentinel.reproductions)
    return True, f"{count} reproduction(s) red, {count} corrected twin(s) green"


def _uncovered(leak_id: str) -> SentinelReport:
    leak = by_id(leak_id)
    return SentinelReport(
        leak=leak.id,
        title="(no sentinel)",
        status="uncovered",
        owed_by=leak.closed_by,
        detail=(
            f"{leak.id} ({leak.site}: {leak.effect}) has no sentinel and no recorded "
            f"deferral. It is simply uncovered: nothing would go red if it came back."
        ),
    )


def audit() -> tuple[SentinelReport, ...]:
    """Check every leak in the inventory, in inventory order.

    One row per leak, saying which of the six states it is in and why. This function decides
    nothing about the build -- gate HG-1 reads these rows and decides -- which is what lets the
    tests assert against exactly the evidence the gate reports.
    """
    deferred = {entry.leak: entry for entry in DEFERRED}
    rows: list[SentinelReport] = []

    for leak in INVENTORY:
        sentinel = for_leak(leak.id)

        if sentinel is None:
            waiver = deferred.get(leak.id)
            if waiver is None:
                rows.append(_uncovered(leak.id))
            else:
                rows.append(
                    SentinelReport(
                        leak=leak.id,
                        title="(no sentinel)",
                        status="deferred",
                        owed_by=waiver.owed_by,
                        detail=f"deferred to card #{waiver.owed_by}: {waiver.reason}",
                    )
                )
            continue

        demonstrated, detail = _demonstrate(sentinel)
        if not demonstrated:
            status = "broken"
        elif not _module_exists(sentinel.subject):
            status = "pending"
            detail = f"{detail}; {sentinel.subject} is card #{leak.closed_by}'s to write"
        elif sentinel.live is None:
            status = "unwired"
            detail = (
                f"{sentinel.subject} now exists and this sentinel is still pointed at a "
                f"miniature of it. Card #{leak.closed_by} must give it a `live` check, or "
                f"{leak.id} is guarded in name only."
            )
        else:
            try:
                sentinel.live()
            except LeakDetected as exc:
                status, detail = "broken", f"{sentinel.subject} has leak {leak.id}: {exc}"
            except Exception as exc:  # a live check that cannot run is red, not absent
                status = "broken"
                detail = (
                    f"the live check against {sentinel.subject} raised "
                    f"{type(exc).__name__}: {exc}"
                )
            else:
                status = "green"
                detail = f"{detail}; {sentinel.subject} checked"

        rows.append(
            SentinelReport(
                leak=leak.id,
                title=sentinel.title,
                status=status,
                owed_by=leak.closed_by,
                detail=detail,
            )
        )

    return tuple(rows)
