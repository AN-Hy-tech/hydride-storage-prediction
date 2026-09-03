"""The mechanical guards behind the leak sentinels.

Seven functions, each answering one question about what a stage did to its data, and each
raising :class:`LeakDetected` with the offending items named. Between them they cover eleven
of the thirteen leaks in ``docs/PHASE-H-RUNBOOK.md`` section 1; ``hydms/qa/sentinels.py``
records which, and which two are still owed.

Six of the seven ask about *held-out* data. The seventh, :func:`assert_metadata_survives`,
asks the opposite question -- whether a stage carried through something the next stage needs
-- because L13 is a leak of a different shape: nothing is contaminated, a column simply
stops existing and takes a validation criterion with it.

**Why these live in the package and not in ``tests/``.** They are not test helpers. Several
of them are the guard the runbook asks the *pipeline itself* to carry -- card #10's merge
must fail on a row it cannot key, card #13's split must assert that no canonical composition
spans two splits, card #26's fit must refuse an empty ``eval_set``. Putting the assertion
here means the card wires this exact function into its code path, and the sentinel then
tests the real guard rather than a parallel copy of it that can drift.

**Every argument is data, never a fitted object.** A detector is handed row labels, a record
of what a fit saw, or a callable -- never a model. That is what lets all ten sentinels be
written and demonstrated red in stage S1, before any of the code they guard exists.

Two conventions hold throughout:

  - :class:`LeakDetected` means *the defect is present*. A malformed call -- an empty
    holdout, one partition, a merge that cannot run on its own inputs -- raises
    ``ValueError`` instead, because a detector that reports a leak when it was misused is a
    detector nobody will believe.
  - Every message names the specific offenders, capped at :data:`_MAX_NAMED`, and says which
    leak it is. ``docs/QA-PROTOCOL.md`` section 4.6: an assertion that reads ``assert False``
    costs the next person an hour.

Card #71.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

__all__ = [
    "LeakDetected",
    "SelectionRecord",
    "assert_disjoint_groups",
    "assert_early_stopping_is_honest",
    "assert_holdout_unchanged",
    "assert_merge_is_keyed",
    "assert_metadata_survives",
    "assert_selection_ignores_holdout",
    "assert_selection_is_nested",
]

# A failure that names two hundred formulae is a failure nobody reads to the end. The total
# is always reported; the listing is truncated.
_MAX_NAMED = 8


class LeakDetected(AssertionError):
    """A named leak from the Phase H inventory is present.

    An ``AssertionError`` subclass, so a sentinel reads as an assertion at its call site and
    pytest renders it as one; and a distinct type, so the gate harness can tell "the detector
    fired" from "the detector itself broke".
    """


def _named(items: Iterable[Any]) -> str:
    """Render offenders for a message: sorted, truncated, and counted."""
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


def _fingerprint(table: Any) -> tuple[Any, ...]:
    """A comparable digest of a table's exact contents, order included.

    Numeric blocks are compared as raw bytes -- which is what "byte-identical" in the L3
    sentinel means, and is stricter than ``==`` because it separates two NaNs with different
    payloads. Object blocks have no meaningful buffer (``tobytes`` would compare pointers),
    so they fall back to ``repr`` of each element, which is exact for floats and stable for
    ``nan``.
    """
    array = table.to_numpy()
    if array.dtype.kind == "O":
        payload: Any = tuple(map(repr, array.ravel().tolist()))
    else:
        payload = array.tobytes()
    return (tuple(array.shape), str(array.dtype), payload)


def _rows(table: Any, labels: Sequence[Hashable], side: str) -> Any:
    """Select ``labels`` from ``table``, refusing a duplicated label.

    A duplicated index label makes ``.loc`` return more rows than were asked for, which would
    compare a different number of rows on each side and report a leak that is really a caller
    error. Held-out row labels are unique by construction; if they are not, that is worth
    failing loudly on its own.
    """
    selected = table.loc[list(labels)]
    if len(selected) != len(labels):
        raise ValueError(
            f"the {side} frame has duplicate index labels among the holdout: asked for "
            f"{len(labels)} rows and .loc returned {len(selected)}. Row labels must identify "
            f"a row uniquely before any of these checks mean anything."
        )
    return selected


# --------------------------------------------------------------------------------------
# L7, L8 -- grouping
# --------------------------------------------------------------------------------------


def assert_disjoint_groups(
    assignments: Mapping[str, Iterable[Hashable]],
    *,
    what: str = "splits",
    key_name: str = "canonical composition",
) -> None:
    """No group key may appear in more than one partition.

    Guards **L8** (``split_data.py:48,55`` split on the raw formula string, so 16
    compositions -- 35 rows -- span two splits) and **L7** (row-level ``StratifiedKFold``
    with no groups, so 141 of 896 training rows share a formula across folds).

    The detector deliberately knows nothing about chemistry. It compares whatever keys it is
    given, which is what makes the *choice of key* the visible decision: handing it raw
    formula strings reproduces the archival assertion that passed while the data leaked, and
    handing it canonical keys is the fix. ``hydms/qa/sentinels.py`` demonstrates both.

    Args:
        assignments: Partition name -> the group keys it contains. A key repeated inside one
            partition is normal (several rows, one material) and is not a finding.
        what: What the partitions are, for the message: "splits", "cross-validation folds".
        key_name: What the keys are, for the message.

    Raises:
        LeakDetected: A key appears in two or more partitions.
        ValueError: Fewer than two partitions were given -- nothing can straddle one.
    """
    if len(assignments) < 2:
        raise ValueError(
            f"assert_disjoint_groups needs at least two {what} to compare, got "
            f"{len(assignments)}. A single partition cannot be straddled."
        )

    where: dict[Hashable, list[str]] = {}
    for partition, keys in assignments.items():
        for key in set(keys):
            where.setdefault(key, []).append(partition)

    straddling = {key: sorted(names) for key, names in where.items() if len(names) > 1}
    if straddling:
        examples = [f"{key!r} in {'+'.join(names)}" for key, names in straddling.items()]
        raise LeakDetected(
            f"{len(straddling)} {key_name}(s) appear in more than one of the {what}: "
            f"{_named(examples)}. Grouping must use the canonical composition key, never the "
            f"raw formula string (leaks L7 and L8)."
        )


# --------------------------------------------------------------------------------------
# L3, L10 -- held-out data is immutable
# --------------------------------------------------------------------------------------


def assert_holdout_unchanged(
    before: Any,
    after: Any,
    *,
    holdout: Iterable[Hashable],
    what: str = "held-out targets",
) -> None:
    """Every held-out row must survive a stage byte-identical.

    Guards **L3** (``CleanLab.py:90`` replaced validation and test ground truth with the
    model's own predictions, so the replaced points have residual exactly zero by
    construction) and **L10** (the recovered ``Outliers_Management.py:60-72`` clipped
    validation and test *feature* values using their own residuals). One assertion, applied
    once to ``y`` and once to ``X``.

    A screening stage may drop or reweight training rows freely -- ``before`` and ``after``
    are compared only on ``holdout``. What it may not do is change, or lose, a held-out row.

    Args:
        before: The table entering the stage, label-indexed. A Series or a DataFrame.
        after: The table leaving it, indexed the same way.
        holdout: The row labels that must be untouched.
        what: What is being compared, for the message.

    Raises:
        LeakDetected: A held-out row changed value or disappeared.
        ValueError: ``holdout`` is empty, or a label is duplicated in either table.
    """
    labels = list(holdout)
    if not labels:
        raise ValueError(
            "assert_holdout_unchanged was given an empty holdout. A vacuous pass here is "
            "exactly the shape of the leak it exists to catch."
        )

    index_after = set(after.index)
    missing = [label for label in labels if label not in index_after]
    if missing:
        raise LeakDetected(
            f"{len(missing)} of {len(labels)} {what} disappeared during the stage: "
            f"{_named(missing)}. Screening may drop training rows only (leak L3)."
        )

    if _fingerprint(_rows(before, labels, "before")) == _fingerprint(_rows(after, labels, "after")):
        return

    changed = [
        label
        for label in labels
        if _fingerprint(_rows(before, [label], "before"))
        != _fingerprint(_rows(after, [label], "after"))
    ]
    raise LeakDetected(
        f"{len(changed)} of {len(labels)} {what} were rewritten by the stage: "
        f"{_named(changed)}. Held-out values are read once, at the end, and are never written "
        f"(leaks L3 and L10)."
    )


# --------------------------------------------------------------------------------------
# L1, L5 -- early stopping
# --------------------------------------------------------------------------------------


def assert_early_stopping_is_honest(
    *,
    eval_rows: Iterable[Hashable],
    scored_rows: Iterable[Hashable],
    use_best_model: bool,
    where: str,
) -> None:
    """The rows that choose the stopping iteration may not be the rows that score it.

    Guards **L1** (``Catboostmodel.py:604-606`` passed the *test* pool as ``eval_set`` and
    then reported that same pool as held-out at ``:684-686``, under a plot legend reading
    "Test RMSE") and **L5** (``:576-582``, ``:654-658`` -- every CV fold early-stopped on the
    fold it was scored on).

    The empty-eval check is the one CatBoost already performs: ``use_best_model=True`` with no
    ``eval_set`` raises at fit time. It is restated here so the failure arrives before the fit
    rather than several minutes into it, and so the property is asserted by this project
    rather than inherited from a library version.

    Args:
        eval_rows: Row labels in the ``eval_set`` -- what early stopping watches.
        scored_rows: Row labels the resulting model's reported metric is computed on.
        use_best_model: Whether the fit will select an iteration using ``eval_rows``.
        where: The fit being described, for the message: "final fit", "outer fold 3".

    Raises:
        LeakDetected: The eval set overlaps the scored rows, or is empty under
            ``use_best_model``.
        ValueError: ``scored_rows`` is empty -- there is no claim to check.
    """
    evaluated = set(eval_rows)
    scored = set(scored_rows)
    if not scored:
        raise ValueError(
            f"{where}: assert_early_stopping_is_honest was given no scored rows, so there is "
            f"no reported metric for the eval set to contaminate."
        )

    if use_best_model and not evaluated:
        raise LeakDetected(
            f"{where}: use_best_model=True with an empty eval_set. CatBoost raises on this at "
            f"fit time; the archival code avoided that raise by handing it the test pool "
            f"instead (leak L1)."
        )

    overlap = evaluated & scored
    if overlap:
        raise LeakDetected(
            f"{where}: {len(overlap)} of {len(scored)} scored rows are also in the eval_set: "
            f"{_named(overlap)}. The stopping iteration was chosen on the rows the model is "
            f"then reported against (leaks L1 and L5)."
        )


# --------------------------------------------------------------------------------------
# L2, L4 -- model selection
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SelectionRecord:
    """What one candidate model contributed to the model-selection decision.

    Card #88's nested protocol emits one of these per model compared. It exists so the two
    questions L2 and L4 ask -- *was a held-out metric in the room when the choice was made*,
    and *was the reported score measured on folds the tuner had already seen* -- can be
    answered from a record rather than by reading the training script.

    Attributes:
        model: What was compared.
        tuned_on: Inner-fold ids the hyperparameter search saw.
        scored_on: Outer-fold ids the reported metric came from.
        metrics: Metric value by split name. A held-out split must not appear here at all.
    """

    model: str
    tuned_on: frozenset[int]
    scored_on: frozenset[int]
    metrics: Mapping[str, float]


def assert_selection_is_nested(
    records: Sequence[SelectionRecord],
    *,
    holdout_splits: Iterable[str] = ("test",),
) -> None:
    """Model selection may not see a held-out metric, nor score on the folds it tuned on.

    Guards **L2** (``benchmark_model_selection.py:335-336`` chose the four ensemble members by
    ``nlargest(4, 'Val_Weighted_Orig')`` and then published Val R² 0.939, with a bootstrap CI,
    on that same validation set) and **L4** (``:1156`` vs ``:1168`` -- one ``splits`` object
    both tuned and scored, so there is no nesting anywhere in the protocol).

    Args:
        records: One per candidate model.
        holdout_splits: Split names whose metrics must be absent from the record entirely.

    Raises:
        LeakDetected: A record carries a held-out metric, or its tuning and scoring folds
            intersect.
        ValueError: No records were given.
    """
    if not records:
        raise ValueError(
            "assert_selection_is_nested was given no records. An empty selection record is "
            "not a clean one; it is a choice nobody wrote down."
        )

    forbidden = set(holdout_splits)
    for record in records:
        present = forbidden & set(record.metrics)
        if present:
            raise LeakDetected(
                f"the selection record for {record.model!r} carries a metric on "
                f"{_named(present)}. Held-out data is read once, at the end; a model chosen "
                f"while its test score was visible was chosen on the test set (leak L2)."
            )

        shared = record.tuned_on & record.scored_on
        if shared:
            raise LeakDetected(
                f"{record.model!r} reports a score from fold(s) {_named(shared)}, which the "
                f"tuner also saw. The reported score must come from an outer fold the "
                f"hyperparameter search never touched (leak L4)."
            )


# --------------------------------------------------------------------------------------
# L6 -- feature selection
# --------------------------------------------------------------------------------------


def assert_selection_ignores_holdout(
    select: Callable[[Any], Sequence[str]],
    frame: Any,
    *,
    holdout: Iterable[Hashable],
    seed: int = 0,
) -> None:
    """Perturbing the held-out rows must not change the selected feature set.

    Guards **L6** (``Boruta_FeatEng.py:57-113`` and ``Feature_selection.py:47-109`` fitted the
    variance filter, the VIF loop and Boruta on all 896 training rows *before* any
    cross-validation, so the selected set had already seen every fold it was later scored on).
    The archival defect is stated in terms of training rows; the property that catches it, and
    every relative of it, is that selection must be blind to anything it does not own.

    This is the one detector that runs the subject rather than reading a record of it, which is
    why it takes a callable. It perturbs only numeric columns -- there is no meaningful
    perturbation of a formula string -- and it perturbs them hard: a shuffle within the
    held-out block, then an affine rescale. A selector that so much as ranks columns by
    variance over the full frame will change its answer.

    Args:
        select: Takes the frame, returns the chosen feature names in order.
        frame: A DataFrame with a ``columns`` attribute and a label index.
        holdout: Row labels the selector is not entitled to look at.
        seed: Fixes the perturbation, so a failure reproduces exactly.

    Raises:
        LeakDetected: The feature set changed -- in membership or in order.
        ValueError: The holdout is empty, or no numeric column could be perturbed, which would
            make the check vacuous.
    """
    labels = list(holdout)
    if not labels:
        raise ValueError("assert_selection_ignores_holdout was given an empty holdout")

    baseline = tuple(select(frame))

    # stdlib `random`, not `numpy.random`: the perturbation must reproduce a failure exactly,
    # and pinning it to the standard library's Mersenne Twister makes that independent of which
    # NumPy is installed -- which matters here, because the lint lane runs outside the pinned
    # environment (docs/QA-PROTOCOL.md section 6) and this package must import under both.
    rng = random.Random(seed)
    perturbed = frame.copy(deep=True)
    touched: list[str] = []
    for column in perturbed.columns:
        if perturbed[column].dtype.kind not in "fiu":
            continue
        block = [float(value) for value in _rows(perturbed[column], labels, "frame").tolist()]
        rng.shuffle(block)
        perturbed.loc[labels, column] = [value * 1.5 + 1.0 for value in block]
        touched.append(str(column))

    if not touched:
        raise ValueError(
            "no numeric column could be perturbed, so this check would pass whatever the "
            "selector does. Give it the featurised frame, not the raw formulae."
        )

    again = tuple(select(perturbed))
    if again == baseline:
        return

    gained = sorted(set(again) - set(baseline))
    lost = sorted(set(baseline) - set(again))
    difference = (
        f"gained {_named(gained)}; lost {_named(lost)}"
        if (gained or lost)
        else f"same features, different order: {baseline} became {again}"
    )
    raise LeakDetected(
        f"perturbing {len(labels)} held-out row(s) across {len(touched)} numeric column(s) "
        f"changed the selected feature set -- {difference}. Selection read data it does not "
        f"own; it belongs inside the training folds (leak L6)."
    )


# --------------------------------------------------------------------------------------
# L9 -- the merge
# --------------------------------------------------------------------------------------


def assert_merge_is_keyed(
    merge: Callable[[Sequence[Any]], Any],
    frames: Sequence[Any],
    *,
    seed: int = 0,
) -> None:
    """A merge must join on a key, not on row position.

    Guards **L9** (``merge_datasets.py:46`` concatenated three feature frames positionally
    after ``reset_index(drop=True)``, so one skipped CBFV row silently attaches every feature
    to the wrong composition). ``docs/FREEZE.md`` calls it the highest-severity correctness
    defect in the repository, and it is silent: nothing in the archival pipeline notices.

    Two properties, because the card's phrasing -- "a shuffled input frame makes the merge
    fail, not pass silently" -- conflates them, and only both together pin the defect:

      1. **Order-invariance.** Reordering an input must either change nothing or raise. What it
         may not do is quietly produce a *different* answer, which is exactly what positional
         concatenation does.
      2. **Coverage.** Removing a row from a non-spine input must raise. A keyed merge that
         silently inner-joins the row away has lost data without saying so.

    ``frames[0]`` is the spine: the frame whose rows define the result. Rows are dropped only
    from the others, because a keyed merge cannot be expected to notice a row its spine never
    asked for.

    Args:
        merge: Takes the sequence of frames, returns the merged frame.
        frames: At least two label-indexed frames, spine first.
        seed: Fixes the shuffle.

    Raises:
        LeakDetected: The merge is order-dependent, or it tolerated a missing row.
        ValueError: Fewer than two frames, or the merge cannot run on its own inputs.
    """
    if len(frames) < 2:
        raise ValueError(
            f"assert_merge_is_keyed needs at least two frames to join, got {len(frames)}"
        )

    try:
        baseline = merge(list(frames))
    except Exception as exc:  # a merge that cannot run at all is a caller error, not a leak
        raise ValueError(
            f"the merge raised on its own unmodified inputs, so nothing below can be measured "
            f"against it: {exc!r}"
        ) from exc
    expected = _fingerprint(baseline.sort_index())

    for position in range(len(frames)):
        shuffled = list(frames)
        shuffled[position] = _shuffle(frames[position], seed)
        try:
            result = merge(shuffled)
        except Exception:  # refusing is loud, which is all this property asks for
            continue
        if _fingerprint(result.sort_index()) != expected:
            raise LeakDetected(
                f"reordering the rows of input frame {position} changed the merged result "
                f"without any complaint. The merge is joining on position, not on a key: one "
                f"skipped row attaches every feature to the wrong composition (leak L9)."
            )

    for position in range(1, len(frames)):
        thinned = list(frames)
        thinned[position] = frames[position].iloc[1:]
        try:
            merge(thinned)
        except Exception:  # any refusal is a pass here; silence is the leak
            continue
        raise LeakDetected(
            f"dropping a row from input frame {position} did not make the merge fail. The join "
            f"must assert that it covers every row of the spine, or a skipped row is absorbed "
            f"silently (leak L9)."
        )


def _shuffle(frame: Any, seed: int) -> Any:
    """Reorder a frame's rows, guaranteeing the order actually changed.

    A four-row frame has a one-in-twenty-four chance of shuffling to itself, which would let
    the order-invariance check above pass without having tested anything. Trying successive
    seeds is cheaper than requiring every caller to hand-pick one.
    """
    original = list(frame.index)
    for attempt in range(16):
        candidate = frame.sample(frac=1, random_state=seed + attempt)
        if list(candidate.index) != original:
            return candidate
    raise ValueError(
        f"could not produce a reordering of a {len(original)}-row frame in 16 attempts; give "
        f"assert_merge_is_keyed frames with at least two distinct rows"
    )


# --------------------------------------------------------------------------------------
# L13 -- the metadata a later stage needs
# --------------------------------------------------------------------------------------


def assert_metadata_survives(
    before: Any,
    after: Any,
    *,
    columns: Iterable[str],
    what: str = "metadata",
) -> None:
    """A stage may add columns and compute features; it may not lose the ones it was given.

    Guards **L13** (``extract_features_cbfv.py:19-21``::

        object_cols = df_raw.select_dtypes(include='object').columns
        cols_to_drop = [col for col in object_cols if col != 'Composition']
        df_raw = df_raw.drop(columns=cols_to_drop)

    which deletes ``Alloy_class``, ``Dataset`` and ``Citation`` in one line because they are
    not numbers. The class is the one that matters: leave-one-alloy-class-out validation
    (AC-6) is the PRD's most important validation number and there is no trace of it anywhere
    in the repository, because after this line there is nothing to fold on).

    The defect is *shape*, not value -- a featuriser drops a column that is not a feature,
    which is locally reasonable and globally fatal. So all three ways of losing it are one
    finding here: the column gone, a row gone, or a label quietly changed.

    Distinct from :func:`assert_holdout_unchanged`, which asks whether a stage rewrote data it
    was not entitled to touch. This asks whether a stage carried through data the next stage
    needs, over **every** row rather than a holdout.

    Args:
        before: The frame entering the stage, label-indexed.
        after: The frame leaving it. Extra columns are expected -- that is what the stage is
            for. Rows are compared by label, and a row of ``before`` that ``after`` has lost
            is a finding; rows ``after`` has *gained* are the merge's business
            (:func:`assert_merge_is_keyed`, leak L9), not this one's.
        columns: The column names that must survive.
        what: What they are, for the message.

    Raises:
        LeakDetected: A named column is missing, a row is missing, or a value changed.
        ValueError: ``columns`` is empty, or ``before`` does not have one of them -- a check
            for a column that was never there passes vacuously, which is the shape of the
            leak it exists to catch.
    """
    wanted = list(columns)
    if not wanted:
        raise ValueError(
            "assert_metadata_survives was given no columns to check. A vacuous pass here is "
            "exactly the shape of the leak it exists to catch."
        )

    absent = [name for name in wanted if name not in before.columns]
    if absent:
        raise ValueError(
            f"{_named(absent)} is not in the frame entering the stage, so its survival "
            f"cannot be checked. Pass the frame as it was *before* featurisation."
        )

    dropped = [name for name in wanted if name not in after.columns]
    if dropped:
        raise LeakDetected(
            f"the stage dropped {len(dropped)} of {len(wanted)} {what} column(s): "
            f"{_named(dropped)}. `extract_features_cbfv.py:19-21` drops every object column "
            f"but the formula, which is how Alloy_class stopped existing and AC-6 stopped "
            f"being answerable (leak L13)."
        )

    index_after = set(after.index)
    missing = [label for label in before.index if label not in index_after]
    if missing:
        raise LeakDetected(
            f"{len(missing)} of {len(before)} row(s) did not survive the stage: "
            f"{_named(missing)}. A row whose {what} is gone cannot be held out by class "
            f"(leak L13)."
        )

    labels = list(before.index)
    for name in wanted:
        if _fingerprint(_rows(before[[name]], labels, "before")) == _fingerprint(
            _rows(after[[name]], labels, "after")
        ):
            continue
        changed = [
            label
            for label in labels
            if _fingerprint(_rows(before[[name]], [label], "before"))
            != _fingerprint(_rows(after[[name]], [label], "after"))
        ]
        raise LeakDetected(
            f"the stage rewrote {name!r} for {len(changed)} of {len(labels)} row(s): "
            f"{_named(changed)}. Carrying {what} through means carrying it unchanged; a "
            f"relabelled row folds into the wrong class (leak L13)."
        )
