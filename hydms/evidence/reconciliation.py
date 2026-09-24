"""L7 -- ``REPORT.md`` against the artifacts it cites: the reconciliation table.

``REPORT.md`` is the archival account of the forward model *as published*, and it is not
corrected in place (``docs/FREEZE.md``): rewriting it would orphan the account it gives. But it
cannot stand unexamined either, because tables committed beside it contradict it. This module
is the record of where, and ``docs/REPORT-RECONCILIATION.md`` is generated from it.

**Generated, because a hand-written evidence table is the defect it would be documenting.**
Every "the artifact says" value is *read from the committed file at emit time* -- nothing here
types a number in -- and every "``REPORT.md`` says" quote is checked by the test suite to occur
in ``REPORT.md`` verbatim. So the page cannot misquote the report, and cannot drift from the CSV
it cites, without a test going red. That is the property the prose version would not have had,
and the reason #37 (the Chapter 1 revision) is written *from* this rather than beside it.

**What the table is not.** It is not a list of the pipeline's leaks -- those are
``docs/PHASE-H-RUNBOOK.md`` §1, and a leaked number can agree perfectly with its own CSV. A row
here is a place where two committed statements about the *same* quantity disagree. Leaks decide
whether a number is worth anything; this table decides which of two numbers was actually
produced. Both matter, and a reader needs to know which question each document answers.

**"Eight".** The audit that opened Phase H said it found eight disagreements and gave three
examples; the other five were never written down anywhere this project can find. This table
is therefore a re-measurement, not a transcription: its rows are the ones that could be
re-derived from committed files, and there are more than eight of them.

Card #89.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import pandas as pd

from hydms.config import repo_root

__all__ = [
    "DISAGREEMENTS",
    "DOCUMENT",
    "Disagreement",
    "document",
    "emit",
    "main",
]

DOCUMENT = repo_root() / "docs" / "REPORT-RECONCILIATION.md"
REPORT = "REPORT.md"

_BENCH = "Machine_Model/reports/benchmarked_model"
_STACKING = f"{_BENCH}/stacking_results.csv"
_IMPROVED = f"{_BENCH}/improved_benchmark_results.csv"
_TTEST = f"{_BENCH}/ttest_best_vs_ensemble_abs_error.csv"
_PAIRWISE = f"{_BENCH}/pairwise_ttest_vs_best.csv"
_SUBGROUPS = f"{_BENCH}/temperature_subgroup_performance_expanded.csv"
_RAW = "Machine_Model/data/raw/hydride_data.csv"
_EVALUATION = "reports/model/evaluation-metrics.csv"
_LOCO = "reports/loco/loco-summary.csv"


def _csv(root: Path, path: str) -> pd.DataFrame:
    return pd.read_csv(root / path)


def _row(frame: pd.DataFrame, model: str, column: str = "Model") -> pd.Series:
    matched = frame.loc[frame[column] == model]
    if len(matched) != 1:
        raise ValueError(f"expected one {model!r} row, found {len(matched)}.")
    return matched.iloc[0]


def _f3(value: float) -> str:
    # U+2212, because REPORT.md writes its negatives with it and the page quotes REPORT.md
    # verbatim; a hyphen beside a minus sign in one table reads as two different things. It is
    # spelled as an escape throughout this file so ruff's RUF001 stays on for everything else.
    return f"{value:.3f}".replace("-", "\u2212")


@dataclass(frozen=True)
class Disagreement:
    """One place where ``REPORT.md`` and a committed artifact say different things.

    Attributes:
        key: A stable slug, used as the row's anchor.
        where: The section of ``REPORT.md``.
        claim: Text quoted from ``REPORT.md`` verbatim -- the test suite asserts it occurs there.
        artifact: The committed file, relative to the repository root.
        measure: Reads ``artifact`` (and anything else committed) and returns what it says,
            as a sentence. Called at emit time; nothing it prints is typed in.
        believe: Which source to believe.
        why: The reason, in a sentence or two.
    """

    key: str
    where: str
    claim: str
    artifact: str
    measure: Callable[[Path], str]
    believe: str
    why: str


# --------------------------------------------------------------------------------------
# The measurements -- each one reads a committed file
# --------------------------------------------------------------------------------------


def _ensemble_headline(root: Path) -> str:
    stacked = _csv(root, _STACKING).iloc[0]
    improved = _row(_csv(root, _IMPROVED), "Ensemble")
    return (
        f"`stacking_results.csv`: CV R² {_f3(stacked['CV_R2_Mean'])}, Val R² "
        f"{_f3(stacked['Val_R2_Orig'])}, Test R² {_f3(stacked['Test_R2_Orig'])}. "
        f"`improved_benchmark_results.csv` agrees with the report instead -- Val "
        f"{_f3(improved['Val_R2_Orig'])}, Test {_f3(improved['Test_R2_Orig'])}. Two committed "
        f"files, two different ensembles"
    )


def _ensemble_ci(root: Path) -> str:
    stacked = _csv(root, _STACKING).iloc[0]
    return (
        f"`stacking_results.csv`: Val R² CI {_f3(stacked['Val_R2_CI_Low'])} to "
        f"{_f3(stacked['Val_R2_CI_High'])}"
    )


def _best_vs_ensemble(root: Path) -> str:
    row = _csv(root, _TTEST).iloc[0]
    return (
        f"t = {_f3(row['t_stat'])}, p = {row['p_value']:.3g}, against best model "
        f"**{row['BestModel']}** -- the report names ExtraTrees as best"
    )


def _cleanlab_test_rows(root: Path) -> str:
    groups = _csv(root, _SUBGROUPS)
    counts = groups.groupby("Model")["Count"].sum()
    totals = ", ".join(f"{model} {int(total)}" for model, total in sorted(counts.items()))
    return f"the test-set subgroup table scores {totals} rows -- the full split, none removed"


def _overfitting_definition(root: Path) -> str:
    row = _row(_csv(root, _IMPROVED), "ExtraTrees")
    return (
        f"ExtraTrees: published column {_f3(row['Overfitting'])}; Train \u2212 Val R² = "
        f"{_f3(row['Train_R2_Orig'] - row['Val_R2_Orig'])}; the footnote's CV \u2212 Val R² = "
        f"{_f3(row['CV_R2_Mean'] - row['Val_R2_Orig'])}"
    )


def _lowest_overfitting(root: Path) -> str:
    table = _csv(root, _IMPROVED)
    ensemble = float(_row(table, "Ensemble")["Overfitting"])
    lower = table.loc[table["Overfitting"] < ensemble].sort_values(
        ["Overfitting", "Model"], kind="stable"
    )
    named = ", ".join(f"{m} {_f3(v)}" for m, v in zip(lower["Model"], lower["Overfitting"], strict=True))
    return f"Ensemble {_f3(ensemble)}; {len(lower)} models are lower: {named}"


def _pairwise(root: Path, model: str) -> str:
    row = _row(_csv(root, _PAIRWISE), model)
    return f"{model} vs ExtraTrees: p_adj = {row['p_value_adj']:.3f}"


def _other_models(root: Path) -> str:
    table = _csv(root, _PAIRWISE)
    above = table.loc[
        (table["p_value_adj"] >= 0.05) & ~table["Model"].isin(["CatBoost", "RandomForest"])
    ]
    named = ", ".join(f"{m} p_adj = {p:.3f}" for m, p in zip(above["Model"], above["p_value_adj"], strict=True))
    return f"not all: {named}" if named else "all other models are below 0.05"


def _subgroups(root: Path) -> str:
    table = _csv(root, _SUBGROUPS)
    wins = []
    for band in ("low", "mid", "high"):
        rows = table.loc[table["Temp_Subgroup"] == band].set_index("Model")
        better = rows["R2"].idxmax()
        wins.append(
            f"{band}: {better} ({_f3(rows.loc['ExtraTrees', 'R2'])} vs "
            f"{_f3(rows.loc['Ensemble', 'R2'])})"
        )
    return "higher R² by subgroup, ExtraTrees vs Ensemble -- " + "; ".join(wins)


def _elements(root: Path) -> str:
    from hydms.data.load import load_hydride_data, parse_formula

    frame = load_hydride_data(root / _RAW)
    counts: dict[str, int] = {}
    for formula in frame["Composition"]:
        for symbol in parse_formula(formula):
            counts[symbol] = counts.get(symbol, 0) + 1
    once = sorted(symbol for symbol, seen in counts.items() if seen == 1)
    return (
        f"{len(counts)} elements over {len(frame)} rows; {len(once)} appear exactly once "
        f"({', '.join(once)})"
    )


def _unique_compositions(root: Path) -> str:
    from hydms.data.canonical import group_keys
    from hydms.data.load import load_hydride_data

    frame = load_hydride_data(root / _RAW)
    return (
        f"{frame['Composition'].nunique()} distinct formula strings, "
        f"{group_keys(frame).nunique()} distinct canonical compositions"
    )


def _europium(root: Path) -> str:
    from hydms.data.load import parse_formula
    from hydms.descriptors.contract import CONTRACT

    verdict = CONTRACT.computability(parse_formula("Eu1Ni5"))
    return (
        f"`Eu1Ni5`: {len(verdict.unavailable)} of the published {len(CONTRACT.names)} "
        f"features cannot be computed, every one blocked by "
        f"{', '.join(sorted({hole.element for hole in verdict.holes}))}"
    )


DISAGREEMENTS: tuple[Disagreement, ...] = (
    Disagreement(
        key="ensemble-headline",
        where="§4.2",
        claim="| **Ensemble** | — | **0.939** | **0.185** | **0.892**",
        artifact=_STACKING,
        measure=_ensemble_headline,
        believe="Neither, as a measure of the model",
        why=(
            "The committed files contradict each other, which is itself the evidence that the "
            "published pipeline is not the committed one. Even the agreeing file is scored on "
            "the validation set that chose the ensemble's members (leak L2)."
        ),
    ),
    Disagreement(
        key="ensemble-ci",
        where="§4.3",
        claim="| **Ensemble** | **0.898** | **0.961** | **0.063** |",
        artifact=_STACKING,
        measure=_ensemble_ci,
        believe="Neither",
        why="It is an interval around the headline above, and inherits that row's contradiction.",
    ),
    Disagreement(
        key="best-vs-ensemble",
        where="§4.2, §4.4",
        claim="t = \u22122.102, p = 0.037 — Ensemble wins.",
        artifact=_TTEST,
        measure=_best_vs_ensemble,
        believe="The CSV, as the record of what ran",
        why=(
            "It names a different best model, so the report's test is not the one on disk. "
            "Neither carries weight today: both compare test-set errors of models selected on "
            "the same data."
        ),
    ),
    Disagreement(
        key="cleanlab-rows",
        where="§3.2, §4.1",
        claim="| Test | 247 | 31 | ~239 |",
        artifact=_SUBGROUPS,
        measure=_cleanlab_test_rows,
        believe="The CSV",
        why=(
            "The report's own §6.4 table uses the same 247-row counts. CleanLab removed nothing "
            "from the scored test split; the ~239 was never realised."
        ),
    ),
    Disagreement(
        key="overfitting-footnote",
        where="§4.2 footnote",
        claim="*Overfitting = CV_R²_mean \u2212 Val_R²_orig.",
        artifact=_IMPROVED,
        measure=_overfitting_definition,
        believe="The column's values; not the footnote",
        why=(
            "The published column is Train \u2212 Val in weight percent, which is what "
            "`benchmark_model_selection.py:1120` computes. The footnote describes a difference "
            "between a log-space CV score and a weight-percent one, which is not a quantity "
            "(`hydms/data/target.py`)."
        ),
    ),
    Disagreement(
        key="lowest-overfitting",
        where="§4.2 key findings",
        claim="with the lowest overfitting (0.039)",
        artifact=_IMPROVED,
        measure=_lowest_overfitting,
        believe="The CSV",
        why="The report's own table shows the lower values; the sentence contradicts it.",
    ),
    Disagreement(
        key="pairwise-randomforest",
        where="§4.4",
        claim="- RandomForest: p_adj ≈ 0.1 — not significant",
        artifact=_PAIRWISE,
        measure=lambda root: _pairwise(root, "RandomForest"),
        believe="The CSV",
        why="The conclusion (not significant) survives; the number does not.",
    ),
    Disagreement(
        key="pairwise-others",
        where="§4.4",
        claim="- All other models: p_adj < 0.05 — significantly worse",
        artifact=_PAIRWISE,
        measure=_other_models,
        believe="The CSV",
        why="A model the report calls significantly worse is not, at its own threshold.",
    ),
    Disagreement(
        key="subgroup-robustness",
        where="§6.4, §4.3",
        claim="the Ensemble is more robust across all three subgroups",
        artifact=_SUBGROUPS,
        measure=_subgroups,
        believe="The CSV",
        why=(
            "The report's §6.4 table, which is this CSV, shows ExtraTrees ahead in every "
            "subgroup. §4.3 rests the ensemble's recommendation on this robustness."
        ),
    ),
    Disagreement(
        key="element-count",
        where="§2.3",
        claim="Fifty-four elements were identified across all formulae.",
        artifact=_RAW,
        measure=_elements,
        believe="The count from the file",
        why=(
            "Counted from every parsed composition, and asserted in `tests/data/test_load.py`. "
            "Probably inherited rather than introduced: the HyStor paper reports 54 for its own "
            "1,282-row release, a different file. It cannot be settled from this repository. "
            "If these 1,279 rows are a subset of that release, the release has at least 55 "
            "elements too and the paper's own count is wrong; if they are not, nothing here "
            "can say what that file contains."
        ),
    ),
    Disagreement(
        key="unique-compositions",
        where="§2.2",
        claim="- **Unique compositions:** 1 149",
        artifact=_RAW,
        measure=_unique_compositions,
        believe="Both; they count different things",
        why=(
            "1,149 is right for strings. As *materials* it overcounts: `La1Ni5` and `LaNi5` "
            "are one alloy. Anything grouped -- splits, folds, resamples -- uses the canonical "
            "key (`hydms.data.canonical.group_keys`), or rows of one material straddle a split."
        ),
    ),
    Disagreement(
        key="europium-row",
        where="§3.1",
        claim="| **Total after merge** | **282** | 1 279 rows \u00d7 282 features |",
        artifact="hydms/descriptors/contract.py",
        measure=_europium,
        believe="The featuriser",
        why=(
            "Europium is absent from CBFV's JARVIS table, and CBFV featurised row 516 anyway "
            "with an all-zero property vector (zero mass, zero polarizability). Its "
            "`avg_polzbl_divi_atom_mass` of 0.096547 is (5/6) \u00d7 Ni's value exactly (#16). "
            "`extract_features_cbfv.py` never read CBFV's `skipped` list, so 1,279 featurised "
            "rows includes one that was not."
        ),
    ),
)


# --------------------------------------------------------------------------------------
# The honest numbers beside the published ones
# --------------------------------------------------------------------------------------


def _honest(root: Path) -> list[str]:
    metrics = _csv(root, _EVALUATION)
    chosen = metrics.loc[
        (metrics["reading"] == "out-of-fold")
        & (metrics["scale"] == "wt_pct")
        & (metrics["subgroup"] == "all")
        & (metrics["interval_from"] == "out-of-fold canonical groups")
    ].set_index("metric")
    loco = _csv(root, _LOCO).iloc[0]
    improved = _row(_csv(root, _IMPROVED), "Ensemble")

    def cell(metric: str) -> str:
        row = chosen.loc[metric]
        return f"{row['point']:.3f} [{row['ci_low']:.3f}, {row['ci_high']:.3f}]"

    return [
        "| Reading | R² (wt%) | MAE (wt%) | Source |",
        "|---|---|---|---|",
        f"| Published: ensemble, validation set | {improved['Val_R2_Orig']:.3f} | "
        f"{improved['Val_MAE_Orig']:.3f} | `REPORT.md` §4.2, `{_IMPROVED}` |",
        f"| Published: ensemble, test set | {improved['Test_R2_Orig']:.3f} | "
        f"{improved['Test_MAE_Orig']:.3f} | same |",
        f"| Now: out-of-fold, group-aware nested CV (#29) | {cell('r2')} | {cell('mae')} | "
        f"`{_EVALUATION}` |",
        f"| Now: leave-one-alloy-class-out, macro over {int(loco['classes_scored'])} classes "
        f"(#30) | {loco['macro_r2']:.3f} | {loco['macro_mae']:.3f} | `{_LOCO}` |",
        f"| Now: the worst held-out class, {loco['worst_class']} | "
        f"{loco['worst_class_r2']:.3f} | — | same |",
    ]


# --------------------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------------------


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def document(root: Path | None = None) -> str:
    """The whole of ``docs/REPORT-RECONCILIATION.md``, measured from the files under ``root``."""
    base = repo_root() if root is None else Path(root)
    lines = [
        "# `REPORT.md` against the artifacts it cites",
        "",
        "Generated by `python -m hydms.evidence.reconciliation --emit`. **Do not edit:** "
        "`tests/evidence/test_reconciliation.py` asserts this file is byte-for-byte what the "
        "code produces, that every quotation below occurs in `REPORT.md` verbatim, and every "
        "\"the artifact says\" value is read from the committed file when the page is built. "
        "The reasoning lives in `hydms/evidence/reconciliation.py`; change it there.",
        "",
        "## Read this first",
        "",
        "**`REPORT.md` is preserved unedited.** It is the archival record of the forward model "
        "*as published*, and every number in it is cited somewhere -- in a draft, a slide, a "
        "conversation. Correcting it in place would make those citations point at text that "
        "no longer says what was cited. So it is corrected *beside* itself, here, and the "
        "freeze (`docs/FREEZE.md`) denies edits to it outright.",
        "",
        "**The published pipeline is not the committed pipeline.** Row 1 is the evidence in "
        "one line: two files committed under `Machine_Model/reports/` describe two different "
        "ensembles, and the report quotes one of them. The pipeline also cannot be re-run to "
        "settle which: `jarvis_filtered_features.csv` has no producer in the repository or its "
        "history, and `merge_datasets.py:46` joins its feature frames by position "
        "(`docs/FREEZE.md` § Why).",
        "",
        "**A row here is a disagreement, not a leak.** A leaked number can agree perfectly "
        "with its own CSV; the thirteen leaks are `docs/PHASE-H-RUNBOOK.md` §1. This table "
        "says which of two numbers was actually produced. Whether either one is worth quoting "
        "is the leak inventory's question, and for every model-performance row the answer is "
        "no.",
        "",
        f"**The audit that opened Phase H counted eight** and wrote down three. The other five "
        f"were never recorded, so this is a re-measurement from committed files, not a "
        f"transcription, and it finds {len(DISAGREEMENTS)}.",
        "",
        "## The disagreements",
        "",
        "| # | `REPORT.md` says | Where | The artifact says | Believe |",
        "|---|---|---|---|---|",
    ]
    for number, item in enumerate(DISAGREEMENTS, start=1):
        lines.append(
            f"| {number} | {_cell(item.claim)} | {item.where} | "
            f"{_cell(item.measure(base))} (`{item.artifact}`) | {item.believe} |"
        )
    lines += ["", "## Why each one is believed the way it is", ""]
    for number, item in enumerate(DISAGREEMENTS, start=1):
        lines.append(f"{number}. **`{item.key}`** -- {item.why}")
    lines += [
        "",
        "## The honest numbers beside the published ones",
        "",
        "The published rows are quoted for comparison only. The rows marked *now* come from "
        "the hardened pipeline: grouping on the canonical composition, selection and early "
        "stopping inside the folds, and nothing scored on data that chose it.",
        "",
        *_honest(base),
        "",
        "The drop is the expected result, not a regression (PRD risk R4). The out-of-fold "
        "interval is too narrow for the reason `reports/model/evaluation.md` gives; the "
        "cross-family row is the one that answers \"will this work on a new alloy family\", "
        "and its answer is: not reliably.",
        "",
    ]
    return "\n".join(lines)


def emit(path: Path | None = None) -> Path:
    """Rewrite the committed page. The whole of ``--emit``. Cheap: it reads committed CSVs."""
    destination = DOCUMENT if path is None else Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # `newline` explicitly, so a page emitted on Windows is byte-identical to one from Linux.
    destination.write_text(document(), encoding="utf-8", newline="\n")
    return destination


def main(argv: list[str] | None = None, out: TextIO | None = None) -> int:
    """``--emit`` rewrites the page; no argument prints it."""
    stream = out if out is not None else sys.stdout
    parser = argparse.ArgumentParser(
        prog="python -m hydms.evidence.reconciliation",
        description="REPORT.md against the artifacts it cites.",
    )
    parser.add_argument("--emit", action="store_true", help=f"rewrite {DOCUMENT.name}")
    args = parser.parse_args(argv)
    if args.emit:
        print(f"wrote {emit()}", file=stream)
    else:
        print(document(), file=stream)
    return 0


if __name__ == "__main__":  # pragma: no cover - the command line
    raise SystemExit(main())
