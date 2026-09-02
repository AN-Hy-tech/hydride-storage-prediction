"""Tests for the gate harness itself.

The harness is the thing that decides whether everything else is allowed to be called
correct, so the tests here are mostly about the ways a check regime lies rather than about
the ways this code crashes:

  - an unimplemented criterion reporting a pass,
  - a gate that raised being counted as absent rather than red,
  - one gate reporting on another's behalf,
  - a typo in a CI workflow selecting zero gates and going green.

`docs/QA-PROTOCOL.md` section 5 requires a gate to have been made red on purpose before it is
trusted. `test_a_failing_gate_turns_the_report_red` and its neighbours are that demonstration
for the harness: they install deliberately broken gates and assert the run goes red.

Card #5.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import pytest
from hydms.config import Config, load
from hydms.gates import (
    Gate,
    GateResult,
    Pending,
    Speed,
    Status,
    UnknownGate,
    registry,
    render_registry,
    render_report,
    run,
    select,
    write_report,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# The frozen three. They are registered so the registry is a complete list of what the
# project has promised to check, and they are absent from the runbook's Phase H gate table
# because this phase does not run them. Both facts are asserted below.
FROZEN = {"AC-5", "AC-7", "AC-8"}


@pytest.fixture(scope="module")
def cfg() -> Config:
    return load()


# --------------------------------------------------------------------------------------
# Test doubles. Each is a way a gate can misbehave.
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Stub:
    name: str
    result: object
    title: str = "a test double"
    card: int = 0
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result  # type: ignore[return-value]


def _passing(name: str = "T-1") -> _Stub:
    return _Stub(name, GateResult.ok(name, "held", measured=1.0, threshold=1.0))


def _failing(name: str = "T-2") -> _Stub:
    return _Stub(name, GateResult.fail(name, "did not hold", measured=0.71, threshold=0.90))


# --------------------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------------------


def test_every_promised_criterion_is_registered() -> None:
    """Twelve: the PRD's eight acceptance criteria plus Phase H's four hardening gates."""
    names = {g.name for g in registry()}
    assert names == {
        "AC-1", "AC-2", "AC-3", "AC-4", "AC-5", "AC-6", "AC-7", "AC-8",
        "HG-1", "HG-2", "HG-3", "HG-4",
    }


def test_gate_names_are_unique_and_sorted() -> None:
    names = [g.name for g in registry()]
    assert names == sorted(names)
    assert len(names) == len(set(names))


def test_every_gate_names_a_card_that_exists_on_one_of_the_two_boards() -> None:
    """A gate owned by no card is a promise nobody is holding.

    Both boards are scanned: the frozen three are owned by cards in `kanban/`, which is
    exactly why they are registered as frozen rather than dropped.
    """
    ids = {
        int(p.name[:3])
        for board in ("kanban", "kanban-hardening")
        for p in (REPO_ROOT / board).glob("[0-9][0-9][0-9]-*.md")
    }
    for gate in registry():
        assert gate.card in ids, f"{gate.name} names card #{gate.card}, which is on no board"


def test_no_unimplemented_gate_can_report_passed(cfg: Config) -> None:
    """The rule the whole harness exists for: absence of evidence is never a pass."""
    report = run(registry(), cfg, selection="--all")
    for result in report.results:
        assert result.status is not Status.PASSED, (
            f"{result.name} reported PASSED while its module still declares a Pending gate"
        )


def test_pending_gates_report_their_owning_card_and_blockers(cfg: Config) -> None:
    """The skip line has to be actionable, or the table is a wall of 'not done'."""
    gate = next(g for g in registry() if g.name == "AC-2")
    result = gate.check(cfg)
    assert result.status is Status.SKIPPED
    assert "#21" in result.message      # who owes it
    assert "#20" in result.message      # what it is waiting for


def test_the_frozen_criteria_say_so(cfg: Config) -> None:
    for name in sorted(FROZEN):
        gate = next(g for g in registry() if g.name == name)
        assert "frozen" in gate.check(cfg).message.lower(), (
            f"{name} is on the frozen board; its skip reason must say so, or a reader will "
            f"take it for work that was merely forgotten"
        )


def test_the_registry_matches_the_runbook_gate_table() -> None:
    """Prose and code must agree on who owns which gate.

    `docs/QA-PROTOCOL.md` section 2, L7: every number quoted in prose traces to an artifact
    that currently holds that value. The runbook's section 4 table is that prose for gates.
    """
    text = (REPO_ROOT / "docs" / "PHASE-H-RUNBOOK.md").read_text(encoding="utf-8")
    row = re.compile(r"^\|\s*\*{0,2}(AC-\d|HG-\d)\*{0,2}[^|]*\|\s*#(\d+)\s*\|", re.MULTILINE)
    documented = {name: int(card) for name, card in row.findall(text)}
    assert documented, "no gate table found in docs/PHASE-H-RUNBOOK.md section 4"

    owners = {g.name: g.card for g in registry()}
    for name, card in documented.items():
        assert owners.get(name) == card, (
            f"the runbook says {name} is owned by card #{card}; the harness says "
            f"#{owners.get(name)}. One of them is wrong."
        )
    assert set(owners) - set(documented) == FROZEN, (
        "every registered gate must appear in the runbook's table unless it is frozen"
    )


# --------------------------------------------------------------------------------------
# Selection
# --------------------------------------------------------------------------------------


def test_selecting_by_name_is_case_insensitive_and_order_preserving() -> None:
    chosen = select(["hg-1", "AC-2"])
    assert [g.name for g in chosen] == ["HG-1", "AC-2"]


def test_a_repeated_name_runs_once() -> None:
    assert [g.name for g in select(["AC-2", "AC-2"])] == ["AC-2"]


def test_an_unknown_name_is_loud() -> None:
    """A silent empty selection would report a green run over zero checks."""
    with pytest.raises(UnknownGate) as exc:
        select(["AC-99"])
    assert "AC-2" in str(exc.value), "the error must list what is available"


def test_the_lanes_partition_the_registry() -> None:
    fast = set(select(speed=Speed.FAST))
    slow = set(select(speed=Speed.SLOW))
    assert not fast & slow
    assert fast | slow == set(registry())
    assert fast, "the fast lane must not be empty, or the per-push CI checks nothing"


# --------------------------------------------------------------------------------------
# Running: the failure modes
# --------------------------------------------------------------------------------------


def test_a_passing_gate_is_green(cfg: Config) -> None:
    report = run([_passing()], cfg)
    assert report.ok
    assert report.counts["passed"] == 1
    assert report.results[0].measured == 1.0


def test_a_failing_gate_turns_the_report_red(cfg: Config) -> None:
    """The demonstration required by QA-PROTOCOL section 5: this harness can go red."""
    report = run([_failing()], cfg)
    assert not report.ok
    assert report.counts["failed"] == 1
    assert report.results[0].measured == 0.71
    assert report.results[0].threshold == 0.90


def test_a_gate_that_raises_is_errored_and_does_not_stop_the_run(cfg: Config) -> None:
    """One broken check must not hide the state of every check after it."""
    gates: list[Gate] = [
        _Stub("T-boom", RuntimeError("artifact bundle is missing")),
        _passing("T-after"),
    ]
    report = run(gates, cfg)
    assert not report.ok
    assert [r.status for r in report.results] == [Status.ERRORED, Status.PASSED]
    assert "artifact bundle is missing" in report.results[0].message


def test_a_gate_may_not_report_on_another_gates_behalf(cfg: Config) -> None:
    impostor = _Stub("T-impostor", GateResult.ok("AC-2", "all good, honestly"))
    report = run([impostor], cfg)
    assert report.results[0].status is Status.ERRORED
    assert report.results[0].name == "T-impostor"
    assert "may only report on itself" in report.results[0].message


def test_a_gate_that_returns_the_wrong_type_is_errored(cfg: Config) -> None:
    report = run([_Stub("T-junk", "looks fine to me")], cfg)
    assert report.results[0].status is Status.ERRORED
    assert "not a GateResult" in report.results[0].message


def test_pending_cannot_be_configured_into_passing(cfg: Config) -> None:
    gate = Pending(
        name="T-pending",
        title="a criterion nobody has written",
        card=999,
        speed=Speed.FAST,
        reason="on purpose",
    )
    assert gate.check(cfg).status is Status.SKIPPED


# --------------------------------------------------------------------------------------
# Strictness: what a skip means depends on what was asked
# --------------------------------------------------------------------------------------


def test_a_skip_is_tolerated_under_a_broad_selection(cfg: Config) -> None:
    report = run(registry(), cfg, selection="--all", strict=False)
    assert report.counts["skipped"] == len(registry())
    assert report.ok, "a whole-registry run must not be red merely because work is unwritten"


def test_a_skip_is_fatal_when_the_gate_was_named(cfg: Config) -> None:
    report = run(select(["AC-2"]), cfg, selection="AC-2", strict=True)
    assert not report.ok, "you asked a specific question and did not get an answer"


# --------------------------------------------------------------------------------------
# The report
# --------------------------------------------------------------------------------------


def test_a_skip_does_not_read_like_a_pass(cfg: Config) -> None:
    text = render_report(run(registry(), cfg, selection="--all"), registry())
    assert "NOT CHECKED" in text
    assert "12 skipped" in text


def test_the_table_names_the_measured_value_and_the_owning_card(cfg: Config) -> None:
    gate = _failing("T-2")
    text = render_report(run([gate], cfg), (gate,))
    assert "0.71" in text and "0.9" in text


def test_a_multi_line_failure_is_printed_below_the_table_not_inside_it(cfg: Config) -> None:
    """A traceback in a table cell destroys the alignment of every other row."""
    gate = _Stub("T-boom", RuntimeError("boom"))
    lines = render_report(run([gate], cfg), (gate,)).splitlines()
    table_row = next(line for line in lines if line.startswith("T-boom"))
    assert "Traceback" not in table_row
    assert "--- T-boom ---" in lines


def test_the_registry_listing_names_the_lane_and_the_card() -> None:
    text = render_registry(registry())
    assert "12 gates registered." in text
    assert "#71" in text and "fast" in text and "slow" in text


def test_the_json_report_round_trips(cfg: Config, tmp_path: Path) -> None:
    report = run([_passing(), _failing()], cfg, selection="--all")
    destination = write_report(report, tmp_path / "nested" / "gate-results.json")

    loaded = json.loads(destination.read_text(encoding="utf-8"))
    assert loaded["schema"] == "hydms.gates/1"
    assert loaded["ok"] is False
    assert loaded["summary"] == {"passed": 1, "failed": 1, "skipped": 0, "errored": 0}
    assert [g["name"] for g in loaded["gates"]] == ["T-1", "T-2"]
    assert loaded["gates"][1]["measured"] == 0.71
    assert loaded["gates"][0]["passed"] is True


def test_the_report_records_what_was_asked_for(cfg: Config) -> None:
    """Card #4 embeds this object. A result set with no record of its selection would let a
    fast-lane run be read later as though it had covered everything."""
    report = run(select(speed=Speed.FAST), cfg, selection="--fast")
    assert report.to_dict()["selection"] == "--fast"
    assert report.to_dict()["strict"] is False
