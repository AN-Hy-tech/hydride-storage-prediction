---
id: 60
status: backlog
priority: High
blocked_by: [59]
assignee: "@amirhossein"
tags: [pb, l5, S5, R1]
---

# Constraint handling

**Phase B — Multi-objective EA** · **L5 Search** · Estimate: 1 d

> **Owns (hidden behind this module):** Which candidates the optimiser is forbidden to propose.

## Why this exists

The screens (45-48) become **constraints** rather than post-hoc filters, so the optimiser
never spends its budget in forbidden regions.

This is load-bearing for risk R1: without the applicability-domain ceiling as a hard
constraint, NSGA-II will find and exploit exactly the extrapolation artifacts the guard
rails exist to prevent.

## Done when

- [ ] VEC window, δ bounds, mixing-enthalpy bounds, minimum fraction, maximum element count and AD ceiling all wired as pymoo constraints
- [ ] Constraint violation magnitudes returned, not booleans, so the algorithm can gradient toward feasibility
- [ ] A test asserts no returned Pareto member violates a hard constraint
- [ ] Constraint settings recorded in the run header for the R1 iteration log

## Runnable check

```bash
python -m pytest tests/search/test_constraints.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S5, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
