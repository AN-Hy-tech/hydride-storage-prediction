"""L3 -- what turns three raw quantile heads into an interval that means its own number.

CatBoost's ``MultiQuantile`` heads are fitted, not calibrated. Card #26 measured what that
costs on this data: the P10-P90 band covered **64.4 %** of held-out rows against a nominal
80 %, and it under-covered in every one of five nested folds (0.57, 0.63, 0.70, 0.69, 0.63).
So this module is not a formality laid on top of an honest interval -- it is the thing that
makes the interval honest, and gate AC-3 has a real gap to close rather than a rounding.

Conformalized quantile regression (Romano, Patterson & Candès 2019) fixes that with one
number: the empirical quantile of the calibration set's conformity scores, added to the upper
head and subtracted from the lower. It is distribution-free and finite-sample -- it assumes
only exchangeability -- and it is what gives AC-3 something to certify.

Six decisions, each of which could have gone the other way.

**CQR over a single ``MultiQuantile`` model, through MAPIE's ``prefit=True``.** MAPIE's
``prefit=False`` path fits the heads itself and accepts exactly four named scikit-learn
estimators; CatBoost is not among them, and no amount of duck typing gets in. ``prefit=True``
takes a list of three *already fitted* regressors, which is the shape card #26's model can be
made to fit -- except that each must return one column and a ``MultiQuantile`` booster returns
three. Hence :class:`_Head`, three thin adapters over one model. The alternatives were
rejected on measurement rather than taste: one CatBoost per quantile triples a search budget
already at 3.5 h **and** forfeits the zero-crossing property #26 measured, because nothing
holds three independently fitted heads in order and CQR's widening cannot repair a crossing;
split conformal around the median was killed by the width measurement below.

**The heads arrive in the order [lower, upper, median], with the median last.** MAPIE's
``_MapieQuantileRegressor`` sets ``single_estimator_ = self.estimators_[2]`` and computes its
conformity scores from positions 0 and 1. That is exactly the positional trap
:func:`~hydms.surrogate.model.column_names` exists to kill, reappearing at the library
boundary -- so :func:`fit_conformal` asserts it rather than trusting this paragraph, in two
ways: MAPIE's own public ``predict`` must return the median head, and the estimator list must
hold the adapters this module put there.

**The band is 80 %, and it is ``conformal.confidence_level`` that moved.** ``pipeline.yaml``
shipped asserting two incompatible things -- heads at [0.1, 0.5, 0.9], an 80 % band, beside a
confidence level of 0.90, which tells MAPIE to expect heads at 0.05 and 0.95. CQR's prefit
contract is exact, so this is a precondition and not a preference. The level moved rather than
the heads because moving the heads refits the model and invalidates #26's 64.4 % baseline;
moving the level costs nothing measured. :func:`hydms.config._validate` now refuses a
configuration where the two disagree.

**Calibration happens once, on the final fit, from rows carved out of ``train``.** Not inside
every outer fold: PRD AC-3 says "coverage on the held-out test set", and a per-fold
calibration would spend training rows the folds cannot spare and would move #26's baseline
under a new partition. Not from ``val`` either -- val chose the stopping iteration, so
conformalising on it recycles data the model was already selected against. The cut is
:func:`calibration_slice`, one fold of ``model.calibration_folds`` through
:func:`~hydms.surrogate.validation.grouped_folds`, because a calibration set that is not
group-disjoint on the canonical composition is leak L8 at a new stage. **State the cost**: at
five folds the deployed model then grows on roughly 714 rows where the cross-validation that
estimated its performance fitted on roughly 893. That asymmetry is real, and
:mod:`hydms.surrogate.calibrate` reports it.

**One constant, not two, chosen before any number was seen.** MAPIE defaults to two, one per
head at ``alpha/2``, which is tighter when the miscoverage is one-sided. The trap is that the
two *cannot be compared on evidence*: coverage on the calibration set is nominal by
construction for both, so the comparison is empty, and comparing them on the test set is leak
L2 in a new place -- selecting a calibration rule with the data that certifies it. Decided a
priori: symmetric is the form Romano et al. report coverage for, it estimates one quantile
rather than two from the same ~179 rows, and it puts one number in the manifest. The one-sided
miscoverage is reported as a diagnostic and is not acted on.

**What is persisted is the constant, not the calibrator.** Card #23 made this decision once
already, the other way round: :class:`~hydms.surrogate.scaler.FittedScaler` stores medians and
IQRs rather than a ``RobustScaler``, so "a scikit-learn upgrade cannot change what a saved
``v1`` does". A conformalised CQR object is strictly worse to pickle -- MAPIE wrapping three
adapters wrapping one booster, four surfaces that must all still unpickle when Chapter 3 is
examined. So :class:`FittedConformal` is a value with one float in it, **MAPIE is a fit-time
dependency and is never imported at predict time**, and
``tests/surrogate/test_conformal.py`` proves that in a subprocess.

MAPIE is used anyway, rather than hand-rolling ten lines, for one reason: the
``ceil((n + 1) * (1 - alpha)) / n`` finite-sample correction is exactly the off-by-one a reimplementation gets
subtly wrong, and **a wrong conformal constant is invisible** -- it under- or over-covers by a
few points, which is precisely and only what AC-3 measures. A hand-roll would therefore use
AC-3 to check the thing AC-3 exists to certify. So MAPIE fits, the constant is extracted, and
:func:`fit_conformal` asserts that applying the stored constant reproduces MAPIE's own
``predict_interval`` to 1e-12 before returning. Same pattern as gate AC-2.

**Why CQR and not split conformal.** On outer-0's 185 held-out rows the raw P10-P90 width has
a coefficient of variation of **0.572** -- p25 0.459, median 0.611, p75 0.847, max 2.315, a
12.2x spread -- and ``Spearman(width, |median error|) = +0.474``: the band is wider where the
model is wrong. CQR adds a constant to both heads, so the calibrated width inherits that
spread. ``SplitConformalRegressor`` with the ``"absolute"`` score would replace the whole
distribution with one number, and ranking by lower confidence bound would reduce to ranking by
mean minus a constant -- losing the mitigation risk R1 depends on. Two caveats belong here
rather than in folklore: +0.474 is moderate, not strong, and the model measured was tuned by a
two-trial probe.

**The arithmetic is in model space.** ``log1p`` capacity, the space the booster was fitted in,
which is what :meth:`~hydms.surrogate.model.QuantileModel.predict_model_space` exists for.
Coverage is invariant under a monotone map, so calibrating there and transforming back gives
the same guarantee in weight percent; what it changes is the *shape* of the widening, which
stays proportional rather than additive once ``expm1`` has run.

Card #27.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NoReturn

import numpy as np
import pandas as pd

from hydms.config import Config
from hydms.config import load as load_config
from hydms.data.canonical import group_keys
from hydms.data.target import to_wt_pct
from hydms.qa.detectors import assert_disjoint_groups
from hydms.surrogate.model import (
    ModelSettings,
    QuantileModel,
    _owned,  # the one definition of "the rows this fit owns"; see the note at its use
    column_names,
)
from hydms.surrogate.validation import grouped_folds

__all__ = [
    "CONFORMAL_PAYLOAD",
    "PARITY_TOLERANCE",
    "SYMMETRIC",
    "ConformalError",
    "FittedConformal",
    "calibrated_heads",
    "calibration_groups",
    "calibration_slice",
    "compare_metrics",
    "conformal_from",
    "fit_conformal",
]

# Same convention as `hydms/surrogate/scaler.py` and `hydms/surrogate/model.py`: the total is
# always reported, the listing is truncated.
_MAX_NAMED = 8

#: The payload key the fitted calibration is saved under, so ``artifacts/v{N}/conformal`` is
#: spelled once rather than at every call site. :func:`conformal_from` reads it back; card #34
#: writes it beside :data:`~hydms.surrogate.scaler.SCALER_PAYLOAD`.
CONFORMAL_PAYLOAD = "conformal"

#: One constant for both heads, not one per head. Decided a priori and not from data -- see
#: this module's docstring for why the alternative cannot be chosen on evidence at all. It is
#: named rather than passed so that the decision has a single site and a reader can find every
#: use of it.
SYMMETRIC = True

#: How closely the stored constant must reproduce MAPIE's own ``predict_interval``. Not an
#: equality: ``(lower - Q)`` subtracted back from ``lower`` is a float round trip and lands
#: within about 1e-16 relative. 1e-12 is this project's tolerance throughout -- gate AC-2 uses
#: it, and `nothing here compares floats with equality`.
PARITY_TOLERANCE = 1e-12

#: The head CQR reports its interval around, and the one MAPIE keeps at position 2.
MEDIAN = 0.5


class ConformalError(ValueError):
    """The calibration cannot be fitted, or is being applied to the wrong prediction.

    A ``ValueError``, like :class:`~hydms.surrogate.scaler.ScalerError`,
    :class:`~hydms.surrogate.model.ModelError` and the data layer's errors below it: a guard
    refusing, naming what it refused.
    """


def _named(items: Iterable[object]) -> str:
    """Render offenders for a message: sorted, truncated, and counted."""
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    shown = ", ".join(listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


def _head_columns(quantiles: Sequence[float]) -> tuple[str, str, str]:
    """The ``(lower, upper, median)`` column names of a quantile set.

    In *this* order, deliberately, because it is the order MAPIE's prefit list wants and the
    single place in this project that has to know it. Everything else here addresses the heads
    by name.
    """
    names = column_names(quantiles)
    median_at = [at for at, q in enumerate(quantiles) if abs(q - MEDIAN) <= PARITY_TOLERANCE]
    if not median_at:
        raise ConformalError(
            f"the quantiles {list(quantiles)} have no median head. Conformalized quantile "
            f"regression reports an interval around the median, and MAPIE's prefit list "
            f"takes it as its third entry."
        )
    if len(names) < 3:
        raise ConformalError(
            f"conformalized quantile regression needs a lower, an upper and a median head; "
            f"the quantiles {list(quantiles)} give {len(names)}."
        )
    return names[0], names[-1], names[median_at[0]]


# --------------------------------------------------------------------------------------
# The value that is stored
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class FittedConformal:
    """A conformal correction: one number, and the accounting that says what it means.

    Constructed only by :func:`fit_conformal` and read back only by :func:`conformal_from`. It
    is the object stored as ``conformal`` in an artifact version, so its fields are also its
    provenance -- a reader of ``artifacts/v{N}/`` can see how many rows produced the constant
    and which band it was calibrated for, without unpickling a library object.

    There is deliberately no MAPIE object in here and no import of MAPIE in this module's
    import path. See the module docstring.

    Attributes:
        correction: The constant, **in model space** (``log1p`` weight percent). Subtracted
            from the lower head and added to the upper. A *negative* value is legal and means
            the raw heads over-covered and the band narrows; it is recorded, not refused.
        confidence_level: The nominal coverage the constant targets. ``conformal.confidence_level``.
        quantiles: The heads it belongs to, in the model's column order.
        lower: The column widened downward.
        upper: The column widened upward.
        median: The column left alone -- the point the interval is reported around.
        calibration_rows: How many rows the constant was estimated from. The finite-sample
            correction is a function of this, so it is not decoration.
        fitted_on: What those rows were, for the message and the model card: ``"train"``.
        symmetric: Whether one constant covers both heads. Always :data:`SYMMETRIC`; recorded
            because a stored artifact must say which rule produced it.
        mapie_version: The version that fitted it. Recorded rather than depended on: nothing
            reads it back, and it is what makes an AC-1 reproducibility failure legible.
    """

    correction: float
    confidence_level: float
    quantiles: tuple[float, ...]
    lower: str
    upper: str
    median: str
    calibration_rows: int
    fitted_on: str
    symmetric: bool = SYMMETRIC
    mapie_version: str = ""

    def __post_init__(self) -> None:
        if not math.isfinite(self.correction):
            raise ConformalError(
                f"the conformal correction is {self.correction}, which is not a finite "
                f"number. Every interval would come back as NaN or infinite and nothing "
                f"downstream would raise -- a candidate with an infinite band ranks by its "
                f"lower bound of minus infinity."
            )
        if not 0.0 < self.confidence_level < 1.0:
            raise ConformalError(
                f"the confidence level is {self.confidence_level}, which is not a coverage "
                f"probability. MAPIE 1.x takes a level, not an alpha -- 0.8, not 0.2."
            )
        if self.calibration_rows <= 0:
            raise ConformalError(
                f"a correction estimated from {self.calibration_rows} row(s) is not a "
                f"conformal guarantee. The finite-sample quantile is a function of that "
                f"count."
            )
        names = set(column_names(self.quantiles))
        outside = [
            name for name in (self.lower, self.upper, self.median) if name not in names
        ]
        if outside:
            raise ConformalError(
                f"column(s) {_named(outside)} are not heads of the quantiles "
                f"{list(self.quantiles)}, whose columns are {_named(names)}. The correction "
                f"belongs to a model with those heads and to no other."
            )
        if self.lower == self.upper:
            raise ConformalError(
                f"the lower and upper heads are the same column, {self.lower!r}. A band of "
                f"zero width widened by a constant is not an interval, it is a point with "
                f"error bars nobody fitted."
            )

    # ----------------------------------------------------------------------------------
    # The one thing it does
    # ----------------------------------------------------------------------------------

    def apply(self, heads: pd.DataFrame) -> pd.DataFrame:
        """Widen the outer heads by the constant. Model space in, model space out.

        The frame comes back with the **same columns in the same order**, which is what makes
        the before-and-after a single column comparison:
        :func:`~hydms.surrogate.model.quantile_metrics` accepts either frame unchanged, so
        ``interval_coverage`` raw against ``interval_coverage`` calibrated needs no new
        measurement code. The median column is copied through untouched -- CQR corrects the
        band, never the point.

        Args:
            heads: :meth:`~hydms.surrogate.model.QuantileModel.predict_model_space`'s output,
                or anything carrying the same columns on any index.

        Returns:
            ``(len(heads), len(heads.columns))`` of ``float64``, on the caller's index. The
            input is never modified.

        Raises:
            ConformalError: it is not a frame, or its columns are not this correction's heads.
        """
        if not isinstance(heads, pd.DataFrame):
            raise ConformalError(
                f"a correction widens a DataFrame of named heads, not a "
                f"{type(heads).__name__}. An array carries no column names, so widening "
                f"column 0 would be a guess about which head is the lower one -- the guess "
                f"hydms.surrogate.model.column_names exists to remove."
            )
        expected = list(column_names(self.quantiles))
        if list(heads.columns) != expected:
            raise ConformalError(
                f"this correction belongs to heads {expected} and the frame carries "
                f"{list(heads.columns)}. Position identifies a quantile in CatBoost's output "
                f"and nothing else does, so a differently ordered frame is a different model."
            )
        values = heads.to_numpy(dtype="float64", copy=True)
        finite = np.isfinite(values)
        if not finite.all():
            rows = heads.index[~finite.all(axis=1)]
            raise ConformalError(
                f"{len(rows)} of {len(heads)} row(s) carry a head that is not a finite "
                f"number: row(s) {_named(rows)}. Widening a NaN produces a NaN interval that "
                f"covers nothing and reports no error."
            )
        widened = pd.DataFrame(values, index=heads.index, columns=expected)
        widened[self.lower] = widened[self.lower] - self.correction
        widened[self.upper] = widened[self.upper] + self.correction
        return widened

    # ----------------------------------------------------------------------------------
    # The things it refuses to do
    # ----------------------------------------------------------------------------------

    def fit(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Always raises. A fitted correction is a value; re-estimating it is the leak."""
        self._refuse("fit")

    def conformalize(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Always raises -- MAPIE's own name for the step, and the one that hides a recalibration."""
        self._refuse("conformalize")

    def _refuse(self, method: str) -> NoReturn:
        raise ConformalError(
            f"{method}() does not exist on a fitted correction, deliberately. This constant "
            f"was estimated from {self.calibration_rows} {self.fitted_on} row(s) held out of "
            f"the model stored beside it, and re-estimating it from the rows being predicted "
            f"gives a band calibrated on its own answers -- nominal coverage by construction, "
            f"and no guarantee at all. Fit a new one with "
            f"hydms.surrogate.conformal.fit_conformal() only as part of training a new "
            f"artifact version."
        )

    # ----------------------------------------------------------------------------------
    # Reading it
    # ----------------------------------------------------------------------------------

    def describe(self) -> pd.DataFrame:
        """One row: the constant and everything needed to read it. For the model card (#83)."""
        return pd.DataFrame(
            [
                {
                    "correction_model_space": self.correction,
                    "confidence_level": self.confidence_level,
                    "lower_head": self.lower,
                    "median_head": self.median,
                    "upper_head": self.upper,
                    "calibration_rows": self.calibration_rows,
                    "fitted_on": self.fitted_on,
                    "symmetric": self.symmetric,
                    "mapie_version": self.mapie_version,
                }
            ],
            index=pd.Index(["conformal"], name="payload"),
        )


def calibrated_heads(
    model: QuantileModel, features: pd.DataFrame, *, conformal: FittedConformal
) -> pd.DataFrame:
    """The model's heads, widened and returned in **weight percent**.

    The composition every reader of an interval wants, in one call, so that "predict then
    widen then transform" cannot be assembled in the wrong order somewhere downstream. Card
    #28 builds the public ``predict()`` on this; card #29 scores against it.

    Exact, not approximate, for the same reason
    :meth:`~hydms.surrogate.model.QuantileModel.predict` gives: ``expm1`` is strictly
    increasing, so transforming a calibrated model-space interval preserves both its ordering
    and its coverage. Nothing is clipped -- a negative lower band is the signal cards #48 and
    #77 act on.

    Raises:
        ConformalError: the correction and the model have different heads.
        ModelError: the batch is not a frame, or does not carry the fitted columns.
        TargetError: a widened head overflows ``expm1`` -- a broken model, not a prediction.
    """
    if tuple(model.quantiles) != tuple(conformal.quantiles):
        raise ConformalError(
            f"the model has heads {list(model.quantiles)} and the correction was fitted for "
            f"{list(conformal.quantiles)}. A conformal constant belongs to the heads it "
            f"calibrated and to no others; they come out of one artifact version together."
        )
    widened = conformal.apply(model.predict_model_space(features))
    return pd.DataFrame(
        {name: to_wt_pct(widened[name]) for name in widened.columns},
        index=widened.index,
        columns=list(widened.columns),
    )


# --------------------------------------------------------------------------------------
# The calibration slice
# --------------------------------------------------------------------------------------


def calibration_slice(
    frame: pd.DataFrame,
    labels: Sequence[Hashable],
    *,
    settings: ModelSettings | None = None,
    config: Config | None = None,
    name: str = "calibration",
) -> tuple[tuple[Hashable, ...], tuple[Hashable, ...]]:
    """Split training rows into the rows the model grows on and the rows that calibrate it.

    The same shape as :func:`~hydms.surrogate.model.stopping_slice`, and cut by the same
    generator for the same reason: a calibration set that shares a composition with the
    fitting rows is leak L8 at a new stage, and the conformity scores would then be residuals
    on materials the trees have already seen -- systematically too small, and a band that
    under-covers exactly where it claims not to.

    It is one fold of ``model.calibration_folds``, so a fifth of the rows at the configured
    five. The rows come out of ``train`` and never out of ``val``: val chose the stopping
    iteration, and calibrating on it recycles data the model was already selected against.

    Args:
        frame: The rows this fit could see, with formula, temperature and target columns --
            the fold generator stratifies on them.
        labels: The training rows, already screened.
        settings: For the seed. Defaults to :meth:`~hydms.surrogate.model.ModelSettings.from_config`.
        config: For ``model.calibration_folds``. Defaults to the packaged configuration.
        name: Prefix for the generated fold names, for messages.

    Returns:
        ``(fitting labels, calibration labels)``, both in frame order.

    Raises:
        ModelError: ``labels`` is empty, repeats, or names an unknown row.
        ValidationError: too few compositions to cut the slice.
        LeakDetected: a composition landed on both sides -- asserted by the fold generator
            rather than assumed.
    """
    cfg = config if config is not None else load_config()
    active = settings if settings is not None else ModelSettings.from_config(cfg)
    # `_owned` rather than a second copy of the same three checks. "The rows a fit owns" has
    # one definition in this layer, in the module that fits; a calibration carve that
    # disagreed with it about a repeated label would be a row counted twice in one place and
    # once in the other.
    owned = _owned(frame, labels, what="held out for calibration")
    folds = grouped_folds(
        owned, splits=cfg.model.calibration_folds, seed=active.seed, name=name
    )
    slice_ = folds[0]
    return tuple(slice_.train), tuple(slice_.test)


# --------------------------------------------------------------------------------------
# The adapters -- one column each, over one model
# --------------------------------------------------------------------------------------


class _Head:
    """One column of a ``MultiQuantile`` model, wearing enough of scikit-learn to satisfy MAPIE.

    MAPIE's prefit path asks two things of each estimator it is handed: that it have ``fit``
    and ``predict`` (:func:`mapie.utils._check_estimator_fit_predict`), and that it look
    fitted (:func:`mapie.utils.check_sklearn_user_model_is_fitted`). The second is why
    :attr:`fitted_` exists and why ``n_features_in_`` deliberately does **not**: MAPIE probes
    any estimator carrying ``n_features_in_`` by calling ``predict(np.zeros((1, n)))``, and
    this adapter refuses a bare array on purpose -- an unnamed matrix is how a permuted batch
    returns plausible, wrong numbers, which is the failure gate AC-4 exists for. Carrying
    ``fitted_`` alone satisfies the check without inviting the probe.

    These objects live for the length of one :func:`fit_conformal` call. Nothing stores them,
    nothing pickles them, and that is what makes three wrappers over one booster cheap: the
    artifact holds a float.
    """

    #: One of `mapie.utils.FIT_INDICATORS`. See the class docstring for why this one.
    fitted_ = True

    def __init__(self, model: QuantileModel, column: str) -> None:
        self.model = model
        self.column = column

    def fit(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ConformalError(
            "this adapter wraps an already-fitted model and cannot be fitted. MAPIE is used "
            "here in prefit mode precisely so that the booster card #26 fitted is the one "
            "being calibrated; a fit reaching here means `prefit=True` was dropped."
        )

    def predict(self, features: Any, **kwargs: Any) -> np.ndarray:
        """This head's column, as a 1-D array, on the rows given."""
        return (
            self.model.predict_model_space(features)[self.column]
            .to_numpy(dtype="float64")
        )

    def __repr__(self) -> str:  # pragma: no cover -- for a failure message
        return f"_Head({self.column!r})"


def _mapie() -> tuple[Any, str]:
    """MAPIE's CQR and the installed version, imported lazily.

    Deferred for two reasons and not one. The first is this layer's usual one -- ``import
    hydms.surrogate`` must stay answerable on an interpreter with no scientific stack, the
    same reason :func:`hydms.surrogate.scaler._robust_scaler` defers scikit-learn. The second
    is the load-bearing one: **MAPIE is a fit-time dependency**. It is an optional extra
    (``pip install hydms[uq]``), the prediction path never touches it, and a stored artifact
    holds a float rather than anything MAPIE built -- so a service that only predicts need not
    have it installed at all, and a MAPIE upgrade cannot change what a saved ``v1`` does.
    """
    try:
        from mapie import __version__ as version
        from mapie.regression import ConformalizedQuantileRegressor
    except ImportError as exc:  # pragma: no cover -- exercised only without the extra
        raise ConformalError(
            "conformal calibration is MAPIE's and it is not importable here. It is an "
            "optional dependency because it is needed to *fit* a calibration and never to "
            "apply one: `pip install -e '.[uq]'`. See docs/ENVIRONMENT.md."
        ) from exc
    return ConformalizedQuantileRegressor, str(version)


# --------------------------------------------------------------------------------------
# The fit
# --------------------------------------------------------------------------------------


def fit_conformal(
    frame: pd.DataFrame,
    model: QuantileModel,
    *,
    calibrate_on: Sequence[Hashable],
    config: Config | None = None,
    target_column: str | None = None,
) -> FittedConformal:
    """Calibrate a fitted model's band on rows it has never seen, and keep the constant.

    The calibration rows must be disjoint from every role the model's own fit gave a row, and
    this checks that against :attr:`~hydms.surrogate.model.QuantileModel.record` rather than
    against an assumption about which slice the fit chose. That matters because the
    early-stopping rows are not a configuration value but a *cut*:
    :func:`~hydms.surrogate.model.stopping_slice` carves one fold out of the rows each fit
    owns, per fit, so "disjoint from the early-stopping split" is only checkable by reading
    what that fit actually did. The record is the reading.

    Args:
        frame: The rows this run could see, features and record side by side --
            :func:`~hydms.surrogate.model.capacity_matrix`'s first return.
        model: The fitted model whose band is being calibrated. Its ``record`` is read; its
            booster is called, never refitted.
        calibrate_on: The calibration rows, from :func:`calibration_slice`.
        config: Defaults to the packaged configuration. ``conformal.confidence_level``.
        target_column: Defaults to ``columns.target``.

    Returns:
        A :class:`FittedConformal` holding one number.

    Raises:
        ConformalError: a calibration row was fitted on, evaluated on or is a scored row; the
            model's heads do not match the configured band; MAPIE placed the estimators
            somewhere other than where this module put them; or the extracted constant does
            not reproduce MAPIE's own interval to :data:`PARITY_TOLERANCE`.
        ModelError: ``calibrate_on`` is empty, repeats, or names an unknown row.
        LeakDetected: a composition spans the calibration rows and the fit.
    """
    cfg = config if config is not None else load_config()
    level = cfg.conformal.confidence_level
    quantiles = tuple(model.quantiles)
    lower, upper, median = _head_columns(quantiles)

    # The prefit contract, checked against *this model's* heads and not only against the file.
    # `hydms.config._validate` refuses a pipeline.yaml where the two disagree; a ModelSettings
    # built by hand in a test or a probe never went through it.
    wanted = ((1.0 - level) / 2.0, (1.0 + level) / 2.0)
    if any(abs(a - b) > PARITY_TOLERANCE for a, b in zip(wanted, (quantiles[0], quantiles[-1]), strict=True)):
        raise ConformalError(
            f"a {level:g} band wants heads at ({wanted[0]:g}, {wanted[1]:g}) and this model "
            f"has ({quantiles[0]:g}, {quantiles[-1]:g}). MAPIE's prefit CQR contract is exact "
            f"-- lower (1 - level) / 2, upper (1 + level) / 2, median 0.5 -- and it does not "
            f"check it, so a mismatch here calibrates the wrong band silently and only AC-3 "
            f"would ever notice."
        )

    calibration = _owned(frame, calibrate_on, what="calibrated on")
    _refuse_overlap(model, calibration.index)

    heads = model.predict_model_space(calibration)
    truth = _model_space_target(calibration, target_column)

    regressor, version = _mapie()
    # [lower, upper, median] -- median LAST. MAPIE's `_MapieQuantileRegressor` reads
    # `estimators_[0]` and `estimators_[1]` as the band and sets
    # `single_estimator_ = estimators_[2]`. That is the positional trap `column_names` was
    # built to kill, reappearing at the library boundary, so the order is written once here
    # and asserted below rather than trusted.
    adapters = [_Head(model, lower), _Head(model, upper), _Head(model, median)]
    calibrator = regressor(estimator=adapters, confidence_level=level, prefit=True)
    calibrator.conformalize(calibration, truth)
    _refuse_misplaced_heads(calibrator, adapters, calibration, heads[median])

    point, intervals = calibrator.predict_interval(
        calibration, symmetric_correction=SYMMETRIC
    )
    low = np.asarray(intervals[:, 0, 0], dtype="float64")
    high = np.asarray(intervals[:, 1, 0], dtype="float64")
    correction = _extract_correction(heads[lower], heads[upper], low, high)

    fitted = FittedConformal(
        correction=correction,
        confidence_level=float(level),
        quantiles=quantiles,
        lower=lower,
        upper=upper,
        median=median,
        calibration_rows=len(calibration),
        fitted_on=str(model.record.where),
        symmetric=SYMMETRIC,
        mapie_version=version,
    )
    _assert_parity(fitted, heads, low, high, point)
    return fitted


def _refuse_overlap(model: QuantileModel, calibration: pd.Index) -> None:
    """No calibration row may have played any part in the fit -- read from the record.

    Row identities first, because they are the exact question, and then canonical
    compositions, because two rows can describe one material and a residual on a material the
    trees already fitted is not a conformity score.
    """
    rows = set(calibration)
    for role, seen in (
        ("grown on", model.record.fitted),
        ("used to stop the fit", model.record.eval_on),
        ("named as the scored rows", model.record.scored_on),
    ):
        overlap = rows & set(seen)
        if overlap:
            raise ConformalError(
                f"{len(overlap)} of the {len(rows)} calibration row(s) were {role} by "
                f"{model.record.where!r}: {_named(overlap)}. A conformity score computed on a "
                f"row the model has already seen is not a residual, and the coverage "
                f"guarantee it produces is nominal by construction and worth nothing."
            )


def _refuse_misplaced_heads(
    calibrator: Any,
    adapters: Sequence[_Head],
    calibration: pd.DataFrame,
    median_head: pd.Series,
) -> None:
    """MAPIE put the three estimators where this module thinks it put them.

    Two checks, because one alone is not enough. The **public** one is decisive about the
    median: ``predict`` returns ``single_estimator_``'s output, which MAPIE takes from
    position 2, so if the list were ever read as ``[lower, median, upper]`` this returns the
    upper head and the comparison fails by the half-width of the band. The **identity** one
    covers the lower/upper pair, which no output distinguishes once the constant is symmetric.
    It reaches into a private attribute deliberately: the alternative is to assume the
    ordering, and the whole point of the check is that the ordering is a library detail that
    can change under a pinned artifact.
    """
    point = np.asarray(calibrator.predict(calibration), dtype="float64")
    drift = float(np.max(np.abs(point - median_head.to_numpy(dtype="float64"))))
    if drift > PARITY_TOLERANCE:
        raise ConformalError(
            f"MAPIE's point prediction differs from the median head by up to {drift:.3e}. It "
            f"returns `estimators_[2]`, so this means the prefit list is not being read as "
            f"[lower, upper, median] -- the interval would be conformalised around the wrong "
            f"head. MAPIE's prefit ordering has changed; do not reorder the list until the "
            f"new contract is read in its source."
        )

    inner = getattr(calibrator, "_mapie_quantile_regressor", None)
    placed = getattr(inner, "estimators_", None)
    if placed is None:  # pragma: no cover -- a MAPIE that has moved its internals
        raise ConformalError(
            "MAPIE no longer exposes the fitted estimator list this check reads "
            "(`_mapie_quantile_regressor.estimators_`), so which adapter became the lower "
            "head can no longer be verified. A silently swapped pair produces an inverted "
            "interval that only AC-3 would ever notice; read the new internals before "
            "removing this check."
        )
    if list(placed[:2]) != list(adapters[:2]):
        raise ConformalError(
            f"MAPIE holds {placed[:2]} as the band where this module passed {adapters[:2]}. "
            f"A swapped pair subtracts the constant from the upper head and adds it to the "
            f"lower one, which inverts every interval and raises nothing."
        )


def _extract_correction(
    lower: pd.Series, upper: pd.Series, low: np.ndarray, high: np.ndarray
) -> float:
    """The one constant MAPIE added, read back off its own output.

    Read rather than recomputed: reimplementing ``ceil((n + 1) * (1 - alpha)) / n`` is exactly the off-by-one
    this module uses MAPIE to avoid. What is checked here is only that the correction really
    is *one* constant -- with ``symmetric_correction=True`` it must be, and if it ever is not,
    a single stored float cannot represent what MAPIE did and this must fail rather than store
    an average of it.
    """
    from_low = lower.to_numpy(dtype="float64") - low
    from_high = high - upper.to_numpy(dtype="float64")
    both = np.concatenate([from_low, from_high])
    spread = float(np.max(both) - np.min(both))
    if spread > PARITY_TOLERANCE:
        raise ConformalError(
            f"the correction MAPIE applied varies by {spread:.3e} across the calibration "
            f"rows and across the two heads, where `symmetric_correction=True` promises one "
            f"constant for both. A single stored float cannot stand for that, and storing "
            f"its average would be a calibration nobody fitted."
        )
    return float(from_low[0])


def _assert_parity(
    fitted: FittedConformal,
    heads: pd.DataFrame,
    low: np.ndarray,
    high: np.ndarray,
    point: np.ndarray,
) -> None:
    """The stored constant reproduces MAPIE's own interval. Gate AC-2's pattern, at fit time.

    This is what buys the right to throw MAPIE away. The artifact holds a float; the claim
    that the float *is* the calibration is checked here, against the library's output, on the
    rows the library saw, before the float is returned. A drift beyond
    :data:`PARITY_TOLERANCE` means applying the stored constant is not the same operation
    MAPIE performed -- and a wrong conformal constant is invisible afterwards, because the
    only thing that measures it is the gate it exists to pass.
    """
    reconstructed = fitted.apply(heads)
    for name, theirs, ours in (
        ("lower", low, reconstructed[fitted.lower].to_numpy(dtype="float64")),
        ("upper", high, reconstructed[fitted.upper].to_numpy(dtype="float64")),
        ("point", np.asarray(point, dtype="float64"), reconstructed[fitted.median].to_numpy(dtype="float64")),
    ):
        drift = float(np.max(np.abs(theirs - ours)))
        if drift > PARITY_TOLERANCE:
            raise ConformalError(
                f"applying the stored constant reproduces MAPIE's {name} bound only to "
                f"{drift:.3e}, where {PARITY_TOLERANCE:g} is required. The artifact stores a "
                f"number rather than a calibrator precisely so that this equality holds; if "
                f"it does not, the stored number is not the calibration."
            )


def _model_space_target(frame: pd.DataFrame, target_column: str | None) -> pd.Series:
    """The calibration truth, in the space the residuals are computed in.

    :func:`~hydms.surrogate.model._target` does exactly this and is the one definition; it is
    reached through this wrapper only so that the import stays with the other private one at
    the top of the file and the reason is written down once.
    """
    from hydms.surrogate.model import _target

    return _target(frame, target_column)


# --------------------------------------------------------------------------------------
# Reading one back
# --------------------------------------------------------------------------------------


def conformal_from(bundle: Any, *, name: str = CONFORMAL_PAYLOAD) -> FittedConformal:
    """The correction held in a loaded artifact version, checked before it is believed.

    The load path, and one line rather than ``bundle[CONFORMAL_PAYLOAD]`` for the reason
    :func:`~hydms.surrogate.scaler.scaler_from` gives: what can be wrong with a stored payload
    does not show up until a prediction is already a number.

      - **It is a pickled calibrator rather than a constant.** A version written against an
        earlier design holds a MAPIE object wrapping three adapters wrapping a booster, which
        needs MAPIE installed to unpickle and can change behaviour under a MAPIE upgrade.
      - **It calibrates heads this version's model does not have.** The quantiles must be the
        ones the stored model was fitted with; a mismatch means the version was assembled from
        two runs.
      - **The payload is absent**, which reads as a ``KeyError`` naming what the version holds.

    Args:
        bundle: A loaded :class:`~hydms.artifacts.store.Artifacts`.
        name: The payload key. :data:`CONFORMAL_PAYLOAD` unless a version stored several.

    Returns:
        The stored :class:`FittedConformal`.

    Raises:
        ConformalError: the payload is not a :class:`FittedConformal`, or its heads are not
            the ones the version's model carries.
        KeyError: the version holds no such payload.
    """
    conformal = bundle[name]
    if not isinstance(conformal, FittedConformal):
        raise ConformalError(
            f"payload {name!r} of {getattr(bundle, 'version', 'this version')} is a "
            f"{type(conformal).__name__}, not a FittedConformal. A pickled calibrator needs "
            f"MAPIE at predict time and can change what a saved version does when MAPIE is "
            f"upgraded, which is the failure AC-1 exists to detect; re-train the version "
            f"through hydms.surrogate.conformal.fit_conformal()."
        )
    model = bundle.get("model")
    stored = getattr(model, "quantiles", None)
    if stored is not None and tuple(stored) != tuple(conformal.quantiles):
        raise ConformalError(
            f"the stored correction calibrates heads {list(conformal.quantiles)} and the "
            f"stored model has {list(stored)}. A conformal constant belongs to the heads it "
            f"was estimated against; these two came from different runs."
        )
    return conformal


def compare_metrics(raw: Mapping[str, float], calibrated: Mapping[str, float]) -> pd.DataFrame:
    """Raw against calibrated, one row per metric that moved. For the calibration report.

    Both mappings are :func:`~hydms.surrogate.model.quantile_metrics` output over the same
    rows, which is the whole reason :meth:`FittedConformal.apply` returns the same columns:
    the before-and-after is a column comparison rather than new measurement code.
    """
    names = [name for name in raw if name in calibrated]
    return pd.DataFrame(
        {
            "raw": [raw[name] for name in names],
            "calibrated": [calibrated[name] for name in names],
            "change": [calibrated[name] - raw[name] for name in names],
        },
        index=pd.Index(names, name="metric"),
    )


def calibration_groups(
    frame: pd.DataFrame, fitting: Sequence[Hashable], calibrating: Sequence[Hashable]
) -> None:
    """Assert no canonical composition spans the two sides of a calibration carve.

    :func:`~hydms.surrogate.validation.grouped_folds` already guarantees this for a slice it
    cut itself. This exists for the carve a caller assembled some other way -- a resumed run,
    a hand-built probe -- because the failure is silent: a calibration row whose composition
    the trees already fitted gives a conformity score that is a training residual, the
    constant comes out too small, and the band under-covers exactly where it claims not to.

    Raises:
        LeakDetected: a composition appears on both sides -- leak L8 at a new stage.
    """
    keys = group_keys(frame)
    assert_disjoint_groups(
        {
            "fitted": keys.loc[list(fitting)].tolist(),
            "calibration": keys.loc[list(calibrating)].tolist(),
        },
        what="calibration carve",
    )
