"""Calibrate the deployed fit's band, and report what the calibration bought.

    python -m hydms.surrogate.calibrate --target capacity
    python -m hydms.surrogate.calibrate --target capacity --no-screening   # a cheaper probe
    python -m hydms.surrogate.calibrate --target capacity --cost           # fits nothing

One deployed fit and one calibration, not a cross-validation: card #27 conformalises **once**,
on the final fit, and gate AC-3 reads the test split afterwards. A per-fold calibration would
spend training rows the folds cannot spare and would move card #26's measured baseline under a
new partition; the per-fold coverage *spread* is a more informative question and it belongs to
cards #29 and #30.

**What this command measures, and what it deliberately does not.** It reports raw against
calibrated coverage on the **calibration rows** -- rows held out of the trees, so the raw
number there is a real measurement of the gap card #26 found, and the calibrated number is
nominal *by construction* and is labelled as such. It does not touch ``test``. Coverage on
held-out data is exactly what AC-3 certifies (card #31), and a command that printed it here
would invite the calibration to be adjusted until the gate passed -- which is leak L2 wearing
new clothes.

**Nothing here is published as an artifact.** Card #34 owns ``artifacts/v1``. This produces the
constant and the evidence that it is honest; :data:`~hydms.surrogate.conformal.CONFORMAL_PAYLOAD`
is the key it will be stored under.

Exit codes:

    0   the run finished and the tables were written
    2   the invocation itself was wrong (unreadable config, unknown target, unwritable path)

Card #27.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, TextIO

import pandas as pd

from hydms.config import Config, ConfigError, load
from hydms.data.splits import SPLIT_NAMES
from hydms.surrogate.conformal import (
    ConformalError,
    FittedConformal,
    calibrated_heads,
    calibration_slice,
    compare_metrics,
    fit_conformal,
)
from hydms.surrogate.model import (
    FitLog,
    ModelError,
    ModelSettings,
    QuantileModel,
    capacity_matrix,
    fit_quantile_model,
    quantile_metrics,
    screened_rows,
)
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.train import REPORTS, TARGETS

EXIT_OK = 0
EXIT_BAD_INVOCATION = 2

#: One file per question, the convention ``hydms.surrogate.train`` set.
TABLES = ("conformal", "conformal-coverage", "conformal-rows")

#: Where the deployed configuration comes from when an earlier run left one. Written by
#: ``python -m hydms.surrogate.train``; absent on a clean checkout, in which case this command
#: uses CatBoost's own defaults and says so, the way ``--budget`` does about its fit times.
CHOSEN = "model-chosen.csv"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.surrogate.calibrate",
        description=(
            "Conformalized quantile regression over the deployed fit: MAPIE estimates the "
            "constant, the artifact stores the number."
        ),
    )
    parser.add_argument(
        "--target", default=TARGETS[0], help=f"what to calibrate; one of {', '.join(TARGETS)}"
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    parser.add_argument(
        "--no-screening",
        action="store_true",
        help="skip the CleanLab stage — faster, and not what a real run does",
    )
    parser.add_argument(
        "--cost",
        action="store_true",
        help="fit nothing: report the row accounting the calibration carve implies",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="a directory to write the CSV tables into; defaults to the configured reports path",
    )
    return parser


def _destination(cfg: Config, given: Path | None) -> Path:
    return given if given is not None else (cfg.paths.reports / REPORTS)


def _write(tables: Mapping[str, pd.DataFrame], destination: Path, out: TextIO) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = destination / f"{name}.csv"
        table.to_csv(path)
        print(f"wrote {path}", file=out)


def _params(destination: Path, out: TextIO) -> tuple[Mapping[str, Any] | None, str]:
    """The hyperparameters the deployed fit uses, from an earlier run's table if there is one.

    Chosen on an inner-fold objective, never on an outer score -- the reading
    ``hydms.surrogate.train._deployed`` makes, and the reason it is a reading rather than a
    re-selection here: picking a configuration by any number this command can see would be
    selecting on data the calibration is about to be certified against.
    """
    table = destination / CHOSEN
    if not table.exists():
        print(
            f"no deployed configuration on disk ({table} is absent), so this fit uses "
            f"CatBoost's own defaults. That is a smoke test of the calibration path, not the "
            f"deployed band — run `python -m hydms.surrogate.train` first for that.",
            file=out,
        )
        return None, "catboost defaults"
    chosen = pd.read_csv(table)
    if chosen.empty or "objective" not in chosen.columns:
        print(f"{table} records no configuration; using CatBoost's defaults.", file=out)
        return None, "catboost defaults"
    best = chosen.loc[chosen["objective"].idxmin()]
    ignore = {"model", "fold", "objective", "seconds", "trials", "pruned"}
    params = {
        str(name): best[name]
        for name in chosen.columns
        if name not in ignore and pd.notna(best[name])
    }
    where = str(best.get("fold", "?"))
    print(
        f"deployed configuration: the one {where!r} chose, on its inner-fold objective "
        f"{float(best['objective']):.5f}",
        file=out,
    )
    return params, f"{CHOSEN}:{where}"


def _rows_table(
    model: QuantileModel, calibrating: tuple[object, ...], split: pd.Series
) -> pd.DataFrame:
    """The row accounting, including the cost the carve imposes -- stated, not hidden.

    The deployed model grows on the training rows *minus* the calibration slice, while the
    cross-validation that estimated its performance fitted on folds cut from all of them. That
    asymmetry is real and card #27 requires it reported rather than left to be inferred from
    two numbers in different files.
    """
    train_rows = int((split == TRAIN).sum())
    return pd.DataFrame(
        [
            {
                "split_train": train_rows,
                "screened_out": len(model.record.removed),
                "calibration": len(calibrating),
                "grown_on": len(model.record.fitted),
                "stopped_on": len(model.record.eval_on),
                "scored_on_named": len(model.record.scored_on),
                "grown_on_share_of_train": (
                    len(model.record.fitted) / train_rows if train_rows else float("nan")
                ),
            }
        ],
        index=pd.Index(["final fit"], name="fit"),
    )


def _coverage(
    model: QuantileModel,
    conformal: FittedConformal,
    frame: pd.DataFrame,
    labels: tuple[object, ...],
    target: str,
) -> pd.DataFrame:
    """Raw against calibrated, over the calibration rows, in weight percent.

    Both sides come from :func:`~hydms.surrogate.model.quantile_metrics` over the same rows --
    which is the whole reason :meth:`~hydms.surrogate.conformal.FittedConformal.apply` returns
    the same columns in the same order. The *calibrated* coverage here is nominal by
    construction and says nothing about generalisation; the *raw* coverage is a genuine
    held-out measurement of the gap this card exists to close.
    """
    rows = frame.loc[list(labels)]
    truth = rows[target]
    raw = quantile_metrics(truth, model.predict(rows), model.quantiles)
    calibrated = quantile_metrics(
        truth, calibrated_heads(model, rows, conformal=conformal), model.quantiles
    )
    return compare_metrics(raw, calibrated)


def _cost(cfg: Config, stream: TextIO) -> int:
    """``--cost``: what the carve takes, arithmetic only. Fits nothing."""
    folds = cfg.model.calibration_folds
    print(
        f"model.calibration_folds is {folds}, so the calibration slice is one fold of "
        f"{folds} — about {100.0 / folds:.0f} % of the screened training rows. Those rows do "
        f"not reach the trees: the deployed model grows on the remainder, while the "
        f"cross-validation that estimated its performance fitted on folds cut from all of "
        f"them. Report that asymmetry with the score, never separately.",
        file=stream,
    )
    print(
        f"conformal.confidence_level is {cfg.conformal.confidence_level:g}, so the heads "
        f"MAPIE requires are "
        f"({(1 - cfg.conformal.confidence_level) / 2:g}, 0.5, "
        f"{(1 + cfg.conformal.confidence_level) / 2:g}) and model.quantiles is "
        f"{list(cfg.model.quantiles)}.",
        file=stream,
    )
    return EXIT_OK


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """Fit, calibrate, report. Returns the process exit code."""
    stream = out if out is not None else sys.stdout
    args = _parser().parse_args(argv)

    if args.target not in TARGETS:
        print(
            f"{args.target!r} is not a target this project fits. It has one: "
            f"{', '.join(TARGETS)} — the maximum gravimetric hydrogen capacity in weight "
            f"percent. The rest of the PRD's objectives are behind the freeze.",
            file=sys.stderr,
        )
        return EXIT_BAD_INVOCATION

    try:
        cfg = load(args.config)
    except (ConfigError, OSError) as error:
        print(f"could not read the configuration: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    if args.cost:
        return _cost(cfg, stream)

    settings = ModelSettings.from_config(cfg)
    if args.no_screening:
        settings = replace(settings, screen_labels=False)
        print(
            "PROBE: screening off. The row counts below are not a real run's.", file=stream
        )

    destination = _destination(cfg, args.report)
    frame, split = capacity_matrix(cfg, settings=settings)
    rows = {name: list(frame.index[split == name]) for name in SPLIT_NAMES}
    print(
        f"{len(frame)} row(s) x {len(settings.features)} feature(s); "
        f"{len(rows[TRAIN])} in {TRAIN!r}",
        file=stream,
    )

    params, provenance = _params(destination, stream)
    log = FitLog()
    started = time.perf_counter()
    try:
        kept = screened_rows(frame, rows[TRAIN], settings=settings)
        fitting, calibrating = calibration_slice(
            frame, kept.kept, settings=settings, config=cfg
        )
        print(
            f"calibration carve: {len(calibrating)} row(s) held out of "
            f"{len(kept.kept)} screened training row(s); the trees grow on {len(fitting)}",
            file=stream,
        )
        model = fit_quantile_model(
            frame,
            train=fitting,
            eval_on=rows["val"],
            scored_on=rows["test"],
            where="final fit",
            params=params,
            settings=settings,
            removed=kept.removed,
            log=log,
        )
        conformal = fit_conformal(frame, model, calibrate_on=calibrating, config=cfg)
    except (ConformalError, ModelError) as error:
        print(f"the calibration failed: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    elapsed = time.perf_counter() - started

    print(
        f"conformal correction {conformal.correction:+.6f} in model space, from "
        f"{conformal.calibration_rows} calibration row(s), for a "
        f"{conformal.confidence_level:g} band "
        f"({'one constant' if conformal.symmetric else 'one per head'}, MAPIE "
        f"{conformal.mapie_version}); {elapsed / 60:.1f} min",
        file=stream,
    )

    coverage = _coverage(
        model, conformal, frame, calibrating, cfg.columns.target
    )
    print(
        "  on the calibration rows — raw coverage is a held-out measurement, calibrated "
        "coverage is nominal by construction:",
        file=stream,
    )
    for metric in ("interval_coverage", "interval_width", "crossings"):
        if metric in coverage.index:
            row = coverage.loc[metric]
            print(
                f"    {metric}: {row['raw']:.4f} -> {row['calibrated']:.4f} "
                f"({row['change']:+.4f})",
                file=stream,
            )
    print(
        f"  the test split was not read. Coverage on held-out data is gate AC-3's "
        f"(card #31); the configuration came from {provenance}.",
        file=stream,
    )

    tables = dict(
        zip(
            TABLES,
            (
                conformal.describe(),
                coverage,
                _rows_table(model, calibrating, split),
            ),
            strict=True,
        )
    )
    try:
        _write(tables, destination, stream)
    except OSError as error:
        print(f"could not write the tables: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
