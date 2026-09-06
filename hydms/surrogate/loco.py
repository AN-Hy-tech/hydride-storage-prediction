"""Leave-one-alloy-class-out: how far the model falls when the family is new. Card #30.

    python -m hydms.surrogate.loco --target capacity            # the run
    python -m hydms.surrogate.loco --target capacity --budget   # fits nothing, costs it
    python -m hydms.surrogate.loco --emit                       # rebuild the write-up

**The single most important validation number in this thesis, and it is expected to be bad.**
Beltrame et al. 2025 found hydride models accurate *within* a family and poor across families;
Li et al. 2025 found heuristic splits "mostly test interpolation rather than true
extrapolation". The random-split R2 this project publishes is an interpolation number. This
command produces the extrapolation one, and AC-6 asks only that the two be **reported side by
side** -- not that the second clears a bar. A model that transfers badly across families is a
finding about hydrides, not a failure of the fit, and it is what tells Architecture A how far a
candidate may stray from known chemistry (#48).

**This is train.py's protocol with one argument changed, and that is the whole design.**
:func:`~hydms.surrogate.validation.nested_scores` takes the outer partition as a parameter;
passing :func:`~hydms.surrogate.validation.leave_one_class_out` gives AC-6's protocol through
the same tuning, the same screening, the same scaler discipline and the same nesting assertion.
Nothing here re-implements scoring. A second scoring path is exactly the duplication the board
is cut by layer to prevent, and it is how two commands came to build two different "deployed
fits" (#34's narrative).

**The classes are cut from the training split only**, because ``nested_scores`` selects the
training rows itself. So a class fold holds out every training row of that family and tunes on
the other nine; ``val`` and ``test`` take no part, exactly as in the random-split run.

**A class is never silently dropped.** Every class appears in ``loco-per-class.csv`` with its
support beside its score, and a class whose score cannot *mean* anything -- fewer than two
held-out rows, or a held-out target with no variance, which makes R2 undefined rather than bad
-- is written with its metrics, ``estimable`` false and the reason in words. The averages
exclude it and the summary says how many were excluded. The threshold is a property of the
metric, not a taste: R2 is a ratio to the total sum of squares, and a constant column makes that
zero. Nothing here drops a class for being *small*; a 19-row LEA fold is a real, readable
result provided its support is printed next to it, which is why the per-class table carries
``rows_scored`` and ``compositions_scored`` as columns rather than as a caveat in prose.

**Two averages, because they answer different questions.** ``macro_r2`` weights every family
equally and is the number AC-6 is about -- the answer to "how does this do on a family it has
not seen", where every family counts once. ``weighted_r2`` weights by support, so AB2 and AB5
alone carry 403 of the 893 training rows and the number is mostly about them; it is the right
average for "how many rows would this get wrong" and the wrong one for "how does it transfer".

**Which of the two is larger is not asserted anywhere here, and that is deliberate.** The first
draft of this docstring claimed the weighted mean flatters the result. A sentinel-budget probe
measured the opposite -- macro 0.2240 against weighted 0.1664, because the two largest families
happened to score below the mean -- so the direction depends on the run and the document
computes it rather than predicting it. The claim that survives measurement is only that the two
differ and mean different things.

**The cost, before anyone starts it.** The budget is ``classes`` x ``model.inner_cv_folds`` x
``model.optuna_trials``, and there are ten classes where the random-split run has five outer
folds -- so this run is about **twice** the one that already takes hours. ``--budget`` reads the
fit times an earlier run measured into ``reports/model/model-fits.csv`` and projects from them,
so the arithmetic can be checked without paying it. Run the real thing deliberately, once, and
commit its tables.

Exit codes:

    0   the run finished and the tables were written, or --budget/--emit did their cheap job
    2   the invocation itself was wrong (unreadable config, unknown target, tables absent)

Card #30; AC-6 reads what this writes.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import TextIO

import pandas as pd

from hydms.config import Config, ConfigError, load
from hydms.data.canonical import alloy_classes, group_keys
from hydms.surrogate.model import (
    FitLog,
    ModelSettings,
    capacity_contender,
    capacity_matrix,
)
from hydms.surrogate.scaler import TRAIN
from hydms.surrogate.validation import Evaluation, leave_one_class_out, nested_scores

EXIT_OK = 0
EXIT_BAD_INVOCATION = 2

#: The only target there is; the flag exists so a run says which one it scored.
TARGETS: tuple[str, ...] = ("capacity",)

#: Where the tables land, under the configured reports path. Its own directory rather than
#: ``model/``, because these are a different protocol's numbers and a reader who confuses them
#: with the random-split ones has made precisely the mistake AC-6 exists to prevent.
REPORTS = "loco"

#: The published document, rebuilt from the tables by ``--emit`` and never written by hand.
DOCUMENT = "loco.md"

#: One file per question.
#:
#: ``loco-run`` is the small one nobody may lose: a probe's tables and a real run's tables are
#: the same shape, so which kind produced these numbers is written *beside* them and not only
#: on a terminal somebody closes. ``--emit`` refuses to publish a document that does not say.
TABLES = ("loco-per-class", "loco-summary", "loco-chosen", "loco-run")

#: The random-split run's averaged record, which AC-6 requires this number to be reported
#: *alongside*. Read, never recomputed -- recomputing it here would be a second answer to a
#: question :mod:`hydms.surrogate.train` already answered, and the two would drift.
RANDOM_SPLIT_TABLE = Path("model") / "model-record.csv"

#: A held-out fold needs at least this many rows for a score to be arithmetic rather than an
#: accident. Two, because R2 over one row is either zero or undefined depending on how the
#: total sum of squares is taken, and neither is a claim. Anything above two is a judgement
#: about noise, and this module makes none -- it prints the support instead.
MIN_SCORED_ROWS = 2

#: How many classes the curated dataset has, used only by ``--budget`` -- which must cost the
#: run *without* loading the data, since the whole point of the flag is that it is free. The
#: run itself never reads this: it counts the classes it was actually given, and the golden
#: record pins the file's own count (``tests/data/test_golden.py``, ``alloy_classes``).
CLASSES = 10


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hydms.surrogate.loco",
        description=(
            "Leave-one-alloy-class-out cross-validation: the same nested protocol as "
            "`train`, with the outer partition cut by alloy class instead of at random."
        ),
    )
    parser.add_argument("--target", default=TARGETS[0], help=f"one of {', '.join(TARGETS)}")
    parser.add_argument(
        "--config", type=Path, default=None, help="a pipeline YAML; defaults to the packaged one"
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=None,
        help="override model.optuna_trials for this run -- a probe, not a result, and the "
        "tables say so",
    )
    parser.add_argument(
        "--no-screening",
        action="store_true",
        help="skip the CleanLab stage -- faster, and not what a real run does",
    )
    parser.add_argument(
        "--budget",
        action="store_true",
        help="fit nothing: report the class count against the cost an earlier run measured",
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help="fit nothing: rebuild the published document from the committed tables",
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


# --------------------------------------------------------------------------------------
# The tables
# --------------------------------------------------------------------------------------


def per_class(evaluation: Evaluation, training: pd.DataFrame) -> pd.DataFrame:
    """One row per alloy class: what it scored, over how much, and whether that means anything.

    ``rows_scored`` is a column and not a footnote. The ten classes range from 19 held-out rows
    to 260, and an R2 over 19 is not the same claim as an R2 over 260 -- a table of scores with
    no counts in it invites exactly the reading AC-6 exists to prevent.

    ``compositions_scored`` sits beside it because the two differ: the same material appears
    under more than one temperature, and it is the composition count that says how many
    independent materials the number rests on.
    """
    classes = alloy_classes(training)
    keys = group_keys(training)
    target = load().columns.target

    held_out = {fold.name: list(fold.test) for fold in evaluation.outer}
    table = evaluation.per_fold.copy()
    table["alloy_class"] = [str(name).split(":", 1)[-1] for name in table["fold"]]
    table["rows_scored"] = [len(held_out[name]) for name in table["fold"]]
    table["compositions_scored"] = [
        int(keys.loc[held_out[name]].nunique()) for name in table["fold"]
    ]
    table["rows_in_class"] = [
        int((classes == label).sum()) for label in table["alloy_class"]
    ]

    verdicts = [
        _estimable(training.loc[held_out[name], target]) for name in table["fold"]
    ]
    table["estimable"] = [ok for ok, _ in verdicts]
    table["not_estimable_because"] = [reason for _, reason in verdicts]
    return table.set_index(["model", "alloy_class"]).sort_index()


def _estimable(target: pd.Series) -> tuple[bool, str]:
    """Whether a class fold's R2 is a number at all, and if not, why not in words.

    Deliberately not a judgement about sample size. R2 is one minus a ratio to the total sum
    of squares, so it is *undefined* when the held-out target does not vary, and meaningless
    below two rows; both conditions are arithmetic. A class that is merely small is estimable
    and is reported with its support, because "too small to be interesting" is the reader's
    call and a filter here would make it silently on their behalf.
    """
    if len(target) < MIN_SCORED_ROWS:
        return False, (
            f"{len(target)} held-out row(s); R2 needs at least {MIN_SCORED_ROWS} to be a "
            f"ratio to anything"
        )
    if float(target.var(ddof=0)) == 0.0:
        return False, (
            f"every held-out row carries the same target ({float(target.iloc[0]):.4g}), so the "
            f"total sum of squares is zero and R2 is undefined rather than bad"
        )
    return True, ""


def summary(table: pd.DataFrame, random_split: pd.DataFrame | None) -> pd.DataFrame:
    """The two averages, the count behind each, and the random-split number beside them.

    AC-6 is met by this row and only by this row: the criterion is that the leave-one-class-out
    figure is *reported alongside* the random-split one, so a summary carrying one without the
    other does not meet it and this function does not produce one. ``random_split_r2`` is null
    when no random-split run is on disk, which AC-6 reads as not-yet-established rather than as
    a pass.

    **The comparison is like for like.** ``macro_r2`` is a mean over outer folds and
    ``random_split_r2`` is read from ``model-record.csv``, which is ``train``'s mean over *its*
    outer folds. It is deliberately not card #29's bootstrap point estimate over the
    out-of-fold rows: that is a different estimator over a different population, and putting it
    opposite a fold mean would make the gap partly an artefact of how the two were averaged.
    """
    rows = []
    for model, group in table.groupby(level="model"):
        usable = group[group["estimable"]]
        weights = usable["rows_scored"].astype(float)
        rows.append(
            {
                "model": str(model),
                "classes": int(len(group)),
                "classes_scored": int(len(usable)),
                "classes_not_estimable": int(len(group) - len(usable)),
                "macro_r2": float(usable["r2"].mean()) if len(usable) else float("nan"),
                "macro_mae": float(usable["mae"].mean()) if len(usable) else float("nan"),
                "weighted_r2": (
                    float((usable["r2"] * weights).sum() / weights.sum())
                    if float(weights.sum()) > 0.0
                    else float("nan")
                ),
                "worst_class": _extreme(usable, smallest=True),
                "worst_class_r2": float(usable["r2"].min()) if len(usable) else float("nan"),
                "best_class": _extreme(usable, smallest=False),
                "best_class_r2": float(usable["r2"].max()) if len(usable) else float("nan"),
                "rows_scored": int(group["rows_scored"].sum()),
                "random_split_r2": _random_split_r2(random_split, str(model)),
            }
        )
    return pd.DataFrame.from_records(rows).set_index("model")


def _extreme(usable: pd.DataFrame, *, smallest: bool) -> str:
    """Which class scored worst or best. Empty when nothing was estimable."""
    if not len(usable):
        return ""
    where = usable["r2"].idxmin() if smallest else usable["r2"].idxmax()
    return str(where[1] if isinstance(where, tuple) else where)


def _random_split_r2(record: pd.DataFrame | None, model: str) -> float:
    """The interpolation number this one must be read against, or NaN if none is on disk."""
    if record is None or record.empty or "r2" not in record.columns:
        return float("nan")
    if model in record.index:
        return float(record.loc[model, "r2"])
    return float(record["r2"].iloc[0])


def _chosen(evaluation: Evaluation) -> pd.DataFrame:
    """What each class fold's search settled on. `train`'s table, cut per class."""
    rows = [
        {"model": model, "alloy_class": str(fold).split(":", 1)[-1], **configuration.row()}
        for (model, fold), configuration in sorted(evaluation.chosen.items())
    ]
    return pd.DataFrame.from_records(rows).set_index(["model", "alloy_class"])


def _run(cfg: Config, settings: ModelSettings, classes: int, *, probe: bool) -> pd.DataFrame:
    """One row saying what kind of run wrote the tables beside it. See ``train._run``."""
    return pd.DataFrame.from_records(
        [
            {
                "probe": probe,
                "protocol": "leave-one-alloy-class-out",
                "outer_folds": classes,
                "optuna_trials": settings.optuna_trials,
                "configured_optuna_trials": cfg.model.optuna_trials,
                "screening": settings.screen_labels,
                "inner_cv_folds": cfg.model.inner_cv_folds,
                "feature_set": "hydms.descriptors.contract.SELECTED",
                "features": len(settings.features),
                "seed": settings.seed,
            }
        ]
    )


def _write(tables: dict[str, pd.DataFrame], destination: Path, out: TextIO) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        path = destination / f"{name}.csv"
        table.to_csv(path)
        print(f"wrote {path}", file=out)


# --------------------------------------------------------------------------------------
# The cheap halves: --budget and --emit
# --------------------------------------------------------------------------------------


def _budget(cfg: Config, settings: ModelSettings, stream: TextIO) -> int:
    """Fit nothing; say what the run would cost, from times a real fit already measured.

    The number that matters is not the total but the *ratio*: ten classes against the
    random-split run's ``model.cv_folds`` outer folds. Somebody who has watched the
    random-split run finish will otherwise assume this one is comparable, and it is twice it.
    """
    fits = CLASSES * cfg.model.inner_cv_folds * settings.optuna_trials
    print(
        f"{CLASSES} class fold(s) x {cfg.model.inner_cv_folds} inner x "
        f"{settings.optuna_trials} trial(s) = {fits} tuning fit(s), plus {CLASSES} refit(s). "
        f"The random-split run is {cfg.model.cv_folds} outer folds, so this protocol is about "
        f"{CLASSES / cfg.model.cv_folds:.1f}x that run -- it is not a variation on it, it is "
        f"another one of it and then some",
        file=stream,
    )

    table = cfg.paths.reports / "model" / "model-fits.csv"
    if not table.exists():
        print(
            f"no fit has been measured on this machine: {table} does not exist. Run "
            f"`python -m hydms.surrogate.train --trials 1` and it will be written.",
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
        f"{len(measured)} fit(s) measured in {table.name}: {seconds:.1f} s each on average. "
        f"{fits} tuning fit(s) at that rate is {fits * seconds / 3600:.1f} h before pruning.",
        file=stream,
    )
    return EXIT_OK


def document(tables: dict[str, pd.DataFrame]) -> str:
    """The published write-up, built from the tables and never typed.

    Generated rather than written because the alternative has already failed here once: a
    number that lives only in prose is a number no test can contradict, and card #29 made the
    same document generated for the same reason.
    """
    per = tables["loco-per-class"]
    once = tables["loco-summary"].iloc[0]
    run = tables["loco-run"].iloc[0]

    lines = [
        "# Leave-one-alloy-class-out",
        "",
        "Generated by `python -m hydms.surrogate.loco --emit`. Do not edit: a test asserts "
        "this file is what the code produces from the committed tables.",
        "",
    ]
    if bool(run["probe"]):
        lines += [
            f"> **These numbers came from a probe, not a result.** {run['optuna_trials']} "
            f"trial(s) against the configured {run['configured_optuna_trials']}"
            f"{', screening off' if not bool(run['screening']) else ''}. A probe's tables and "
            f"a real run's tables are the same shape, which is why this line is generated "
            f"from `loco-run.csv` rather than remembered.",
            "",
        ]

    random_split = float(once["random_split_r2"])
    macro = float(once["macro_r2"])
    lines += [
        "## The two numbers, side by side",
        "",
        "AC-6 asks for exactly this comparison and asks nothing about the size of the gap.",
        "",
        "| Protocol | R2 | What it measures |",
        "|---|---|---|",
        f"| Random split (`train`) | {_or_absent(random_split)} | interpolation: every family "
        f"is in the training rows |",
        f"| Leave-one-alloy-class-out | {macro:.4f} | extrapolation: the family is new |",
        "",
        f"Macro average over {int(once['classes_scored'])} estimable class(es) of "
        f"{int(once['classes'])}; every family counts once, which is what AC-6 asks. The "
        f"support-weighted average is {float(once['weighted_r2']):.4f} -- "
        f"{_direction(float(once['weighted_r2']), macro)} -- because it weights families by "
        f"how many rows they brought rather than by being families. Neither is wrong; they "
        f"answer different questions, and only the macro one is about transfer.",
        "",
        f"Worst family: **{once['worst_class']}** at R2 {float(once['worst_class_r2']):.4f}. "
        f"Best: **{once['best_class']}** at {float(once['best_class_r2']):.4f}.",
        "",
        "## Per class",
        "",
        "Read every score against the support beside it. An R2 over 19 held-out rows and an "
        "R2 over 260 are not the same claim.",
        "",
        "| Class | R2 | MAE | rows | compositions | estimable |",
        "|---|---|---|---|---|---|",
    ]
    for (_model, label), row in per.iterrows():
        note = "yes" if bool(row["estimable"]) else f"no -- {row['not_estimable_because']}"
        lines.append(
            f"| {label} | {float(row['r2']):.4f} | {float(row['mae']):.4f} | "
            f"{int(row['rows_scored'])} | {int(row['compositions_scored'])} | {note} |"
        )
    lines += [
        "",
        "## How to read this",
        "",
        "A model that transfers badly across families is a finding about hydrides, not a "
        "failure of the fit: the literature reports the same pattern, and it is the number "
        "that tells the inverse design how far a candidate may stray from known chemistry "
        "(card #48). The random-split figure is not wrong; it answers a different question, "
        "and quoting it alone is what AC-6 exists to stop.",
        "",
    ]
    return "\n".join(lines)


def _or_absent(value: float) -> str:
    """A number, or a phrase -- never the string ``nan``.

    ``summary`` writes NaN when no random-split run is on disk, and a table cell reading ``nan``
    invites a reader to treat it as a measurement that came out strange. AC-6 fails on this
    state anyway; the document should say the same thing in words.
    """
    return f"{value:.4f}" if value == value else "**not published** -- run `train` first"


def _direction(weighted: float, macro: float) -> str:
    """Which way the support-weighted mean falls, measured rather than predicted.

    A sentinel-budget probe had it *below* the macro mean, which is the opposite of what this
    document's first draft asserted -- the two largest families happened to score under the
    average. Whether that holds at the configured budget is not something prose can know, so
    the sentence is generated from the two numbers in front of it.
    """
    if weighted != weighted or macro != macro:
        return "not comparable, one of the two is undefined"
    if weighted > macro:
        return f"higher than the macro average by {weighted - macro:.4f}"
    if weighted < macro:
        return f"lower than the macro average by {macro - weighted:.4f}"
    return "identical to the macro average, which happens only when every class is the same size"


def _read_tables(source: Path) -> dict[str, pd.DataFrame]:
    """The committed tables, refusing a partial set rather than emitting half a document."""
    tables: dict[str, pd.DataFrame] = {}
    missing = []
    for name in TABLES:
        path = source / f"{name}.csv"
        if not path.exists():
            missing.append(path.name)
            continue
        index = [0, 1] if name in ("loco-per-class", "loco-chosen") else 0
        tables[name] = pd.read_csv(path, index_col=index)
    if missing:
        raise FileNotFoundError(
            f"{source} is missing {', '.join(missing)}. The document is generated from the "
            f"run's tables, so it cannot be rebuilt before the run has happened: "
            f"`python -m hydms.surrogate.loco --target capacity`."
        )
    return tables


def _emit(cfg: Config, source: Path, stream: TextIO) -> int:
    try:
        tables = _read_tables(source)
    except (FileNotFoundError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return EXIT_BAD_INVOCATION
    path = source / DOCUMENT
    path.write_text(document(tables), encoding="utf-8")
    print(f"wrote {path}", file=stream)
    return EXIT_OK


# --------------------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """Run the protocol with the class-wise outer cut and report. Returns the exit code."""
    stream = out if out is not None else sys.stdout
    args = _parser().parse_args(argv)

    if args.target not in TARGETS:
        print(
            f"{args.target!r} is not a target this project fits. It has one: "
            f"{', '.join(TARGETS)}.",
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
    if args.emit:
        return _emit(cfg, destination, stream)
    if args.budget:
        return _budget(cfg, settings, stream)

    probe = args.trials is not None or args.no_screening
    if probe:
        print(
            f"PROBE: {settings.optuna_trials} trial(s) against the configured "
            f"{cfg.model.optuna_trials}"
            f"{', screening off' if not settings.screen_labels else ''}. "
            f"These numbers are a cost check, not a result.",
            file=stream,
        )

    frame, split = capacity_matrix(cfg, settings=settings)
    training = frame.loc[split == TRAIN]
    classes = alloy_classes(training)
    print(
        f"{len(frame)} row(s), {len(training)} in {TRAIN!r}, "
        f"{classes.nunique()} alloy class(es): "
        + ", ".join(f"{label} {count}" for label, count in classes.value_counts().items()),
        file=stream,
    )

    log = FitLog()
    started = time.perf_counter()
    evaluation = nested_scores(
        frame,
        split,
        [capacity_contender(settings=settings, log=log)],
        outer=leave_one_class_out,
    )
    elapsed = time.perf_counter() - started
    print(
        f"leave-one-alloy-class-out: {len(evaluation.outer)} class fold(s) in "
        f"{elapsed / 60:.1f} min",
        file=stream,
    )

    table = per_class(evaluation, training)
    record = _read_random_split(cfg)
    once = summary(table, record)
    tables = {
        TABLES[0]: table,
        TABLES[1]: once,
        TABLES[2]: _chosen(evaluation),
        TABLES[3]: _run(cfg, settings, len(evaluation.outer), probe=probe),
    }
    _write(tables, destination, stream)

    for model, row in once.iterrows():
        against = float(row["random_split_r2"])
        beside = f"{against:.4f}" if against == against else "not on disk"
        print(
            f"{model}: macro R2 {float(row['macro_r2']):.4f} over "
            f"{int(row['classes_scored'])} class(es), weighted "
            f"{float(row['weighted_r2']):.4f}; random split {beside}. "
            f"Worst {row['worst_class']} {float(row['worst_class_r2']):.4f}",
            file=stream,
        )
    print(
        "Publish the write-up with `python -m hydms.surrogate.loco --emit`; it is generated "
        "from these tables, never typed.",
        file=stream,
    )
    return EXIT_OK


def _read_random_split(cfg: Config) -> pd.DataFrame | None:
    """`train`'s averaged record, if a run has left one. Read, never recomputed."""
    path = cfg.paths.reports / RANDOM_SPLIT_TABLE
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, index_col=0)
    except (OSError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
