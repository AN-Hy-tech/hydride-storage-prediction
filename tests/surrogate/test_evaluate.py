"""Evaluation metrics with bootstrap confidence intervals: what the interval is *around*.

Three properties carry this file, and each of them is a decision card #29 settled that could be
undone by a plausible-looking edit.

**The resampling unit is the canonical composition.** `group_keys` is the seam #13 splits on,
#88 folds on and #87 joins on, and a row-level resample here would be a fourth meaning of "the
same material" -- leak L8's logic applied to intervals instead of splits. A test that only
checked "an interval came back" would pass on the wrong unit, so the fixtures below are built
so that the two units give *demonstrably* different answers.

**The point estimate is the statistic on the data, not the mean of the replicates.** The
bootstrap estimates spread; publishing its centre instead would publish a number nobody
computed on the observations.

**Every claim a row makes travels with the row.** The feature set, the reading, and the caveat
that the interval is too narrow are columns rather than a header, because a row is what gets
quoted into a chapter.

Card #29.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

pytest.importorskip("pandas", reason="the evaluation layer is pandas frames end to end")

import pandas as pd  # noqa: E402
from hydms.config import load  # noqa: E402
from hydms.data.metadata import CANONICAL_KEY_COLUMN  # noqa: E402
from hydms.surrogate.evaluate import (  # noqa: E402
    CONFIDENCE,
    GROUPS,
    INTERVAL_CAVEAT,
    PER_FOLD,
    ROWS,
    UNKNOWN_RUN,
    EvaluationError,
    _replicates,
    main,
    metrics_table,
    per_fold_intervals,
    read_out_of_fold,
    read_run,
    subgroup_table,
    to_markdown,
)
from hydms.surrogate.model import ModelSettings, quantile_metrics  # noqa: E402

QUANTILES = (0.1, 0.5, 0.9)
TARGET = "H2_W% (max)"
LOG_TARGET = "log_H2_W% (max)"
TEMPERATURE = "temperature(K)"
CHEAP = 200  # resamples, where the test is about the unit rather than the third decimal


def _out_of_fold(rows: int = 120, *, groups: int = 40, folds: int = 5) -> pd.DataFrame:
    """A synthetic out-of-fold table with real column names and a real group structure.

    ``groups`` distinct canonical keys over ``rows`` rows, so materials repeat -- which is the
    whole reason the unit matters. Temperatures span a range so `pd.qcut` has bands to cut.
    """
    rng = np.random.default_rng(11)
    truth = rng.uniform(0.2, 6.0, size=rows)
    median = truth + rng.normal(scale=0.4, size=rows)
    frame = pd.DataFrame(
        {
            "model": "catboost-multiquantile",
            "fold": [f"outer-{i % folds}" for i in range(rows)],
            TARGET: truth,
            LOG_TARGET: np.log1p(truth),
            "q0.1": median - 0.8,
            "q0.5": median,
            "q0.9": median + 0.8,
            "log_q0.1": np.log1p(np.clip(median - 0.8, 0.01, None)),
            "log_q0.5": np.log1p(np.clip(median, 0.01, None)),
            "log_q0.9": np.log1p(np.clip(median + 0.8, 0.01, None)),
            CANONICAL_KEY_COLUMN: [f"key-{i % groups}" for i in range(rows)],
            TEMPERATURE: rng.uniform(250.0, 600.0, size=rows),
        },
        index=[f"row-{i}" for i in range(rows)],
    )
    return frame


# --------------------------------------------------------------------------------------
# The resampling unit
# --------------------------------------------------------------------------------------


def test_a_group_resample_draws_whole_compositions_and_a_row_resample_does_not() -> None:
    """The property, at its sharpest: one material, and the group bootstrap has no variance.

    Six rows describing a single canonical composition can be drawn six times as rows and give
    six different replicates; drawn as *groups* there is one thing to draw, so every replicate
    is the whole set. That difference is the entire content of the decision, and it is what a
    resample keyed on the raw formula string -- or on nothing -- would silently lose.
    """
    keys = ["the-same-material"] * 6
    grouped = _replicates(keys, resamples=50, seed=42, by_group=True)
    rowwise = _replicates(keys, resamples=50, seed=42, by_group=False)

    assert all(sorted(index) == list(range(6)) for index in grouped), (
        "a group resample of one composition must return that composition whole, every time"
    )
    assert any(sorted(index) != list(range(6)) for index in rowwise), (
        "a row resample of six rows must vary; if it does not, the fixture is wrong"
    )


def test_a_resampled_group_carries_all_of_its_rows() -> None:
    """83 of the 780 real training groups span more than one temperature.

    So a group must arrive whole -- every row of it, at every temperature it was measured at --
    or a resample taken inside a temperature band would cut it in half locally, in exactly the
    bands where the data is thinnest.
    """
    keys = ["a", "a", "a", "b", "c", "c"]
    for index in _replicates(keys, resamples=30, seed=7, by_group=True):
        drawn = [keys[at] for at in index]
        for key in set(drawn):
            expected = keys.count(key)
            assert drawn.count(key) % expected == 0, (
                f"{key!r} appears {drawn.count(key)} times, which is not a whole number of "
                f"its {expected}-row block"
            )


def test_the_same_seed_gives_the_same_interval() -> None:
    """AC-1's question, asked of this module. An interval that moves between runs is noise."""
    table = _out_of_fold()
    cfg = load()
    first = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    second = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    pd.testing.assert_frame_equal(first, second)


# --------------------------------------------------------------------------------------
# The point estimate
# --------------------------------------------------------------------------------------


def test_the_point_estimate_is_the_statistic_on_the_data() -> None:
    """Not the mean of the replicates, and this is the one definition of it.

    `quantile_metrics` is what card #26's per-fold table reports, so an evaluation whose point
    estimate came from anywhere else would put a different number beside the same name.
    """
    table = _out_of_fold()
    cfg = load()
    metrics = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    expected = quantile_metrics(
        table[TARGET], table[["q0.1", "q0.5", "q0.9"]], QUANTILES
    )
    for metric, value in expected.items():
        row = metrics[
            (metrics["metric"] == metric)
            & (metrics["scale"] == "wt_pct")
            & (metrics["interval_from"] == GROUPS)
        ]
        assert len(row) == 1
        assert row["point"].iloc[0] == pytest.approx(value, abs=1e-12)


def test_the_interval_brackets_the_point_estimate() -> None:
    table = _out_of_fold()
    cfg = load()
    metrics = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    inside = metrics[np.isfinite(metrics["point"])]
    assert (inside["ci_low"] <= inside["point"] + 1e-9).all()
    assert (inside["point"] <= inside["ci_high"] + 1e-9).all()
    assert (metrics["confidence"] == CONFIDENCE).all()


def test_both_scales_are_reported_and_they_are_not_the_same_number() -> None:
    """R2 on log1p capacity and R2 in weight percent are different claims about the same fit.

    The archival script scored cross-validation on the log scale "to avoid negative scores",
    which is that observation read the other way round -- so both are emitted and each says
    which it is.
    """
    table = _out_of_fold()
    cfg = load()
    metrics = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    assert set(metrics["scale"]) == {"wt_pct", "log"}
    wt = metrics[(metrics["metric"] == "rmse") & (metrics["scale"] == "wt_pct")]["point"]
    log = metrics[(metrics["metric"] == "rmse") & (metrics["scale"] == "log")]["point"]
    assert wt.iloc[0] != log.iloc[0]


# --------------------------------------------------------------------------------------
# What every row has to say
# --------------------------------------------------------------------------------------


def test_the_too_narrow_caveat_is_a_column_on_every_row() -> None:
    """Card #29 settled this against prose, and gave the reason: prose is what a session drops.

    A reader who quotes a bound out of this table cannot quote it without the sentence that
    says the bound is too narrow.
    """
    table = _out_of_fold()
    cfg = load()
    metrics = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    assert (metrics["interval_caveat"] == INTERVAL_CAVEAT).all()
    assert "Bengio" in INTERVAL_CAVEAT
    assert (metrics["feature_set"] == "hydms.descriptors.contract.SELECTED").all()
    assert not metrics["selection_refitted_per_fold"].any()
    assert (metrics["reading"] == "out-of-fold").all()


def test_both_resampling_units_are_published_side_by_side() -> None:
    """Card #25's precedent: publish the comparison that justifies a choice.

    The group correction is worth 13 % of the independent units on the real data, which is a
    real correction and a small one. Publishing both is what stops a later session
    re-litigating the choice from a paragraph -- or overselling it.
    """
    table = _out_of_fold()
    cfg = load()
    metrics = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    assert set(metrics["interval_from"]) == {GROUPS, ROWS}
    grouped = metrics[metrics["interval_from"] == GROUPS]
    rowwise = metrics[metrics["interval_from"] == ROWS]
    assert grouped["units"].iloc[0] < rowwise["units"].iloc[0], (
        "there are fewer canonical groups than rows in the fixture, so the group bootstrap "
        "must report fewer independent units"
    )
    # The same point estimate under both units: only the interval differs.
    for metric in ("r2", "rmse", "mae"):
        left = grouped[(grouped["metric"] == metric) & (grouped["scale"] == "wt_pct")]
        right = rowwise[(rowwise["metric"] == metric) & (rowwise["scale"] == "wt_pct")]
        assert left["point"].iloc[0] == pytest.approx(right["point"].iloc[0], abs=1e-12)


# --------------------------------------------------------------------------------------
# Subgroups
# --------------------------------------------------------------------------------------


def test_subgroups_record_how_thin_they_got() -> None:
    """`rows_min` and `rows_max` are what make a thin temperature band visible.

    Subgroup *n* varies between replicates because the resample is taken at the split level
    and each band is a mask on it. A band that is thin in most replicates is a band whose
    interval is wide for a reason a reader has to be able to see.
    """
    table = _out_of_fold()
    cfg = load()
    subgroups = subgroup_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    assert set(subgroups["subgroup"]) == {"fold", "temperature"}
    assert (subgroups["rows_min"] <= subgroups["rows"]).all()
    assert (subgroups["rows"] <= subgroups["rows_max"]).all()
    assert (subgroups["rows_min"] < subgroups["rows_max"]).any(), (
        "if no subgroup's size ever varied across replicates, the resample is not being "
        "taken at the split level"
    )
    assert (subgroups["interval_from"] == GROUPS).all(), (
        "subgroup intervals are the principled unit only; the row comparison is published "
        "once, over everything"
    )


def test_the_split_level_resample_is_shared_with_the_headline_table() -> None:
    """Q6: one resample, every breakdown computed from it — and it is shared by determinism.

    `_replicates` is a pure function of the keys, the count and the seed, so `metrics_table`
    and `subgroup_table` given the same table see the same draws without passing one another
    an object. Asserted rather than assumed: if it ever stopped holding, a group spanning two
    temperature bands would be resampled independently in each, which is precisely the local
    break of the canonical seam this design exists to avoid.
    """
    table = _out_of_fold()
    keys = table[CANONICAL_KEY_COLUMN].tolist()
    cfg = load()
    first = _replicates(keys, resamples=CHEAP, seed=cfg.seed, by_group=True)
    second = _replicates(keys, resamples=CHEAP, seed=cfg.seed, by_group=True)
    assert all(np.array_equal(a, b) for a, b in zip(first, second, strict=True))


def test_every_outer_fold_gets_its_own_row() -> None:
    table = _out_of_fold()
    cfg = load()
    subgroups = subgroup_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    folds = subgroups[subgroups["subgroup"] == "fold"]
    assert set(folds["subgroup_value"]) == set(table["fold"])


# --------------------------------------------------------------------------------------
# The second, cruder interval
# --------------------------------------------------------------------------------------


def test_the_per_fold_interval_is_a_second_reading_and_says_so() -> None:
    """It prices fold-to-fold spread, part of which card #24 measured to be training size.

    Two intervals that disagree are more honest than one that looks authoritative, so this one
    rides in the same table under its own `interval_from`.
    """
    per_fold = pd.DataFrame(
        {
            "model": ["catboost"] * 5,
            "fold": [f"outer-{i}" for i in range(5)],
            "r2": [0.71, 0.66, 0.74, 0.69, 0.72],
            "rows_fitted": [704.0, 571.0, 688.0, 640.0, 701.0],
        }
    )
    rows = per_fold_intervals(per_fold, seed=42, resamples=CHEAP)
    assert (rows["interval_from"] == PER_FOLD).all()
    assert (rows["units"] == 5).all()

    r2 = rows[rows["metric"] == "r2"].iloc[0]
    assert r2["point"] == pytest.approx(per_fold["r2"].mean(), abs=1e-12)
    assert r2["ci_low"] < r2["point"] < r2["ci_high"]

    assert "rows_fitted" in set(rows["metric"]), (
        "the fold sizes are carried as a metric on purpose: part of the spread this interval "
        "prices is training size and not the model, and a table that hides it invites the "
        "other reading"
    )


# --------------------------------------------------------------------------------------
# Reading what the run left behind
# --------------------------------------------------------------------------------------


def test_a_table_without_the_canonical_key_is_refused_by_name(tmp_path) -> None:
    """Silently falling back to a row resample would publish the comparison as the result.

    The two readings would then be the same number under two labels, which is worse than
    either of them alone.
    """
    table = _out_of_fold().drop(columns=[CANONICAL_KEY_COLUMN])
    directory = tmp_path / "model"
    directory.mkdir()
    table.to_csv(directory / "model-out-of-fold.csv")
    with pytest.raises(EvaluationError, match="canonical key"):
        read_out_of_fold(directory, config=load())


def test_an_absent_table_names_the_run_that_writes_it(tmp_path) -> None:
    with pytest.raises(EvaluationError, match="hydms.surrogate.train"):
        read_out_of_fold(tmp_path, config=load())


def test_a_round_trip_through_csv_survives(tmp_path) -> None:
    """The published table is a CSV, so the CSV is what the module must be able to read."""
    directory = tmp_path / "model"
    directory.mkdir()
    _out_of_fold().to_csv(directory / "model-out-of-fold.csv")
    table = read_out_of_fold(directory, config=load())
    assert len(table) == 120
    assert table[CANONICAL_KEY_COLUMN].nunique() == 40


# --------------------------------------------------------------------------------------
# The command
# --------------------------------------------------------------------------------------


def test_the_artifact_reading_refuses_by_name_until_card_34(capsys) -> None:
    """The card's own runnable check, and it cannot run yet -- so it says which card it needs.

    `load_surrogate()` would raise `PredictionError: nothing is promoted` from three frames
    down. Card #29's decision was to keep the flag as the second reading rather than re-aim it
    to make the check green, so the refusal has to name what is missing and what to run instead.
    """
    assert main(["--artifact", "current"]) == 2
    message = capsys.readouterr().err
    assert "#34" in message
    assert "without --artifact" in message


def test_the_command_writes_both_tables_and_the_write_up(tmp_path, capsys) -> None:
    directory = tmp_path / "model"
    directory.mkdir()
    _out_of_fold().to_csv(directory / "model-out-of-fold.csv")

    assert main(["--report", str(directory), "--resamples", "100", "--emit"]) == 0
    for name in ("evaluation-metrics", "evaluation-subgroups"):
        assert (directory / f"{name}.csv").is_file()
    document = (directory / "evaluation.md").read_text(encoding="utf-8")
    assert INTERVAL_CAVEAT in document
    assert "canonical compositions" in document
    assert "out-of-fold" in capsys.readouterr().out


# --------------------------------------------------------------------------------------
# Which kind of run produced these numbers
# --------------------------------------------------------------------------------------


def test_an_unlabelled_run_is_reported_as_unknown_and_not_as_a_full_one(tmp_path) -> None:
    """The default has to be the bad case, because the two look identical on disk.

    A reduced run writes the same seven tables with the same columns as a real one.
    `train.py` prints `These numbers are a cost check, not a result` to a terminal somebody
    closes; `model-run.csv` is the copy card #37 will actually read. If it is missing, the
    honest answer is "nobody said" -- and defaulting to "full" is how a cost check becomes a
    thesis number.
    """
    assert read_run(tmp_path) == UNKNOWN_RUN
    assert not UNKNOWN_RUN.startswith("full")


def test_a_probe_is_named_as_a_probe_with_its_budget(tmp_path) -> None:
    pd.DataFrame.from_records(
        [
            {
                "probe": True,
                "optuna_trials": 2,
                "configured_optuna_trials": 25,
                "screening": False,
            }
        ]
    ).to_csv(tmp_path / "model-run.csv", index=False)
    run = read_run(tmp_path)
    assert run.startswith("PROBE")
    assert "2 of 25" in run
    assert "screening off" in run


def test_a_full_run_says_so_and_only_then(tmp_path) -> None:
    pd.DataFrame.from_records(
        [
            {
                "probe": False,
                "optuna_trials": 25,
                "configured_optuna_trials": 25,
                "screening": True,
            }
        ]
    ).to_csv(tmp_path / "model-run.csv", index=False)
    assert read_run(tmp_path).startswith("full")


def test_the_run_record_the_training_command_writes_is_the_one_this_module_reads(
    tmp_path,
) -> None:
    """The seam between the two modules, closed in a test rather than by two matching lists.

    `train.py` writes the record and `evaluate.py` reads it. Nothing else connects them, so a
    renamed column would leave the banner silently reporting "unknown" on a real run — which
    fails in the safe direction and is therefore exactly the kind of drift nobody notices.
    """
    from hydms.surrogate.train import _run

    cfg = load()
    settings = ModelSettings.from_config(cfg)

    _run(cfg, settings, probe=False).to_csv(tmp_path / "model-run.csv", index=False)
    assert read_run(tmp_path).startswith("full")

    probe = replace(settings, optuna_trials=2, screen_labels=False)
    _run(cfg, probe, probe=True).to_csv(tmp_path / "model-run.csv", index=False)
    run = read_run(tmp_path)
    assert run.startswith("PROBE")
    assert f"2 of {cfg.model.optuna_trials}" in run
    assert "screening off" in run


def test_the_document_leads_with_a_warning_unless_the_run_was_full() -> None:
    """The loudest thing Markdown has, above everything, including the headline table."""
    from datetime import datetime, timezone

    table = _out_of_fold()
    cfg = load()
    dated = datetime(2026, 9, 5, tzinfo=timezone.utc)

    for run, warned in (
        (UNKNOWN_RUN, True),
        ("PROBE (2 of 25 trial(s)) — a cost check, not a result", True),
        ("full — 25 trial(s), screening on", False),
    ):
        metrics = metrics_table(
            table,
            config=cfg,
            quantiles=QUANTILES,
            seed=cfg.seed,
            resamples=50,
            run=run,
        )
        subgroups = subgroup_table(
            table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=50, run=run
        )
        document = to_markdown(metrics, subgroups, sha="abc", dirty=False, dated=dated)
        assert (document.startswith("# Model evaluation")) is True
        banner = "not a result" in document.split("## What these numbers")[0]
        assert banner is warned, f"{run!r} should {'' if warned else 'not '}raise the banner"
        assert f"- Run: {run}" in document, "the run is stated even when it needs no banner"


def test_the_write_up_is_generated_and_therefore_reproducible() -> None:
    """Card #25's shape: the document is a function of the tables, so it can be checked.

    A write-up composed by hand beside its tables is one that stops agreeing with them
    silently, on the day somebody edits one of the two.
    """
    from datetime import datetime, timezone

    table = _out_of_fold()
    cfg = load()
    metrics = metrics_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    subgroups = subgroup_table(
        table, config=cfg, quantiles=QUANTILES, seed=cfg.seed, resamples=CHEAP
    )
    dated = datetime(2026, 9, 5, tzinfo=timezone.utc)
    first = to_markdown(metrics, subgroups, sha="abc123def456", dirty=False, dated=dated)
    second = to_markdown(metrics, subgroups, sha="abc123def456", dirty=False, dated=dated)
    assert first == second
    assert "abc123def456" in first
    assert "clean tree" in first
