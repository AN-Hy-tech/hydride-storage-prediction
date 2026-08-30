---
id: 13
status: backlog
priority: High
blocked_by: [10, 11]
assignee: "@amirhossein"
tags: [p1, l1, S1, AC-1]
---

# Stratified unique-formula splits, seeded and reproducible

**Phase 1 — Hardening Chapter 1** · **L1 Data** · Estimate: 1 d

> **Owns (hidden behind this module):** The train/val/test protocol and the guarantee that no formula spans two splits.

## Why this exists

The existing `split_data.py` splits on unique formulae with stratification, which the
domain memo notes is better than most published hydride ML. Preserve that behaviour exactly
— this ticket ports it, it does not redesign it.

Documented target: 1279 rows, 1149 unique formulae, 896 / 136 / 247.

## Done when

- [ ] Split is stratified on binned target and grouped by unique formula
- [ ] **No formula appears in more than one split** — asserted, not assumed
- [ ] Seed comes from config; same seed reproduces identical splits
- [ ] Split sizes match the documented 896 / 136 / 247

## Runnable check

```bash
python -m pytest tests/data/test_splits.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S1, AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
