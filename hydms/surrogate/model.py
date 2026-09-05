"""L3 -- the capacity model, its quantile heads, and the rows allowed to stop it.

Two changes from ``Machine_Model/src/Catboostmodel.py``, and both are structural rather than
remembered.

**The eval set is never the scored set (leaks L1 and L5).** ``:604-606`` fitted the final
model with ``eval_set=test_pool`` and then reported that same pool as held out at
``:684-686``, under a plot legend reading "Test RMSE"; ``:576-582`` did the same thing inside
every cross-validation fold. Here :func:`fit_quantile_model` cannot be called without naming
the rows the resulting model will be *scored* against, and its first statement hands those
identities to :func:`~hydms.qa.detectors.assert_early_stopping_is_honest`. There is no path
through this module that fits without that check, which is why the L1 and L5 sentinels can
point at it rather than at a copy of it.

**The weights are blind to the target (leak L12).** ``:516-518`` is
``np.where(np.expm1(y) > 3, 2.0, 1.0)`` -- rows weighted by their own answer at a hand-tuned
threshold, repeated at ``:570-572`` inside each fold. :func:`sample_weights` takes the frame
and slices it to the declared features in its first statement, so the target is not reachable
from anything below; :func:`~hydms.qa.detectors.assert_weights_ignore_target` measures that
rather than trusting it.

**The heads.** ``MultiQuantile:alpha=...`` returns one column per alpha **in the order given
in the string**, and position is the only thing identifying P10 from P90. This module turns
that position into a name once, at :func:`column_names`, and every result it returns is a
frame with those names on it. A test asserts the mapping against a fitted model rather than
against the docstring.

**What it is fitted on.** :data:`~hydms.descriptors.contract.SELECTED`, card #25's consensus
fourteen -- not :data:`~hydms.descriptors.contract.CONTRACT`, which stays the published 22
and the candidate pool gate AC-2 checks parity across. Selection is **not** re-run inside the
tuning loop: one Boruta pass costs 676 s (card #24) against a budget measured in thousands of
fits, so per-fold selection here is not a slower option but an impossible one. The
consequence is a sentence every number out of this module owes: a score here belongs to a
*fixed* fourteen-feature pipeline, and not to the procedure that chose those fourteen -- whose
own folds each selected between 16 and 20.

**What it is not fitted on: a scaler.** CatBoost splits on thresholds and
:class:`~hydms.surrogate.scaler.FittedScaler` is affine, so the tree ensemble is invariant to
it up to floating point -- measured, see the card's narrative. The scaler belongs to the
distance-based work downstream (the applicability domain, card #48) and to the artifact
bundle; refitting it per fold inside a tuning loop would add a leak surface for no effect.
A model from here therefore consumes **raw** features, and says so in
:attr:`QuantileModel.feature_names`.

**Space.** The booster is fitted on ``log1p`` capacity
(:func:`~hydms.data.target.to_model_space`) and every number this module reports is weight
percent. Back-transforming the three heads is exact rather than approximate: ``expm1`` is
strictly increasing, and a quantile is equivariant under a monotone map, so the ``expm1`` of
the model-space P90 *is* the P90 of the weight-percent distribution.

Card #26.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

import numpy as np
import pandas as pd

from hydms.config import Config
from hydms.config import load as load_config
from hydms.data.load import load_hydride_data, parse_formula
from hydms.data.metadata import CANONICAL_KEY_COLUMN, with_features, with_metadata
from hydms.data.screening import label_issues, screen
from hydms.data.splits import SPLIT_NAMES, assign_splits
from hydms.data.target import model_space_name, to_model_space, to_wt_pct
from hydms.descriptors.contract import SELECTED, FeatureContract
from hydms.descriptors.featurize import featurize
from hydms.qa import assert_early_stopping_is_honest
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.validation import (
    Contender,
    Fold,
    ScoringTask,
    TuningTask,
    grouped_folds,
)

__all__ = [
    "FIXED",
    "MODEL_PAYLOAD",
    "SEARCH_SPACE",
    "SENTINEL_BUDGET",
    "SENTINEL_SPACE",
    "Configuration",
    "FitLog",
    "FitRecord",
    "Hyperparameter",
    "ModelError",
    "ModelSettings",
    "QuantileModel",
    "ScreenedRows",
    "capacity_contender",
    "capacity_matrix",
    "column_names",
    "final_fit",
    "fit_quantile_model",
    "loss_function",
    "model_from",
    "quantile_metrics",
    "quantile_metrics_from_arrays",
    "sample_weights",
    "scored_table",
    "screened_rows",
    "sentinel_settings",
    "stopping_slice",
]

# Same convention as `hydms/surrogate/validation.py` and `hydms/qa/detectors.py`: a failure
# that names two hundred rows is a failure nobody reads to the end.
_MAX_NAMED = 8

#: The payload key the fitted model is saved under, so ``artifacts/v{N}/model.joblib`` is
#: spelled once rather than at every call site. :func:`model_from` reads it back, beside
#: :data:`~hydms.surrogate.scaler.SCALER_PAYLOAD` and
#: :data:`~hydms.surrogate.conformal.CONFORMAL_PAYLOAD`.
MODEL_PAYLOAD = "model"

#: The prefix :meth:`Configuration.row` puts on every hyperparameter column of
#: ``model-chosen.csv``, so that a reader of that table can tell a hyperparameter from the
#: bookkeeping beside it. Named here because **both sides of the file have to agree**:
#: ``hydms.surrogate.calibrate`` reads the deployed configuration back out by this prefix, and
#: it does so as an *allow*-list. It was a deny-list once -- every column except a named few --
#: and that shipped a `features` count and a set of `param.`-prefixed names straight into
#: ``CatBoostRegressor(**params)``, which raised
#: ``unexpected keyword argument 'features'`` the first time anybody ran the two commands in
#: sequence against a real table. A deny-list over a file format silently admits every column
#: added later; an allow-list refuses them.
PARAM_PREFIX = "param."


class ModelError(ValueError):
    """The fit cannot run, or a caller handed it something it must refuse.

    Distinct from :class:`~hydms.qa.detectors.LeakDetected`, which the honesty check raises:
    this is "that call does not make sense", not "that call is the audit's defect".
    """


def _named(items: Iterable[object]) -> str:
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    return f"{', '.join(listed[:_MAX_NAMED])}, ... ({len(listed) - _MAX_NAMED} more)"


# --------------------------------------------------------------------------------------
# The quantile heads
# --------------------------------------------------------------------------------------


def loss_function(quantiles: Sequence[float]) -> str:
    """``"MultiQuantile:alpha=0.1,0.5,0.9"`` for these quantiles, in this order.

    Built rather than written out, because the order in this string is what decides the order
    of the columns coming back, and a literal here would be a second place for that order to
    live. ``pipeline.yaml``'s loader already refuses an unsorted or repeating list.
    """
    if not quantiles:
        raise ModelError("a MultiQuantile loss over no quantiles has no heads to fit.")
    return "MultiQuantile:alpha=" + ",".join(f"{value:g}" for value in quantiles)


def column_names(quantiles: Sequence[float]) -> tuple[str, ...]:
    """The column name for each quantile: ``("q0.1", "q0.5", "q0.9")``.

    The one place position becomes name. CatBoost returns an ``(n, len(alphas))`` array whose
    columns follow the alpha string and carry no labels, so every result leaving this module
    is put on these names immediately and nothing downstream indexes a quantile by number.
    """
    return tuple(f"q{value:g}" for value in quantiles)


# --------------------------------------------------------------------------------------
# The search space
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Hyperparameter:
    """One dimension of the Optuna search, as data rather than as a ``suggest_`` call.

    Declared this way so the space can be asserted against the archival script in a test, and
    so a reduced space is a substituted value a reader can see in full rather than a branch
    inside the objective -- the same move :data:`~hydms.surrogate.selection.SENTINEL_BUDGET`
    makes for Boruta.

    Attributes:
        name: The CatBoost parameter.
        kind: ``"int"`` or ``"float"``.
        low: Inclusive lower bound.
        high: Inclusive upper bound.
        log: Whether Optuna samples it on a log scale.
    """

    name: str
    kind: str
    low: float
    high: float
    log: bool = False

    def __post_init__(self) -> None:
        if self.kind not in ("int", "float"):
            raise ModelError(f"{self.name!r}: a hyperparameter is 'int' or 'float', not {self.kind!r}.")
        if self.low > self.high:
            raise ModelError(
                f"{self.name!r}: the low bound {self.low} is above the high bound {self.high}, "
                f"so nothing can be sampled from it."
            )
        if self.log and self.low <= 0:
            raise ModelError(
                f"{self.name!r} is sampled on a log scale and its low bound is {self.low}; "
                f"log of a non-positive bound is undefined."
            )

    def suggest(self, trial: Any) -> Any:
        """Ask a trial for a value. The only place this module calls Optuna's API."""
        if self.kind == "int":
            return trial.suggest_int(self.name, int(self.low), int(self.high), log=self.log)
        return trial.suggest_float(self.name, float(self.low), float(self.high), log=self.log)


#: The search space: ported from ``Machine_Model/src/Catboostmodel.py:545-563`` -- the *live*
#: study at ``:542``, not the two commented-out earlier ones above it -- with **one bound
#: changed**, and the change is a measurement.
#:
#: **``learning_rate`` starts at 5e-4, where the archival study started at 1e-4.** The
#: archival pairing let the search reach 1e-4 with ``iterations`` capped at 30,000, and at
#: that corner the fit does not converge: measured on a real inner fold at the configured
#: ``early_stopping_rounds``, the best iteration is **29,999** -- the cap itself, still
#: improving when the budget ran out. The whole decade, one fit each, same fold, same
#: parameters otherwise:
#:
#: ===============  ==============  =========  ======
#: learning_rate    best iteration  seconds    R2
#: ===============  ==============  =========  ======
#: 0.005                       813        4.4  0.6800
#: 0.001                     4,230       12.9  0.6847
#: 0.0005                    8,501       25.7  0.6831
#: 0.0003                   13,991       44.1  0.6816
#: 0.0001                   29,999       82.4  0.6803
#: ===============  ==============  =========  ======
#:
#: The best iteration goes as roughly ``4.2 / learning_rate`` and **R2 is flat across the
#: whole decade**. So the low corner buys nothing and costs everything: nineteen times the
#: wall time for the same model, and at the bottom for a model that never finished. Card #26
#: measured the same corner at **397 s against 7 s** under its own parameters and scored it
#: *worse* (0.691 against 0.705); it left the space ported because narrowing it is a
#: modelling decision, and boxed the decision onto the card that would pay for the run.
#:
#: **Why 5e-4 exactly, and not a rounder number.** ``iterations`` is sampled from 10,000, so
#: the binding question is whether a trial converges inside the *smallest* budget the space
#: can hand it. At 5e-4 the optimum is at 8,501 -- inside 10,000 -- and at 3e-4 it is at
#: 13,991, which is not. The bound is therefore the measured point at which every corner of
#: this space converges within its own iteration budget, rather than a round number chosen
#: for looking like one.
#:
#: ``depth`` is sampled to 25, which CatBoost accepts under ``Lossguide`` and which
#: ``max_leaves`` then makes mostly inert: a 64-leaf tree cannot be 25 deep. That one is
#: recorded and still ported -- it is inert, not expensive, and there is no run to protect
#: from it.
#:
#: Card #29, box (ii). The narrowing lands **before** the run this thesis quotes, because
#: narrowing afterwards would publish a model the project then changed.
SEARCH_SPACE: tuple[Hyperparameter, ...] = (
    Hyperparameter("learning_rate", "float", 0.0005, 0.005, log=True),
    Hyperparameter("depth", "int", 7, 25),
    Hyperparameter("iterations", "int", 10000, 30000),
    Hyperparameter("l2_leaf_reg", "float", 1.0, 10.0),
    Hyperparameter("bagging_temperature", "float", 0.0, 1.0),
    Hyperparameter("random_strength", "float", 0.5, 15.0),
    Hyperparameter("max_leaves", "int", 16, 128),
    Hyperparameter("min_data_in_leaf", "int", 1, 20),
    Hyperparameter("border_count", "int", 32, 256),
)


#: What every fit sets whatever the search chose, and why each one is not in the space.
#:
#: ``grow_policy`` is the archival choice, and it is what makes ``max_leaves`` and
#: ``min_data_in_leaf`` mean anything. ``task_type`` is not a preference: ``MultiQuantile`` is
#: one of the few regression losses with **no GPU support**, so this trains on CPU and the
#: slow lane's budget is a CPU budget.
#:
#: **``bootstrap_type`` is the one departure from the archival parameters, and it is what
#: makes a ported dimension do anything at all.** ``bagging_temperature`` is a Bayesian-
#: bootstrap parameter, and CatBoost's CPU default is not Bayesian. Measured: under the
#: default, ``bagging_temperature`` 0.0 and 1.0 give a bit-identical fit -- same tree count,
#: same best iteration, the same loss to six decimals -- while under ``Bayesian`` they give
#: 0.1444 and 0.1526. So the archival search spent one of its nine dimensions on a parameter
#: that did nothing. Pinning the bootstrap is what the sampled parameter evidently meant.
#:
#: **Not here: `od_type` and `od_pval`.** ``:556-557`` set ``od_type='IncToDec'`` and
#: ``od_pval=1e-2`` in the parameters *and* passed ``early_stopping_rounds=5000`` to ``fit``.
#: CatBoost accepts the pair -- measured, it does not raise, and on a fit where both could
#: act they stopped at the same iteration -- so this is not a conflict to resolve but a
#: redundancy to remove. This module sets the one ``pipeline.yaml`` declares, which is the one
#: the card means by "early stopping on the validation split", and leaves the other unset
#: rather than carrying two stopping rules and no statement of which applied.
FIXED: Mapping[str, Any] = {
    "grow_policy": "Lossguide",
    "bootstrap_type": "Bayesian",
    "task_type": "CPU",
    "verbose": 0,
    "allow_writing_files": False,
}


# --------------------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelSettings:
    """Every knob the fit and its search have, in one object.

    A dataclass rather than a pile of keyword arguments for the reason
    :class:`~hydms.surrogate.selection.SelectionSettings` gives: the leak sentinels must run
    the real code under a budget a FAST gate can afford, and one substituted object is a
    change a reader can see in full.

    Attributes:
        quantiles: The alphas, ascending. Their order is the column order.
        early_stopping_rounds: ``od_wait``. Rounds without improvement on the eval set before
            the fit stops.
        optuna_trials: Trials per outer fold. The budget is a *product* -- see
            :func:`capacity_contender`.
        stopping_folds: The early-stopping slice is one fold of this many, cut from the rows
            a fit owns by :func:`~hydms.surrogate.validation.grouped_folds`. Five means the
            slice is a fifth of them, grouped on the canonical composition like every other
            fold in this project.
        seed: Everything stochastic derives from it: the slice, the sampler, the booster.
        features: The columns fitted on. :data:`~hydms.descriptors.contract.SELECTED`.
        space: The search space. :data:`SEARCH_SPACE` for a real run.
        screen_labels: Whether CleanLab screens the rows a fit owns. ``True`` is the real
            path; it is the same stage card #24's selector runs, over the same rows.
        target: The raw target column, in weight percent. ``None`` means nobody said, and a
            fit then **refuses** rather than reaching for the file -- see below.
        temperature: The temperature column, carried into the row-level prediction record so
            card #29's per-temperature breakdown does not have to re-read the matrix.

    **The two column names are here because a fit must not re-read ``pipeline.yaml``.**
    ``hydms.config.load`` parses and revalidates the file on every call and caches nothing.
    Before these fields existed, ``_columns`` reached for it from inside the scoring path --
    about six reads a fit, some 2,300 in a 381-fit run, each one a window in which an edit to
    the working tree changes what the run believes it is fitting. It has already fired once,
    killing a probe on its third trial, and two sessions share this checkout. So the names are
    resolved **once**, by :meth:`from_config`, and a settings object built by hand without
    them makes :func:`fit_quantile_model` refuse by name rather than silently read a file that
    may be half-written. Card #29, box (i).
    """

    quantiles: tuple[float, ...]
    early_stopping_rounds: int
    optuna_trials: int
    stopping_folds: int
    seed: int
    features: tuple[str, ...] = SELECTED.names
    space: tuple[Hyperparameter, ...] = SEARCH_SPACE
    screen_labels: bool = True
    target: str | None = None
    temperature: str | None = None

    @classmethod
    def from_config(cls, config: Any | None = None) -> ModelSettings:
        """The settings ``pipeline.yaml`` declares. No literal in this module is a threshold."""
        cfg = config if config is not None else load_config()
        return cls(
            quantiles=tuple(cfg.model.quantiles),
            early_stopping_rounds=cfg.model.early_stopping_rounds,
            optuna_trials=cfg.model.optuna_trials,
            stopping_folds=cfg.model.stopping_folds,
            seed=cfg.seed,
            target=cfg.columns.target,
            temperature=cfg.columns.temperature,
        )


#: The reduced space the leak sentinels fit under. Same parameter names, same kinds, tiny
#: bounds -- so the code path is identical and the cost is not.
SENTINEL_SPACE: tuple[Hyperparameter, ...] = (
    Hyperparameter("learning_rate", "float", 0.05, 0.2, log=True),
    Hyperparameter("depth", "int", 3, 4),
    Hyperparameter("iterations", "int", 20, 40),
)


#: The budget the L1, L5 and L12 live checks run the real model under, and the whole of what
#: it changes about it.
#:
#: A real trial is a fit of up to 30,000 boosted iterations and the protocol asks for
#: thousands of them; gate HG-1 is ``Speed.FAST`` and runs on every gate invocation and every
#: test in ``tests/leaks/``. So the sentinels fit **the same function over the same folds**
#: under a space that stops in a few hundred milliseconds.
#:
#: **What this covers and what it does not.** L1 and L5 are questions about *row identities* --
#: which rows chose the stopping iteration, which rows the result is reported against -- and
#: an identity does not depend on how many trees were grown. L12 is a question about what the
#: weighting reads, which does not either. What the reduced space does not cover is whether
#: the *chosen hyperparameters* are any good, and that is not what these three sentinels ask.
SENTINEL_BUDGET: dict[str, Any] = {
    "optuna_trials": 2,
    "space": SENTINEL_SPACE,
    "early_stopping_rounds": 5,
    "screen_labels": False,
}


def sentinel_settings(settings: ModelSettings | None = None) -> ModelSettings:
    """The real settings under :data:`SENTINEL_BUDGET`. What the live checks fit.

    A function rather than a constant so that a change to ``pipeline.yaml`` reaches the
    sentinels: only the four keys above are overridden, and the quantiles, the stopping-slice
    count, the feature set and the seed stay whatever the configuration says they are.
    """
    base = settings if settings is not None else ModelSettings.from_config()
    return replace(base, **SENTINEL_BUDGET)


# --------------------------------------------------------------------------------------
# The weights -- leak L12
# --------------------------------------------------------------------------------------


def sample_weights(
    frame: pd.DataFrame, *, settings: ModelSettings | None = None
) -> pd.Series:
    """One weight per row, from the rows' own features and from nothing else.

    **This project fits unweighted, and the weight of the decision is in the blindness rather
    than in the number.** ``Catboostmodel.py:516-518`` doubled the weight of every row above
    3 wt%, so the fit was told which examples matter *because of what they measure*; leak L12
    is that dependency, not the threshold. Replacing 3 with 4 changes nothing, and a
    feature-conditioned scheme would need a justification this dataset does not supply -- so
    the honest scheme is the constant one, and what is asserted is that it is a constant of
    the features.

    The frame is sliced to the declared features in the first statement and is not read
    again, which is the same guard :func:`~hydms.surrogate.selection.select_features` uses for
    leak L6: no later edit to this function can reach the target, whatever it is later asked
    to do. :func:`~hydms.qa.detectors.assert_weights_ignore_target` measures it by perturbing
    the target and requiring the weights not to move, and the L12 sentinel runs *this*
    function -- not a paraphrase -- against the real matrix.

    **The fold-size argument does not land here.** Screening removes between 15 and 144 of a
    fold's roughly 710 training rows depending on the fold (card #24), so ``outer-1`` fits on
    571 rows where ``outer-2`` fits on 704, and an unweighted mean over folds treats those as
    equal evidence. That is an argument about how folds are *aggregated*, not about how rows
    inside one fit are weighted; the answer is that ``rows_fitted`` is reported as a metric
    beside every fold's score, so the spread is visible rather than corrected for.

    Args:
        frame: The rows a fit owns, features and record side by side.
        settings: Defaults to :meth:`ModelSettings.from_config`. Only ``features`` is read.

    Returns:
        A ``float64`` Series of ones on ``frame``'s index, named ``weight``.

    Raises:
        ModelError: A declared feature is missing from the frame.
    """
    active = settings if settings is not None else ModelSettings.from_config()
    missing = [name for name in active.features if name not in frame.columns]
    if missing:
        raise ModelError(
            f"the frame is missing {len(missing)} of {len(active.features)} declared "
            f"feature(s): {_named(missing)}. Weights are a function of the features, so a "
            f"frame without them cannot be weighed."
        )
    # THE guard. Nothing below reads `frame`, so no later edit to this function can reach the
    # target -- which is the whole of leak L12.
    features = frame.loc[:, list(active.features)]
    return pd.Series(1.0, index=features.index, name="weight", dtype="float64")


# --------------------------------------------------------------------------------------
# The matrix
# --------------------------------------------------------------------------------------


def capacity_matrix(
    config: Config | None = None, *, settings: ModelSettings | None = None
) -> tuple[pd.DataFrame, pd.Series]:
    """The rows and columns the capacity model is fitted on, and card #13's split over them.

    One assembly, called by the training command, by card #34's artifact run and by the L1,
    L5 and L12 sentinels, so that "the matrix" is one object rather than three that agree
    until they do not. The rows are chosen by asking the contract which compositions it can
    serve -- the idiom :func:`~hydms.descriptors.featurize.featurize`'s docstring documents --
    and the join is :func:`~hydms.data.metadata.with_features`, never a ``concat``, because
    ``temperature(K)`` arrives from both sides and that function is what checks they agree.

    The contract is ``settings.features``, which is
    :data:`~hydms.descriptors.contract.SELECTED`: fourteen features, not the published 22.

    Returns:
        ``(frame, split)`` -- the record and matrix side by side, and the split assignment
        restricted to the same rows and in the same order.
    """
    cfg = config if config is not None else load_config()
    active = settings if settings is not None else ModelSettings.from_config(cfg)
    contract = FeatureContract.from_names(active.features)

    names = cfg.columns
    record = with_metadata(load_hydride_data())
    split = assign_splits(record)
    keep = [
        label
        for label, formula in record[names.formula].items()
        if contract.computability(parse_formula(formula)).complete
    ]
    usable = record.loc[keep]
    features = featurize(
        usable[names.formula], usable[names.temperature], contract=contract
    )
    return with_features(usable, features), split.loc[keep]


# --------------------------------------------------------------------------------------
# The rows a fit owns
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ScreenedRows:
    """The rows a fit may learn from, after CleanLab, and what it cost them.

    Attributes:
        kept: Labels that survived, in frame order.
        removed: Labels screening dropped.
        flagged: How many rows CleanLab flagged, or ``None`` if it did not run.
        offered: How many were handed in.
    """

    kept: tuple[Hashable, ...]
    removed: tuple[Hashable, ...] = ()
    flagged: int | None = None
    offered: int = 0

    def __len__(self) -> int:
        return len(self.kept)


def screened_rows(
    frame: pd.DataFrame,
    labels: Sequence[Hashable],
    *,
    settings: ModelSettings | None = None,
    target_column: str | None = None,
) -> ScreenedRows:
    """CleanLab over the rows a fit owns, once.

    The same stage :func:`~hydms.surrogate.selection.select_features` runs, called at the same
    scope: the rows named by ``labels`` and nothing else, declared to
    :func:`~hydms.data.screening.screen` as ``train``, which is what entitles it to drop any
    of them and what stops it touching anything else (leaks L3 and L10).

    **It is called once per fold, never once per fit.** One pass costs about fourteen seconds
    on the real matrix, and the tuning loop makes thousands of fits over the same rows; a
    screen inside :func:`fit_quantile_model` would multiply a fixed cost by the search budget
    for an identical verdict every time. That is why this is a separate function and why the
    fit does not call it.

    Args:
        frame: The rows this fit could see, features and record side by side.
        labels: The subset it owns.
        settings: Defaults to :meth:`ModelSettings.from_config`.
        target_column: Defaults to ``columns.target``. Read in model space if the frame
            already carries the transformed column.

    Returns:
        A :class:`ScreenedRows`.

    Raises:
        ModelError: ``labels`` is empty, repeats, or names a row the frame does not have.
        ScreeningError: from the stage itself.
    """
    active = settings if settings is not None else ModelSettings.from_config()
    owned = _owned(frame, labels, what="screened")
    if not active.screen_labels:
        return ScreenedRows(kept=tuple(owned.index), offered=len(owned))

    target = _target(owned, _resolve(active, target_column))
    verdict = label_issues(
        owned.loc[:, list(active.features)], target, seed=active.seed
    )
    # Every row here is one this fit owns, so the split declared to `screen` is `train` for
    # all of them -- the same statement `select_features` makes, for the same reason.
    result = screen(
        owned,
        pd.Series(TRAIN, index=owned.index),
        label_issues=verdict.issues,
        label_quality=verdict.quality,
    )
    return ScreenedRows(
        kept=tuple(result.frame.index),
        removed=tuple(result.removed),
        flagged=verdict.flagged,
        offered=len(owned),
    )


def _owned(
    frame: pd.DataFrame, labels: Sequence[Hashable], *, what: str
) -> pd.DataFrame:
    """``frame.loc[labels]``, refusing an empty, repeating or unknown selection."""
    listed = list(labels)
    if not listed:
        raise ModelError(
            f"no rows were {what}. A fit on no rows returns a constant and reads as a "
            f"successful run."
        )
    unknown = [label for label in listed if label not in frame.index]
    if unknown:
        raise ModelError(
            f"{len(unknown)} label(s) to be {what} are not in the frame: {_named(unknown)}. "
            f"They are the frame's own labels, from a fold or from a split assignment."
        )
    if len(set(listed)) != len(listed):
        raise ModelError(
            f"the labels to be {what} repeat: {len(listed)} given, {len(set(listed))} "
            f"distinct. A row counted twice is weighted twice."
        )
    return frame.loc[listed]


def _columns(target_column: str | None) -> tuple[str, str]:
    """The raw and model-space names of the target, in that order.

    **No fit reaches the fallback below.** Every entry point in this module resolves the name
    once through :func:`_resolve`, from :attr:`ModelSettings.target`, and hands a string down;
    the ``None`` branch is left for the callers that have no settings to resolve from --
    :func:`hydms.surrogate.conformal.fit_conformal`, which calibrates once, and tests that
    build a frame and no settings. Putting a configuration read on the scoring path is what
    card #29's box (i) is about, and :class:`ModelSettings` says what it cost.
    """
    raw = target_column if target_column is not None else load_config().columns.target
    return raw, model_space_name(raw)


def _resolve(settings: ModelSettings, target_column: str | None) -> str:
    """The target column this call means: the override, else what the settings carry.

    Refuses rather than falling back to ``pipeline.yaml``. A settings object with no target is
    one that did not come from :meth:`ModelSettings.from_config`, and the honest thing to do
    with it is to say so: reading the file here is the race box (i) removed, and doing it
    only sometimes would be the same race with a smaller window.
    """
    if target_column is not None:
        return target_column
    if settings.target is not None:
        return settings.target
    raise ModelError(
        "the settings carry no target column and none was passed. Build them with "
        "ModelSettings.from_config(), which resolves it once, or pass target_column= "
        "explicitly. This does not fall back to pipeline.yaml: a fit that re-reads the "
        "configuration is a fit whose answer depends on when it ran."
    )


def _target(frame: pd.DataFrame, target_column: str | None) -> pd.Series:
    """The fitting target, in model space, from whichever column the frame carries."""
    raw, transformed = _columns(target_column)
    if transformed in frame.columns:
        return frame[transformed]
    if raw in frame.columns:
        return to_model_space(frame[raw])
    raise ModelError(
        f"the frame carries neither {raw!r} nor {transformed!r}, so there is nothing to fit "
        f"against. Pass the record beside the matrix, not the matrix alone."
    )


def _truth(frame: pd.DataFrame, target_column: str | None) -> pd.Series:
    """The target in **weight percent**, which is the space every metric is reported in.

    The raw column when the frame has it, rather than ``to_wt_pct(to_model_space(y))``: that
    round trip is accurate to about 1e-16 and is still a round trip, and a score should be
    computed against the measurement rather than against a re-derivation of it.
    """
    raw, transformed = _columns(target_column)
    if raw in frame.columns:
        return frame[raw]
    if transformed in frame.columns:
        return to_wt_pct(frame[transformed])
    raise ModelError(
        f"the frame carries neither {raw!r} nor {transformed!r}, so there is nothing to score "
        f"against."
    )


# --------------------------------------------------------------------------------------
# The early-stopping slice
# --------------------------------------------------------------------------------------


def stopping_slice(
    frame: pd.DataFrame,
    labels: Sequence[Hashable],
    *,
    settings: ModelSettings | None = None,
    name: str = "stopping",
) -> tuple[tuple[Hashable, ...], tuple[Hashable, ...]]:
    """Split the rows a fit owns into the rows it learns from and the rows that stop it.

    The eval set has to come from somewhere, and every wrong answer to "where" is one of the
    two leaks this module exists to close: the scored rows (L1, L5) or a slice that shares a
    composition with them (L7 wearing L5's clothes). So the slice is cut by
    :func:`~hydms.surrogate.validation.grouped_folds` -- the project's only fold generator,
    grouped on the canonical composition and stratified on the target and temperature -- out
    of the rows the fit already owns. It is one fold of ``settings.stopping_folds``, so a
    fifth of them at the configured five, and no composition spans the two sides.

    The final fit is the exception that needs no cut: ``val`` is already a group-disjoint
    tenth of the data, and it is what ``pipeline.yaml``'s ``early_stopping_rounds`` comment
    means by "the VALIDATION split". This function is for fits *inside* the training split,
    where there is no ``val`` to reach for and reaching for ``test`` is the audit's defect.

    Args:
        frame: The rows this fit could see, with formula, temperature and target columns --
            the fold generator stratifies on them.
        labels: The rows it owns, already screened.
        settings: Defaults to :meth:`ModelSettings.from_config`.
        name: Prefix for the generated fold names, for messages.

    Returns:
        ``(fitting labels, stopping labels)``, both in frame order.

    Raises:
        ModelError: ``labels`` is empty, repeats, or names an unknown row.
        ValidationError: too few compositions to cut the slice.
        LeakDetected: a composition landed on both sides -- which cannot happen, and is
            asserted by the fold generator rather than assumed.
    """
    active = settings if settings is not None else ModelSettings.from_config()
    owned = _owned(frame, labels, what="split for early stopping")
    folds = grouped_folds(
        owned, splits=active.stopping_folds, seed=active.seed, name=name
    )
    slice_ = folds[0]
    return tuple(slice_.train), tuple(slice_.test)


# --------------------------------------------------------------------------------------
# The fit
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FitRecord:
    """Which rows one fit saw in which role, and what the fit cost.

    The evidence the L1 and L5 sentinels read. It records *identities*, never values, which
    is why a sentinel can check a run's honesty without refitting it and why this can be
    written to a CSV beside the scores.

    Attributes:
        where: The fit, as it appears in a failure message: ``"final fit"``, ``"outer-2"``.
        fitted: Rows the trees were grown on.
        eval_on: Rows that chose the stopping iteration.
        scored_on: Rows the resulting model is reported against. Declared *before* the fit,
            which is what makes the honesty check possible at all.
        removed: Rows screening dropped from ``fitted``.
        best_iteration: The iteration ``use_best_model`` kept.
        trees: How many trees survived that truncation.
        seconds: Wall time of the fit alone.
    """

    where: str
    fitted: tuple[Hashable, ...]
    eval_on: tuple[Hashable, ...]
    scored_on: tuple[Hashable, ...]
    removed: tuple[Hashable, ...] = ()
    best_iteration: int = -1
    trees: int = 0
    seconds: float = 0.0

    def row(self) -> dict[str, object]:
        """One row of :meth:`FitLog.table`."""
        return {
            "where": self.where,
            "fitted": len(self.fitted),
            "eval_on": len(self.eval_on),
            "scored_on": len(self.scored_on),
            "removed": len(self.removed),
            "best_iteration": self.best_iteration,
            "trees": self.trees,
            "seconds": round(self.seconds, 3),
        }


class FitLog:
    """Every fit a run made, in order.

    Passed in rather than kept in module state, so that "what did this run fit" is a question
    with one answer per run and no answer at all for a run nobody asked about. The sentinels
    hand one to :func:`capacity_contender` and read the records back; ``hydms.surrogate.train``
    hands one in and writes the table out.
    """

    def __init__(self) -> None:
        self._records: list[FitRecord] = []

    def add(self, record: FitRecord) -> FitRecord:
        self._records.append(record)
        return record

    @property
    def records(self) -> tuple[FitRecord, ...]:
        return tuple(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Any:
        return iter(self._records)

    def table(self) -> pd.DataFrame:
        """One row per fit: where it was, how many rows in each role, what it cost."""
        return pd.DataFrame.from_records(
            [record.row() for record in self._records],
            columns=[
                "where",
                "fitted",
                "eval_on",
                "scored_on",
                "removed",
                "best_iteration",
                "trees",
                "seconds",
            ],
        )


@dataclass(frozen=True)
class QuantileModel:
    """A fitted CatBoost ``MultiQuantile`` model, with its columns already named.

    Attributes:
        booster: The ``CatBoostRegressor``. Reachable, because card #27 conformalises it and
            card #34 stores it; every *use* of it in this project goes through
            :meth:`predict`.
        feature_names: The columns it was fitted on, in fitting order. **Raw**, unscaled --
            see this module's docstring.
        quantiles: The alphas, in the order the loss string named them, which is the order
            the booster's columns arrive in.
        record: What rows it saw, in which role.
    """

    booster: Any
    feature_names: tuple[str, ...]
    quantiles: tuple[float, ...]
    record: FitRecord

    @property
    def columns(self) -> tuple[str, ...]:
        """The names :meth:`predict` returns, in order."""
        return column_names(self.quantiles)

    def predict_model_space(self, features: pd.DataFrame) -> pd.DataFrame:
        """The heads as the booster emits them: ``log1p`` capacity, one named column each.

        For card #27, whose conformal residuals are computed in the space the model was
        fitted in. Everything a person reads should come from :meth:`predict` instead.

        Raises:
            ModelError: the batch is not a frame, or does not carry the fitted columns.
        """
        matrix = self._batch(features)
        values = np.asarray(self.booster.predict(matrix), dtype="float64")
        if values.ndim != 2 or values.shape[1] != len(self.quantiles):
            raise ModelError(
                f"the booster returned {values.shape} for {len(matrix)} row(s) and "
                f"{len(self.quantiles)} quantile(s). MultiQuantile returns one column per "
                f"alpha; a different width means the loss string and this model disagree."
            )
        return pd.DataFrame(values, index=features.index, columns=list(self.columns))

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """The heads in weight percent, one named column per quantile.

        Exact, not approximate: ``expm1`` is strictly increasing and a quantile is equivariant
        under a monotone map, so the ``expm1`` of the model-space P90 *is* the P90 of the
        weight-percent distribution. Nothing is clipped -- a negative lower band is the signal
        that the model has left what it can defend, and suppressing it here would hide the
        thing cards #48 and #77 exist to act on.

        Args:
            features: A frame carrying :attr:`feature_names`, in any order, on any index.

        Returns:
            ``(len(features), len(quantiles))`` of ``float64``, columns named by
            :attr:`columns`, on the caller's index.

        Raises:
            ModelError: the batch is not a frame, or does not carry the fitted columns.
            TargetError: a head is so large that ``expm1`` overflows -- a broken model, not a
                prediction.
        """
        model_space = self.predict_model_space(features)
        return pd.DataFrame(
            {name: to_wt_pct(model_space[name]) for name in self.columns},
            index=features.index,
            columns=list(self.columns),
        )

    def _batch(self, features: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(features, pd.DataFrame):
            raise ModelError(
                f"a model predicts from a DataFrame, not a {type(features).__name__}. An "
                f"array carries no column names, so a permuted matrix would return "
                f"plausible, wrong numbers -- the failure gate AC-4 exists for."
            )
        missing = [name for name in self.feature_names if name not in features.columns]
        if missing:
            raise ModelError(
                f"the batch is missing {len(missing)} of {len(self.feature_names)} fitted "
                f"feature(s): {_named(missing)}. A model is stored with the contract it was "
                f"fitted against; build the batch from that contract."
            )
        return features.loc[:, list(self.feature_names)]


def model_from(bundle: Any, *, name: str = MODEL_PAYLOAD) -> QuantileModel:
    """The fitted model held in a loaded artifact version, checked before it is believed.

    The load path, and one line rather than ``bundle[MODEL_PAYLOAD]`` for the reason
    :func:`~hydms.surrogate.scaler.scaler_from` and
    :func:`~hydms.surrogate.conformal.conformal_from` give: what can be wrong with a stored
    payload does not show up until a prediction is already a number.

      - **It is a bare booster rather than a QuantileModel.** A ``CatBoostRegressor`` unpickles
        happily, has its own ``predict``, and returns an unnamed ``(n, 3)`` array -- so the
        caller is back to identifying P10 by position, which is the trap
        :func:`column_names` exists to remove. It also has a ``fit``.
      - **It was fitted on no columns**, which cannot be featurised against and would let a
        batch of anything through.
      - **The payload is absent**, which reads as a ``KeyError`` naming what the version does
        hold.

    What it deliberately does *not* check is that the fitted columns are in the version's
    feature contract. That cross-check belongs where the featurisation contract is built --
    :func:`~hydms.surrogate.predict.load_surrogate` -- because that is where a name outside
    the contract stops being an observation and becomes an unbuildable column.

    Args:
        bundle: A loaded :class:`~hydms.artifacts.store.Artifacts`.
        name: The payload key. :data:`MODEL_PAYLOAD` unless a version stored several.

    Returns:
        The stored :class:`QuantileModel`.

    Raises:
        ModelError: the payload is not a :class:`QuantileModel`, or it records no fitted
            columns.
        KeyError: the version holds no such payload.
    """
    model = bundle[name]
    if not isinstance(model, QuantileModel):
        raise ModelError(
            f"payload {name!r} of {getattr(bundle, 'version', 'this version')} is a "
            f"{type(model).__name__}, not a QuantileModel. A bare booster predicts an "
            f"unnamed array and carries neither the column order it was fitted on nor the "
            f"alphas its columns follow, which is the silent failure gate AC-4 exists to "
            f"catch; re-train the version through hydms.surrogate.model.final_fit()."
        )
    if not model.feature_names:
        raise ModelError(
            f"the stored model of {getattr(bundle, 'version', 'this version')} records no "
            f"fitted columns, so there is nothing to featurise against and any batch at all "
            f"would be accepted."
        )
    return model


def fit_quantile_model(
    frame: pd.DataFrame,
    *,
    train: Sequence[Hashable],
    eval_on: Sequence[Hashable],
    scored_on: Sequence[Hashable],
    where: str,
    params: Mapping[str, Any] | None = None,
    settings: ModelSettings | None = None,
    target_column: str | None = None,
    removed: Sequence[Hashable] = (),
    log: FitLog | None = None,
) -> QuantileModel:
    """One honest fit: grow on ``train``, stop on ``eval_on``, be reported on ``scored_on``.

    ``scored_on`` is required and is not used to fit anything. That is the point of it: a
    caller cannot reach this function without saying what the resulting model will be claimed
    about, and the first thing done with that answer is
    :func:`~hydms.qa.detectors.assert_early_stopping_is_honest`. ``Catboostmodel.py:604-606``
    is unwritable here -- passing the test rows as ``eval_on`` raises before a tree is grown.

    ``use_best_model=True`` is not optional either. CatBoost validates at fit time that it has
    a non-empty ``eval_set``, so the only two ways to satisfy this call are a real eval set or
    a refusal; the archival code took the third option, which was to hand it the test pool.

    Args:
        frame: The rows this fit could see, features and record side by side.
        train: The rows to grow trees on -- already screened; see :func:`screened_rows`.
        eval_on: The rows that choose the stopping iteration. Disjoint from ``scored_on``,
            asserted.
        scored_on: The rows the resulting model will be reported against. Not read.
        where: The fit's name, for the failure message and the record.
        params: The searched hyperparameters. Defaults to CatBoost's own, which is only
            useful for a smoke test.
        settings: Defaults to :meth:`ModelSettings.from_config`.
        target_column: Defaults to ``columns.target``.
        removed: What screening dropped on the way here, recorded rather than recomputed.
        log: A :class:`FitLog` to append the record to.

    Returns:
        A :class:`QuantileModel`.

    Raises:
        ModelError: a row set is empty, repeats, is unknown, or ``train`` overlaps either
            ``scored_on`` or ``eval_on``.
        LeakDetected: ``eval_on`` overlaps ``scored_on``, or is empty -- leaks L1 and L5.
    """
    active = settings if settings is not None else ModelSettings.from_config()
    # Resolved once, here, so that nothing below this line reaches for `pipeline.yaml`. See
    # `_resolve` and `ModelSettings`: this function used to read the file twice per fit.
    target = _resolve(active, target_column)

    # First, before anything is read and long before anything is fitted. A leak that raises
    # after twenty minutes of boosting is a leak somebody comments out.
    assert_early_stopping_is_honest(
        eval_rows=eval_on,
        scored_rows=scored_on,
        use_best_model=True,
        where=where,
    )
    scored = set(scored_on)
    overlap = set(train) & scored
    if overlap:
        raise ModelError(
            f"{where}: {len(overlap)} of the {len(scored)} scored row(s) are also being "
            f"fitted on: {_named(overlap)}. That is not leak L1 -- it is cruder than L1 -- "
            f"and the fold protocol should never produce it."
        )
    grown_and_watched = set(train) & set(eval_on)
    if grown_and_watched:
        raise ModelError(
            f"{where}: {len(grown_and_watched)} row(s) are both fitted on and in the eval "
            f"set: {_named(grown_and_watched)}. Early stopping watching rows the trees are "
            f"already growing on never fires -- the loss on them falls whatever the model is "
            f"doing elsewhere -- so `use_best_model` would keep the last iteration and this "
            f"would look like a fit that simply never overfitted."
        )

    fitting = _owned(frame, train, what="fitted on")
    stopping = _owned(frame, eval_on, what="evaluated on")
    # The target is transformed on the two row sets this fit owns, never on `frame`. A
    # `to_model_space(frame[target])` here would read every scored row on the way past --
    # harmlessly, and then indistinguishably from reading them on purpose. Scoping it is what
    # lets `tests/surrogate/test_no_test_leak.py` fill the scored rows with NaN and still
    # expect this to succeed.
    grown_on = _target(fitting, target)
    stopped_on = _target(stopping, target)

    pool = _pool()
    booster = _regressor(active, params)
    weights = sample_weights(fitting, settings=active)

    started = time.perf_counter()
    booster.fit(
        pool(
            fitting.loc[:, list(active.features)],
            grown_on,
            weight=weights.to_numpy(),
        ),
        eval_set=pool(stopping.loc[:, list(active.features)], stopped_on),
    )
    seconds = time.perf_counter() - started

    record = FitRecord(
        where=where,
        fitted=tuple(fitting.index),
        eval_on=tuple(stopping.index),
        scored_on=tuple(scored_on),
        removed=tuple(removed),
        best_iteration=int(booster.get_best_iteration() or 0),
        trees=int(booster.tree_count_ or 0),
        seconds=seconds,
    )
    if log is not None:
        log.add(record)
    return QuantileModel(
        booster=booster,
        feature_names=tuple(active.features),
        quantiles=tuple(active.quantiles),
        record=record,
    )


def final_fit(
    frame: pd.DataFrame,
    split: pd.Series,
    *,
    params: Mapping[str, Any] | None = None,
    settings: ModelSettings | None = None,
    target_column: str | None = None,
    log: FitLog | None = None,
) -> QuantileModel:
    """The three-split fit: grown on ``train``, stopped on ``val``, reported on ``test``.

    **This is no longer the deployed fit.** The model this project ships carves a calibration
    slice out of the screened training rows before growing a tree, because a band calibrated on
    rows the trees already saw under-covers exactly where it claims not to; that sequence is
    :func:`hydms.surrogate.deploy.deployed_fit` and it is the only thing that builds a
    deployable model. This function remains the uncarved arrangement -- the honest answer to
    "grow on train, stop on val, report on test" -- and is what the leak L1 argument below is
    written about.

    The one place in this project that names all three splits in one call, and the site the
    audit's leak L1 lives at: ``Catboostmodel.py:604-606`` combined ``train`` and ``val`` into
    the fitting pool and then handed ``test`` in as the ``eval_set``, so the split that was
    published as held out is the split that chose the stopping iteration. Here ``val`` does
    that job -- which is what ``pipeline.yaml``'s ``early_stopping_rounds`` comment has said
    all along -- and ``test`` is named only so that
    :func:`~hydms.qa.detectors.assert_early_stopping_is_honest` has something to check the
    eval set against. Not one value of it is read.

    Args:
        frame: The whole matrix, every split -- :func:`capacity_matrix`'s first return. Like
            :func:`~hydms.surrogate.scaler.fit_scaler`, this selects the rows itself, and a
            pre-filtered training subset is the one call it refuses.
        split: Card #13's assignment, indexed as ``frame`` is.
        params: The hyperparameters. Card #34 passes what the nested run chose.
        settings: Defaults to :meth:`ModelSettings.from_config`.
        target_column: Defaults to ``columns.target``.
        log: A :class:`FitLog` to record the fit into.

    Returns:
        A :class:`QuantileModel` fitted on the training split alone.

    Raises:
        ModelError: the split does not line up with the frame, or a split is empty.
        LeakDetected: never, unless this function is edited into leak L1.
    """
    active = settings if settings is not None else ModelSettings.from_config()
    if not split.index.equals(frame.index):
        raise ModelError(
            f"the split assignment is indexed differently from the matrix: {len(split)} "
            f"label(s) against {len(frame)}. It comes from assign_splits() on this frame."
        )
    rows = {name: list(frame.index[split == name]) for name in SPLIT_NAMES}
    empty = [name for name, labels in rows.items() if not labels]
    if empty:
        raise ModelError(
            f"the split assigns no row to {_named(empty)}; it holds "
            f"{_named(split.unique())}. The final fit needs all three: it grows on "
            f"{TRAIN!r}, stops on the validation split and is reported on the test split."
        )

    target = _resolve(active, target_column)
    kept = screened_rows(frame, rows[TRAIN], settings=active, target_column=target)
    return fit_quantile_model(
        frame,
        train=kept.kept,
        eval_on=rows["val"],
        scored_on=rows["test"],
        where="final fit",
        params=params,
        settings=active,
        target_column=target,
        removed=kept.removed,
        log=log,
    )


def _regressor(settings: ModelSettings, params: Mapping[str, Any] | None) -> Any:
    """``CatBoostRegressor`` with the loss, the seed and the stopping rule pinned.

    Imported lazily, like ``hydms.surrogate.scaler``'s scikit-learn import: ``import
    hydms.surrogate`` must stay cheap enough for ``hydms.gates list`` and for every test that
    only wants the fold protocol.
    """
    from catboost import CatBoostRegressor

    return CatBoostRegressor(
        **{
            **dict(params or {}),
            **FIXED,
            "loss_function": loss_function(settings.quantiles),
            "random_seed": settings.seed,
            "early_stopping_rounds": settings.early_stopping_rounds,
            "use_best_model": True,
        }
    )


def _pool() -> Any:
    """CatBoost's ``Pool``, imported lazily for the same reason."""
    from catboost import Pool

    return Pool


# --------------------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------------------


def quantile_metrics(
    actual: pd.Series, predicted: pd.DataFrame, quantiles: Sequence[float]
) -> dict[str, float]:
    """What one fit's predictions are worth, in weight percent.

    All of it in weight percent, including the pinball loss, because that is the unit the
    thesis claims and an R² computed on ``log1p`` capacity flatters the model against its own
    published numbers. The archival script scored cross-validation on the log scale "to avoid
    negative scores", which is the same observation read the other way round.

    Returns:
        ``r2``, ``rmse``, ``mae`` of the median head; ``pinball`` averaged over every head;
        ``interval_coverage`` and ``interval_width`` between the outermost two; and
        ``crossings``, the share of rows with any adjacent pair of heads out of order. None of these
        names may be a split name -- :data:`~hydms.surrogate.validation.HELD_OUT_SPLITS` --
        and none is.

    Raises:
        ModelError: the prediction is not aligned to the truth, or the quantiles are not the
            prediction's columns.
    """
    names = column_names(quantiles)
    if list(predicted.columns) != list(names):
        raise ModelError(
            f"the prediction carries columns {list(predicted.columns)} where these quantiles "
            f"name {list(names)}. Position identifies a quantile in CatBoost's output and "
            f"nothing else does."
        )
    if not predicted.index.equals(actual.index):
        raise ModelError(
            f"the prediction is not on the truth's index: {len(predicted)} row(s) against "
            f"{len(actual)}. They are paired by label, never by position."
        )

    return quantile_metrics_from_arrays(
        actual.to_numpy(dtype="float64"), predicted.to_numpy(dtype="float64"), quantiles
    )


def quantile_metrics_from_arrays(
    truth: np.ndarray, heads: np.ndarray, quantiles: Sequence[float]
) -> dict[str, float]:
    """The arithmetic behind :func:`quantile_metrics`, on arrays that are already aligned.

    Public, and separate from the frame-level function above, because card #29's bootstrap
    calls it tens of thousands of times: 2,000 replicates across every subgroup and both
    scales. Paying for a ``DataFrame`` construction and a column-name check on each of those
    would make the interval cost more than the run that produced the predictions, and
    re-implementing the seven metrics beside it would mean the published interval was around
    a *different* statistic from the published point estimate -- which is the failure mode a
    thesis chapter cannot survive. One definition, two entry points, and the checking lives
    at the frame-level one where a caller can still make the mistake it catches.

    Args:
        truth: ``(n,)`` observations, in whatever space the caller is reporting.
        heads: ``(n, len(quantiles))`` predictions, columns in ``quantiles`` order.
        quantiles: The alphas, ascending.

    Returns:
        The dictionary :func:`quantile_metrics` documents.
    """
    median = heads[:, len(quantiles) // 2]
    residual = truth - median

    total = float(((truth - truth.mean()) ** 2).sum())
    pinball = float(
        np.mean(
            [
                np.mean(np.maximum(alpha * (truth - heads[:, at]), (alpha - 1.0) * (truth - heads[:, at])))
                for at, alpha in enumerate(quantiles)
            ]
        )
    )
    low, high = heads[:, 0], heads[:, -1]
    # Any adjacent pair out of order, not just the outermost: MultiQuantile fits the heads
    # jointly but does not constrain them to be monotone, and a P50 above the P90 is as much
    # a broken interval as a P10 above it. Measured at 23 % of rows on a small fit, so this
    # is a real number to report rather than a defensive zero.
    crossings = float(np.mean(np.any(np.diff(heads, axis=1) < 0.0, axis=1)))
    return {
        "r2": float("nan") if total == 0.0 else 1.0 - float((residual**2).sum()) / total,
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "mae": float(np.mean(np.abs(residual))),
        "pinball": pinball,
        "interval_coverage": float(np.mean((truth >= low) & (truth <= high))),
        "interval_width": float(np.mean(high - low)),
        "crossings": crossings,
    }


def scored_table(
    frame: pd.DataFrame,
    model: QuantileModel,
    *,
    settings: ModelSettings,
    target_column: str,
) -> pd.DataFrame:
    """One row per scored row: what the truth was, what the heads said, in both spaces.

    **The unit the bootstrap resamples.** Before this existed, :func:`_score_fold` computed
    ``model.predict(scored)``, handed it to :func:`quantile_metrics` and dropped the frame, so
    the only resamplable object a nested run left behind was five fold scores -- a spread card
    #24 measured to be confounded with training size, since screening removes between 15 and
    144 of a fold's ~710 rows. Card #29 needs an interval over *rows*, so the rows are kept.

    **Both spaces, neither derived from the other.** The booster is fitted on ``log1p``
    capacity and :meth:`QuantileModel.predict` back-transforms with ``expm1``; taking the
    model-space columns by re-transforming the weight-percent ones would be a round trip, and
    card #11 measured that ``expm1(log1p(y))`` returns ``y`` exactly on only 794 of 1,279
    rows. So the heads come from :meth:`QuantileModel.predict` and
    :meth:`QuantileModel.predict_model_space` separately, and the truth from the frame's own
    two columns.

    **What rides along, and why each one.** The canonical key, because
    :func:`~hydms.data.canonical.group_keys` is the project's one definition of "the same
    material" and card #29's bootstrap resamples groups rather than rows -- re-deriving it
    downstream would be a fourth meaning of the phrase. The temperature, because the card
    asks for a per-temperature breakdown and reading it back out of the matrix would mean
    re-featurising 1,278 rows to recover one column.

    Args:
        frame: The rows being scored, record and matrix side by side.
        model: The fitted model. Called, never refitted.
        settings: The settings the fit was made under. ``temperature`` is read from them.
        target_column: The raw target, already resolved -- see :func:`_resolve`.

    Returns:
        A frame on ``frame``'s index, carrying the truth in both spaces, one column per head
        in both spaces, the canonical key and the temperature.

    Raises:
        ModelError: the frame carries neither target column, or has lost the canonical key.
    """
    raw, transformed = _columns(target_column)
    table = pd.DataFrame(index=frame.index)
    table[raw] = _truth(frame, target_column)
    table[transformed] = _target(frame, target_column)

    for name, values in (("", model.predict(frame)), ("log_", model.predict_model_space(frame))):
        for column in values.columns:
            table[f"{name}{column}"] = values[column]

    if CANONICAL_KEY_COLUMN not in frame.columns:
        raise ModelError(
            f"the scored rows carry no {CANONICAL_KEY_COLUMN!r} column, so the predictions "
            f"cannot be grouped by material. It is attached by "
            f"hydms.data.metadata.with_metadata, which capacity_matrix calls; a frame "
            f"assembled some other way has to attach it too."
        )
    table[CANONICAL_KEY_COLUMN] = frame[CANONICAL_KEY_COLUMN]
    if settings.temperature is not None and settings.temperature in frame.columns:
        table[settings.temperature] = frame[settings.temperature]
    return table


# --------------------------------------------------------------------------------------
# The contender -- card #88's protocol, with this model in it
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Configuration:
    """What one outer fold's search settled on, and what it cost to find out.

    Stored by :func:`~hydms.surrogate.validation.nested_scores` in ``Evaluation.chosen`` and
    never inspected by it. Card #29 reads it; so does anybody asking whether two folds chose
    the same model.

    Attributes:
        params: The winning hyperparameters, as CatBoost takes them.
        objective: The inner-fold pinball loss they achieved. Lower is better.
        trials: How many trials ran, pruned ones included.
        pruned: How many of them were pruned.
        seconds: Wall time of the whole search.
        features: The feature set fitted on, recorded here because a score belongs to a
            feature set and card #25's is not the published 22.
    """

    params: Mapping[str, Any]
    objective: float
    trials: int
    pruned: int
    seconds: float
    features: tuple[str, ...] = ()

    def row(self) -> dict[str, object]:
        """One row of the chosen-hyperparameter table."""
        return {
            "objective": self.objective,
            "trials": self.trials,
            "pruned": self.pruned,
            "seconds": round(self.seconds, 1),
            "features": len(self.features),
            **{
                f"{PARAM_PREFIX}{name}": value
                for name, value in sorted(self.params.items())
            },
        }


@dataclass(frozen=True)
class _FoldRows:
    """One inner fold, reduced to the three row sets a fit needs. Computed once per fold."""

    fold: Fold
    fitting: tuple[Hashable, ...]
    stopping: tuple[Hashable, ...]
    scoring: tuple[Hashable, ...]
    removed: tuple[Hashable, ...]


def _prepare(
    frame: pd.DataFrame,
    fold: Fold,
    *,
    settings: ModelSettings,
    target_column: str,
) -> _FoldRows:
    """Screen a fold's training rows and cut its stopping slice. Once, before the trials.

    This is the expensive-but-fixed half of a fold: CleanLab costs about fourteen seconds and
    the answer does not depend on any hyperparameter, so doing it here rather than inside the
    objective divides the run's screening cost by the trial count.
    """
    kept = screened_rows(
        frame, list(fold.train), settings=settings, target_column=target_column
    )
    fitting, stopping = stopping_slice(
        frame, kept.kept, settings=settings, name=f"{fold.name}-stop"
    )
    return _FoldRows(
        fold=fold,
        fitting=fitting,
        stopping=stopping,
        scoring=tuple(fold.test),
        removed=kept.removed,
    )


def _score_fold(
    frame: pd.DataFrame,
    rows: _FoldRows,
    params: Mapping[str, Any],
    *,
    settings: ModelSettings,
    target_column: str,
    where: str,
    log: FitLog | None,
    keep: Callable[[pd.DataFrame], None] | None = None,
) -> dict[str, float]:
    """Fit on one fold's rows and score it on the rows that fit never saw.

    ``keep`` is where the row-level predictions go when somebody wants them, and it is
    ``None`` everywhere else. The distinction is not tidiness: the *search* calls this
    function once per trial per inner fold -- 375 times in a configured run, thousands at the
    archival trial count -- and holding a frame for each of those would be a record of every
    fit the search made rather than of the run's result. Only the scored fits, one per outer
    fold, hand their predictions on; that is card #29's out-of-fold table.
    """
    model = fit_quantile_model(
        frame,
        train=rows.fitting,
        eval_on=rows.stopping,
        scored_on=rows.scoring,
        where=where,
        params=params,
        settings=settings,
        target_column=target_column,
        removed=rows.removed,
        log=log,
    )
    scored = frame.loc[list(rows.scoring)]
    truth = _truth(scored, target_column)
    metrics = quantile_metrics(truth, model.predict(scored), settings.quantiles)
    metrics["rows_fitted"] = float(len(rows.fitting))
    metrics["rows_scored"] = float(len(rows.scoring))
    if keep is not None:
        keep(
            scored_table(
                scored, model, settings=settings, target_column=target_column
            )
        )
    return metrics


def capacity_contender(
    *,
    name: str = "catboost-multiquantile",
    settings: ModelSettings | None = None,
    target_column: str | None = None,
    log: FitLog | None = None,
    log_trials: bool = False,
) -> Contender:
    """This model as a contender for :func:`~hydms.surrogate.validation.nested_scores`.

    The two moments card #88's protocol asks for, and nothing else. ``tune`` sees one outer
    fold's *training* rows and the inner folds cut from them; ``score`` refits the winner on
    those same training rows and is scored on the outer fold's held-out ones, which the search
    never saw. No fold is both tuned on and scored on, and the protocol -- not this function --
    is what asserts it.

    **The budget is a product and it is worth writing out.** ``model.cv_folds`` outer x
    ``model.inner_cv_folds`` inner x ``model.optuna_trials`` per contender, plus one refit per
    outer fold. At the archival trial count of 300 that is 4,500 fits, and card #26's
    narrative records what that measured out at on this machine and what ``pipeline.yaml``
    was set to as a result. The nesting is never what gets collapsed to afford it: three inner
    folds tuned and scored in one pass is leak L4 returning.

    **Selection does not run in here.** The feature set is
    :data:`~hydms.descriptors.contract.SELECTED`, fixed, for the reason this module's
    docstring gives -- so every number this contender produces belongs to a fixed fourteen and
    not to the procedure that chose them.

    Args:
        name: What appears in the :class:`~hydms.qa.detectors.SelectionRecord`.
        settings: Defaults to :meth:`ModelSettings.from_config`.
        target_column: Defaults to ``columns.target``.
        log: A :class:`FitLog` to record the scored fits into -- one per outer fold. The L5
            sentinel passes one and reads it back; that is how it checks a real run rather
            than a description of one.
        log_trials: Also record every fit the *search* made. Off by default because a record
            holds row identities and a real search makes thousands of fits: at the configured
            budget that is a list of some two million labels, for a run whose honesty is
            already guaranteed by :func:`fit_quantile_model` refusing to fit otherwise. The
            sentinels turn it on, because under :data:`SENTINEL_BUDGET` the search makes six
            fits per fold and checking them is then free.

    Returns:
        A :class:`~hydms.surrogate.validation.Contender`.
    """
    active = settings if settings is not None else ModelSettings.from_config()
    # Once, when the contender is built -- not once per fit. See `_resolve`.
    target = _resolve(active, target_column)

    def tune(task: TuningTask) -> Configuration:
        started = time.perf_counter()
        prepared = [
            _prepare(task.frame, fold, settings=active, target_column=target)
            for fold in task.folds
        ]

        def objective(trial: Any) -> float:
            params = {knob.name: knob.suggest(trial) for knob in active.space}
            losses: list[float] = []
            for step, rows in enumerate(prepared):
                metrics = _score_fold(
                    task.frame,
                    rows,
                    params,
                    settings=active,
                    target_column=target,
                    where=f"{task.outer} / {rows.fold.name} / trial {trial.number}",
                    log=log if log_trials else None,
                )
                losses.append(metrics["pinball"])
                trial.report(float(np.mean(losses)), step)
                if trial.should_prune():
                    raise _optuna().TrialPruned()
            return float(np.mean(losses))

        study = _study(active)
        study.optimize(objective, n_trials=active.optuna_trials)
        states = [trial.state.name for trial in study.trials]
        return Configuration(
            params=dict(study.best_params),
            objective=float(study.best_value),
            trials=len(states),
            pruned=sum(1 for state in states if state == "PRUNED"),
            seconds=time.perf_counter() - started,
            features=tuple(active.features),
        )

    def score(configuration: Any, task: ScoringTask) -> Mapping[str, float]:
        kept = screened_rows(
            task.train, list(task.train.index), settings=active, target_column=target
        )
        fitting, stopping = stopping_slice(
            task.train, kept.kept, settings=active, name=f"{task.fold.name}-stop"
        )
        frame = pd.concat([task.train, task.test])
        rows = _FoldRows(
            fold=task.fold,
            fitting=fitting,
            stopping=stopping,
            scoring=tuple(task.test.index),
            removed=kept.removed,
        )
        return _score_fold(
            frame,
            rows,
            configuration.params,
            settings=active,
            target_column=target,
            where=task.fold.name,
            log=log,
            # The one place predictions are kept. `task.keep` is the protocol's sink; a
            # contender that never calls it leaves `Evaluation.out_of_fold` empty, which is
            # exactly what every contender did before card #29.
            keep=task.keep,
        )

    return Contender(name=name, tune=tune, score=score)


def _optuna() -> Any:
    """Optuna, imported lazily. Only the search needs it; a fit does not."""
    import optuna

    return optuna


def _study(settings: ModelSettings) -> Any:
    """A minimising TPE study, seeded, with a pruner that can actually fire.

    The sampler is the archival one -- ``TPESampler(seed=...)`` -- and the seed is
    ``pipeline.yaml``'s, so AC-1 can ask the same question of the search that it asks of the
    splits. **Every outer fold's search is seeded identically**, which is deliberate: the
    first trials are then the same design in every fold, so a fold that settles somewhere else
    settled there because of its rows and not because of its draw. TPE adapts to each fold's
    own objective after its startup trials, so the searches diverge where it matters.

    **The pruner is not the archival one, because the archival one never pruned.**
    ``Catboostmodel.py:541`` is ``MedianPruner(n_startup_trials=5, n_warmup_steps=10,
    interval_steps=3)`` and ``:583`` reports one step per cross-validation fold, of which
    there were ten -- steps 0 to 9, every one of them below the ten-step warmup. The pruning
    branch at ``:584-585`` was unreachable for the whole published run. Here there are three
    inner folds and the warmup is one, so a trial that is losing after the first fold stops
    after the first fold.

    The direction is ``minimize``: the objective is the pinball loss the quantile heads are
    actually fitted against, not the R² of the median. Selecting a three-headed model by the
    R² of one head throws away the other two.
    """
    optuna = _optuna()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    return optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=settings.seed),
        pruner=optuna.pruners.MedianPruner(
            n_startup_trials=5, n_warmup_steps=1, interval_steps=1
        ),
    )
