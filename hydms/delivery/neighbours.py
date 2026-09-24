"""L6 -- the known alloys nearest a composition, and what was *measured* on them.

::

    from hydms.delivery.neighbours import nearest_measured

    nearest_measured("LaNi5", 5, bundle=bundle)     # -> Neighbourhood

A prediction answer names one nearest alloy and its distance (``novelty.nearest``), and nothing
that was measured on it. Card #82 asks the page to show the k nearest *with their measured
capacities*, because a reader who can see that the three closest known alloys were measured at
1.3-1.5 wt% reads a 1.4 wt% prediction very differently from one whose neighbours span 0.2-6.
``GET /v1/neighbours`` serves that; this module is what it serves.

**It is a lookup, not a prediction, and it says so by its shape.** No model runs, no screen
judges, and there is no interval, because nothing here is estimated: every capacity in a
:class:`Neighbourhood` is a training row as it was recorded. HG-2's rule -- no number without
an interval and a domain verdict -- is about *predictions*, and a measured value dressed with a
band would be claiming an uncertainty nobody computed. So the payload carries
``"basis": "measured"`` and has no field a prediction could occupy.

**The same reference the novelty screen judges with, read off the running bundle.** Not
:meth:`~hydms.screens.novelty.NoveltyReference.packaged`: a client of a service must hear about
the reference that deployment loaded, which is the rule :mod:`hydms.delivery.modelcard` follows
for the same reason. The first neighbour is therefore always the ``novelty.nearest`` a
prediction for the same formula carries (:func:`~hydms.screens.novelty.nearest_known` states
why), and ``reference_sha256`` is the digest ``GET /v1/model`` reports for that screen.

**Which rows.** The training split's, filed under each composition's canonical key -- the same
780 compositions the novelty distance is measured against, and the same 893 rows the
applicability reference was measured over. Validation and test rows are not "known" for this
purpose, for the reason :func:`~hydms.screens.novelty.emit` gives: a candidate is near what the
model *learned from*.

Card #82.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from hydms.delivery.contract import UNIT, ContractError, check_formula

if TYPE_CHECKING:  # pragma: no cover - typing only
    from hydms.delivery.predict import ArtifactBundle

__all__ = [
    "BASIS",
    "DEFAULT_K",
    "MAX_K",
    "SCHEMA",
    "KnownAlloy",
    "Measured",
    "Neighbourhood",
    "UnreadableFormula",
    "nearest_measured",
]

#: The payload's own schema. Separate from :data:`hydms.delivery.contract.SCHEMA` because this
#: is not an answer and must never be read as one.
SCHEMA = "hydms.delivery.neighbours/1"

#: What every capacity in the payload is. Carried on the payload rather than implied, so a body
#: pasted somewhere without its route still says it is not a prediction.
BASIS = "measured"

#: How many neighbours a caller gets without asking. Five fit one chart legibly.
DEFAULT_K = 5

#: The most a caller may ask for. Not a cost bound -- the distance to all 780 compositions is
#: one vectorised call either way -- but a relevance one: past a couple of dozen the "nearest"
#: known alloys are simply the corpus, sorted, and the corpus is not what this route is for.
MAX_K = 25


class UnreadableFormula(ValueError):
    """The formula is not a composition the metric can place. Carries the parser's own sentence."""


def _number(value: object, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ContractError(f"{what} must be a number, not {type(value).__name__}.")
    number = float(value)
    if not math.isfinite(number):
        raise ContractError(f"{what} is {number}, which is not a finite number.")
    return number


@dataclass(frozen=True)
class Measured:
    """One training row: the capacity recorded at one temperature, and the alloy's family."""

    temperature_k: float
    capacity: float
    alloy_class: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "temperature_k", _number(self.temperature_k, "temperature_k"))
        object.__setattr__(self, "capacity", _number(self.capacity, "capacity"))
        object.__setattr__(self, "alloy_class", str(self.alloy_class))

    def to_dict(self) -> dict[str, Any]:
        return {
            "temperature_k": self.temperature_k,
            "capacity": self.capacity,
            "alloy_class": self.alloy_class,
        }


@dataclass(frozen=True)
class KnownAlloy:
    """A training composition, its distance from the one asked about, and every row measured on it.

    Attributes:
        formula: The composition as the reference spells it.
        distance: On the ElMD modified-Pettifor scale. Zero means the asked formula *is* this
            composition, however it was spelled.
        measured: Every training row of it, ascending in temperature. Never empty.
    """

    formula: str
    distance: float
    measured: tuple[Measured, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "distance", _number(self.distance, "distance"))
        object.__setattr__(self, "measured", tuple(self.measured))
        if self.distance < 0.0:
            raise ContractError(
                f"{self.formula!r} is at distance {self.distance}; distances are not negative."
            )
        if not self.measured:
            raise ContractError(
                f"{self.formula!r} carries no measurement. A known alloy is known because a "
                f"row measured it; one without rows is not a neighbour worth showing."
            )

    def closest_to(self, temperature_k: float) -> Measured:
        """The row measured nearest ``temperature_k``; the cooler one on a tie."""
        return min(
            self.measured,
            key=lambda row: (abs(row.temperature_k - temperature_k), row.temperature_k),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "formula": self.formula,
            "distance": self.distance,
            "measured": [row.to_dict() for row in self.measured],
        }


@dataclass(frozen=True)
class Neighbourhood:
    """The k known alloys nearest one formula, nearest first, as the answering deployment sees them.

    Attributes:
        formula: What was asked about, exactly as typed.
        model_version: The artifact version whose deployment answered. The neighbours come from
            its novelty reference, which is a property of the data rather than of the fit, but
            the version is on every body this service returns and a caller must not have to
            know which bodies are exempt.
        metric: ``"ElMD"``, and ``scale`` its ordering -- the same pair a prediction's
            ``novelty`` carries.
        novelty_ceiling: The distance past which the novelty screen refuses. Served so a chart
            can mark it without a second request.
        reference_sha256: The digest of the reference the neighbours were read from; ``None``
            only if the deployment did not record one.
        neighbours: Nearest first. Never empty.
    """

    formula: str
    model_version: str
    metric: str
    scale: str
    novelty_ceiling: float
    reference_sha256: str | None
    neighbours: tuple[KnownAlloy, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "neighbours", tuple(self.neighbours))
        object.__setattr__(
            self, "novelty_ceiling", _number(self.novelty_ceiling, "novelty_ceiling")
        )
        if not self.neighbours:
            raise ContractError(
                "a neighbourhood with no neighbours asserts the composition has no near "
                "chemistry, which is a different claim and not one a lookup can make."
            )
        distances = [alloy.distance for alloy in self.neighbours]
        if distances != sorted(distances):
            raise ContractError("the neighbours are not in order of distance, nearest first.")

    def to_dict(self) -> dict[str, Any]:
        """The body ``GET /v1/neighbours`` serves."""
        return {
            "schema": SCHEMA,
            "formula": self.formula,
            "model_version": self.model_version,
            "basis": BASIS,
            "unit": UNIT,
            "metric": self.metric,
            "scale": self.scale,
            "novelty_ceiling": self.novelty_ceiling,
            "reference_sha256": self.reference_sha256,
            "neighbours": [alloy.to_dict() for alloy in self.neighbours],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> Neighbourhood:
        """Rebuild one from a served body. Raises :class:`ContractError` on anything else."""
        if not isinstance(payload, Mapping):
            raise ContractError(f"a neighbourhood is a JSON object, not {type(payload).__name__}.")
        if payload.get("schema") != SCHEMA:
            raise ContractError(
                f"the body's schema is {payload.get('schema')!r}; this reader knows {SCHEMA!r}."
            )
        if payload.get("basis") != BASIS or payload.get("unit") != UNIT:
            raise ContractError(
                f"the body says its capacities are {payload.get('basis')!r} in "
                f"{payload.get('unit')!r}; a neighbourhood's are {BASIS!r} in {UNIT!r}."
            )
        try:
            return cls(
                formula=str(payload["formula"]),
                model_version=str(payload["model_version"]),
                metric=str(payload["metric"]),
                scale=str(payload["scale"]),
                novelty_ceiling=payload["novelty_ceiling"],
                reference_sha256=(
                    None
                    if payload["reference_sha256"] is None
                    else str(payload["reference_sha256"])
                ),
                neighbours=tuple(
                    KnownAlloy(
                        formula=str(alloy["formula"]),
                        distance=alloy["distance"],
                        measured=tuple(
                            Measured(
                                temperature_k=row["temperature_k"],
                                capacity=row["capacity"],
                                alloy_class=row["alloy_class"],
                            )
                            for row in alloy["measured"]
                        ),
                    )
                    for alloy in payload["neighbours"]
                ),
            )
        except (KeyError, TypeError) as error:
            raise ContractError(f"a neighbourhood body is missing or mistypes {error}.") from error


def _novelty_screen(bundle: ArtifactBundle) -> Any:
    """The running screen whose reference holds known compositions and their measurements."""
    from hydms.delivery.predict import DeliveryError

    for screen in bundle._screens:
        reference: Any = getattr(screen, "reference", None)
        if hasattr(reference, "petti") and hasattr(reference, "measurements"):
            if not reference.measurements:
                raise DeliveryError(
                    f"the {screen.name!r} screen's reference records no measurements, so "
                    f"there is no measured capacity to serve beside a neighbour. Regenerate it "
                    f"with `python -m hydms.screens.novelty --emit`."
                )
            return screen
    raise DeliveryError(
        f"artifact {bundle.version} runs no novelty screen ({', '.join(bundle.screens)}), so "
        f"it has no known chemistry to measure a distance from. A deployment that narrowed "
        f"its screens narrowed this route with them."
    )


def nearest_measured(formula: str, k: int = DEFAULT_K, *, bundle: ArtifactBundle) -> Neighbourhood:
    """The ``k`` known compositions nearest ``formula``, each with its measured rows.

    Args:
        formula: The composition, as typed. Held to :func:`~hydms.delivery.contract.check_formula`,
            the rule ``POST /v1/predict`` applies, so both routes reject the same strings with
            the same sentence.
        k: How many, from 1 to :data:`MAX_K`.
        bundle: The deployment answering.

    Raises:
        ContractError: the formula is blank or not a string, or ``k`` is out of range. The
            caller's error; the transport serves it as an invalid request.
        UnreadableFormula: the formula is a string and not a composition -- an unknown symbol,
            or one the two parsers read differently. Carries the novelty screen's own sentence,
            which is the one a prediction for the same string would be refused with.
        DeliveryError: the deployment runs no novelty screen, or its reference records no
            measurements. Never the caller's fault.
    """
    from hydms.screens.novelty import METRIC, MOD_PETTI, nearest_known

    check_formula(formula)
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= MAX_K:
        raise ContractError(f"k is {k!r}; ask for between 1 and {MAX_K} neighbours.")
    screen = _novelty_screen(bundle)
    reference = screen.reference
    positions, distances, cause = nearest_known(formula, reference, k)
    if cause:
        raise UnreadableFormula(cause)
    return Neighbourhood(
        formula=formula,
        model_version=bundle.version,
        metric=METRIC,
        scale=MOD_PETTI,
        novelty_ceiling=float(reference.ceiling),
        reference_sha256=bundle.reference_digests.get(str(screen.name)),
        neighbours=tuple(
            KnownAlloy(
                formula=reference.formulas[int(position)],
                distance=float(distance),
                measured=tuple(
                    Measured(
                        temperature_k=row.temperature_k,
                        capacity=row.capacity,
                        alloy_class=row.alloy_class,
                    )
                    for row in reference.measurements[int(position)]
                ),
            )
            for position, distance in zip(positions, distances, strict=True)
        ),
    )
