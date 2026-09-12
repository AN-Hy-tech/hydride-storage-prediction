"""Tests for `python -m hydms.gates`.

The exit code is the whole contract as far as CI is concerned, so that is what these check.
Everything a workflow file can get wrong -- a mistyped gate name, no selection at all, a
config that will not load -- must exit non-zero rather than quietly reporting a green run
over nothing.

Card #5.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hydms.config import load
from hydms.gates import Speed, Status, registry, run, select
from hydms.gates.__main__ import EXIT_BAD_INVOCATION, EXIT_GATE_FAILED, EXIT_OK, main, summarise


def test_list_exits_zero_and_names_every_gate(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["list"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "12 gates registered." in out
    assert "AC-2" in out and "HG-4" in out


def test_run_all_is_green_while_the_phase_is_unwritten(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CI that is permanently red is CI that is permanently ignored -- but the run must say
    plainly what it did not establish."""
    assert main(["run", "--all", "--no-report"]) == EXIT_OK
    assert "NOT CHECKED" in capsys.readouterr().out


def test_run_all_strict_is_red(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "--all", "--strict", "--no-report"]) == EXIT_GATE_FAILED


def test_naming_an_unimplemented_gate_is_red(
    capsys: pytest.CaptureFixture[str], unwritten
) -> None:
    """The runnable check on cards #31, #32, #33, #71, #77 and #79 is exactly this
    invocation. It must not report success before the card that owns it has landed.

    The gate is taken from the registry rather than named, so landing one does not quietly
    turn this test into a test of that gate -- which is what card #21 did to it.
    """
    assert main(["run", unwritten[0].name, "--no-report"]) == EXIT_GATE_FAILED


def test_an_unknown_gate_name_is_a_bad_invocation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "AC-42", "--no-report"]) == EXIT_BAD_INVOCATION
    assert "no gate named" in capsys.readouterr().err


def test_selecting_nothing_is_a_bad_invocation(capsys: pytest.CaptureFixture[str]) -> None:
    """`run` with no lane and no names must not be read as 'run everything'."""
    assert main(["run", "--no-report"]) == EXIT_BAD_INVOCATION
    assert "nothing selected" in capsys.readouterr().err


def test_an_unreadable_config_is_a_bad_invocation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "not-a-config.yaml"
    bad.write_text("seed: 42\n", encoding="utf-8")
    assert main(["run", "--all", "--config", str(bad), "--no-report"]) == EXIT_BAD_INVOCATION
    assert "configuration error" in capsys.readouterr().err


def test_the_fast_lane_excludes_the_gates_that_need_a_retrain(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["run", "--fast", "--no-report"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "HG-1" in out
    assert "AC-1" not in out, "AC-1 needs two full training runs; it belongs to the slow lane"


def test_a_report_is_written_where_it_is_asked_for(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "gate-results.json"
    assert main(["run", "--all", "--report", str(destination)]) == EXIT_OK

    written = json.loads(destination.read_text(encoding="utf-8"))
    assert written["selection"] == "--all"
    assert sum(written["summary"].values()) == len(registry())
    assert written["summary"]["failed"] == 0 and written["summary"]["errored"] == 0
    assert str(destination) in capsys.readouterr().out


def test_summary_is_appended_where_it_is_asked_for(tmp_path: Path) -> None:
    """`--summary` is what gives `summarise()` a consumer: CI's `$GITHUB_STEP_SUMMARY`.

    It appends rather than truncates, because a step summary is accumulated by every step in
    the job and rewriting it would delete what ran before. Card #86.
    """
    destination = tmp_path / "summary" / "step.md"
    destination.parent.mkdir()
    destination.write_text("an earlier step wrote this\n", encoding="utf-8")

    assert main(["run", "--fast", "--no-report", "--summary", str(destination)]) == EXIT_OK

    written = destination.read_text(encoding="utf-8").splitlines()
    assert written[0] == "an earlier step wrote this"
    assert written[-1].startswith("gates --fast:")


def test_summarise_is_one_line_and_says_which_way_it_went(unwritten) -> None:
    name = unwritten[0].name
    report = run(select([name]), load(), selection=name, strict=True)
    line = summarise(report)
    assert "\n" not in line
    assert "RED" in line and name in line


def test_summarise_names_the_gates_rather_than_echoing_the_selection(unwritten) -> None:
    """The naming must survive a selection that does not contain the names.

    This is the question the test above *looks* like it asks and does not. There the
    selection is the gate's own name, so `name in line` was satisfied by the echo of the
    input — and it stayed satisfied while `summarise` reported nothing but tallies. Measured
    on 2026-09-12 against the real fast lane, the line read `gates --fast: green -- 7 passed,
    0 failed, 2 skipped, 0 errored` with AC-5 and HG-4 the skips, naming neither.

    So: select by *lane*, strike the selection string out of the line, and only then ask
    whether the gates that were not green are named. Card #86 owns the fix.
    """
    report = run(select(speed=Speed.FAST), load(), selection="--fast", strict=True)
    not_green = [r.name for r in report.results if r.status is not Status.PASSED]
    if not not_green:
        pytest.skip("every fast gate passed in this checkout, so there is nothing to name")

    line = summarise(report)
    assert "\n" not in line
    # Subtract the input before asking whether the sentence names anything: without this the
    # assertion passes on the echo, which is exactly how the gap survived.
    without_echo = line.replace("--fast", "")
    for gate in not_green:
        assert gate in without_echo, (
            f"{gate} was not green and summarise() did not name it: {line!r}"
        )
