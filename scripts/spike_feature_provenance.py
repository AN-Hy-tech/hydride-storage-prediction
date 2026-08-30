"""Resolve which CBFV element-property table produces each selected feature.

Card #8, the provenance spike. This is a HARD GATE: the descriptor layer cannot be
reimplemented from a table nobody has identified, so nothing in L2 may start until every
selected feature is accounted for.

Why it resolves this empirically rather than by reading the table CSVs: CBFV synthesises
composite descriptors of its own (`a_divi_b`, `a_mult_b`) that appear in no table's header.
Matching against headers alone would leave every composite unaccounted for and produce a
false negative. So we run the real `generate_features` once per `elem_prop`, with exactly
the arguments the original script used, and diff the column names it actually emits.

The question this answers is narrow and factual: for each selected feature, which of
{magpie, oliynyk, jarvis, mat2vec, onehot} emits a column of that name, and is the answer
unique? A feature emitted by no table fails the gate. A feature emitted by several is
reported, because it means the name alone does not identify the source.

Usage:
    python scripts/spike_feature_provenance.py --check-all-22
    python scripts/spike_feature_provenance.py --n 40 --json out.json

Must run under the pinned `Project` conda environment (CBFV 1.1.0). Exits non-zero when
any selected feature is unaccounted for.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Every table CBFV 1.1.0 ships. `random_200` is excluded: it is 200 random vectors with
# generated names, so it can only ever produce accidental matches.
ELEM_PROPS = ["magpie", "oliynyk", "jarvis", "mat2vec", "onehot"]

# The statistics CBFV prefixes onto each element property.
STATISTICS = ("avg_", "dev_", "range_", "sum_", "max_", "min_", "mode_", "var_")

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "Machine_Model" / "data" / "raw" / "hydride_prefeaturizing.csv"
SELECTED = REPO / "Machine_Model" / "reports" / "feature_selection" / "feature_selection_report.csv"


def load_selected() -> list[str]:
    """The feature names the published pipeline selected, in SHAP-importance order."""
    return pd.read_csv(SELECTED)["Feature"].tolist()


def columns_for(elem_prop: str, sample: pd.DataFrame) -> list[str]:
    """Column names CBFV emits for one table, using the original script's exact arguments.

    `extend_features=True` and `drop_duplicates=False` are not incidental: they are what
    `Machine_Model/src/extract_features_cbfv.py:31` passed, and changing either changes the
    emitted column set. Reproducing the call is the whole point of the spike.
    """
    from CBFV.composition import generate_features

    X, _y, _formulae, _skipped = generate_features(
        sample.copy(), elem_prop=elem_prop, drop_duplicates=False, extend_features=True
    )
    return list(X.columns)


def build_sample(n: int) -> pd.DataFrame:
    """The featuriser's input, preprocessed the way the original script preprocessed it."""
    df = pd.read_csv(RAW).head(n)
    object_cols = df.select_dtypes(include="object").columns
    df = df.drop(columns=[c for c in object_cols if c != "Composition"])
    return df.rename(columns={"log_H2_W% (max)": "target", "Composition": "formula"})


def split_statistic(feature: str) -> tuple[str, str]:
    """Split `dev_Zunger_radii_sum` into ('dev', 'Zunger_radii_sum')."""
    for stat in STATISTICS:
        if feature.startswith(stat):
            return stat.rstrip("_"), feature[len(stat):]
    return "", feature


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=20, help="formulae to featurise per table")
    parser.add_argument("--check-all-22", action="store_true",
                        help="fail unless every selected feature is accounted for")
    parser.add_argument("--json", type=Path, help="also write the mapping as JSON")
    args = parser.parse_args()

    selected = load_selected()
    sample = build_sample(args.n)
    print(f"Featurising {len(sample)} formulae once per table: {', '.join(ELEM_PROPS)}\n")

    emitted: dict[str, list[str]] = {}
    for elem_prop in ELEM_PROPS:
        try:
            emitted[elem_prop] = columns_for(elem_prop, sample)
            print(f"  {elem_prop:9s} -> {len(emitted[elem_prop]):5d} columns")
        except Exception as exc:  # a table that will not run is a finding, not a crash
            emitted[elem_prop] = []
            print(f"  {elem_prop:9s} -> FAILED: {type(exc).__name__}: {exc}")

    # `temperature(K)` is a passthrough: it is a raw input column that extend_features
    # carries into X, not a descriptor any table produces. Attributing it to a table would
    # be wrong, so it is classified separately rather than counted as unaccounted.
    passthrough = {c for c in sample.columns if c not in ("formula", "target")}

    rows = []
    unaccounted = []
    for feature in selected:
        sources = [p for p, cols in emitted.items() if feature in cols]
        stat, base = split_statistic(feature)
        if feature in passthrough:
            kind = "passthrough (raw input column, not a descriptor)"
        elif not sources:
            kind = "UNACCOUNTED"
            unaccounted.append(feature)
        elif len(sources) == 1:
            kind = "unique"
        else:
            kind = "ambiguous (emitted by more than one table)"
        rows.append({"feature": feature, "statistic": stat, "base_property": base,
                     "sources": sources, "kind": kind})

    width = max(len(r["feature"]) for r in rows)
    print(f"\n{'feature'.ljust(width)}  {'stat':6s}  sources")
    print("-" * (width + 40))
    for r in rows:
        src = ", ".join(r["sources"]) if r["sources"] else r["kind"]
        print(f"{r['feature'].ljust(width)}  {r['statistic']:6s}  {src}")

    by_table: dict[str, int] = {}
    for r in rows:
        for s in r["sources"]:
            by_table[s] = by_table.get(s, 0) + 1
    print("\nFeatures per table:", ", ".join(f"{k}={v}" for k, v in sorted(by_table.items())) or "none")

    if args.json:
        args.json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Wrote {args.json}")

    if unaccounted:
        print(f"\nSTOP GATE FAILED: {len(unaccounted)} feature(s) produced by no table:")
        for feature in unaccounted:
            print(f"  - {feature}")
        print("Tickets 16-21 stay blocked.")
        return 1

    if args.check_all_22:
        print(f"\nSTOP GATE PASSED: all {len(selected)} selected features accounted for.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
