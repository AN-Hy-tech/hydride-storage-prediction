"""The transport's declared shapes: what a caller may send, and what it will get back.

Every model here is a statement in the OpenAPI document that card #79 snapshots and card #80
writes a reference from. None of them is a *rule*: the rules about a request live in
:class:`~hydms.delivery.contract.PredictionRequest` and the rules about an answer live in
:class:`~hydms.delivery.contract.PredictionResult`, and this module is deliberately shallow
over both.

**What the request models declare, and what they refuse to declare.** They declare the JSON
facts only the transport can see -- that the body is an object, that ``formula`` arrives as a
JSON string rather than a number, that an unknown field is an error. They do *not* re-declare
that a formula must be non-empty or a temperature finite, even though pydantic could: those
are the contract's, and a second owner of a rule is how the two come to disagree about which
sentence a caller is shown. So :class:`Candidate` has no ``min_length`` and no
``allow_inf_nan``; ``{"formula": "   "}`` reaches
:class:`~hydms.delivery.contract.PredictionRequest`, raises there, and is served with the
contract's own sentence by the handler in :mod:`hydms.delivery.api.service`.

``extra="forbid"`` is a rule of its own and it is the transport's to make. Card #75 is
explicit that a caller who could choose its own screens, version or confidence level could
widen its own interval until the answer looked good; those are deployment decisions and the
only way to say so at the boundary is to refuse a body that names them. A silently ignored
``"version": "v1"`` would tell a caller it had pinned a version when it had not.

``strict=True`` for the same reason at one remove: in pydantic's lax mode ``"298"`` is
accepted as a temperature, and a client that sends its numbers as strings is a client whose
next release sends ``"two hundred"``. An **integer** is still accepted for a float -- pydantic
allows that widening in strict mode -- so the documented ``{"temperature_k": 298}`` works.

**The response models mirror the contract exactly, and are checked to.** Each carries
``extra="forbid"``, so a field the contract grows and this module does not is a loud failure
rather than a field quietly dropped on its way out -- the one failure mode a response model
introduces, closed by the same mechanism that introduced it.
``tests/delivery/test_api.py`` pins field-for-field equality against
:meth:`~hydms.delivery.contract.PredictionResult.to_dict`, so the check does not depend on
anyone remembering to look.

Card #78.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from hydms.delivery.contract import SCHEMA, SPACE, UNIT
from hydms.delivery.neighbours import SCHEMA as NEIGHBOURS_SCHEMA

__all__ = [
    "Answer",
    "BatchBody",
    "BatchResponse",
    "Candidate",
    "Declined",
    "Health",
    "InvalidRequest",
    "KnownAlloyBody",
    "MeasuredBody",
    "NeighbourhoodBody",
    "PredictionResultBody",
    "Problem",
    "RefusalBody",
    "model_card_schema",
]


class _Body(BaseModel):
    """A request body: exactly the declared fields, in the JSON types they are declared in."""

    model_config = ConfigDict(extra="forbid", strict=True)


class _Payload(BaseModel):
    """A response body: the contract's own keys, and nothing this module invented."""

    # No `populate_by_name`: these models are only ever validated from the contract's own
    # `to_dict()` output, which spells that field `schema`, and nothing constructs one by
    # python field name. One accepted spelling per key is one thing for #80 to document.
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------------------
# What a caller sends
# --------------------------------------------------------------------------------------


class Candidate(_Body):
    """One composition at one temperature -- the whole of what a caller may choose."""

    formula: str = Field(
        description=(
            "The composition, as written. Not normalised by the caller: 'Pr1Co5' and "
            "'Pr1Co5 ' are the same material and the pipeline is what says so."
        ),
        examples=["LaNi5", "La0.8Ce0.2Ni5"],
    )
    temperature_k: float = Field(
        description=(
            "Kelvin. Outside the trained window the answer is a refusal with a reason, "
            "not an error."
        ),
        examples=[298.0],
    )


class BatchBody(_Body):
    """Many candidates in one request. Answers come back in the order they were sent."""

    candidates: list[Candidate] = Field(
        description=(
            "The candidates to answer, in order. The per-request limit is reported by "
            "GET /v1/health as `max_batch_rows`; a longer list is refused whole, because "
            "truncating it would answer a question nobody asked."
        )
    )


# --------------------------------------------------------------------------------------
# What comes back
# --------------------------------------------------------------------------------------


class RequestBody(_Payload):
    """The request an answer carries, so a stored answer says what it answers."""

    formula: str
    temperature_k: float


class IntervalBody(_Payload):
    """The calibrated band, its nominal level, and the width a reader should see."""

    lower: float
    upper: float
    level: float
    width: float
    unit: str = UNIT
    space: str = SPACE


class ScreenVerdictBody(_Payload):
    """One rule's judgement: which rule, whether it passed, its code and its sentence."""

    screen: str
    passed: bool
    code: str
    reason: str


class DomainVerdictBody(_Payload):
    """The applicability verdict every answer carries -- with a reason, never a bare flag."""

    admitted: bool
    code: str
    reason: str
    screens: list[ScreenVerdictBody]


class NoveltyBody(_Payload):
    """How far this composition is from the nearest alloy the model was trained on."""

    distance: float
    nearest: str
    metric: str


class PredictionResultBody(_Payload):
    """An answer with a number in it -- and therefore with an interval and a verdict."""

    contract_schema: str = Field(default=SCHEMA, alias="schema")
    refused: Literal[False]
    request: RequestBody
    capacity: float
    unit: str = UNIT
    space: str = SPACE
    interval: IntervalBody
    domain: DomainVerdictBody
    novelty: NoveltyBody | None
    model_version: str


class RefusalBody(_Payload):
    """An answer with no number in it, and a stated reason for that."""

    contract_schema: str = Field(default=SCHEMA, alias="schema")
    refused: Literal[True]
    request: RequestBody
    code: str
    explanation: str
    model_version: str | None
    screens: list[ScreenVerdictBody]


#: What either prediction route returns. A consumer branches on ``refused`` -- the one
#: boolean the contract exists to make readable -- and the discriminator puts that in the
#: OpenAPI document rather than leaving a client to infer it from which fields are present.
Answer = Annotated[
    PredictionResultBody | RefusalBody,
    Field(discriminator="refused"),
]


class BatchResponse(_Payload):
    """Many answers, positionally matched to the candidates that were sent."""

    contract_schema: str = Field(default=SCHEMA, alias="schema")
    count: int
    answers: list[Answer]


class Health(_Payload):
    """Liveness, and the two facts a caller needs before it trusts anything else."""

    status: Literal["ok"]
    model_version: str = Field(description="The artifact version answering right now.")
    max_batch_rows: int = Field(
        description="The most candidates POST /v1/predict/batch will accept in one request."
    )


class MeasuredBody(_Payload):
    """One training row as it was recorded. No interval, because nothing was estimated."""

    temperature_k: float
    capacity: float
    alloy_class: str


class KnownAlloyBody(_Payload):
    """A training composition near the one asked about, with every row measured on it."""

    formula: str
    distance: float = Field(
        description=(
            "ElMD on the modified-Pettifor scale. 0 means it is the composition asked about."
        )
    )
    measured: list[MeasuredBody] = Field(
        description="Every training row, ascending in temperature."
    )


class NeighbourhoodBody(_Payload):
    """The known alloys nearest a composition. A lookup, not a prediction, and shaped so."""

    neighbours_schema: str = Field(default=NEIGHBOURS_SCHEMA, alias="schema")
    formula: str
    model_version: str
    basis: Literal["measured"] = Field(
        default="measured",
        description="Every capacity here is a recorded training row, never an estimate.",
    )
    unit: str = UNIT
    metric: str
    scale: str
    novelty_ceiling: float = Field(
        description=(
            "The distance past which POST /v1/predict refuses as beyond-known-chemistry."
        )
    )
    reference_sha256: str | None = Field(
        description=(
            "The novelty reference the neighbours were read from, as GET /v1/model reports it."
        )
    )
    neighbours: list[KnownAlloyBody] = Field(description="Nearest first.")


# --------------------------------------------------------------------------------------
# What a malformed request gets
# --------------------------------------------------------------------------------------


class Problem(_Payload):
    """One thing wrong with a request, and where in the request it is."""

    location: list[str | int] = Field(
        description="The path to the offending field, e.g. ['candidates', 3, 'formula']."
    )
    message: str
    kind: str = Field(
        description=(
            "Which layer refused it: a pydantic error type for a JSON-shape problem, or "
            "'contract' when hydms.delivery.contract refused the request it was handed."
        )
    )


class InvalidRequest(_Payload):
    """A request that was not understood. Never an answer, and it says so by its shape.

    It carries no ``refused`` key, so :func:`~hydms.delivery.contract.answer_from` refuses it
    with its own sentence rather than reading it as a prediction. That is the distinction the
    status code alone cannot carry: both this and a refusal are served as 422 -- ``docs/
    PHASE-H-RUNBOOK.md`` fixes the refusal's code and card #78 fixes this one -- and the body
    is what says whether a *material* was declined or a *request* was rejected.
    """

    error: str = Field(description="'invalid_request' or 'batch_too_large'.")
    message: str
    problems: list[Problem]


#: What a 422 from ``POST /v1/predict`` can hold. Two unrelated shapes under one status code,
#: which is the price of the runbook fixing a refusal at 422 and the card fixing a malformed
#: request there too. A consumer tells them apart by one key: ``refused`` on an answer,
#: ``error`` on a rejected request. Documentation only -- neither route returns this type.
Declined = RefusalBody | InvalidRequest


def model_card_schema() -> dict[str, Any]:
    """The OpenAPI schema for ``GET /v1/model``: an object whose keys are not pinned here.

    :func:`~hydms.delivery.modelcard.model_card` reports what the *loaded* deployment holds --
    a screen's own thresholds, under the screen's own name for them -- so its keys depend on
    which screens are running. Declaring them as a fixed model here would either be wrong for
    a narrowed deployment or would have to be widened every time a screen gains a threshold,
    and the payload already carries its own ``schema`` field for a consumer to check.
    """
    return {
        "type": "object",
        "required": ["schema", "version", "features", "interval", "screens", "metrics"],
        "properties": {
            "schema": {"type": "string"},
            "version": {"type": "string"},
            "trained_at": {"type": ["string", "null"]},
            "provenance": {"type": ["object", "null"]},
            "features": {"type": "array", "items": {"type": "string"}},
            "interval": {"type": "object"},
            "screens": {"type": "array", "items": {"type": "object"}},
            "trained_ranges": {"type": "object"},
            "metrics": {"type": "object"},
        },
    }
