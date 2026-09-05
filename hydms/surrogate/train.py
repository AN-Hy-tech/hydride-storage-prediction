"""Fit the capacity model through card #88's protocol, and write down what it cost.

    python -m hydms.surrogate.train --target capacity
    python -m hydms.surrogate.train --target capacity --trials 5     # a cheaper probe
    python -m hydms.surrogate.train --target capacity --budget       # fits nothing

**This is the slow lane**, and the budget is a product: ``model.cv_folds`` outer folds x
``model.inner_cv_folds`` inner folds x ``model.optuna_trials`` per outer fold, plus one refit
per outer fold and one deployed fit. At the archival trial count of 300 that is 4,500 fits and
about 43 hours on this machine; ``pipeline.yaml`` sets 25 and says why. ``--budget`` is the
cheap half -- it reads the fit table an earlier run left on disk and reports the measured cost
per fit against the configured product, so the arithmetic can be checked without paying it.

**Nothing here is published as an artifact.** Card #34 owns ``artifacts/v1``: the version
directory, the manifest, the gate report embedded beside it. This command produces the
evidence that a version *could* honestly be cut -- the per-fold scores, the chosen
hyperparameters, the row identities of every fit, the **row-level out-of-fold predictions**
card #29 puts an interval around, and the deployed fit's SHAP and partial-dependence tables --
and leaves the promotion to the card that owns it.

**It is run once, and everything downstream reads what it wrote.** The explainability tables
are computed here rather than by :mod:`hydms.surrogate.evaluate` because they need the
*deployed fit*, which exists only inside this run; recomputing them would mean a second fit,
and two fits mean the chapter describes a different model from the one that ships. That is
also why card #34 promotes from this run rather than making its own.

Exit codes:

    0   the run finished and the tables were written
    2   the invocation itself was wrong (unreadable config, unknown target, unwritable path)
    3   the run finished and its numbers were written, but the deployed fit could not be
        explained -- the SHAP and partial-dependence tables are missing and everything else
        is there

**Three, and not two, because of what this command costs.** A failure in the explainability
step after three hours of boosting must not throw away the scores; the run is the expensive,
irreproducible half and the explanation is the cheap one. So the tables are written either
way, the failure is named on stderr, and the exit code says which of the two states this is
rather than letting a partial success look like a whole one.

Card #26; the explainability tables and the run record are card #29's.
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

from hydms.config import Config, ConfigError, load
from hydms.surrogate.evaluate import EXPLAINABILITY, EvaluationError, pdp_table, shap_table
from hydms.surrogate.model import (
    Configuration,
    FitLog,
    ModelSettings,
    QuantileModel,
    capacity_contender,
    capacity_matrix,
    final_fit,
)
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.validation import Evaluation, nested_scores

EXIT_OK = 0
EXIT_BAD_INVOCATION = 2
EXIT_UNEXPLAINED = 3

#: The only target there is. The flag exists so that a run says which one it fitted -- the PRD
#: has more objectives waiting behind the freeze (PRD section 5, S8 onward) -- and so the
#: refusal names what exists rather than failing on a column lookup somewhere deeper.
TARGETS: tuple[str, ...] = ("capacity",)

#: Where the tables land, under the configured reports path.
REPORTS = "model"

#: One file per question, so a reader opens the one they came for.
#:
#: ``model-out-of-fold`` is the row-level one and it is the reason card #29 can put an interval
#: around anything: before it, ``_score_fold`` computed ``model.predict(scored)``, handed it to
#: the metrics and dropped the frame, so the only resamplable object a run left behind was five
#: fold scores -- a spread card #24 measured to be confounded with training size. The
#: explainability pair is written here rather than by ``hydms.surrogate.evaluate`` because they
#: need the **deployed fit**, which exists only inside this run; recomputing them would mean a
#: second fit, and two fits mean the chapter describes a different model from the one that ships.
#:
#: ``model-run`` is the smallest and the one a reader must not lose: **a probe's tables and a
#: real run's tables are the same shape.** This command says
#: ``These numbers are a cost check, not a result`` on stdout, and stdout is not what card #37
#: reads six weeks later -- so the reduced budget is written down beside the numbers it
#: produced, and :mod:`hydms.surrogate.evaluate` refuses to publish a document that does not
#: say which kind of run it came from.
TABLES = (
    "model-per-fold",
    "model-record",
    "model-chosen",
    "model-fits",
    "model-out-of-fold",
    "model-shap",
    "model-pdp",
    "model-run",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.surrogate.train",
        description=(
            "CatBoost MultiQuantile through the nested, group-aware protocol: early stopping "
            "on rows the score never sees (leaks L1 and L5)."
        ),
    )
    parser.add_argument(
        "--target",
        default=TARGETS[0],
        help=f"what to fit; one of {', '.join(TARGETS)}",
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=None,
        help="override model.optuna_trials for this run — a probe, not a result, and the run "
        "says so in its own output",
    )
    parser.add_argument(
        "--no-screening",
        action="store_true",
        help="skip the CleanLab stage — faster, and not what a real run does",
    )
    parser.add_argument(
        "--skip-final",
        action="store_true",
        help="stop after cross-validation; do not make the deployed fit",
    )
    parser.add_argument(
        "--budget",
        action="store_true",
        help="fit nothing: report the configured product against the cost an earlier run "
        "measured, from the fit table on disk",
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


def _write(tables: dict[str, pd.DataFrame], destination: Path, out: TextIO) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = destination / f"{name}.csv"
        table.to_csv(path)
        print(f"wrote {path}", file=out)


def _budget(cfg: Config, settings: ModelSettings, source: Path, stream: TextIO) -> int:
    """``--budget``: the product, and what a fit actually cost the last time one was measured.

    Fits nothing. The measured half comes from ``model-fits.csv``, which every run writes, so
    the projection is a reading of this machine rather than a number somebody remembered.
    """
    fits = cfg.model.cv_folds * cfg.model.inner_cv_folds * settings.optuna_trials
    print(
        f"{cfg.model.cv_folds} outer x {cfg.model.inner_cv_folds} inner x "
        f"{settings.optuna_trials} trial(s) = {fits} tuning fit(s), plus "
        f"{cfg.model.cv_folds} refit(s) and one deployed fit",
        file=stream,
    )

    table = source / f"{TABLES[3]}.csv"
    if not table.exists():
        print(
            f"no fit has been measured on this machine: {table} does not exist. Run the "
            f"command without --budget, or with --trials, and it will be written.",
            file=stream,
        )
        return EXIT_OK

    try:
        measured = pd.read_csv(table)
    except (OSError, ValueError) as error:
        print(f"could not read {table}: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    if "seconds" not in measured.columns or measured.empty:
        print(f"{table} records no fit times, so there is nothing to project from.", file=stream)
        return EXIT_OK

    seconds = float(measured["seconds"].mean())
    print(
        f"{len(measured)} fit(s) measured in {table.name}: {seconds:.1f} s each on average, "
        f"{measured['seconds'].min():.1f}-{measured['seconds'].max():.1f} s. "
        f"{fits} tuning fit(s) at that rate is {fits * seconds / 3600:.1f} h before pruning.",
        file=stream,
    )
    return EXIT_OK


def _per_fold(evaluation: Evaluation) -> pd.DataFrame:
    """The per-fold scores with the fold sizes beside them, which is how they must be read.

    Card #24 measured screening removing between 15 and 144 of a fold's roughly 710 training
    rows, so one outer fold fits on 571 rows where another fits on 704 -- a 23 % difference in
    training size before the model sees anything. Part of the spread in any column here is
    that and not the model, and a table of scores with no row counts in it invites the other
    reading. ``rows_fitted`` is carried as a metric for exactly this reason.
    """
    table = evaluation.per_fold.copy()
    held_out = {fold.name: len(fold.test) for fold in evaluation.outer}
    table["held_out_rows"] = table["fold"].map(held_out)
    return table.set_index(["model", "fold"])


def _record(evaluation: Evaluation, settings: ModelSettings) -> pd.DataFrame:
    """The averaged score per contender, with the feature set it belongs to named in the row.

    Card #25's box, carried here rather than in a comment: these numbers describe a **fixed**
    fourteen-feature pipeline, not the procedure that chose those fourteen -- whose own five
    folds each selected between 16 and 20 features. A reader who takes this as an estimate of
    "the pipeline including selection" is reading a number nobody measured.
    """
    rows = []
    for record in evaluation.records:
        rows.append(
            {
                "model": record.model,
                "features": len(settings.features),
                "feature_set": "hydms.descriptors.contract.SELECTED",
                "selection_refitted_per_fold": False,
                "tuned_on_folds": len(record.tuned_on),
                "scored_on_folds": len(record.scored_on),
                **record.metrics,
            }
        )
    return pd.DataFrame.from_records(rows).set_index("model")


def _chosen(evaluation: Evaluation) -> pd.DataFrame:
    """What each outer fold's search settled on, one row per (model, fold)."""
    rows = [
        {"model": model, "fold": fold, **configuration.row()}
        for (model, fold), configuration in sorted(evaluation.chosen.items())
    ]
    return pd.DataFrame.from_records(rows).set_index(["model", "fold"])


def _deployed(evaluation: Evaluation) -> tuple[str, Configuration]:
    """The configuration the deployed fit uses, and the fold it came from.

    **Chosen on an inner-fold number, never on an outer one.** Every configuration in
    ``evaluation.chosen`` carries the pinball loss its own search achieved on the inner folds,
    and that is what is compared here. The outer scores -- the ones this run reports -- take no
    part in the choice, which is what keeps picking a configuration from being leak L2 in a
    new place: ``benchmark_model_selection.py:335-336`` ranked ensemble members by the
    validation score it then published.
    """
    chosen: Mapping[tuple[str, str], Configuration] = evaluation.chosen
    (_, fold), configuration = min(chosen.items(), key=lambda entry: entry[1].objective)
    return fold, configuration


def _run(cfg: Config, settings: ModelSettings, *, probe: bool) -> pd.DataFrame:
    """One row saying what kind of run wrote the tables beside it.

    The `PROBE:` line this command prints goes to a terminal somebody closes. This goes to
    disk, in the same directory as the numbers, and `hydms.surrogate.evaluate` puts it at the
    top of the published document -- because the failure it guards against is not a reader who
    misunderstands a caveat, it is a reader who never saw one.
    """
    return pd.DataFrame.from_records(
        [
            {
                "probe": probe,
                "optuna_trials": settings.optuna_trials,
                "configured_optuna_trials": cfg.model.optuna_trials,
                "screening": settings.screen_labels,
                "cv_folds": cfg.model.cv_folds,
                "inner_cv_folds": cfg.model.inner_cv_folds,
                "feature_set": "hydms.descriptors.contract.SELECTED",
                "features": len(settings.features),
                "seed": settings.seed,
            }
        ]
    )


def _explain(
    model: QuantileModel, frame: pd.DataFrame, stream: TextIO
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """SHAP and partial dependence for the deployed fit, on **its own training rows**.

    Leak L11: ``benchmark_model_selection.py:1375,1383,1394`` computed both on ``X_test``,
    which is what makes ``REPORT.md`` section 6.1 a test-set artefact. The rows handed over
    here are ``model.record.fitted`` -- the rows this fit actually grew on, after screening,
    read off the fit's own record rather than re-derived from the split. Re-deriving them
    would give the split's training rows, which is *not* the same set: screening drops some of
    them, and an explanation averaged over rows the model never saw is a different object from
    the one section 6.1 claims to be.

    The population's name goes into a ``computed_on`` column on both tables, and the L11
    sentinel asserts that name is not in
    :data:`~hydms.surrogate.validation.HELD_OUT_SPLITS`.
    """
    rows = frame.loc[list(model.record.fitted)]
    shap = shap_table(model, rows, computed_on=EXPLAINABILITY)
    pdp = pdp_table(model, rows, computed_on=EXPLAINABILITY)
    print(
        f"  explained on {len(rows)} {EXPLAINABILITY!r} row(s) — never on a held-out split "
        f"(leak L11): {len(shap)} SHAP row(s), {len(pdp)} partial-dependence point(s)",
        file=stream,
    )
    return shap, pdp


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """Run the protocol and report. Returns the process exit code."""
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

    settings = ModelSettings.from_config(cfg)
    if args.trials is not None:
        if args.trials < 1:
            print(f"--trials must be at least 1, got {args.trials}", file=sys.stderr)
            return EXIT_BAD_INVOCATION
        settings = replace(settings, optuna_trials=args.trials)
    if args.no_screening:
        settings = replace(settings, screen_labels=False)

    destination = _destination(cfg, args.report)
    if args.budget:
        return _budget(cfg, settings, destination, stream)

    probe = args.trials is not None or args.no_screening
    if probe:
        # Said once, loudly, in the run's own output. A table written by a reduced run and a
        # table written by a real one are the same shape, and the difference has to be
        # somewhere a reader will see it.
        print(
            f"PROBE: {settings.optuna_trials} trial(s) against the configured "
            f"{cfg.model.optuna_trials}"
            f"{', screening off' if not settings.screen_labels else ''}. "
            f"These numbers are a cost check, not a result.",
            file=stream,
        )

    frame, split = capacity_matrix(cfg, settings=settings)
    print(
        f"{len(frame)} row(s) x {len(settings.features)} feature(s) "
        f"({', '.join(settings.features[:3])}, ...); "
        f"{int((split == TRAIN).sum())} in {TRAIN!r}",
        file=stream,
    )

    log = FitLog()
    started = time.perf_counter()
    evaluation = nested_scores(
        frame, split, [capacity_contender(settings=settings, log=log)]
    )
    elapsed = time.perf_counter() - started
    print(
        f"nested cross-validation: {len(evaluation.outer)} outer fold(s) in "
        f"{elapsed / 60:.1f} min",
        file=stream,
    )
    for record in evaluation.records:
        scores = ", ".join(f"{k}={v:.4f}" for k, v in sorted(record.metrics.items()))
        print(f"  {record.model}: {scores}", file=stream)

    fold, configuration = _deployed(evaluation)
    shap = pd.DataFrame()
    pdp = pd.DataFrame()
    unexplained = False
    if not args.skip_final:
        print(
            f"deployed fit: the configuration {fold!r} chose, on its inner-fold objective "
            f"{configuration.objective:.5f}",
            file=stream,
        )
        model = final_fit(
            frame, split, params=configuration.params, settings=settings, log=log
        )
        print(
            f"  grown on {len(model.record.fitted)} row(s), stopped on "
            f"{len(model.record.eval_on)} at iteration {model.record.best_iteration} "
            f"({model.record.trees} tree(s), {model.record.seconds:.1f} s); "
            f"{len(model.record.scored_on)} test row(s) named and not read",
            file=stream,
        )
        try:
            shap, pdp = _explain(model, frame, stream)
        except EvaluationError as error:
            # Named, not raised. Everything below still writes: a run that has already cost
            # hours must not lose its scores because SHAP would not compute.
            print(
                f"could not explain the deployed fit: {error}",
                file=sys.stderr,
            )
            print(
                "the scores are written anyway; model-shap.csv and model-pdp.csv are empty.",
                file=sys.stderr,
            )
            unexplained = True

    tables = dict(
        zip(
            TABLES,
            (
                _per_fold(evaluation),
                _record(evaluation, settings),
                _chosen(evaluation),
                log.table(),
                evaluation.out_of_fold,
                shap,
                pdp,
                _run(cfg, settings, probe=probe),
            ),
            strict=True,
        )
    )
    try:
        _write(tables, destination, stream)
    except OSError as error:
        print(f"could not write the tables: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    return EXIT_UNEXPLAINED if unexplained else EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
