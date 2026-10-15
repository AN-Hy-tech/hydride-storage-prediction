"""L6 -- which columns the model may see, chosen from rows the score will not come from.

**The archival selector, and what this is a port of.** ``REPORT.md`` 3.3 describes five
stages: ``VarianceThreshold``, a correlation filter at ``|r| > 0.1``, RandomForest importance
above 0.005, Boruta, then SHAP and VIF. **That selector does not exist.** There is no
correlation filter and no 0.005 threshold anywhere in the archival ``src/``, and SHAP is
computed after the fact for the report, never used as a filter. Two selectors exist:

  - ``Boruta_FeatEng.py`` -- the live one, and what this module ports. Three stages:
    ``VarianceThreshold(0.001)`` at ``:57`` with ``temperature(K)`` force-re-added at
    ``:59-61``, ``BorutaPy`` over a depth-6 ``RandomForestRegressor`` at ``:66-68`` with the
    same force-re-add at ``:71-73``, then an iterative VIF loop at ``:78-113`` dropping the
    highest until the maximum falls to 30, with ``temperature(K)`` held out of the dropping.
  - ``Feature_selection.py`` -- dead code. It reads ``data/augmented/``, whose writer was
    deleted in ``5c3bcb1``, and writes an output nothing consumes.

Three things about the port are not the archival behaviour, and each is one of the two named
defects or their consequence.

**The rows are the fold's, never the split's -- leak L6.** ``Boruta_FeatEng.py`` fits all
three stages on all 896 training rows and the pipeline then reports a cross-validated score
over those same rows, so every fold's held-out data helped choose the features it was scored
on. Here :func:`select_features` takes the row labels it is entitled to and slices to them
*before* anything is fitted; the frame it was handed is not read again. That is what
:func:`~hydms.qa.detectors.assert_selection_ignores_holdout` measures -- perturb the rows the
selector does not own, and the answer must not move, in membership or in order --
and :func:`select_across_folds` is the protocol shape, one selection per outer fold of card
#88's :func:`~hydms.surrogate.validation.grouped_folds`.

**The input is screened -- the ``Boruta_FeatEng.py:23-25`` bypass.** That file reads
``data/splits/`` -- the *pre-CleanLab* splits -- while its own comment claims it reads managed
data, so the effective published pipeline ran CleanLab and then ignored it. Here the selector
calls :func:`~hydms.data.screening.label_issues` on its own rows and hands the verdict to
:func:`~hydms.data.screening.screen`, which is the stage entitled to act on it. Screening
therefore happens *inside* the fold too, for the same reason selection does.

**Nothing is scaled.** The archival selector ran on raw feature values -- scaling appears
only later, inside the model pipelines of ``benchmark_model_selection.py`` -- and card #24 is
not blocked on the scaler for that reason. It matters for exactly one stage:
``VarianceThreshold`` is the only one of the three that is not scale-invariant (Boruta ranks
against shadow features and VIF is an R², both unchanged by an affine map). Card #24 carried a
box predicting that ``avg_is_alkaline``, whose inter-quartile span over the training rows is
exactly zero, would be dropped there. **It is not, and the premise was wrong**: a zero IQR is
not constancy. The column takes 75 distinct values over the 893 training rows and its variance
is 0.0707, seventy times the threshold, so it survives -- raw or scaled, since a
:class:`~hydms.surrogate.scaler.FittedScaler` substitutes a scale of 1.0 for a zero span and
the shift does not change a variance. The verdict is recorded rather than assumed, which is
what the box asked for.

**What the stages cost, because it decides how anything may call this.** Measured on the real
893 x 21 training matrix: ``label_issues`` 14 s, Boruta at the configured ``max_iter`` of 2000
**676 s**, the VIF loop under a second. A full pass is therefore eleven minutes, and
:func:`select_across_folds` over five outer folds is an hour -- a slow-lane run and card #25's
job, never something a test or a gate does at the configured budget.
:data:`SENTINEL_BUDGET` is how the L6 live check stays affordable, and it says there exactly
what it changes.

Card #24. The runnable entry point is :mod:`hydms.surrogate.select`.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Hashable, Iterable, Sequence
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd

from hydms.config import load as load_config
from hydms.data.metadata import non_feature_columns
from hydms.data.screening import label_issues, screen
from hydms.data.target import model_space_name, to_model_space

# "train" spelled once in the surrogate layer -- the same import validation.py takes, for the
# reason card #23 wrote beside it.
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.validation import (
    OUTER_FOLDS,
    FoldSet,
    FoldSpace,
    grouped_folds,
)

__all__ = [
    "SENTINEL_BUDGET",
    "STAGE_NAMES",
    "FoldSelection",
    "Selection",
    "SelectionError",
    "SelectionSettings",
    "Stage",
    "select_across_folds",
    "select_features",
    "selected_names",
    "sentinel_settings",
]

# A failure that names two hundred features is a failure nobody reads to the end. Same
# convention as `hydms/surrogate/validation.py` and `hydms/data/screening.py`.
_MAX_NAMED = 8

#: The three stages of the live archival selector, in the order it runs them. Named here so a
#: trace, a report and a test all spell them the same way.
STAGE_NAMES: tuple[str, ...] = ("variance", "boruta", "vif")


class SelectionError(ValueError):
    """The selector cannot run on what it was given, and the message says why.

    A ``ValueError``, like :class:`~hydms.data.splits.SplitError`,
    :class:`~hydms.surrogate.scaler.ScalerError` and
    :class:`~hydms.surrogate.validation.ValidationError` beside it. The *leak* detector for
    this module is :func:`~hydms.qa.detectors.assert_selection_ignores_holdout`, which raises
    ``LeakDetected``; if that fires it means selection read rows it does not own, which is a
    defect here rather than in the input.
    """


def _named(items: Iterable[object]) -> str:
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    return f"{', '.join(listed[:_MAX_NAMED])}, ... ({len(listed) - _MAX_NAMED} more)"


# --------------------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SelectionSettings:
    """Every knob the three stages have, in one object.

    A dataclass rather than a pile of keyword arguments because the L6 live check needs to
    run the real selector under a smaller budget, and one substituted object is a change a
    reader can see in full. :meth:`from_config` is what a real run uses; anything else is a
    deliberate departure and should say why at the call site.

    Attributes:
        variance_threshold: ``VarianceThreshold``'s threshold, on **raw** feature values.
        boruta_max_iter: ``BorutaPy(max_iter=...)``.
        boruta_max_depth: The depth of the ``RandomForestRegressor`` Boruta ranks against,
            and of the forest :func:`~hydms.data.screening.label_issues` cross-fits.
        boruta_estimators: Trees per forest, or ``"auto"`` -- Boruta's own setting, which
            grows the forest with the number of confirmed features. ``"auto"`` is the
            archival value.
        vif_threshold: The iterative VIF loop drops the highest until the maximum is at or
            below this.
        must_keep: Force-kept through the variance filter and protected from the VIF loop.
        seed: Everything stochastic derives from it.
        screen_labels: Whether to run CleanLab over the selector's own rows. ``True`` is the
            real path and what closes the ``Boruta_FeatEng.py:23-25`` bypass.
    """

    variance_threshold: float
    boruta_max_iter: int
    boruta_max_depth: int
    vif_threshold: float
    must_keep: tuple[str, ...]
    seed: int
    boruta_estimators: int | str = "auto"
    screen_labels: bool = True

    @classmethod
    def from_config(cls, config: Any | None = None) -> SelectionSettings:
        """The settings ``pipeline.yaml`` declares. No literal in this module is a threshold."""
        cfg = config if config is not None else load_config()
        return cls(
            variance_threshold=cfg.selection.variance_threshold,
            boruta_max_iter=cfg.selection.boruta_max_iter,
            boruta_max_depth=cfg.selection.boruta_max_depth,
            vif_threshold=cfg.selection.vif_threshold,
            must_keep=tuple(cfg.selection.must_keep),
            seed=cfg.seed,
        )


#: The budget the L6 live check runs the real selector under, and the whole of what it
#: changes about it.
#:
#: Boruta at the configured ``max_iter`` of 2000 costs **676 s** on the real training matrix
#: and :func:`~hydms.data.screening.label_issues` costs another 14 s. The detector runs the
#: selector **twice**, and gate HG-1 is ``Speed.FAST`` -- it runs on every gate invocation and
#: every test in ``tests/leaks/`` -- so the real budget is not a check, it is a build nobody
#: would wait for.
#:
#: **What this covers and what it does not.** It is the same function, the same three stages
#: in the same order, over the same 1,278-row frame and the same 893 training labels; both
#: runs use it, so the comparison the detector makes is exact. What it does not cover is
#: whether Boruta's *verdict* is stable -- at ten iterations it confirms 12 features where
#: the full budget confirms 13. That is not what L6 asks. L6 asks which rows the stages read,
#: and a selector that read the perturbed rows would answer differently at any budget.
#: Screening is off for the same affordability reason and for one more: its own guard is the
#: L3 sentinel, which watches :func:`~hydms.data.screening.screen` directly.
SENTINEL_BUDGET: dict[str, Any] = {
    "boruta_max_iter": 10,
    "boruta_estimators": 50,
    "screen_labels": False,
}


# --------------------------------------------------------------------------------------
# The result
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Stage:
    """What one of the three stages did.

    Attributes:
        name: One of :data:`STAGE_NAMES`.
        kept: The features that survived it, in the order it left them.
        dropped: What it removed, in the order it removed them -- which for the VIF loop is
            the order of the drops and therefore readable as the loop's own trace.
        restored: Features the stage would have dropped and ``must_keep`` put back.
        detail: One sentence for the log and for the Chapter 1 revision.
    """

    name: str
    kept: tuple[str, ...]
    dropped: tuple[str, ...]
    restored: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class Selection:
    """The chosen features, and every count behind them.

    Attributes:
        features: The selected set, in the order the last stage left it.
        stages: The three :class:`Stage` records, in run order.
        candidates: What entered stage one.
        rows: How many rows the selector actually fitted on, after screening.
        rows_offered: How many it was entitled to, before screening.
        held_out: How many rows of the frame it was handed and never read. Zero is legal --
            a caller may hand it exactly the rows it owns -- but it is recorded, because the
            claim "selection ran inside the folds" is a claim about this number.
        removed: The labels screening dropped, if it ran.
        flagged: How many rows CleanLab flagged, or ``None`` if it did not run.
    """

    features: tuple[str, ...]
    stages: tuple[Stage, ...]
    candidates: tuple[str, ...]
    rows: int
    rows_offered: int
    held_out: int
    removed: tuple[Hashable, ...] = ()
    flagged: int | None = None

    def __len__(self) -> int:
        """How many features were selected."""
        return len(self.features)

    def __contains__(self, name: object) -> bool:
        return name in self.features

    def record(self) -> dict[str, object]:
        """The counts and the chosen names as one row of a table of selections.

        Defined here, once, because two callers build such a table over the same columns:
        :meth:`FoldSelection.per_fold` writes one row per outer fold, and
        :mod:`hydms.surrogate.select` writes one for a single pass over the whole training
        split. Card #25 compares those two tables against each other, and a comparison
        between two differently-shaped rows is a comparison nobody can read.
        """
        return {
            "rows_offered": self.rows_offered,
            "rows_fitted": self.rows,
            "removed": len(self.removed),
            "flagged": self.flagged,
            "held_out": self.held_out,
            "selected": len(self.features),
            "features": ", ".join(self.features),
        }

    def trace(self) -> pd.DataFrame:
        """Stage by stage: in, out, dropped, restored -- the counts the card asks be logged.

        Returns:
            One row per stage, indexed by stage name, with ``features_in``,
            ``features_out``, ``dropped``, ``restored`` and ``detail``. The first row's
            ``features_in`` is the candidate count, so the table reads top to bottom as the
            funnel it is.
        """
        rows = []
        entering = len(self.candidates)
        for stage in self.stages:
            rows.append(
                {
                    "stage": stage.name,
                    "features_in": entering,
                    "features_out": len(stage.kept),
                    "dropped": ", ".join(stage.dropped),
                    "restored": ", ".join(stage.restored),
                    "detail": stage.detail,
                }
            )
            entering = len(stage.kept)
        return pd.DataFrame.from_records(
            rows, columns=["stage", "features_in", "features_out", "dropped", "restored", "detail"]
        ).set_index("stage")


# --------------------------------------------------------------------------------------
# The stages
# --------------------------------------------------------------------------------------


def _restore(
    kept: Sequence[str], candidates: Sequence[str], must_keep: Sequence[str]
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Put back anything ``must_keep`` names that the stage dropped, and say what was put back.

    ``Boruta_FeatEng.py`` does this twice by hand, at ``:59-61`` and ``:71-73``, appending the
    column to the end of the list both times. Appending is preserved: the order the model
    eventually sees is the order the archival selector produced, and the L6 detector compares
    order as well as membership.
    """
    present = set(kept)
    restored = tuple(name for name in must_keep if name not in present and name in set(candidates))
    return (*tuple(kept), *restored), restored


def _variance(
    features: pd.DataFrame, settings: SelectionSettings
) -> tuple[pd.DataFrame, Stage]:
    """``VarianceThreshold`` at the configured threshold, on raw values. ``Boruta_FeatEng.py:57``."""
    from sklearn.feature_selection import VarianceThreshold

    filt = VarianceThreshold(threshold=settings.variance_threshold)
    filt.fit(features)
    survived = [
        name for name, keep in zip(features.columns, filt.get_support(), strict=True) if keep
    ]
    kept, restored = _restore(survived, list(features.columns), settings.must_keep)
    dropped = tuple(name for name in features.columns if name not in set(kept))
    return features[list(kept)], Stage(
        name="variance",
        kept=kept,
        dropped=dropped,
        restored=restored,
        detail=(
            f"variance over {len(features)} row(s) at or below "
            f"{settings.variance_threshold:g} drops {len(dropped)} of {features.shape[1]}"
        ),
    )


def _boruta(
    features: pd.DataFrame, target: pd.Series, settings: SelectionSettings
) -> tuple[pd.DataFrame, Stage]:
    """``BorutaPy`` over a depth-limited forest. ``Boruta_FeatEng.py:66-73``.

    ``.to_numpy()`` on both sides: ``BorutaPy`` indexes its input positionally and a
    ``DataFrame`` reaches it as one, so the column names are read back off ``features``
    rather than off anything Boruta returns.
    """
    from boruta import BorutaPy
    from sklearn.ensemble import RandomForestRegressor

    forest = RandomForestRegressor(
        n_jobs=-1, max_depth=settings.boruta_max_depth, random_state=settings.seed
    )
    if settings.boruta_estimators != "auto":
        forest.set_params(n_estimators=int(settings.boruta_estimators))
    selector = BorutaPy(
        forest,
        n_estimators=settings.boruta_estimators,
        verbose=0,
        random_state=settings.seed,
        max_iter=settings.boruta_max_iter,
    )
    with warnings.catch_warnings():
        # BorutaPy 0.3 predates the NumPy 1.20 alias removals and scikit-learn 1.6's tag
        # API; the deprecations it emits are its own, not this project's, and burying a real
        # warning from our code under them is the cost of letting them through.
        warnings.simplefilter("ignore", category=DeprecationWarning)
        warnings.simplefilter("ignore", category=FutureWarning)
        selector.fit(features.to_numpy(), target.to_numpy())

    confirmed = [
        name for name, keep in zip(features.columns, selector.support_, strict=True) if keep
    ]
    kept, restored = _restore(confirmed, list(features.columns), settings.must_keep)
    dropped = tuple(name for name in features.columns if name not in set(kept))
    weak = int(np.asarray(selector.support_weak_).sum())
    return features[list(kept)], Stage(
        name="boruta",
        kept=kept,
        dropped=dropped,
        restored=restored,
        detail=(
            f"boruta confirms {len(confirmed)} of {features.shape[1]} in at most "
            f"{settings.boruta_max_iter} iteration(s), leaving {weak} tentative"
        ),
    )


def _vif(
    features: pd.DataFrame, settings: SelectionSettings
) -> tuple[pd.DataFrame, Stage]:
    """Drop the highest VIF until the maximum is at or below the threshold. ``:78-113``.

    ``must_keep`` is excluded from the *dropping*, not from the computation: the archival
    loop measures every column's VIF and then picks the maximum among the droppable ones, so
    ``temperature(K)`` still inflates the others' factors and still cannot itself be removed.
    A non-finite VIF -- a column that is an exact linear combination of the rest, where the
    R² is 1 and the divide is by zero -- is treated as infinite and dropped first, which is
    what the archival ``except: append(np.inf)`` amounts to.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    kept = list(features.columns)
    protected = set(settings.must_keep)
    dropped: list[str] = []
    while True:
        droppable = [name for name in kept if name not in protected]
        if not droppable:
            break
        values = features[kept].to_numpy()
        with warnings.catch_warnings():
            # `1 / (1 - R^2)` divides by zero for a perfectly collinear column. The archival
            # loop silenced the same RuntimeWarning at `:80`; the resulting `inf` is the
            # signal, not an error.
            warnings.simplefilter("ignore", category=RuntimeWarning)
            factors = pd.Series(
                [_factor(variance_inflation_factor, values, at) for at in range(len(kept))],
                index=kept,
            )
        candidates = factors.loc[droppable]
        if float(candidates.max()) <= settings.vif_threshold:
            break
        worst = str(candidates.idxmax())
        kept.remove(worst)
        dropped.append(worst)

    return features[kept], Stage(
        name="vif",
        kept=tuple(kept),
        dropped=tuple(dropped),
        restored=(),
        detail=(
            f"iterative VIF above {settings.vif_threshold:g} drops {len(dropped)} of "
            f"{features.shape[1]}, protecting {_named(protected & set(features.columns))}"
        ),
    )


def _factor(measure: Callable[..., float], values: Any, at: int) -> float:
    """One VIF, with a singular design matrix reported as infinite rather than raised."""
    try:
        factor = float(measure(values, at))
    except (ValueError, ZeroDivisionError, np.linalg.LinAlgError):
        return float("inf")
    return factor if np.isfinite(factor) else float("inf")


# --------------------------------------------------------------------------------------
# The selector
# --------------------------------------------------------------------------------------


def _candidates(frame: pd.DataFrame, features: Sequence[str] | None) -> tuple[str, ...]:
    """The columns the selector may choose from: the numeric ones that are not metadata.

    Derived rather than declared, so a frame carrying a new descriptor gets it considered
    without a second list to update -- but derived through
    :func:`~hydms.data.metadata.non_feature_columns`, so the target and the alloy class
    cannot become candidates by the same generosity.
    """
    if features is not None:
        missing = [name for name in features if name not in frame.columns]
        if missing:
            raise SelectionError(
                f"{len(missing)} named candidate feature(s) are not columns of the frame: "
                f"{_named(missing)}."
            )
        chosen = tuple(features)
    else:
        excluded = set(non_feature_columns())
        chosen = tuple(
            str(name)
            for name in frame.columns
            if name not in excluded and frame[name].dtype.kind in "fiu"
        )
    forbidden = [name for name in chosen if name in set(non_feature_columns())]
    if forbidden:
        raise SelectionError(
            f"{len(forbidden)} candidate(s) are not features: {_named(forbidden)}. Selection "
            f"choosing the target would choose it every time (hydms.data.metadata)."
        )
    if not chosen:
        raise SelectionError(
            f"no candidate feature could be found among the frame's {len(frame.columns)} "
            f"column(s). Selection over nothing returns nothing and reads as a clean run; "
            f"pass the joined record and matrix from hydms.data.metadata.with_features."
        )
    return chosen


def select_features(
    frame: pd.DataFrame,
    train: Sequence[Hashable],
    *,
    features: Sequence[str] | None = None,
    settings: SelectionSettings | None = None,
    target_column: str | None = None,
) -> Selection:
    """Choose the feature set, from ``train`` and from nothing else.

    The three archival stages in order -- variance, Boruta, VIF -- run over the rows named by
    ``train``, screened first. The frame's other rows are sliced away in the first statement
    and never read again, which is the whole of the fix for leak L6 and the property
    :func:`~hydms.qa.detectors.assert_selection_ignores_holdout` measures.

    Args:
        frame: The record and the feature matrix side by side, as
            :func:`~hydms.data.metadata.with_features` returns them -- so the target column
            is present for screening and for Boruta, and the metadata travels with it.
            Rows outside ``train`` may be present; they are the point of the guard.
        train: The row labels the selector is entitled to. In a nested run these are one
            outer fold's training labels (:func:`select_across_folds`); at the top of the
            pipeline they are the training split's.
        features: The candidate columns. Defaults to every numeric column of ``frame`` that
            :func:`~hydms.data.metadata.non_feature_columns` does not forbid.
        settings: Defaults to :meth:`SelectionSettings.from_config`.
        target_column: Defaults to ``columns.target``. Read in **model space** if the frame
            already carries the transformed column, and transformed here if it does not --
            Boruta ranks against the quantity the model is fitted on.

    Returns:
        A :class:`Selection`, whose :meth:`~Selection.trace` is the stage-by-stage table.

    Raises:
        SelectionError: ``train`` is empty, names a label the frame does not have, or the
            frame carries no usable candidate or no target.
        ScreeningError: from :func:`~hydms.data.screening.screen`, if the rows handed to it
            cannot be screened.
        LeakDetected: from inside :func:`~hydms.data.screening.screen`, if screening changed
            a row it does not own. Unreached; it is the guard that keeps the claim true.
    """
    config = load_config()
    active = settings if settings is not None else SelectionSettings.from_config(config)
    names = config.columns

    labels = list(train)
    if not labels:
        raise SelectionError(
            "select_features was given no training labels. A selector with no rows returns "
            "whatever the must-keeps are and reads as a successful run."
        )
    unknown = [label for label in labels if label not in frame.index]
    if unknown:
        raise SelectionError(
            f"{len(unknown)} training label(s) are not in the frame: {_named(unknown)}. "
            f"They are the frame's own labels, from a fold or from a split assignment."
        )
    if len(set(labels)) != len(labels):
        raise SelectionError(
            f"the training labels repeat: {len(labels)} given, {len(set(labels))} distinct. "
            f"A row counted twice is weighted twice in every stage."
        )

    # THE guard. Everything below reads `owned`; `frame` is not touched again, so no stage
    # can see a row this selector does not own however it is later rewritten.
    owned = frame.loc[labels]
    held_out = len(frame) - len(owned)

    candidates = _candidates(frame, features)
    target_name = target_column if target_column is not None else names.target
    model_space = model_space_name(target_name)
    if model_space in owned.columns:
        target = owned[model_space]
    elif target_name in owned.columns:
        target = to_model_space(owned[target_name])
    else:
        raise SelectionError(
            f"the frame carries neither {target_name!r} nor {model_space!r}, so there is "
            f"nothing for Boruta to rank against. Selection is supervised; pass the record "
            f"beside the matrix, not the matrix alone."
        )

    removed: tuple[Hashable, ...] = ()
    flagged: int | None = None
    if active.screen_labels:
        verdict = label_issues(
            owned[list(candidates)], target, seed=active.seed
        )
        # Every row here is one this selector owns, so the split it declares to `screen` is
        # `train` for all of them -- which is also what entitles `screen` to drop any of them.
        screening = screen(
            owned,
            pd.Series(TRAIN, index=owned.index),
            label_issues=verdict.issues,
            label_quality=verdict.quality,
        )
        owned = screening.frame
        removed = screening.removed
        flagged = verdict.flagged
        target = target.loc[owned.index]

    matrix = owned[list(candidates)]
    if matrix.empty:
        raise SelectionError(
            f"screening left {len(matrix)} of {len(labels)} row(s), so every stage would fit "
            f"on nothing. {len(removed)} row(s) were removed."
        )

    stages: list[Stage] = []
    matrix, stage = _variance(matrix, active)
    stages.append(stage)
    matrix, stage = _boruta(matrix, target, active)
    stages.append(stage)
    matrix, stage = _vif(matrix, active)
    stages.append(stage)

    return Selection(
        features=tuple(str(name) for name in matrix.columns),
        stages=tuple(stages),
        candidates=candidates,
        rows=len(matrix),
        rows_offered=len(labels),
        held_out=held_out,
        removed=removed,
        flagged=flagged,
    )


def selected_names(
    frame: pd.DataFrame,
    train: Sequence[Hashable],
    *,
    settings: SelectionSettings | None = None,
    **kwargs: Any,
) -> tuple[str, ...]:
    """:func:`select_features`, returning only the names.

    The shape :func:`~hydms.qa.detectors.assert_selection_ignores_holdout` wants -- a callable
    from a frame to feature names -- so the L6 check runs this module rather than a paraphrase
    of it. Bind ``train`` with :func:`functools.partial` and hand the result to the detector.
    """
    return select_features(frame, train, settings=settings, **kwargs).features


# --------------------------------------------------------------------------------------
# Inside the folds
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FoldSelection:
    """One selection per outer fold, and what the folds agree about.

    There is deliberately no single "the selected features" here. Selection inside the folds
    produces one answer per fold, and collapsing them into one is a decision -- card #25's,
    made with the fold-to-fold spread in front of it. :meth:`consensus` and :meth:`union` are
    the two obvious readings, offered side by side rather than one of them silently winning.

    Attributes:
        folds: The outer partition the selections were cut from.
        selections: One :class:`Selection` per fold, in fold order.
    """

    folds: FoldSet
    selections: tuple[Selection, ...]

    def __len__(self) -> int:
        return len(self.selections)

    def consensus(self) -> tuple[str, ...]:
        """Features every fold selected, in the first fold's order.

        The conservative reading: a feature no fold disagreed about. This is the set a
        cross-validated claim is entitled to, because it is the only one that does not depend
        on which rows happened to be held out.
        """
        if not self.selections:
            return ()
        shared = set(self.selections[0].features).intersection(
            *(set(entry.features) for entry in self.selections[1:])
        )
        return tuple(name for name in self.selections[0].features if name in shared)

    def union(self) -> tuple[str, ...]:
        """Every feature any fold selected, in first-seen order. The permissive reading."""
        seen: dict[str, None] = {}
        for entry in self.selections:
            for name in entry.features:
                seen.setdefault(name, None)
        return tuple(seen)

    def per_fold(self) -> pd.DataFrame:
        """Fold by fold: rows fitted on, rows removed, features selected, and which.

        The table card #25 publishes the old-22 against, and the evidence that selection
        moved between folds at all -- which is the observable difference between running it
        inside the folds and running it once.
        """
        return pd.DataFrame.from_records(
            [
                {"fold": fold.name, **entry.record()}
                for fold, entry in zip(self.folds, self.selections, strict=True)
            ],
            columns=[
                "fold",
                "rows_offered",
                "rows_fitted",
                "removed",
                "flagged",
                "held_out",
                "selected",
                "features",
            ],
        ).set_index("fold")

    def stability(self) -> pd.DataFrame:
        """How many folds selected each feature, most agreed-upon first.

        The number that says whether "the 22 features" was ever a stable object. A feature
        chosen by two folds out of five is not a finding about hydrogen storage; it is a
        finding about which rows were held out.
        """
        counts: dict[str, int] = dict.fromkeys(self.union(), 0)
        for entry in self.selections:
            for name in entry.features:
                counts[name] += 1
        table = pd.DataFrame(
            {"folds": list(counts.values())}, index=pd.Index(list(counts), name="feature")
        )
        table["of"] = len(self.selections)
        return table.sort_values(["folds", "feature"], ascending=[False, True])


def select_across_folds(
    frame: pd.DataFrame,
    split: pd.Series,
    *,
    outer: Callable[[pd.DataFrame, FoldSpace], FoldSet] = OUTER_FOLDS,
    settings: SelectionSettings | None = None,
) -> FoldSelection:
    """Run the selector once per outer fold of card #88's protocol.

    The protocol shape the card asks for, in one call, so that no caller has to assemble it --
    assembling it is where L6 came from. The outer partition is
    :func:`~hydms.surrogate.validation.grouped_folds` over the training split, grouped on the
    canonical composition; each fold's *training* labels are what :func:`select_features` is
    handed, and each fold's held-out rows are never offered to it.

    Like :func:`~hydms.surrogate.scaler.fit_scaler` and
    :func:`~hydms.surrogate.validation.nested_scores`, it takes the **whole** matrix with the
    split assignment and selects the training rows itself. Handing in a pre-filtered training
    subset is the one call this refuses.

    **This is a slow-lane run.** One pass over the real matrix costs eleven minutes at the
    configured Boruta budget, so five folds is about an hour. Card #25 is what runs it and
    publishes the comparison.

    Args:
        frame: The joined record and matrix, every split.
        split: Card #13's assignment, from
            :func:`~hydms.data.splits.assign_splits`, indexed as ``frame`` is.
        outer: How the outer partition is cut.
            :data:`~hydms.surrogate.validation.OUTER_FOLDS` by default;
            :func:`~hydms.surrogate.validation.leave_one_class_out` gives the AC-6 partition
            through the same path.
        settings: Defaults to :meth:`SelectionSettings.from_config`.

    Returns:
        A :class:`FoldSelection`.

    Raises:
        SelectionError: The split does not line up with the frame, or holds nothing out.
        ValidationError: from the fold generator.
        LeakDetected: A composition landed in two folds -- leak L7.
    """
    if not split.index.equals(frame.index):
        raise SelectionError(
            f"the split assignment is indexed differently from the frame: {len(split)} "
            f"label(s) against {len(frame)}. It comes from assign_splits() on this frame."
        )
    training = frame.loc[split == TRAIN]
    if training.empty:
        raise SelectionError(
            f"the split assigns no row to {TRAIN!r}; it holds {_named(split.unique())}. "
            f"There is nothing to select on."
        )
    if len(training) == len(frame):
        raise SelectionError(
            f"every one of the {len(frame)} rows is assigned to {TRAIN!r}, so the split "
            f"holds nothing out. Selection inside folds of the whole dataset is leak L6 "
            f"with extra steps."
        )

    folds = grouped_folds(training, name="outer")
    # The frame handed to each selection is the *training split*, not the fold's own rows:
    # `held_out` then counts what the selector was offered and refused to read, which is the
    # number that makes "it ran inside the folds" checkable rather than asserted.
    return FoldSelection(
        folds=folds,
        selections=tuple(
            select_features(training, list(fold.train), settings=settings) for fold in folds
        ),
    )


def sentinel_settings(settings: SelectionSettings | None = None) -> SelectionSettings:
    """The real settings under :data:`SENTINEL_BUDGET`. What the L6 live check runs.

    A function rather than a constant so that a change to ``pipeline.yaml``'s thresholds
    reaches the sentinel: only the three keys :data:`SENTINEL_BUDGET` names are overridden,
    and the variance threshold, the VIF threshold and the must-keeps stay whatever the
    configuration says they are.
    """
    base = settings if settings is not None else SelectionSettings.from_config()
    return replace(base, **SENTINEL_BUDGET)
