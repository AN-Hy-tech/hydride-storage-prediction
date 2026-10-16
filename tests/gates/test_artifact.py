"""Card #33 — the door two gates use to reach a version that has no gates yet.

The knot: :func:`~hydms.surrogate.predict.load_surrogate` refuses a version whose gate run is
unestablished, and the first thing ever recorded against a freshly-saved version is a gate run.
Three ways out were written up on the card. The one taken splits ``load_surrogate`` rather than
weakening it — :func:`~hydms.surrogate.predict.surrogate_from` is everything below the version
lookup, and the gates load the bundle themselves with ``require_gates=False``.

That decision is only worth anything if it cannot quietly widen, so this file pins both sides:
the gates' door opens on an ungated version, and the delivery path's does not, **and the two
produce the same object** — otherwise AC-4 would be certifying a second assembly of the
prediction path rather than the one that ships.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")

from hydms import artifacts  # noqa: E402
from hydms.artifacts import GatesIncomplete  # noqa: E402
from hydms.gates._artifact import NoCandidate, candidate  # noqa: E402
from hydms.gates._core import GateReport, GateResult  # noqa: E402
from hydms.surrogate.predict import Surrogate, load_surrogate, surrogate_from  # noqa: E402

pytestmark = pytest.mark.gate


def _green() -> GateReport:
    return GateReport(
        results=(GateResult.ok("AC-3", "established"), GateResult.ok("AC-4", "established")),
        selection="--all",
        strict=False,
        started_at="2026-09-06T00:00:00+00:00",
        duration_s=0.0,
    )


# --------------------------------------------------------------------------------------
# The door opens where the delivery path's does not
# --------------------------------------------------------------------------------------


def test_a_version_with_no_gate_report_is_reachable_here_and_nowhere_else(
    deployed, pointed_at
) -> None:
    cfg, settings, _frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)

    scored = candidate(config)
    assert isinstance(scored.surrogate, Surrogate)
    assert scored.version == "v1"
    assert not scored.promoted

    with pytest.raises(GatesIncomplete):
        load_surrogate("v1", store=config.paths.artifacts)


def test_the_gate_and_the_delivery_path_assemble_the_same_object(deployed, pointed_at) -> None:
    """The whole justification for splitting rather than flagging.

    If these two ever diverged, AC-4 would be certifying something the search layer never
    calls, which is precisely the duplication AC-4 exists to catch — arriving in the checker.
    """
    cfg, settings, _frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)
    store = config.paths.artifacts

    through_the_gate = candidate(config).surrogate
    directly = surrogate_from(artifacts.load("v1", store=store, require_gates=False))

    assert through_the_gate.version == directly.version
    assert through_the_gate.feature_names == directly.feature_names
    assert through_the_gate.quantiles == directly.quantiles
    assert through_the_gate.confidence_level == directly.confidence_level


# --------------------------------------------------------------------------------------
# Which version
# --------------------------------------------------------------------------------------


def test_the_promoted_version_wins_over_the_newest(deployed, pointed_at) -> None:
    """After card #34 promotes, a gate that scored a later candidate would certify the wrong
    model. Before it promotes, the newest *is* the candidate — the other test above."""
    cfg, settings, _frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)
    store = config.paths.artifacts

    from hydms.surrogate.deploy import save_deployed

    save_deployed(fit, settings=settings, store=store, notes="a second, later version")
    assert artifacts.versions(store=store) == ("v1", "v2")

    assert candidate(config).version == "v2", "nothing promoted: the newest is the candidate"

    from hydms.descriptors.contract import FeatureContract

    artifacts.save(
        fit.payloads,
        contract=FeatureContract.from_names(fit.model.feature_names),
        gates=_green(),
        store=store,
        version="v3",
    )
    artifacts.promote("v3", store=store)
    scored_at = candidate(config)
    assert scored_at.version == "v3" and scored_at.promoted
    assert "promoted" in scored_at.provenance


def test_an_empty_store_names_the_command_that_fills_it(deployed, tmp_path: Path) -> None:
    cfg, *_ = deployed
    empty = replace(cfg, paths=replace(cfg.paths, artifacts=tmp_path / "nothing"))
    with pytest.raises(NoCandidate) as absent:
        candidate(empty)
    assert "hydms.surrogate.calibrate" in str(absent.value)
    assert "A gate over no artifact is not a pass" in str(absent.value)


def test_a_clone_without_lfs_payloads_has_no_candidate_rather_than_a_broken_one(
    deployed, tmp_path: Path
) -> None:
    """Card #7. The CI fast lane checks out without `git lfs pull`: SKIPPED, not ERRORED."""
    from hydms.descriptors.contract import FeatureContract

    cfg, _settings, _frame, _split, fit = deployed
    store = tmp_path / "artifacts"
    artifacts.save(
        fit.payloads,
        contract=FeatureContract.from_names(fit.model.feature_names),
        gates=_green(),
        store=store,
    )
    for payload in (store / "v1").glob("*.joblib"):
        payload.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:00\nsize 1\n")
    pointed = replace(cfg, paths=replace(cfg.paths, artifacts=store))
    with pytest.raises(NoCandidate) as absent:
        candidate(pointed)
    assert "git lfs pull" in str(absent.value)
    assert isinstance(absent.value.__cause__, artifacts.PayloadNotFetched)
