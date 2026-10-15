"""Card #31 — the coverage gate, and the four things it has to get right.

1. **It measures coverage on the held-out split and nowhere else.** ``calibrate`` reports on the
   calibration rows and refuses to look at ``test``; AC-3 is the one place ``test`` is read, and
   the rows it scores are asserted to be exactly that split.
2. **It reports three numbers, not a boolean.** Calibrated coverage, raw coverage on the same
   rows, and the binomial standard error at this ``n``. The card's third box — "failure reports
   measured vs nominal coverage, not just a boolean" — is a statement about the passing message
   too, because a green gate whose number nobody can see is a green gate nobody can audit.
3. **It goes red on purpose.** ``docs/QA-PROTOCOL.md`` §5 will not trust a gate that has never
   failed, and a gate over a calibration that is correct by construction never fails by itself.
   So a version is stored whose correction has been destroyed, and the gate is required to catch
   it and to say which way the band is wrong.
4. **It scores against the artifact's nominal level, not the file's.** A configuration edited
   after the fit must not be able to move the bar; the version carries the level its correction
   targeted and the gate says so out loud when the two disagree.
"""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("pandas", reason="the surrogate layer is pandas frames end to end")
pytest.importorskip("joblib", reason="the artifact store persists through joblib")

from hydms.gates import Status  # noqa: E402
from hydms.gates.ac3_conformal_coverage import (  # noqa: E402
    GATE,
    HELD_OUT,
    TOLERANCE,
    _standard_error,
)

pytestmark = pytest.mark.gate


@pytest.fixture
def scored(deployed, pointed_at):
    """The gate's result over one real, cheap, ungated artifact version."""
    cfg, settings, _frame, _split, fit = deployed
    return GATE.check(pointed_at(fit, cfg, settings))


# --------------------------------------------------------------------------------------
# What it establishes
# --------------------------------------------------------------------------------------


def test_coverage_is_measured_and_reported_against_the_nominal_level(scored, deployed) -> None:
    _cfg, _settings, _frame, _split, fit = deployed
    assert isinstance(scored.measured, float)
    assert 0.0 <= scored.measured <= 1.0
    assert scored.threshold == fit.conformal.confidence_level


def test_it_scores_the_test_split_and_says_how_many_rows(scored, deployed) -> None:
    _cfg, _settings, _frame, split, _fit = deployed
    assert f"{int((split == HELD_OUT).sum())} held-out row(s) in {HELD_OUT!r}" in scored.message


def test_it_reports_the_raw_band_beside_the_calibrated_one(scored) -> None:
    """The gap card #27 exists to close, measured on rows nothing was fitted on.

    A green AC-3 that did not show this would establish that the band is honest without ever
    saying what the calibration bought — which is the number Chapter 1 quotes.
    """
    assert "Raw (the same heads, correction not applied)" in scored.message
    assert "Calibrated: coverage" in scored.message


def test_it_reports_the_standard_error_so_a_near_miss_is_readable(scored) -> None:
    assert "Binomial standard error" in scored.message


def test_the_tolerance_is_about_two_standard_errors_at_this_test_size(deployed) -> None:
    """Why 0.05 and not 0.02: the bar has to sit above the noise it is measured through."""
    _cfg, _settings, _frame, split, fit = deployed
    error = _standard_error(fit.conformal.confidence_level, int((split == HELD_OUT).sum()))
    assert error < TOLERANCE < 3.0 * error


def test_it_names_the_version_it_scored(scored) -> None:
    assert "v1" in scored.message


# --------------------------------------------------------------------------------------
# It goes red on purpose
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("correction", "direction"),
    [(-4.0, "Under-covering"), (4.0, "Over-covering")],
)
def test_a_destroyed_correction_is_caught_and_the_direction_named(
    deployed, pointed_at, correction: float, direction: str
) -> None:
    """A correction of ±4 in ``log1p`` space is a band that is absurd in one direction.

    Injected into the stored payload rather than into the arithmetic, because that is where it
    would really go wrong: the correction is a number in an artifact, and a version that
    carries the wrong one loads, predicts and answers without raising anything.
    """
    cfg, settings, _frame, _split, fit = deployed
    broken = replace(fit, conformal=replace(fit.conformal, correction=correction))
    result = GATE.check(pointed_at(broken, cfg, settings))

    assert result.status is Status.FAILED, result.message
    assert direction in result.message, result.message
    assert abs(result.measured - result.threshold) > TOLERANCE
    assert "risk R1" in result.message


def test_the_failure_reports_the_measured_number_not_only_that_it_failed(
    deployed, pointed_at
) -> None:
    cfg, settings, _frame, _split, fit = deployed
    broken = replace(fit, conformal=replace(fit.conformal, correction=-4.0))
    result = GATE.check(pointed_at(broken, cfg, settings))
    assert f"{result.measured:.4f}" in result.message
    assert isinstance(result.measured, float) and isinstance(result.threshold, float)


# --------------------------------------------------------------------------------------
# The level comes from the artifact, never from the file
# --------------------------------------------------------------------------------------


def test_a_config_edited_after_the_fit_cannot_move_the_bar(deployed, pointed_at) -> None:
    """The artifact's own level governs, and the drift is reported rather than absorbed."""
    cfg, settings, _frame, _split, fit = deployed
    config = pointed_at(fit, cfg, settings)
    edited = replace(config, conformal=replace(config.conformal, confidence_level=0.95))

    result = GATE.check(edited)

    assert result.threshold == fit.conformal.confidence_level
    assert not math.isclose(result.threshold, 0.95)
    assert "The file changed after the fit" in result.message


# --------------------------------------------------------------------------------------
# No artifact is a skip, never a pass
# --------------------------------------------------------------------------------------


def test_an_empty_store_is_skipped_with_the_command_that_fixes_it(deployed, tmp_path: Path) -> None:
    cfg, *_ = deployed
    empty = replace(cfg, paths=replace(cfg.paths, artifacts=tmp_path / "nothing"))
    result = GATE.check(empty)
    assert result.status is Status.SKIPPED
    assert "A gate over no artifact is not a pass" in result.message
