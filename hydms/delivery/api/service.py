"""The HTTP boundary: transport, validation, error shape, and which version answered.

Seven routes, and not one of them computes anything. ``POST /v1/predict`` builds the contract's
own request type, hands it to :func:`~hydms.delivery.predict.predict_capacity`, and serialises
what comes back; ``POST /v1/predict/batch`` hands the whole list to
:func:`~hydms.delivery.predict.predict_many` in one call (card #84); ``GET /v1/health`` reports the

loaded version; ``GET /v1/model`` returns :func:`~hydms.delivery.modelcard.model_card`;
``GET /v1/neighbours`` returns :func:`~hydms.delivery.neighbours.nearest_measured` -- the known
alloys nearest a composition, with what was *measured* on them, which is a lookup and not a
prediction (card #82); and ``GET /v1/evidence`` and ``GET /v1/evidence/parity`` serve what
:func:`hydms.evidence.reader.read` found in the committed tables at startup (card #83, ADR
0007). A
handler that reached into the model would be the shallow design stage S6 exists to avoid, and
it is how the app and the API start disagreeing -- so ``tests/delivery/test_api.py`` parses
every module in this package and fails on an import of the surrogate, the descriptors, the
screens or an array library.

**Why the app talks to the library instead of the app being the library.** The Streamlit pages
(#82-#84) are HTTP clients of this service rather than in-process callers, so that one
prediction path exists and gate HG-3 covers the interface too. An in-process Streamlit call
would give the app a private path no contract test sees. The full argument is #85's ADR.

The one loaded thing
--------------------

The evidence is read **once** too, in the same lifespan, so the scores the model-card page shows
and the per-family transfer scores the refusals quote come from one moment. Unlike the bundle,
missing evidence does not stop the service: a prediction does not depend on it, and the reader
serves each absence as a score with its reason rather than raising (ADR 0007).

The bundle is resolved **once**, at startup, in the lifespan. If it cannot be resolved the
lifespan raises and the server does not start -- there is no lazy load in a request path, no
default version and no unversioned fallback, because a service that answers from "whatever was
lying around" cannot say what a number came from, and every answer this project serves carries
its version for exactly that reason. The failure a caller sees in that case is no answer at
all, which is the honest one.

Two status codes, and the body is what separates them
------------------------------------------------------

``docs/PHASE-H-RUNBOOK.md`` fixes a refusal at **422**, and card #78 fixes a malformed request
at 422 as well. They are therefore told apart by their bodies, not their codes, and the split
is exactly the one the contract already makes:

``{"refused": true, ...}``
    A *material* was declined, with a code from the screens' declared vocabulary and a
    sentence naming the rule. :func:`~hydms.delivery.contract.answer_from` reads it.

``{"error": "invalid_request", ...}``
    A *request* was rejected -- a missing field, a formula that is not a string, a temperature
    that is not finite, an unknown key, a batch over the limit. It carries no ``refused`` key
    at all, so a consumer that tries to read it as an answer is told so by the contract rather
    than quietly handed a refusal it never received.

A 200 is always an answer with a number in it. A 500 is always the deployment's fault and
never a statement about a candidate -- :class:`~hydms.delivery.predict.DeliveryError` is the
type for that, and it is deliberately not mapped to a 4xx.

Card #78.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from hydms.delivery.contract import SCHEMA, ContractError, PredictionRequest
from hydms.delivery.modelcard import model_card
from hydms.delivery.neighbours import DEFAULT_K, MAX_K, UnreadableFormula, nearest_measured
from hydms.delivery.predict import (
    ArtifactBundle,
    DeliveryError,
    load_bundle,
    predict_capacity,
    predict_many,
)
from hydms.evidence.reader import Evidence
from hydms.evidence.reader import read as read_evidence

from .schemas import (
    Answer,
    BatchBody,
    BatchResponse,
    Candidate,
    Declined,
    EvidenceBody,
    Health,
    InvalidRequest,
    NeighbourhoodBody,
    ParityBody,
    Problem,
    model_card_schema,
)

__all__ = ["MAX_BATCH_ROWS", "create_app"]

#: The most candidates one batch request may carry.
#:
#: Measured, not chosen, and measured twice. Until card #84 every candidate went through
#: :func:`~hydms.delivery.predict.predict_capacity` as its own one-row frame, at 66-78 ms a row
#: against ``v2`` (13 ms featurise, 22 ms surrogate, 34 ms screens, all of it per-call pandas
#: overhead), so the limit was 256 rows: about 19 s, and 38 s on a machine half as fast, inside
#: the 60 s timeout most clients and proxies default to.
#:
#: The route now makes one :func:`~hydms.delivery.predict.predict_many` call per request, and
#: re-measured end to end (``TestClient``, ``v3``, the curated corpus repeated, 2026-09-26, the
#: development machine: 20 logical CPUs) a request costs **0.27 s at 256 rows, 1.00 s at 1,024,
#: 3.05 s at 4,096 and 5.64 s at 8,192** -- 0.7-1.0 ms a row. Time has stopped being the
#: binding constraint; the **response** has not: an answer serialises to about 1.1 KB, so
#: 4,096 rows is a 4.5 MB body. 4,096 is 3 s here and so about 6 s at half speed -- a tenth of
#: the timeout budget, left deliberately, because a busy server is slower than an idle one --
#: and a client with more rows chunks (:meth:`~hydms.delivery.client.ServiceClient.predict_many`
#: does, reading this number from ``GET /v1/health``).
#:

#: It is a module constant with a ``create_app`` override rather than a configuration key
#: because it is transport policy -- how much work one HTTP request may do -- and not a
#: threshold the pipeline reads. Nothing below this layer knows or should know it.
MAX_BATCH_ROWS = 4096

#: The path prefix every route lives under. Versioned so that a contract change is a new
#: prefix rather than a surprise for whoever wrote a client.
PREFIX = "/v1"

_TITLE = "HydMS prediction service"
_DESCRIPTION = (
    "Maximum gravimetric hydrogen-storage capacity for one composition at one temperature, "
    "with a calibrated interval and an applicability verdict. Every answer carries the "
    "artifact version that produced it; a candidate the screens decline comes back as a "
    "structured refusal with a reason and no number, never as a bare estimate."
)


# --------------------------------------------------------------------------------------
# The loaded deployment
# --------------------------------------------------------------------------------------


def _bundle(request: Request) -> ArtifactBundle:
    """The one bundle this process answers from, resolved at startup.

    Raises:
        DeliveryError: the application is serving without a completed startup. It is a 500
            rather than a refusal on purpose: no candidate was judged, so there is nothing to
            refuse, and the alternative -- loading a bundle here -- is the silent fallback the
            card forbids.
    """
    loaded: ArtifactBundle | None = getattr(request.app.state, "bundle", None)
    if loaded is None:
        raise DeliveryError(
            "the service is answering requests with no artifact bundle loaded, which means "
            "its startup did not complete. Nothing is loaded on demand here: a version "
            "resolved per request is a version nobody can name afterwards."
        )
    return loaded


#: The dependency, spelled once. ``Annotated`` rather than a ``Depends`` default because a
#: call in a default argument is evaluated at import and shared across every request -- here
#: it is harmless and FastAPI's own idiom, but the rule that catches it is worth keeping.
Bundle = Annotated[ArtifactBundle, Depends(_bundle)]


def _evidence(request: Request) -> Evidence:
    """The evidence this process read at startup. A 500 without it, for :func:`_bundle`'s reason."""
    loaded: Evidence | None = getattr(request.app.state, "evidence", None)
    if loaded is None:
        raise DeliveryError(
            "the service is answering with no evidence read, which means its startup did not "
            "complete. Evidence read per request could disagree with the refusals beside it."
        )
    return loaded


EvidenceRead = Annotated[Evidence, Depends(_evidence)]


def _lifespan(
    resolve: Callable[[], ArtifactBundle], evidence: Callable[[], Evidence]
) -> Any:
    """Load the bundle and read the evidence before the first request.

    The bundle refuses to start the service if it cannot be resolved. The evidence never does:
    the reader returns each absence as a score with its reason.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        # Deliberately unguarded. `load_bundle` already says what is wrong and what to do
        # about it -- nothing promoted, no such version, gates unestablished -- and wrapping
        # those sentences in a vaguer one of our own would cost an operator the fix.
        app.state.bundle = resolve()
        app.state.evidence = evidence()
        yield
        app.state.bundle = None
        app.state.evidence = None

    return lifespan


# --------------------------------------------------------------------------------------
# Refusing a request
# --------------------------------------------------------------------------------------


def _invalid(message: str, problems: list[Problem], *, error: str = "invalid_request") -> JSONResponse:
    """The one 422 body a malformed request gets, whoever noticed it was malformed."""
    return JSONResponse(
        status_code=422,
        content=InvalidRequest(
            error=error, message=message, problems=problems
        ).model_dump(by_alias=True),
    )


def _contract_problem(error: ContractError, location: list[str | int]) -> Problem:
    """A contract refusal of a *request*, in the same shape pydantic's errors arrive in."""
    return Problem(location=location, message=str(error), kind="contract")


def _requests(
    candidates: list[Candidate], *, location: Callable[[int], list[str | int]]
) -> tuple[list[PredictionRequest], list[Problem]]:
    """Build every request first, collecting every problem rather than stopping at the first.

    Two reasons it happens before any prediction runs. A batch whose fortieth row is malformed
    should not cost the caller thirty-nine predictions it will not receive; and a client
    fixing an upload wants the whole list of what is wrong with it, not one line per attempt.

    The transport builds the contract's own type rather than re-stating its rules, then throws
    the objects away and lets :func:`~hydms.delivery.predict.predict_capacity` build its own.
    A library may not assume its caller validated anything, and the two constructions cannot
    disagree because they are the same constructor.

    The returned list is aligned with ``candidates`` **only when no problem was found** -- a
    candidate that raised contributes nothing to it. Both callers refuse the request before
    reading it, which is the only correct use; a caller that predicted from it anyway would be
    answering the wrong rows.

    ``location`` says *where* in the request the offending candidate was, never *which field*
    of it. The contract's sentences name the field in words -- "the formula is empty",
    "temperature_k must be finite" -- but :class:`~hydms.delivery.contract.ContractError`
    carries no field, and recovering one by reading the sentence is how a message written for
    one defect ends up attached to another (``docs/QA-PROTOCOL.md`` section 4.8).
    """
    built: list[PredictionRequest] = []
    problems: list[Problem] = []
    for position, candidate in enumerate(candidates):
        try:
            built.append(
                PredictionRequest(
                    formula=candidate.formula, temperature_k=candidate.temperature_k
                )
            )
        except ContractError as error:
            problems.append(_contract_problem(error, location(position)))
    return built, problems


def _validation_handler(request: Request, error: Exception) -> Response:
    """Pydantic's account of a malformed body, in this service's own envelope.

    FastAPI's default is ``{"detail": [...]}``, which is a fine shape and the wrong one here:
    a client would have to parse two error vocabularies, one for the errors pydantic caught
    and one for the errors the contract caught, and would eventually handle only whichever it
    met first.
    """
    assert isinstance(error, RequestValidationError)
    # The only route with a query string is the neighbours lookup, and a sentence calling its
    # query "a prediction request" would describe the caller's mistake with the wrong noun.
    if any(entry["loc"] and entry["loc"][0] == "query" for entry in error.errors()):
        message = "the query is not a valid neighbours request."
    else:
        message = "the request body is not a valid prediction request."
    problems = [
        Problem(
            location=[part if isinstance(part, int) else str(part) for part in entry["loc"]],
            message=str(entry["msg"]),
            kind=str(entry["type"]),
        )
        for entry in error.errors()
    ]
    return _invalid(message, problems)


# --------------------------------------------------------------------------------------
# The routes
# --------------------------------------------------------------------------------------


def _router(max_batch_rows: int) -> APIRouter:
    router = APIRouter(prefix=PREFIX)

    @router.post(
        "/predict",
        response_model=Answer,
        summary="Predict one composition's capacity at one temperature",
        responses={
            # The 200 entry carries no `model` of its own, though only a result can arrive
            # there: naming one makes FastAPI publish `PredictionResultBody` a second time
            # under a validation-shaped `-Input` name, and a response documented as an input
            # is a worse thing for a client to read than a union with one arm it never sees.
            # The description says which arm that is.
            200: {
                "description": (
                    "An answer: an estimate, its interval and a domain verdict. **Only ever "
                    "an answer** -- a refusal is served as 422 and never here, so of the two "
                    "shapes below only the first arrives with this status."
                )
            },
            422: {
                "model": Declined,
                "description": (
                    "Either a refusal -- a material this deployment declines to answer "
                    "about, carrying `refused: true`, a code and a reason -- or an invalid "
                    "request, carrying `error`. Never a number."
                ),
            },
        },
    )
    def predict(
        body: Candidate,
        response: Response,
        bundle: Bundle,
    ) -> Any:
        built, problems = _requests([body], location=lambda _: ["body"])
        if problems:
            return _invalid(
                "the request names a composition or a temperature this system cannot read.",
                problems,
            )
        answer = predict_capacity(
            built[0].formula, built[0].temperature_k, bundle=bundle
        )
        # 422 for a refusal, fixed by the runbook's own acceptance check. The status says
        # "there is no number in this body"; the body says why.
        response.status_code = 422 if answer.refused else 200
        return answer.to_dict()

    @router.post(
        "/predict/batch",
        response_model=BatchResponse,
        summary="Predict many compositions in one request",
        responses={
            200: {
                "description": (
                    "One answer per candidate, in the order they were sent. A refused row is "
                    "a refusal in the list, not a failed request: the request succeeded, and "
                    "each row says for itself whether it carries a number."
                )
            },
            422: {
                "model": InvalidRequest,
                "description": (
                    "The request was rejected whole -- a malformed row, or more rows than "
                    "`max_batch_rows`."
                ),
            },
        },
    )
    def predict_batch(
        body: BatchBody,
        bundle: Bundle,
    ) -> Any:
        if len(body.candidates) > max_batch_rows:
            return _invalid(
                f"this request carries {len(body.candidates)} candidates and the limit is "
                f"{max_batch_rows}. Split it into requests of at most {max_batch_rows}: the "
                f"limit bounds how long one request runs and how large its answer is, and a "
                f"client that chunks gets the same answers row for row.",

                [Problem(location=["candidates"], message="too many candidates", kind="limit")],
                error="batch_too_large",
            )
        built, problems = _requests(
            body.candidates, location=lambda position: ["candidates", position]
        )
        if problems:
            return _invalid(
                "one or more candidates name a composition or a temperature this system "
                "cannot read. No prediction was run: the whole request is rejected so that "
                "a caller never has to guess which rows were answered.",
                problems,
            )
        # One call for the whole list (card #84): featurised, predicted and screened once, and
        # each answer is exactly what `/predict` would have said about that row alone.
        answers = [answer.to_dict() for answer in predict_many(built, bundle=bundle)]
        return {"schema": SCHEMA, "count": len(answers), "answers": answers}

    @router.get(
        "/health",
        response_model=Health,
        summary="Liveness, and which artifact version is answering",
    )
    def health(bundle: Bundle, evidence: EvidenceRead) -> Any:
        # Liveness alone would be a check that passes while the service answers from a model
        # nobody meant to deploy. The version is the half that makes it worth reading, and
        # the batch limit is here because it is the one policy a client must respect and
        # there is nowhere else a client can discover it at runtime. The evidence digest is
        # how a service still serving yesterday's tables shows it (ADR 0007).
        return {
            "status": "ok",
            "model_version": bundle.version,
            "max_batch_rows": max_batch_rows,
            "evidence_sha256": evidence.digest,
        }

    @router.get(
        "/model",
        summary="The model card: version, training date, what has been certified, and ranges",
        responses={
            200: {
                "description": "The deployment's own description of itself.",
                "content": {"application/json": {"schema": model_card_schema()}},
            }
        },
    )
    def model(bundle: Bundle) -> Any:
        return model_card(bundle)

    @router.get(
        "/evidence",
        response_model=EvidenceBody,
        summary="Every committed score: procedure, artifact and transfer, each with its run",
        responses={
            200: {
                "description": (
                    "The three readings of the model, read from the committed tables once at "
                    "startup (ADR 0007). A score whose table or run record is missing, or whose "
                    "record says `probe`, is served with `value` null and `absent_because` "
                    "saying which. It is never omitted. A present score carries an `interval` "
                    "or `no_interval_because`, exactly one."
                )
            }
        },
    )
    def evidence(read: EvidenceRead) -> Any:
        return read.to_dict()

    @router.get(
        "/evidence/parity",
        response_model=ParityBody,
        summary="The scored rows behind the procedure and transfer scores, for a parity plot",
        responses={
            200: {
                "description": (
                    "Every out-of-fold row of the random-split run and of the "
                    "leave-one-alloy-class-out run: the measurement, the median head and the "
                    "raw 10-90 band. **Predictions scored against measurements, not new "
                    "predictions.** A reading whose run is not a result is served with no rows "
                    "and `absent_because`."
                )
            }
        },
    )
    def parity(read: EvidenceRead) -> Any:
        return read.parity_dict()

    @router.get(
        "/neighbours",
        response_model=NeighbourhoodBody,
        summary="The known alloys nearest a composition, with their measured capacities",
        responses={
            200: {
                "description": (
                    "The k training compositions nearest the formula on the ElMD scale, nearest "
                    "first, each with every row measured on it. **Measured values, not "
                    "predictions**: there is no interval because nothing was estimated. The "
                    "first neighbour is the `novelty.nearest` a prediction for the same "
                    "formula names."
                )
            },
            422: {
                "model": InvalidRequest,
                "description": (
                    "The query was rejected: no formula, a blank one, one that is not a "
                    "composition, or `k` out of range. Never a refusal: nothing was judged."
                ),
            },
        },
    )
    def neighbours(
        bundle: Bundle,
        formula: Annotated[
            str, Query(description="The composition, as written.", examples=["LaNi5"])
        ],
        k: Annotated[
            int, Query(ge=1, le=MAX_K, description="How many neighbours, nearest first.")
        ] = DEFAULT_K,
    ) -> Any:
        try:
            found = nearest_measured(formula, k, bundle=bundle)
        except ContractError as error:
            return _invalid(
                "the query names no composition to look up.",
                [_contract_problem(error, ["query", "formula"])],
            )
        except UnreadableFormula as error:
            # The novelty screen's own sentence, so the lookup and a prediction for the same
            # string say the same thing about why it is not a composition.
            return _invalid(
                "the formula is not a composition this system can place on the ElMD scale.",
                [Problem(location=["query", "formula"], message=str(error), kind="composition")],
            )
        return found.to_dict()

    return router


def create_app(
    *,
    resolve: Callable[[], ArtifactBundle] | None = None,
    evidence: Callable[[], Evidence] | None = None,
    max_batch_rows: int = MAX_BATCH_ROWS,
) -> FastAPI:
    """Build the application. Nothing is loaded until it starts.

    Args:
        resolve: How to obtain the bundle at startup. Defaults to
            :func:`~hydms.delivery.predict.load_bundle`, which resolves the **promoted**
            version. It is a parameter so that a test can start the service over a temporary
            store, and for no other reason -- in particular it is not a way for a request to
            choose a version, which card #75 forbids and the request schema refuses.
        evidence: How to read the evidence at startup. Defaults to
            :func:`hydms.evidence.reader.read` over the repository's committed tables. A
            parameter so a test can serve damaged evidence, and for no other reason.
        max_batch_rows: The batch limit. See :data:`MAX_BATCH_ROWS` for where the number
            comes from.

    Returns:
        A :class:`~fastapi.FastAPI` whose startup resolves one bundle and whose shutdown drops
        it. Importing this module, or calling this function, touches no artifact: ``app`` at
        the package root is built at import time and must stay cheap, because
        ``uvicorn hydms.delivery.api:app`` imports it before it can report anything usefully.
    """
    if max_batch_rows < 1:
        raise DeliveryError(
            f"max_batch_rows is {max_batch_rows}; a batch endpoint that accepts no rows is "
            f"a route that can only fail."
        )
    application = FastAPI(
        title=_TITLE,
        description=_DESCRIPTION,
        version=SCHEMA,
        lifespan=_lifespan(
            resolve if resolve is not None else load_bundle,
            evidence if evidence is not None else read_evidence,
        ),
    )
    application.add_exception_handler(RequestValidationError, _validation_handler)
    application.include_router(_router(max_batch_rows))
    generated = application.openapi
    application.openapi = lambda: _json_discriminator_keys(generated())  # type: ignore[method-assign,unused-ignore]
    return application


#: How pydantic before 2.14 spells a boolean discriminator value in ``mapping``, and how JSON
#: spells it. A client matches the key against the ``refused`` it received, which is JSON
#: ``true``; ``"True"`` is Python's ``str(True)`` leaking into the contract.
_BOOLEAN_KEYS = {"True": "true", "False": "false"}


def _json_discriminator_keys(node: Any) -> Any:
    """Rewrite every boolean ``discriminator.mapping`` key to its JSON spelling, in place.

    Pydantic 2.14 changed ``"True"`` to ``"true"``, so without this the document -- and the
    committed snapshot gate HG-3 compares it to -- depended on which pydantic was installed:
    the pinned environment and an unpinned CI lane disagreed on eight bytes (card #108).
    Owning the spelling here makes the contract a function of the code alone. Idempotent:
    FastAPI caches the document, and a second pass finds nothing left to rewrite.

    Raises:
        DeliveryError: a mapping holds both spellings of one value, which this rewrite would
            silently merge.
    """
    if isinstance(node, dict):
        mapping = node.get("discriminator", {}).get("mapping")
        if isinstance(mapping, dict):
            for python, json_ in _BOOLEAN_KEYS.items():
                if python in mapping:
                    if json_ in mapping:
                        raise DeliveryError(
                            f"a discriminator mapping holds both {python!r} and {json_!r}; "
                            f"they are one JSON value and only one target can be published."
                        )
                    mapping[json_] = mapping.pop(python)
        for value in node.values():
            _json_discriminator_keys(value)
    elif isinstance(node, list):
        for value in node:
            _json_discriminator_keys(value)
    return node

