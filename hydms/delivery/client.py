"""L6 -- the prediction service, from the other side of the wire.

The app (card #82) is an **HTTP client** of the service in :mod:`hydms.delivery.api`, not an
in-process caller of :func:`~hydms.delivery.predict.predict_capacity`. That is what keeps one
prediction path under one set of guard rails: HG-3's transport-parity gate covers everything
the page shows, and the page cannot acquire a featuriser, a scaler or a model of its own,
because nothing it imports has one.

**Four outcomes, and a caller can never confuse two of them.**

========================  =====================================  ======================================
What happened             What comes back                        What it means
========================  =====================================  ======================================
answered                  a ``PredictionResult``                 an estimate *with* its band
declined                  a ``Refusal``                          not a low number: no number
could not read the input  an :class:`InvalidRequest`             the caller's error, not the material's
no service                :class:`ServiceUnreachable` is raised  nothing on the page is a prediction
========================  =====================================  ======================================

The first two come back through :func:`~hydms.delivery.contract.answer_from`, the one door back
from JSON that #79's parity gate also uses, so this module never learns what the discriminator
is called. :class:`InvalidRequest` is its own type because the service sends a malformed request and
a refused material with the same ``422`` and nothing else in common (``docs/API.md``); a page
that rendered the one as the other would tell a researcher their alloy was unanswerable when
their formula had a typo.

**A service that answers with something other than the contract is an error, not an outcome.**
A ``500``, a body that is not JSON, or a ``200`` that :func:`answer_from` cannot rebuild raise
:class:`ServiceError`. There is no fallback that renders "something": a page that shows a
half-read payload is how a dropped interval becomes a bare number on screen.

**The neighbours lookup is a fifth call and not a fifth outcome.** ``GET /v1/neighbours``
returns a :class:`~hydms.delivery.neighbours.Neighbourhood` -- measured rows, no prediction -- or
the same :class:`InvalidRequest` a malformed prediction gets. It has no refusal, because nothing
is judged.

It uses :mod:`urllib` rather than an HTTP library. The client makes five kinds of request, all
JSON, all to one host; a dependency would buy nothing it needs, and the `app` extra -- which
CI does not install -- would then be the only thing that made this module importable.

Card #82.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from hydms.delivery.contract import (
    Answer,
    ContractError,
    PredictionRequest,
    answer_from,
)
from hydms.delivery.neighbours import Neighbourhood

__all__ = [
    "DEFAULT_URL",
    "InvalidRequest",
    "ServiceClient",
    "ServiceError",
    "ServiceUnreachable",
]

#: Where ``uvicorn hydms.delivery.api:app --port 8000`` listens, which is the command
#: ``docs/API.md`` gives. The app reads ``HYDMS_API_URL`` in preference to it.
DEFAULT_URL = "http://127.0.0.1:8000"

#: The service's version prefix. A contract change is a new prefix, so a client pinned to
#: this one fails loudly against a service that has moved rather than misreading it.
PREFIX = "/v1"

#: Seconds to wait for one request. A single prediction is well under a second; a batch of
#: the published 256-row limit is measured at about 19 s (``service.MAX_BATCH_ROWS``), so
#: this leaves room for a machine half as fast without hanging a page indefinitely.
TIMEOUT_S = 60.0


class ServiceUnreachable(ConnectionError):
    """Nothing answered at the service's address. Not a refusal, and never rendered as one."""


class ServiceError(RuntimeError):
    """The service answered, but not with anything the delivery contract describes."""


@dataclass(frozen=True)
class InvalidRequest:
    """The service could not read the *request*: an empty formula, a field it does not declare.

    Deliberately not a :class:`~hydms.delivery.contract.Refusal`. A refusal is a statement about
    a material; this is a statement about what was typed, and it carries no ``code`` from the
    screens' vocabulary because no screen ever saw it. Named for ``CONTEXT.md``'s
    *Refusal vs Invalid request*, which is the distinction this type exists to keep.

    Attributes:
        message: The service's one-line summary.
        problems: Each problem's own sentence, in the order the service listed them.
    """

    message: str
    problems: tuple[str, ...]

    @property
    def refused(self) -> bool:
        """``False``: nothing was refused, because nothing was asked about a material."""
        return False


class ServiceClient:
    """The prediction service at one address.

    Args:
        base_url: Scheme, host and port, with no path -- ``http://127.0.0.1:8000``.
        timeout: Seconds to wait for any one request.
    """

    def __init__(self, base_url: str = DEFAULT_URL, *, timeout: float = TIMEOUT_S) -> None:
        url = str(base_url).strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            raise ValueError(
                f"the service address {base_url!r} is not an http(s) URL; the app talks to the "
                f"service over HTTP and nothing else."
            )
        self.base_url = url
        self.timeout = float(timeout)

    # ----------------------------------------------------------------------------------
    # The wire
    # ----------------------------------------------------------------------------------

    def _exchange(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        """One request; the status and the decoded JSON body, whatever the status."""
        url = f"{self.base_url}{PREFIX}{path}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                status, raw = int(response.status), response.read()
        except urllib.error.HTTPError as error:
            # urllib raises for every non-2xx status, and a 422 is an *answer* here.
            status, raw = int(error.code), error.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
            reason = getattr(error, "reason", error)
            raise ServiceUnreachable(
                f"the prediction service at {self.base_url} did not answer ({reason}). "
                f"Nothing on this page is a prediction."
            ) from error
        try:
            return status, json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ServiceError(
                f"{method} {path} answered {status} with a body that is not JSON; the "
                f"delivery contract has no such answer."
            ) from error

    def _outcome(self, status: int, payload: Any, where: str) -> Answer | InvalidRequest:
        """Read one prediction body: an answer, a refusal, or an invalid request."""
        if not isinstance(payload, Mapping):
            raise ServiceError(f"{where} answered {status} with a JSON {type(payload).__name__}.")
        if status == 422 and "refused" not in payload and "error" in payload:
            return _invalid_request(payload)
        if status not in (200, 422):
            raise ServiceError(
                f"{where} answered {status}; the contract answers 200 or 422. "
                f"{payload.get('detail') or payload.get('message') or ''}".strip()
            )
        try:
            answer = answer_from(payload)
        except ContractError as error:
            raise ServiceError(
                f"{where} answered {status} with a body outside the contract: {error}"
            ) from error
        if answer.refused != (status == 422):
            raise ServiceError(
                f"{where} answered {status} with refused={answer.refused}; the status and the "
                f"answer disagree about whether a number was given."
            )
        return answer

    def _get(self, path: str) -> dict[str, Any]:
        status, payload = self._exchange("GET", path)
        if status != 200 or not isinstance(payload, dict):
            raise ServiceError(f"GET {PREFIX}{path} answered {status}.")
        return payload

    # ----------------------------------------------------------------------------------
    # The routes
    # ----------------------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """``GET /v1/health``: which version is answering, and the batch limit."""
        return self._get("/health")

    def model(self) -> dict[str, Any]:
        """``GET /v1/model``: the deployment's own description of itself."""
        return self._get("/model")

    def predict(self, formula: str, temperature_k: float) -> Answer | InvalidRequest:
        """``POST /v1/predict`` for one composition at one temperature."""
        body = {"formula": formula, "temperature_k": temperature_k}
        status, payload = self._exchange("POST", "/predict", body)
        return self._outcome(status, payload, f"POST {PREFIX}/predict")

    def neighbours(self, formula: str, k: int | None = None) -> Neighbourhood | InvalidRequest:
        """``GET /v1/neighbours``: the known alloys nearest ``formula``, with measured capacities.

        Args:
            formula: The composition, as typed.
            k: How many. ``None`` takes the service's default rather than restating it here.
        """
        query: dict[str, object] = {"formula": formula}
        if k is not None:
            query["k"] = int(k)
        path = f"/neighbours?{urllib.parse.urlencode(query)}"
        where = f"GET {PREFIX}/neighbours"
        status, payload = self._exchange("GET", path)
        if not isinstance(payload, Mapping):
            raise ServiceError(f"{where} answered {status} with a JSON {type(payload).__name__}.")
        if status == 422 and "error" in payload:
            return _invalid_request(payload)
        if status != 200:
            raise ServiceError(f"{where} answered {status}; the route answers 200 or 422.")
        try:
            return Neighbourhood.from_dict(payload)
        except ContractError as error:
            raise ServiceError(f"{where} answered a body outside the contract: {error}") from error

    def predict_many(
        self, requests: Iterable[PredictionRequest], *, batch_rows: int | None = None
    ) -> list[Answer] | InvalidRequest:
        """``POST /v1/predict/batch``, in chunks no larger than the service accepts.

        The answers come back in the order the requests were given. A request the service
        rejects rejects the whole call -- the service validates a batch before predicting any
        of it, and a page that showed the rows either side of a malformed one would be showing
        a sweep with a hole in it.

        Args:
            requests: What to ask, in order.
            batch_rows: The chunk size. ``None`` asks ``GET /v1/health`` for the limit, which
                is the service's to set and not this client's to remember.
        """
        asked = list(requests)
        size = int(batch_rows) if batch_rows is not None else int(self.health()["max_batch_rows"])
        if size < 1:
            raise ValueError(f"a batch of {size} row(s) carries nothing.")
        answers: list[Answer] = []
        for start in range(0, len(asked), size):
            chunk = asked[start : start + size]
            body = {"candidates": [request.to_dict() for request in chunk]}
            status, payload = self._exchange("POST", "/predict/batch", body)
            where = f"POST {PREFIX}/predict/batch"
            if status == 422 and isinstance(payload, Mapping) and "error" in payload:
                return _invalid_request(payload)
            if status != 200 or not isinstance(payload, Mapping):
                raise ServiceError(f"{where} answered {status}.")
            rows = payload.get("answers")
            if not isinstance(rows, Sequence) or len(rows) != len(chunk):
                raise ServiceError(
                    f"{where} was sent {len(chunk)} candidate(s) and answered "
                    f"{len(rows) if isinstance(rows, Sequence) else 'no'} row(s); a batch that "
                    f"returns fewer rows than it was given attaches answers to the wrong inputs."
                )
            for row in rows:
                # A row has no status of its own; give it the one a lone request would carry, so
                # `_outcome` refuses a non-object row itself rather than `row.get` raising here.
                refused = isinstance(row, Mapping) and row.get("refused") is True
                outcome = self._outcome(422 if refused else 200, row, where)
                if isinstance(outcome, InvalidRequest):  # pragma: no cover -- a row is never one
                    raise ServiceError(f"{where} answered a row that is not an answer.")
                answers.append(outcome)
        return answers


def _invalid_request(payload: Mapping[str, Any]) -> InvalidRequest:
    problems = payload.get("problems") or ()
    return InvalidRequest(
        message=str(payload.get("message") or "the request could not be read."),
        problems=tuple(
            str(problem.get("message", problem)) if isinstance(problem, Mapping) else str(problem)
            for problem in problems
        ),
    )
