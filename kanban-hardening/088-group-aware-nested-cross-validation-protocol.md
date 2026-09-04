---
id: 88
status: done
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

- [x] `hydms/surrogate/validation.py` provides the project's only fold generator
- [x] Folds are grouped on the canonical composition key from #87 — `StratifiedGroupKFold`, stratified
      on the binned target
- [x] **The group vector is `hydms.data.canonical.group_keys(frame)`, called, not re-derived.** It
      returns one key per row aligned to the frame's index and is the same function #13 splits on;
      two ways of computing "the same material" is two answers. Do not group on the raw formula
      string, on `str.strip()` of it, or on a `groupby` of `Composition` — the first leaks 35 rows,
      and the second reproduces only the whitespace third of the normalisation
- [x] A test asserts **no canonical composition appears in two folds**
- [x] Tuning runs on inner folds; the reported score comes from an outer fold the tuner never saw
- [x] Seeds come from config; the same seed reproduces identical folds
- [x] The leave-one-alloy-class-out protocol (#30) is expressed through the same interface
- [x] The protocol records, with every score, which folds produced it — so a later reader can check
- [x] That record is a `hydms.qa.SelectionRecord` per model compared, carrying `tuned_on`,
      `scored_on` and metrics keyed by split. A protocol that cannot emit one cannot be checked
- [x] The **L2 sentinel**, the **L4 sentinel** and the **L7 sentinel** (ticket 71) are wired to this
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

- 2026-09-04: Landed. `hydms/surrogate/validation.py`: `grouped_folds` (the only fold generator),
  `leave_one_class_out`, and `nested_scores`, which takes the whole matrix *and* #13's split
  assignment and selects the training rows itself -- the same refusal `fit_scaler` makes, so
  cross-validation cannot quietly run over the test split. HG-1 goes 5/13 to **8/13**; suite 770 to
  807. Four things worth carrying forward:

  **The 141-of-896 figure was a floor, and here is the number.** Reproducing the archival shape --
  `StratifiedKFold(5, shuffle=True, random_state=42)` on the binned target, no `groups=` -- over the
  893-row reproduced training split: **181 of 893 rows (20.3%) sit in a fold their canonical
  composition also occupies**, against **144** under the raw formula string. The canonical key adds
  a quarter again to the leak, exactly as the 2026-09-03 note predicted. The group-aware cut leaves
  **156 compositions in each of the five folds** (780 compositions, divided exactly).

  **A fold id is issued for content, not by counting.** `assert_selection_is_nested` finds L4 by
  intersecting `tuned_on` with `scored_on`; if inner and outer ids came from two counters that
  intersection would be empty whatever the protocol did, and the detector would be decoration. So
  `FoldSpace` issues an id *for the set of canonical compositions a fold holds out*, and an inner
  fold over an outer fold's materials collides with it. The L4 live hook checks that premise --
  `space.known(fold.held_out) == fold.id` -- **before** it checks the conclusion. Measuring the
  instruction before implementing it, again.

  **`tuned_on` is measured, not declared.** The inner folds handed to a search record every fold it
  reads, and a search that read none is refused: it tuned on something the protocol cannot write
  down, which is the state the archival pipeline was in. It cannot catch a tuner that rebuilds folds
  from the frame -- but the frame it gets holds the outer fold's training rows and nothing else.

  **The stratification is #13's, not a second one.** `hydms.data.splits.stratify` was exposed for
  exactly this and its docstring says so, so the folds stratify on the merged
  `(temperature bin, target bin)` key rather than on the target alone as the box above asks. Two
  stratification schemes would be two answers to the same question. It is recomputed for every fold
  set from the rows that set is allowed to see -- quantile bins are a function of the targets they
  are computed over, and taking them once over the whole training matrix would let every fold's
  held-out rows shape the folds. About 35 ms a call. (by @assistant)

- 2026-09-04: `model.inner_cv_folds: 3` is new in `pipeline.yaml` -- the outer count was already
  there and the inner one is a separate knob because the cost is their product. The loader now also
  refuses `cv_folds > split.min_stratum_size`: rare strata are merged up to `min_stratum_size` (5)
  compositions and `StratifiedGroupKFold` cannot spread a stratum over more folds than it has
  members. At 5 and 5 the real data sits exactly on that line. (by @assistant)

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
