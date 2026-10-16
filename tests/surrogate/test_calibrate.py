"""Card #96 — ``calibrate --report`` is an input path too, and ``--save`` must not hide that.

``--report`` names the directory the tables are written to **and** the one
``model-chosen.csv`` is read from. Pointed at a scratch directory, the fit used to fall back to
CatBoost's own defaults, print one sentence about it, exit 0, and -- with ``--save`` -- persist
that smoke test as a version whose manifest says ``deployed fit``. It happened once, on
2026-09-07, and was caught only because somebody read the sentence.

**The sentence is not what is asserted here.** It existed before the fix and the defect survived
it. What is asserted is the chosen path: with no configuration to read, ``--save`` returns the
bad-invocation code **before** anything is stamped, featurised or fitted, and writes nothing. And
the two neighbouring paths stay open -- a smoke run without ``--save``, and ``--save`` with a
configuration on disk -- so the refusal cannot pass by refusing everything.

Nothing here fits. The first step past the refusal is replaced by a sentinel that raises, which
is how "the run went on" is observed without paying for CatBoost.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest
from hydms.surrogate import calibrate
from hydms.surrogate.deploy import CHOSEN
from hydms.surrogate.model import PARAM_PREFIX


class _WentOn(Exception):
    """Raised by the first step past the refusal: the run was not refused."""


def _went_on(*_args: object, **_kwargs: object) -> None:
    raise _WentOn


def _forbidden(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("a refused --save reached a step it must never reach")


@pytest.fixture
def guarded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every expensive or persisting step fails the test if a refusal reaches it."""
    monkeypatch.setattr(calibrate.provenance, "begin", _forbidden)
    monkeypatch.setattr(calibrate, "capacity_matrix", _forbidden)
    monkeypatch.setattr(calibrate, "deployed_fit", _forbidden)
    monkeypatch.setattr(calibrate, "save_deployed", _forbidden)


def _no_table(directory: Path) -> None:
    """The case that happened: a scratch ``--report`` with nothing in it."""


def _empty_table(directory: Path) -> None:
    pd.DataFrame(columns=["fold", "objective"]).to_csv(directory / CHOSEN, index=False)


def _no_params(directory: Path) -> None:
    """A table from a ``train`` that predates the ``param.`` prefix."""
    pd.DataFrame({"fold": ["outer-0"], "objective": [0.1], "depth": [6]}).to_csv(
        directory / CHOSEN, index=False
    )


@pytest.mark.parametrize("left", [_no_table, _empty_table, _no_params], ids=lambda f: f.__name__)
def test_save_is_refused_before_the_fit_when_no_configuration_was_read(
    tmp_path: Path,
    guarded: None,
    left: object,
    capsys: pytest.CaptureFixture[str],
) -> None:
    left(tmp_path)  # type: ignore[operator]
    before = sorted(tmp_path.iterdir())

    code = calibrate.main(["--report", str(tmp_path), "--save"], out=io.StringIO())

    assert code == calibrate.EXIT_BAD_INVOCATION
    assert sorted(tmp_path.iterdir()) == before, "a refusal wrote into the report directory"
    err = capsys.readouterr().err
    assert "refusing --save" in err
    assert str(tmp_path / CHOSEN) in err


def test_a_smoke_run_without_save_is_still_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Defaults without ``--save`` is a legitimate probe of the calibration path."""
    monkeypatch.setattr(calibrate.provenance, "begin", _went_on)

    with pytest.raises(_WentOn):
        calibrate.main(["--report", str(tmp_path)], out=io.StringIO())


def test_save_goes_on_when_a_configuration_is_on_disk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pd.DataFrame({"fold": ["outer-0"], "objective": [0.1], f"{PARAM_PREFIX}depth": [6]}).to_csv(
        tmp_path / CHOSEN, index=False
    )
    monkeypatch.setattr(calibrate.provenance, "begin", _went_on)

    with pytest.raises(_WentOn):
        calibrate.main(["--report", str(tmp_path), "--save"], out=io.StringIO())
