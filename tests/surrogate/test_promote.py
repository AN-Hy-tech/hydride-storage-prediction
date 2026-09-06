"""Card #34 — certifying a candidate version, and refusing to when it is not established.

The command's whole subject is a refusal, so that is what most of this file measures. Three
properties, each a way a promotion regime lies:

**A skip is not a pass.** Seven of the twelve registered criteria are unwritten while Phase H
runs, and four of those are frozen out of this phase entirely. The command must refuse, name
them, and write nothing — a version promoted over a `SKIPPED` would carry a manifest claiming
evidence nobody produced.

**A refusal writes nothing.** Not a partial version, not a moved pointer. Asserted on the
directory listing rather than on the exit code, because an exit code is what a script reads and
the directory is what the next run inherits.

**A green run promotes a version that carries the report** — a *new* one, because a manifest is
sealed when it is written. The candidate stays on disk, and the promoted version's notes point
back at it, so the chain from a promoted model to the commit that fitted it is two hops and
neither is inferred.

The gate registry is not stubbed out here. It is patched to a small set of stand-in gates,
because this file is about the promotion logic and a real ``--all`` run costs two minutes of
CatBoost — but the stand-ins are real :class:`~hydms.gates.Gate` objects, so the shape the
command consumes cannot drift from the shape the harness produces.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

pytest.importorskip("joblib", reason="the artifact store persists through joblib")

from hydms import artifacts  # noqa: E402
from hydms.config import Config  # noqa: E402
from hydms.gates import Gate, GateResult, Speed  # noqa: E402
from hydms.surrogate import promote as command  # noqa: E402

CONTRACT = {"features": [{"name": "temperature(K)"}]}


@dataclass(frozen=True)
class _Stub:
    """A gate with a fixed verdict. Real enough to satisfy the ``Gate`` protocol."""

    name: str
    verdict: str
    card: int = 99
    title: str = "a stand-in"
    speed: Speed = Speed.FAST

    def check(self, cfg: Config) -> GateResult:
        if self.verdict == "PASSED":
            return GateResult.ok(self.name, "established")
        if self.verdict == "SKIPPED":
            return GateResult.skip(self.name, "not implemented")
        return GateResult.fail(self.name, "did not hold", measured=1.0, threshold=0.0)


@pytest.fixture
def store(tmp_path: Path) -> Path:
    """One candidate version with no gate report — what ``calibrate --save`` leaves."""
    directory = tmp_path / "artifacts"
    artifacts.save(
        {"model": [1, 2, 3]},
        contract=CONTRACT,
        seeds={"pipeline": 42},
        gates=None,
        notes="deployed fit",
        store=directory,
    )
    return directory


@pytest.fixture
def registered(monkeypatch):
    """Replace the registry with a chosen set of stand-in gates."""

    def _register(*gates: Gate) -> None:
        monkeypatch.setattr("hydms.gates._core._discover", lambda: tuple(gates))

    return _register


def _run(store: Path, *argv: str, capsys) -> tuple[int, str, str]:
    code = command.main(["--store", str(store), *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# --------------------------------------------------------------------------------------
# Refusal
# --------------------------------------------------------------------------------------


def test_a_skipped_criterion_refuses_the_promotion_and_is_named(store, registered, capsys) -> None:
    registered(_Stub("AC-2", "PASSED"), _Stub("AC-6", "SKIPPED", card=30))
    code, _out, err = _run(store, capsys=capsys)

    assert code == command.EXIT_UNESTABLISHED
    assert "AC-6 SKIPPED (card #30)" in err
    assert "AC-2" not in err.split("NOT promotable")[1].split("\n")[0]


def test_a_failed_criterion_refuses_the_promotion(store, registered, capsys) -> None:
    registered(_Stub("AC-3", "FAILED", card=31))
    code, _out, err = _run(store, capsys=capsys)
    assert code == command.EXIT_UNESTABLISHED
    assert "AC-3 FAILED (card #31)" in err


def test_a_refusal_writes_no_version_and_moves_no_pointer(store, registered, capsys) -> None:
    registered(_Stub("AC-6", "SKIPPED"))
    _run(store, capsys=capsys)

    assert artifacts.versions(store=store) == ("v1",)
    assert artifacts.current(store=store) is None
    assert not any(path.name.startswith(".") for path in store.iterdir())


# --------------------------------------------------------------------------------------
# Certification
# --------------------------------------------------------------------------------------


def test_a_green_run_writes_a_second_version_carrying_the_report(store, registered, capsys) -> None:
    registered(_Stub("AC-2", "PASSED"), _Stub("AC-3", "PASSED"))
    code, out, _err = _run(store, capsys=capsys)

    assert code == command.EXIT_OK
    assert artifacts.versions(store=store) == ("v1", "v2")
    assert artifacts.current(store=store) == "v2"

    manifest = artifacts.read_manifest(store / "v2")
    assert manifest.unestablished() == ()
    assert {entry["name"] for entry in manifest.gates["gates"]} == {"AC-2", "AC-3"}
    assert "v2" in out


def test_the_certified_version_points_back_at_the_fit_that_made_it(store, registered) -> None:
    """Two hops from a promoted model to the commit that fitted it, neither inferred."""
    registered(_Stub("AC-2", "PASSED"))
    command.main(["--store", str(store)])

    source = artifacts.read_manifest(store / "v1")
    certified = artifacts.read_manifest(store / "v2")
    assert "certified copy of v1" in certified.notes
    assert source.created_at in certified.notes
    # A tmp_path store sits outside any work tree, so `describe_git` records no SHA. The note
    # has to read as a sentence either way, which is the case this asserts.
    assert (source.git.sha or "an unknown commit") in certified.notes


def test_the_payloads_and_the_seeds_are_the_candidates_own(store, registered) -> None:
    registered(_Stub("AC-2", "PASSED"))
    command.main(["--store", str(store)])

    assert artifacts.load("v2", store=store)["model"] == [1, 2, 3]
    assert artifacts.read_manifest(store / "v2").seeds == {"pipeline": 42}


def test_dry_run_certifies_nothing(store, registered, capsys) -> None:
    registered(_Stub("AC-2", "PASSED"))
    code, out, _err = _run(store, "--dry-run", capsys=capsys)

    assert code == command.EXIT_OK
    assert "--dry-run" in out
    assert artifacts.versions(store=store) == ("v1",)
    assert artifacts.current(store=store) is None


# --------------------------------------------------------------------------------------
# Invocation
# --------------------------------------------------------------------------------------


def test_an_empty_store_names_the_command_that_fills_it(tmp_path: Path, capsys) -> None:
    code, _out, err = _run(tmp_path / "nothing", capsys=capsys)
    assert code == command.EXIT_BAD_INVOCATION
    assert "hydms.surrogate.calibrate" in err


def test_an_unknown_version_lists_the_ones_that_exist(store, capsys) -> None:
    code, _out, err = _run(store, "--version", "v9", capsys=capsys)
    assert code == command.EXIT_BAD_INVOCATION
    assert "Present: v1" in err


def test_it_certifies_the_newest_version_by_default(store, registered, capsys) -> None:
    artifacts.save({"model": [4]}, contract=CONTRACT, gates=None, store=store, notes="newer")
    registered(_Stub("AC-2", "PASSED"))
    _run(store, capsys=capsys)

    assert "certified copy of v2" in artifacts.read_manifest(store / "v3").notes


# --------------------------------------------------------------------------------------
# The state Phase H is actually in
# --------------------------------------------------------------------------------------


def test_the_real_registry_cannot_certify_anything_in_this_phase() -> None:
    """Recorded as a test because it is the finding, not a limitation of the command.

    ``promote`` requires every registered criterion to have passed, and three of them — AC-5,
    AC-7 and AC-8 — belong to phases ``docs/FREEZE.md`` has frozen, so no amount of Phase H
    work makes them green. That is the store's guarantee working exactly as written.

    **Card #34's open decision has since been taken**: those three, and only those three, may
    be named to ``--waive``, which records them in ``current.json`` and never in the manifest.
    This test still asserts they are unwritten, because the day one of them is implemented the
    waiver stops being warranted and somebody has to notice. Which criteria are waivable is
    derived from the board by ``tests/artifacts/test_waiver_scope.py``.
    """
    from hydms.gates import Pending, registry

    unwritten = {gate.name for gate in registry() if isinstance(gate, Pending)}
    assert {"AC-5", "AC-7", "AC-8"} <= unwritten, (
        "the frozen-phase gates are implemented -- card #34's open decision may have been "
        "settled, or the freeze may have lifted; re-read the card before editing this"
    )


def test_the_report_the_command_embeds_is_the_shape_the_store_validates(
    store, registered
) -> None:
    """The manifest's gate block must survive a JSON round trip and the store's own validator."""
    registered(_Stub("AC-2", "PASSED"))
    command.main(["--store", str(store)])

    raw = json.loads((store / "v2" / "manifest.json").read_text(encoding="utf-8"))
    from hydms.artifacts.manifest import validate_gate_report

    validate_gate_report(raw["gates"])


# --------------------------------------------------------------------------------------
# --waive: the way out of the phase, and the four things it will not do — card #34
# --------------------------------------------------------------------------------------


def test_a_waived_skip_lets_the_promotion_through_and_says_so_loudly(
    store, registered, capsys
) -> None:
    registered(_Stub("AC-2", "PASSED"), _Stub("AC-7", "SKIPPED", card=57))
    code, out, _err = _run(store, "--waive", "AC-7", capsys=capsys)

    assert code == command.EXIT_OK
    assert "WAIVED" in out and "AC-7 (card #57)" in out
    assert artifacts.current(store=store) == "v2"
    assert artifacts.waived(store=store) == {"AC-7": "not implemented"}


def test_the_reason_recorded_is_the_gates_own_not_the_operators(
    store, registered, capsys
) -> None:
    """A `Pending` gate already states why it is pending, and that sentence is reviewed code.
    Nothing on the command line contributes to what gets written down."""
    registered(_Stub("AC-2", "PASSED"), _Stub("AC-7", "SKIPPED", card=57))
    _run(store, "--waive", "AC-7", capsys=capsys)
    assert artifacts.waived(store=store)["AC-7"] == "not implemented"


def test_waiving_does_not_touch_what_the_manifest_records(store, registered, capsys) -> None:
    """The promoted version's embedded report still says AC-7 was skipped. The artifact's
    account of what was measured is exactly as truthful after a waiver as before it."""
    registered(_Stub("AC-2", "PASSED"), _Stub("AC-7", "SKIPPED", card=57))
    _run(store, "--waive", "AC-7", capsys=capsys)

    raw = json.loads((store / "v2" / "manifest.json").read_text(encoding="utf-8"))
    statuses = {entry["name"]: entry["status"] for entry in raw["gates"]["gates"]}
    assert statuses == {"AC-2": "PASSED", "AC-7": "SKIPPED"}
    assert "waived" not in json.dumps(raw["gates"])


def test_a_failure_cannot_be_waived_at_the_command_line_either(store, registered, capsys) -> None:
    registered(_Stub("AC-3", "FAILED", card=31))
    code, _out, err = _run(store, "--waive", "AC-3", capsys=capsys)

    assert code == command.EXIT_BAD_INVOCATION
    assert "it is FAILED in this run" in err
    assert artifacts.current(store=store) is None
    assert artifacts.versions(store=store) == ("v1",), "nothing was written"


def test_waiving_one_skip_does_not_carry_another(store, registered, capsys) -> None:
    """Phase H's real shape: AC-7 is out of reach, AC-6 is work this phase owes. The refusal
    has to name AC-6 and must not be satisfied by the waiver beside it.

    And the accepted waiver is still reported: an operator who waives three criteria and is
    refused for a fourth must be able to see the three were parsed, or the refusal reads as the
    flag having done nothing.
    """
    registered(
        _Stub("AC-2", "PASSED"),
        _Stub("AC-6", "SKIPPED", card=30),
        _Stub("AC-7", "SKIPPED", card=57),
    )
    code, out, err = _run(store, "--waive", "AC-7", capsys=capsys)

    assert code == command.EXIT_UNESTABLISHED
    assert "AC-6 SKIPPED (card #30)" in err
    assert "WAIVED" in out and "AC-7 (card #57)" in out
    assert artifacts.current(store=store) is None


def test_the_two_counts_one_run_prints_are_the_same_count(store, registered, capsys) -> None:
    """Both messages answer "how much is left?" and they have to agree.

    They did not. The waiver summary computed ``len(results) - len(waived)`` while the refusal
    computed ``len(outstanding)``, so a run over five passes, three waivers and four genuine
    skips announced **9** and then **4**, six lines apart, about the same twelve criteria. The
    summary was ignoring every criterion that had *passed*.

    Nothing caught it because nothing asserted the sentence -- which is the project's own rule
    (``docs/QA-PROTOCOL.md`` section 3: no number in prose that a test does not check) applied
    to prose the code itself prints. The count is derived once now; this test is what keeps it
    that way, and it is written against the numbers rather than the wording so it survives an
    edit to the message.
    """
    registered(
        _Stub("AC-1", "PASSED"),
        _Stub("AC-2", "PASSED"),
        _Stub("AC-6", "SKIPPED", card=30),
        _Stub("AC-7", "SKIPPED", card=57),
        _Stub("AC-8", "SKIPPED", card=56),
    )
    code, out, err = _run(store, "--waive", "AC-7", "--waive", "AC-8", capsys=capsys)

    assert code == command.EXIT_UNESTABLISHED
    # Five criteria, two waived, two passed -- so exactly one is left to establish, and the
    # naive "total minus waived" would have said three.
    assert "has 1 of 5 criteria left to establish" in out
    assert "1 of 5 criteria are unestablished" in err
    assert "3 of 5" not in out


def test_waiving_a_name_nothing_answers_to_lists_what_is_registered(
    store, registered, capsys
) -> None:
    registered(_Stub("AC-2", "PASSED"), _Stub("AC-7", "SKIPPED", card=57))
    code, _out, err = _run(store, "--waive", "AC-70", capsys=capsys)

    assert code == command.EXIT_BAD_INVOCATION
    assert "no criterion by that name" in err and "AC-7" in err


def test_a_dry_run_with_a_waiver_still_writes_nothing(store, registered, capsys) -> None:
    registered(_Stub("AC-2", "PASSED"), _Stub("AC-7", "SKIPPED", card=57))
    code, out, _err = _run(store, "--waive", "AC-7", "--dry-run", capsys=capsys)

    assert code == command.EXIT_OK
    assert "was waived (AC-7)" in out
    assert artifacts.versions(store=store) == ("v1",)
    assert artifacts.current(store=store) is None
