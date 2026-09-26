---
id: 13
status: done
priority: High
blocked_by: [10, 11, 87]
assignee: "@amirhossein"
tags: [p1, l1, S1, AC-1]
---

# Stratified unique-formula splits, seeded and reproducible

**Stage S2 — Data layer** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** The train/val/test protocol and the guarantee that no
> **canonical composition** spans two splits.

## Why this exists

The existing `split_data.py` splits on unique formulae with stratification, which the
domain memo notes is better than most published hydride ML. Port the stratification and the
rare-stratum merging exactly — this ticket does not redesign them.

**Amended for Phase H — the grouping key changes.** `split_data.py` groups on the raw formula
**string** and asserts that no formula spans two splits. That assertion passes, and it is not the
property anyone wants. Measured on the real data: 1,279 rows carry 1,149 distinct formula strings but
only **1,115 distinct canonical compositions**, and **16 of those (35 rows) land in more than one
split** under the published seed. `Ce1Mg12` sits in test while `Mg12Ce1` sits in validation — the same
measurement, 6.0 wt% at 598 K, written two ways. `Pr1Co5` and `Pr1Co5 ` differ by a trailing space.
Every selected feature is a composition statistic plus temperature, so these rows carry byte-identical
feature vectors up to temperature. That is leak **L8**.

The split therefore groups on the canonical key from ticket 87.

Documented target: 1279 rows, 1149 raw formulae, 896 / 136 / 247.

## Done when

- [x] Split is stratified on binned target and grouped by **canonical composition**, not raw formula
- [x] **No canonical composition appears in more than one split** — asserted, not assumed
- [x] **Group on `hydms.data.canonical.group_keys(frame)`, called, not re-derived.** #87 landed it:
      one key per row, aligned to the frame's index, the same function #88's folds group on. The
      published protocol is reproduced end to end in `tests/data/test_canonical.py::published_split`
      — stratification, rare-stratum merging, both `StratifiedShuffleSplit` calls, seed 42 — and
      returns 896/136/247 exactly, so this card can port from a reproduction that is known faithful
      rather than from the archival file
- [x] The 16 known cross-split collisions are covered by a regression test
- [x] The **L8 sentinel** (ticket 71) is wired to this module — a `live` check in
      `hydms/qa/sentinels.py` calling `hydms.qa.assert_disjoint_groups` on the real splits, keyed on
      the canonical composition. Gate HG-1 goes red once `hydms/data/splits.py` exists without one
- [x] Seed comes from config; same seed reproduces identical splits
- [x] Split sizes are close to the documented 896 / 136 / 247 and any difference is explained by the
      35 rows the raw-string key formerly allowed to leak — an exact match is **not** expected, and
      matching exactly would mean the grouping key did not change

- [x] **Grouping on the key moves four `(key, temperature)` pairs, not only the split boundaries.**
      Canonicalisation takes 1272 distinct `(Composition, temperature(K))` pairs to 1268, and four of
      the eleven repeats exist only because two spellings became one material. Those four are two
      measurements of one material at one temperature; the split must place both on the same side,
      which grouping on the key does for free, but any per-row deduplication added later must not
      silently drop one of them

- [x] **Measured: 893 / 131 / 255 rows, over 780 / 111 / 224 compositions.** The published
      896/136/247 came from 1149 formula strings; this comes from 1115 compositions, so it
      cannot match and matching would have meant the key changed nothing. Fractions still land
      where `pipeline.yaml` asks — 0.698 / 0.102 / 0.199 against 0.70 / 0.10 / 0.20
- [x] **The archival check stays green here, and that is the point of asserting it.** Grouping
      on the composition implies grouping on the string and never the reverse, so
      `split_data.py:126-129` passes on this split too. Asserted in `tests/data/test_splits.py`
      so the relationship between the weak check and the strong one is on record rather than
      inferred: the archival assertion passing has never meant anything
- [x] **The row order of the input does not change anybody's split.** The decision is made over
      groups and `groupby` sorts, so the permutation is a function of the keys, the stratum
      counts and the seed alone. Same invariance the keyed merge has (#10), asserted the same way
- [x] **The mean is taken in model space, and that is not free.** `split_data.py` read the
      already-log-transformed `target` column, so the per-group mean is a mean of `log1p` values.
      Quantile binning is invariant to a monotone transform but a *mean over a group* is not, so
      averaging in weight percent would move groups of two or more rows into different bins.
      `stratify()` goes through `hydms.data.target.to_model_space` for that reason

## Runnable check

```bash
conda run --no-capture-output -n Project python -m pytest tests/data/test_splits.py -q
conda run --no-capture-output -n Project python -m pytest tests/leaks/test_l7_l8_grouping.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-09-03: #87 landed the key and reproduced the published split to demonstrate it. Measured
  through that reproduction: the archival assertion (no *formula string* spans two splits) is green
  while 16 canonical compositions — 35 rows — sit on both sides of a line, and grouping the same
  protocol on the canonical key leaves none. Both halves are asserted in
  `tests/data/test_canonical.py`; this card's job is to make the split module do it (by @assistant)

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Amended for Phase H. The published assertion (no raw formula spans two splits) passes while 35
  rows leak, because 1,149 formula strings collapse to 1,115 canonical compositions. Grouping moves to
  the canonical key. Expect the split sizes to shift slightly; that shift is the fix working (by @assistant)

- 2026-09-03: Landed. `hydms/data/splits.py` — `assign_splits`, `stratify`, `split_summary`;
  16 tests in `tests/data/test_splits.py`; the **L8 sentinel is wired** and `audit()` now reports
  `L8 green`, the second of thirteen. Three things this card taught:

  **Porting from the reproduction rather than from the archival file was the whole job.** #87's
  `published_split` fixture already re-ran `split_data.py:63-135` and matched 896/136/247 exactly,
  so the port had a known-faithful source and the only edit was the unit. Everything else —
  quantile bins, the rare-stratum merge with its distances measured against the *pre-merge*
  counts, both `StratifiedShuffleSplit` calls — is transcribed.

  **The averaging space is a real decision hiding inside a transcription.** Quantile binning does
  not care about a monotone transform, so it is tempting to bin the raw target; but the archival
  code averaged the *log* column per formula, and a mean does not commute with `log1p`. Any group
  with two or more rows would land in a different bin. Recorded in the module docstring because it
  is exactly the kind of thing a later "simplification" removes.

  **The live hook is cached, because the protocol is not cheap.** Two shuffle splits over 1115
  compositions on top of keying 1279 formulae costs ~0.7 s, and `audit()` runs on every gate
  invocation and every test in `tests/leaks/`. `_l8_real_splits` is `lru_cache`d, the same shape
  `_l9_real_frames` uses. The hook re-derives the keys with `group_keys` rather than trusting
  anything the split returned, so a module that had quietly grouped on something else would show
  up as a straddle rather than as agreement with itself. (by @assistant)
