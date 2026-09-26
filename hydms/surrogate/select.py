"""Run feature selection inside the folds, and print what each fold chose.

    python -m hydms.surrogate.select --config hydms/config/pipeline.yaml
    python -m hydms.surrogate.select --once            # the training split, not the folds
    python -m hydms.surrogate.select --report reports/selection
    python -m hydms.surrogate.select --emit-comparison # publish, fitting nothing

**This is the slow lane.** At ``pipeline.yaml``'s Boruta budget one pass over the real
training matrix costs about eleven minutes, so the default five-fold run takes roughly an
hour. ``--once`` is the single pass -- useful for a cost check or for reproducing what the
archival selector did, and **not** a result: a selection fitted on the whole training split is
leak L6, which is what this module exists to stop, so the run says so in its own output.

``--emit-comparison`` is the cheap half and card #25's runnable check: it fits nothing, reads
the tables the runs above left on disk, and publishes the old-22-versus-new-N write-up from
them (:mod:`hydms.surrogate.comparison`). It dates the write-up from the run record the
five-fold run writes (:data:`hydms.provenance.SELECTION_RECORD`), and says *not recorded* when
there is none. A file's modification time is not a run date (card #106). Regenerating the document therefore costs a second
rather than an hour, which is the only reason it can be checked against the code that
generates it.

Exit codes:

    0   the run finished and the tables were written
    2   the invocation itself was wrong (unreadable config, unwritable report directory)

Card #24.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from typing import TextIO

import pandas as pd

from hydms import provenance
from hydms.config import Config, ConfigError, load
from hydms.data.load import load_hydride_data, parse_formula
from hydms.data.metadata import with_features, with_metadata
from hydms.data.splits import assign_splits
from hydms.descriptors.contract import CONTRACT, FeatureContract
from hydms.descriptors.featurize import featurize
from hydms.surrogate.comparison import DOCUMENT, Comparison, ComparisonError
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.selection import (
    SelectionSettings,
    select_across_folds,
    select_features,
)

EXIT_OK = 0
EXIT_BAD_INVOCATION = 2

#: The feature this run leaves out of the candidate set by default. **Drop the feature, keep
#: the rows** -- card #24's trade, decided by measuring both sides rather than by argument.
#:
#: **What carrying it costs.** ``dev_Gordy_electonegativity`` is not computable from the
#: citable 2024 Oliynyk table for 21 of the dataset's 55 elements, so the full 22 refuse **266
#: of the 1,279 rows**, 193 of the 893 training rows. The loss is not spread evenly: AB5 loses
#: 67 of 143 training rows (46.9 %) and MIC 37 of 87 (42.5 %), against AB2's 28 of 260 (10.8 %)
#: and LEA's none. AC-6 scores one fold per alloy class, so carrying the feature would report
#: the AB5 and MIC verdicts over about half of each class -- which is the number the leave-one-
#: class-out result exists to produce. Dropping it costs one row instead: the remaining 21
#: cover 1,278 of 1,279, the exception being ``Eu1Ni5``, whose europium blocks all six JARVIS
#: features.
#:
#: **What dropping it costs, measured on the 700 training rows where the comparison is
#: controlled** -- same rows, same seed, the configured Boruta budget, only the column varying.
#: With it, Boruta confirms 13 features including it. Without it, 14 -- and **twelve of the
#: thirteen are the same**. Its absence is taken up by ``dev_gilmor_number_of_valence_electron``
#: and by ``temperature(K)``, which the 22-feature run confirms only through the must-keep. So
#: the feature is real -- Boruta selects it whenever it can -- but it is not carrying anything
#: the rest of the set cannot: it displaces, rather than adds.
#:
#: A quarter of the training rows against a substitutable descriptor is not a close trade.
#: ``--all-features`` runs the other way, for the comparison card #25 publishes.
COSTLY_FEATURE = "dev_Gordy_electonegativity"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.surrogate.select",
        description="Port of Boruta_FeatEng.py, run inside the training folds (leak L6).",
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="one pass over the whole training split — the archival, leaking shape, for cost "
        "comparison only",
    )
    parser.add_argument(
        "--all-features",
        action="store_true",
        help=f"keep {COSTLY_FEATURE!r} as a candidate, at the cost of 266 rows",
    )
    parser.add_argument(
        "--no-screening",
        action="store_true",
        help="skip the CleanLab stage — faster, and not what a real run does",
    )
    parser.add_argument(
        "--emit-comparison",
        action="store_true",
        help="publish the old-22 vs new-N comparison from tables already on disk — fits "
        "nothing, and is card #25's runnable check",
    )
    parser.add_argument(
        "--publish",
        type=Path,
        default=None,
        help="where --emit-comparison writes; defaults to the configured reports path",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="a directory to write the CSV tables into; defaults to the configured reports path",
    )
    return parser


def _matrix(cfg: Config, *, all_features: bool) -> tuple[pd.DataFrame, pd.Series]:
    """The joined record and feature matrix, and #13's split assignment over it.

    The rows are chosen by asking the contract which compositions it can serve, using the
    idiom :func:`~hydms.descriptors.featurize.featurize`'s own docstring documents, rather
    than by naming formulae. The join is
    :func:`~hydms.data.metadata.with_features`, never a ``concat`` -- ``temperature(K)`` is a
    column of the raw file *and* one of the features, and that function is the one that checks
    the two agree before taking the matrix's ``float64`` copy.
    """
    names = cfg.columns
    # `load_hydride_data()` resolves `paths.raw` itself and knows the filename; naming the
    # file here would be a second answer to where the data is.
    record = with_metadata(load_hydride_data())
    split = assign_splits(record)

    contract = (
        CONTRACT
        if all_features
        else FeatureContract.from_names(
            [name for name in CONTRACT.names if name != COSTLY_FEATURE]
        )
    )
    keep = [
        label
        for label, formula in record[names.formula].items()
        if contract.computability(parse_formula(formula)).complete
    ]
    usable = record.loc[keep]
    features = featurize(
        usable[names.formula], usable[names.temperature], contract=contract
    )
    return with_features(usable, features), split.loc[keep]


def _record_name(args: argparse.Namespace) -> str:
    """The run record's file name, carrying the same suffix as the tables beside it.

    Only the default five-fold run, the one card #25 publishes, writes
    :data:`~hydms.provenance.SELECTION_RECORD`. Every variant inserts what varied, so a probe
    never overwrites the record of the run the published date is read from.
    """
    varied = (
        ("-once" if args.once else "")
        + ("-all-features" if args.all_features else "")
        + ("-unscreened" if args.no_screening else "")
    )
    stem = provenance.SELECTION_RECORD.removesuffix(provenance.RECORD_SUFFIX)
    return f"{stem}{varied}{provenance.RECORD_SUFFIX}"


def _begin(
    cfg: Config, settings: SelectionSettings, args: argparse.Namespace
) -> provenance.Stamp:
    """Stamp the run before the matrix is built and before Boruta, never after.

    Any of ``--once``, ``--all-features`` and ``--no-screening`` makes the run a **probe**. None
    of them is the run the published comparison calls "selection": ``--once`` is leak L6, and the
    other two are the contrasts card #25 sets beside the result.
    """
    return provenance.begin(
        cfg.root,
        protocol=provenance.FEATURE_SELECTION,
        probe=bool(args.once or args.all_features or args.no_screening),
        settings={
            "once": bool(args.once),
            "all_features": bool(args.all_features),
            "screening": settings.screen_labels,
            "boruta_max_iter": settings.boruta_max_iter,
            "boruta_max_depth": settings.boruta_max_depth,
            "boruta_estimators": settings.boruta_estimators,
            "variance_threshold": settings.variance_threshold,
            "vif_threshold": settings.vif_threshold,
            "seed": settings.seed,
        },
    )


def _write(tables: dict[str, pd.DataFrame], destination: Path, out: TextIO) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = destination / f"{name}.csv"
        table.to_csv(path)
        print(f"wrote {path}", file=out)


def _emit(cfg: Config, args: argparse.Namespace, stream: TextIO) -> int:
    """``--emit-comparison``: publish the write-up from the tables the runs left behind.

    Nothing is fitted here. The expensive runs are the ones above; this reads what they
    wrote, so the published document can be regenerated -- and therefore checked -- at any
    time without an hour of Boruta.
    """
    source = args.report or (cfg.paths.reports / "selection")
    destination = args.publish or (cfg.paths.reports / "feature_selection")
    try:
        comparison = Comparison.read(source, config=cfg)
    except (ComparisonError, OSError, KeyError, ValueError) as error:
        print(f"could not read the selection tables: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    print(
        f"{comparison.folds} fold(s) from {source}, run date {comparison.dated_text}",
        file=stream,
    )
    print(f"consensus ({len(comparison.consensus)}): {', '.join(comparison.consensus)}", file=stream)
    print(f"union ({len(comparison.union)}): {', '.join(comparison.union)}", file=stream)
    print(
        f"declared ({len(comparison.selected)}): {', '.join(comparison.selected.names)}",
        file=stream,
    )
    if tuple(comparison.selected.names) != comparison.consensus:
        # Not an error: the declaration is a decision and a future card may take a different
        # one. It is printed because a silent divergence between the contract and the run it
        # cites is exactly the drift this document exists to prevent.
        print(
            "NOTE: the declared set is not this run's consensus. That is a decision, and "
            "reports/feature_selection/old_vs_new.md must say which reading it published.",
            file=stream,
        )

    try:
        _write(comparison.tables(), destination, stream)
        # The record travels with the evidence, so the published directory dates itself the
        # same way the run directory does when it is read back.
        record = source / provenance.SELECTION_RECORD
        if record.is_file() and record.resolve() != (destination / record.name).resolve():
            shutil.copyfile(record, destination / record.name)
            print(f"wrote {destination / record.name}", file=stream)
        document = destination / DOCUMENT
        document.write_text(comparison.to_markdown(), encoding="utf-8")
    except OSError as error:
        print(f"could not write the comparison: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    print(f"wrote {document}", file=stream)
    return EXIT_OK


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """Run the selector and report. Returns the process exit code."""
    stream = out if out is not None else sys.stdout
    args = _parser().parse_args(argv)

    try:
        cfg = load(args.config)
    except (ConfigError, OSError) as error:
        print(f"could not read the configuration: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    if args.emit_comparison:
        return _emit(cfg, args, stream)

    settings = SelectionSettings.from_config(cfg)
    if args.no_screening:
        settings = replace(settings, screen_labels=False)

    stamp = _begin(cfg, settings, args)
    frame, split = _matrix(cfg, all_features=args.all_features)
    print(
        f"{len(frame)} row(s) x {len(frame.columns)} column(s); "
        f"{int((split == TRAIN).sum())} in {TRAIN!r}",
        file=stream,
    )

    # What varied is in the file name, so a probe cannot silently overwrite a result. The
    # five-fold screened run over the 21 candidates -- the one card #25 publishes -- is the
    # unsuffixed one, because it is the run this project means when it says "selection".
    suffix = ("-all-features" if args.all_features else "") + (
        "-unscreened" if args.no_screening else ""
    )

    tables: dict[str, pd.DataFrame] = {}
    if args.once:
        print(
            "\n--once: ONE selection over the whole training split. This is the archival "
            "shape and it is leak L6 — every fold's held-out rows help choose the features "
            "the fold is scored on. Do not report it as a result.\n",
            file=stream,
        )
        selection = select_features(
            frame, list(frame.index[split == TRAIN]), settings=settings
        )
        print(selection.trace().to_string(), file=stream)
        print(
            f"\n{len(selection)} feature(s) from {len(selection.candidates)}: "
            f"{', '.join(selection.features)}",
            file=stream,
        )
        tables[f"selection-once{suffix}"] = pd.DataFrame.from_records(
            [{"run": "training-split", **selection.record()}]
        ).set_index("run")
        tables[f"selection-once{suffix}-trace"] = selection.trace()
    else:
        folds = select_across_folds(frame, split, settings=settings)
        print(f"\n{len(folds)} outer fold(s), grouped on the canonical composition:\n", file=stream)
        print(folds.per_fold().drop(columns=["features"]).to_string(), file=stream)
        print("\nhow often each feature was chosen:\n", file=stream)
        print(folds.stability().to_string(), file=stream)
        consensus, union = folds.consensus(), folds.union()
        print(
            f"\nconsensus ({len(consensus)}): {', '.join(consensus)}"
            f"\nunion ({len(union)}): {', '.join(union)}",
            file=stream,
        )
        tables[f"selection-per-fold{suffix}"] = folds.per_fold()
        tables[f"selection-stability{suffix}"] = folds.stability()
        for fold, selection in zip(folds.folds, folds.selections, strict=True):
            tables[f"selection-trace-{fold.name}{suffix}"] = selection.trace()

    destination = args.report or (cfg.paths.reports / "selection")
    record = destination / _record_name(args)
    try:
        _write(tables, destination, stream)
        provenance.write(record, stamp.finish())
    except OSError as error:
        print(f"could not write the report: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    print(f"wrote {record}", file=stream)
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
