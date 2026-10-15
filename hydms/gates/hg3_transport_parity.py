"""HG-3 -- the API's answer equals the library's answer, and the contract cannot move quietly.

``docs/PHASE-H-RUNBOOK.md`` section 4: this gate fails when the API's answer differs from
``predict_capacity()``'s for the same input.

AC-4 checks that known alloys round-trip through the library. It says nothing about the
transport boundary, where a float can be truncated by serialisation, a column reordered by a
dict round trip, and an interval dropped by a response model that forgot a field. This gate
extends AC-4 to the edge of the system, and snapshots the OpenAPI document so a breaking
contract change is a visible diff rather than a surprise for whoever wrote a client.

It covers the Streamlit app too, because the app is an HTTP client rather than an in-process
caller -- which is exactly why it was built that way (#85's ADR).

Four claims, and only one of them needs an artifact
----------------------------------------------------

**The published contract is the committed one.** :mod:`hydms.delivery.api.openapi` builds the
document from the code and compares it to the file committed beside the package. A response
model that loses a field, a route that loses a documented status, a request model that gains
one -- each is a change to what a client reads, and each arrives in a diff nobody reviewed
unless the document is a file. This half runs in a checkout with no artifact on disk, which
makes it the half that can go red on a push.

**The HTTP door is the same door as** :func:`~hydms.delivery.predict.predict_capacity`'s.
The request model declares exactly the fields the contract's own request type declares, and
refuses anything else. Card #78's handoff asked for this to be pinned here: a batch endpoint
that accepted a frame with an alloy-class column would make ``untrusted-family`` reachable at
the request door and oblige :data:`~hydms.gates.hg2_refusal_path.NOT_ALWAYS` to say so. It does
not accept one, and the structural check is what keeps that true -- ``extra="forbid"`` over
exactly ``formula`` and ``temperature_k``, measured rather than remembered.

**Parity, against a real artifact.** Every probe HG-2 sends through the library is sent again
over HTTP, and the served body must equal
:meth:`~hydms.delivery.contract.PredictionResult.to_dict` **value for value** -- so a truncated
float is a failure naming the pointer it was truncated at, not a tolerance. The same probes go
through the batch route in one request, and each row must equal its own single-shot answer,
which is order-preservation and per-row refusal in one comparison. Reusing HG-2's probe set is
deliberate: a second list here would drift from the one whose library behaviour is pinned, and
then "the API agrees with the library" would be established over inputs nobody checked the
library on.

**A refusal and a rejected request are both 422, and the body is the whole difference.** Card
#78 could not put them at different statuses -- the runbook's own acceptance ``curl`` fixes a
refusal at 422 and the card fixes a malformed request there too -- so the split is one key:
``refused`` on an answer, ``error`` on a rejected request, sharing nothing.
:func:`~hydms.delivery.contract.answer_from` must **rebuild** the first and **refuse** the
second, because a client that reads an error body as an answer fails silently, and silence is
what this pair can produce. ``CONTEXT.md`` carries the term.

What this gate does not establish
----------------------------------

That the *deployed* service answers. It exercises the application in-process over ASGI through
:class:`~fastapi.testclient.TestClient`, which serialises and parses real JSON but starts no
socket. A proxy that rewrites a body, a gateway that truncates a float, a reverse proxy's own
timeout -- none of those are here, and none of them are in this repository either.

Owned by card #79.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Final

from hydms.config import Config

from ._artifact import NoCandidate, candidate
from ._core import Gate, GateResult, Speed, Status
from .hg2_refusal_path import NOT_ALWAYS, PROBES, Reachability

__all__ = ["GATE", "REJECTED", "Rejected"]

#: A failure naming every probe is a failure nobody reads to the end.
_MAX_NAMED = 8

#: The batch limit is transport policy and the service reports it at ``GET /v1/health``; this
#: gate reads it from there rather than importing the constant, so a deployment that narrowed
#: it is measured as it runs rather than as it was declared.
_OVER_LIMIT_BY = 1


# --------------------------------------------------------------------------------------
# The probes that exist only at this door
#
# HG-2's PROBES are inputs a *material* can be judged on, and they are reused whole. These are
# the ones that never reach the library at all: a body the contract cannot build a request
# from. They are this gate's alone because `predict_capacity` has no way to be asked them --
# there is no such thing as passing an unknown field to a function with two parameters.
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Rejected:
    """One body the transport must reject, and the envelope it must reject it in.

    Attributes:
        name: The probe's label in the result message.
        why: What it is for. Prose, in the failure message, so a red gate says which guarantee
            moved rather than only which string did.
        route: The path it is sent to.
        body: The JSON body, serialised by the client.
        content: The raw request body, for the two literals a conforming client cannot send.
            ``json.dumps`` serialises with ``allow_nan=False``, so ``NaN`` and ``Infinity``
            reach this door only from a client that emits the non-standard spelling -- rare,
            real, and a 500 from inside the request type if the guard were ever removed.
        error: The ``error`` value the envelope must carry.
    """

    name: str
    why: str
    body: Any = None
    content: str | None = None
    route: str = "/v1/predict"
    error: str = "invalid_request"


def _rejected() -> tuple[Rejected, ...]:
    return (
        Rejected(
            name="an-empty-formula",
            why="the contract's own rule, reached through the transport. The request models "
            "deliberately do not re-declare it (#78), so this is the one check that the "
            "caller is shown the contract's sentence rather than a second opinion",
            body={"formula": "", "temperature_k": 298.0},
        ),
        Rejected(
            name="a-formula-that-is-not-a-string",
            why="a JSON type only the transport can see. `strict=True` is what makes '298' a "
            "rejection rather than a silent coercion, and a client that sends its numbers as "
            "strings is a client whose next release sends 'two hundred'",
            body={"formula": 5, "temperature_k": 298.0},
        ),
        Rejected(
            name="a-missing-temperature",
            why="half a question. It must be rejected as a request rather than defaulted, "
            "because a temperature nobody gave is a number nobody can name afterwards",
            body={"formula": "LaNi5"},
        ),
        Rejected(
            name="a-temperature-that-is-not-finite",
            why="the contract's finiteness guard, reachable only from a client that types the "
            "non-standard literal. Kept rather than replaced by a pydantic constraint, so "
            "this is where it is established that it still answers",
            content='{"formula": "LaNi5", "temperature_k": NaN}',
        ),
        Rejected(
            name="a-caller-choosing-its-own-version",
            why="card #75's rule at the boundary: a caller that could pin a version could ask "
            "the deployment that agrees with it. A silently ignored field would be worse than "
            "a rejection -- it would tell the caller it had pinned something",
            body={"formula": "LaNi5", "temperature_k": 298.0, "version": "v1"},
        ),
        Rejected(
            name="a-caller-choosing-its-own-screens",
            why="the same rule, and the one that matters most: a caller that could name its "
            "screens could turn the applicability domain off and get a number back for a "
            "candidate every rule declines",
            body={"formula": "LaNi5", "temperature_k": 298.0, "screens": []},
        ),
        Rejected(
            name="a-batch-carrying-an-alloy-class",
            why="#78's inherited box, behaviourally. A batch route that accepted a frame with "
            "an alloy-class column would make `untrusted-family` reachable by typing a "
            "request, and HG-2 records that code as one no caller can reach at this door. The "
            "body is refused whole rather than the field ignored",
            route="/v1/predict/batch",
            body={
                "candidates": [
                    {"formula": "LaNi5", "temperature_k": 298.0, "alloy_class": "AB5"}
                ]
            },
        ),
        Rejected(
            name="a-batch-with-one-malformed-row",
            why="the whole request is rejected rather than the readable rows answered, so a "
            "caller never has to guess which rows it got. The location must name the row",
            route="/v1/predict/batch",
            body={
                "candidates": [
                    {"formula": "LaNi5", "temperature_k": 298.0},
                    {"formula": " ", "temperature_k": 298.0},
                ]
            },
        ),
    )


#: The rejected-request probe set: one body per rule the transport owns.
REJECTED: Final = _rejected()


# --------------------------------------------------------------------------------------
# The two claims that need no artifact
# --------------------------------------------------------------------------------------


def _contract_document() -> list[str]:
    """How the committed OpenAPI document differs from the one the code produces."""
    from hydms.delivery.api.openapi import SNAPSHOT_FILE, drift

    try:
        return drift()
    except FileNotFoundError:
        return [
            f"no contract is committed at {SNAPSHOT_FILE}. Write it with `python -m "
            f"hydms.delivery.api.openapi --emit` and commit it -- an uncommitted contract is "
            f"a contract that can change without a diff, which is the whole of what this half "
            f"of the gate checks."
        ]


def _request_door() -> list[str]:
    """The transport declares exactly the contract's request, and refuses everything else."""
    from hydms.delivery.api.schemas import BatchBody, Candidate
    from hydms.delivery.contract import PredictionRequest

    found: list[str] = []
    declared = set(Candidate.model_fields)
    owed = {entry.name for entry in dataclasses.fields(PredictionRequest)}
    if declared != owed:
        extra = ", ".join(sorted(declared - owed)) or "none"
        missing = ", ".join(sorted(owed - declared)) or "none"
        found.append(
            f"the request model declares {sorted(declared)} and PredictionRequest declares "
            f"{sorted(owed)} -- extra at the door: {extra}; missing from it: {missing}. A "
            f"field the HTTP door accepts and the library does not is a second prediction "
            f"path with its own inputs, and `untrusted-family` is the one HG-2 records as "
            f"unreachable here precisely because no such field exists."
        )
    for model in (Candidate, BatchBody):
        if model.model_config.get("extra") != "forbid":
            found.append(
                f"{model.__name__} does not forbid unknown fields, so a body naming its own "
                f"`version` or `screens` is accepted and silently ignored -- which tells a "
                f"caller it pinned a deployment decision when it did not (card #75)."
            )
    return found


# --------------------------------------------------------------------------------------
# The behavioural half
# --------------------------------------------------------------------------------------


def _compare(left: Any, right: Any, *, left_name: str, right_name: str) -> list[str]:
    from hydms.delivery.api.openapi import differences

    return differences(left, right, left_name=left_name, right_name=right_name)


@dataclass(frozen=True)
class Served:
    """What one probe came back with over HTTP, reduced to what this gate asserts about it."""

    name: str
    code: str
    refused: bool
    body: dict[str, Any]
    findings: tuple[str, ...]


def _answer(client: Any, probe: Any, bundle: Any) -> Served:
    """One probe through both paths, compared value for value."""
    from hydms.delivery.contract import ADMITTED, Refusal, answer_from
    from hydms.delivery.predict import predict_capacity

    library = predict_capacity(probe.formula, probe.temperature_k, bundle=bundle)
    expected = library.to_dict()
    refused = isinstance(library, Refusal)
    code = library.code if isinstance(library, Refusal) else ADMITTED

    response = client.post(
        "/v1/predict",
        json={"formula": probe.formula, "temperature_k": probe.temperature_k},
    )
    body = response.json()
    found: list[str] = []

    # Value for value, at full precision. `differences` names the pointer, so a band that
    # arrived narrower than the one that was calibrated reports `/interval/lower` and both
    # numbers rather than "the bodies differ".
    found.extend(_compare(expected, body, left_name="the library", right_name="served"))

    wanted = 422 if refused else 200
    if response.status_code != wanted:
        found.append(
            f"came back as HTTP {response.status_code} where the library "
            f"{'refused' if refused else 'answered'} it, so the status and the body disagree "
            f"about whether there is a number in it"
        )

    # The one door back from JSON. Equality here is stricter than the body comparison above --
    # it is the reconstructed dataclass, so a field that survived serialisation but cannot be
    # read back is a failure a key-by-key diff would pass.
    try:
        rebuilt = answer_from(body)
    except Exception as error:
        found.append(
            f"could not be rebuilt by answer_from(): {type(error).__name__}: {error}. That "
            f"function is the only door back from JSON this project offers a client"
        )
    else:
        if rebuilt != library:
            found.append(
                f"rebuilt into an answer the library does not equal: served {rebuilt!r} "
                f"against {library!r}"
            )

    if refused and "error" in body:
        found.append(
            "carries both `refused` and `error`, so a client cannot tell a declined material "
            "from a rejected request by the one key that separates them"
        )
    if not refused and "error" in body:
        found.append("is an answer carrying an `error` key, which no answer may carry")

    return Served(probe.name, code, refused, body, tuple(found))


def _rejection(client: Any, probe: Rejected) -> tuple[bool, list[str]]:
    """One malformed body, and the envelope it must come back in."""
    from hydms.delivery.contract import ContractError, answer_from

    if probe.content is not None:
        response = client.post(
            probe.route, content=probe.content, headers={"content-type": "application/json"}
        )
    else:
        response = client.post(probe.route, json=probe.body)

    found: list[str] = []
    try:
        body = response.json()
    except ValueError:
        return False, [f"came back with a body that is not JSON: {response.text[:120]!r}"]

    if response.status_code != 422:
        found.append(
            f"came back as HTTP {response.status_code}, not 422. A body the contract cannot "
            f"read is a rejected request, and a 500 would make it the deployment's fault"
        )
    if body.get("error") != probe.error:
        found.append(
            f"carries error={body.get('error')!r} where the envelope declares {probe.error!r}"
        )
    if "refused" in body:
        found.append(
            "carries a `refused` key, so a rejected request is indistinguishable from a "
            "declined material -- which is the pair the status code cannot separate"
        )
    if not body.get("problems"):
        found.append("names nothing that is wrong with it, so a client cannot fix the request")

    # The silent failure this pair can produce: a client reaching for the contract's reader and
    # being handed a half-understood payload instead of being told what it is holding.
    try:
        answer_from(body)
    except ContractError:
        pass
    except Exception as error:
        found.append(
            f"made answer_from() raise {type(error).__name__} rather than a ContractError, so "
            f"a client cannot handle 'this is not an answer' as one case"
        )
    else:
        found.append(
            "was read by answer_from() as an answer. A rejected request rebuilt into a "
            "prediction is the one failure in this pair that is completely silent"
        )
    return not found, found


def _batch(client: Any, singles: Sequence[Served], limit: int) -> list[str]:
    """The same probes in one request: order preserved, and a refused row is not a failure."""
    from hydms.delivery.contract import SCHEMA

    sent = [
        {"formula": probe.formula, "temperature_k": probe.temperature_k} for probe in PROBES
    ]
    response = client.post("/v1/predict/batch", json={"candidates": sent})
    found: list[str] = []
    if response.status_code != 200:
        return [
            f"the batch route answered HTTP {response.status_code} for {len(sent)} candidates "
            f"of which {sum(1 for s in singles if s.refused)} are refused -- a refused row is "
            f"a refusal in the list, not a failed request: {response.text[:200]}"
        ]

    body = response.json()
    if body.get("schema") != SCHEMA:
        found.append(f"the batch response declares schema {body.get('schema')!r}, not {SCHEMA!r}")
    if body.get("count") != len(sent):
        found.append(f"the batch answered count={body.get('count')} for {len(sent)} candidates")

    answers = body.get("answers", [])
    if len(answers) != len(sent):
        return [
            *found,
            f"the batch returned {len(answers)} answers for {len(sent)} candidates, so "
            f"position no longer identifies the candidate a row is about",
        ]

    for position, (row, single) in enumerate(zip(answers, singles, strict=True)):
        found.extend(
            f"row {position} ({single.name}) {line}"
            for line in _compare(
                single.body, row, left_name="served one at a time", right_name="in the batch"
            )
        )

    # The limit is policy, and it is reported by the deployment rather than imported, so a
    # service started with a narrower one is measured at the width it actually runs.
    over = [{"formula": "LaNi5", "temperature_k": 298.0}] * (limit + _OVER_LIMIT_BY)
    refusal = client.post("/v1/predict/batch", json={"candidates": over})
    if refusal.status_code != 422 or refusal.json().get("error") != "batch_too_large":
        found.append(
            f"{len(over)} candidates against a declared limit of {limit} came back as HTTP "
            f"{refusal.status_code} carrying error={refusal.json().get('error')!r}. A limit "
            f"the service publishes at /v1/health and does not enforce is a limit a client "
            f"discovers by timing out"
        )
    return found


def _deployment(client: Any, bundle: Any, answered: Sequence[Served]) -> tuple[int, list[str]]:
    """Which version the transport says is answering, against the one that answered."""
    found: list[str] = []
    health = client.get("/v1/health").json()
    if health.get("model_version") != bundle.version:
        found.append(
            f"/v1/health reports version {health.get('model_version')!r} and the bundle that "
            f"answered is {bundle.version!r}. A number without the version that produced it is "
            f"not evidence (card #83)"
        )
    card = client.get("/v1/model").json()
    if card.get("version") != bundle.version:
        found.append(
            f"/v1/model describes version {card.get('version')!r} while {bundle.version!r} is "
            f"answering, so the deployment's description of itself is of a different model"
        )
    for served in answered:
        if served.body.get("model_version") != bundle.version:
            found.append(
                f"{served.name} came back stamped {served.body.get('model_version')!r} rather "
                f"than {bundle.version!r}"
            )
    limit = health.get("max_batch_rows")
    if not isinstance(limit, int) or limit < 1:
        found.append(
            f"/v1/health reports max_batch_rows={limit!r}, which a client cannot respect. It "
            f"is the one policy a caller must know and there is nowhere else to discover it"
        )
        limit = 0
    return limit, found


def _vocabulary(reached: set[str], declared: set[str]) -> list[str]:
    """Every declared reason code is reachable over HTTP, or its absence is on the record."""
    from hydms.delivery.contract import ADMITTED

    found: list[str] = []
    unexplained = sorted(declared - reached - set(NOT_ALWAYS) - {ADMITTED})
    if unexplained:
        found.append(
            f"{_named(unexplained)} is declared by a screen on the delivery path and no probe "
            f"reaches it over HTTP, and nothing says why. Either the probe set stopped "
            f"covering it, or its reachability now depends on the fit -- in which case say so "
            f"in hydms.gates.hg2_refusal_path.NOT_ALWAYS, which is where the request door's "
            f"record lives and where HG-2 reads it from"
        )
    wrong = sorted(
        code
        for code, (kind, _) in NOT_ALWAYS.items()
        if kind is Reachability.NEVER and code in reached
    )
    if wrong:
        found.append(
            f"{_named(wrong)} became reachable by typing a formula and a temperature at the "
            f"HTTP door, and it is recorded as one no caller can reach there. The transport "
            f"is supplying an input a caller never gave, which is the third door #77's handoff "
            f"warned about and #78 kept shut with `extra=\"forbid\"`"
        )
    return found


# --------------------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------------------


def _lines(items: Sequence[str]) -> str:
    listed = list(items)
    shown = listed[:_MAX_NAMED]
    more = "" if len(listed) <= _MAX_NAMED else f"\n  ... ({len(listed) - _MAX_NAMED} more)"
    return "\n".join(f"  {line}" for line in shown) + more


def _named(codes: Iterable[object]) -> str:
    listed = sorted(str(code) for code in codes)
    if not listed:
        return "none"
    if len(listed) <= _MAX_NAMED:
        return ", ".join(f"`{code}`" for code in listed)
    shown = ", ".join(f"`{code}`" for code in listed[:_MAX_NAMED])
    return f"{shown}, ... ({len(listed) - _MAX_NAMED} more)"


@dataclass(frozen=True)
class TransportParity:
    """The gate. Every number it reports is measured in this call."""

    name: str = "HG-3"
    title: str = "Transport parity: the API's answer equals predict_capacity()'s"
    card: int = 79
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        try:
            from fastapi.testclient import TestClient
        except ImportError as absent:
            # Not a pass and not a silent one: the service is a deliverable of this phase, so
            # an environment that cannot start it has not established transport parity. CI
            # installs the extra for exactly this reason.
            return GateResult.skip(
                self.name,
                f"the prediction service cannot be started here: {absent}. Install the extra "
                f"-- `pip install -e '.[api,dev]'` -- and run this again. Nothing about the "
                f"transport is established until it runs.",
            )

        from hydms.delivery.api import create_app
        from hydms.delivery.api.openapi import SNAPSHOT_FILE

        # The two halves that need no artifact, first, so a contract change is red on a push in
        # a checkout where the behavioural half cannot run at all.
        moved = _contract_document()
        if moved:
            return GateResult.fail(
                self.name,
                f"the published contract is {len(moved)} value(s) away from the code:\n"
                f"{_lines(moved)}\n"
                f"If every line is a change you meant, `python -m hydms.delivery.api.openapi "
                f"--emit` and commit the diff. If any is not, an edit moved what a client "
                f"reads and nothing else would have said so.",
                measured=f"{len(moved)} difference(s) against {SNAPSHOT_FILE.name}",
                threshold="0",
            )
        door = _request_door()
        if door:
            return GateResult.fail(
                self.name,
                f"the HTTP door accepts something predict_capacity() does not:\n{_lines(door)}",
                measured=f"{len(door)} defect(s) at the request door",
                threshold="0",
            )

        try:
            scored = candidate(cfg)
        except NoCandidate as absent:
            return GateResult.skip(
                self.name,
                f"the committed OpenAPI document is what the code produces and the HTTP door "
                f"declares exactly the contract's request -- but no answer was served, so "
                f"parity is not established. {absent}",
            )

        from hydms.delivery.contract import reason_codes
        from hydms.delivery.predict import bundle_from

        bundle = bundle_from(scored.surrogate, cfg=cfg)
        with TestClient(create_app(resolve=lambda: bundle)) as client:
            served = [_answer(client, probe, bundle) for probe in PROBES]
            broken = [
                f"{result.name} {finding}" for result in served for finding in result.findings
            ]
            answered = [result for result in served if not result.refused]
            limit, deployment = _deployment(client, bundle, answered)
            broken.extend(deployment)
            if not broken:
                broken.extend(_batch(client, served, limit))
            rejections = [(probe, _rejection(client, probe)) for probe in REJECTED]

        broken.extend(
            f"{probe.name} ({probe.route}) {finding}"
            for probe, (_, findings) in rejections
            for finding in findings
        )
        if broken:
            return GateResult.fail(
                self.name,
                f"{len(broken)} transport finding(s) against {scored.provenance}:\n"
                f"{_lines(broken)}",
                measured=f"{len(broken)} finding(s) over {len(served)} probe(s) and "
                f"{len(REJECTED)} rejected request(s)",
                threshold="0",
            )

        declared = set(reason_codes())
        reached = {result.code for result in served}
        vocabulary = _vocabulary(reached, declared)
        if vocabulary:
            return GateResult.fail(
                self.name,
                f"the API serves a different reason vocabulary than the screens "
                f"declare:\n{_lines(vocabulary)}",
                measured=f"{len(reached)} of {len(declared)} code(s) over HTTP",
                threshold="every declared code reachable over HTTP, or its absence stated",
            )

        never = sorted(
            code for code, (kind, _) in NOT_ALWAYS.items() if kind is Reachability.NEVER
        )
        from hydms.delivery.contract import ADMITTED

        quiet = sorted(declared - reached - {ADMITTED} - set(never))
        return GateResult(
            self.name,
            Status.PASSED,
            f"going over HTTP does not change the answer. {len(served)} probe(s) against "
            f"{scored.provenance} were served and compared to predict_capacity() value for "
            f"value at full precision -- {len(answered)} answered with an interval, a verdict "
            f"and a version, {len(served) - len(answered)} refused with a code and a sentence "
            f"and no number -- and every body rebuilt through answer_from() into an object "
            f"equal to the library's. The same {len(served)} in one batch came back in order, "
            f"each row equal to its own single-shot answer, and {limit + _OVER_LIMIT_BY} "
            f"candidates against the published limit of {limit} were refused whole. "
            f"{len(REJECTED)} malformed request(s) came back as 422 carrying `error` and no "
            f"`refused`, and answer_from() refused every one of them rather than reading it as "
            f"a prediction. The committed contract at {SNAPSHOT_FILE.name} is what the code "
            f"produces, and the door declares exactly the contract's two fields. Codes over "
            f"HTTP: {_named(reached)}; {_named(never)} has no input at this door and must stay "
            f"unreachable; {_named(quiet) if quiet else 'nothing else'} went unreached on this "
            f"fit, which NOT_ALWAYS records as the fit's to decide.",
            measured=f"0 differences over {len(served)} probe(s), {len(REJECTED)} rejection(s)",
            threshold="every served value equal to the library's; the contract committed",
        )


GATE: Gate = TransportParity()
