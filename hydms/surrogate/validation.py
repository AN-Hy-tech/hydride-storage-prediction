"""L3 -- the folds, and the guarantee that the data which produced a score never chose it.

Two leaks share one root, and this module is the shape both are fixed by.

**L7** ``benchmark_model_selection.py:895`` folds *rows*::

    kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for train_idx, val_idx in kf.split(X_train, y_binned):

No ``groups=``. Measured on the reproduced training split, 141 of 896 rows have their exact
formula in another fold, and that is the count under the **raw string** -- the canonical key
merges spellings the string kept apart, so the true figure can only be higher. Every selected
feature is a composition statistic or the temperature (PRD section 2.3), so a colliding row
carries a feature vector identical to a training row up to temperature. Some compositions
appear six times at six temperatures with one identical descriptor vector. That is not a
near-duplicate problem; it is the same point on both sides of the line.

**L4** ``benchmark_model_selection.py:1156`` builds one ``splits`` object, tunes with it, and
then at ``:1168`` reports a score from it. The published ``CV_R2_Mean`` is a tuning optimum.
**L2** ``:335-336`` is the same defect one level up: the four ensemble members were chosen by
``nlargest(4, 'Val_Weighted_Orig')`` and the headline Val R2 0.939 was then published, with a
bootstrap interval, on that same validation set.

Four decisions worth stating rather than reading out of the arithmetic.

**The unit is the material, not the spelling.**
:func:`~hydms.data.canonical.group_keys` is *called*, never re-derived -- the same function
card #13 splits on and card #12 joins ``Alloy_class`` on. Grouping on the raw string, on
``str.strip()`` of it, or on a ``groupby`` of the parsed composition are three different
answers to "the same material", and a project with three answers has none.
:func:`~hydms.qa.detectors.assert_disjoint_groups` -- the detector gate HG-1 reads -- runs
over the folds before they are returned, so a caller cannot receive a leaking fold set.

**A fold id is not a counter.** :class:`~hydms.qa.detectors.SelectionRecord` records which
folds tuned a model and which folds scored it, and
:func:`~hydms.qa.detectors.assert_selection_is_nested` fires when those two sets intersect.
If inner and outer ids came from two independent counters that intersection would be empty by
construction and the detector would be decoration. So an id is issued *for the set of
canonical compositions the fold holds out* (:class:`FoldSpace`): ask twice for the same set
and you get the same id back. A protocol that tunes on the folds it then scores on produces a
record whose two sets overlap, and L4 fires on it. ``tests/surrogate/test_validation.py``
measures that the guard is not vacuous rather than trusting this paragraph.

**What the tuner saw is measured, not assumed.** :attr:`TuningTask.folds` records every fold
that is read. ``tuned_on`` is therefore the folds the hyperparameter search *actually*
touched, and a search that touched none is refused -- it tuned on something nobody wrote down,
which is the state the archival pipeline was in. The tuner is handed a frame holding the outer
fold's training rows and nothing else, so it cannot reach the rows it will be scored on even
if it tries.

**Cross-validation never sees the held-out splits.** :func:`nested_scores` takes the whole
matrix *and* card #13's split assignment and selects the training rows itself, exactly as
:func:`~hydms.surrogate.scaler.fit_scaler` does, refusing a split that holds nothing out. It
follows that a metric named after ``val`` or ``test`` cannot have been computed inside the
protocol, so both names are refused in a record -- which is stricter than
:func:`~hydms.qa.detectors.assert_selection_is_nested`'s default of ``("test",)``, and
deliberately: what L2 published was a **validation** score.

The stratification is card #13's, :func:`~hydms.data.splits.stratify`, and it is recomputed
for every fold set from the rows that set is allowed to see. Quantile bins of the target are a
function of the targets they are computed over; taking them once over the whole training
matrix would let the held-out rows of every fold shape the folds. It costs about 35 ms per
call on the real training split.

Card #88.
"""

from __future__ import annotations

from collections.abc import Callable, Hashable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial
from typing import Any

import pandas as pd

from hydms.config import Split as SplitSettings
from hydms.config import load as load_config
from hydms.data.canonical import alloy_classes, group_keys
from hydms.data.splits import SPLIT_NAMES, stratify
from hydms.qa import SelectionRecord, assert_disjoint_groups, assert_selection_is_nested

# "train" spelled once in the surrogate layer, for the reason card #23 wrote beside it: a bare
# string in two modules is how one of them comes to mean something slightly different.
from hydms.surrogate.scaler import TRAIN

__all__ = [
    "HELD_OUT_SPLITS",
    "OUTER_FOLDS",
    "Contender",
    "Evaluation",
    "Fold",
    "FoldSet",
    "FoldSpace",
    "ScoringTask",
    "TuningTask",
    "ValidationError",
    "grouped_folds",
    "leave_one_class_out",
    "nested_scores",
]

# A failure that names two hundred folds is a failure nobody reads to the end. Same convention
# as `hydms/data/metadata.py`, `hydms/surrogate/scaler.py` and `hydms/qa/detectors.py`.
_MAX_NAMED = 8

#: The splits cross-validation must never touch, and therefore the metric names a selection
#: record may not carry. Derived from :data:`~hydms.data.splits.SPLIT_NAMES` rather than
#: written out, so adding a fourth split cannot leave this list quietly behind.
HELD_OUT_SPLITS: tuple[str, ...] = tuple(name for name in SPLIT_NAMES if name != TRAIN)


class ValidationError(ValueError):
    """The protocol cannot run, or a caller handed it something it must refuse.

    A ``ValueError``, like :class:`~hydms.data.splits.SplitError` and
    :class:`~hydms.surrogate.scaler.ScalerError` beside it: a guard refusing, naming what it
    refused. The *leak* detectors for the same defects are
    :func:`~hydms.qa.detectors.assert_disjoint_groups` and
    :func:`~hydms.qa.detectors.assert_selection_is_nested`, which raise
    :class:`~hydms.qa.detectors.LeakDetected` and are what gate HG-1 reads.
    """


def _named(items: Iterable[object]) -> str:
    """Render offenders for a message: sorted, truncated, and counted."""
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


def _splitter() -> Any:
    """Import ``StratifiedGroupKFold`` at call time, with a message saying what it is for.

    Deferred for the same reason :func:`hydms.data.splits._sklearn` defers its imports:
    ``python -m hydms.gates list`` and the board scripts must stay answerable on an
    interpreter with no scientific stack.
    """
    try:
        from sklearn.model_selection import StratifiedGroupKFold
    except ImportError as exc:  # pragma: no cover -- exercised only on a bare interpreter
        raise ValidationError(
            "the fold generator is scikit-learn's StratifiedGroupKFold, and it is not "
            "importable here. It is a core dependency; see docs/ENVIRONMENT.md."
        ) from exc
    return StratifiedGroupKFold


# --------------------------------------------------------------------------------------
# Folds
# --------------------------------------------------------------------------------------


class FoldSpace:
    """The numbering that makes two folds *the same fold* when they hold out the same materials.

    Ids are issued for content -- the frozen set of canonical composition keys a fold holds
    out -- and not by counting. That is what gives
    :func:`~hydms.qa.detectors.assert_selection_is_nested` something to detect: an inner fold
    that happens to hold out exactly what an outer fold holds out receives the outer fold's
    id, so a protocol that tunes on the folds it scores on writes a record whose ``tuned_on``
    and ``scored_on`` intersect. With two independent counters the same record would look
    perfectly nested.

    One space is created per :func:`nested_scores` run and threaded through every fold set it
    builds, which is the scope over which two ids need to be comparable. A fold set built on
    its own gets a fresh space, and therefore the readable ``0, 1, 2, ...`` of its own
    generation order.
    """

    def __init__(self) -> None:
        self._issued: dict[frozenset[str], int] = {}

    def identify(self, held_out: Iterable[str]) -> int:
        """The id of the fold holding out exactly these keys, issuing one if it is new."""
        content = frozenset(held_out)
        if content not in self._issued:
            self._issued[content] = len(self._issued)
        return self._issued[content]

    def known(self, held_out: Iterable[str]) -> int | None:
        """The id already issued for these keys, or ``None``. Never issues one.

        The read-only half, so that a check *of* the numbering -- the L4 sentinel asks whether
        an outer fold's content still resolves to the outer fold's id -- cannot change what it
        is measuring.
        """
        return self._issued.get(frozenset(held_out))

    def __len__(self) -> int:
        return len(self._issued)


@dataclass(frozen=True)
class Fold:
    """One train/test partition of a frame, addressed by what it holds out.

    Attributes:
        id: Issued by a :class:`FoldSpace`. Two folds holding out the same materials share
            one, whatever set they belong to -- see that class for why.
        name: For messages and for the per-fold table: ``"outer-2"``, ``"class:AB5"``.
        train: Row labels the model may fit on.
        test: Row labels it is scored on.
        held_out: The canonical composition keys in :attr:`test`.
    """

    id: int
    name: str
    train: tuple[Hashable, ...]
    test: tuple[Hashable, ...]
    held_out: frozenset[str]


@dataclass(frozen=True)
class FoldSet:
    """An ordered partition of one frame, with its own disjointness already asserted.

    Attributes:
        name: What the set is: ``"outer"``, ``"outer-0-inner"``, ``"class"``.
        folds: In generation order, which is a function of the seed and the data alone.
        grouped_on: What the folds keep together, for the failure message: the canonical
            composition, or the alloy class.
    """

    name: str
    folds: tuple[Fold, ...]
    grouped_on: str = "canonical composition"

    def __iter__(self) -> Iterator[Fold]:
        return iter(self.folds)

    def __len__(self) -> int:
        return len(self.folds)

    def __getitem__(self, index: int) -> Fold:
        return self.folds[index]

    def ids(self) -> frozenset[int]:
        """The fold ids, as a :class:`~hydms.qa.detectors.SelectionRecord` wants them."""
        return frozenset(fold.id for fold in self.folds)

    def assignments(self) -> dict[str, frozenset[str]]:
        """Fold name -> the keys it holds out, ready for
        :func:`~hydms.qa.detectors.assert_disjoint_groups`."""
        return {fold.name: fold.held_out for fold in self.folds}


def _complete(folds: Sequence[Fold], frame: pd.DataFrame, *, name: str) -> None:
    """Every row is held out exactly once, and no fold is empty on either side.

    A partition that quietly drops rows scores a model on less than it claims to, and a fold
    with an empty side is a fit or a score that never happened. Both are cheap to check and
    neither is visible in the numbers afterwards.
    """
    held = sum(len(fold.test) for fold in folds)
    if held != len(frame):
        raise ValidationError(
            f"the {name} folds hold out {held} row(s) between them, but the frame has "
            f"{len(frame)}. Every row belongs to exactly one test fold; a partition that "
            f"loses rows reports a score over data it never saw."
        )
    empty = [fold.name for fold in folds if not fold.train or not fold.test]
    if empty:
        raise ValidationError(
            f"{len(empty)} of the {name} folds are empty on one side: {_named(empty)}. "
            f"A fold with no training rows is a fit that never happened; one with no test "
            f"rows is a score that never happened."
        )


def _assemble(
    frame: pd.DataFrame,
    keys: pd.Series,
    partitions: Iterable[tuple[str, Sequence[Hashable]]],
    *,
    space: FoldSpace,
    name: str,
    grouped_on: str,
) -> FoldSet:
    """Turn held-out row labels into a checked :class:`FoldSet`.

    The one place a fold is constructed, so the disjointness assertion and the completeness
    check cannot be skipped by adding a second generator later.
    """
    labels = list(frame.index)
    folds: list[Fold] = []
    for fold_name, test_labels in partitions:
        test = tuple(test_labels)
        held_labels = set(test)
        held = frozenset(keys.loc[list(test)])
        train = tuple(label for label in labels if label not in held_labels)
        folds.append(
            Fold(id=space.identify(held), name=fold_name, train=train, test=test, held_out=held)
        )

    if len(folds) < 2:
        raise ValidationError(
            f"a {name} fold set needs at least two folds to be a partition; got {len(folds)}. "
            f"Nothing can straddle one fold, so its disjointness would mean nothing."
        )

    _complete(folds, frame, name=name)
    assert_disjoint_groups(
        {fold.name: fold.held_out for fold in folds},
        what="cross-validation folds",
        key_name=grouped_on,
    )
    return FoldSet(name=name, folds=tuple(folds), grouped_on=grouped_on)


def grouped_folds(
    frame: pd.DataFrame,
    space: FoldSpace | None = None,
    *,
    splits: int | None = None,
    seed: int | None = None,
    name: str = "fold",
    formula_column: str | None = None,
    settings: SplitSettings | None = None,
) -> FoldSet:
    """``StratifiedGroupKFold`` over the canonical compositions of ``frame``.

    The project's fold generator. Groups are
    :func:`~hydms.data.canonical.group_keys` -- called, so that "the same material" has one
    definition -- and the stratification is card #13's
    :func:`~hydms.data.splits.stratify`, computed over ``frame`` alone.

    Args:
        frame: The rows to partition. For a nested run this is the outer fold's training
            rows; it must never be the whole dataset -- see :func:`nested_scores`.
        space: The numbering to draw ids from. A fresh one by default, which is right for a
            fold set nothing will be compared against.
        splits: Number of folds. Defaults to ``model.cv_folds`` in ``pipeline.yaml``.
        seed: Defaults to ``seed``. The same seed over the same rows reproduces the folds
            exactly, which is what AC-1 asks of every stochastic step.
        name: Prefix for the fold names, and the name of the set.
        formula_column: Defaults to ``columns.formula``.
        settings: Bin counts and the minimum stratum size, defaulting to ``pipeline.yaml``'s.
            ``split.min_stratum_size`` is 5 and ``model.cv_folds`` is 5: every stratum
            therefore holds at least as many compositions as there are folds, which is what
            keeps ``StratifiedGroupKFold`` from having to place a stratum it cannot divide.

    Returns:
        A :class:`FoldSet` whose disjointness has already been asserted.

    Raises:
        ValidationError: Fewer than two folds were asked for, or there are fewer distinct
            compositions than folds.
        LeakDetected: A composition landed in two folds -- leak L7. Raised rather than
            returned: there is nothing useful to do with a leaking fold set.
        SplitError: A stratum cannot be divided; see :func:`~hydms.data.splits.stratify`.
        CanonicalisationError: A row cannot be given a canonical key.
    """
    config = load_config()
    count = config.model.cv_folds if splits is None else splits
    rng_seed = config.seed if seed is None else seed

    if count < 2:
        raise ValidationError(
            f"{name}: cross-validation needs at least two folds, got {count}. One fold is "
            f"not a partition, and nothing can be held out of it."
        )

    keys = group_keys(frame, formula_column)
    distinct = keys.nunique()
    if distinct < count:
        raise ValidationError(
            f"{name}: {distinct} distinct composition(s) cannot be divided into {count} "
            f"group-disjoint fold(s). The unit is the material, not the row -- {len(frame)} "
            f"row(s) describe those {distinct} compositions."
        )

    strata = stratify(frame, formula_column=formula_column, settings=settings)
    labels = list(frame.index)
    splitter = _splitter()(n_splits=count, shuffle=True, random_state=rng_seed)
    partitions = [
        (f"{name}-{position}", [labels[at] for at in test_at])
        for position, (_, test_at) in enumerate(
            splitter.split(frame, keys.map(strata), groups=keys)
        )
    ]
    return _assemble(
        frame,
        keys,
        partitions,
        space=space if space is not None else FoldSpace(),
        name=name,
        grouped_on="canonical composition",
    )


def leave_one_class_out(
    frame: pd.DataFrame,
    space: FoldSpace | None = None,
    *,
    name: str = "class",
    formula_column: str | None = None,
    class_column: str | None = None,
    aliases: Mapping[str, str] | None = None,
) -> FoldSet:
    """One fold per alloy class, holding out every row of it. AC-6, card #30.

    The same interface as :func:`grouped_folds` and the same guarantees, so #30's protocol is
    this module's protocol with the outer partition swapped -- not a second, parallel way of
    scoring a model. The labels are :func:`~hydms.data.canonical.alloy_classes`, reconciled
    per canonical composition, so a class fold holds out every spelling of every material in
    the class; a composition that carried two labels in the file would otherwise put the same
    material in two folds, which is leak L7 wearing a different hat.

    Args:
        frame: The rows to partition, with a formula column and a class column.
        space: As :func:`grouped_folds`.
        name: Prefix for the fold names; folds are named ``"<name>:<label>"``.
        formula_column: Defaults to ``columns.formula``.
        class_column: Defaults to ``columns.alloy_class``.
        aliases: Applied before reconciliation, for a source whose vocabulary is not the
            curated one.

    Returns:
        A :class:`FoldSet` with one fold per class, in label order.

    Raises:
        ValidationError: Fewer than two classes are present.
        LeakDetected: A composition appears under two classes.
        CanonicalisationError: A row cannot be keyed, or carries a label outside the curated
            vocabulary.
    """
    keys = group_keys(frame, formula_column)
    classes = alloy_classes(
        frame, formula_column=formula_column, class_column=class_column, aliases=aliases
    )
    labels = sorted(set(classes))
    if len(labels) < 2:
        raise ValidationError(
            f"leave-one-alloy-class-out needs at least two classes, and the frame holds "
            f"{_named(labels)}. With one class the held-out fold is the whole dataset."
        )

    partitions = [
        (f"{name}:{label}", list(classes.index[classes == label])) for label in labels
    ]
    return _assemble(
        frame,
        keys,
        partitions,
        space=space if space is not None else FoldSpace(),
        name=name,
        grouped_on="canonical composition",
    )


# --------------------------------------------------------------------------------------
# The nested protocol
# --------------------------------------------------------------------------------------


#: The default outer cut of the nested protocol: :func:`grouped_folds` under the name
#: ``outer``, so folds read ``outer-0 ...`` in every record and message. Card #30 passes
#: :func:`leave_one_class_out` here instead, and nothing else about the protocol changes.
OUTER_FOLDS: Callable[[pd.DataFrame, FoldSpace], FoldSet] = partial(grouped_folds, name="outer")



class _WatchedFolds(Sequence[Fold]):
    """The inner folds, recording which of them were read.

    So that ``tuned_on`` is a measurement rather than a claim. A tuner that iterates every
    fold records every fold; one that reads none records none, and :func:`nested_scores`
    refuses the result -- a search that ignored the folds it was given tuned on something
    nobody wrote down.

    It cannot catch a tuner that goes around the folds entirely and rebuilds its own from the
    frame. Nothing short of taking the frame away can, and the frame is what a tuner needs;
    the guard here is against the accident, not the determined caller. The frame it is handed
    holds the outer fold's training rows and nothing else, so even that caller cannot reach
    the rows it will be scored on.
    """

    def __init__(self, folds: Sequence[Fold]) -> None:
        self._folds = tuple(folds)
        self.touched: set[int] = set()

    def __len__(self) -> int:
        return len(self._folds)

    def __getitem__(self, index: Any) -> Any:
        # `Any` rather than the overloaded `int | slice` of the `Sequence` protocol: a
        # faithful pair of overloads here would be four lines of typing ceremony guarding a
        # two-line body.
        selected = self._folds[index]
        for fold in selected if isinstance(selected, tuple) else (selected,):
            self.touched.add(fold.id)
        return selected

    def __iter__(self) -> Iterator[Fold]:
        for fold in self._folds:
            self.touched.add(fold.id)
            yield fold


@dataclass(frozen=True)
class TuningTask:
    """Everything the hyperparameter search is allowed to see, and nothing else.

    Attributes:
        frame: The outer fold's **training** rows. Not the dataset, not the training split --
            the rows this outer fold permits.
        folds: The inner folds over those rows. Reading one is recorded; see
            :class:`_WatchedFolds`.
        outer: The name of the outer fold this search belongs to, for messages.
    """

    frame: pd.DataFrame
    folds: Sequence[Fold]
    outer: str


@dataclass(frozen=True)
class ScoringTask:
    """The one fit that is scored: refit on the outer fold's training rows, scored on its test.

    Attributes:
        train: The outer fold's training rows -- the same rows the search saw.
        test: The outer fold's held-out rows, seen here for the first time.
        fold: The outer fold itself, whose id lands in the record's ``scored_on``.
    """

    train: pd.DataFrame
    test: pd.DataFrame
    fold: Fold


@dataclass(frozen=True)
class Contender:
    """One model in the comparison: how it is tuned, and how it is scored.

    Two callables rather than a class, because the protocol needs exactly two moments from a
    model and inheriting anything else would let a model reach past them.

    Attributes:
        name: What appears in the :class:`~hydms.qa.detectors.SelectionRecord`.
        tune: Given a :class:`TuningTask`, returns whatever configuration it chose. The
            protocol stores it and never inspects it.
        score: Given that configuration and a :class:`ScoringTask`, returns metrics by name.
            A metric named after a held-out split is refused -- see :data:`HELD_OUT_SPLITS`.
    """

    name: str
    tune: Callable[[TuningTask], Any]
    score: Callable[[Any, ScoringTask], Mapping[str, float]]


@dataclass(frozen=True)
class Evaluation:
    """What a nested run concluded, and the evidence a later reader checks it with.

    Attributes:
        records: One :class:`~hydms.qa.detectors.SelectionRecord` per contender, already
            asserted nested. This is what card #26 chooses from and what the L2 and L4
            sentinels read.
        outer: The outer folds the scores came from.
        per_fold: One row per (model, outer fold), with the metrics that fold produced.
            ``records`` is the mean of it; this is the spread behind that mean.
        chosen: The configuration each contender's search settled on, by
            ``(model, outer fold name)``. Without it a nested result is unusable: nothing
            says which hyperparameters won.
        space: The numbering the ids were drawn from, so a reader can ask whether two ids
            could have collided rather than assuming they could not.
    """

    records: tuple[SelectionRecord, ...]
    outer: FoldSet
    per_fold: pd.DataFrame
    chosen: Mapping[tuple[str, str], Any] = field(default_factory=dict)
    space: FoldSpace = field(default_factory=FoldSpace)

    def record(self, model: str) -> SelectionRecord:
        """The record for one contender.

        Raises:
            KeyError: No such contender. Loud on purpose, as
                :func:`~hydms.qa.leaks.by_id` is: a lookup that silently returns nothing is
                how a comparison comes to be reported over a model it never ran.
        """
        for entry in self.records:
            if entry.model == model:
                return entry
        known = ", ".join(entry.model for entry in self.records)
        raise KeyError(f"no record for {model!r}. The evaluation compared: {known}")


def _metrics(value: Mapping[str, float], *, model: str, fold: str) -> dict[str, float]:
    """Check one fold's metrics before they enter a record."""
    if not value:
        raise ValidationError(
            f"{model!r} returned no metric for fold {fold!r}. A fold that scores nothing "
            f"cannot be part of a comparison; it is a fit whose result nobody wrote down."
        )
    checked: dict[str, float] = {}
    for key, number in value.items():
        if not isinstance(key, str):
            raise ValidationError(
                f"{model!r} returned a metric keyed by {key!r} on fold {fold!r}. Metric "
                f"names are strings -- they are split names in the record."
            )
        # A type, not a `float()` call: `float("0.94")` succeeds, and a metric that arrived
        # as text means something upstream stringified a score. `bool` is an `int` and is
        # not a metric.
        if isinstance(number, bool) or not isinstance(number, int | float):
            raise ValidationError(
                f"{model!r} returned {number!r} for metric {key!r} on fold {fold!r}, which "
                f"is not a number."
            )
        checked[key] = float(number)
    return checked


def _averaged(scores: Sequence[Mapping[str, float]], *, model: str) -> dict[str, float]:
    """The mean of each metric across the outer folds, refusing a moving metric set."""
    names = {frozenset(entry) for entry in scores}
    if len(names) > 1:
        raise ValidationError(
            f"{model!r} reported different metrics on different outer folds: "
            f"{_named(tuple(sorted(sorted(entry)) for entry in names))}. A mean over folds "
            f"that measured different things is not a score."
        )
    return {
        key: sum(entry[key] for entry in scores) / len(scores) for key in sorted(scores[0])
    }


def nested_scores(
    frame: pd.DataFrame,
    split: pd.Series,
    contenders: Sequence[Contender],
    *,
    outer: Callable[[pd.DataFrame, FoldSpace], FoldSet] = OUTER_FOLDS,
    inner_splits: int | None = None,
    seed: int | None = None,
    settings: SplitSettings | None = None,
    holdout_splits: Sequence[str] = HELD_OUT_SPLITS,
) -> Evaluation:
    """Tune on inner folds, score on an outer fold the search never saw.

    The whole protocol, in one call, so that no caller has to assemble it -- assembling it is
    where L4 came from. For every outer fold: inner folds are cut from that fold's training
    rows, each contender's search is handed those and nothing else, and the configuration it
    returns is scored on the outer fold's held-out rows. The result is one record per
    contender, checked with :func:`~hydms.qa.detectors.assert_selection_is_nested` before it
    is returned.

    Args:
        frame: The whole matrix, with its formula, temperature and target columns. Handing
            in a pre-filtered training subset is the one call this guard is shaped to refuse
            -- like :func:`~hydms.surrogate.scaler.fit_scaler`, it selects the rows itself.
        split: Card #13's assignment, from
            :func:`~hydms.data.splits.assign_splits`, indexed as ``frame`` is.
        contenders: The models being compared. One is legitimate -- the record still says
            what tuned it and what scored it.
        outer: How the outer partition is cut. :data:`OUTER_FOLDS` by default;
            :func:`leave_one_class_out` gives card #30's AC-6 protocol through this same
            path.
        inner_splits: Number of inner folds. Defaults to ``model.inner_cv_folds``.
        seed: Defaults to ``seed`` in ``pipeline.yaml``.
        settings: Passed to the stratification of the inner folds.
        holdout_splits: Metric names a record may not carry. Defaults to every split that is
            not ``train`` -- see this module's docstring.

    Returns:
        An :class:`Evaluation`.

    Raises:
        ValidationError: The split holds nothing out, a contender's search read no fold, a
            fold scored nothing, or no contender was given.
        LeakDetected: The records are not nested, or carry a held-out metric -- leaks L4 and
            L2.
    """
    if not contenders:
        raise ValidationError(
            "nested_scores was given no contenders. An empty comparison is not a clean one; "
            "it is a choice nobody wrote down."
        )
    names = [contender.name for contender in contenders]
    if len(set(names)) != len(names):
        raise ValidationError(
            f"two contenders share a name: {_named(names)}. A record is addressed by the "
            f"model's name, and two models under one name is one comparison nobody can read."
        )
    if not split.index.equals(frame.index):
        raise ValidationError(
            f"the split assignment is indexed differently from the matrix: {len(split)} "
            f"label(s) against {len(frame)}. It comes from assign_splits() on this frame."
        )

    training = frame.loc[split == TRAIN]
    if len(training) == len(frame):
        raise ValidationError(
            f"every one of the {len(frame)} rows is assigned to {TRAIN!r}, so the split "
            f"holds nothing out. Cross-validation inside the training split is not a "
            f"substitute for a test set that was never used."
        )
    if training.empty:
        raise ValidationError(
            f"the split assigns no row to {TRAIN!r}; it holds "
            f"{_named(split.unique())}. There is nothing to cross-validate."
        )

    config = load_config()
    rng_seed = config.seed if seed is None else seed
    inner_count = config.model.inner_cv_folds if inner_splits is None else inner_splits

    space = FoldSpace()
    outer_set = outer(training, space)

    tuned: dict[str, set[int]] = {contender.name: set() for contender in contenders}
    scores: dict[str, list[dict[str, float]]] = {contender.name: [] for contender in contenders}
    chosen: dict[tuple[str, str], Any] = {}
    rows: list[dict[str, Any]] = []

    for fold in outer_set:
        fold_train = training.loc[list(fold.train)]
        fold_test = training.loc[list(fold.test)]
        # Cut once per outer fold, before the contender loop: every model is compared on the
        # same inner folds, and the ids do not depend on how many models were passed in.
        inner_set = grouped_folds(
            fold_train,
            space,
            splits=inner_count,
            seed=rng_seed,
            name=f"{fold.name}-inner",
            settings=settings,
        )

        for contender in contenders:
            watched = _WatchedFolds(inner_set.folds)
            configuration = contender.tune(
                TuningTask(frame=fold_train, folds=watched, outer=fold.name)
            )
            if not watched.touched:
                raise ValidationError(
                    f"{contender.name!r} read none of the {len(inner_set)} inner folds of "
                    f"{fold.name}. A search that ignores the folds it is given tuned on "
                    f"something this protocol cannot record, which is the state leak L4 "
                    f"describes."
                )
            tuned[contender.name] |= watched.touched
            chosen[contender.name, fold.name] = configuration

            metrics = _metrics(
                contender.score(
                    configuration, ScoringTask(train=fold_train, test=fold_test, fold=fold)
                ),
                model=contender.name,
                fold=fold.name,
            )
            scores[contender.name].append(metrics)
            rows.append({"model": contender.name, "fold": fold.name, **metrics})

    records = tuple(
        SelectionRecord(
            model=contender.name,
            tuned_on=frozenset(tuned[contender.name]),
            scored_on=outer_set.ids(),
            metrics=_averaged(scores[contender.name], model=contender.name),
        )
        for contender in contenders
    )
    assert_selection_is_nested(records, holdout_splits=holdout_splits)

    return Evaluation(
        records=records,
        outer=outer_set,
        per_fold=pd.DataFrame.from_records(rows),
        chosen=chosen,
        space=space,
    )
