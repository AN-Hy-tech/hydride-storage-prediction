"""Card #79 -- transport parity, and the eight ways it has to go red.

``docs/QA-PROTOCOL.md`` section 5 will not trust a gate that has never failed, and this one
would be easy to write as decoration: the API and the library agree trivially while the API is
a thin wrapper, so a check that never fails looks exactly like a check that works. Every branch
that can fail is therefore made to fail here, on purpose, and the stages are the real defects
rather than stand-ins -- a float rounded on its way out, a discriminator that appears on both
shapes, rows reordered in a batch, a version the deployment misreports.

**Two halves, and the first one is red without any artifact at all.** The committed OpenAPI
document and the request model's declared fields are facts about the code, so they fail in a
checkout with nothing on disk -- which is the half CI can run, since ``.gitignore`` excludes
``/artifacts/``. The parity half needs a version and skips honestly when there is none.

**A skip is not a pass, twice over.** With no artifact the gate skips rather than reporting the
contract half as a pass; and in an environment with no ``api`` extra it skips rather than
quietly establishing nothing, because a service that cannot start has not been shown to agree
with anything.

**The stage that matters most is the silent one.** A rejected request that carries ``refused``
is indistinguishable from a declined material, and a client branching on that key reads one as
the other with no error anywhere. That is staged by giving the error envelope the key, and the
gate is required to name it.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")
pytest.importorskip("fastapi", reason="the `api` extra: pip install -e '.[api]'")
pytest.importorskip("httpx", reason="the FastAPI TestClient transport; the `dev` extra")
pytest.importorskip(
    "ElMD",
    reason="the `novelty` extra; ElMD is on the prediction path, so CI installs it",
)

from hydms.config import Config, load  # noqa: E402
from hydms.delivery import contract as _contract  # noqa: E402
from hydms.delivery import predict as _delivery  # noqa: E402
from hydms.delivery.api import openapi as _openapi  # noqa: E402
from hydms.delivery.api import schemas as _schemas  # noqa: E402
from hydms.delivery.api import service as _service  # noqa: E402
from hydms.delivery.contract import SCHEMA  # noqa: E402
from hydms.gates import Speed, Status, registry, select  # noqa: E402
from hydms.gates import hg3_transport_parity as hg3  # noqa: E402
from hydms.gates._artifact import NoCandidate  # noqa: E402
from hydms.gates.hg2_refusal_path import NOT_ALWAYS, PROBES, Reachability  # noqa: E402
from hydms.gates.hg3_transport_parity import GATE, REJECTED  # noqa: E402
from hydms.screens.window import OUTSIDE_WINDOW  # noqa: E402
from pydantic import BaseModel, ConfigDict  # noqa: E402

pytestmark = pytest.mark.gate


@pytest.fixture
def served(deployed, pointed_at) -> Config:
    """A configuration pointed at one real, cheap, ungated artifact version."""
    cfg, settings, _frame, _split, fit = deployed
    return pointed_at(fit, cfg, settings)


@pytest.fixture(autouse=True)
def _forget_bundles():
    """The delivery layer caches by ``(store, version)``; every test here writes a new store."""
    _delivery.clear_cache()
    yield
    _delivery.clear_cache()


# --------------------------------------------------------------------------------------
# It passes, and says what it established
# --------------------------------------------------------------------------------------


def test_it_passes_over_a_real_artifact(served: Config) -> None:
    result = GATE.check(served)

    assert result.status is Status.PASSED, result.message
    assert result.name == "HG-3"


def test_the_message_names_the_version_that_answered_and_what_was_compared(
    served: Config,
) -> None:
    """A gate result that does not say *of what* is not evidence (the AC-3 convention)."""
    result = GATE.check(served)

    assert "nothing is promoted yet" in result.message
    assert "value for value at full precision" in result.message
    assert f"{len(PROBES)} probe(s)" in result.message
    assert f"{len(REJECTED)} malformed request(s)" in result.message


def test_it_is_registered_as_hg_3_in_the_fast_lane() -> None:
    """The card's last box. A gate nothing selects is a gate nothing runs."""
    (found,) = select(["HG-3"])

    assert found is GATE
    assert found.card == 79
    assert found.speed is Speed.FAST
    assert GATE in registry()


def test_every_rejected_probe_declares_what_it_is_for() -> None:
    """A probe with no stated purpose cannot fail; it can only be re-labelled (card #90)."""
    for probe in REJECTED:
        assert probe.why.strip(), probe.name
        assert (probe.body is None) != (probe.content is None), probe.name


# --------------------------------------------------------------------------------------
# The contract half: red with no artifact in sight
# --------------------------------------------------------------------------------------


def _refuse_to_look(monkeypatch) -> None:
    monkeypatch.setattr(
        hg3, "candidate", lambda cfg: pytest.fail("looked for an artifact first")
    )


def test_a_document_that_no_longer_matches_the_code_is_red(monkeypatch, tmp_path: Path) -> None:
    """The snapshot's whole purpose: an edit that moves what a client reads, in a diff."""
    stale = _openapi.document()
    stale["paths"]["/v1/predict"]["post"]["summary"] = "Predict, probably"
    snapshot = tmp_path / "openapi.json"
    snapshot.write_text(_openapi.serialise(stale), encoding="utf-8")
    monkeypatch.setattr(_openapi, "SNAPSHOT_FILE", snapshot)
    _refuse_to_look(monkeypatch)

    result = GATE.check(load())

    assert result.status is Status.FAILED, result.message
    assert "/paths/~1v1~1predict/post/summary" in result.message
    assert "Predict, probably" in result.message
    assert "--emit" in result.message


def test_an_uncommitted_contract_is_red_rather_than_absent(monkeypatch, tmp_path: Path) -> None:
    """A contract nobody committed cannot change in a diff, which is the failure itself."""
    monkeypatch.setattr(_openapi, "SNAPSHOT_FILE", tmp_path / "nothing.json")
    _refuse_to_look(monkeypatch)

    result = GATE.check(load())

    assert result.status is Status.FAILED, result.message
    assert "no contract is committed" in result.message


def test_the_committed_contract_is_current() -> None:
    """The state the repository is supposed to be in, asserted rather than assumed."""
    assert _openapi.drift() == []


class _WithAVersion(BaseModel):
    """A request model that lets a caller pin the deployment that answers it (card #75)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    formula: str
    temperature_k: float
    version: str = "v1"


class _ThatIgnoresTheRest(BaseModel):
    """A request model that accepts `screens` and silently drops it."""

    model_config = ConfigDict(extra="ignore", strict=True)

    formula: str
    temperature_k: float


def test_a_field_the_library_does_not_have_is_red_at_the_door(monkeypatch) -> None:
    """#78's inherited box: the HTTP door accepts nothing `predict_capacity()` does not."""
    monkeypatch.setattr(_schemas, "Candidate", _WithAVersion)
    _refuse_to_look(monkeypatch)

    result = GATE.check(load())

    assert result.status is Status.FAILED, result.message
    assert "version" in result.message
    assert "second prediction path" in result.message


def test_a_door_that_ignores_unknown_fields_is_red(monkeypatch) -> None:
    """A silently ignored `screens` tells a caller it narrowed a deployment when it did not."""
    monkeypatch.setattr(_schemas, "Candidate", _ThatIgnoresTheRest)
    _refuse_to_look(monkeypatch)

    result = GATE.check(load())

    assert result.status is Status.FAILED, result.message
    assert "does not forbid unknown fields" in result.message


# --------------------------------------------------------------------------------------
# A skip is not a pass
# --------------------------------------------------------------------------------------


def test_with_no_artifact_it_skips_rather_than_passing_on_the_contract_half(
    monkeypatch,
) -> None:
    def _absent(cfg: Config):
        raise NoCandidate("no artifact version in /nowhere, so there is no model to score.")

    monkeypatch.setattr(hg3, "candidate", _absent)

    result = GATE.check(load())

    assert result.status is Status.SKIPPED
    assert "parity is not established" in result.message
    assert "no model to score" in result.message


def test_an_environment_that_cannot_start_the_service_skips_and_names_the_extra(
    monkeypatch,
) -> None:
    """`importorskip` reasoning applied to a gate: a service that cannot start proved nothing."""
    monkeypatch.setitem(sys.modules, "fastapi.testclient", None)

    result = GATE.check(load())

    assert result.status is Status.SKIPPED
    assert "pip install -e '.[api,dev]'" in result.message


# --------------------------------------------------------------------------------------
# The parity half: the four defects the transport can introduce
# --------------------------------------------------------------------------------------


def _rounding(places: int):
    """A transport that answers with a rounded interval -- the truncation this gate is about."""
    real = _delivery.predict_capacity

    def _served(formula: str, temperature_k: float, *, bundle: Any = None):
        answer = real(formula, temperature_k, bundle=bundle)
        interval = getattr(answer, "interval", None)
        if interval is None:
            return answer
        return replace(
            answer, interval=replace(interval, lower=round(interval.lower, places))
        )

    return _served


def test_an_interval_bound_truncated_in_transport_is_red(monkeypatch, served: Config) -> None:
    """The card's own example, staged: a band quietly narrower than the calibrated one."""
    monkeypatch.setattr(_service, "predict_capacity", _rounding(2))

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert "/interval/lower" in result.message
    assert "the library" in result.message and "served" in result.message


def test_a_rejected_request_carrying_the_answer_discriminator_is_red(
    monkeypatch, served: Config
) -> None:
    """The silent failure: a client that branches on `refused` reads an error as an answer."""
    real = _service._invalid

    def _confused(message: str, problems: list[Any], *, error: str = "invalid_request"):
        response = real(message, problems, error=error)
        body = json.loads(response.body)
        return _service.JSONResponse(status_code=422, content={"refused": False, **body})

    monkeypatch.setattr(_service, "_invalid", _confused)

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert "carries a `refused` key" in result.message


def test_a_declared_code_the_api_stops_reaching_is_red(monkeypatch, served: Config) -> None:
    """Not "a code is missing" -- "a code is missing and nothing in the repo says why"."""
    real = _contract.reason_codes
    monkeypatch.setattr(
        _contract, "reason_codes", lambda screens=None: (*real(screens), "invented-code")
    )

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert "invented-code" in result.message
    assert "NOT_ALWAYS" in result.message


def test_a_code_with_no_input_at_this_door_becoming_reachable_is_red(
    monkeypatch, served: Config
) -> None:
    """The `untrusted-family` failure, staged on a code this fit really does reach over HTTP."""
    monkeypatch.setitem(
        NOT_ALWAYS, OUTSIDE_WINDOW, (Reachability.NEVER, "staged for this test")
    )

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert OUTSIDE_WINDOW in result.message
    assert "third door" in result.message


# --------------------------------------------------------------------------------------
# The batch and the deployment, staged against a stub transport
#
# These three failures need a *misbehaving* service rather than a misbehaving library, and the
# cheapest honest way to produce one is to answer the checker directly. What is under test here
# is the checker: a comparison that cannot report a reordered batch is a comparison that would
# pass over one.
# --------------------------------------------------------------------------------------


@dataclass
class _Reply:
    status_code: int
    payload: dict[str, Any]

    def json(self) -> dict[str, Any]:
        return self.payload

    @property
    def text(self) -> str:
        return json.dumps(self.payload)


class _Stub:
    """A client that answers from a script, in call order."""

    def __init__(self, *replies: _Reply, gets: dict[str, dict[str, Any]] | None = None) -> None:
        self._replies = list(replies)
        self._gets = gets or {}

    def post(self, url: str, **kwargs: Any) -> _Reply:
        return self._replies.pop(0)

    def get(self, url: str) -> _Reply:
        return _Reply(200, self._gets.get(url, {}))


def _rows(count: int) -> list[hg3.Served]:
    return [
        hg3.Served(
            name=probe.name,
            code="admitted",
            refused=False,
            body={"position": position},
            findings=(),
        )
        for position, probe in enumerate(PROBES[:count])
    ]


def _batch_reply(bodies: list[dict[str, Any]]) -> _Reply:
    return _Reply(200, {"schema": SCHEMA, "count": len(bodies), "answers": bodies})


def test_a_batch_that_reorders_its_rows_is_caught() -> None:
    """Positional matching is the whole contract of the batch route -- nothing else labels a row."""
    singles = _rows(len(PROBES))
    reversed_rows = [single.body for single in reversed(singles)]
    client = _Stub(_batch_reply(reversed_rows), _Reply(422, {"error": "batch_too_large"}))

    found = hg3._batch(client, singles, 256)

    assert found, "a reversed batch must not compare equal to the answers it reorders"
    assert any("row 0" in line for line in found), found


def test_a_batch_that_fails_the_whole_request_over_one_refused_row_is_caught() -> None:
    """A refused row is a refusal *in the list*: the request succeeded and each row says so."""
    client = _Stub(_Reply(422, {"error": "invalid_request"}))

    found = hg3._batch(client, _rows(len(PROBES)), 256)

    assert any("not a failed request" in line for line in found), found


def test_a_published_limit_that_is_not_enforced_is_caught() -> None:
    """A limit reported at /v1/health and not enforced is a limit a client discovers by timing out."""
    singles = _rows(len(PROBES))
    answered = _batch_reply([single.body for single in singles])
    client = _Stub(answered, _Reply(200, {"schema": SCHEMA, "count": 0, "answers": []}))

    found = hg3._batch(client, singles, 256)

    assert any("does not enforce" in line for line in found), found


def test_a_deployment_that_misreports_which_version_answered_is_caught() -> None:
    """"A number without the version that produced it is not evidence" -- at the transport."""
    bundle = dataclasses.make_dataclass("_Bundle", [("version", str)])("v2")
    client = _Stub(
        gets={
            "/v1/health": {"status": "ok", "model_version": "v1", "max_batch_rows": 256},
            "/v1/model": {"version": "v1"},
        }
    )

    limit, found = hg3._deployment(client, bundle, _rows(1))

    assert limit == 256
    assert len(found) == 3, found
    assert any("/v1/health reports version" in line for line in found), found
    assert any("/v1/model describes version" in line for line in found), found


def test_a_health_route_that_publishes_no_usable_limit_is_caught() -> None:
    bundle = dataclasses.make_dataclass("_Bundle", [("version", str)])("v2")
    client = _Stub(
        gets={
            "/v1/health": {"status": "ok", "model_version": "v2", "max_batch_rows": 0},
            "/v1/model": {"version": "v2"},
        }
    )

    limit, found = hg3._deployment(client, bundle, [])

    assert limit == 0
    assert any("a client cannot respect" in line for line in found), found


# --------------------------------------------------------------------------------------
# The vocabulary check, on its own
# --------------------------------------------------------------------------------------


def test_the_vocabulary_check_reports_both_of_its_failures() -> None:
    declared = {"admitted", "outside-window", "invented-code"}

    unexplained = hg3._vocabulary({"admitted", "outside-window"}, declared)
    assert any("invented-code" in line for line in unexplained), unexplained

    never = [code for code, (kind, _) in NOT_ALWAYS.items() if kind is Reachability.NEVER]
    appeared = hg3._vocabulary({"admitted", *never}, {"admitted", *never})
    assert any("no caller can reach" in line for line in appeared), appeared


def test_the_vocabulary_check_is_quiet_when_every_code_is_accounted_for() -> None:
    sometimes = [
        code for code, (kind, _) in NOT_ALWAYS.items() if kind is Reachability.SOMETIMES
    ]

    assert hg3._vocabulary({"admitted"}, {"admitted", *sometimes}) == []
