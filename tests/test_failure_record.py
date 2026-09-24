"""The failure record: a red run keeps its tracebacks whatever happened to the terminal. Card #100.

Every test here runs an inner pytest session through `pytester` with a fresh instance of the
recorder the suite itself registered, so what is exercised is the class `tests/conftest.py`
actually installs, not a copy. The inner sessions write their records under `tmp_path`.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

RECORDER_NAME = "hydms-failure-record"


def _fresh_recorder(request: pytest.FixtureRequest, directory: Path, watched: tuple[Path, ...] = ()):
    registered = request.config.pluginmanager.get_plugin(RECORDER_NAME)
    assert registered is not None, f"tests/conftest.py did not register {RECORDER_NAME!r}"
    return type(registered)(directory, watched)


def _the_one_record(directory: Path) -> Path:
    records = sorted(directory.iterdir())
    assert len(records) == 1, f"expected one record, found {[p.name for p in records]}"
    return records[0]


def test_a_red_run_leaves_its_long_traceback_on_disk(
    pytester: pytest.Pytester, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    pytester.makepyfile(
        test_inner="""
        def test_the_one_that_fails():
            print("captured-marker-" + str(7000 + 731))  # computed: the source listing must not match
            observed = 41
            assert observed == 42, "distinctive-message-5512"
        """
    )
    records = tmp_path / "records"
    # The default `--tb`, which is what #100's lost run used before a pipe kept its last 15 lines.
    result = pytester.runpytest(plugins=[_fresh_recorder(request, records)])
    result.assert_outcomes(failed=1)
    terminal = result.stdout.str()

    record = _the_one_record(records)
    text = record.read_text(encoding="utf-8")
    assert "test_inner.py::test_the_one_that_fails  [call]" in text
    assert "observed = 41" in text  # the traceback's own source line, at long style
    assert "distinctive-message-5512" in text
    assert "captured-marker-7731" in text  # the test's captured stdout
    assert "collected 1" in text
    for section in ("alive at the START", "alive at the END", "modified WHILE the run was going"):
        assert section in text
    assert f"failure record written: {record}" in terminal


def test_a_green_run_writes_nothing(
    pytester: pytest.Pytester, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    pytester.makepyfile(test_inner="def test_fine():\n    pass\n")
    records = tmp_path / "records"
    result = pytester.runpytest(plugins=[_fresh_recorder(request, records)])
    result.assert_outcomes(passed=1)
    assert not records.exists()
    assert "failure record" not in result.stdout.str()


def test_a_collection_error_is_recorded(
    pytester: pytest.Pytester, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    pytester.makepyfile(test_broken="import this_module_does_not_exist_9931\n")
    records = tmp_path / "records"
    result = pytester.runpytest(plugins=[_fresh_recorder(request, records)])
    result.assert_outcomes(errors=1)
    text = _the_one_record(records).read_text(encoding="utf-8")
    assert "test_broken.py  [collect]" in text
    assert "this_module_does_not_exist_9931" in text


def test_a_source_file_edited_during_the_run_is_named(
    pytester: pytest.Pytester, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    watched = tmp_path / "watched"
    watched.mkdir()
    edited, untouched = watched / "edited.py", watched / "untouched.py"
    an_hour_ago = time.time() - 3600
    for path in (edited, untouched):
        path.write_text("x = 1\n", encoding="utf-8")
        os.utime(path, (an_hour_ago, an_hour_ago))
    # The other session's repair landing mid-run, which is how one of #100's greens meant nothing.
    pytester.makepyfile(
        test_inner=f"""
        from pathlib import Path

        def test_edits_a_source_file_mid_run():
            Path(r"{edited}").write_text("x = 2\\n", encoding="utf-8")
            assert False
        """
    )
    records = tmp_path / "records"
    result = pytester.runpytest(plugins=[_fresh_recorder(request, records, (watched,))])
    result.assert_outcomes(failed=1)
    text = _the_one_record(records).read_text(encoding="utf-8")
    modified = text.split("modified WHILE the run was going:")[1].split("=" * 100)[0]
    assert str(edited) in modified
    assert str(untouched) not in modified


def test_a_record_that_cannot_be_written_is_reported_not_raised(
    pytester: pytest.Pytester, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    pytester.makepyfile(test_inner="def test_fails():\n    assert False\n")
    blocked = tmp_path / "a-file-where-the-directory-should-be"
    blocked.write_text("", encoding="utf-8")
    result = pytester.runpytest(plugins=[_fresh_recorder(request, blocked)])
    result.assert_outcomes(failed=1)  # the run's own result, not an INTERNALERROR
    assert "failure record could NOT be written" in result.stdout.str()


def test_the_suite_records_into_a_gitignored_directory(
    request: pytest.FixtureRequest, repo_root: Path
) -> None:
    registered = request.config.pluginmanager.get_plugin(RECORDER_NAME)
    assert registered is not None
    assert registered.directory == repo_root / "reports" / "test-failures"
    # A record must never make the tree dirty: that would move every provenance stamp after it.
    probe = (registered.directory / "any-record.txt").relative_to(repo_root).as_posix()
    check = subprocess.run(["git", "check-ignore", "-q", probe], cwd=repo_root, check=False)
    assert check.returncode == 0, f"{probe} is not gitignored"
