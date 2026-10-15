"""L1 -- one pinned record of what the data layer produces. Card #15.

Every other file in ``tests/data/`` checks a *mechanism*: that the merge keys, that the split
groups, that screening refuses. This one checks the **result**, as a single record, so that a
change anywhere in the layer shows up as a diff of named facts rather than as one assertion
failing somewhere in a hundred.

Two kinds of fact live here, and the difference is the point:

  - **Facts that must not move.** 1279 rows, 1149 formula strings, 1115 compositions, ten
    alloy classes. The dataset itself is fixed input; if one of these moves, the data
    changed, not the code.
  - **Facts that moved, on purpose, with the movement pinned too.** The split is 893/131/255
    where the published one was 896/136/247, because the unit is now the canonical
    composition; screening removes two rows the archival pipeline kept. Both are recorded
    *with* the superseded value, so nobody can quietly restore the old number and nobody can
    mistake the new one for agreement.

A deviation fails with a table of every differing fact -- name, expected, actual -- because a
bare ``assert 893 == 896`` tells the next reader neither which stage moved nor whether
anything else moved with it.

**There are two records, because there are two screenings, and only one of them is the one
the deployed pipeline runs.** :data:`GOLDEN` is measured by :func:`measure`, which calls
``screen()`` over the whole frame **without** ``label_issues=`` -- CleanLab needs a feature
matrix this layer does not build, so the judgement stage contributes nothing to it and
``screened.label_quality_findings`` is 0. Reading ``screened.removed: 2`` as "screening drops
two rows" was the silent half of this file: the fit behind ``artifacts/v1`` drops **20 of its
893 training rows**, eighteen of them CleanLab's. :data:`DEPLOYED_SCREENING` is that number,
measured by :func:`measure_deployed_screening` through the same public entry point the fit
uses (:func:`hydms.surrogate.model.screened_rows`), with the pre-CleanLab count recorded
beside it over the *same* rows so the two are comparable. It costs ~18 s, which is why it is
marked ``slow``; it is not skipped anywhere, because it is the only check of a number that is
otherwise invisible.
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
from hydms.data.metadata import class_distribution, with_features, with_metadata  # noqa: E402
from hydms.data.screening import LABEL_QUALITY, screen  # noqa: E402
from hydms.data.splits import SPLIT_NAMES, assign_splits, split_summary  # noqa: E402
from hydms.descriptors.contract import CONTRACT, FeatureContract  # noqa: E402
from hydms.descriptors.featurize import featurize  # noqa: E402
from hydms.surrogate.model import ModelSettings, screened_rows  # noqa: E402
from hydms.surrogate.scaler import TRAIN  # noqa: E402
from hydms.surrogate.select import COSTLY_FEATURE  # noqa: E402

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
    # --- screening (#14), STRUCTURAL ONLY. Two rows, both from train. -------------------
    # `measure()` calls `screen()` without `label_issues=`, so these are the exact-duplicate
    # and malformed-formula findings and nothing else. `label_quality_findings` states that
    # as a measured 0 rather than as a comment: if someone starts passing a verdict here it
    # goes red, and until then nobody can read `screened.removed: 2` as what the pipeline
    # drops. What it actually drops is DEPLOYED_SCREENING below.
    "screened.rows_out": 1277,
    "screened.removed": 2,
    "screened.removed_from_val": 0,
    "screened.removed_from_test": 0,
    "screened.label_quality_findings": 0,
    # --- what the descriptor contract can serve, and the one row it cannot --------------
    # Card #29's Q8: CLAUDE.md's 1,115 canonical compositions against the modelling matrix's
    # 1,114 groups over 1,278 rows. It is not an off-by-one and not the temperature
    # duplicates Q8 guessed at. The 21-feature contract (`dev_Gordy_electonegativity`
    # excluded -- `hydms.surrogate.select.COSTLY_FEATURE`) refuses exactly one row, `Eu1Ni5`,
    # whose europium blocks all six JARVIS features; that row is the *only* row of its
    # canonical composition, so losing it loses exactly one group. 1115 - 1 = 1114, and the
    # arithmetic is asserted below rather than left as prose. It sits in `test`, which is why
    # `split_rows.train` is 893 on both populations.
    "modelling_rows": 1278,
    "modelling_compositions": 1114,
    "unfeaturisable_rows": 1,
    "unfeaturisable_compositions": 1,
    "unfeaturisable_rows_in_train": 0,
}

#: What the **deployed** screening does -- the call the fit behind ``artifacts/v1`` makes, on
#: training rows only, with CleanLab's verdict. Measured by :func:`measure_deployed_screening`
#: and reconciled against ``reports/model/conformal-rows.csv``, which records the same 893 and
#: 20 for that run. Kept as a second record rather than folded into :data:`GOLDEN` because it
#: needs the featuriser and ~18 s of cross-fitting, and because the two are answers to
#: different questions: what the *stage* removes with no judgement, and what the *pipeline*
#: removes with one.
DEPLOYED_SCREENING: dict[str, object] = {
    "deployed.offered": 893,
    "deployed.kept": 873,
    "deployed.removed": 20,
    "deployed.flagged": 18,
    # The same rows, screened with no verdict -- the pre-CleanLab value recorded beside the
    # post-CleanLab one, the way `split_rows.published_*` records the pre-#13 split. That the
    # two structural removals are both in `train` is why GOLDEN's whole-frame 2 and this 2
    # are the same number; it is measured on these 893 rows, not assumed from that.
    "deployed.removed_before_cleanlab": 2,
}

#: Facts whose value is a *decision recorded*, not a measurement of today's code. They are
#: compared like the rest so that restoring an old number is a visible failure; the reason
#: each was superseded is on the card named here.
SUPERSEDED = {
    "split_rows.published_train": "#13 -- grouping moved from the formula string to the composition",
    "split_rows.published_val": "#13",
    "split_rows.published_test": "#13",
}


def modelling_contract() -> FeatureContract:
    """The 21-feature contract the modelling matrix is built from.

    ``COSTLY_FEATURE`` is imported rather than spelled out: the whole point of the facts it
    decides is that they track the contract, and a copy of the string here would keep passing
    after the contract changed under it.
    """
    return FeatureContract.from_names([name for name in CONTRACT.names if name != COSTLY_FEATURE])


def featurisable(record: pd.DataFrame, contract: FeatureContract) -> list[object]:
    """The labels the contract can serve, by its own verdict rather than by a list here."""
    return [
        label
        for label, formula in record["Composition"].items()
        if contract.computability(parse_formula(formula)).complete
    ]


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

    keep = featurisable(raw, modelling_contract())
    refused = [label for label in raw.index if label not in set(keep)]

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
        "screened.label_quality_findings": sum(
            1 for finding in screened.findings if finding.kind == LABEL_QUALITY
        ),
        "modelling_rows": len(keep),
        "modelling_compositions": keys.loc[keep].nunique(),
        "unfeaturisable_rows": len(refused),
        "unfeaturisable_compositions": keys.nunique() - keys.loc[keep].nunique(),
        "unfeaturisable_rows_in_train": int((split.loc[refused] == TRAIN).sum()),
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


def measure_deployed_screening() -> dict[str, object]:
    """Screen the training rows the way the fit does, and record what it removed.

    Not a reimplementation of the pipeline: it builds the matrix the way
    ``hydms.surrogate.select`` builds it and then calls
    :func:`hydms.surrogate.model.screened_rows`, which is the entry point
    ``hydms.surrogate.deploy`` calls and the one that wrote
    ``reports/model/conformal-rows.csv``'s 893 / 20. Anything measured through a private
    helper here would be a second answer that could agree with itself while disagreeing with
    the fit.

    ``removed_before_cleanlab`` is the same 893 rows through ``screen()`` with no verdict, so
    the pre- and post-CleanLab counts are over one population rather than two.
    """
    contract = modelling_contract()
    record = with_metadata(load_hydride_data())
    split = assign_splits(record)
    keep = featurisable(record, contract)
    usable = record.loc[keep]
    frame = with_features(
        usable, featurize(usable["Composition"], usable["temperature(K)"], contract=contract)
    )

    train = [label for label in frame.index if split.loc[label] == TRAIN]
    deployed = screened_rows(frame, train, settings=ModelSettings.from_config())
    structural = screen(frame.loc[train], pd.Series(TRAIN, index=pd.Index(train)))

    return {
        "deployed.offered": deployed.offered,
        "deployed.kept": len(deployed.kept),
        "deployed.removed": len(deployed.removed),
        "deployed.flagged": deployed.flagged,
        "deployed.removed_before_cleanlab": len(structural.removed),
    }


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


def test_the_off_by_one_against_the_modelling_matrix_is_the_one_unfeaturisable_row() -> None:
    """Card #29's Q8, closed by arithmetic rather than by a narrative sentence.

    1,115 canonical compositions over the 1,279 curated rows; 1,114 over the 1,278 the
    modelling matrix carries. Q8 left open whether that was a real off-by-one and guessed at
    temperature duplicates. It is neither: the 21-feature contract refuses exactly one row,
    that row is the only row of its composition, and it is held out. Each of those three is a
    fact in GOLDEN, so this test is the equation that ties them together -- if a second row
    ever became unfeaturisable, or a refused row stopped being alone in its composition, the
    equation is what goes red.
    """
    assert GOLDEN["canonical_compositions"] == 1115
    assert (
        GOLDEN["modelling_compositions"]
        == GOLDEN["canonical_compositions"] - GOLDEN["unfeaturisable_compositions"]
    )
    assert GOLDEN["modelling_rows"] == GOLDEN["hydride_data.rows"] - GOLDEN["unfeaturisable_rows"]
    # One row refused, one composition lost: the refused row was alone in its composition.
    assert GOLDEN["unfeaturisable_rows"] == GOLDEN["unfeaturisable_compositions"] == 1
    # And it is not a training row, which is why 893 is the train size on both populations.
    assert GOLDEN["unfeaturisable_rows_in_train"] == 0
    assert GOLDEN["split_rows.train"] == 893


@pytest.mark.slow
def test_the_deployed_screening_removes_twenty_of_the_eight_hundred_and_ninety_three() -> None:
    """The number GOLDEN cannot see, because GOLDEN's `screen()` call has no verdict to act on.

    ~18 s, nearly all of it CleanLab cross-fitting the 893 x 14 training matrix. That cost is
    the reason this was invisible and is not a reason to leave it so: nothing else in the
    suite pins what the pipeline actually drops, and `reports/model/conformal-rows.csv` is a
    committed artefact of one run rather than a check.
    """
    report = diff(DEPLOYED_SCREENING, measure_deployed_screening())
    assert not report, f"the deployed screening no longer removes what it removed:\n\n{report}\n"


def test_the_deployed_removals_account_for_themselves() -> None:
    """Twenty removed, eighteen of them CleanLab's and two of them structural.

    Asserted as an identity over the record rather than as three loose numbers: `removed` is
    exactly the CleanLab flags plus the pre-CleanLab removals, which says both that every flag
    on a training row was acted on and that no row was counted twice. If `screen()` ever
    started double-counting a row that is both a duplicate and a label issue, `removed` would
    fall below the sum and this is what would say so.
    """
    assert (
        DEPLOYED_SCREENING["deployed.removed"]
        == DEPLOYED_SCREENING["deployed.flagged"]
        + DEPLOYED_SCREENING["deployed.removed_before_cleanlab"]
    )
    assert (
        DEPLOYED_SCREENING["deployed.kept"]
        == DEPLOYED_SCREENING["deployed.offered"] - DEPLOYED_SCREENING["deployed.removed"]
    )
    assert DEPLOYED_SCREENING["deployed.offered"] == GOLDEN["split_rows.train"]
    # The contrast this file exists to make legible: the structural record sees no judgement.
    assert GOLDEN["screened.label_quality_findings"] == 0
    assert DEPLOYED_SCREENING["deployed.flagged"] > 0


def test_the_golden_record_covers_every_stage_of_the_layer() -> None:
    """A golden test that stops covering a stage is worse than none: it reports agreement it
    never checked. Each prefix here is one module of `hydms/data/`, and `deployed` is the
    screening stage as the pipeline runs it -- the half that was missing until #15 closed."""
    prefixes = ("hydride_data", "canonical_compositions", "class_rows", "split_rows", "screened")
    for prefix in prefixes:
        assert any(name.startswith(prefix) for name in GOLDEN), prefix
    assert any(name.startswith("deployed") for name in DEPLOYED_SCREENING)
    assert set(GOLDEN).isdisjoint(DEPLOYED_SCREENING), "the two records must not share a fact"


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
