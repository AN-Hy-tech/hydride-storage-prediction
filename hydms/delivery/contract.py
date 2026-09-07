"""L6 -- the vocabulary every consumer of a prediction speaks.

Three consumers are about to be built on one prediction path: the HTTP API (#78), the
Streamlit interface (#82) and the batch CSV screen (#84). If each invents its own shape for
an answer, the honest-interval guarantee becomes three guarantees that drift apart and gate
HG-2 has nothing single to check. So the contract is written *before* the callers exist, and
it is written as types rather than as a convention.

**The structural half of HG-2 lives here.** :class:`PredictionResult` has no default for
``interval`` and none for ``domain``, and :meth:`PredictionResult.__post_init__` refuses
``None`` for either. There is therefore no way to spell a bare number in this module -- not a
rule about what callers should include, but a type that cannot represent the thing the gate
forbids. The behavioural half -- that no path *evades* the type -- is #77's.

``refused`` is a property on both answer types rather than a field on either, for the same
reason. A field can be set to ``False`` on a refusal; a property cannot. A consumer reading
JSON branches on that one boolean and needs to know nothing else about the vocabulary, which
is the same redundancy :class:`~hydms.screens.protocol.Verdicts` carries with ``passed``
beside ``code``.

**Units and the target space are in the type, not in a field name.** ``capacity`` alone
would be a number whose meaning has to be looked up: the surrogate is fitted on
``log1p(capacity)`` (card #11) and everything a person reads is ``expm1`` of that, so the two
spaces are one function call apart and a result that does not say which it is in is a result
that can be believed in the wrong one. :data:`UNIT` and :data:`SPACE` are carried on every
:class:`Interval` and every :class:`PredictionResult`, checked on construction, and
serialised, so a JSON payload crossing the transport boundary still says what it means.

The refusal codes are enumerated, never written down
----------------------------------------------------

A literal list of reason codes in this module would be a second source of truth, and it would
drift from the screens that actually emit them -- which is precisely what
``docs/QA-PROTOCOL.md`` L6 means by "every refusal reason code is reachable and asserted".
So the vocabulary is *derived*: :func:`reason_codes` is
:data:`~hydms.screens.protocol.ADMITTED`, plus the union of the declared
:attr:`~hydms.screens.protocol.Screen.reasons` of the screens the delivery path runs, plus
the shared :data:`~hydms.screens.protocol.INDETERMINATE`. Card #44 made a screen's vocabulary
declared rather than discovered for exactly this reason, and
:func:`~hydms.screens.protocol.apply_screens` refuses a code outside it, so the two ends
cannot disagree.

:func:`delivery_screens` is what "the screens the delivery path runs" means today: the
temperature window (#44) and the applicability-domain ceiling (#48). The ElMD novelty screen
(#49) has **landed** -- :func:`hydms.screens.novelty.novelty_screen` -- and is still not in
that tuple, which is now a decision rather than an absence: adding it makes ElMD, an optional
extra, a hard requirement of every prediction. #76 owns that call, because #76 owns what the
bundle and the service require. When it joins, the vocabulary widens on its own and nothing in
this module changes.

**A cause no screen can judge is** :data:`~hydms.screens.protocol.INDETERMINATE`. #77 refuses
an unparseable formula and an unknown element, and neither is a threshold any screen declares
a code for. They are not a gap in the vocabulary: ``INDETERMINATE`` is the declared code for
"this rule could not be evaluated on this candidate", the applicability screen already emits
it for a formula it cannot give a physical ceiling to, and the *explanation* is where the
parse error's own sentence goes. What that costs #76 is an ordering constraint -- screen
before featurising, or catch :class:`~hydms.descriptors.featurize.FeaturisationError` and map
it -- and it is boxed on #76 and #77 rather than assumed here.

Usage::

    from hydms.delivery.contract import (
        Interval, DomainVerdict, PredictionRequest, PredictionResult, Refusal, answer_from
    )

    request = PredictionRequest(formula="LaNi5", temperature_k=298.0)
    result = PredictionResult(
        request=request,
        capacity=1.42,
        interval=Interval(lower=0.98, upper=1.91, level=0.8),
        domain=DomainVerdict.admitted_by(("temperature", "domain")),
        novelty=None,                      # #49 has not landed; None means "not measured"
        model_version="v2",
    )
    answer_from(json.loads(json.dumps(result.to_dict()))) == result      # True

Card #75.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from hydms.screens.protocol import ADMITTED, INDETERMINATE, Screen

__all__ = [
    "ADMITTED",
    "INDETERMINATE",
    "SCHEMA",
    "SPACE",
    "UNIT",
    "Answer",
    "ContractError",
    "DomainVerdict",
    "Interval",
    "Novelty",
    "PredictionRequest",
    "PredictionResult",
    "Refusal",
    "ScreenVerdict",
    "answer_from",
    "delivery_screens",
    "reason_codes",
]

#: The payload shape, carried in every serialised answer. Same convention and same spelling
#: rule as :data:`hydms.gates._core.SCHEMA` and :data:`hydms.artifacts.manifest.SCHEMA`: a
#: reader that meets an unknown schema says so rather than guessing at the fields.
SCHEMA = "hydms.delivery/1"

#: The unit every capacity in this module is in: weight percent of hydrogen, gravimetric, on
#: a **material** basis. Not a system basis -- comparing it to a DOE system target is a
#: two-step overstatement (PRD section 4.4), which is why #83 must carry that caveat and why
#: the unit is on the type rather than in a docstring.
UNIT = "wt%"

#: The space the numbers are in. The surrogate is fitted on ``log1p`` of capacity (card #11)
#: and every number here is ``expm1`` of a head, so this string says which side of that
#: transform a reader is on.
SPACE = "capacity"

# A failure that names two hundred codes is a failure nobody reads to the end. The total is
# always reported; the listing is truncated. Same convention as `hydms/screens/protocol.py`.
_MAX_NAMED = 8


class ContractError(ValueError):
    """An answer cannot be built, or a payload is not one.

    A ``ValueError``, like :class:`~hydms.screens.protocol.ScreenError` and the other layer
    guards in this project. Every raise names the field and what was wrong with it: the
    failure this module exists to prevent is a number whose meaning nobody can recover, so
    its own errors must never be one.
    """


def _named(items: Iterable[object]) -> str:
    listed = sorted(map(repr, items))
    if len(listed) <= _MAX_NAMED:
        return ", ".join(listed)
    return f"{', '.join(listed[:_MAX_NAMED])}, ... ({len(listed) - _MAX_NAMED} more)"


def _finite(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ContractError(
            f"{what} must be a number, not {type(value).__name__}. A capacity that arrives "
            f"as a string crosses a transport boundary unnoticed and compares wrongly."
        )
    number = float(value)
    if not math.isfinite(number):
        raise ContractError(
            f"{what} is {number}, which is not a finite number. NaN does not survive JSON "
            f"and an infinite bound is not an interval."
        )
    return number


def _sentence(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(
            f"{what} is blank. Every verdict carries a sentence a reader gets, including the "
            f"ones that admitted -- 'cannot predict' only sends a user away."
        )
    return value


# --------------------------------------------------------------------------------------
# The vocabulary, derived from the screens
# --------------------------------------------------------------------------------------


def delivery_screens() -> tuple[Screen, ...]:
    """The screens the delivery path runs, in the order their verdicts are reported.

    The temperature window (#44) and the applicability-domain ceiling (#48). #49's ElMD
    novelty screen has landed and is deliberately still absent: it would make the optional
    ``novelty`` extra a hard requirement of every prediction, which is #76's decision to make
    rather than this function's. When it joins, :func:`reason_codes` widens on its own.

    Built fresh on each call rather than held as a module constant: both screens read
    ``hydms/config/pipeline.yaml`` for their thresholds, and a constant would freeze whatever
    configuration happened to be loaded when this module was first imported.
    """
    from hydms.screens.domain import applicability_domain
    from hydms.screens.window import temperature_window

    return (temperature_window(), applicability_domain())


def reason_codes(screens: Sequence[Screen] | None = None) -> tuple[str, ...]:
    """Every code an answer may carry: admitted, the screens' declared reasons, indeterminate.

    Args:
        screens: The screens that will run. Defaults to :func:`delivery_screens`.

    Returns:
        The codes, sorted, with :data:`~hydms.screens.protocol.ADMITTED` first. Sorted rather
        than in screen order because this is a *set* rendered for a reader -- an API document
        (#80) and a test that asserts reachability both want a stable listing, and two screens
        may declare the same code.

    There is deliberately no literal list of codes in this module. A code reaches a caller
    only by being declared on a screen, and :func:`~hydms.screens.protocol.apply_screens`
    refuses a screen that emits one it did not declare, so the vocabulary a consumer sees and
    the vocabulary a screen can produce are the same set by construction.
    """
    running = tuple(delivery_screens()) if screens is None else tuple(screens)
    declared: set[str] = {INDETERMINATE}
    for screen in running:
        reasons = getattr(screen, "reasons", None)
        if not isinstance(reasons, tuple) or not reasons:
            raise ContractError(
                f"screen {getattr(screen, 'name', screen)!r} declares no reason vocabulary, "
                f"so the delivery layer cannot enumerate what it may have to explain. Card "
                f"#44 requires the declaration."
            )
        declared.update(str(reason) for reason in reasons)
    if ADMITTED in declared:
        raise ContractError(
            f"a screen declares {ADMITTED!r} among its reasons. That code means admitted; "
            f"reasons are the codes on which a screen rejects."
        )
    return (ADMITTED, *sorted(declared))


@lru_cache(maxsize=1)
def _vocabulary() -> frozenset[str]:
    """:func:`reason_codes` over the default screens, built once per process.

    Cached, and safe to cache, because a screen's *reason vocabulary* is a property of the
    screen class rather than of any threshold in ``pipeline.yaml``: tightening the temperature
    window changes which candidates get ``outside-window``, never whether that code exists.
    :func:`reason_codes` itself is uncached and takes an explicit screen list, which is what a
    test with a different screen set uses.
    """
    return frozenset(reason_codes())


def _code(value: object, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{what} is blank; every verdict names the rule it came from.")
    known = _vocabulary()
    if value not in known:
        raise ContractError(
            f"{what} is {value!r}, which no screen on the delivery path declares. The "
            f"vocabulary is {_named(known)}. A code invented at the rejection site is "
            f"unreachable from the screens and cannot be asserted (docs/QA-PROTOCOL.md, L6)."
        )
    return value


# --------------------------------------------------------------------------------------
# The request
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PredictionRequest:
    """What a caller asks: one composition at one temperature.

    Deliberately the *whole* of the input. Anything else a caller might want to vary -- which
    artifact version answers, which screens run, how wide the band is -- is deployment
    configuration, and a request that could choose it would let a caller widen its own
    interval until the answer looked good.

    Attributes:
        formula: The composition, as written. Not parsed, normalised or case-folded here:
            :func:`~hydms.data.load.parse_formula` owns that and its refusals are part of the
            answer (#77). Surrounding whitespace is kept, because ``'Pr1Co5 '`` and
            ``'Pr1Co5'`` are the same material and the *pipeline* is what says so -- a strip
            here would hide the one behaviour #74 measures.
        temperature_k: Kelvin. Not screened here: whether it is inside the trained range is
            :func:`~hydms.screens.window.temperature_window`'s verdict, and turning it into a
            construction error would make the refusal unobservable, which is the thing card
            #44 exists to prevent.
    """

    formula: str
    temperature_k: float

    def __post_init__(self) -> None:
        if not isinstance(self.formula, str) or not self.formula.strip():
            raise ContractError(
                "a request needs a composition; the formula is empty. An empty string is a "
                "caller error rather than an unparseable material, and the two must not "
                "arrive as the same refusal."
            )
        object.__setattr__(
            self, "temperature_k", _finite(self.temperature_k, "temperature_k")
        )

    def to_dict(self) -> dict[str, Any]:
        """The request as JSON-ready primitives."""
        return {"formula": self.formula, "temperature_k": self.temperature_k}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PredictionRequest:
        """Rebuild a request from :meth:`to_dict`'s output."""
        missing = [name for name in ("formula", "temperature_k") if name not in payload]
        if missing:
            raise ContractError(f"a request payload is missing {_named(missing)}.")
        return cls(formula=payload["formula"], temperature_k=payload["temperature_k"])


# --------------------------------------------------------------------------------------
# The pieces of an answer
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Interval:
    """A calibrated prediction interval, in weight percent, with the level it targets.

    Attributes:
        lower: The calibrated lower head. **Not clipped at zero** -- a negative lower bound is
            the signal that the band reaches below zero capacity, which cards #48 and #77 act
            on, and squashing it here would hide exactly what the interval exists to show
            (:mod:`hydms.surrogate.predict` makes the same refusal one layer down).
        upper: The calibrated upper head.
        level: The **nominal** coverage the band targets -- ``conformal.confidence_level``.
            Nominal, not measured: what the band is worth on held-out data is gate AC-3's to
            establish, and a field called ``coverage`` here would be read as that number.
        unit: :data:`UNIT`.
        space: :data:`SPACE`.
    """

    lower: float
    upper: float
    level: float
    unit: str = UNIT
    space: str = SPACE

    def __post_init__(self) -> None:
        object.__setattr__(self, "lower", _finite(self.lower, "interval lower"))
        object.__setattr__(self, "upper", _finite(self.upper, "interval upper"))
        object.__setattr__(self, "level", _finite(self.level, "interval level"))
        if self.upper < self.lower:
            raise ContractError(
                f"the interval is inverted: lower={self.lower:g} is above "
                f"upper={self.upper:g}. Quantile crossing is a real defect of a multiquantile "
                f"fit and it is counted (`quantile_metrics`), but an answer that reports it as "
                f"an interval is an answer whose width is negative."
            )
        if not 0.0 < self.level < 1.0:
            raise ContractError(
                f"the nominal level is {self.level:g}; it is a probability, so it lies "
                f"strictly between 0 and 1. MAPIE takes `confidence_level`, not `alpha` -- "
                f"0.2 here would silently claim a 20% band (docs/LIBRARY-APIS.md)."
            )
        _units(self.unit, self.space, "an interval")

    @property
    def width(self) -> float:
        """``upper - lower``, in :data:`UNIT`.

        Computed rather than stored, so it cannot disagree with the bounds it came from. It is
        not a constant across candidates even though the conformal correction is: the
        correction is constant in ``log1p`` space and ``expm1`` stretches it by more at a high
        prediction than at a low one.
        """
        return self.upper - self.lower

    def contains(self, value: float) -> bool:
        """Whether ``value`` lies inside the closed band."""
        return self.lower <= value <= self.upper

    def to_dict(self) -> dict[str, Any]:
        """The interval as JSON-ready primitives, ``width`` included for a reader."""
        return {
            "lower": self.lower,
            "upper": self.upper,
            "level": self.level,
            "width": self.width,
            "unit": self.unit,
            "space": self.space,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Interval:
        """Rebuild an interval. ``width`` is ignored: it is derived, and derived twice is drift."""
        missing = [name for name in ("lower", "upper", "level") if name not in payload]
        if missing:
            raise ContractError(f"an interval payload is missing {_named(missing)}.")
        return cls(
            lower=payload["lower"],
            upper=payload["upper"],
            level=payload["level"],
            unit=payload.get("unit", UNIT),
            space=payload.get("space", SPACE),
        )


def _units(unit: object, space: object, what: str) -> None:
    if unit != UNIT or space != SPACE:
        raise ContractError(
            f"{what} claims unit {unit!r} in space {space!r}; this contract carries "
            f"{UNIT!r} in {SPACE!r}. The surrogate is fitted on log1p(capacity) and every "
            f"number here is expm1 of a head, so a payload that names the other space is a "
            f"number a reader would believe in the wrong one."
        )


@dataclass(frozen=True)
class ScreenVerdict:
    """One screen's answer about this candidate, carried verbatim into the result.

    The composite :class:`DomainVerdict` says whether the candidate was admitted and names the
    worst code; this says what *each* rule decided. A candidate rejected by one screen and
    admitted by three is a different finding from one rejected by all four, and card #44's
    whole shape is that you can see which.

    Attributes:
        screen: The screen's name -- ``'temperature'``, ``'domain'``.
        passed: ``True`` where this screen admitted.
        code: :data:`~hydms.screens.protocol.ADMITTED`, or one of the screen's declared
            reasons.
        reason: The sentence a reader gets.
    """

    screen: str
    passed: bool
    code: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.screen, str) or not self.screen.strip():
            raise ContractError("a screen verdict needs the name of the screen it came from.")
        if not isinstance(self.passed, bool):
            raise ContractError(
                f"screen {self.screen!r} reports passed={self.passed!r}, which is not a "
                f"bool. A missing verdict is the silent drop wearing a different hat."
            )
        object.__setattr__(self, "code", _code(self.code, f"screen {self.screen!r}'s code"))
        object.__setattr__(
            self, "reason", _sentence(self.reason, f"screen {self.screen!r}'s reason")
        )
        if self.passed != (self.code == ADMITTED):
            raise ContractError(
                f"screen {self.screen!r} disagrees with itself: passed={self.passed} with "
                f"code={self.code!r}. 'passed' is true exactly where the code is "
                f"{ADMITTED!r}."
            )

    def to_dict(self) -> dict[str, Any]:
        """The verdict as JSON-ready primitives."""
        return {
            "screen": self.screen,
            "passed": self.passed,
            "code": self.code,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ScreenVerdict:
        """Rebuild one screen's verdict."""
        missing = [
            name for name in ("screen", "passed", "code", "reason") if name not in payload
        ]
        if missing:
            raise ContractError(f"a screen-verdict payload is missing {_named(missing)}.")
        return cls(
            screen=payload["screen"],
            passed=payload["passed"],
            code=payload["code"],
            reason=payload["reason"],
        )


@dataclass(frozen=True)
class DomainVerdict:
    """Whether this candidate is one the model may be asked about, and why.

    The second half of HG-2's "never a bare number": an interval says how uncertain the model
    is, and this says whether the question was inside what the model can defend at all. They
    come apart in both directions and #30 measured it -- ``SS`` is the best family by R² with
    the second-worst interval coverage, ``HEA`` the second worst by R² with the best -- so
    neither substitutes for the other.

    Attributes:
        admitted: ``True`` only where every screen admitted.
        code: :data:`~hydms.screens.protocol.ADMITTED`, or the **worst** rejection code, in
            the precedence the emitting screen defines.
        reason: The sentence a reader gets, naming every rule that rejected.
        screens: Each screen's own verdict, in the order they ran.
    """

    admitted: bool
    code: str
    reason: str
    screens: tuple[ScreenVerdict, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.admitted, bool):
            raise ContractError(
                f"a domain verdict reports admitted={self.admitted!r}, which is not a bool."
            )
        object.__setattr__(self, "code", _code(self.code, "the domain verdict's code"))
        object.__setattr__(self, "reason", _sentence(self.reason, "the domain verdict's reason"))
        object.__setattr__(self, "screens", tuple(self.screens))
        if self.admitted != (self.code == ADMITTED):
            raise ContractError(
                f"the domain verdict disagrees with itself: admitted={self.admitted} with "
                f"code={self.code!r}. 'admitted' is true exactly where the code is "
                f"{ADMITTED!r}."
            )
        if self.admitted and any(not verdict.passed for verdict in self.screens):
            rejected = [verdict.screen for verdict in self.screens if not verdict.passed]
            raise ContractError(
                f"the verdict says admitted, but {_named(rejected)} rejected. A composite "
                f"verdict is admitted only where every screen admitted "
                f"(`Verdicts.admitted`)."
            )
        if not self.admitted and self.screens and all(v.passed for v in self.screens):
            raise ContractError(
                "the verdict says rejected and every screen admitted. A rejection with no "
                "rule behind it is the unexplained absence this layer exists to remove."
            )

    @classmethod
    def admitted_by(cls, screens: Sequence[str]) -> DomainVerdict:
        """The admitted verdict, with one passing :class:`ScreenVerdict` per named screen.

        The happy path spelled once, because writing it out at three call sites is how the
        sentence a user reads comes to differ between the API and the app.
        """
        names = tuple(screens)
        if not names:
            raise ContractError(
                "admitted_by() was given no screens. A verdict nothing judged is the silent "
                "drop's mirror image -- the candidate is admitted *because* the rules did not "
                "run (hydms.screens.protocol.apply_screens refuses the same call)."
            )
        return cls(
            admitted=True,
            code=ADMITTED,
            reason=f"inside every applicability rule that ran: {', '.join(names)}",
            screens=tuple(
                ScreenVerdict(
                    screen=name, passed=True, code=ADMITTED, reason="inside this rule"
                )
                for name in names
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """The verdict as JSON-ready primitives."""
        return {
            "admitted": self.admitted,
            "code": self.code,
            "reason": self.reason,
            "screens": [verdict.to_dict() for verdict in self.screens],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> DomainVerdict:
        """Rebuild a domain verdict."""
        missing = [name for name in ("admitted", "code", "reason") if name not in payload]
        if missing:
            raise ContractError(f"a domain-verdict payload is missing {_named(missing)}.")
        return cls(
            admitted=payload["admitted"],
            code=payload["code"],
            reason=payload["reason"],
            screens=tuple(
                ScreenVerdict.from_dict(entry) for entry in payload.get("screens", ())
            ),
        )


@dataclass(frozen=True)
class Novelty:
    """How far this composition is from the nearest alloy the model was trained on.

    Attributes:
        distance: The metric's value. Non-negative, and ``0.0`` means the composition *is* a
            training alloy.
        nearest: The nearest training composition, as its formula string.
        metric: What measured it -- ``'ElMD'``. Named rather than assumed: #48 established
            that the applicability ceiling is **not** a composition distance, so a distance in
            a result is novelty evidence for AC-7 and must never be read as the domain
            verdict.
    """

    distance: float
    nearest: str
    metric: str = "ElMD"

    def __post_init__(self) -> None:
        object.__setattr__(self, "distance", _finite(self.distance, "the novelty distance"))
        if self.distance < 0.0:
            raise ContractError(
                f"the novelty distance is {self.distance:g}; a distance is non-negative."
            )
        if not isinstance(self.nearest, str) or not self.nearest.strip():
            raise ContractError(
                "a novelty measurement names the nearest known alloy; this one does not. A "
                "distance without the thing it is a distance to cannot be checked."
            )
        if not isinstance(self.metric, str) or not self.metric.strip():
            raise ContractError("a novelty measurement names the metric that produced it.")

    def to_dict(self) -> dict[str, Any]:
        """The measurement as JSON-ready primitives."""
        return {"distance": self.distance, "nearest": self.nearest, "metric": self.metric}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Novelty:
        """Rebuild a novelty measurement."""
        missing = [name for name in ("distance", "nearest") if name not in payload]
        if missing:
            raise ContractError(f"a novelty payload is missing {_named(missing)}.")
        return cls(
            distance=payload["distance"],
            nearest=payload["nearest"],
            metric=payload.get("metric", "ElMD"),
        )


# --------------------------------------------------------------------------------------
# The two answers
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class PredictionResult:
    """An answer with a number in it -- and therefore with an interval and a verdict.

    ``interval`` and ``domain`` have no defaults and cannot be ``None``. That is the whole
    structural claim of card #75 and the half of HG-2 that is a type rather than a check:
    there is no way to construct this object holding a point estimate alone.

    ``novelty`` has no default either, so a caller must *say* what it knows. ``None`` is
    legal and means "not measured" -- #49's screen is unstarted and ``ElMD`` is not in the
    ``Project`` environment -- and it is a stated absence rather than a missing field, which
    is the distinction AC-7 will need when it asks every published candidate for a distance.

    Attributes:
        request: What was asked. Carried so that an answer read from a log or a batch file is
            self-contained; the batch path (#84) writes thousands of these and a row that does
            not say what it answers is a row nobody can check.
        capacity: The point estimate -- the **median** head, in :data:`UNIT`. Not the lower
            confidence bound: ``lcb`` is the *ranking* key (risk R1) and reporting it as the
            estimate would understate every answer by design.
        interval: The calibrated band and its nominal level.
        domain: The applicability verdict, with a reason.
        novelty: The ElMD distance to the nearest known alloy, or ``None`` if not measured.
        model_version: Which artifact version answered -- ``'v2'``. A number without the
            version that produced it is not evidence (card #83).
        unit: :data:`UNIT`.
        space: :data:`SPACE`.

    An admitted verdict is **not** required. A result may carry a rejecting verdict and still
    carry its number: that is the "genuinely low prediction versus a refusal" distinction #80
    has to answer, and collapsing the two would mean the only way to see the model's answer
    for an out-of-domain candidate is to remove the screen.
    """

    request: PredictionRequest
    capacity: float
    interval: Interval
    domain: DomainVerdict
    novelty: Novelty | None
    model_version: str
    unit: str = UNIT
    space: str = SPACE

    def __post_init__(self) -> None:
        if not isinstance(self.request, PredictionRequest):
            raise ContractError(
                f"a result carries the request it answers; this one carries "
                f"{type(self.request).__name__}."
            )
        object.__setattr__(self, "capacity", _finite(self.capacity, "the capacity estimate"))
        if not isinstance(self.interval, Interval):
            raise ContractError(
                "a result cannot be constructed without an interval. A point estimate alone "
                "is the bare number gate HG-2 exists to forbid: a tree ensemble extrapolates "
                "as a constant, so outside the training hull it returns a plausible flat "
                "value and the band is what makes that visible (risk R1)."
            )
        if not isinstance(self.domain, DomainVerdict):
            raise ContractError(
                "a result cannot be constructed without a domain verdict. An interval says "
                "how uncertain the model is; the verdict says whether the question was one "
                "the model may be asked at all, and #30 measured the two coming apart in "
                "both directions."
            )
        if self.novelty is not None and not isinstance(self.novelty, Novelty):
            raise ContractError(
                f"novelty is {type(self.novelty).__name__}; it is a Novelty, or None meaning "
                f"'not measured'."
            )
        if not isinstance(self.model_version, str) or not self.model_version.strip():
            raise ContractError(
                "a result names the artifact version that answered. An unversioned number "
                "cannot be reproduced and must never reach a caller (card #78's health check "
                "reports the same string)."
            )
        _units(self.unit, self.space, "a result")
        # Unreached: `Interval.__post_init__` already refuses any other unit or space, so a
        # band that constructed at all agrees with this. Kept as the guard that would fire if
        # the unit ever became per-instance -- the same shape as `featurize`'s closing
        # contract check, and for the same reason.
        if self.interval.unit != self.unit or self.interval.space != self.space:
            raise ContractError(
                f"the result is in {self.unit!r}/{self.space!r} and its interval is in "
                f"{self.interval.unit!r}/{self.interval.space!r}. A band in a different space "
                f"from its estimate is not a band around it."
            )

    @property
    def refused(self) -> bool:
        """Always ``False``. A property, not a field, so it cannot be set to the wrong value."""
        return False

    def to_dict(self) -> dict[str, Any]:
        """The whole answer as JSON-ready primitives, under :data:`SCHEMA`."""
        return {
            "schema": SCHEMA,
            "refused": False,
            "request": self.request.to_dict(),
            "capacity": self.capacity,
            "unit": self.unit,
            "space": self.space,
            "interval": self.interval.to_dict(),
            "domain": self.domain.to_dict(),
            "novelty": None if self.novelty is None else self.novelty.to_dict(),
            "model_version": self.model_version,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PredictionResult:
        """Rebuild a result from :meth:`to_dict`'s output. See :func:`answer_from`."""
        _schema(payload)
        missing = [
            name
            for name in ("request", "capacity", "interval", "domain", "model_version")
            if name not in payload
        ]
        if missing:
            raise ContractError(
                f"a result payload is missing {_named(missing)}. A payload without an "
                f"interval or a domain verdict is the bare number arriving by another door."
            )
        novelty = payload.get("novelty")
        return cls(
            request=PredictionRequest.from_dict(payload["request"]),
            capacity=payload["capacity"],
            interval=Interval.from_dict(payload["interval"]),
            domain=DomainVerdict.from_dict(payload["domain"]),
            novelty=None if novelty is None else Novelty.from_dict(novelty),
            model_version=payload["model_version"],
            unit=payload.get("unit", UNIT),
            space=payload.get("space", SPACE),
        )


@dataclass(frozen=True)
class Refusal:
    """An answer with no number in it, and a stated reason for that.

    A refusal is a *result*, not an error. It travels the same path, serialises to the same
    schema and is told apart by one boolean, because the alternative -- an exception at the
    boundary -- is what turns "contains Tc, which appears in no training alloy" into "500
    Internal Server Error" and sends the user away instead of telling them what to do next.

    There is no ``capacity`` field and no ``interval`` field. A refusal that carried a number
    "for reference" would be the bare number with a disclaimer, and every consumer would
    eventually read it.

    Attributes:
        request: What was asked.
        code: The machine-readable reason, from :func:`reason_codes`. A cause no screen can
            judge -- an unparseable formula, an element no property table covers -- is
            :data:`~hydms.screens.protocol.INDETERMINATE`, and the sentence goes in
            ``explanation``.
        explanation: The human-readable reason. One sentence, naming the candidate and the
            rule.
        model_version: Which artifact version was loaded, or ``None`` when the refusal
            happened before one was -- an unparseable formula needs no model.
        screens: Each screen's verdict, where screens ran.
    """

    request: PredictionRequest
    code: str
    explanation: str
    model_version: str | None = None
    screens: tuple[ScreenVerdict, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.request, PredictionRequest):
            raise ContractError(
                f"a refusal carries the request it declines; this one carries "
                f"{type(self.request).__name__}."
            )
        object.__setattr__(self, "code", _code(self.code, "the refusal code"))
        if self.code == ADMITTED:
            raise ContractError(
                f"a refusal cannot carry {ADMITTED!r}: that code means the candidate was "
                f"admitted, and an admitted candidate gets a result with a number in it."
            )
        object.__setattr__(
            self, "explanation", _sentence(self.explanation, "the refusal explanation")
        )
        object.__setattr__(self, "screens", tuple(self.screens))
        if self.model_version is not None and (
            not isinstance(self.model_version, str) or not self.model_version.strip()
        ):
            raise ContractError(
                "a refusal names the artifact version that was loaded, or None if none was."
            )

    @property
    def refused(self) -> bool:
        """Always ``True``. A property, not a field, so it cannot be set to the wrong value."""
        return True

    def to_dict(self) -> dict[str, Any]:
        """The refusal as JSON-ready primitives, under :data:`SCHEMA`."""
        return {
            "schema": SCHEMA,
            "refused": True,
            "request": self.request.to_dict(),
            "code": self.code,
            "explanation": self.explanation,
            "model_version": self.model_version,
            "screens": [verdict.to_dict() for verdict in self.screens],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Refusal:
        """Rebuild a refusal from :meth:`to_dict`'s output. See :func:`answer_from`."""
        _schema(payload)
        missing = [
            name for name in ("request", "code", "explanation") if name not in payload
        ]
        if missing:
            raise ContractError(f"a refusal payload is missing {_named(missing)}.")
        return cls(
            request=PredictionRequest.from_dict(payload["request"]),
            code=payload["code"],
            explanation=payload["explanation"],
            model_version=payload.get("model_version"),
            screens=tuple(
                ScreenVerdict.from_dict(entry) for entry in payload.get("screens", ())
            ),
        )


#: What a prediction path returns. Both members carry ``request``, ``refused`` and a
#: ``to_dict`` under the same :data:`SCHEMA`, so a consumer that only needs "did it answer"
#: reads one boolean and a consumer that needs the number checks the type.
Answer = PredictionResult | Refusal


def _schema(payload: Mapping[str, Any]) -> None:
    declared = payload.get("schema")
    if declared is not None and declared != SCHEMA:
        raise ContractError(
            f"the payload carries schema {declared!r}, and this version of hydms reads "
            f"{SCHEMA!r}. A reader that guesses at unknown fields is how a dropped interval "
            f"becomes a silently narrower band."
        )


def answer_from(payload: Mapping[str, Any]) -> Answer:
    """Rebuild whichever answer a payload holds, dispatching on ``refused``.

    The one door back from JSON, so no consumer has to know that the discriminator is called
    ``refused`` or that ``True`` means :class:`Refusal`. #79's transport-parity gate compares
    what the API returned to what :func:`predict_capacity` returned, and it can only do that
    if both sides come back through one function.

    Raises:
        ContractError: the payload does not say whether it was refused, carries an unknown
            schema, or is missing a field its own kind requires.
    """
    if "refused" not in payload:
        raise ContractError(
            "the payload does not say whether it was refused. That boolean is the whole of "
            "how a consumer tells a refusal from a genuinely low prediction; a payload "
            "without it is ambiguous in the one way this contract exists to prevent."
        )
    refused = payload["refused"]
    if not isinstance(refused, bool):
        raise ContractError(f"'refused' is {refused!r}, which is not a bool.")
    return Refusal.from_dict(payload) if refused else PredictionResult.from_dict(payload)
