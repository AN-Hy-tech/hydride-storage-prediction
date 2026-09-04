"""The store's four promises: written once, one door, gates or no load, promotion is a pointer.

Every test here names a directory outright rather than using the configured one, so nothing in
this file can write into the repository's own `artifacts/`.

Card #4.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from hydms.artifacts import (
    ArtifactError,
    Artifacts,
    GatesIncomplete,
    Manifest,
    PayloadCorrupt,
    VersionNotFound,
    current,
    load,
    promote,
    read_manifest,
    save,
    version_dir,
    versions,
)
from hydms.gates._core import GateReport, GateResult

pytest.importorskip("joblib", reason="joblib is not installed in this interpreter")


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path: Path) -> Path:
    return tmp_path / "artifacts"


@pytest.fixture()
def contract() -> dict[str, Any]:
    """A contract payload in `FeatureContract.as_manifest()`'s shape.

    Deliberately not the real 22: most of what this file tests is the store, and the real
    contract pulls in pandas. `test_the_real_feature_contract_round_trips` uses the real one.
    """
    return {
        "features": [
            {"name": "avg_polzbl_divi_atom_mass", "statistic": "avg",
             "table": "jarvis", "property": "polzbl_divi_atom_mass", "dtype": "float64"},
            {"name": "temperature(K)", "statistic": None,
             "table": None, "property": None, "dtype": "float64"},
        ]
    }


def report(*pairs: tuple[str, str]) -> GateReport:
    """A real `GateReport`, so this file cannot drift from the shape the harness writes."""
    builders = {
        "PASSED": lambda name: GateResult.ok(name, "established"),
        "SKIPPED": lambda name: GateResult.skip(name, "not implemented"),
        "FAILED": lambda name: GateResult.fail(name, "did not hold"),
    }
    return GateReport(
        results=tuple(builders[status](name) for name, status in pairs),
        selection="--all",
        strict=False,
        started_at="2026-09-04T00:00:00+00:00",
        duration_s=0.0,
    )


GREEN = (("AC-2", "PASSED"), ("HG-1", "PASSED"))


@pytest.fixture()
def green(store: Path, contract: dict[str, Any]) -> Manifest:
    """A saved v1 whose gates all passed — the only kind that loads or promotes."""
    return save(
        {"model": {"trees": 100}, "scaler": {"centre": 1.0}},
        contract=contract,
        seeds={"pipeline": 42},
        gates=report(*GREEN),
        store=store,
    )


# --------------------------------------------------------------------------------------
# The round trip
# --------------------------------------------------------------------------------------


def test_save_then_load_returns_the_objects_that_went_in(store: Path, green: Manifest) -> None:
    bundle = load("v1", store=store)
    assert isinstance(bundle, Artifacts)
    assert bundle.version == "v1"
    assert bundle["model"] == {"trees": 100}
    assert bundle["scaler"] == {"centre": 1.0}
    assert bundle.names == ("model", "scaler")


def test_each_payload_becomes_one_named_file(store: Path, green: Manifest) -> None:
    files = sorted(path.name for path in (store / "v1").iterdir())
    assert files == ["manifest.json", "model.joblib", "scaler.joblib"]


def test_the_bundle_names_what_it_holds_when_asked_for_something_else(
    store: Path, green: Manifest
) -> None:
    bundle = load("v1", store=store)
    with pytest.raises(KeyError, match="model, scaler"):
        bundle["calibrator"]
    assert bundle.get("calibrator") is None
    assert "scaler" in bundle
    assert len(bundle) == 2


# --------------------------------------------------------------------------------------
# What the manifest records
# --------------------------------------------------------------------------------------


def test_the_manifest_records_the_five_things_the_card_names(
    store: Path, green: Manifest
) -> None:
    manifest = read_manifest(store / "v1")
    assert manifest.git.sha is None or len(manifest.git.sha) == 40   # a tmp dir has no work tree
    assert manifest.seeds == {"pipeline": 42}
    assert "catboost" in manifest.packages
    assert manifest.feature_names == ("avg_polzbl_divi_atom_mass", "temperature(K)")
    assert manifest.gates is not None
    assert [entry["name"] for entry in manifest.gates["gates"]] == ["AC-2", "HG-1"]


def test_the_manifest_is_readable_without_loading_any_payload(
    store: Path, green: Manifest
) -> None:
    """CI asks "did its gates pass?" on a bare interpreter; that must not need joblib or the
    memory to hold a model."""
    manifest = read_manifest(store / "v1")
    assert manifest.version == "v1"
    assert manifest.unestablished() == ()


def test_the_seed_defaults_to_the_configured_one(store: Path, contract: dict[str, Any]) -> None:
    save({"model": 1}, contract=contract, gates=report(*GREEN), store=store)
    from hydms.config import load as load_config

    assert read_manifest(store / "v1").seeds == {"pipeline": load_config().seed}


def test_a_seed_that_is_not_an_integer_is_refused(
    store: Path, contract: dict[str, Any]
) -> None:
    with pytest.raises(ArtifactError, match="not integers"):
        save({"model": 1}, contract=contract, seeds={"pipeline": "42"}, store=store)  # type: ignore[dict-item]


def test_a_contract_is_not_optional(store: Path) -> None:
    with pytest.raises(ArtifactError, match="features"):
        save({"model": 1}, contract={"nothing": "useful"}, store=store)


# --------------------------------------------------------------------------------------
# Written once
# --------------------------------------------------------------------------------------


def test_the_first_version_is_v1_and_the_next_is_v2(
    store: Path, contract: dict[str, Any]
) -> None:
    assert save({"model": 1}, contract=contract, store=store).version == "v1"
    assert save({"model": 2}, contract=contract, store=store).version == "v2"
    assert versions(store=store) == ("v1", "v2")


def test_versions_sort_numerically_not_lexicographically(
    store: Path, contract: dict[str, Any]
) -> None:
    """A string sort puts v10 before v9 and promotes the wrong artifact on the tenth retrain."""
    save({"model": 9}, contract=contract, version="v9", store=store)
    assert save({"model": 10}, contract=contract, store=store).version == "v10"
    assert versions(store=store) == ("v9", "v10")


def test_an_existing_version_is_never_overwritten(store: Path, green: Manifest) -> None:
    with pytest.raises(ArtifactError, match="written once"):
        save({"model": 2}, contract={"features": []}, version="v1", store=store)
    assert load("v1", store=store)["model"] == {"trees": 100}


def test_a_number_left_by_a_half_written_run_is_never_reused(
    store: Path, contract: dict[str, Any]
) -> None:
    """`versions()` ignores a directory with no manifest, but `save` must not hand its number
    to a second run: two different artifacts under one name is worse than a gap."""
    store.mkdir(parents=True)
    (store / "v1").mkdir()
    assert versions(store=store) == ()
    assert save({"model": 1}, contract=contract, store=store).version == "v2"


def test_a_save_that_fails_leaves_nothing_behind(
    store: Path, contract: dict[str, Any]
) -> None:
    with pytest.raises(Exception):  # noqa: B017 - joblib's own error type is not the point
        save({"model": lambda x: x}, contract=contract, store=store)
    assert versions(store=store) == ()
    assert not (store / "v1").exists()
    assert list(store.iterdir()) == []


@pytest.mark.parametrize("name", ["Model", "../escape", "model.joblib", "2model", ""])
def test_a_payload_name_that_is_not_a_plain_identifier_is_refused(
    store: Path, contract: dict[str, Any], name: str
) -> None:
    with pytest.raises(ArtifactError, match="file names"):
        save({name: 1}, contract=contract, store=store)


def test_a_version_with_no_payloads_records_provenance_for_nothing(
    store: Path, contract: dict[str, Any]
) -> None:
    with pytest.raises(ArtifactError, match="no payloads"):
        save({}, contract=contract, store=store)


# --------------------------------------------------------------------------------------
# Gates or no load
# --------------------------------------------------------------------------------------


def test_a_version_whose_gates_all_passed_loads_by_default(
    store: Path, green: Manifest
) -> None:
    assert load("v1", store=store).version == "v1"


def test_a_skipped_gate_stops_the_load_and_names_itself(
    store: Path, contract: dict[str, Any]
) -> None:
    save({"model": 1}, contract=contract, gates=report(("AC-2", "PASSED"), ("AC-3", "SKIPPED")),
         store=store)
    with pytest.raises(GatesIncomplete, match="AC-3 SKIPPED"):
        load("v1", store=store)


def test_a_failed_gate_stops_the_load(store: Path, contract: dict[str, Any]) -> None:
    save({"model": 1}, contract=contract, gates=report(("HG-1", "FAILED")), store=store)
    with pytest.raises(GatesIncomplete, match="HG-1 FAILED"):
        load("v1", store=store)


def test_a_version_with_no_gate_run_at_all_does_not_load(
    store: Path, contract: dict[str, Any]
) -> None:
    save({"model": 1}, contract=contract, store=store)
    with pytest.raises(GatesIncomplete, match="records no gate run"):
        load("v1", store=store)


def test_require_gates_false_is_the_only_way_past(
    store: Path, contract: dict[str, Any]
) -> None:
    """The escape hatch exists for the card that has just written a version and wants it back.
    It is a keyword at the call site precisely so it is visible in a diff."""
    save({"model": 1}, contract=contract, store=store)
    assert load("v1", store=store, require_gates=False)["model"] == 1


def test_a_gate_report_the_store_cannot_read_is_refused_at_save_time(
    store: Path, contract: dict[str, Any]
) -> None:
    from hydms.artifacts import ManifestError

    with pytest.raises(ManifestError, match="schema"):
        save({"model": 1}, contract=contract, gates={"gates": []}, store=store)
    assert versions(store=store) == ()


# --------------------------------------------------------------------------------------
# Promotion is a pointer
# --------------------------------------------------------------------------------------


def test_nothing_is_promoted_until_something_is(store: Path, green: Manifest) -> None:
    assert current(store=store) is None
    with pytest.raises(VersionNotFound, match="nothing is promoted"):
        load(store=store)


def test_promotion_makes_load_with_no_version_work(store: Path, green: Manifest) -> None:
    assert promote("v1", store=store) == "v1"
    assert current(store=store) == "v1"
    assert load(store=store).version == "v1"


def test_promotion_refuses_a_version_its_gates_did_not_establish(
    store: Path, contract: dict[str, Any]
) -> None:
    save({"model": 1}, contract=contract, gates=report(("AC-3", "SKIPPED")), store=store)
    with pytest.raises(GatesIncomplete, match="AC-3 SKIPPED"):
        promote("v1", store=store)
    assert current(store=store) is None


def test_rollback_is_one_small_write(store: Path, contract: dict[str, Any]) -> None:
    """Card #7's claim, made structural: reverting to the previous version is a pointer move,
    not a retrain."""
    save({"model": "old"}, contract=contract, gates=report(*GREEN), store=store)
    save({"model": "new"}, contract=contract, gates=report(*GREEN), store=store)

    promote("v2", store=store)
    assert load(store=store)["model"] == "new"
    promote("v1", store=store)
    assert load(store=store)["model"] == "old"


def test_the_pointer_records_when_it_was_moved(store: Path, green: Manifest) -> None:
    promote("v1", store=store)
    pointer = json.loads((store / "current.json").read_text(encoding="utf-8"))
    assert pointer["version"] == "v1"
    assert pointer["promoted_at"].startswith("20")


def test_a_pointer_naming_a_version_that_is_gone_says_so(
    store: Path, green: Manifest
) -> None:
    promote("v1", store=store)
    (store / "current.json").write_text(json.dumps({"version": "v7"}), encoding="utf-8")
    with pytest.raises(VersionNotFound, match="v7"):
        load(store=store)


def test_an_unreadable_pointer_is_not_silently_ignored(store: Path, green: Manifest) -> None:
    store.mkdir(parents=True, exist_ok=True)
    (store / "current.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ArtifactError, match="records no version"):
        current(store=store)


# --------------------------------------------------------------------------------------
# Integrity
# --------------------------------------------------------------------------------------


def test_a_tampered_payload_is_refused_rather_than_unpickled(
    store: Path, green: Manifest
) -> None:
    """A truncated or edited model otherwise unpickles into something that still predicts."""
    path = store / "v1" / "model.joblib"
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(PayloadCorrupt, match="does not match the manifest"):
        load("v1", store=store)


def test_a_missing_payload_file_is_refused(store: Path, green: Manifest) -> None:
    (store / "v1" / "scaler.joblib").unlink()
    with pytest.raises(PayloadCorrupt, match="scaler"):
        load("v1", store=store)


@pytest.mark.parametrize("name", ["current", "v", "v1.0", "latest", "V1"])
def test_a_name_that_is_not_a_version_is_refused(store: Path, name: str) -> None:
    with pytest.raises(VersionNotFound, match="not an artifact version"):
        version_dir(name, store=store)


def test_asking_for_a_version_that_was_never_saved_lists_the_ones_there_are(
    store: Path, green: Manifest
) -> None:
    with pytest.raises(VersionNotFound, match="Versions present: v1"):
        load("v4", store=store)


# --------------------------------------------------------------------------------------
# The feature contract, which is why AC-4 exists
# --------------------------------------------------------------------------------------


def test_the_real_feature_contract_round_trips(store: Path) -> None:
    pytest.importorskip("pandas", reason="the contract module imports pandas")
    from hydms.descriptors.contract import CONTRACT

    save({"model": 1}, contract=CONTRACT, gates=report(*GREEN), store=store)
    bundle = load("v1", store=store)

    assert bundle.feature_names == CONTRACT.names
    assert bundle.contract() == CONTRACT


def test_an_edited_feature_list_is_caught_by_the_contracts_own_digest(store: Path) -> None:
    """The failure this whole record exists for: a model fed a matrix built to a different
    contract returns plausible, wrong numbers instead of an error (AC-4)."""
    pytest.importorskip("pandas", reason="the contract module imports pandas")
    from hydms.descriptors.contract import CONTRACT, ContractError

    save({"model": 1}, contract=CONTRACT, gates=report(*GREEN), store=store)

    path = store / "v1" / "manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload["contract"]["features"]
    features[0], features[1] = features[1], features[0]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # The bundle still loads: the payload files are untouched, and the store does not digest
    # the manifest itself. The contract does, which is the check that matters.
    bundle = load("v1", store=store)
    with pytest.raises(ContractError, match="digest"):
        bundle.contract()
