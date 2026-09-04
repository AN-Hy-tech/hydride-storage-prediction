"""Run feature selection inside the folds, and print what each fold chose.

    python -m hydms.surrogate.select --config hydms/config/pipeline.yaml
    python -m hydms.surrogate.select --once            # the training split, not the folds
    python -m hydms.surrogate.select --report reports/selection

**This is the slow lane.** At ``pipeline.yaml``'s Boruta budget one pass over the real
training matrix costs about eleven minutes, so the default five-fold run takes roughly an
hour. ``--once`` is the single pass -- useful for a cost check or for reproducing what the
archival selector did, and **not** a result: a selection fitted on the whole training split is
leak L6, which is what this module exists to stop, so the run says so in its own output.

Exit codes:

    0   the run finished and the tables were written
    2   the invocation itself was wrong (unreadable config, unwritable report directory)

Card #24.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from typing import TextIO

import pandas as pd

from hydms.config import Config, ConfigError, load
from hydms.data.load import load_hydride_data, parse_formula
from hydms.data.metadata import with_features, with_metadata
from hydms.data.splits import assign_splits
from hydms.descriptors.contract import CONTRACT, FeatureContract
from hydms.descriptors.featurize import featurize
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


def _write(tables: dict[str, pd.DataFrame], destination: Path, out: TextIO) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = destination / f"{name}.csv"
        table.to_csv(path)
        print(f"wrote {path}", file=out)


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """Run the selector and report. Returns the process exit code."""
    stream = out if out is not None else sys.stdout
    args = _parser().parse_args(argv)

    try:
        cfg = load(args.config)
    except (ConfigError, OSError) as error:
        print(f"could not read the configuration: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION

    settings = SelectionSettings.from_config(cfg)
    if args.no_screening:
        settings = replace(settings, screen_labels=False)

    frame, split = _matrix(cfg, all_features=args.all_features)
    print(
        f"{len(frame)} row(s) x {len(frame.columns)} column(s); "
        f"{int((split == TRAIN).sum())} in {TRAIN!r}",
        file=stream,
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
        tables["selection-once-trace"] = selection.trace()
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
        tables["selection-per-fold"] = folds.per_fold()
        tables["selection-stability"] = folds.stability()
        for fold, selection in zip(folds.folds, folds.selections, strict=True):
            tables[f"selection-trace-{fold.name}"] = selection.trace()

    destination = args.report or (cfg.paths.reports / "selection")
    try:
        _write(tables, destination, stream)
    except OSError as error:
        print(f"could not write the report: {error}", file=sys.stderr)
        return EXIT_BAD_INVOCATION
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
