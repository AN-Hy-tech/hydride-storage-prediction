"""Card #77 -- the gate the whole phase exists for, and the six ways it has to go red.

``docs/QA-PROTOCOL.md`` section 5 will not trust a gate that has never failed, and this one
makes a claim strong enough that a check which quietly established nothing would be worse than
no check at all. So every branch that can fail is made to fail here, on purpose.

**It passes over a real artifact.** The same cheap deployed fit AC-3 and AC-4 score, written
with no gate report -- the state card #33's knot is about -- and reached through
:func:`~hydms.delivery.predict.bundle_from`, which is that same split one layer up. The last
test in this file pins that :func:`~hydms.delivery.predict.load_bundle` still refuses the very
version the gate just scored, so the escape cannot widen without something going red.

**The structural half goes red without any artifact at all.** A default on ``interval``, a
``capacity`` field on ``Refusal``, a branch of ``predict_capacity`` that returns something
else, a bare ``return`` -- each is injected and the gate is required to name it. That is the
half CI can run: ``.gitignore`` excludes ``/artifacts/``, so the fast lane has no version to
score and this gate is one that **can go red where it cannot go green**.

**A skip is not a pass, twice over.** With no artifact the gate skips rather than reporting
the structural half as a pass; and with a fit that refuses every probe it skips too, because a
model that refuses everything satisfies "never a bare number" trivially and establishes
nothing about the branch that returns a number.

**Reachability is per door, and all three of its failures are exercised**: a declared code no
door reaches, a code this door stopped reaching with nothing saying why, and
``untrusted-family`` becoming reachable by typing -- which is card #76's finding turned into
an assertion.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import pytest

pytest.importorskip("pandas", reason="the delivery path is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")
pytest.importorskip(
    "ElMD",
    reason="the `novelty` extra; ElMD is on the prediction path, so CI installs it",
)

from hydms.config import Config  # noqa: E402
from hydms.delivery import contract as _contract  # noqa: E402
from hydms.delivery import predict as _delivery  # noqa: E402
from hydms.delivery.contract import (  # noqa: E402
    DomainVerdict,
    Interval,
    PredictionRequest,
)
from hydms.gates import Status  # noqa: E402
from hydms.gates import hg2_refusal_path as hg2  # noqa: E402
from hydms.gates._artifact import NoCandidate  # noqa: E402
from hydms.gates.hg2_refusal_path import GATE, NOT_ALWAYS, PROBES, Reachability  # noqa: E402
from hydms.screens.domain import UNTRUSTED_FAMILY  # noqa: E402
from hydms.screens.window import OUTSIDE_WINDOW  # noqa: E402

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
    assert result.name == "HG-2"


def test_the_message_names_both_doors_and_the_version_that_answered(served: Config) -> None:
    """A gate result that does not say *of what* is not evidence (the AC-3 convention)."""
    result = GATE.check(served)

    assert "request door" in result.message
    assert "curated frame" in result.message
    assert "nothing is promoted yet" in result.message
    assert "0 bare numbers" in str(result.measured)


def test_it_reports_how_many_exits_it_read_rather_than_how_many_it_sampled(
    served: Config,
) -> None:
    """The card's "asserted exhaustively, not sampled": the count is of returns, not inputs."""
    result = GATE.check(served)

    exits, findings = hg2._exits()
    assert not findings
    assert f"all {exits} exits" in result.message
    assert exits >= 3, "predict_capacity has a parse branch, a refusal branch and an answer"


def test_untrusted_family_is_recorded_as_unreachable_by_typing(served: Config) -> None:
    """Card #76's finding, as a standing assertion rather than a paragraph."""
    kind, why = NOT_ALWAYS[UNTRUSTED_FAMILY]

    assert kind is Reachability.NEVER
    assert "no label" in why or "supplies no label" in why
    assert UNTRUSTED_FAMILY in GATE.check(served).message


def test_every_probe_declares_what_it_is_for() -> None:
    """A probe with no stated purpose cannot fail; it can only be re-labelled (card #90)."""
    for probe in PROBES:
        assert probe.why.strip(), probe.name
        assert probe.formula.strip(), probe.name


# --------------------------------------------------------------------------------------
# The structural half: red with no artifact in sight
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Defaulted:
    """A result type whose interval may be omitted -- the bare number, arriving by default."""

    request: PredictionRequest
    capacity: float
    domain: DomainVerdict
    novelty: object
    model_version: str
    interval: Interval | None = None


@dataclass(frozen=True)
class _RefusalWithANumber:
    """A refusal carrying a capacity "for reference" -- the bare number with a disclaimer."""

    request: PredictionRequest
    code: str
    explanation: str
    capacity: float = 0.0
    model_version: str | None = None
    screens: tuple[object, ...] = field(default_factory=tuple)


def test_a_default_on_the_interval_is_a_structural_finding(monkeypatch) -> None:
    monkeypatch.setattr(_contract, "PredictionResult", _Defaulted)

    found = hg2._structural()

    assert found, "a defaulted interval is exactly the bare number card #75 forbids"
    assert any("interval" in line and "default" in line for line in found), found


def test_a_refusal_that_carries_a_number_is_a_structural_finding(monkeypatch) -> None:
    monkeypatch.setattr(_contract, "Refusal", _RefusalWithANumber)

    found = hg2._structural()

    assert any("capacity" in line for line in found), found


def test_the_real_contract_has_no_structural_finding() -> None:
    assert hg2._structural() == []


def _returns_a_float(formula: str, temperature_k: float) -> float:
    """A prediction path that answers with a number and nothing else."""
    return 1.4


def _returns_nothing(formula: str, temperature_k: float) -> None:
    """A prediction path with a branch that falls out silently."""
    if formula:
        return
    return None


def test_a_branch_returning_a_bare_number_is_caught_by_reading_the_source(
    monkeypatch,
) -> None:
    """No probe set can establish this. Reading every exit can, and that is the difference."""
    monkeypatch.setattr(_delivery, "predict_capacity", _returns_a_float)

    _count, findings = hg2._exits()

    assert findings
    assert any("not a Refusal or a PredictionResult" in line for line in findings), findings


def test_a_bare_return_is_caught_as_an_answer_of_none(monkeypatch) -> None:
    monkeypatch.setattr(_delivery, "predict_capacity", _returns_nothing)

    _count, findings = hg2._exits()

    assert any("bare `return`" in line for line in findings), findings


def test_the_gate_is_red_on_a_structural_finding_before_it_looks_for_an_artifact(
    monkeypatch,
) -> None:
    """The half CI can run: no artifact is on disk in the fast lane, and this still fails."""
    monkeypatch.setattr(_contract, "PredictionResult", _Defaulted)
    monkeypatch.setattr(
        hg2, "candidate", lambda cfg: pytest.fail("looked for an artifact first")
    )
    from hydms.config import load

    result = GATE.check(load())

    assert result.status is Status.FAILED
    assert "without an interval and a domain verdict" in result.message


# --------------------------------------------------------------------------------------
# A skip is not a pass
# --------------------------------------------------------------------------------------


def test_with_no_artifact_it_skips_rather_than_passing_on_the_structural_half(
    monkeypatch,
) -> None:
    def _absent(cfg: Config):
        raise NoCandidate("no artifact version in /nowhere, so there is no model to score.")

    monkeypatch.setattr(hg2, "candidate", _absent)
    from hydms.config import load

    result = GATE.check(load())

    assert result.status is Status.SKIPPED
    assert "not established" in result.message
    assert "no model to score" in result.message


def test_a_fit_that_refuses_everything_establishes_nothing_and_says_so(
    served: Config,
) -> None:
    """"Never a bare number" is satisfied trivially by never answering. That is not a pass."""
    nowhere = replace(
        served,
        domain=replace(
            served.domain, temperature_min_k=1200.0, temperature_max_k=1300.0
        ),
    )

    result = GATE.check(nowhere)

    assert result.status is Status.SKIPPED, result.message
    assert "branch that returns a number was never reached" in result.message
    assert OUTSIDE_WINDOW in result.message


# --------------------------------------------------------------------------------------
# Reachability, per door -- all three failures
# --------------------------------------------------------------------------------------


def test_a_declared_code_this_door_stopped_reaching_is_red(monkeypatch, served: Config) -> None:
    """Not "a code is missing" -- "a code is missing and nothing in the repo says why"."""
    real = _contract.reason_codes
    monkeypatch.setattr(
        _contract, "reason_codes", lambda screens=None: (*real(screens), "invented-code")
    )

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert "invented-code" in result.message
    assert "NOT_ALWAYS" in result.message


def test_a_code_no_door_reaches_is_red_as_dead_vocabulary(monkeypatch, served: Config) -> None:
    real = _contract.reason_codes
    monkeypatch.setattr(
        _contract, "reason_codes", lambda screens=None: (*real(screens), "invented-code")
    )
    monkeypatch.setitem(
        NOT_ALWAYS, "invented-code", (Reachability.SOMETIMES, "for this test")
    )

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert "reachable through neither" in result.message


def test_a_code_with_no_input_at_this_door_becoming_reachable_is_red(
    monkeypatch, served: Config
) -> None:
    """The `untrusted-family` failure, staged on a code this fit really does reach."""
    monkeypatch.setitem(
        NOT_ALWAYS, OUTSIDE_WINDOW, (Reachability.NEVER, "staged for this test")
    )

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert OUTSIDE_WINDOW in result.message
    assert "stays unreachable" in str(result.threshold)


# --------------------------------------------------------------------------------------
# The behavioural half: what a probe finding looks like
# --------------------------------------------------------------------------------------


def test_a_deployment_without_the_novelty_screen_is_caught(monkeypatch, served: Config) -> None:
    """AC-7 answered with a blank is the failure only a deployment would have shown (#76)."""
    real = _contract.delivery_screens
    monkeypatch.setattr(_delivery, "delivery_screens", lambda cfg=None: real(cfg)[:2])

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert "no novelty distance" in result.message
    assert "AC-7" in result.message


def test_a_refusal_that_stops_naming_the_range_is_caught(monkeypatch, served: Config) -> None:
    """#49's defect: the right code with a sentence that no longer says what it is about."""
    from hydms.screens import window as window_module

    real = window_module.Window.verdict

    def _vague(self, candidates):
        table = real(self, candidates)
        reason = next(c for c in table.columns if str(c).endswith("reason"))
        table[reason] = "cannot predict"
        return table

    monkeypatch.setattr(window_module.Window, "verdict", _vague)

    result = GATE.check(served)

    assert result.status is Status.FAILED, result.message
    assert "never names" in result.message


# --------------------------------------------------------------------------------------
# The escape it walks through, pinned so it cannot widen
# --------------------------------------------------------------------------------------


def test_the_version_it_scored_is_one_the_delivery_path_refuses(served: Config) -> None:
    """The same pin ``tests/gates/test_artifact.py`` holds for AC-3 and AC-4, one layer up.

    The gate reaches its candidate through :func:`~hydms.delivery.predict.bundle_from`, which
    takes an already-loaded surrogate. :func:`~hydms.delivery.predict.load_bundle` -- the door
    a deployment uses -- still refuses this exact version, because its gate run is the thing
    the gate is producing. If that ever stops being true, the split became a hole.

    The version is **named** rather than left to the promotion pointer, which is the stronger
    half of what ``load_surrogate`` promises: nothing is promoted in this store, so the pointer
    would refuse for a reason that has nothing to do with gates.
    """
    from hydms.artifacts import GatesIncomplete

    assert GATE.check(served).status is Status.PASSED

    with pytest.raises(GatesIncomplete):
        _delivery.load_bundle("v1", store=served.paths.artifacts)
