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
from functools import lru_cache
from typing import Any

from .detectors import (
    LeakDetected,
    SelectionRecord,
    assert_disjoint_groups,
    assert_early_stopping_is_honest,
    assert_explanation_is_not_held_out,
    assert_holdout_unchanged,
    assert_merge_is_keyed,
    assert_metadata_survives,
    assert_selection_ignores_holdout,
    assert_selection_is_nested,
    assert_weights_ignore_target,
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


@lru_cache(maxsize=1)
def _screening_run() -> tuple[Any, Any, Any]:
    """Card #14's screening of the real 1279 rows: before, after, and the held-out labels.

    The label-quality input is `True` for **every** row -- a method that condemns the whole
    dataset. That is not a plausible screening; it is the strongest available pressure on the
    contract, and it needs no invented heuristic to stand in for a feature matrix that does
    not exist until S3. Under it a correct stage drops every training row and leaves every
    held-out row exactly where it was, byte for byte. A stage that touched the holdout could
    not hide.

    Cached: the split it depends on costs ~0.7 s and `audit()` runs on every gate invocation.
    """
    pd = _pandas()
    from hydms.data.load import load_hydride_data
    from hydms.data.screening import screen
    from hydms.data.splits import assign_splits

    frame = load_hydride_data()
    split = assign_splits(frame)
    condemn_everything = pd.Series(True, index=frame.index)
    result = screen(frame, split, label_issues=condemn_everything)
    return frame, result.frame, list(split[split != "train"].index)


def _l3_live() -> None:
    """Card #14's screening, against the real dataset: held-out **targets** are immutable."""
    before, after, held_out = _screening_run()
    assert_holdout_unchanged(
        before["H2_W% (max)"], after["H2_W% (max)"], holdout=held_out
    )


def _l10_live() -> None:
    """The same run, on the other side of the table: held-out **features** are immutable.

    L10 has no closing card -- `Ashghal/Outliers_Management.py` is not being ported, which is
    an accident rather than a fix -- so this hook is watchfulness, not a fix. It guards the
    module where the clipping would come back if screening ever grew outlier handling.
    """
    before, after, held_out = _screening_run()
    columns = [name for name in before.columns if name != "H2_W% (max)"]
    assert_holdout_unchanged(
        before[columns], after[columns], holdout=held_out, what="held-out feature rows"
    )


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


@lru_cache(maxsize=1)
def _l8_real_splits() -> tuple[Any, Any]:
    """Card #13's split of the real 1279 rows, and their canonical keys. Computed once.

    Cached because the protocol costs about 0.7 s -- two `StratifiedShuffleSplit` cuts over
    1115 compositions, on top of keying 1279 formulae -- and `audit()` runs on every gate
    invocation and every test in `tests/leaks/`.
    """
    from hydms.data.canonical import group_keys
    from hydms.data.load import load_hydride_data
    from hydms.data.splits import assign_splits

    frame = load_hydride_data()
    return assign_splits(frame), group_keys(frame)


def _l8_live() -> None:
    """Card #13's splits, against the real dataset. The wiring the `unwired` state demands.

    The keys handed to the detector come from `group_keys` here rather than from anything the
    split module returned, so a split that had quietly grouped on something else would show
    up as a straddle rather than as agreement with itself.
    """
    from hydms.data.splits import SPLIT_NAMES

    split, keys = _l8_real_splits()
    assert_disjoint_groups({name: keys[split == name] for name in SPLIT_NAMES})


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


@lru_cache(maxsize=1)
def _l9_real_frames() -> tuple[Any, ...]:
    """The real spine and two real per-composition blocks, read once.

    The spine is ``hydride_data.csv`` through card #9's loader -- 1279 measurement rows over
    1149 distinct formula strings -- and the blocks are one row per distinct formula, which
    is the shape every descriptor block has (PRD section 2.3: every selected feature is a
    composition statistic or the temperature). So the live check exercises the one-to-many
    join the pipeline actually performs, on the data it actually performs it on, rather than
    a four-row miniature.

    The two columns are derived from :func:`~hydms.data.load.parse_formula` because they must
    come from somewhere real and the descriptor layer (cards #16-#20) does not exist yet.
    They are stand-ins for its output, not a claim about which descriptors it will produce.
    """
    pd = _pandas()
    from hydms.data.load import load_hydride_data, parse_formula

    spine = load_hydride_data()
    formulae = list(dict.fromkeys(spine["Composition"]))
    parsed = [parse_formula(formula) for formula in formulae]
    index = pd.Index(formulae, name="Composition")
    return (
        spine,
        pd.DataFrame({"n_elements": [float(len(c)) for c in parsed]}, index=index),
        pd.DataFrame({"total_amount": [sum(c.values()) for c in parsed]}, index=index),
    )


def _l9_real_merge(frames: Sequence[Any]) -> Any:
    """Call the real :func:`hydms.data.merge.merge_features` the way the pipeline will."""
    from hydms.data.merge import FeatureBlock, merge_features

    spine, *blocks = frames
    return merge_features(
        spine,
        [
            FeatureBlock(name=f"descriptor block {position}", frame=frame, key=("Composition",))
            for position, frame in enumerate(blocks)
        ],
    )


def _l9_live() -> None:
    """Card #10's merge, against the real dataset. The wiring the `unwired` state demands."""
    assert_merge_is_keyed(_l9_real_merge, _l9_real_frames())


# --------------------------------------------------------------------------------------
# L13 -- Alloy_class through featurisation
# --------------------------------------------------------------------------------------

_CLASS_ROWS = ("row-0", "row-1", "row-2", "row-3")


def _class_frame() -> Any:
    """Four rows as the raw file has them: a formula, its class, and the target.

    Two of them are the same material under two spellings, because that is the case the
    re-join has to survive: `Ce1Mg12` and `Mg12Ce1` are one composition carrying two class
    labels in the file, and a featuriser that keeps the class per *string* keeps two answers.
    """
    pd = _pandas()
    return pd.DataFrame(
        {
            "Composition": ["Ce1Mg12", "Mg12Ce1", "LaNi5", "TiFe"],
            "Alloy_class": ["MIC", "Mg", "AB5", "AB"],
            "H2_W% (max)": [6.0, 6.0, 1.4, 1.9],
        },
        index=list(_CLASS_ROWS),
    )


def _drop_object_columns(frame: Any) -> Any:
    """`extract_features_cbfv.py:19-21`, transcribed.

    The features it then computes are irrelevant to the defect, so this stops at the drop.
    """
    object_columns = frame.select_dtypes(include="object").columns
    return frame.drop(columns=[name for name in object_columns if name != "Composition"])


def _featurise_carrying_metadata(frame: Any) -> Any:
    """The same stage, keeping the columns it was handed and adding one of its own."""
    featurised = frame.copy(deep=True)
    featurised["n_elements"] = [2.0, 2.0, 2.0, 2.0]
    return featurised


def _l13_alloy_class_dropped() -> None:
    before = _class_frame()
    assert_metadata_survives(
        before,
        _drop_object_columns(before),
        columns=("Alloy_class",),
        what="row metadata",
    )


def _l13_alloy_class_carried_through() -> None:
    before = _class_frame()
    assert_metadata_survives(
        before,
        _featurise_carrying_metadata(before),
        columns=("Alloy_class",),
        what="row metadata",
    )


def _l13_a_row_loses_its_class() -> None:
    """The quieter half: the column survives and one row's label does not."""
    before = _class_frame()
    after = _featurise_carrying_metadata(before)
    after.loc["row-1", "Alloy_class"] = None
    assert_metadata_survives(
        before, after, columns=("Alloy_class",), what="row metadata"
    )


#: The one feature that cannot be built for most of the curated set. The citable 2024 Oliynyk
#: edition leaves ``gordy_en`` blank for 21 of the dataset's 55 elements (#16), so the full 22
#: refuse **266 of the 1,279** rows while the remaining 21 cover **1,278** -- every row but
#: ``Eu1Ni5``, whose europium blocks all six JARVIS features. The hook below leaves it out so
#: that it checks the real featuriser over almost the whole file rather than over three
#: quarters of it. That is a statement about *this check's* coverage and nothing else: which
#: features the project keeps is the trade cards #24 and #25 own, and the hook must not be
#: read as having pre-empted it.
_GORDY = "dev_Gordy_electonegativity"


@lru_cache(maxsize=1)
def _featurisation_run() -> tuple[Any, Any]:
    """Card #20's featuriser over the real curated rows: the record before, the join after.

    The `unwired` state exists for exactly this: the sentinel was written in S1 against a
    four-row miniature of ``extract_features_cbfv.py``, and it only becomes a guard when it is
    pointed at the module the drop could return to. That module is
    ``hydms.descriptors.featurize``, and the join it must survive is
    ``hydms.data.metadata.with_features`` -- both real, both called here exactly as a caller
    would call them.

    The rows are chosen by asking the contract, using the idiom
    :func:`~hydms.descriptors.featurize.featurize`'s own docstring documents, rather than by
    naming formulae: 1,278 of the 1,279 survive that question and the one that does not is
    named by the verdict rather than by this file. Refusing to run at all on an empty
    selection is the point of the check below -- a live hook that quietly featurises nothing
    reports a green it never earned.

    Cached: it costs ~0.35 s and ``audit()`` runs on every gate invocation.
    """
    from hydms.config import load as load_config
    from hydms.data.load import load_hydride_data, parse_formula
    from hydms.data.metadata import with_features, with_metadata
    from hydms.descriptors.contract import CONTRACT, FeatureContract
    from hydms.descriptors.featurize import featurize

    names = load_config().columns
    record = with_metadata(load_hydride_data())
    contract = FeatureContract.from_names(
        [name for name in CONTRACT.names if name != _GORDY]
    )
    keep = [
        label
        for label, formula in record[names.formula].items()
        if contract.computability(parse_formula(formula)).complete
    ]
    if not keep:
        raise ValueError(
            f"the L13 live check could not featurise a single one of {len(record)} curated "
            f"row(s) from the {len(contract)}-feature contract, so it would have asserted "
            f"over an empty frame. A vacuous pass is the shape of the leak it exists to "
            f"catch."
        )

    before = record.loc[keep]
    features = featurize(
        before[names.formula], before[names.temperature], contract=contract
    )
    return before, with_features(before, features)


def _l13_live() -> None:
    """Card #12's join, against the real dataset: the class arrives on the other side.

    ``with_features`` asserts this itself before it returns -- the guard belongs to the
    pipeline, not to the sentinel -- and this runs the same detector over the same frames, so
    that weakening the guard inside the join cannot make HG-1 green.
    """
    from hydms.data.metadata import metadata_columns

    before, after = _featurisation_run()
    assert_metadata_survives(
        before, after, columns=metadata_columns(), what="row metadata"
    )


# --------------------------------------------------------------------------------------
# L2, L4, L7 -- the nested protocol, against the real training split
# --------------------------------------------------------------------------------------


def _baseline_prediction(frame: Any, statistic: str) -> float:
    """A constant predictor: the median or the mean of the rows it was fitted on."""
    from hydms.config import load as load_config

    values = frame[load_config().columns.target]
    return float(values.median() if statistic == "median" else values.mean())


def _baseline_error(frame: Any, prediction: float) -> float:
    """Mean absolute error of a constant prediction over ``frame``."""
    from hydms.config import load as load_config

    return float((frame[load_config().columns.target] - prediction).abs().mean())


def _tune_baseline(task: Any) -> str:
    """Choose between the two constants on the inner folds -- and on nothing else.

    A search, in the only sense the protocol cares about: it reads the folds it is given,
    fits on each fold's training rows and scores on each fold's held-out ones, and returns
    the winner. Reading them is what ``tuned_on`` records.
    """
    scored: dict[str, float] = {}
    for statistic in ("median", "mean"):
        errors = [
            _baseline_error(
                task.frame.loc[list(fold.test)],
                _baseline_prediction(task.frame.loc[list(fold.train)], statistic),
            )
            for fold in task.folds
        ]
        scored[statistic] = sum(errors) / len(errors)
    return min(scored, key=lambda name: scored[name])


def _score_baseline(configuration: str, task: Any) -> dict[str, float]:
    """Refit the chosen constant on the outer fold's training rows; score its held-out ones."""
    return {
        "outer": _baseline_error(
            task.test, _baseline_prediction(task.train, configuration)
        )
    }


@lru_cache(maxsize=1)
def _validation_run() -> tuple[Any, Any]:
    """Card #88's nested protocol over the real training split. Computed once.

    **The contender is a stand-in and is not a claim about the surrogate.** It chooses
    between predicting the training median and the training mean, because what these three
    sentinels check is the protocol's bookkeeping -- which folds the search was shown, which
    fold produced the score, what the record says about both -- and that is answered by any
    contender that actually reads its folds. The model is card #26's, and when it exists this
    hook does not have to change: it is the protocol that is the subject, not the model run
    through it.

    Cached because it costs about a second -- keying 1,279 formulae, one split, and six
    stratifications over the training rows -- and ``audit()`` runs on every gate invocation
    and every test in ``tests/leaks/``.
    """
    from hydms.data.load import load_hydride_data
    from hydms.data.splits import assign_splits
    from hydms.surrogate.validation import Contender, nested_scores

    frame = load_hydride_data()
    contender = Contender(name="constant baseline", tune=_tune_baseline, score=_score_baseline)
    return frame, nested_scores(frame, assign_splits(frame), [contender])


def _l7_live() -> None:
    """Card #88's outer folds, over the real training rows. The wiring `unwired` demands.

    The keys handed to the detector come from `group_keys` here rather than from anything the
    fold set carries, exactly as `_l8_live` re-derives them: folds that had quietly grouped on
    something else would show up as a straddle rather than as agreement with themselves.
    """
    from hydms.data.canonical import group_keys

    frame, evaluation = _validation_run()
    keys = group_keys(frame)
    assert_disjoint_groups(
        {fold.name: keys.loc[list(fold.test)] for fold in evaluation.outer},
        what="cross-validation folds",
    )


def _l4_live() -> None:
    """The reported score came from outer folds the search never saw.

    The premise is checked before the conclusion. `assert_selection_is_nested` finds L4 by
    intersecting `tuned_on` with `scored_on`, which detects nothing at all if inner and outer
    ids were issued by two independent counters. So this first asks the run's own
    :class:`~hydms.surrogate.validation.FoldSpace` whether an outer fold's held-out
    compositions still resolve to that outer fold's id -- if they do, an inner fold holding
    the same materials would have collided with it, and the intersection below is a real
    question.
    """
    _, evaluation = _validation_run()
    for fold in evaluation.outer:
        issued = evaluation.space.known(fold.held_out)
        if issued != fold.id:
            raise ValueError(
                f"outer fold {fold.name!r} has id {fold.id} but its {len(fold.held_out)} "
                f"held-out composition(s) resolve to {issued!r} in the run's own fold space. "
                f"Ids are supposed to be issued for content; if they are not, tuned_on and "
                f"scored_on cannot intersect and this sentinel checks nothing."
            )
    assert_selection_is_nested(evaluation.records)


def _l2_live() -> None:
    """The selection record carries no metric from a split the protocol never touched.

    Stricter than the miniature above, deliberately. `assert_selection_is_nested` forbids a
    `test` metric by default; cross-validation here runs inside the training split, so a
    `val` metric could not have been computed either -- and a **validation** score published
    beside the choice it made is precisely what L2 is.
    """
    from hydms.surrogate.validation import HELD_OUT_SPLITS

    _, evaluation = _validation_run()
    assert_selection_is_nested(evaluation.records, holdout_splits=HELD_OUT_SPLITS)


def _l6_live() -> None:
    """Card #24's selector, over the real matrix, asked twice. The wiring `unwired` demands.

    `assert_selection_ignores_holdout` runs the subject rather than reading a record of it, so
    this hook only has to supply the real one and the rows it is entitled to: the whole
    1,278-row joined frame, and the 893 labels #13 assigns to `train`. The detector perturbs
    the other 385 -- shuffled within the held-out block, then rescaled -- and requires the
    same answer, order included.

    **The budget is reduced and that is stated where it lives**, on
    `hydms.surrogate.selection.SENTINEL_BUDGET`: Boruta at the configured `max_iter` costs 676
    seconds per call and this hook makes two, while HG-1 is a FAST gate. What is not reduced
    is anything L6 is about -- the frame, the training labels, the three stages or their order.

    Cached, like `_featurisation_run` and `_validation_run`: `audit()` runs on every gate
    invocation and on every test in `tests/leaks/`.
    """
    _l6_run()


@lru_cache(maxsize=1)
def _l6_run() -> None:
    """The measurement behind `_l6_live`. Separate so `lru_cache` holds the cost, not the hook.

    A raising call is not cached -- `lru_cache` stores no exception -- so a red sentinel is
    re-measured on every audit rather than remembered, which is the right way round.
    """
    from functools import partial

    from hydms.config import load as load_config
    from hydms.data.load import load_hydride_data, parse_formula
    from hydms.data.metadata import with_features, with_metadata
    from hydms.data.splits import assign_splits
    from hydms.descriptors.contract import CONTRACT, FeatureContract
    from hydms.descriptors.featurize import featurize
    from hydms.surrogate.selection import selected_names, sentinel_settings

    names = load_config().columns
    record = with_metadata(load_hydride_data())
    split = assign_splits(record)
    contract = FeatureContract.from_names(
        [name for name in CONTRACT.names if name != _GORDY]
    )
    keep = [
        label
        for label, formula in record[names.formula].items()
        if contract.computability(parse_formula(formula)).complete
    ]
    usable = record.loc[keep]
    frame = with_features(
        usable, featurize(usable[names.formula], usable[names.temperature], contract=contract)
    )
    training = [label for label in frame.index if split.loc[label] == "train"]
    held_out = [label for label in frame.index if label not in set(training)]
    if not training or not held_out:
        raise ValueError(
            f"the L6 live check needs rows on both sides of the line and has "
            f"{len(training)} training and {len(held_out)} held-out row(s). A selector "
            f"cannot be caught reading a holdout that is empty."
        )

    assert_selection_ignores_holdout(
        partial(selected_names, train=training, settings=sentinel_settings()),
        frame,
        holdout=held_out,
    )


# --------------------------------------------------------------------------------------
# L12 -- the sample weights
# --------------------------------------------------------------------------------------

_CAPACITY = "H2_W% (max)"


def _weighting_frame() -> Any:
    """Six rows straddling 3 wt%, the threshold the archival weighting was hand-tuned to.

    Two features and the target, because the whole question is which of the three columns a
    weighting reads.
    """
    pd = _pandas()
    return pd.DataFrame(
        {
            "avg_atomic_mass": [58.7, 47.9, 24.3, 91.2, 88.9, 140.1],
            "temperature(K)": [298.0, 303.0, 573.0, 323.0, 298.0, 598.0],
            _CAPACITY: [1.5, 2.0, 2.5, 3.5, 4.0, 5.0],
        },
        index=list(_ROW_LABELS),
    )


def _l12_weights_conditioned_on_the_target() -> None:
    """`Catboostmodel.py:516-518` -- np.where(np.expm1(y) > 3, 2.0, 1.0), rows weighted by y."""
    assert_weights_ignore_target(
        lambda frame: [2.0 if value > 3.0 else 1.0 for value in frame[_CAPACITY]],
        _weighting_frame(),
        target_column=_CAPACITY,
    )


def _l12_weights_conditioned_on_a_feature() -> None:
    """The same expression, one column to the left.

    The minimal difference the contract asks for: same ``np.where(x > threshold, 2, 1)``
    shape, same two weights, same rows -- only the column it reads changes. A twin that
    returned a flat 1.0 would also pass, and would prove less: it would leave open whether
    the detector objects to *thresholding* rather than to reading the answer.
    """
    assert_weights_ignore_target(
        lambda frame: [2.0 if value > 300.0 else 1.0 for value in frame["temperature(K)"]],
        _weighting_frame(),
        target_column=_CAPACITY,
    )


# --------------------------------------------------------------------------------------
# The real model -- card #26
# --------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _model_settings() -> Any:
    """Card #26's settings under its `SENTINEL_BUDGET`, and the matrix they describe."""
    from hydms.surrogate.model import sentinel_settings

    return sentinel_settings()


@lru_cache(maxsize=1)
def _model_matrix() -> tuple[Any, Any]:
    """The fourteen-feature matrix the capacity model is fitted on, and #13's split over it.

    `capacity_matrix` is the function the training command and card #34 call, so these hooks
    check the real matrix rather than one assembled a second way beside it.
    """
    from hydms.surrogate.model import capacity_matrix

    return capacity_matrix(settings=_model_settings())


@lru_cache(maxsize=1)
def _deployed_fit() -> Any:
    """The deployed fit, under the reduced budget. The model, cached, fitted once.

    **The budget is reduced and that is stated where it lives**, on
    `hydms.surrogate.model.SENTINEL_BUDGET`: a real trial grows up to 30,000 boosted trees and
    HG-1 is a FAST gate. What L1 asks is not affected by it. The question is which rows chose
    the stopping iteration and which rows the result is reported against, and a row identity
    does not depend on how many trees were grown. Nor is what L11 asks: which rows an
    explanation was computed over does not depend on the size of the ensemble explained.

    The model rather than its record, because the L11 hook has to *call* it -- SHAP reads the
    trees. One fit serves both hooks; `audit()` runs on every gate invocation and on every test
    in `tests/leaks/`.

    **It is `deploy.deployed_fit`, not `model.final_fit`, and the difference is the point.**
    The fit this project ships carves a calibration slice out of the screened training rows
    before growing a tree, so its `record.fitted` is a strictly smaller set than `final_fit`'s.
    L1 and L11 are questions about *the deployed fit*, so when the deployed fit moved these
    hooks moved with it; a sentinel aimed at a fit nothing ships is guarding in name only.
    `final_fit` is still the honest three-split fit and still has its own tests -- it is simply
    no longer what gets deployed.
    """
    from hydms.surrogate.deploy import deployed_fit

    frame, split = _model_matrix()
    return deployed_fit(frame, split, settings=_model_settings()).model


def _final_fit_record() -> Any:
    """What the deployed fit stopped on and was scored on. `_deployed_fit`'s record."""
    return _deployed_fit().record


@lru_cache(maxsize=1)
def _model_run() -> tuple[Any, Any]:
    """Card #88's nested protocol with card #26's model in it. The evaluation, and every fit.

    Every fit, including the search's: `log_trials=True` is affordable here and only here,
    because `SENTINEL_BUDGET` cuts the search to two trials. So the L5 hook below checks the
    real thing -- each of the fits a fold actually made -- rather than the five that scored.

    Cached, like `_validation_run` and `_l6_run`: `audit()` runs on every gate invocation and
    on every test in `tests/leaks/`.
    """
    from hydms.surrogate.model import FitLog, capacity_contender
    from hydms.surrogate.validation import nested_scores

    frame, split = _model_matrix()
    settings = _model_settings()
    log = FitLog()
    evaluation = nested_scores(
        frame,
        split,
        [capacity_contender(settings=settings, log=log, log_trials=True)],
    )
    return evaluation, log


def _l1_live() -> None:
    """The deployed fit stopped on the validation split, and is reported on the test split.

    The premise is checked before the conclusion, as `_l4_live` does. `assert_early_stopping_
    is_honest` compares two sets of row labels, and would pass just as happily on two sets
    that were not the splits at all -- an eval set quietly cut out of the training rows would
    satisfy it while leaving `val` unused and the audit's arrangement unexamined. So this
    first asks whether the fit's eval set *is* the validation split and its scored rows *are*
    the test split, and only then asks whether they overlap.
    """
    frame, split = _model_matrix()
    record = _final_fit_record()
    expected = {
        "eval_on": set(frame.index[split == "val"]),
        "scored_on": set(frame.index[split == "test"]),
    }
    for field, wanted in expected.items():
        got = set(getattr(record, field))
        if got != wanted:
            raise ValueError(
                f"the final fit's {field} is {len(got)} row(s) where the split assigns "
                f"{len(wanted)}, differing on {len(got ^ wanted)}. This hook checks the "
                f"arrangement L1 is about -- stop on val, report on test -- and it cannot "
                f"check an arrangement the fit did not use."
            )
    assert_early_stopping_is_honest(
        eval_rows=record.eval_on,
        scored_rows=record.scored_on,
        use_best_model=True,
        where=record.where,
    )


def _l5_live() -> None:
    """No fit inside the protocol early-stops on rows it is scored on, or on a held-out split.

    Two questions, and the second is not the detector's. `assert_early_stopping_is_honest`
    runs once per recorded fit -- the search's as well as the five that scored, since
    `_model_run` logs them all. But a fit could satisfy it and still be dishonest in the way
    L1 was, by stopping on rows from `val` or `test`: those are disjoint from an inner fold's
    scored rows, so the detector would pass them. Cross-validation is entitled to the
    training split and nothing else, so that is asserted here directly.
    """
    frame, split = _model_matrix()
    evaluation, log = _model_run()
    if not log.records:
        raise ValueError(
            "the nested run recorded no fits, so this hook checked nothing. It reads "
            "hydms.surrogate.model.FitLog, which capacity_contender fills."
        )

    held_out = set(frame.index[split != "train"])
    for record in log.records:
        assert_early_stopping_is_honest(
            eval_rows=record.eval_on,
            scored_rows=record.scored_on,
            use_best_model=True,
            where=record.where,
        )
        reached = held_out.intersection(record.eval_on) | held_out.intersection(record.fitted)
        if reached:
            raise LeakDetected(
                f"{record.where}: {len(reached)} row(s) from a held-out split were used to "
                f"fit or to stop a cross-validation fit. Cross-validation runs inside the "
                f"training split; a fold that stops on `val` passes the disjointness check "
                f"and is still leak L1's arrangement (leak L5)."
            )

    scored = {frozenset(record.scored_on) for record in log.records}
    for fold in evaluation.outer:
        if frozenset(fold.test) not in scored:
            raise ValueError(
                f"outer fold {fold.name!r} holds out {len(fold.test)} row(s) that no recorded "
                f"fit was scored on. The log is what this hook checks, so a fold missing from "
                f"it is a fold nobody checked."
            )


def _l12_live() -> None:
    """The real weighting function, over the real matrix, cannot see the target.

    `assert_weights_ignore_target` runs the subject rather than reading a record of it, so
    this hook supplies `hydms.surrogate.model.sample_weights` itself -- bound to the settings
    a fit binds it to, which is where the decision to slice the frame down to the declared
    features lives. Perturbing the capacity column must leave every weight where it was.

    The cheapest of the live checks: a weighting function fits nothing, so this costs two
    calls and no model.
    """
    from functools import partial

    from hydms.config import load as load_config
    from hydms.surrogate.model import sample_weights

    frame, _ = _model_matrix()
    assert_weights_ignore_target(
        partial(sample_weights, settings=_model_settings()),
        frame,
        target_column=load_config().columns.target,
    )

# --------------------------------------------------------------------------------------
# L11 -- explainability
# --------------------------------------------------------------------------------------

_EXPLAINED_FEATURES = ("avg_atomic_mass", "temperature(K)")


def _explanation(computed_on: str) -> Any:
    """A SHAP record in miniature: one row per feature, naming the rows it came from."""
    pd = _pandas()
    return pd.DataFrame(
        {
            "feature": list(_EXPLAINED_FEATURES),
            "mean_abs_shap": [0.31, 0.12],
            "computed_on": [computed_on] * len(_EXPLAINED_FEATURES),
        }
    )


def _l11_explained_on_the_test_split() -> None:
    """`benchmark_model_selection.py:1375,1383,1394` -- shap_values(X_test), pdp on X_test."""
    assert_explanation_is_not_held_out(
        _explanation("test"), held_out=("val", "test"), where="the SHAP record"
    )


def _l11_explained_on_the_training_rows() -> None:
    assert_explanation_is_not_held_out(
        _explanation("train"), held_out=("val", "test"), where="the SHAP record"
    )


def _l11_explanation_names_nothing() -> None:
    """The archival state proper: a plot, and no record of which rows produced it.

    Not the same failure as naming ``test``, and worth its own reproduction: a record with no
    ``computed_on`` column passes any check that only looks at values, and it is what the
    archival script actually left behind.
    """
    record = _explanation("train").drop(columns=["computed_on"])
    assert_explanation_is_not_held_out(
        record, held_out=("val", "test"), where="the SHAP record"
    )


@lru_cache(maxsize=1)
def _explainability_record() -> tuple[Any, Any]:
    """The real SHAP and partial-dependence tables of the deployed fit, under the reduced budget.

    The rows are `model.record.fitted` -- the rows this fit actually grew on, read off the
    fit's own record rather than re-derived from the split, because screening drops some of the
    training rows and an explanation averaged over rows the model never saw is a different
    object from the one REPORT section 6.1 claims to be.

    Cached beside `_final_fit_record`, whose fit it shares.
    """
    from hydms.surrogate.evaluate import EXPLAINABILITY, pdp_table, shap_table

    frame, _ = _model_matrix()
    model = _deployed_fit()
    rows = frame.loc[list(model.record.fitted)]
    return (
        shap_table(model, rows, computed_on=EXPLAINABILITY),
        pdp_table(model, rows, computed_on=EXPLAINABILITY),
    )


def _l11_live() -> None:
    """The real explainability tables name the training rows, and cover every fitted feature.

    The premise before the conclusion, as `_l1_live` and `_l4_live` do.
    `assert_explanation_is_not_held_out` reads one column, and would pass just as happily on a
    record that explained *nothing* -- an empty table, or one covering three of fourteen
    features -- while `computed_on` said `train`. A partial explanation published as the
    model's explanation is a smaller version of the same misreading L11 is about, so this first
    asks whether the record covers the model's own feature set, and only then whether the rows
    it came from were held out.
    """
    from hydms.surrogate.validation import HELD_OUT_SPLITS

    shap, pdp = _explainability_record()
    model = _deployed_fit()
    expected = set(model.feature_names)
    for name, record in (("SHAP", shap), ("partial dependence", pdp)):
        covered = set(record["feature"])
        if covered != expected:
            raise ValueError(
                f"the {name} record covers {len(covered)} of the model's "
                f"{len(expected)} fitted feature(s), differing on "
                f"{len(covered ^ expected)}. This hook checks a record of the whole model, "
                f"and it cannot check one that explains part of it."
            )
        assert_explanation_is_not_held_out(
            record, held_out=HELD_OUT_SPLITS, where=f"the {name} record"
        )


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
        live=_l1_live,
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
        live=_l2_live,
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
        live=_l3_live,
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
        live=_l4_live,
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
        live=_l5_live,
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
        live=_l6_live,
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
        live=_l7_live,
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
        live=_l8_live,
    ),
    Sentinel(
        leak="L9",
        title="the merge joins on a key and refuses a row it cannot cover",
        detector="hydms.qa.detectors.assert_merge_is_keyed",
        subject="hydms.data.merge",
        reproductions=(
            Reproduction("positional concat", _l9_positional_merge, _l9_keyed_merge),
        ),
        live=_l9_live,
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
        live=_l10_live,
    ),
    Sentinel(
        leak="L11",
        title="the explainability record names the rows it ran on, and they are not held out",
        detector="hydms.qa.detectors.assert_explanation_is_not_held_out",
        subject="hydms.surrogate.evaluate",
        reproductions=(
            Reproduction(
                "SHAP and PDP computed on the test split",
                _l11_explained_on_the_test_split,
                _l11_explained_on_the_training_rows,
            ),
            Reproduction(
                "an explanation with no record of what it ran on",
                _l11_explanation_names_nothing,
                _l11_explained_on_the_training_rows,
            ),
        ),
        live=_l11_live,
    ),
    Sentinel(
        leak="L12",
        title="sample weights are blind to the target",
        detector="hydms.qa.detectors.assert_weights_ignore_target",
        subject="hydms.surrogate.model",
        reproductions=(
            Reproduction(
                "rows weighted by their own capacity, at a hand-tuned threshold",
                _l12_weights_conditioned_on_the_target,
                _l12_weights_conditioned_on_a_feature,
            ),
        ),
        live=_l12_live,
    ),
    Sentinel(
        leak="L13",
        title="Alloy_class survives featurisation for every row",
        detector="hydms.qa.detectors.assert_metadata_survives",
        subject="hydms.descriptors.featurize",
        reproductions=(
            Reproduction(
                "every object column but the formula dropped",
                _l13_alloy_class_dropped,
                _l13_alloy_class_carried_through,
            ),
            Reproduction(
                "one row's class lost while the column survives",
                _l13_a_row_loses_its_class,
                _l13_alloy_class_carried_through,
            ),
        ),
        live=_l13_live,
    ),
)


#: Empty, and that is the point: every leak in the inventory now has a sentinel.
#:
#: L11 was the last entry here. It was deferred rather than omitted because a sentinel needs a
#: record to assert against, and no explainability record existed until card #29 decided what
#: SHAP and partial dependence are computed on. That decision is
#: :data:`hydms.surrogate.evaluate.EXPLAINABILITY`, and the sentinel above reads it.
#:
#: The shape stays. A gap nobody wrote down is indistinguishable from coverage, and the next
#: leak this project finds should be recorded here on the day it is found rather than on the
#: day somebody has time to guard it.
DEFERRED: tuple[Deferral, ...] = ()


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
