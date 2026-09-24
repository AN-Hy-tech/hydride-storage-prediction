"""L6 -- the forward-prediction page, as data.

``app/main.py`` (card #82) is a Streamlit script, and Streamlit is in the ``app`` extra that CI
does not install. So everything the page *promises* is decided here, where the fast lane runs
it, and the script only lays out what this module returns -- the same split
:mod:`hydms.figures` makes between a chart's description and its renderer, for the same
reason: a guarantee that lives in an optional dependency is a guarantee nobody checks.

**What the page promises, and where each one is enforced.**

* An estimate is never shown without its interval. :func:`prediction_view` writes the
  headline from the interval and the estimate together, and the figure is
  :func:`~hydms.figures.prediction_band`, which cannot draw a point without its band.
* A refusal is shown as a refusal, with its reason. :class:`PageView` for a refusal has no
  figure and no number: there is no field for one to sit in, as there is none on
  :class:`~hydms.delivery.contract.Refusal`. Its headline says in words that this is not a low
  prediction, because that is the one misreading a refusal invites.
* The domain verdict is shown screen by screen, passed or not, each with its reason -- an
  admitted answer included, so "admitted" is a finding the reader can check rather than an
  absence of warnings.
* The artifact version answering is on every view that has one.
* An unreachable service is a view of its own, which says so and shows nothing else.
* The nearest known alloys are drawn with what was **measured** on them
  (:func:`neighbours_figure`, from ``GET /v1/neighbours``), never with a prediction for them.
* The temperature sweep is drawn over the training rows behind each part of it
  (:func:`sweep_view`, over :func:`support_from` the served model card), and a temperature the
  service refused is a listed gap, never a point on the curve.

**The reference the band is drawn against is the deployment's, not the package's.** The
prediction band anchors its axis to the trained capacity range, and
:func:`~hydms.figures.prediction_band` defaults to the committed
``hydms/screens/domain-reference.json``. A client of a service must not assume the service
judged against the same file it happens to have installed, so :func:`reference_from` rebuilds
the reference from ``GET /v1/model`` -- the facts the answering deployment says it used.

Card #82.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from hydms.delivery.client import InvalidRequest
from hydms.delivery.contract import (
    UNIT,
    Answer,
    PredictionRequest,
    PredictionResult,
    Refusal,
    ScreenVerdict,
)
from hydms.delivery.neighbours import Neighbourhood
from hydms.figures import (
    Figure,
    Neighbour,
    TemperatureSupport,
    nearest_neighbours,
    prediction_band,
    temperature_sweep,
)
from hydms.screens.domain import DomainReference

__all__ = [
    "ANSWERED",
    "INVALID_REQUEST",
    "REFUSED",
    "SWEEP_STEP_K",
    "UNREACHABLE",
    "PageView",
    "SweepView",
    "VerdictRow",
    "neighbours_figure",
    "prediction_view",
    "reference_from",
    "support_from",
    "sweep_requests",
    "sweep_temperatures",
    "sweep_view",
    "unreachable_view",
]

#: The four things a page can be showing. A view is exactly one of them.
ANSWERED = "answered"
REFUSED = "refused"
INVALID_REQUEST = "invalid-request"
UNREACHABLE = "unreachable"

#: Kelvin between two points of the temperature sweep. 25 K puts 25 points across the served
#: 195-773 K window -- one batch request, well under the batch limit -- and resolves the curve
#: finer than the 50 K support bins beneath it, so no bin is represented by a single point.
SWEEP_STEP_K = 25.0


class PageError(ValueError):
    """The model card does not carry the facts the page needs to draw against."""


@dataclass(frozen=True)
class VerdictRow:
    """One screen's verdict as the page lists it."""

    screen: str
    passed: bool
    code: str
    reason: str

    @classmethod
    def of(cls, verdict: ScreenVerdict) -> VerdictRow:
        return cls(
            screen=verdict.screen, passed=verdict.passed, code=verdict.code, reason=verdict.reason
        )


@dataclass(frozen=True)
class PageView:
    """Everything the prediction page shows for one request.

    Attributes:
        kind: :data:`ANSWERED`, :data:`REFUSED`, :data:`INVALID_REQUEST` or :data:`UNREACHABLE`.
        headline: The one sentence the page leads with.
        detail: Sentences under it -- the refusal's explanation, the invalid request's
            problems, the caveat an answer carries.
        verdicts: Every screen's verdict, in the order the service ran them.
        figure: The prediction band, for an answer; ``None`` for every other kind.
        version: The artifact version that answered, or ``None`` where nothing did.
    """

    kind: str
    headline: str
    detail: tuple[str, ...] = ()
    verdicts: tuple[VerdictRow, ...] = ()
    figure: Figure | None = None
    version: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in (ANSWERED, REFUSED, INVALID_REQUEST, UNREACHABLE):
            raise PageError(f"{self.kind!r} is not something the page can be showing.")
        if (self.figure is not None) != (self.kind == ANSWERED):
            raise PageError(
                f"a {self.kind} view {'without' if self.figure is None else 'with'} a figure: "
                f"only an answer is drawn, and an answer is always drawn."
            )


def _number(value: float) -> str:
    return f"{value:g}"


def reference_from(card: Mapping[str, Any]) -> DomainReference:
    """The applicability reference the answering deployment judged against, from its model card.

    Raises:
        PageError: the card does not carry the trained capacity range. The page will not fall
            back to the installed package's reference: that is a different deployment's claim.
    """
    ranges = card.get("trained_ranges") or {}
    capacity = ranges.get("capacity")
    needed = ("low", "high", "cross_family_max", "sole_family", "rows_above", "rows")
    if not isinstance(capacity, Mapping) or any(key not in capacity for key in needed):
        raise PageError(
            f"model card {card.get('version')!r} does not state the trained capacity range, so "
            f"the band has nothing honest to be drawn against."
        )
    span = ranges.get("feature_span") or {}
    transfer = (card.get("metrics") or {}).get("transfer_r2") or {}
    return DomainReference(
        rows=int(capacity["rows"]),
        trained_min=float(capacity["low"]),
        trained_max=float(capacity["high"]),
        cross_family_max=float(capacity["cross_family_max"]),
        sole_family=str(capacity["sole_family"]),
        rows_above=int(capacity["rows_above"]),
        feature_span={str(name): (float(pair[0]), float(pair[1])) for name, pair in span.items()},
        transfer={str(family): float(score) for family, score in transfer.items()},
    )


def _answered(result: PredictionResult, reference: DomainReference) -> PageView:
    interval = result.interval
    request = result.request
    headline = (
        f"{request.formula} at {_number(request.temperature_k)} K: {result.capacity:.2f} {UNIT}, "
        f"between {interval.lower:.2f} and {interval.upper:.2f} {UNIT} "
        f"({_number(interval.level * 100)}% nominal band, {interval.width:.2f} {UNIT} wide)."
    )
    detail = [
        "The level is nominal -- what the band is calibrated to -- not coverage measured on "
        "this composition.",
        "This is a material weight percent. Comparing it to a DOE target, which is set for a "
        "whole storage system, is a two-step overstatement (PRD 4.4).",
    ]
    if result.novelty is not None:
        detail.append(
            f"Nearest known alloy: {result.novelty.nearest}, at {result.novelty.distance:.2f} on "
            f"the {result.novelty.metric} scale."
        )
    return PageView(
        kind=ANSWERED,
        headline=headline,
        detail=tuple(detail),
        verdicts=tuple(VerdictRow.of(screen) for screen in result.domain.screens),
        figure=prediction_band(result, reference=reference),
        version=result.model_version,
    )


def _refused(refusal: Refusal) -> PageView:
    request = refusal.request
    return PageView(
        kind=REFUSED,
        headline=(
            f"No prediction for {request.formula} at {_number(request.temperature_k)} K. "
            f"The service declined to answer ({refusal.code}) -- this is not a low capacity, "
            f"it is no capacity at all."
        ),
        detail=(refusal.explanation,),
        verdicts=tuple(VerdictRow.of(screen) for screen in refusal.screens),
        version=refusal.model_version,
    )


def _invalid_request(invalid: InvalidRequest, version: str | None) -> PageView:
    return PageView(
        kind=INVALID_REQUEST,
        headline=(
            f"The request could not be read: {invalid.message} No material was judged, so "
            f"nothing here is a statement about one."
        ),
        detail=invalid.problems,
        version=version,
    )


def prediction_view(
    outcome: Answer | InvalidRequest, *, card: Mapping[str, Any]
) -> PageView:
    """The page for one request's outcome.

    Args:
        outcome: What :meth:`~hydms.delivery.client.ServiceClient.predict` returned.
        card: ``GET /v1/model`` from the same service, for the reference the band is drawn
            against and the version an invalid request is reported under.
    """
    if isinstance(outcome, InvalidRequest):
        version = card.get("version")
        return _invalid_request(outcome, str(version) if version is not None else None)
    if isinstance(outcome, Refusal):
        return _refused(outcome)
    if isinstance(outcome, PredictionResult):
        return _answered(outcome, reference_from(card))
    raise PageError(f"{type(outcome).__name__} is not an outcome the service can return.")


def unreachable_view(error: BaseException) -> PageView:
    """The page when there is no service to ask. It says so, and shows nothing else."""
    return PageView(
        kind=UNREACHABLE,
        headline=(
            "The prediction service is not answering, so this page cannot predict anything. "
            "No estimate below is stale or cached: there is none."
        ),
        detail=(str(error),),
    )


# --------------------------------------------------------------------------------------
# The nearest known alloys, and the temperature sweep (the two boxes the service now serves)
# --------------------------------------------------------------------------------------


def neighbours_figure(result: PredictionResult, neighbourhood: Neighbourhood) -> Figure:
    """The nearest known alloys, with what was measured on them, beside the prediction.

    One dot per neighbour: the row measured **closest to the asked temperature**, because a
    capacity measured at 600 K is not comparable with a prediction at 298 K and the chart
    caption says which temperatures were used. The whole of each neighbour's measurements is on
    the :class:`~hydms.delivery.neighbours.Neighbourhood` for a table beside it.

    Raises:
        PageError: the neighbourhood is of another formula, or was served by another artifact
            version -- a service restarted between the two requests. Drawing them together would
            put two deployments' statements on one axis.
    """
    if neighbourhood.formula != result.request.formula:
        raise PageError(
            f"the neighbours are of {neighbourhood.formula!r} and the answer is about "
            f"{result.request.formula!r}; one chart cannot carry both."
        )
    if neighbourhood.model_version != result.model_version:
        raise PageError(
            f"the answer came from artifact {result.model_version} and the neighbours from "
            f"{neighbourhood.model_version}: the service changed version between the two "
            f"requests. Ask again."
        )
    kelvin = result.request.temperature_k
    return nearest_neighbours(
        result,
        [
            Neighbour(
                formula=alloy.formula,
                distance=alloy.distance,
                capacity=(row := alloy.closest_to(kelvin)).capacity,
                temperature_k=row.temperature_k,
                alloy_class=row.alloy_class,
            )
            for alloy in neighbourhood.neighbours
        ],
        novelty_ceiling=neighbourhood.novelty_ceiling,
    )


def support_from(card: Mapping[str, Any]) -> TemperatureSupport:
    """The training rows per temperature bin, as the answering deployment reports them.

    Raises:
        PageError: the card carries no support. The sweep will not be drawn over a histogram
            the page made up or remembered: that is the "39 rows above 500 K" constant
            :class:`~hydms.figures.TemperatureSupport` was written to retire.
    """
    support = (card.get("trained_ranges") or {}).get("temperature_support")
    if not isinstance(support, Mapping) or not support.get("counts"):
        raise PageError(
            f"model card {card.get('version')!r} does not report how many training rows sit "
            f"at each temperature, so a sweep would have nothing honest beneath it."
        )
    return TemperatureSupport(
        edges=tuple(float(edge) for edge in support["edges"]),
        counts=tuple(int(count) for count in support["counts"]),
        source=str(support.get("source") or "training rows per temperature bin"),
    )


def sweep_temperatures(card: Mapping[str, Any], *, step: float = SWEEP_STEP_K) -> tuple[float, ...]:
    """Temperatures across the served trained window, ``step`` apart, both ends included.

    Read from the card rather than typed, so a deployment with a different window sweeps its
    own; every one of them is inside the window, so the ``temperature`` screen admits each.
    """
    window = (card.get("trained_ranges") or {}).get("temperature")
    if not isinstance(window, Mapping) or "low" not in window or "high" not in window:
        raise PageError(
            f"model card {card.get('version')!r} does not state its temperature window."
        )
    if step <= 0:
        raise PageError(f"a sweep step of {step:g} K never reaches the other end of the window.")
    low, high = float(window["low"]), float(window["high"])
    points = [low]
    while points[-1] + step < high:
        points.append(points[-1] + step)
    if points[-1] != high:
        points.append(high)
    return tuple(points)


def sweep_requests(formula: str, card: Mapping[str, Any]) -> list[PredictionRequest]:
    """One request per :func:`sweep_temperatures` point, for ``ServiceClient.predict_many``.

    Here rather than in the script so the script builds no contract object of its own: it
    imports the client, this module and the renderer, and nothing else.
    """
    return [
        PredictionRequest(formula=formula, temperature_k=kelvin)
        for kelvin in sweep_temperatures(card)
    ]


@dataclass(frozen=True)
class SweepView:
    """One composition across the trained window: the curve where it was answered, and where not.

    Attributes:
        headline: What the sweep shows, in one sentence.
        figure: The sweep over its support, or ``None`` when no temperature was answered -- a
            curve through no points is not a finding.
        refused: ``(temperature, code)`` for every temperature the service declined. Listed,
            never interpolated across: a gap in the curve is where the model would not answer,
            and a line drawn through it would answer for it.
        version: The artifact version that answered, or ``None`` where nothing did.
    """

    headline: str
    figure: Figure | None
    refused: tuple[tuple[float, str], ...]
    version: str | None


def sweep_view(answers: Sequence[Answer], *, card: Mapping[str, Any]) -> SweepView:
    """The temperature sweep for one composition, from ``predict_many``'s answers.

    Raises:
        PageError: the answers are of more than one composition, or come from more than one
            artifact version, or the card carries no support.
    """
    if not answers:
        raise PageError("a sweep of no temperatures shows nothing.")
    formulas = {answer.request.formula for answer in answers}
    versions = {answer.model_version for answer in answers if answer.model_version is not None}
    if len(formulas) != 1:
        raise PageError(f"a sweep is one composition and was given {sorted(formulas)}.")
    if len(versions) > 1:
        raise PageError(
            f"the sweep was answered by {sorted(versions)}: the service changed version "
            f"part-way through. Ask again."
        )
    formula = next(iter(formulas))
    version = next(iter(versions)) if versions else None
    answered = [answer for answer in answers if isinstance(answer, PredictionResult)]
    refused = tuple(
        sorted(
            (answer.request.temperature_k, answer.code)
            for answer in answers
            if isinstance(answer, Refusal)
        )
    )
    support = support_from(card)
    if not answered:
        return SweepView(
            headline=(
                f"No temperature in the trained window was answered for {formula}: the "
                f"service declined every one, so there is no curve to draw."
            ),
            figure=None,
            refused=refused,
            version=version,
        )
    if refused:
        headline = (
            f"{formula} across the trained window: answered at {len(answered)} of "
            f"{len(answers)} temperatures. The curve is drawn only where the service answered; "
            f"the {len(refused)} refused temperature(s) are listed, not filled in."
        )
    else:
        headline = f"{formula} across the trained window, every temperature answered."
    return SweepView(
        headline=headline,
        figure=temperature_sweep(answered, support=support),
        refused=refused,
        version=version,
    )
