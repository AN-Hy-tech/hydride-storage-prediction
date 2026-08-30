---
id: 47
status: backlog
priority: Normal
blocked_by: [20, 44]
assignee: "@amirhossein"
tags: [pa, l4, S3]
---

# Atomic size-mismatch screens

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** The geometric solid-solution criteria.

## Why this exists

Atomic size mismatch δ and the hydride-forming to non-forming radius ratio r_A/r_B.
Published AB2 criteria: δ >= 9.7%, r_A/r_B in 1.149-1.219.

`REPORT.md` 7.2 already found `dev_Zunger_radii_sum` (size deviation) is a top-ranked SHAP
feature with r = -0.404, so the model has independently learned that size mismatch matters.
These screens make that physics explicit as a constraint rather than leaving it implicit in
the surrogate.

## Done when

- [ ] δ and r_A/r_B computed from composition and element radii
- [ ] Thresholds per family in config with sources cited
- [ ] Mixing-enthalpy bounds included where the Hume-Rothery criteria apply
- [ ] Screens report the computed value alongside the verdict, not just pass/fail

## Runnable check

```bash
python -m pytest tests/screens/test_size.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
