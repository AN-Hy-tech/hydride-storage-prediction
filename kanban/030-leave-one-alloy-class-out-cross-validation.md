---
id: 30
status: backlog
priority: High
blocked_by: [12, 28]
assignee: "@amirhossein"
tags: [p1, l3, S6, AC-6, R2]
---

# Leave-one-alloy-class-out cross-validation

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How well the model transfers to a family it has not seen.

## Why this exists

The single most important validation number in this thesis. Beltrame et al. 2025 found
hydride models are accurate *within* a family and poor *across* families; Li et al. 2025
found heuristic splits 'mostly test interpolation rather than true extrapolation'.

**Expect this to be substantially worse than the random-split number, and report it anyway.**
That honesty is a contribution, and it is what tells Architecture A how far a candidate may
stray from known chemistry.

## Done when

- [ ] One fold per alloy class; train on the rest, test on the held-out class
- [ ] Per-class R2, MAE and support reported, not only an average
- [ ] Classes with too few rows to test are reported as such, not silently skipped
- [ ] Result feeds the applicability-domain ceiling (48) and the Chapter 1 revision (37)

## Runnable check

```bash
python -m hydms.surrogate.loco --artifact current
```

## Traces to

`docs/PRD-inverse-design.md` — S6, AC-6, R2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
