"""Gate HG-4 -- ruff, mypy and the coverage floor on ``hydms/``.

Three of these build a *fake checkout* under ``tmp_path`` and point the gate at it, rather
than asserting against this repository. That is deliberate and it is the only way the red
cases can be tested at all: this repository is green, and a test that could only observe the
green case would never have seen the gate fail. ``docs/QA-PROTOCOL.md`` section 5 asks for
exactly that -- make it red on purpose, and record that you did.

What a fake checkout has to contain is itself informative: a ``pyproject.toml`` (the gate
refuses without one), a ``hydms/`` tree for ruff and mypy to read, and whatever coverage
configuration the third leg needs. Nothing else -- the gate takes its whole world from
``cfg.root``.

Card #86.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from hydms.config import Config, load
from hydms.gates import Pending, Speed, Status, registry
from hydms.gates.hg4_hygiene import GATE

CLEAN = "def add(left: int, right: int) -> int:\n    return left + right\n"

#: An unused import. F401 is in ruff's default `F` selection and this repository enables it.
RUFF_DIRTY = "import os\n\n\ndef add(left: int, right: int) -> int:\n    return left + right\n"

#: Returns a str where the annotation promises an int. mypy alone catches this; ruff does not.
MYPY_DIRTY = 'def add(left: int, right: int) -> int:\n    return "not an int"\n'

PYPROJECT = """
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.mypy]
python_version = "3.10"
files = ["hydms"]
disallow_untyped_defs = true

[tool.coverage.report]
fail_under = 80
"""


@pytest.fixture
def checkout(tmp_path: Path):
    """A factory: write one module into a fake checkout, get a ``Config`` pointed at it."""

    def _make(source: str) -> Config:
        (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
        package = tmp_path / "hydms"
        package.mkdir(exist_ok=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "sample.py").write_text(source, encoding="utf-8")
        return replace(load(), root=tmp_path)

    return _make


def test_hg4_is_registered_implemented_and_fast() -> None:
    """The registry is the list of what this project promises to check, so being *in* it is
    not the claim -- being implemented is. HG-4 was `Pending` until card #86."""
    registered = {gate.name: gate for gate in registry()}
    assert "HG-4" in registered
    gate = registered["HG-4"]
    assert not isinstance(gate, Pending), "HG-4 is registered but still unimplemented"
    assert gate.speed is Speed.FAST
    assert gate.card == 86


def test_a_checkout_with_no_pyproject_is_a_loud_skip(tmp_path: Path) -> None:
    """An installed wheel is not a checkout. The honest answer is 'not established'."""
    result = GATE.check(replace(load(), root=tmp_path))
    assert result.status is Status.SKIPPED
    assert "pyproject.toml" in result.message


@pytest.mark.skipif(shutil.which("ruff") is None, reason="ruff is not on PATH")
def test_a_ruff_violation_is_a_failure_that_names_ruff(checkout) -> None:
    result = GATE.check(checkout(RUFF_DIRTY))
    assert result.status is Status.FAILED
    assert "ruff" in result.message
    # The violation itself has to survive into the message: a red gate that does not say what
    # is wrong costs the next person the run again (`GateResult`'s own contract).
    assert "F401" in result.message


@pytest.mark.skipif(shutil.which("mypy") is None, reason="mypy is not on PATH")
def test_a_type_error_is_a_failure_that_names_mypy(checkout) -> None:
    """Deliberately a fault ruff cannot see, so the leg under test is the one that reports."""
    result = GATE.check(checkout(MYPY_DIRTY))
    assert result.status is Status.FAILED
    assert "mypy" in result.message
    assert "ruff" not in result.message.split("failed on this checkout")[0]


@pytest.mark.skipif(
    shutil.which("ruff") is None or shutil.which("mypy") is None, reason="lint tools absent"
)
def test_clean_code_with_no_coverage_data_skips_rather_than_passing(checkout) -> None:
    """The third leg is unanswerable in a checkout nobody has run the suite in.

    A skip rather than a pass, and that asymmetry is the whole point of the harness: "the
    floor was not measured" and "the floor holds" must not look alike.
    """
    result = GATE.check(checkout(CLEAN))
    assert result.status is Status.SKIPPED
    assert "coverage" in result.message


@pytest.mark.skipif(
    shutil.which("ruff") is None or shutil.which("mypy") is None, reason="lint tools absent"
)
def test_stale_coverage_data_is_not_a_verdict(checkout) -> None:
    """Data written before the code it claims to measure establishes nothing.

    This is not hypothetical: `pytest --cov` writes its data file only when the run *ends*,
    so a gate running inside that suite reads the previous run's file. Reporting a number
    from it would be a verdict about code that no longer exists.
    """
    pytest.importorskip("coverage", reason="the floor is read through coverage's own API")
    cfg = checkout(CLEAN)
    data = cfg.root / ".coverage"
    data.write_bytes(b"")

    # Make the source unambiguously newer than the data file.
    import os
    import time

    stamp = time.time()
    os.utime(data, (stamp - 60, stamp - 60))
    os.utime(cfg.root / "hydms" / "sample.py", (stamp, stamp))

    result = GATE.check(cfg)
    assert result.status is Status.SKIPPED
    assert "before the most recent change" in result.message


def test_the_real_repository_is_answered_without_erroring() -> None:
    """Whatever the verdict here, the gate must not raise: an ERRORED gate is a broken gate.

    This is the one test that runs against this checkout, and it deliberately asserts nothing
    about pass-or-fail -- that depends on whether anyone has run `pytest --cov` recently,
    which is a fact about the machine and not about the code.
    """
    result = GATE.check(load())
    assert result.status is not Status.ERRORED
    assert result.name == "HG-4"
