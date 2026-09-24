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

**The reference the band is drawn against is the deployment's, not the package's.** The
prediction band anchors its axis to the trained capacity range, and
:func:`~hydms.figures.prediction_band` defaults to the committed
``hydms/screens/domain-reference.json``. A client of a service must not assume the service
judged against the same file it happens to have installed, so :func:`reference_from` rebuilds
the reference from ``GET /v1/model`` -- the facts the answering deployment says it used.

Card #82.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from hydms.delivery.client import InvalidRequest
from hydms.delivery.contract import (
    UNIT,
    Answer,
    PredictionResult,
    Refusal,
    ScreenVerdict,
)
from hydms.figures import Figure, prediction_band
from hydms.screens.domain import DomainReference

__all__ = [
    "ANSWERED",
    "INVALID_REQUEST",
    "REFUSED",
    "UNREACHABLE",
    "PageView",
    "VerdictRow",
    "prediction_view",
    "reference_from",
    "unreachable_view",
]

#: The four things a page can be showing. A view is exactly one of them.
ANSWERED = "answered"
REFUSED = "refused"
INVALID_REQUEST = "invalid-request"
UNREACHABLE = "unreachable"


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
