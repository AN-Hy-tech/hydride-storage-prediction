"""L1 -- which **training** rows are suspect, and the record of what was removed.

``CleanLab.py`` is the audit's fourth broken link and its worst single line. At ``:90``,
reached for validation at ``:96`` and test at ``:97``::

    managed_df['target'] = np.where(outliers_mask, y_pred, y)

**Every held-out label whose residual exceeds a threshold is replaced by the model's own
prediction.** A point so replaced has residual exactly zero by construction, so any R² or
RMSE computed downstream is measured partly against synthetic targets. That is leak **L3**,
and it is more severe than any of the three the PRD names. It is inert today only because
nothing reads the file's output -- ``Boruta_FeatEng.py:23-25`` reads the *pre-CleanLab*
splits while its comment claims otherwise -- and this module is what would have wired it in.

The same file does it to training labels too, at ``:64`` and ``:80``: ``cleaned_y_train`` is
``predicted_label`` wherever CleanLab flagged an issue. That is not L3 -- a training label is
not a measurement anyone reports a score against -- but it is the same reflex, a model
correcting the data it is about to be fitted on, and it is why the contract below is *no
label is ever rewritten*, on any split, rather than *no held-out label*.

So this stage may **drop** training rows. It may not:

  - rewrite a label, on any split, ever;
  - drop, reorder or alter a held-out row -- ``y`` and ``X`` for validation and test leave
    byte-identical, and :func:`hydms.qa.assert_holdout_unchanged` is called on both before
    the result is returned, which is the same detector gate HG-1 runs (leaks L3 and L10);
  - clip a feature value. The recovered ``Ashghal/Outliers_Management.py:60-72`` clipped
    validation and test *features* using their own residuals -- leak **L10**, the same defect
    on the other side of the table. No stage closes L10, because it is absent by accident
    rather than by fix: the file is simply not being ported. The day this module grows
    outlier handling is the day it comes back, which is why the L10 sentinel watches here.

**Reweighting is deliberately not offered.** The card allows "drop or reweight"; the only
weighting the archival pipeline had is ``Catboostmodel.py:516-518`` --
``np.where(np.expm1(y) > 3, 2.0, 1.0)``, a target-conditioned weight with a hand-tuned
threshold, which is leak **L12**. Choosing a weighting policy is card #26's decision, made
with the surrogate in view. A weight vector invented here would be a second answer.

**What the screening actually looks for**, in three kinds, reported separately because they
are different claims:

  - ``exact-duplicate`` -- structural, no judgement. Rows 687 and 694 of
    ``hydride_data.csv`` are byte-identical across all six columns: one ``La0.9Ce0.1Ni5``
    measurement at 373 K, 1.40 wt%, same citation URL, entered twice. There is no information
    in the second copy and keeping it gives that one measurement twice the weight of every
    other row in its split and in every fold. Detected with ``DataFrame.duplicated``, so no
    row number is hard-coded and a new duplicate is found rather than missed. Both copies
    land in ``train`` under #13's split, so the later one is dropped.
  - ``malformed-formula`` -- a declared, named defect. :data:`MALFORMED_FORMULAE` holds the
    one this dataset has, and the reason.
  - ``label-quality`` -- the CleanLab judgement. :func:`label_issues` makes the call and
    returns what :func:`screen` takes; it is a separate function because CleanLab needs a
    *feature matrix*, which this layer does not build. Card #24's selector supplies one and
    calls both, which is what closes the ``Boruta_FeatEng.py:23-25`` bypass.

**Why :func:`label_issues` throws away two of CleanLab's four columns.**
``find_label_issues`` returns ``is_label_issue``, ``label_quality``, ``given_label`` and
``predicted_label``. That last column is ``CleanLab.py:90``'s leak in raw form -- the archival
code wrote it into ``target`` -- so it is not returned here at all. There is no object in this
module a caller could reach a predicted label through, which is a stronger statement than a
rule saying not to use it.

**A finding on a held-out row is reported, not acted on.** That is the contract meeting the
data: if a duplicate or a defect lands in validation or test, it is named in the report with
``removed=False`` and left exactly where it is. Silently removing it would be the mirror image
of L3 -- improving a held-out set by touching it.

**The counter-caution, which belongs in this docstring and not in a footnote.** Removing real
measurements from underrepresented regimes flatters every metric that follows. The domain memo
supplies the physics: sloping plateaus make measured capacity depend on measurement pressure,
and pressure is not a column in this dataset. So a row CleanLab calls a label issue is often a
*correct* measurement taken under conditions the features cannot express -- and the
high-temperature regime, where 130 of the 893 scored out-of-fold rows sit above 500 K
(measured by `TemperatureSupport.above()` over `reports/model/model-out-of-fold.csv`), is exactly where those rows
live. Every removal is reported with its reason so the Chapter 1 revision (#37) can say how
many, of what kind, and from where.

Card #14.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass

import pandas as pd

from hydms.config import load as load_config
from hydms.data.splits import SPLIT_NAMES
from hydms.qa import assert_holdout_unchanged

__all__ = [
    "EXACT_DUPLICATE",
    "LABEL_QUALITY",
    "MALFORMED_FORMULA",
    "MALFORMED_FORMULAE",
    "Finding",
    "LabelIssues",
    "Screening",
    "ScreeningError",
    "label_issues",
    "screen",
]

_MAX_NAMED = 8

#: A row that repeats an earlier row byte for byte. Arithmetic, not judgement.
EXACT_DUPLICATE = "exact-duplicate"

#: A row whose formula cannot mean what it says. Declared in :data:`MALFORMED_FORMULAE`.
MALFORMED_FORMULA = "malformed-formula"

#: A row a label-quality method flagged. The judgement, and the only kind that needs a model.
LABEL_QUALITY = "label-quality"

#: Formula strings this project has decided are defective, and why. Matched on the string as
#: it appears in the file, not on a row number, so the decision survives a re-export.
#:
#: **The correction is not applied.** ``Mg0.853Ni0.125La0.022`` is plainly what was meant --
#: the three amounts sum to 1.000 exactly -- and writing that correction down would be a
#: better fix than dropping the row. It cannot happen *here*: the canonical key, the split
#: and the class join are all computed upstream of this stage, so by the time screening sees
#: the row it has already been keyed and split as essentially pure magnesium. A correction
#: layer has to sit above :mod:`hydms.data.load`, whose stated contract is that it normalises
#: nothing, and moving that line is a deliberate decision rather than a repair made in
#: passing. **Card #9 decided against it on 2026-09-12**: the loader normalises nothing, full
#: stop, so the row is dropped from training and named in the report, and this text is where
#: the reading survives. The whole benefit of correcting would have been this one row; the cost
#: would have been the first place in the pipeline entitled to rewrite a value it was given,
#: checked by nothing downstream. If a re-export fixes the typo at source, the row simply
#: arrives correct.
MALFORMED_FORMULAE: Mapping[str, str] = {
    "Mg0853Ni0.125La0.022": (
        "a missing decimal point: the amount reads 853, so the atomic fractions are Mg 0.9998, "
        "Ni 1.5e-04, La 2.6e-05 -- essentially pure magnesium, whose feature vector is nothing "
        "like the Mg-Ni-La alloy the 4.96 wt% label describes. 0.853 + 0.125 + 0.022 = 1.000 "
        "exactly, so the intended formula is Mg0.853Ni0.125La0.022"
    ),
}


class ScreeningError(ValueError):
    """The stage cannot run on what it was given, and the message says why.

    A ``ValueError``, like the other data-layer guards. The *leak* detector for this stage is
    :func:`hydms.qa.detectors.assert_holdout_unchanged`, which raises ``LeakDetected``; if
    that fires here it means the stage broke its own contract, which is a defect in this
    module rather than in its input.
    """


def _named(items: Iterable[object]) -> str:
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    return f"{', '.join(listed[:_MAX_NAMED])}, ... ({len(listed) - _MAX_NAMED} more)"


@dataclass(frozen=True)
class Finding:
    """One row the screening has something to say about.

    Attributes:
        label: The row's index label in the frame that entered the stage.
        kind: :data:`EXACT_DUPLICATE`, :data:`MALFORMED_FORMULA` or :data:`LABEL_QUALITY`.
        split: Which split the row is in.
        reason: Why, in a sentence a reader of the Chapter 1 revision can use.
        removed: Whether the row was actually dropped. ``False`` for every held-out row --
            the finding is recorded and the row stays, because improving a held-out set by
            touching it is the mirror image of leak L3.
        quality: The label-quality score, when one was supplied. ``None`` otherwise.
    """

    label: Hashable
    kind: str
    split: str
    reason: str
    removed: bool
    quality: float | None = None


@dataclass(frozen=True)
class Screening:
    """What the stage did, and the frame it produced.

    Attributes:
        frame: The screened table. Held-out rows are byte-identical to their inputs and in
            their original order; training rows may be absent.
        findings: Every row the stage had something to say about, in frame order.
        removed: The index labels actually dropped.
        entering: The split of every row that *entered* the stage, in order, so that
            :meth:`counts` can report ``rows_in`` without being handed the input frame again.
    """

    frame: pd.DataFrame
    findings: tuple[Finding, ...]
    removed: tuple[Hashable, ...]
    entering: tuple[str, ...] = ()

    def report(self) -> pd.DataFrame:
        """The findings as a table: label, kind, split, removed, quality, reason.

        Empty of rows but not of columns when nothing was found, so a caller can write it out
        without special-casing the happy path.
        """
        return pd.DataFrame(
            [
                {
                    "label": finding.label,
                    "kind": finding.kind,
                    "split": finding.split,
                    "removed": finding.removed,
                    "quality": finding.quality,
                    "reason": finding.reason,
                }
                for finding in self.findings
            ],
            columns=["label", "kind", "split", "removed", "quality", "reason"],
        )

    def counts(self) -> pd.DataFrame:
        """Rows in, flagged, removed and kept, per split -- the numbers #37 reports.

        Reported per split rather than as a total because the interesting property is that
        ``removed`` is zero everywhere except ``train``, and a total cannot show that.
        """
        by_split = pd.Series([finding.split for finding in self.findings], dtype=object)
        removed = pd.Series(
            [finding.split for finding in self.findings if finding.removed], dtype=object
        )
        entering = pd.Series(self.entering, dtype=object)
        records = [
            {
                "split": name,
                "rows_in": int((entering == name).sum()),
                "flagged": int((by_split == name).sum()),
                "removed": int((removed == name).sum()),
                "rows_out": int((entering == name).sum()) - int((removed == name).sum()),
            }
            for name in SPLIT_NAMES
        ]
        return pd.DataFrame.from_records(records).set_index("split")


def _validate(frame: pd.DataFrame, split: pd.Series) -> None:
    if not split.index.equals(frame.index):
        raise ScreeningError(
            "the split assignment is not aligned to the frame: "
            f"{len(split)} label(s) against {len(frame)}. Pass the Series "
            "hydms.data.splits.assign_splits returned for this frame."
        )
    unknown = set(split.dropna().unique()) - set(SPLIT_NAMES)
    if unknown:
        raise ScreeningError(
            f"the split assignment holds {_named(unknown)}, which is not one of "
            f"{SPLIT_NAMES}. Screening's whole contract is stated per split, so it cannot "
            f"proceed on a row whose split it does not recognise."
        )
    missing = split.isna()
    if bool(missing.any()):
        raise ScreeningError(
            f"{int(missing.sum())} row(s) have no split: {_named(frame.index[missing])}. "
            f"An unassigned row cannot be screened, because whether it may be dropped "
            f"depends entirely on which side of the line it is on."
        )


@dataclass(frozen=True)
class LabelIssues:
    """CleanLab's verdict on a set of rows, in the two columns :func:`screen` accepts.

    Attributes:
        issues: Boolean per row -- ``find_label_issues``' ``is_label_issue``.
        quality: The score behind it, in ``[0, 1]``, low meaning suspect.
        rows: How many rows were judged.
        estimator: What was cross-fitted to produce the judgement, for the report and for
            the Chapter 1 revision. A label-quality verdict is a property of the model that
            produced it as much as of the data, and a number nobody can attribute to a
            method is not evidence.
    """

    issues: pd.Series
    quality: pd.Series
    rows: int
    estimator: str

    @property
    def flagged(self) -> int:
        """How many rows were flagged."""
        return int(self.issues.sum())


def label_issues(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    estimator: object | None = None,
    seed: int | None = None,
) -> LabelIssues:
    """Cross-fit a regressor over these rows and ask CleanLab which labels it cannot explain.

    The only place in this project that calls CleanLab. It is deliberately given a matrix and
    a target rather than a frame and a column name: this function must be impossible to point
    at the whole dataset by accident, and the caller that assembles ``features`` is the one
    that knows which rows it is entitled to (card #24 -- selection runs inside the training
    folds, and the rows it screens are that fold's rows).

    **Held-out rows must not be in ``features``.** There is no split argument here to check
    it against; the guard is :func:`screen`, which is what acts on the verdict and which
    refuses to remove anything that is not ``train``. This function judges what it is handed.

    Args:
        features: The matrix, one row per label. Its index is carried onto both results, so
            :func:`screen` pairs the verdict by label rather than by position.
        target: The labels, in **model space** -- this is the quantity a model is fitted on,
            and CleanLab's judgement is "the cross-fitted model cannot reproduce this value".
        estimator: The regressor to cross-fit. Defaults to the archival selector's forest --
            ``RandomForestRegressor(max_depth=selection.boruta_max_depth)`` -- so the model
            deciding which labels are suspect is the same family as the one deciding which
            features matter, rather than a second, unrelated choice. **It runs on one
            thread, and an estimator that would run on more is refused** (card #104): a
            scikit-learn forest's ``predict`` adds its trees' predictions under a lock in
            whatever order the threads finish, so a parallel forest returns a slightly
            different sum on every call. CleanLab ranks rows by that residual and drops the
            worst from its own refits, so the drift grows, measured on SS's outer-training
            rows, to 5e-4 in ``label_quality`` between two identical calls in one process,
            and to a different verdict between two LOACO runs. One thread costs about half
            as much again per pass (34 s against 23 s on those rows). That is minutes on a
            run of hours, and it buys a verdict that does not move.
        seed: Defaults to ``seed`` in ``pipeline.yaml``. CleanLab's own ``seed`` argument.
            With the one-thread estimator, the same seed over the same rows reproduces the
            verdict bit for bit. The earlier "measured" here held for the flagged set on
            one call pair, not for the scores, and not across runs (#104).

    Returns:
        A :class:`LabelIssues`. Splat it into :func:`screen`::

            verdict = label_issues(X, y)
            screen(frame, split, label_issues=verdict.issues, label_quality=verdict.quality)

    Raises:
        ScreeningError: The target is not aligned to the matrix, or either is empty, or the
            estimator would predict on more than one thread.
    """
    if estimator is not None and _threads(estimator) not in (None, 1):
        raise ScreeningError(
            f"the estimator runs on n_jobs={_threads(estimator)}. A parallel forest sums its "
            f"trees in thread-finishing order, so the same rows and seed give a different "
            f"verdict on every call (card #104). Pass it with n_jobs=1."
        )
    if not isinstance(features, pd.DataFrame):
        raise ScreeningError(
            f"label_issues needs a DataFrame so the verdict can be returned on its index, "
            f"not a {type(features).__name__}. A verdict paired by position is leak L9 in a "
            f"new place."
        )
    if len(target) != len(features) or not target.index.equals(features.index):
        raise ScreeningError(
            f"the target is not aligned to the matrix: {len(target)} label(s) against "
            f"{len(features)} row(s). They are paired by label, never by position."
        )
    if features.empty:
        raise ScreeningError(
            "label_issues was given no rows. An empty verdict flags nothing, which would "
            "read downstream as a clean dataset rather than as a check that never ran."
        )

    from cleanlab.regression.learn import CleanLearning
    from sklearn.ensemble import RandomForestRegressor

    config = load_config()
    rng_seed = config.seed if seed is None else seed
    model = (
        estimator
        if estimator is not None
        else RandomForestRegressor(
            n_jobs=1, max_depth=config.selection.boruta_max_depth, random_state=rng_seed
        )
    )

    # `.to_numpy()`, not the frame: CleanLab hands X straight to the estimator's `fit`, and a
    # scikit-learn estimator fitted on a DataFrame remembers its column names and then warns
    # -- or, worse, silently accepts a different order -- on every cross-fit slice.
    verdict = CleanLearning(model, seed=rng_seed).find_label_issues(
        X=features.to_numpy(), y=target.to_numpy()
    )
    return LabelIssues(
        issues=pd.Series(
            verdict["is_label_issue"].to_numpy(), index=features.index, name="is_label_issue"
        ),
        quality=pd.Series(
            verdict["label_quality"].to_numpy(), index=features.index, name="label_quality"
        ),
        rows=len(features),
        estimator=type(model).__name__,
    )


def _threads(estimator: object) -> object:
    """The estimator's ``n_jobs``, or ``None`` when it has no such parameter."""
    get_params = getattr(estimator, "get_params", None)
    return get_params().get("n_jobs") if callable(get_params) else None


def screen(
    frame: pd.DataFrame,
    split: pd.Series,
    *,
    label_issues: pd.Series | None = None,
    label_quality: pd.Series | None = None,
    formula_column: str | None = None,
) -> Screening:
    """Drop suspect **training** rows, and report every finding on every split.

    Args:
        frame: The table entering the stage, e.g. the output of
            :func:`hydms.data.load.load_hydride_data`.
        split: Which split each row is in, from
            :func:`hydms.data.splits.assign_splits`, aligned to ``frame``'s index.
        label_issues: Boolean per row -- what
            ``CleanLearning(...).find_label_issues(X, y)['is_label_issue']`` returns. May
            cover a subset of the rows (the training ones); labels it does not mention are
            treated as clean. Optional, because the feature matrix it needs does not exist
            until S3.
        label_quality: The score behind ``label_issues``, recorded in the report. Optional.
        formula_column: Defaults to ``columns.formula``.

    Returns:
        A :class:`Screening`: the screened frame, every finding, and what was dropped.

    Raises:
        ScreeningError: The split assignment does not match the frame, or names a split this
            module does not know.
        LeakDetected: The stage changed a held-out row or a label. It is raised rather than
            returned because there is nothing useful to do with a screening that leaked --
            and if it fires, the defect is in this module.
    """
    _validate(frame, split)
    names = load_config().columns
    formula = formula_column if formula_column is not None else names.formula

    findings: list[Finding] = []
    seen: set[Hashable] = set()

    def note(label: Hashable, kind: str, reason: str, quality: float | None = None) -> None:
        if label in seen:
            return
        seen.add(label)
        findings.append(
            Finding(
                label=label,
                kind=kind,
                split=str(split.loc[label]),
                reason=reason,
                removed=str(split.loc[label]) == "train",
                quality=quality,
            )
        )

    for label in frame.index[frame.duplicated(keep="first")]:
        first = frame.index[frame.eq(frame.loc[label]).all(axis=1)][0]
        note(
            label,
            EXACT_DUPLICATE,
            f"byte-identical to row {first!r} across every column -- one measurement "
            f"recorded twice, which would weight it double in its split and in every fold",
        )

    if formula in frame.columns:
        for label, value in frame[formula].items():
            if str(value) in MALFORMED_FORMULAE:
                note(label, MALFORMED_FORMULA, MALFORMED_FORMULAE[str(value)])

    if label_issues is not None:
        # Built as a set of labels rather than by reindexing onto the frame: CleanLab is
        # fitted on the training rows, so what it returns covers those alone, and a reindex
        # would have to invent a value for every row it never saw.
        flagged = {label for label, value in label_issues.items() if bool(value)}
        for label in frame.index:
            if label not in flagged:
                continue
            score = (
                float(label_quality.loc[label])
                if label_quality is not None and label in label_quality.index
                else None
            )
            note(
                label,
                LABEL_QUALITY,
                "flagged as a label issue. Note the counter-caution: a sloping plateau makes "
                "capacity depend on a measurement pressure this dataset does not record, so a "
                "flagged row may be a correct measurement the features cannot express",
                score,
            )

    dropped = tuple(finding.label for finding in findings if finding.removed)
    screened = frame.drop(index=list(dropped)) if dropped else frame.copy()

    held_out = [label for label in frame.index if str(split.loc[label]) != "train"]
    if held_out:
        assert_holdout_unchanged(
            frame[names.target], screened[names.target], holdout=held_out,
            what="held-out targets",
        )
        assert_holdout_unchanged(
            frame.drop(columns=[names.target]),
            screened.drop(columns=[names.target]),
            holdout=held_out,
            what="held-out feature values",
        )
    assert_holdout_unchanged(
        frame, screened, holdout=list(screened.index), what="rows that survived screening"
    )

    return Screening(
        frame=screened,
        findings=tuple(findings),
        removed=dropped,
        entering=tuple(str(value) for value in split),
    )
