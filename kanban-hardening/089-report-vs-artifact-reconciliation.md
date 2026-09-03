---
id: 89
status: backlog
priority: High
blocked_by: [34]
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

- [ ] `docs/REPORT-RECONCILIATION.md` tabulates each disagreement: the claim, its location in
      `REPORT.md`, the artifact that refutes it, and the artifact's value
- [ ] Each row states which source to believe and why
- [ ] It records that the published pipeline is not the committed pipeline, with the evidence
- [ ] It notes `REPORT.md` is preserved unedited, and why
- [ ] The new honest numbers from #29 and #30 are shown beside the published ones
- [ ] **A ninth disagreement, found by #9: the file contains 55 elements, not 54.** `REPORT.md` §2.3
      ("Fifty-four elements were identified across all formulae") and the PRD's dataset table both say
      54. Counted from the parsed compositions of all 1279 rows of `hydride_data.csv` the answer is
      **55**, seven of which appear exactly once (N, Eu, Lu, Pb, Au, Os, Re). Asserted in
      `tests/data/test_load.py`. Check whether it is inherited rather than introduced: the HyStor paper
      reports 54 for its own 1,282-row release, which is a different file
- [ ] **A tenth disagreement, found by #11: §4.2's "Overfitting" footnote mixes two target
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
- [ ] Linked from the model card (#83) and from `kanban-hardening/README.md`

- [ ] **A corrupted row in the published feature matrix (from #16).** `Eu1Ni5` -- row 516,
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
python scripts/check_board.py --root .
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
