"""The run record -- card #105.

Two halves, as the module has them. Writing: a record states when the run *started* and what
code it started on, both taken before the fit. Reading: "is this a result?" has one answer, and
it is no unless the record positively says the run was full -- absent, unreadable, a probe, and
a ``probe`` cell nobody can parse are all refused.

The last test is the rule made executable: no module that serves, screens, draws or gates reads
a ``*-run.csv`` or a ``probe`` cell by hand. Before this card four consumers each parsed it
their own way and one did not parse it at all.
"""

from __future__ import annotations

import ast
import csv
import re
from datetime import date
from pathlib import Path

import pytest
from hydms import provenance
from hydms.provenance import (
    LEAVE_ONE_CLASS_OUT,
    LOCO_RECORD,
    NOT_RECORDED,
    RANDOM_SPLIT,
    NotAResult,
    begin,
    read,
    result,
    write,
)

SETTINGS = {"optuna_trials": 25, "configured_optuna_trials": 25, "screening": True, "seed": 42}


def _write(tmp_path: Path, *, probe: bool = False, protocol: str = RANDOM_SPLIT) -> Path:
    stamp = begin(tmp_path, protocol=protocol, probe=probe, settings=SETTINGS)
    return write(tmp_path / LOCO_RECORD, stamp.finish())


# --------------------------------------------------------------------------------------
# Round trip
# --------------------------------------------------------------------------------------


def test_a_full_run_round_trips_as_a_result_with_its_run_date(tmp_path: Path) -> None:
    path = _write(tmp_path, protocol=LEAVE_ONE_CLASS_OUT)
    record = result(path)

    assert record.probe is False
    assert record.protocol == LEAVE_ONE_CLASS_OUT
    assert record.run_date == date.today().isoformat()
    assert record.get("seed") == "42"
    assert record.flag("screening") is True
    assert float(record.get("elapsed_s") or "nan") >= 0.0


def test_the_record_carries_every_column_the_card_names(tmp_path: Path) -> None:
    fields = read(_write(tmp_path)).fields
    required = {
        "probe", "protocol", "run_id", "started_at", "finished_at", "elapsed_s", "git_sha",
        "code_modified", "python", "platform", "cpu_count", "catboost_thread_count",
        "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    } | {f"pkg_{name.lower()}" for name in provenance.PACKAGES}
    assert required <= set(fields)
    assert fields["catboost_thread_count"] == "default", "model.FIXED does not pin it (#32)"


def test_the_settings_come_first_in_the_order_the_old_files_had(tmp_path: Path) -> None:
    """Same file, more columns: a reader of a pre-#105 record sees the same leading fields."""
    fields = list(read(_write(tmp_path)).fields)
    assert fields[:2] == ["probe", "protocol"]
    assert fields[2 : 2 + len(SETTINGS)] == list(SETTINGS)


def test_the_start_is_stamped_at_begin_not_at_finish(tmp_path: Path, monkeypatch) -> None:
    """The run date is when the run started. A stamp read at finish would date a five-hour
    run by the morning after -- and read ``code_modified`` off the run's own output."""
    from datetime import datetime, timedelta

    stamp = begin(tmp_path, protocol=RANDOM_SPLIT, probe=False, settings={})
    later = stamp.started_at + timedelta(days=1)
    monkeypatch.setattr(provenance, "_now", lambda: later)
    row = stamp.finish()

    assert row["started_at"] == stamp.started_at.isoformat(timespec="seconds")
    assert row["finished_at"] == later.isoformat(timespec="seconds")
    assert datetime.fromisoformat(row["started_at"]).tzinfo is not None, "offset is stated"


def test_a_setting_cannot_overwrite_the_records_own_fields(tmp_path: Path) -> None:
    stamp = begin(tmp_path, protocol=RANDOM_SPLIT, probe=True, settings={"probe": False})
    with pytest.raises(ValueError, match="probe"):
        stamp.finish()


def test_a_record_must_be_named_as_one(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="-run.csv"):
        write(tmp_path / "loco-summary.csv", {"probe": "False"})


# --------------------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------------------


def test_a_probe_is_refused_as_a_result_and_says_so(tmp_path: Path) -> None:
    path = _write(tmp_path, probe=True)
    with pytest.raises(NotAResult, match="probe=True"):
        result(path)
    assert read(path).probe is True, "read describes; only result refuses"


def test_an_absent_record_is_absent_and_never_full(tmp_path: Path) -> None:
    record = read(tmp_path / LOCO_RECORD)
    assert record.state == "absent"
    assert record.probe is None
    with pytest.raises(NotAResult, match="no run record"):
        result(tmp_path / LOCO_RECORD)


def test_a_record_with_no_date_is_read_as_not_recorded(tmp_path: Path) -> None:
    """The committed pre-#105 records: settings only. Still a result, never given a date."""
    path = tmp_path / LOCO_RECORD
    path.write_text(
        ",probe,protocol,outer_folds,optuna_trials,configured_optuna_trials,screening\n"
        "0,False,leave-one-alloy-class-out,10,25,25,True\n",
        encoding="utf-8",
    )
    record = result(path)
    assert record.run_date is None
    assert record.run_date_text == NOT_RECORDED
    assert "" not in record.fields, "pandas' index column is not a field"


@pytest.mark.parametrize(
    ("body", "why"),
    [
        ("probe\n", "holds 0"),
        ("probe\nFalse\nFalse\n", "holds 2"),
    ],
)
def test_a_record_that_is_not_one_row_is_unreadable(tmp_path: Path, body: str, why: str) -> None:
    path = tmp_path / LOCO_RECORD
    path.write_text(body, encoding="utf-8")
    assert read(path).state == "unreadable"
    with pytest.raises(NotAResult, match=why):
        result(path)


@pytest.mark.parametrize("cell", ["", "maybe", "nan", "None"])
def test_a_probe_cell_nobody_can_parse_is_not_a_result(tmp_path: Path, cell: str) -> None:
    path = tmp_path / LOCO_RECORD
    path.write_text(f"probe,optuna_trials\n{cell},25\n", encoding="utf-8")
    assert read(path).probe is None
    with pytest.raises(NotAResult, match="not a boolean"):
        result(path)


# --------------------------------------------------------------------------------------
# Every spelling pandas and csv write
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cell", "probe"),
    [
        ("True", True), ("False", False), ("true", True), ("false", False),
        ("TRUE", True), ("FALSE", False), ("1", True), ("0", False),
        ("1.0", True), ("0.0", False), ("yes", True), ("no", False), (" True ", True),
    ],
)
def test_probe_is_read_in_every_spelling(tmp_path: Path, cell: str, probe: bool) -> None:
    path = tmp_path / LOCO_RECORD
    path.write_text(f"probe\n{cell}\n", encoding="utf-8")
    assert read(path).probe is probe


@pytest.mark.parametrize("probe", [True, False])
@pytest.mark.parametrize("index", [True, False])
def test_probe_is_read_as_pandas_writes_it(tmp_path: Path, probe: bool, index: bool) -> None:
    pd = pytest.importorskip("pandas")
    path = tmp_path / LOCO_RECORD
    pd.DataFrame.from_records([{"probe": probe, "optuna_trials": 25}]).to_csv(path, index=index)
    assert read(path).probe is probe
    assert set(read(path).fields) == {"probe", "optuna_trials"}


@pytest.mark.parametrize("probe", [True, False])
def test_probe_is_read_as_csv_writes_it(tmp_path: Path, probe: bool) -> None:
    path = tmp_path / LOCO_RECORD
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["probe"])
        writer.writerow([probe])
    assert read(path).probe is probe


def test_a_record_pandas_reads_back_is_the_record_written(tmp_path: Path) -> None:
    """The committed records are opened by people with pandas; the shape must survive it."""
    pd = pytest.importorskip("pandas")
    path = _write(tmp_path)
    frame = pd.read_csv(path)
    assert len(frame) == 1
    assert bool(frame.loc[0, "probe"]) is False
    assert path.read_bytes().count(b"\r") == 0, "\\n on every platform"


# --------------------------------------------------------------------------------------
# The committed records
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("record", ["reports/model/model-run.csv", "reports/loco/loco-run.csv"])
def test_the_committed_records_are_read_as_full_runs(repo_root: Path, record: str) -> None:
    """Both predate #105. They are full runs with no run date, and stay that way until the
    maintainer's next real run replaces them -- they are never backfilled from git."""
    path = repo_root / record
    if not path.is_file():
        pytest.skip(f"{record} is not in this checkout")
    found = result(path)
    if found.get("started_at") is None:
        assert found.run_date_text == NOT_RECORDED


# --------------------------------------------------------------------------------------
# Nothing downstream parses a record by hand
# --------------------------------------------------------------------------------------

#: The packages that serve, screen, draw or gate. A record they read goes through
#: ``hydms.provenance`` or not at all.
CONSUMERS = ("hydms/delivery", "hydms/screens", "hydms/figures", "hydms/gates", "app")

#: A string that *is* a record's file name, or the ``-run.csv`` tail an f-string builds one from.
#: Prose that merely mentions ``loco-run.csv`` is a longer string and does not match.
_RECORD_NAME = re.compile(r"[\w.-]*" + re.escape(provenance.RECORD_SUFFIX))


def _offences(source: str) -> list[str]:
    """Every place a module names a record file or reads a ``probe`` cell itself."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _RECORD_NAME.fullmatch(node.value)
        ):
            found.append(f"line {node.lineno}: names {node.value!r}")
        elif (
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and node.slice.value == "probe"
        ):
            found.append(f"line {node.lineno}: reads ['probe']")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "probe"
        ):
            found.append(f"line {node.lineno}: reads .get('probe')")
    return found


@pytest.mark.parametrize(
    "source",
    [
        'RUN = "loco-run.csv"',
        'path = directory / f"{name}-run.csv"',
        'flag = row["probe"]',
        'flag = run[0].get("probe", "")',
    ],
)
def test_the_detector_catches_each_kind_of_hand_read(source: str) -> None:
    """The positive control: a scan that finds nothing proves nothing until it has found one."""
    assert _offences(source)


def test_the_detector_leaves_prose_alone() -> None:
    assert _offences('"""Read ``loco-run.csv`` beside it."""\nmsg = f"see `loco-run.csv`"') == []


def test_no_consumer_reads_a_run_record_except_through_provenance(repo_root: Path) -> None:
    offences = {}
    for package in CONSUMERS:
        for path in sorted((repo_root / package).rglob("*.py")):
            found = _offences(path.read_text(encoding="utf-8"))
            if found:
                offences[str(path.relative_to(repo_root))] = found
    assert offences == {}, (
        "read the run record through hydms.provenance.read/result, never by hand (#105)"
    )


def test_provenance_imports_nothing_outside_the_standard_library() -> None:
    """A gate must read a record on an interpreter with no scientific stack."""
    tree = ast.parse(Path(provenance.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    assert imported <= {
        "__future__", "csv", "os", "platform", "time", "uuid", "collections", "dataclasses",
        "datetime", "pathlib", "typing", "hydms",
    }
