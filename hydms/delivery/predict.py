"""L6 -- the one prediction path: a formula and a temperature in, a trustworthy answer out.

::

    from hydms.delivery import predict_capacity

    predict_capacity("LaNi5", 298.0)          # -> PredictionResult, or Refusal

This is the phase's one genuinely deep module. Everything the Phase H audit found dangerous
lives behind that call -- parsing, canonicalisation, featurisation, column order, the scaler
that must not be applied, quantile assembly, conformal widening, the applicability check and
the novelty distance -- and none of it is reachable from what comes back. The API (#78) and
the Streamlit pages (#82-#84) are transports over this function; if any step leaked upward it
would be duplicated between them, and the two copies would disagree about what a user is
told.

What comes back is a :data:`~hydms.delivery.contract.Answer`: a
:class:`~hydms.delivery.contract.PredictionResult` that cannot be constructed without an
interval and a domain verdict, or a :class:`~hydms.delivery.contract.Refusal` that carries no
number at all. Card #75 made that structural; this module is the path that must not evade it,
which is gate HG-2's (#77) half.

The order is forced, not chosen
-------------------------------

Card #76 offered two orderings for the unparseable formula -- screen before featurising, or
catch :class:`~hydms.descriptors.featurize.FeaturisationError` and map it -- and the first
turns out not to exist. :class:`~hydms.screens.domain.ApplicabilityDomain` judges a
**prediction**: it bounds the median head against the composition's physical ceiling and
against the 5.19 wt% level above which the corpus holds one family. A screen that reads a
prediction cannot run before one exists, so "screen first" would have meant two screening
passes and a rule for merging their verdicts -- a second composition rule, which is the defect
#90 exists to make visible. So the path is: **null check, featurise, predict, screen,
resolve, answer**, and a formula that will not parse is caught where it raises and mapped to
:data:`~hydms.screens.protocol.INDETERMINATE` carrying the parse error's own sentence.

That code is not a gap in the vocabulary and not an invention here. ``INDETERMINATE`` is the
declared code for "this rule could not be evaluated on this candidate", and the applicability
screen already emits it for the very same cause -- a formula it cannot give a physical ceiling
to, because "it does not parse, or it names an element the ``oliynyk`` table has no mass for".
One cause, one code, reached two ways.

A rejected candidate gets a refusal, not a low number
-----------------------------------------------------

:class:`~hydms.delivery.contract.PredictionResult` *permits* a rejecting verdict beside a
number, deliberately, so that a consumer can show what the model said about an out-of-domain
candidate without deleting the screen. **This path does not use that freedom.** Where any
screen rejects, ``predict_capacity`` returns a :class:`~hydms.delivery.contract.Refusal`,
which has no ``capacity`` field and no ``interval`` field at all -- the same branch
:func:`hydms.delivery.refusals.answers` takes, so the catalogue in ``docs/REFUSALS.md``
documents this function rather than something adjacent to it.

What "loads once" is worth, measured
-------------------------------------

:class:`ArtifactBundle` is immutable, version-stamped, and memoised by ``(store, version)``.
The card asks for that so a prediction path cannot silently pick up a different model between
two calls -- AC-4 is unanswerable otherwise. It is also, separately, most of the cost of a
prediction. Measured on the maintainer's machine, per call, if the parts were rebuilt each
time:

===========================================  ==========
:func:`~hydms.config.load`                    14.4 ms
``delivery_screens()`` without a shared cfg   47 ms     (three screens, three config reads)
``NoveltyReference.packaged()``                5.2 ms   (780 compositions x 103 Pettifor slots)
featurising one candidate, 14 features         ~4 ms
===========================================  ==========

So the screens are built **once, with one shared configuration**, and held.

**One cost is paid twice and is left that way deliberately.** A candidate is featurised here, for
the screens to range-check against the trained feature spans, and again inside
:meth:`~hydms.surrogate.predict.Surrogate.predict`, which owns the path from a formula to an
interval. Removing the duplicate would mean either re-deriving the featurisation contract in two
places -- the drift #28's docstring exists to prevent -- or widening #28's interface with a
"predict from this matrix" door, which is exactly the door "never scale, never reorder" is closed
against. The measured price of keeping both closed is ~4 ms on a call whose fixed cost is an
order of magnitude larger, and the alternative buys nothing until a **batch** entry point exists.
That is #78's and #84's problem, not this one's, and it is the right place for it: a batch
featurises and screens once for the whole frame, where the saving is real. That is why
:func:`~hydms.delivery.contract.delivery_screens` grew a ``cfg`` argument: its docstring is
right that a module-level constant would freeze whatever configuration was loaded first, and
a bundle is the thing that may legitimately hold them, because a bundle is already pinned to
one version for its lifetime and :func:`clear_cache` is how it is dropped.

One cache or two
----------------

Card #76 asks for "no global mutable state" and #28 observes that the surrogate layer already
has some: :data:`hydms.surrogate.predict._LOADED` memoises loaded surrogates. The exception is
stated rather than removed, and it is the same one twice. Both caches hold **immutable,
content-addressed** objects keyed by ``(store, version)``; an artifact version is written once
and never edited, so a key can only ever name one set of bytes. What is deliberately *not*
cached, in either layer, is the promotion pointer -- :func:`load_bundle` resolves
``current.json`` on every call, so promoting or rolling back takes effect on the next
prediction rather than on the next process.

The two caches are not two copies. This one holds the *same*
:class:`~hydms.surrogate.predict.Surrogate` object the surrogate layer memoised, obtained
through :func:`~hydms.surrogate.predict.load_surrogate` rather than by unpickling the booster
a second time -- which is the failure the card's "loads once" box names. :func:`clear_cache`
here clears both, because a test that writes a new version into a directory this process has
already read must not get a stale answer from either.

What the bundle does **not** hold is the scaler. Card #26 fits on raw features, ``#28``
proves the negative with a stored scaler that raises on ``transform``, and #48 landed as a
capacity ceiling that reads no scaled matrix -- so nothing on this path has a use for it. The
payload stays in the artifact because a version is sealed when written, not because a consumer
was found.

Which reference answered
------------------------

The applicability and novelty screens judge against committed reference files --
``hydms/screens/domain-reference.json`` and ``hydms/screens/novelty-reference.json`` -- which
are properties of the **curated data**, not of any one fit, and are therefore regenerated
beside the code rather than sealed into an artifact version. Card #76 names the risk that
creates: a promoted version is sealed and its reference is not, so a served ``v2`` could in
principle be screened against numbers measured from data it was never fitted on, and nothing
would say so.

Pinning a copy into the bundle is not available to ``v1`` or ``v2``: a manifest is sealed when
it is written, and re-saving to add a field would make a re-save look like a promotion. So the
bundle does the half that is available today -- it **digests what it actually loaded** and
reports it (:attr:`ArtifactBundle.reference_digests`), so #78's ``/v1/model`` can state which
reference answered and a replay (#91) can tell whether it still has it. The other half, the
*binding* -- a manifest field recorded at fit time, so a mismatch is detectable rather than
merely visible -- belongs to the card that writes versions, and is boxed on #91. Until it
exists the honest reading of a digest is "this is what answered", never "this matches what was
fitted": an absent record means unknown.

Cards #76, #28, #48, #49, #75, #90.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from hydms.config import Config
from hydms.config import load as load_config
from hydms.descriptors.contract import FeatureContract
from hydms.descriptors.featurize import FeaturisationError, featurize
from hydms.screens.protocol import SEPARATOR, Screen, Verdicts, apply_screens

from .contract import (
    ADMITTED,
    INDETERMINATE,
    Answer,
    DomainVerdict,
    Interval,
    Novelty,
    PredictionRequest,
    PredictionResult,
    Refusal,
    ScreenVerdict,
    delivery_screens,
    resolve,
)

__all__ = [
    "CANDIDATE",
    "ArtifactBundle",
    "DeliveryError",
    "clear_cache",
    "load_bundle",
    "novelty_from",
    "predict_capacity",
    "screen_verdicts",
]

#: The index label the single candidate carries through the screens. A screen's verdict is
#: addressed by label (:func:`~hydms.screens.protocol.apply_screens` refuses a repeated one),
#: so the one-row frame needs one, and a named label reads better than ``0`` in the error a
#: malformed screen produces.
CANDIDATE = "candidate"

#: The column the width lives in, spelled once. It is
#: :data:`hydms.surrogate.predict.INTERVAL_WIDTH` and it is what
#: :func:`~hydms.screens.domain.applicability_domain` reads as ``width``; the two agreeing is
#: what lets the `high-uncertainty` rule see the band this function is about to report.
WIDTH_COLUMN = "interval_width"


class DeliveryError(ValueError):
    """The deployment cannot answer, and the reason is the deployment rather than the request.

    A ``ValueError``, like :class:`~hydms.delivery.contract.ContractError` and every other
    layer guard here. It is raised for a bundle that cannot be assembled -- an artifact whose
    heads the configured screens would not read, a screen list with nothing in it -- and never
    for anything a caller typed. A candidate this system will not answer about comes back as a
    :class:`~hydms.delivery.contract.Refusal`, which is a *result*; a deployment that cannot
    answer about anything is not a result and must not be dressed as one.
    """


# --------------------------------------------------------------------------------------
# The bundle
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ArtifactBundle:
    """One artifact version and the screens that judge its answers, loaded once and frozen.

    Constructed only by :func:`load_bundle`. Everything public about it is a *fact* a caller
    may report -- which version answered, what band it targets, which rules ran, which
    reference they read -- and none of it is an object a caller could predict from, refit, or
    reconfigure. #78's ``GET /v1/model`` is written against exactly this surface.

    Attributes:
        version: The artifact version that answers, e.g. ``"v2"``. A number without the
            version that produced it is not evidence (card #83).
        screens: The screen names, in the order they run and therefore in the precedence
            :func:`~hydms.delivery.contract.resolve` applies across them.
        feature_names: The columns this version predicts from, in fitting order.
        confidence_level: The **nominal** coverage the band targets. Nominal, not measured:
            what it is worth on held-out data is gate AC-3's to establish (card #31).
    """

    version: str
    screens: tuple[str, ...]
    feature_names: tuple[str, ...]
    confidence_level: float
    _surrogate: Any = field(repr=False)
    _contract: FeatureContract = field(repr=False)
    _screens: tuple[Screen, ...] = field(repr=False)
    _formula_column: str = field(repr=False)
    _heads: tuple[str, str, str] = field(repr=False)
    _digests: tuple[tuple[str, str], ...] = field(repr=False)

    @property
    def reference_digests(self) -> dict[str, str]:
        """SHA-256 of each screen's reference, by screen name, for the ones that have one.

        Of the reference **as loaded**, not of the file on disk, so a bundle built with an
        overridden reference reports the numbers that actually judged rather than the ones
        that happened to be committed. See the module docstring for what this does and does
        not license: it says which reference answered; it does not say that reference matches
        the data the version was fitted on, because nothing records that yet (#91).
        """
        return dict(self._digests)

    @property
    def lower_head(self) -> str:
        """The column holding the calibrated lower bound -- the ranking key (risk R1)."""
        return self._heads[0]

    @property
    def median_head(self) -> str:
        """The column holding the point estimate. Not the bound: the bound understates."""
        return self._heads[1]

    @property
    def upper_head(self) -> str:
        """The column holding the calibrated upper bound."""
        return self._heads[2]


#: Assembled bundles by ``(store, version)``. See the module docstring, "One cache or two":
#: safe because an artifact version is written once, and the promotion pointer is deliberately
#: outside the key so a rollback takes effect on the next call.
_BUNDLES: dict[tuple[str, str], ArtifactBundle] = {}


def clear_cache() -> None:
    """Forget every assembled bundle, and every surrogate underneath one.

    Both, because they are two caches over the same artifact version: dropping only this one
    would rebuild the screens around a :class:`~hydms.surrogate.predict.Surrogate` the
    surrogate layer is still memoising, which is precisely the stale answer a test that writes
    a new version into an already-read directory is trying to avoid.
    """
    from hydms.surrogate.predict import clear_cache as clear_surrogate_cache

    _BUNDLES.clear()
    clear_surrogate_cache()


def _digest(screen: Screen) -> tuple[str, str] | None:
    """``(screen name, sha256)`` of the reference this screen judges against, if it has one.

    Duck-typed on ``reference.to_json()`` rather than on the two screen classes that have one
    today, so a fourth screen with a committed reference is reported without editing this
    layer -- and so a screen with no reference (the temperature window, whose thresholds are
    config) is simply absent from the mapping rather than reported as having an empty one.
    """
    reference = getattr(screen, "reference", None)
    to_json = getattr(reference, "to_json", None)
    if not callable(to_json):
        return None
    return (
        str(screen.name),
        hashlib.sha256(str(to_json()).encode("utf-8")).hexdigest(),
    )


def load_bundle(
    version: str | None = None,
    *,
    store: Path | None = None,
    screens: Sequence[Screen] | None = None,
    cfg: Config | None = None,
) -> ArtifactBundle:
    """The promoted artifact version and the screens that judge it, assembled once.

    Args:
        version: Which version. Defaults to the promoted one -- the pin in ``current.json``.
        store: The artifacts directory. Defaults to the configured ``paths.artifacts``.
        screens: The rules to run. Defaults to
            :func:`~hydms.delivery.contract.delivery_screens`. **A deployment decision, not a
            request parameter** -- #75 is explicit that a caller who could choose its own
            screens could widen its own interval until the answer looked good. It is a
            parameter here because which rules ran is a property of the deployment that the
            answer then *carries*: every verdict appears in
            :attr:`~hydms.delivery.contract.DomainVerdict.screens`, so a bundle assembled with
            a narrowed set produces answers that visibly say so.
        cfg: Loaded configuration. Defaults to one read here and shared by every screen.

    Returns:
        An :class:`ArtifactBundle`, memoised by ``(store, version)`` when built with the
        default screens. A bundle built with an explicit ``screens`` or ``cfg`` is **not**
        cached: it is not the deployment's bundle, and putting it in the cache would let a
        test's narrowed screen set answer a later caller's prediction.

    Raises:
        DeliveryError: the version's model reports a median head the configured screens would
            not read. See below -- this is the one deployment inconsistency that would
            otherwise be silent.
        PredictionError: nothing is promoted and no version was named, or the artifact is
            internally inconsistent.
        VersionNotFound: no such version.
        GatesIncomplete: the version's recorded gate run did not establish every criterion.

    **The surrogate is wrapped, not re-loaded.** :func:`~hydms.surrogate.predict.load_surrogate`
    already returns a frozen object pinned to one version, refuses a version whose gates are
    unestablished, and is memoised -- the immutability the card's "loads once" box asks for.
    Calling :func:`hydms.artifacts.load` again here is how a second unpickle of the same
    booster comes back, so this function does not.

    **Why the median head is checked.** The applicability screen is built from *config*: it
    reads the median of ``model.quantiles``, which is ``q0.5`` today. The artifact was fitted
    with its own quantiles. If the two ever disagreed, the screen would find no prediction
    column, and :class:`~hydms.screens.domain.ApplicabilityDomain` would quietly fall back to
    judging only the feature spans -- dropping ``above-physical-ceiling`` and
    ``out-of-domain``, the two rules that bound the number itself. That is a silent weakening
    of the guard rail this whole phase exists to install, so it is a loud failure instead.
    """
    from hydms.surrogate.predict import load_surrogate

    default = screens is None and cfg is None
    # One read, not two: `load_config()` is 14.4 ms, and resolving the store and building the
    # screens both want it.
    config = cfg if cfg is not None else load_config()
    root = Path(store) if store is not None else config.paths.artifacts
    surrogate = load_surrogate(version, store=root)

    if default:
        cached = _BUNDLES.get((str(root), surrogate.version))
        if cached is not None:
            return cached

    running = tuple(delivery_screens(config) if screens is None else screens)
    if not running:
        raise DeliveryError(
            "a bundle was assembled with no screens. An answer nothing judged is the silent "
            "drop's mirror image -- the candidate is admitted *because* the rules did not "
            "run -- and it is the one way a prediction path can return a bare number while "
            "every type in the contract still holds."
        )

    described = surrogate.describe().iloc[0]
    heads = (
        str(described["lower_head"]),
        str(described["median_head"]),
        str(described["upper_head"]),
    )
    _check_heads(surrogate, heads, running, config)

    bundle = ArtifactBundle(
        version=surrogate.version,
        screens=tuple(str(screen.name) for screen in running),
        feature_names=surrogate.feature_names,
        confidence_level=surrogate.confidence_level,
        _surrogate=surrogate,
        # Built from the *fitted* names, the way `surrogate_from` builds its own: the manifest
        # may declare more than the model consumes (the published 22 beside a selection
        # narrowed to 14, card #25), and featurising the difference costs eight columns per
        # candidate that neither the model nor any feature span reads.
        _contract=FeatureContract.from_names(surrogate.feature_names),
        _screens=running,
        _formula_column=config.columns.formula,
        _heads=heads,
        _digests=tuple(
            digest for digest in map(_digest, running) if digest is not None
        ),
    )
    if default:
        _BUNDLES[(str(root), surrogate.version)] = bundle
    return bundle


def _check_heads(
    surrogate: Any, heads: tuple[str, str, str], screens: Sequence[Screen], config: Config
) -> None:
    """Refuse an artifact whose median head the configured screens would not find."""
    from hydms.surrogate.model import column_names

    configured = column_names(config.model.quantiles)
    expected = configured[len(configured) // 2]
    if expected == heads[1]:
        return
    reading = [
        str(screen.name)
        for screen in screens
        if getattr(screen, "prediction", None) is not None
    ]
    if not reading:
        return
    raise DeliveryError(
        f"artifact {surrogate.version} reports its point estimate in {heads[1]!r}, and "
        f"{', '.join(reading)} would look for {expected!r}, which config's "
        f"model.quantiles={tuple(config.model.quantiles)} names. The screen would find no "
        f"prediction to bound and would fall back to judging the feature spans alone -- "
        f"dropping the two rules that bound the capacity itself. Refit the version against "
        f"this configuration, or restore the quantiles it was fitted with; do not serve the "
        f"pair."
    )


# --------------------------------------------------------------------------------------
# The public call
# --------------------------------------------------------------------------------------


def predict_capacity(
    formula: str,
    temperature_k: float,
    *,
    bundle: ArtifactBundle | None = None,
    version: str | None = None,
    store: Path | None = None,
) -> Answer:
    """The maximum gravimetric capacity of one composition at one temperature, or a refusal.

    Args:
        formula: The composition, as written. Not stripped or normalised here --
            :func:`~hydms.data.load.parse_formula` owns the grammar and its refusals are part
            of the answer.
        temperature_k: Kelvin.
        bundle: A pre-assembled :class:`ArtifactBundle`. #78 holds one for the process
            lifetime; a test passes one built over a temporary store. Defaults to the
            promoted version's.
        version: Which artifact version to answer from, when no ``bundle`` was given.
            Defaults to the promoted one.
        store: The artifacts directory, when no ``bundle`` was given.

    Returns:
        A :class:`~hydms.delivery.contract.PredictionResult` where every screen admitted --
        carrying the point estimate in weight percent, the calibrated interval and its nominal
        level, the domain verdict with a reason, the ElMD distance to the nearest known alloy,
        and the artifact version -- or a :class:`~hydms.delivery.contract.Refusal` carrying a
        code and a sentence and **no number at all**.

        The estimate is the median head, back-transformed to weight percent. It is not the
        lower confidence bound: the bound is the *ranking* key, deliberately conservative, and
        reporting it as the estimate would understate every answer by design (risk R1).

    Raises:
        ~hydms.delivery.contract.ContractError: the request itself is malformed -- an empty
            formula, a non-finite temperature. Card #75 decided that is a caller error rather
            than an unanswerable material, and that "the two must not arrive as the same
            refusal"; whether a malformed request should instead come back as a
            :class:`~hydms.delivery.contract.Refusal` is boxed on #77.
        DeliveryError, PredictionError, GatesIncomplete: the deployment cannot answer at all.
            See :func:`load_bundle`. These are never a statement about the candidate.

    **Every answer is screened, and the screens see this call's own prediction.** The
    temperature window, the applicability ceiling and the novelty distance all run, on a
    one-row frame carrying the featurised candidate, its formula, the median head and the
    band width -- so ``high-uncertainty`` judges the interval that is about to be reported and
    ``above-physical-ceiling`` judges the number that is about to be shown, rather than
    either judging something adjacent to it.
    """
    request = PredictionRequest(formula=formula, temperature_k=temperature_k)
    loaded = bundle if bundle is not None else load_bundle(version, store=store)

    formulas = pd.Series([request.formula], index=pd.Index([CANDIDATE]))
    temperatures = pd.Series([request.temperature_k], index=pd.Index([CANDIDATE]))
    try:
        features = featurize(formulas, temperatures, contract=loaded._contract)
        intervals = loaded._surrogate.predict(formulas, temperatures)
    except FeaturisationError as error:
        # The one cause with no screen of its own, and the code for it is declared rather than
        # invented: `INDETERMINATE` means "this rule could not be evaluated on this
        # candidate". The featuriser's own sentence is the explanation because it names the
        # offending string and says what is wrong with it -- #90's whole point being that a
        # true verdict with a sentence written for a different defect is the defect no
        # assertion catches.
        return Refusal(
            request=request,
            code=INDETERMINATE,
            explanation=str(error),
            model_version=loaded.version,
        )

    verdicts = apply_screens(_candidate(loaded, request, features, intervals), loaded._screens)
    judged = screen_verdicts(verdicts, CANDIDATE)
    code, reason = resolve(judged)
    if code != ADMITTED:
        return Refusal(
            request=request,
            code=code,
            explanation=reason,
            model_version=loaded.version,
            screens=judged,
        )

    row = intervals.loc[CANDIDATE]
    return PredictionResult(
        request=request,
        capacity=float(row[loaded.median_head]),
        interval=Interval(
            # Read by the names the *calibration* recorded rather than by position, the same
            # rule `_with_bound_and_width` follows one layer down: `lcb + interval_width` is
            # the upper head only up to a rounding, and a band whose quantiles are not in
            # ascending order would take the wrong column entirely.
            lower=float(row[loaded.lower_head]),
            upper=float(row[loaded.upper_head]),
            level=loaded.confidence_level,
        ),
        domain=DomainVerdict(
            admitted=True, code=ADMITTED, reason=reason, screens=judged
        ),
        novelty=novelty_from(verdicts, loaded.screens, CANDIDATE),
        model_version=loaded.version,
    )


# --------------------------------------------------------------------------------------
# Assembling the candidate, and reading the verdicts back
# --------------------------------------------------------------------------------------


def _candidate(
    bundle: ArtifactBundle,
    request: PredictionRequest,
    features: pd.DataFrame,
    intervals: pd.DataFrame,
) -> pd.DataFrame:
    """The one-row frame the screens judge: the features, the formula, the number, the band.

    Every column each screen reads, and no column it does not. The temperature is already in
    ``features`` -- it is a passthrough descriptor, and the window reads it under the same
    ``columns.temperature`` name -- so it is not added twice.

    **The alloy class is deliberately absent, and that costs one reachable code.**
    :class:`~hydms.screens.domain.ApplicabilityDomain` judges ``untrusted-family`` from a class
    label and the leave-one-class-out transfer measured for it (#30). A user types a formula
    and a temperature; there is no label, and nothing in the package maps a novel composition
    to a family. Supplying the column with an unknown value would be worse than omitting it --
    the screen answers ``indeterminate`` for a class it has no transfer estimate for, so every
    novel candidate, which is the entire point of the exercise, would be refused for the wrong
    reason. Omitting it means the signal does not run and says so. ``untrusted-family`` is
    therefore declared, documented in ``docs/REFUSALS.md``, and **not reachable through this
    function**; it is reachable where a class label genuinely exists, which is the batch CSV
    path (#84) and the screening of curated frames.
    """
    frame = features.copy()
    frame[bundle._formula_column] = request.formula
    frame[bundle.median_head] = intervals[bundle.median_head]
    frame[WIDTH_COLUMN] = intervals[WIDTH_COLUMN]
    return frame


def screen_verdicts(verdicts: Verdicts, label: object = CANDIDATE) -> tuple[ScreenVerdict, ...]:
    """One :class:`~hydms.delivery.contract.ScreenVerdict` per screen, for one candidate.

    The bridge from the composite table :func:`~hydms.screens.protocol.apply_screens` returns
    to the contract's own types, in the order the screens ran -- which is the order
    :func:`~hydms.delivery.contract.resolve` reads as precedence.

    It is the contract's type that is built rather than a dict, so a code the screens emitted
    and the delivery layer does not declare is refused *here*, by
    :class:`~hydms.delivery.contract.ScreenVerdict` itself, rather than by a check this module
    would have to keep in step with it.

    Lives in this module rather than beside the catalogue that first needed it, so the
    dependency runs the right way: :mod:`hydms.delivery.refusals` generates a document from
    the production path, and the production path must not import a document generator to
    borrow a function from it. Card #76 moved it; :func:`~hydms.delivery.contract.resolve`
    moved to the contract in the same pass and for the same reason.
    """
    return tuple(
        ScreenVerdict(
            screen=name,
            passed=bool(verdicts.table.loc[label, f"{name}{SEPARATOR}passed"]),
            code=str(verdicts.table.loc[label, f"{name}{SEPARATOR}code"]),
            reason=str(verdicts.table.loc[label, f"{name}{SEPARATOR}reason"]),
        )
        for name in verdicts.screens
    )


def novelty_from(
    verdicts: Verdicts, screens: Sequence[str], label: object = CANDIDATE
) -> Novelty | None:
    """The ElMD distance and its nearest alloy for one candidate, or ``None`` if none measured.

    Args:
        verdicts: The composite table :func:`~hydms.screens.protocol.apply_screens` returned.
        screens: The screen names, in run order.
        label: Which candidate's row to read.

    Read off the verdict frame rather than by calling the metric again: card #49 carries
    ``distance`` and ``nearest`` on the verdict row precisely so that the number and the
    verdict cannot come from two paths that disagree.

    ``None`` means "not measured", which on the delivery path can only happen to a bundle
    assembled with a narrowed screen set -- :func:`~hydms.delivery.contract.delivery_screens`
    includes the novelty screen, so a deployment's own bundle always measures one. It is
    returned rather than raised because a caller who removed the screen removed the
    measurement with it, and :class:`~hydms.delivery.contract.PredictionResult` has a stated
    spelling for that.

    It takes the screen names and a label rather than a bundle so that
    :mod:`hydms.delivery.refusals` can read the same number off its own probe run. An admitted
    probe whose distance was measured and then reported as ``None`` would be a page saying
    "not measured" about something it measured, on a page whose whole worth is that its
    sentences are true.
    """
    from hydms.screens.novelty import DISTANCE_COLUMN, NEAREST_COLUMN

    for name in screens:
        distance = f"{name}{SEPARATOR}{DISTANCE_COLUMN}"
        nearest = f"{name}{SEPARATOR}{NEAREST_COLUMN}"
        if distance in verdicts.table.columns and nearest in verdicts.table.columns:
            measured = verdicts.table.loc[label, distance]
            if pd.isna(measured):
                return None
            return Novelty(
                distance=float(measured),
                nearest=str(verdicts.table.loc[label, nearest]),
            )
    return None
