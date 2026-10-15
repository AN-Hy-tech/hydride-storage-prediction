"""AC-6 — that the extrapolation number is published beside the interpolation one. Card #30.

The criterion is the word *alongside*, so most of this file is about the three ways a report
can fail to be one: the run has not happened, the run was a probe, or the class figure is
published on its own. Only the last of those is a mistake somebody could make while believing
they had satisfied the criterion, which is why it is a `FAILED` and not a `SKIPPED`.

The gate reads committed CSVs rather than fitting, because the protocol behind them costs about
4.7 hours. That makes the tables the gate's whole input, so every test here writes a real
directory of them and points the config at it — nothing is monkeypatched into the gate, and a
change to the columns `hydms.surrogate.loco` writes reaches this file rather than being
absorbed by a mock.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from hydms.config import Config
from hydms.gates._core import Status
from hydms.gates.ac6_leave_one_class_out import GATE

SUMMARY_HEADER = (
    "model,classes,classes_scored,classes_not_estimable,macro_r2,macro_mae,weighted_r2,"
    "worst_class,worst_class_r2,best_class,best_class_r2,rows_scored,random_split_r2"
)
RUN_HEADER = (
    "probe,protocol,outer_folds,optuna_trials,configured_optuna_trials,screening,"
    "inner_cv_folds,feature_set,features,seed"
)


def _config(tmp_path: Path) -> Config:
    from hydms.config import load

    cfg = load()
    return replace(cfg, paths=replace(cfg.paths, reports=tmp_path))


def _tables(
    tmp_path: Path,
    *,
    macro: str = "0.2240",
    random_split: str = "0.7459",
    probe: str = "False",
) -> Path:
    directory = tmp_path / "loco"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "loco-summary.csv").write_text(
        f"{SUMMARY_HEADER}\n"
        f"catboost-multiquantile,10,10,0,{macro},0.5134,0.1664,HEA,-0.3026,A2B,0.6703,893,"
        f"{random_split}\n",
        encoding="utf-8",
    )
    (directory / "loco-run.csv").write_text(
        f"{RUN_HEADER}\n"
        f"{probe},leave-one-alloy-class-out,10,25,25,True,3,"
        f"hydms.descriptors.contract.SELECTED,14,42\n",
        encoding="utf-8",
    )
    return directory


def test_both_numbers_published_is_the_whole_criterion(tmp_path: Path) -> None:
    _tables(tmp_path)
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.PASSED
    assert "0.2240" in result.message and "0.7459" in result.message
    assert "+0.5219" in result.message, "the gap is reported"
    assert "deliberately not what this gate measures" in result.message


def test_a_very_bad_transfer_number_still_passes(tmp_path: Path) -> None:
    """The criterion asks that the number be reported, not that it be good. A threshold here
    would be this project deciding in advance what hydride chemistry is allowed to do."""
    _tables(tmp_path, macro="-1.8000")
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.PASSED
    assert "-1.8000" in result.message


def test_no_run_at_all_skips_and_names_the_command_that_would_fix_it(tmp_path: Path) -> None:
    """Not a failure: nothing has been established, and `promote` already treats a skip as
    exactly that. What the message must not do is leave the reader to guess what runs it."""
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.SKIPPED
    assert "hydms.surrogate.loco" in result.message
    assert "4.7 h" in result.message


def test_half_a_run_is_still_no_run(tmp_path: Path) -> None:
    """The provenance row is not optional: without it the gate cannot tell a result from a
    probe, and a gate that cannot tell must not pass."""
    directory = _tables(tmp_path)
    (directory / "loco-run.csv").unlink()
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.SKIPPED
    assert "loco-run.csv" in result.message


def test_a_probes_tables_fail_rather_than_skip(tmp_path: Path) -> None:
    """A probe's tables are the same shape as a real run's, so committed probe numbers are a
    defect somebody introduced — not an absence somebody has yet to fill. The two get
    different words on purpose."""
    _tables(tmp_path, probe="True")
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.FAILED
    assert "probe=True" in result.message
    assert result.measured == "probe"


def test_a_probe_cell_nobody_can_parse_fails_rather_than_passing(tmp_path: Path) -> None:
    """Before #105 the gate refused only ``true``/``1``/``yes``, so ``probe=maybe`` passed as a
    full run. Through :func:`hydms.provenance.result` an unreadable cell is not a result."""
    _tables(tmp_path, probe="maybe")
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.FAILED
    assert result.measured == "no readable record"


def test_the_class_number_published_alone_fails(tmp_path: Path) -> None:
    """The mistake this gate exists to catch, and the only one a person could make while
    believing they had met the criterion."""
    _tables(tmp_path, random_split="")
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.FAILED
    assert "alongside" in result.message
    assert result.measured == "0.2240 alone"


def test_a_nan_random_split_number_reads_as_absent_not_as_a_number(tmp_path: Path) -> None:
    """`summary()` writes NaN when no random-split run is on disk. A column of NaN must not
    satisfy 'reported alongside', which it would if the cell were merely parsed."""
    _tables(tmp_path, random_split="nan")
    assert GATE.check(_config(tmp_path)).status is Status.FAILED


def test_a_summary_with_no_rows_fails_rather_than_reporting_nothing(tmp_path: Path) -> None:
    directory = _tables(tmp_path)
    (directory / "loco-summary.csv").write_text(SUMMARY_HEADER + "\n", encoding="utf-8")
    result = GATE.check(_config(tmp_path))

    assert result.status is Status.FAILED
    assert "header and no rows" in result.message


def test_the_gate_names_the_directory_the_command_actually_writes() -> None:
    """The gate restates the directory rather than importing it, so that reading a manifest
    does not require pandas — the same trade `hydms.artifacts.manifest.GATE_SCHEMA` makes.
    This is the test that keeps the two from drifting apart. The record's name is no longer
    restated: both sides import it from `hydms.provenance` (card #105)."""
    from hydms import provenance
    from hydms.gates.ac6_leave_one_class_out import REPORTS, SUMMARY
    from hydms.surrogate import loco

    assert REPORTS == loco.REPORTS
    assert f"{loco.TABLES[1]}.csv" == SUMMARY
    assert f"{loco.TABLES[3]}.csv" == provenance.LOCO_RECORD


def test_the_gate_is_fast_because_it_reads_rather_than_refits() -> None:
    """It was declared SLOW while it was a stub, on the reasoning that one refit per alloy
    class is a retrain. That is true of the protocol and false of this check."""
    from hydms.gates._core import Speed

    assert GATE.speed is Speed.FAST
    assert GATE.card == 30
