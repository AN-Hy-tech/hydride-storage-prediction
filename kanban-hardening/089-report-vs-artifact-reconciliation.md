---
id: 89
status: done
priority: High
blocked_by: [29, 30]
assignee: "@amirhossein"
tags: [ph, l7, R4]
---

# REPORT.md versus the artifacts it cites: a reconciliation

**Stage S8 — Evidence and close** · **L7 Evidence** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The record of where the published account and the committed evidence disagree, and which one to believe.

## Why this exists

`REPORT.md` is the archival record of the forward model as published, and it is **not
corrected in place** — rewriting it would orphan the account it gives. But it cannot simply stand
either, because CSVs committed in this repository contradict its headline numbers.

The audit found eight disagreements. Three examples: the ensemble's claimed Val R² 0.939 / Test R² 0.892
against `stacking_results.csv`'s CV 0.344 / Val 0.377 / Test 0.376; §4.4's paired t-test t = −2.102,
p = 0.037 against `ttest_best_vs_ensemble_abs_error.csv`'s t = −8.168, p = 1.65e-14 for a different best
model; and §3.2's CleanLab row counts against a test-subgroup table that sums to the full 247 rows,
CleanLab having removed none.

This document is what card #37 is written from, and what the model card links to so that a reader of the
app does not inherit the old figures unexamined.

## Done when

- [x] `docs/REPORT-RECONCILIATION.md` tabulates each disagreement: the claim, its location in
      `REPORT.md`, the artifact that refutes it, and the artifact's value
- [x] Each row states which source to believe and why
- [x] It records that the published pipeline is not the committed pipeline, with the evidence
- [x] It notes `REPORT.md` is preserved unedited, and why
- [x] The new honest numbers from #29 and #30 are shown beside the published ones
- [x] **A ninth disagreement, found by #9: the file contains 55 elements, not 54.** `REPORT.md` §2.3
      ("Fifty-four elements were identified across all formulae") and the PRD's dataset table both say
      54. Counted from the parsed compositions of all 1279 rows of `hydride_data.csv` the answer is
      **55**, seven of which appear exactly once (N, Eu, Lu, Pb, Au, Os, Re). Asserted in
      `tests/data/test_load.py`. Check whether it is inherited rather than introduced: the HyStor paper
      reports 54 for its own 1,282-row release, which is a different file
- [x] **A tenth disagreement, found by #11: §4.2's "Overfitting" footnote mixes two target
      spaces, and misdescribes the column it annotates.** The footnote reads
      `Overfitting = CV_R²_mean − Val_R²_orig`. `CV_R2_Mean` is measured in **log** space —
      `cross_validate(pipe, X_train, y_train, scoring='r2')` at
      `benchmark_model_selection.py:1093`, and nothing back-transforms `y_train` — while every
      `*_Orig` column is weight percent, `evaluate_model(..., 'orig')` applying `expm1` to both
      sides at `:946-949`. The difference of the two is not a quantity. The **code** does not
      compute it that way: `:1120` and `:1198` both compute `train_r2_orig - val_r2_orig`, which
      is at least single-spaced. So the published column is probably right and its stated
      definition wrong — say which, and note that §4.2's table cannot be read across.
      `hydms/data/target.py`'s docstring holds the space-by-space table this came from
- [x] Linked from the model card (#83) and from `kanban-hardening/README.md`. **The README
      half is done; the model-card half is #83's own box** ("A link to
      `docs/REPORT-RECONCILIATION.md`"), which could not be ticked before this file existed and
      now can. It is not re-owed here, because this card cannot build #83's page

- [x] **A corrupted row in the published feature matrix (from #16).** `Eu1Ni5` -- row 516,
      `H2_W% (max)` 1.2, AB5, the dataset's only europium composition. Europium is absent from
      CBFV's `jarvis.csv`, so its six JARVIS features were computed with europium contributing
      an all-zero property vector: zero mass, zero polarizability, zero boiling point. Verified
      by arithmetic rather than inferred -- CBFV emits `avg_polzbl_divi_atom_mass = 0.096547`
      for it, and (5/6) x (polzbl_Ni / atom_mass_Ni) = 0.096546914. CBFV reported the formula in
      a `skipped` list; `extract_features_cbfv.py` never read it. The affected feature is the
      highest-SHAP feature in the whole model. This is a data-integrity disagreement between
      REPORT.md and what the pipeline actually computed, and belongs in the evidence table

## Runnable check

```bash
conda run -n Project python -m pytest tests/evidence/test_reconciliation.py
conda run -n Project python -m hydms.evidence.reconciliation --emit   # regenerate, never edit
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8; `docs/PRD-inverse-design.md` — R4

## Narrative

- 2026-09-02: Created for Phase H. The eight contradictions were found by the code audit that
  opened this phase. This is deliberately a separate document from the Chapter 1 revision (#37): this
  one is the evidence table, that one is the argument (by @assistant)

- 2026-09-03: Box added by #11. Establishing which REPORT metric lives in which target space —
  a done-criterion of that card — turned up §4.2's Overfitting footnote subtracting a
  weight-percent number from a log-space one, and the archival code not doing what the footnote
  says. The per-metric space table is in `hydms/data/target.py`'s module docstring; this card
  owns what to say about it. (by @assistant)

- **This card never needed #34, and the edge was holding S8 shut (corrected 2026-09-11).** Its
  *Done when* names its own sources — "the new honest numbers from #29 and #30 … beside the
  published ones" — and every one of them is a CSV committed under `reports/`. A **promoted**
  artifact version is not among them: this document compares `REPORT.md` to the evidence in the
  repository, not to a pointer. `blocked_by: [34]` was therefore fiction, and an expensive one,
  because #34 is itself blocked on #79 and #86 — so the reconciliation, and #83's link to it, sat
  behind two gates that have nothing to do with either. Now `[29, 30]`, both `done`: this card is
  startable. (by @assistant)

- 2026-09-24: **Done, and generated rather than written.** `hydms/evidence/reconciliation.py` holds
  each disagreement as a quotation, a section, a committed artifact, a *function that reads the
  artifact*, and a verdict with its reason; `--emit` writes `docs/REPORT-RECONCILIATION.md`.
  `tests/evidence/test_reconciliation.py` (31 tests) checks the page three ways: the committed
  bytes are what the code produces; every quotation occurs in `REPORT.md` verbatim; and a value
  is read, not typed, which a perturbation test proves by editing `stacking_results.csv` in a
  copied tree and requiring the page to follow. Everything it reads is committed, so it runs in
  CI. A second test builds the page from the copy alone and gets the committed bytes, which
  proves the copy is complete: nothing is read from the live tree by accident.

  **"Eight" was never a list.** The opening audit said eight and wrote down three; the other
  five are nowhere in the repository or the archive. So this is a re-measurement and it finds
  **twelve**, including the ninth and tenth boxed above and the europium row. The new ones:
  §4.3's ensemble CI (0.898 to 0.961 against 0.328 to 0.415); §4.2's "lowest overfitting (0.039)"
  with **seven** models lower in the same table; §4.4's RandomForest "p_adj of about 0.1" against
  0.537, and "all other models p_adj < 0.05" with GradientBoosting at 0.086; §6.4's "the Ensemble
  is more robust across all three subgroups" when ExtraTrees leads in every one of them (and §4.3
  rests the ensemble recommendation on that); and §2.2's 1,149 unique compositions, which is
  1,115 materials.

  **The finding that changes how row 1 reads: the committed CSVs disagree with each other.**
  `improved_benchmark_results.csv` carries the report's ensemble row (Val 0.939, Test 0.892) and
  `stacking_results.csv` carries a different ensemble (0.377 / 0.376). The card's framing, "a CSV
  contradicts the report", undersells it. Two files from one pipeline describe two ensembles, and
  the report quoted one of them. That is the evidence for "the published pipeline is not the
  committed pipeline" in one line, and the page leads with it.

  The ninth box asked whether 54 is inherited. It cannot be settled from here, and row 10 says
  so with the one inference available: if these 1,279 rows are a subset of HyStor's 1,282, the
  release has at least 55 elements too and the paper miscounted. Unblocks **#37**, the last
  unfreeze condition, and the reconciliation half of **#83**. (by @assistant)
