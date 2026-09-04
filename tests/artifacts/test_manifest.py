"""What a manifest records, and what it refuses to read.

The QA protocol's L0 row asks for one thing by name: *the artifact manifest round-trips*. That
is the first section here. The rest tests the two judgements the manifest makes rather than
merely stores -- whether a gate run established anything, and whether a file on disk is still
the file that was written.

Card #4.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from hydms.artifacts.manifest import (
    GATE_SCHEMA,
    RECORDED_PACKAGES,
    SCHEMA,
    Git,
    Manifest,
    ManifestError,
    PayloadRecord,
    describe_git,
    digest_file,
    environment,
    now,
    resolved_packages,
    validate_gate_report,
)


def gate_entry(name: str, status: str) -> dict[str, object]:
    return {
        "name": name,
        "status": status,
        "passed": status == "PASSED",
        "measured": None,
        "threshold": None,
        "message": "",
        "duration_s": 0.0,
    }


def gate_report(*pairs: tuple[str, str], ok: bool = True) -> dict[str, object]:
    """A gate report in the harness's shape. `test_the_embedded_gate_schema_is_the_harnesss`
    is what keeps this fixture honest as the harness evolves."""
    return {
        "schema": GATE_SCHEMA,
        "selection": "--all",
        "strict": False,
        "started_at": now(),
        "duration_s": 0.0,
        "summary": {"passed": 0, "failed": 0, "skipped": 0, "errored": 0},
        "ok": ok,
        "gates": [gate_entry(name, status) for name, status in pairs],
    }


@pytest.fixture()
def manifest() -> Manifest:
    python_version, machine = environment()
    return Manifest(
        version="v1",
        created_at=now(),
        git=Git(sha="0" * 40, branch="feat/phase-h", dirty=False),
        seeds={"pipeline": 42},
        packages={"numpy": "1.26.4", "mapie": None},
        python=python_version,
        platform=machine,
        contract={"features": [{"name": "temperature(K)", "statistic": None,
                                "table": None, "property": None, "dtype": "float64"}]},
        payloads=(PayloadRecord(name="model", file="model.joblib", sha256="ab" * 32, bytes=7),),
        gates=gate_report(("AC-2", "PASSED")),
        notes="written by a test",
    )


# --------------------------------------------------------------------------------------
# Round trip
# --------------------------------------------------------------------------------------


def test_the_manifest_round_trips_through_json(manifest: Manifest) -> None:
    """The L0 requirement in docs/QA-PROTOCOL.md, stated as a test."""
    restored = Manifest.from_dict(json.loads(json.dumps(manifest.to_dict())))
    assert restored == manifest


def test_the_round_trip_preserves_every_recorded_fact(manifest: Manifest) -> None:
    restored = Manifest.from_dict(json.loads(json.dumps(manifest.to_dict())))
    assert restored.git.sha == "0" * 40
    assert restored.git.dirty is False
    assert restored.seeds == {"pipeline": 42}
    # `null` is a recorded absence, not a missing key: reading an old manifest must be able to
    # tell "mapie was not installed" from "this store did not yet record mapie".
    assert restored.packages["mapie"] is None
    assert restored.feature_names == ("temperature(K)",)
    assert restored.notes == "written by a test"


def test_an_unknown_schema_is_refused_rather_than_guessed(manifest: Manifest) -> None:
    payload = manifest.to_dict()
    payload["schema"] = "hydms.artifacts/99"
    with pytest.raises(ManifestError, match="hydms.artifacts/99"):
        Manifest.from_dict(payload)


def test_a_missing_required_key_names_itself(manifest: Manifest) -> None:
    payload = manifest.to_dict()
    del payload["packages"]
    with pytest.raises(ManifestError, match="packages"):
        Manifest.from_dict(payload)


def test_a_malformed_payload_record_names_itself(manifest: Manifest) -> None:
    payload = manifest.to_dict()
    payload["payloads"] = [{"name": "model", "file": "model.joblib"}]
    with pytest.raises(ManifestError, match="sha256"):
        Manifest.from_dict(payload)


# --------------------------------------------------------------------------------------
# The gate verdict
# --------------------------------------------------------------------------------------


def test_the_embedded_gate_schema_is_the_harnesss() -> None:
    """`GATE_SCHEMA` is restated here rather than imported, to keep the dependency one-way.

    That restatement is only safe while this test exists: the day the harness bumps its schema,
    this fails and the manifest is updated in the same change rather than silently embedding a
    shape it can no longer read.
    """
    from hydms.gates._core import SCHEMA as HARNESS_SCHEMA

    assert GATE_SCHEMA == HARNESS_SCHEMA


def test_a_passing_run_leaves_nothing_unestablished(manifest: Manifest) -> None:
    assert manifest.gate_run_recorded
    assert manifest.unestablished() == ()


def test_a_skip_counts_as_unestablished(manifest: Manifest) -> None:
    """The point of the whole module. A skip is not a mild pass."""
    payload = manifest.to_dict()
    payload["gates"] = gate_report(("AC-2", "PASSED"), ("AC-3", "SKIPPED"))
    assert Manifest.from_dict(payload).unestablished() == (("AC-3", "SKIPPED"),)


def test_the_runs_own_ok_flag_is_not_consulted(manifest: Manifest) -> None:
    """`GateReport.ok` tolerates a skip under a broad selection, deliberately -- CI that is red
    for the length of the phase is CI nobody reads. An artifact about to be loaded into a
    prediction path is exactly where that leniency must not apply."""
    payload = manifest.to_dict()
    payload["gates"] = gate_report(("AC-3", "SKIPPED"), ok=True)
    restored = Manifest.from_dict(payload)
    assert restored.gates is not None and restored.gates["ok"] is True
    assert restored.unestablished() == (("AC-3", "SKIPPED"),)


@pytest.mark.parametrize("status", ["FAILED", "ERRORED", "SKIPPED"])
def test_every_non_passing_status_is_unestablished(manifest: Manifest, status: str) -> None:
    payload = manifest.to_dict()
    payload["gates"] = gate_report(("HG-1", status))
    assert Manifest.from_dict(payload).unestablished() == (("HG-1", status),)


def test_a_run_over_zero_gates_is_not_a_run(manifest: Manifest) -> None:
    payload = manifest.to_dict()
    payload["gates"] = gate_report()
    assert Manifest.from_dict(payload).gate_run_recorded is False


def test_no_gates_at_all_is_not_a_run(manifest: Manifest) -> None:
    payload = manifest.to_dict()
    payload["gates"] = None
    restored = Manifest.from_dict(payload)
    assert restored.gate_run_recorded is False
    assert restored.unestablished() == ()


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (["not", "a", "mapping"], "mapping"),
        ({"schema": "something/else", "gates": []}, "something/else"),
        ({"schema": GATE_SCHEMA}, "'gates' list"),
        ({"schema": GATE_SCHEMA, "gates": [{"name": "AC-2"}]}, "'name' and 'status'"),
    ],
)
def test_an_unreadable_gate_report_is_refused(payload: object, match: str) -> None:
    """Not "no gates" and not "all fine" -- unreadable, and said so at save time."""
    with pytest.raises(ManifestError, match=re.escape(match)):
        validate_gate_report(payload)


# --------------------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------------------


def test_git_provenance_is_read_from_this_checkout(repo_root: Path) -> None:
    if subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_root, capture_output=True, check=False,
    ).returncode != 0:
        pytest.skip("not a git work tree")

    git = describe_git(repo_root)
    assert git.known
    assert git.sha is not None and re.fullmatch(r"[0-9a-f]{40}", git.sha)
    assert git.dirty in (True, False)


def test_git_provenance_outside_a_repository_is_unknown_not_fatal(tmp_path: Path) -> None:
    """An installed package in a container has no work tree. Refusing to save an artifact for
    that reason would be worse than recording honestly that the provenance is unknown."""
    git = describe_git(tmp_path)
    if git.known:  # pragma: no cover - only if pytest's tmp dir sits inside a repository
        pytest.skip(f"{tmp_path} is inside a git work tree")
    assert git.sha is None
    assert git.dirty is None
    assert "not a work tree" in git.detail


def test_an_unknown_cleanliness_is_not_a_clean_one() -> None:
    """`git status` returns "" for a clean tree and the call returns None when it failed. The
    two must not collapse: `dirty=False` is a claim, `dirty=None` is the absence of one."""
    assert Git(sha="a" * 40, dirty=None).dirty is None
    assert Git(sha="a" * 40, dirty=False).dirty is False


def test_every_recorded_package_is_reported_present_or_absent() -> None:
    packages = resolved_packages()
    assert set(packages) == set(RECORDED_PACKAGES)
    assert all(value is None or isinstance(value, str) for value in packages.values())


def test_recorded_packages_covers_every_core_runtime_dependency(repo_root: Path) -> None:
    """A new core dependency that nothing records is a fitted model whose provenance is
    incomplete: a CatBoost or scikit-learn upgrade can change a fit from the same seed, which
    is the failure AC-1 exists to detect."""
    text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    block = text.split("\ndependencies = [", 1)[1].split("]", 1)[0]
    declared = {name.lower() for name in re.findall(r'"\s*([A-Za-z0-9_.\-]+)', block)}
    recorded = {name.lower() for name in RECORDED_PACKAGES}
    assert declared, "could not parse [project] dependencies out of pyproject.toml"
    assert declared <= recorded, (
        f"core dependencies not recorded in the manifest: {sorted(declared - recorded)}. "
        f"Add them to hydms.artifacts.manifest.RECORDED_PACKAGES."
    )


def test_the_schema_constant_is_written_into_every_manifest(manifest: Manifest) -> None:
    assert manifest.to_dict()["schema"] == SCHEMA


# --------------------------------------------------------------------------------------
# Digests
# --------------------------------------------------------------------------------------


def test_digest_file_reports_the_sha256_and_the_length(tmp_path: Path) -> None:
    import hashlib

    path = tmp_path / "payload.bin"
    blob = b"a trained model, notionally" * 1000
    path.write_bytes(blob)

    digest, size = digest_file(path)
    assert digest == hashlib.sha256(blob).hexdigest()
    assert size == len(blob)


def test_digest_file_reads_a_file_larger_than_one_chunk(tmp_path: Path) -> None:
    """The chunked read is what keeps the integrity check runnable on a real model rather than
    only on the small ones a test writes."""
    import hashlib

    path = tmp_path / "big.bin"
    blob = bytes(range(256)) * 8192  # 2 MiB, past the 1 MiB chunk
    path.write_bytes(blob)

    digest, size = digest_file(path)
    assert digest == hashlib.sha256(blob).hexdigest()
    assert size == len(blob)
