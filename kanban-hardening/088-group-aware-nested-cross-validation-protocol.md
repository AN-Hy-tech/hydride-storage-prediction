---
id: 88
status: backlog
priority: High
blocked_by: [13, 23]
assignee: "@amirhossein"
tags: [ph, l3, AC-6, R4]
---

# Group-aware nested cross-validation protocol

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How a score is produced, and the guarantee that the data which produced it was never used to choose it.

## Why this exists

Two leaks share one root: the reported score comes from the same data that chose the
configuration being scored.

**L7** — cross-validation splits rows, not groups. Measured on the reproduced training split, **141 of
896 rows (15.7 %)** have their exact formula in a different fold. Because the features are composition
statistics plus temperature, those rows are near-identical to rows the model trained on. Some
compositions appear six times at six temperatures with one identical descriptor vector.

**L4** — the same `splits` object is used to tune and then to report. The published `CV_R2_Mean` is a
tuning optimum, not a held-out estimate.

This card builds the protocol both leaks are fixed by, once, in one place, so that every later card
scores through it rather than re-deriving folds.

## Done when

- [ ] `hydms/surrogate/validation.py` provides the project's only fold generator
- [ ] Folds are grouped on the canonical composition key from #87 — `StratifiedGroupKFold`, stratified
      on the binned target
- [ ] **The group vector is `hydms.data.canonical.group_keys(frame)`, called, not re-derived.** It
      returns one key per row aligned to the frame's index and is the same function #13 splits on;
      two ways of computing "the same material" is two answers. Do not group on the raw formula
      string, on `str.strip()` of it, or on a `groupby` of `Composition` — the first leaks 35 rows,
      and the second reproduces only the whitespace third of the normalisation
- [ ] A test asserts **no canonical composition appears in two folds**
- [ ] Tuning runs on inner folds; the reported score comes from an outer fold the tuner never saw
- [ ] Seeds come from config; the same seed reproduces identical folds
- [ ] The leave-one-alloy-class-out protocol (#30) is expressed through the same interface
- [ ] The protocol records, with every score, which folds produced it — so a later reader can check
- [ ] That record is a `hydms.qa.SelectionRecord` per model compared, carrying `tuned_on`,
      `scored_on` and metrics keyed by split. A protocol that cannot emit one cannot be checked
- [ ] The **L2 sentinel**, the **L4 sentinel** and the **L7 sentinel** (ticket 71) are wired to this
      module — `live` checks in `hydms/qa/sentinels.py` calling `hydms.qa.assert_selection_is_nested`
      on the real records and `hydms.qa.assert_disjoint_groups` on the real folds. Gate HG-1 goes red
      once `hydms/surrogate/validation.py` exists without them

## Runnable check

```bash
conda run -n Project python -m pytest tests/surrogate/test_validation.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S4; `docs/PRD-inverse-design.md` — AC-6, R4

## Narrative

- 2026-09-03: #87 landed the group key. `hydms.data.canonical.group_keys` is the single seam — 1279
  rows to 1115 canonical compositions — and the L7 sentinel's live hook should call
  `assert_disjoint_groups` on folds keyed by it. Note that the 141-of-896 figure above was measured
  on the **raw formula string**, so it is a floor: the canonical key merges spellings the string kept
  apart, and the true row-level collision count inside the published training split can only be
  higher (by @assistant)

- 2026-09-02: Created for Phase H. Expect the reported score to fall when this lands — that is
  the point, and per PRD R4 it is a reported result, not a failure. Note the installed
  `ml-model-training` skill is silent on both grouping and nested CV; its worked example would
  reintroduce exactly these two leaks (by @assistant)
