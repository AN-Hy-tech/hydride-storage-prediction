---
id: 13
status: backlog
priority: High
blocked_by: [10, 11, 87]
assignee: "@amirhossein"
tags: [p1, l1, S1, AC-1]
---

# Stratified unique-formula splits, seeded and reproducible

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 1 d

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

- [ ] Split is stratified on binned target and grouped by **canonical composition**, not raw formula
- [ ] **No canonical composition appears in more than one split** — asserted, not assumed
- [ ] The 16 known cross-split collisions are covered by a regression test
- [ ] The **L8 sentinel** (ticket 71) is wired to this module — a `live` check in
      `hydms/qa/sentinels.py` calling `hydms.qa.assert_disjoint_groups` on the real splits, keyed on
      the canonical composition. Gate HG-1 goes red once `hydms/data/splits.py` exists without one
- [ ] Seed comes from config; same seed reproduces identical splits
- [ ] Split sizes are close to the documented 896 / 136 / 247 and any difference is explained by the
      35 rows the raw-string key formerly allowed to leak — an exact match is **not** expected, and
      matching exactly would mean the grouping key did not change

## Runnable check

```bash
python -m pytest tests/data/test_splits.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Amended for Phase H. The published assertion (no raw formula spans two splits) passes while 35
  rows leak, because 1,149 formula strings collapse to 1,115 canonical compositions. Grouping moves to
  the canonical key. Expect the split sizes to shift slightly; that shift is the fix working (by @assistant)
