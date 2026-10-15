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

**This command builds the deployed fit, and it is the only one that does.**
:func:`hydms.surrogate.deploy.deployed_fit` is the single definition -- screen, carve, fit,
calibrate -- and the model it returns is the one that ships. ``hydms.surrogate.train`` used to
build a second, uncarved fit of its own and explain *that*; the two were different models, so
the SHAP and partial-dependence tables described something with no band and the correction
belonged to something with no explanation. Both tables are written here now, off the same fit
the correction belongs to.

**With ``--save`` it persists that fit as an artifact version, and nothing more.** The version
carries **no gate report**, which :func:`hydms.artifacts.store.save` documents as the honest
state for a model nobody has certified: it cannot be promoted and
:func:`~hydms.surrogate.predict.load_surrogate` refuses it. Card #34 owns promotion.

Exit codes:

    0   the run finished and the tables were written
    2   the invocation itself was wrong (unreadable config, unknown target, unwritable path)
    3   the fit and its calibration were written, but the deployed fit could not be
        explained -- the SHAP and partial-dependence tables are empty and everything else
        is there

Cards #27 and #34.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import TextIO

import pandas as pd

from hydms import provenance
from hydms.config import Config, ConfigError, load
from hydms.data.splits import SPLIT_NAMES
from hydms.surrogate.conformal import (
    ConformalError,
    FittedConformal,
    calibrated_heads,
    compare_metrics,
)
from hydms.surrogate.deploy import (
    DeployedFit,
    deployed_fit,
    deployed_params,
    explain,
    rows_table,
    save_deployed,
)
from hydms.surrogate.evaluate import EvaluationError
from hydms.surrogate.model import (
    FIXED,
    FitLog,
    ModelError,
    ModelSettings,
    QuantileModel,
    capacity_matrix,
    quantile_metrics,
)
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.train import REPORTS, TARGETS

EXIT_OK = 0
EXIT_BAD_INVOCATION = 2
EXIT_UNEXPLAINED = 3

#: One file per question, the convention ``hydms.surrogate.train`` set.
#:
#: ``model-shap`` and ``model-pdp`` moved here from ``hydms.surrogate.train`` when the deployed
#: fit did. They describe **the model this command builds** -- the one with the calibration
#: carve in it, and therefore the only one that can carry a band. While ``train`` wrote them
#: they described its own uncarved fit, which nothing could ship: an explanation of a model
#: that does not exist downstream is leak L11's shape arriving by another door.
TABLES = ("conformal", "conformal-coverage", "conformal-rows", "model-shap", "model-pdp")

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
    parser.add_argument(
        "--save",
        action="store_true",
        help="persist the deployed fit as a new artifact version — the model, its conformal "
        "correction and the scaler. The version carries no gate report, so it cannot be "
        "promoted and predict() refuses it until one is recorded (card #34)",
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


def _save(
    fit: DeployedFit, *, settings: ModelSettings, probe: bool, stream: TextIO
) -> int:
    """``--save``: persist the deployed fit, and say what the version can and cannot do.

    A probe's model and a real run's model are the same shape, exactly as their tables are, so
    the reduced budget goes into the version's ``notes`` where a reader of
    ``artifacts/v{N}/manifest.json`` will meet it. An artifact that does not say it came from a
    probe is an artifact somebody will promote.
    """
    from hydms.artifacts.manifest import ArtifactError

    note = "screening off — a probe, not a deployable fit" if probe else "deployed fit"
    try:
        manifest = save_deployed(fit, settings=settings, notes=note)
    except ArtifactError as error:
        print(f"could not save the deployed fit: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    print(
        f"saved {manifest.version}: {', '.join(sorted(fit.payloads))} — "
        f"**no gate report**, so it cannot be promoted and predict() refuses it. Card #34 "
        f"records the gates; read it back meanwhile with "
        f"hydms.artifacts.store.load({manifest.version!r}, require_gates=False).",
        file=stream,
    )
    return EXIT_OK


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
    # Stamped before the fit (card #105). Which search chose the configuration is the train
    # record's `run_id`, read now because `deployed_params` reads the same directory.
    stamp = provenance.begin(
        cfg.root,
        protocol=provenance.DEPLOYED_FIT,
        probe=args.no_screening,
        settings={
            "screening": settings.screen_labels,
            "seed": settings.seed,
            "features": len(settings.features),
            "source_run_id": provenance.read(destination / provenance.TRAIN_RECORD).get(
                "run_id"
            ),
        },
        catboost_thread_count=FIXED.get("thread_count"),
    )
    frame, split = capacity_matrix(cfg, settings=settings)
    rows = {name: list(frame.index[split == name]) for name in SPLIT_NAMES}
    print(
        f"{len(frame)} row(s) x {len(settings.features)} feature(s); "
        f"{len(rows[TRAIN])} in {TRAIN!r}",
        file=stream,
    )

    params, chosen_from = deployed_params(destination, stream)
    log = FitLog()
    started = time.perf_counter()
    try:
        fit = deployed_fit(frame, split, params=params, settings=settings, config=cfg, log=log)
    except (ConformalError, ModelError) as error:
        print(f"the calibration failed: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    elapsed = time.perf_counter() - started
    model, conformal, calibrating = fit.model, fit.conformal, fit.calibration
    print(
        f"calibration carve: {len(calibrating)} row(s) held out of "
        f"{len(fit.fitting) + len(calibrating)} screened training row(s); the trees grow on "
        f"{len(fit.fitting)}",
        file=stream,
    )

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
        f"(card #31); the configuration came from {chosen_from}.",
        file=stream,
    )

    shap = pd.DataFrame()
    pdp = pd.DataFrame()
    unexplained = False
    try:
        shap, pdp = explain(fit, frame)
        print(
            f"  explained on {len(fit.model.record.fitted)} row(s) the trees grew on — never "
            f"on a held-out split (leak L11): {len(shap)} SHAP row(s), {len(pdp)} "
            f"partial-dependence point(s)",
            file=stream,
        )
    except EvaluationError as error:
        # Named, not raised. The tables below still write: the fit is the irreproducible half
        # and the explanation is the cheap one, which is the reading
        # `hydms.surrogate.train` took when it owned this step.
        print(f"could not explain the deployed fit: {error}", file=sys.stderr)
        print(
            "the calibration is written anyway; model-shap.csv and model-pdp.csv are empty.",
            file=sys.stderr,
        )
        unexplained = True

    tables = dict(
        zip(
            TABLES,
            (
                conformal.describe(),
                coverage,
                rows_table(fit, split),
                shap,
                pdp,
            ),
            strict=True,
        )
    )
    try:
        _write(tables, destination, stream)
        written = provenance.write(destination / provenance.CALIBRATE_RECORD, stamp.finish())
        print(f"wrote {written}", file=stream)
    except OSError as error:
        print(f"could not write the tables: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    if args.save:
        code = _save(fit, settings=settings, probe=args.no_screening, stream=stream)
        if code != EXIT_OK:
            return code

    return EXIT_UNEXPLAINED if unexplained else EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
