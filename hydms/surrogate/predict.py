"""L3 — the surrogate's public interface: formulas and temperatures in, a calibrated
interval out.

One call, and the whole of what a caller may know::

    from hydms.surrogate import predict

    predict(["LaNi5", "TiFe"], 298.0)
    #          q0.1    q0.5    q0.9     lcb  interval_width

Everything the interval is made of is hidden behind that call. Which regressor was fitted,
whether a scaler was involved, how the band was calibrated, which artifact version answered —
none of it reaches the caller, and the information-hiding check card #28 sets is that swapping
CatBoost for another regressor would require no change outside this layer.

**Why the search layer never sees the model.** The optimiser (frozen, L5) proposes thousands of
compositions and ranks them. If it could reach the booster it could call ``predict`` on the raw
heads, and the raw heads under-cover: card #26's probe measured 64.4 % against a nominal 80 %,
in every fold. Ranking on a number that means 64 % when it says 80 % is risk R1 — the optimiser
walks into extrapolation and the interval does not widen to say so. (A probe number: the
direction holds in all five folds, the magnitude awaits a full run.)

``lcb`` is therefore a **column**, not something a caller derives. It is the calibrated lower
head, looked up by the name the correction itself records (:attr:`FittedConformal.lower`)
rather than by position, so a configuration with a different band still produces the bound its
own calibration targeted. It duplicates one of the head columns, deliberately: a ranking key
whose meaning is "the number you rank on" is cheaper than a convention nobody can enforce.

Four things this module does **not** do, each because it belongs somewhere else.

**It does not scale.** ``FittedScaler`` is affine and CatBoost splits on thresholds, so the
ensemble is invariant to it; card #26 therefore fits on raw features and records that in
:attr:`QuantileModel.feature_names`. Applying the persisted scaler on the way in would feed the
model a matrix it was never fitted on and return plausible, wrong numbers. The scaler stays in
the bundle because the applicability domain (card #48) is distance-based and needs it — the
card's box is right about *persisting* it and wrong about where it is applied, and
``test_the_stored_scaler_is_never_applied`` measures that rather than asserting it in prose.

**It does not clip.** A negative lower bound is the signal cards #48 and #77 act on. Squashing
it here would hide the one thing that says the model has left what it can defend.

**It does not refuse an out-of-domain candidate.** The temperature bounds, the applicability
ceiling and the novelty distance are L4 screens (cards #44, #48, #49) and the refusal that
carries them is L6 (cards #75, #76 and #77). A surrogate that silently declined rows would
make the screen verdict unobservable — the thing card #44 exists to prevent.

**It does not import MAPIE.** The calibration is a stored float, not a calibrator (card #27),
so the prediction path never touches the library that estimated it. That is a claim about an
import graph and it is checked in a subprocess, not asserted here.

**Head names are ``column_names``', not ``p10``/``p50``/``p90``.** The card's job story writes
the frame as ``[p10, p50, p90, lcb, interval_width]``; the heads keep the
:func:`~hydms.surrogate.model.column_names` spelling instead, for two reasons. The quantiles
are configuration (``model.quantiles``), so ``p10`` would be a literal restatement of one
possible value, and ``column_names`` is this project's single place where position becomes
name — a second naming rule here is the positional trap coming back one layer up. It also
keeps :func:`~hydms.surrogate.model.quantile_metrics` able to score this frame with no new
measurement code, which is what card #29 needs.

Card #28.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from hydms.config import load as load_config
from hydms.descriptors.contract import FeatureContract
from hydms.descriptors.featurize import featurize

from .conformal import FittedConformal, calibrated_heads, conformal_from
from .model import QuantileModel, column_names, model_from

__all__ = [
    "INTERVAL_WIDTH",
    "LOWER_BOUND",
    "PredictionError",
    "Surrogate",
    "clear_cache",
    "load_surrogate",
    "predict",
]

#: The ranking key: the calibrated lower confidence bound, in weight percent. Named here so
#: that the string appears once and every downstream sort can spell it from this module.
LOWER_BOUND = "lcb"

#: Upper head minus lower head, in weight percent. It is *not* constant even though the
#: conformal correction is: the correction is a constant in ``log1p`` space, and ``expm1``
#: stretches it by more at a high prediction than at a low one. A width column therefore says
#: something a single stored number cannot, which is why AC-7 asks candidates to carry it.
INTERVAL_WIDTH = "interval_width"


class PredictionError(ValueError):
    """The surrogate cannot answer, and the reason is the artifact rather than the batch.

    Batch problems keep the error of the layer that found them —
    :class:`~hydms.descriptors.featurize.FeaturisationError` for a formula the contract cannot
    serve, :class:`~hydms.surrogate.model.ModelError` for a matrix the model will not take —
    so that a caller can tell "this candidate is unanswerable" from "this deployment is
    broken" without reading the message.
    """


# --------------------------------------------------------------------------------------
# The loaded surrogate
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Surrogate:
    """One artifact version, ready to answer, with nothing of its machinery reachable.

    Constructed only by :func:`load_surrogate`. The three private fields are the whole of the
    hidden state; everything public about this object is a *fact* — which version answered,
    which heads it carries, what level its band targets — and none of it is an object a caller
    could call ``fit`` on.

    Immutable, and pinned to one version for its lifetime. A prediction path that can silently
    pick up a different model between two calls cannot honour AC-4 and cannot be reasoned
    about at all, which is the property :class:`~hydms.artifacts.store.Artifacts` already
    carries and this type inherits by holding one.

    Attributes:
        version: The artifact version that answered, e.g. ``"v1"``. Reportable, because a
            number without the version that produced it is not evidence (card #83).
    """

    version: str
    _model: QuantileModel = field(repr=False)
    _conformal: FittedConformal = field(repr=False)
    _contract: FeatureContract = field(repr=False)

    # -- what a caller may know ----------------------------------------------------------

    @property
    def quantiles(self) -> tuple[float, ...]:
        """The alphas the heads were fitted for, in the order the columns arrive in."""
        return tuple(self._model.quantiles)

    @property
    def feature_names(self) -> tuple[str, ...]:
        """The columns this version featurises and predicts from, in fitting order."""
        return tuple(self._model.feature_names)

    @property
    def confidence_level(self) -> float:
        """The nominal coverage the band targets — ``conformal.confidence_level``.

        Nominal, not measured. What it is *worth* on held-out data is gate AC-3's to establish
        (card #31), and this property is deliberately not the place that number appears.
        """
        return self._conformal.confidence_level

    @property
    def columns(self) -> tuple[str, ...]:
        """The columns :meth:`predict` returns, in order: the heads, then ``lcb``, then the width."""
        return (*column_names(self.quantiles), LOWER_BOUND, INTERVAL_WIDTH)

    # -- the one thing it does -----------------------------------------------------------

    def predict(
        self,
        formulas: Sequence[str] | pd.Series,
        temperatures: float | Sequence[float] | np.ndarray | pd.Series,
    ) -> pd.DataFrame:
        """A calibrated interval per candidate. See :func:`predict`, which delegates here."""
        features = featurize(formulas, temperatures, contract=self._contract)
        if features.empty:
            return _empty_intervals(features.index, self.columns)
        heads = calibrated_heads(self._model, features, conformal=self._conformal)
        return _with_bound_and_width(heads, self._conformal)

    def describe(self) -> pd.DataFrame:
        """One row saying which artifact answered and what its band claims. For card #83.

        The model card needs to state the version, the level and the width of the band beside
        every number it reports; handing out the model so a page could read those off it is
        the leak of internals this whole module exists to prevent.
        """
        return pd.DataFrame(
            [
                {
                    "version": self.version,
                    "quantiles": ", ".join(f"{q:g}" for q in self.quantiles),
                    "confidence_level": self.confidence_level,
                    "lower_head": self._conformal.lower,
                    "median_head": self._conformal.median,
                    "upper_head": self._conformal.upper,
                    "features": len(self.feature_names),
                    "calibration_rows": self._conformal.calibration_rows,
                }
            ],
            index=pd.Index(["surrogate"], name="payload"),
        )


# --------------------------------------------------------------------------------------
# Loading it
# --------------------------------------------------------------------------------------

#: Loaded surrogates by ``(store, version)``. Safe to cache because an artifact version is
#: written once and never edited (:mod:`hydms.artifacts.store`), so a key can only ever name
#: one set of bytes. What is *not* cached is the promotion pointer: :func:`load_surrogate`
#: reads ``current.json`` on every call, so promoting or rolling back takes effect on the next
#: prediction rather than on the next process.
_LOADED: dict[tuple[str, str], Surrogate] = {}


def clear_cache() -> None:
    """Forget every loaded surrogate. For tests that write a version into a temporary store."""
    _LOADED.clear()


def load_surrogate(
    version: str | None = None, *, store: Path | None = None
) -> Surrogate:
    """The promoted artifact version, loaded and checked, ready to predict from.

    Args:
        version: Which version. Defaults to the promoted one — the pin in ``current.json``.
        store: The artifacts directory. Defaults to the configured ``paths.artifacts``.

    Returns:
        A :class:`Surrogate` holding that version's model and calibration and nothing else.

    Raises:
        PredictionError: nothing is promoted and no version was named, or the version's model
            was fitted on a column its own feature contract does not declare.
        VersionNotFound: no such version.
        GatesIncomplete: the version's recorded gate run did not establish every criterion.
        PayloadCorrupt: a stored file no longer matches its recorded digest.
        ModelError, ConformalError: a payload is not the type it is stored under, or the
            model and the correction came from different runs.
        KeyError: the version holds no model, or no calibration.

    **The gate check is never relaxed.** :func:`hydms.artifacts.store.load` takes a
    ``require_gates=False`` for the card that has just written a version and wants it back;
    this function does not forward it and takes no equivalent, so an artifact whose gates are
    unestablished — a run that died, a version saved before AC-3 was written, anything a
    ``SKIPPED`` appears in — cannot answer a prediction at all. That is what card #28's
    "refuses to run against an unpromoted version" buys, and it is strictly stronger than the
    promotion pointer: :func:`hydms.artifacts.store.promote` already refuses to point at a
    version whose gates are incomplete, so *promoted* implies *gates established* and the
    converse is the case this check adds. Naming a version explicitly stays legal — rollback
    inspection and card #33's gate both need to score a candidate version before the pointer
    moves — but a named version faces exactly the same check the promoted one does.
    """
    from hydms import artifacts

    root = Path(store) if store is not None else load_config().paths.artifacts
    resolved = version if version is not None else artifacts.current(store=root)
    if resolved is None:
        known = ", ".join(artifacts.versions(store=root)) or "none"
        raise PredictionError(
            f"nothing is promoted in {root}, so there is no pinned model to predict from. "
            f"Versions present: {known}. Promote one with hydms.artifacts.promote(), or name "
            f"a version explicitly. A prediction from an unpinned artifact is not a "
            f"prediction anybody can reproduce."
        )

    key = (str(root), resolved)
    cached = _LOADED.get(key)
    if cached is not None:
        return cached

    bundle = artifacts.load(resolved, store=root)
    model = model_from(bundle)
    conformal = conformal_from(bundle)

    declared = frozenset(getattr(bundle, "feature_names", ()) or ())
    if declared:
        outside = [name for name in model.feature_names if name not in declared]
        if outside:
            raise PredictionError(
                f"{bundle.version}'s model was fitted on {len(outside)} column(s) its own "
                f"feature contract does not declare: {', '.join(sorted(outside))}. The "
                f"featuriser is driven by the fitted names, so this version cannot be "
                f"predicted from at all -- the model and the manifest came from different "
                f"runs."
            )

    surrogate = Surrogate(
        version=bundle.version,
        _model=model,
        _conformal=conformal,
        # Built from the *fitted* names rather than from the manifest's contract, in fitting
        # order. The manifest may declare more than the model consumes -- the published 22
        # recorded beside a model selection narrowed to 14 (card #25) -- and featurising the
        # difference would cost eight columns per candidate that nothing ever reads.
        _contract=FeatureContract.from_names(model.feature_names),
    )
    _LOADED[key] = surrogate
    return surrogate


# --------------------------------------------------------------------------------------
# The public call
# --------------------------------------------------------------------------------------


def predict(
    formulas: Sequence[str] | pd.Series,
    temperatures: float | Sequence[float] | np.ndarray | pd.Series,
    *,
    version: str | None = None,
    store: Path | None = None,
) -> pd.DataFrame:
    """Calibrated maximum-capacity intervals for a batch of candidate alloys.

    The deep interface the search layer sees. Composition strings and kelvin go in; a frame of
    intervals in weight percent comes out, and nothing about how it was produced is reachable
    from what comes back.

    Args:
        formulas: The compositions, as strings. A ``Series`` keeps its index; any other
            sequence is labelled by position. A bare ``str`` is refused rather than iterated
            character by character.
        temperatures: One kelvin value per formula, or a scalar for all of them.
        version: Which artifact version to answer from. Defaults to the promoted one.
        store: The artifacts directory. Defaults to the configured ``paths.artifacts``.

    Returns:
        ``(len(formulas), len(quantiles) + 2)`` of ``float64`` on the caller's index, columns
        :attr:`Surrogate.columns` — one per quantile head, then :data:`LOWER_BOUND` and
        :data:`INTERVAL_WIDTH`. All in **weight percent**. Rank on :data:`LOWER_BOUND`; the
        median head is a point estimate and ranking on it is what risk R1 describes.

        Nothing is clipped and no row is dropped. A negative ``lcb`` means the calibrated band
        reaches below zero capacity, which is a candidate the model cannot defend rather than
        a candidate with no capacity, and it is the screens' (#48) and the refusal path's
        (#77) business, not this function's.

    Raises:
        FeaturisationError: a formula will not parse, or a composition cannot produce every
            feature the model was fitted on. Every offending row is named and nothing is
            silently dropped.
        PredictionError: nothing is promoted, or the artifact is internally inconsistent.
        ModelError, ConformalError: see :func:`load_surrogate`.
        GatesIncomplete: the version's gates are not all established.

    The load is cached per ``(store, version)``, so a batch loop pays for unpickling a model
    once. Call :func:`clear_cache` after writing a version into a directory this process has
    already read.
    """
    return load_surrogate(version=version, store=store).predict(formulas, temperatures)


# --------------------------------------------------------------------------------------
# Assembling the frame
# --------------------------------------------------------------------------------------


def _with_bound_and_width(
    heads: pd.DataFrame, conformal: FittedConformal
) -> pd.DataFrame:
    """The calibrated heads, plus the ranking key and the width, in that order.

    The heads arrive from :func:`~hydms.surrogate.conformal.calibrated_heads` in the model's
    column order and leave in it unchanged — appended to, never renamed or reordered — which
    is what lets :func:`~hydms.surrogate.model.quantile_metrics` score this frame directly.

    Both added columns are looked up by the names the *correction* records rather than by
    position. ``conformal.lower`` is the head its constant widened downward, so it is the
    bound the calibration actually targeted; picking column 0 instead would be the positional
    assumption ``column_names`` exists to remove, and it would quietly pick the wrong head for
    any band whose quantiles are not in ascending order.
    """
    lower = heads[conformal.lower]
    upper = heads[conformal.upper]
    frame = heads.copy()
    frame[LOWER_BOUND] = lower
    # In weight percent, so this is not the stored constant doubled: `expm1` is convex, and
    # the same model-space widening is a wider band at 6 wt% than at 1 wt%.
    frame[INTERVAL_WIDTH] = upper - lower
    return frame


def _empty_intervals(index: pd.Index, columns: Sequence[str]) -> pd.DataFrame:
    """The right frame for a batch of no candidates: no rows, every column, ``float64``.

    An empty batch is a normal outcome of filtering — card #84 screens a CSV and may keep
    nothing — and it must not reach the booster. CatBoost's ``predict`` over zero rows does
    not reliably return the ``(0, n_alphas)`` shape
    :meth:`~hydms.surrogate.model.QuantileModel.predict_model_space` checks for, so "no
    candidates" would surface as a shape error about the loss string. The dtypes are stated
    rather than inferred: an empty frame with ``object`` columns compares equal to nothing and
    concatenates wrongly.
    """
    return pd.DataFrame(
        {name: pd.Series(dtype="float64") for name in columns},
        index=index,
        columns=list(columns),
    )
