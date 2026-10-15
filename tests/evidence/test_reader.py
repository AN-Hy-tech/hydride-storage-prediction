"""The Evidence Reader: three readings, each with its interval or its reason, and never a gap.

Card #83; ADR 0007. The reader decides, once, whether a committed table is a result and which of
the three scores a number is. So these tests are about the decisions: a probe's tables are
served as absent with the record's own reason, a missing table is an absent score and not a
missing row, and every present score carries an interval or the sentence saying why it has
none. The committed values are checked against the tables they are copied from, never against
numbers typed here.
"""

from __future__ import annotations

import ast
import csv
import shutil
import sys
from pathlib import Path

import pytest
from hydms import provenance
from hydms.evidence import reader
from hydms.evidence.reader import ARTIFACT, PROCEDURE, QUANTITIES, READINGS, TRANSFER, Score


@pytest.fixture(scope="module")
def committed(repo_root: Path) -> reader.Evidence:
    if not (repo_root / reader.EVALUATION_METRICS).is_file():
        pytest.skip("no committed evidence in this checkout")
    return reader.read(repo_root)


@pytest.fixture()
def copy(repo_root: Path, tmp_path: Path) -> Path:
    """The committed evidence in a scratch root, to be damaged one file at a time."""
    for relative in reader.read(repo_root).sources:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo_root / relative, target)
    return tmp_path


# --------------------------------------------------------------------------------------
# What the committed tables say, read through the reader
# --------------------------------------------------------------------------------------


def test_every_reading_serves_every_quantity_it_owes(committed: reader.Evidence) -> None:
    for reading in (PROCEDURE, ARTIFACT):
        assert {s.quantity for s in committed.of(reading) if s.subject == "all"} == set(QUANTITIES)
    assert committed.score(TRANSFER, "r2", "macro").value is not None
    families = [s for s in committed.of(TRANSFER) if s.subject.startswith("family:")]
    assert len(families) == 10


def test_the_procedure_score_is_the_evaluation_tables_own_number(
    committed: reader.Evidence, repo_root: Path
) -> None:
    score = committed.score(PROCEDURE, "r2")
    table = repo_root / reader.EVALUATION_METRICS
    lines = list(csv.DictReader(table.read_text(encoding="utf-8").splitlines()))
    (row,) = [
        found for found in lines
        if found["metric"] == "r2" and found["scale"] == "wt_pct" and found["subgroup"] == "all"
        and found["interval_from"] == "out-of-fold canonical groups"
    ]
    assert score.value == float(row["point"])
    assert score.interval is not None
    assert (score.interval.low, score.interval.high) == (float(row["ci_low"]), float(row["ci_high"]))
    assert score.interval.caveat == row["interval_caveat"]


def test_the_artifact_score_has_no_interval_and_says_why(committed: reader.Evidence) -> None:
    score = committed.score(ARTIFACT, "r2")
    assert score.interval is None
    assert score.no_interval_because == reader.ARTIFACT_NO_INTERVAL
    assert "AC-3" in score.no_interval_because
    assert score.run.version is not None and score.run.kind == "gate run"


def test_the_transfer_score_carries_the_emitted_interval_and_its_caveat(
    committed: reader.Evidence,
) -> None:
    from hydms.surrogate.loco import TRANSFER_CAVEAT

    score = committed.score(TRANSFER, "r2", "macro")
    assert score.interval is not None
    assert score.interval.low <= score.value <= score.interval.high  # type: ignore[operator]
    assert score.interval.caveat == TRANSFER_CAVEAT


def test_the_near_ambient_bin_is_served_with_an_interval_that_crosses_zero(
    committed: reader.Evidence,
) -> None:
    # The model card owes this limit with its interval (#83); the reader is where it comes from.
    coldest = min(
        (s for s in committed.of(PROCEDURE) if s.subject.startswith("temperature:")),
        key=lambda s: float(s.subject.split("(")[1].split(",")[0]),
    )
    assert coldest.interval is not None
    assert coldest.interval.low < 0.0 < coldest.interval.high


def test_a_run_whose_record_predates_the_date_says_not_recorded(committed: reader.Evidence) -> None:
    run = committed.score(TRANSFER, "r2", "macro").run
    assert run.run_date is None
    assert run.run_date_text == provenance.NOT_RECORDED


def test_both_parity_readings_serve_every_scored_row(committed: reader.Evidence) -> None:
    assert set(committed.parity) == {PROCEDURE, TRANSFER}
    assert len(committed.parity[PROCEDURE]) == len(committed.parity[TRANSFER]) == 893
    assert committed.parity_absent == {}


# --------------------------------------------------------------------------------------
# Refusing, and being absent without disappearing
# --------------------------------------------------------------------------------------


def test_a_probes_transfer_tables_are_absent_with_the_records_reason(copy: Path) -> None:
    record = copy / reader.TRANSFER_RECORD
    provenance.write(record, {"probe": "True", "optuna_trials": "1", "configured_optuna_trials": "25"})
    evidence = reader.read(copy)
    score = evidence.score(TRANSFER, "r2", "macro")
    assert score.value is None
    assert score.absent_because is not None and "probe=True" in score.absent_because
    assert TRANSFER not in evidence.parity
    assert "probe=True" in evidence.parity_absent[TRANSFER]
    assert evidence.score(PROCEDURE, "r2").value is not None


def test_an_absent_record_refuses_rather_than_assuming_the_good_case(copy: Path) -> None:
    (copy / reader.PROCEDURE_RECORD).unlink()
    evidence = reader.read(copy)
    assert all(s.value is None for s in evidence.of(PROCEDURE))
    assert "no run record" in (evidence.score(PROCEDURE, "r2").absent_because or "")


def test_a_missing_table_is_an_absent_score_not_a_missing_row(copy: Path) -> None:
    (copy / reader.ARTIFACT_SCORE).unlink()
    evidence = reader.read(copy)
    served = {s.quantity for s in evidence.of(ARTIFACT)}
    assert served == set(QUANTITIES)
    assert all(s.value is None and s.absent_because for s in evidence.of(ARTIFACT))


def test_without_the_intervals_table_the_transfer_score_says_it_has_none(copy: Path) -> None:
    (copy / reader.TRANSFER_INTERVALS).unlink()
    score = reader.read(copy).score(TRANSFER, "r2", "macro")
    assert score.value is not None and score.interval is None
    assert "loco --emit" in (score.no_interval_because or "")


def test_the_digest_moves_when_a_served_byte_moves(copy: Path) -> None:
    before = reader.read(copy).digest
    path = copy / reader.TRANSFER_SUMMARY
    path.write_text(path.read_text(encoding="utf-8").replace("0.25", "0.35", 1), encoding="utf-8")
    assert reader.read(copy).digest != before


def test_an_empty_root_serves_every_reading_as_absent(tmp_path: Path) -> None:
    evidence = reader.read(tmp_path)
    assert {s.reading for s in evidence.scores} == set(READINGS)
    assert all(s.value is None and s.absent_because for s in evidence.scores)
    assert set(evidence.parity_absent) == {PROCEDURE, TRANSFER}


# --------------------------------------------------------------------------------------
# The Score object
# --------------------------------------------------------------------------------------


def _run() -> reader.Run:
    return reader.Run(record="r", run_date=None)


@pytest.mark.parametrize(
    "fields",
    [
        {"reading": "out-of-fold", "value": 1.0, "no_interval_because": "x"},
        {"reading": PROCEDURE, "value": 1.0},
        {"reading": PROCEDURE, "value": 1.0, "no_interval_because": "x",
         "interval": reader.Interval(0.0, 2.0, 0.95, "g", "c")},
        {"reading": PROCEDURE, "value": None},
        {"reading": PROCEDURE, "value": 1.0, "no_interval_because": "x", "absent_because": "y"},
    ],
)
def test_a_score_cannot_be_built_half_stated(fields: dict) -> None:
    with pytest.raises(ValueError):
        Score(quantity="r2", subject="all", unit="", source="s", run=_run(), **fields)


def test_the_reader_imports_nothing_outside_the_standard_library() -> None:
    tree = ast.parse(Path(reader.__file__).read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    assert names - set(sys.stdlib_module_names) == {"hydms"}
