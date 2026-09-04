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
- [ ] The folds come from `hydms.surrogate.validation.leave_one_class_out`, passed to
      `nested_scores` as its `outer=` cut -- #88 built AC-6's protocol as this protocol with the
      outer partition swapped, and a second scoring path here is the duplication the board is
      shaped to prevent
- [ ] **The smallest class fold is 19 rows.** Measured over the 893-row training split (#88):
      LEA 19 rows / 19 compositions, A2B 29 / 21, HEA 51 / 47, AB 59 / 55, SS 73 / 69, MEA 76 / 69,
      MIC 87 / 81, Mg 96 / 89, AB5 143 / 123, AB2 260 / 207. Report every per-class number beside
      its support and #29's interval; an R2 over 19 rows is not the same claim as one over 260

## Runnable check

```bash
python -m hydms.surrogate.loco --artifact current
```

## Traces to

`docs/PRD-inverse-design.md` — S6, AC-6, R2

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: The two boxes above were added by #88, which built the leave-one-class-out cut and
  measured the class supports while doing it. (by @assistant)
