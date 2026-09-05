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

    ``promote`` requires every registered criterion to have passed, and four of them — AC-5,
    AC-7, AC-8 and, until #78 lands, HG-3 — belong to phases ``docs/FREEZE.md`` has frozen.
    So no artifact can be promoted before those phases resume, and ``predict()`` therefore
    refuses every version this phase produces. That is the store's guarantee working exactly as
    written; whether Phase H should be able to certify a *phase-scoped* subset is an open
    decision recorded on card #34, and it is not this test's to take.
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
