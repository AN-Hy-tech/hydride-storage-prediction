"""L1 -- one pinned record of what the data layer produces. Card #15.

Every other file in ``tests/data/`` checks a *mechanism*: that the merge keys, that the split
groups, that screening refuses. This one checks the **result**, as a single record, so that a
change anywhere in the layer shows up as a diff of named facts rather than as one assertion
failing somewhere in a hundred.

Two kinds of fact live here, and the difference is the point:

  - **Facts that must not move.** 1279 rows, 1149 formula strings, 1115 compositions, ten
    alloy classes. These are what makes ``REPORT.md``'s numbers still attributable: the
    rewrite reads the same dataset the archived scripts read.
  - **Facts that moved, on purpose, with the movement pinned too.** The split is 893/131/255
    where the published one was 896/136/247, because the unit is now the canonical
    composition; screening removes two rows the archival pipeline kept. Both are recorded
    *with* the superseded value, so nobody can quietly restore the old number and nobody can
    mistake the new one for agreement.

A deviation fails with a table of every differing fact -- name, expected, actual -- because a
bare ``assert 893 == 896`` tells the next reader neither which stage moved nor whether
anything else moved with it.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pandas", reason="the data layer is pandas frames end to end")
pytest.importorskip("sklearn", reason="the split protocol is scikit-learn's")

import pandas as pd  # noqa: E402  -- only importable once the skips above have passed
from hydms.data.canonical import collapse, group_keys  # noqa: E402
from hydms.data.load import (  # noqa: E402
    load_hydride_data,
    load_ml_hydpark,
    load_prefeaturized,
    parse_formula,
)
from hydms.data.metadata import class_distribution, with_metadata  # noqa: E402
from hydms.data.screening import screen  # noqa: E402
from hydms.data.splits import SPLIT_NAMES, assign_splits, split_summary  # noqa: E402

#: What the data layer produces, as of card #15. Every value is measured by :func:`measure`
#: below, not copied from a document -- where a document disagrees, the document is what is
#: wrong (``docs/REPORT-RECONCILIATION.md``, card #89).
GOLDEN: dict[str, object] = {
    # --- the sources, unchanged since the archival pipeline read them -------------------
    "hydride_data.rows": 1279,
    "hydride_data.columns": 6,
    "prefeaturized.rows": 1279,
    "ml_hydpark.rows": 772,
    "distinct_elements": 55,
    # --- identity ----------------------------------------------------------------------
    "formula_strings": 1149,
    "after_whitespace": 1142,
    "after_element_order": 1121,
    "canonical_compositions": 1115,
    # --- the target --------------------------------------------------------------------
    "target_min_wt_pct": 0.1,
    "target_max_wt_pct": 7.19,
    "temperature_min_k": 195,
    "temperature_max_k": 773,
    # --- alloy class, after reconciliation on the canonical key (#12) -------------------
    "alloy_classes": 10,
    "class_rows.AB5": 196,
    "class_rows.AB2": 371,
    "class_rows.AB": 90,
    "class_rows.A2B": 32,
    "class_rows.Mg": 148,
    "class_rows.HEA": 77,
    "class_rows.MEA": 109,
    "class_rows.LEA": 26,
    "class_rows.SS": 103,
    "class_rows.MIC": 127,
    "class_rows.total": 1279,
    "class_relabelled_rows": 13,
    "smallest_class_compositions": 24,
    # --- the split (#13). Moved on purpose; the published value is pinned beside it. ----
    "split_rows.train": 893,
    "split_rows.val": 131,
    "split_rows.test": 255,
    "split_compositions.train": 780,
    "split_compositions.val": 111,
    "split_compositions.test": 224,
    "split_rows.published_train": 896,
    "split_rows.published_val": 136,
    "split_rows.published_test": 247,
    "split_straddling_compositions": 0,
    # --- screening (#14). Two rows, both from train. -----------------------------------
    "screened.rows_out": 1277,
    "screened.removed": 2,
    "screened.removed_from_val": 0,
    "screened.removed_from_test": 0,
}

#: Facts whose value is a *decision recorded*, not a measurement of today's code. They are
#: compared like the rest so that restoring an old number is a visible failure; the reason
#: each was superseded is on the card named here.
SUPERSEDED = {
    "split_rows.published_train": "#13 -- grouping moved from the formula string to the composition",
    "split_rows.published_val": "#13",
    "split_rows.published_test": "#13",
}


def measure() -> dict[str, object]:
    """Run the data layer end to end and record what it produced."""
    raw = load_hydride_data()
    keys = group_keys(raw)
    stages = collapse(raw["Composition"])
    resolved = with_metadata(raw)
    classes = class_distribution(raw)
    split = assign_splits(raw)
    sizes = split_summary(split, keys)
    screened = screen(raw, split)
    counts = screened.counts()

    elements = {symbol for formula in raw["Composition"] for symbol in parse_formula(formula)}
    straddling = {
        key
        for key, group in pd.DataFrame({"key": keys, "split": split}).groupby("key")
        if len(set(group["split"])) > 1
    }

    facts: dict[str, object] = {
        "hydride_data.rows": len(raw),
        "hydride_data.columns": len(raw.columns),
        "prefeaturized.rows": len(load_prefeaturized()),
        "ml_hydpark.rows": len(load_ml_hydpark()),
        "distinct_elements": len(elements),
        "formula_strings": stages.raw,
        "after_whitespace": stages.stages[1].distinct,
        "after_element_order": stages.stages[2].distinct,
        "canonical_compositions": stages.compositions,
        "target_min_wt_pct": float(raw["H2_W% (max)"].min()),
        "target_max_wt_pct": float(raw["H2_W% (max)"].max()),
        "temperature_min_k": int(raw["temperature(K)"].min()),
        "temperature_max_k": int(raw["temperature(K)"].max()),
        "alloy_classes": len(classes),
        "class_rows.total": int(classes["reconciled"].sum()),
        "class_relabelled_rows": int((raw["Alloy_class"] != resolved["Alloy_class"]).sum()),
        "smallest_class_compositions": int(classes["compositions"].min()),
        "split_straddling_compositions": len(straddling),
        "screened.rows_out": len(screened.frame),
        "screened.removed": len(screened.removed),
        "screened.removed_from_val": int(counts.loc["val", "removed"]),
        "screened.removed_from_test": int(counts.loc["test", "removed"]),
    }
    facts.update(
        {f"class_rows.{name}": int(row.reconciled) for name, row in classes.iterrows()}
    )
    facts.update({f"split_rows.{name}": int(sizes.loc[name, "rows"]) for name in SPLIT_NAMES})
    facts.update(
        {f"split_compositions.{name}": int(sizes.loc[name, "compositions"]) for name in SPLIT_NAMES}
    )
    # Recorded decisions, not measurements: they are carried through so that a change to
    # GOLDEN that quietly restored the published counts would fail here rather than pass.
    facts.update({name: GOLDEN[name] for name in SUPERSEDED})
    return facts


def diff(expected: dict[str, object], actual: dict[str, object]) -> str:
    """Every differing fact as a table, or an empty string when they agree."""
    names = sorted(set(expected) | set(actual))
    rows = [
        (name, expected.get(name, "<absent>"), actual.get(name, "<absent>"))
        for name in names
        if expected.get(name, "<absent>") != actual.get(name, "<absent>")
    ]
    if not rows:
        return ""
    width = max(len(name) for name, _, _ in rows)
    lines = [f"{'fact'.ljust(width)}  {'expected':>12}  {'actual':>12}"]
    lines += [f"{name.ljust(width)}  {want!s:>12}  {got!s:>12}" for name, want, got in rows]
    return "\n".join(lines)


def test_the_data_layer_reproduces_the_documented_dataset() -> None:
    """The whole record at once, so a deviation is read as a diff rather than as one number."""
    report = diff(GOLDEN, measure())
    assert not report, f"the data layer no longer produces the golden record:\n\n{report}\n"


def test_the_superseded_counts_are_labelled_with_the_card_that_moved_them() -> None:
    """A pinned number with no reason beside it is a number the next reader will 'fix'."""
    for name, reason in SUPERSEDED.items():
        assert name in GOLDEN
        assert reason, name
    assert GOLDEN["split_rows.train"] != GOLDEN["split_rows.published_train"]


def test_the_golden_record_covers_every_stage_of_the_layer() -> None:
    """A golden test that stops covering a stage is worse than none: it reports agreement it
    never checked. Each prefix here is one module of `hydms/data/`."""
    prefixes = ("hydride_data", "canonical_compositions", "class_rows", "split_rows", "screened")
    for prefix in prefixes:
        assert any(name.startswith(prefix) for name in GOLDEN), prefix


def test_a_deviation_is_reported_as_a_named_diff_not_a_bare_assertion() -> None:
    """Delete the comparison in your head and something must go red. The diff names the fact,
    what was expected and what arrived -- which is the difference between "the split moved"
    and "893 != 896 somewhere in the data layer"."""
    report = diff(GOLDEN, {**GOLDEN, "split_rows.train": 896, "screened.removed": 0})
    assert "split_rows.train" in report
    assert "893" in report and "896" in report
    assert "screened.removed" in report
    assert "hydride_data.rows" not in report, "facts that agree must not appear in the diff"


def test_a_fact_that_disappears_from_the_measurement_is_a_deviation() -> None:
    """The failure mode a dict comparison hides: a stage stops reporting and the record still
    passes because nothing looked for it."""
    without = {name: value for name, value in GOLDEN.items() if name != "canonical_compositions"}
    assert "<absent>" in diff(GOLDEN, without)
