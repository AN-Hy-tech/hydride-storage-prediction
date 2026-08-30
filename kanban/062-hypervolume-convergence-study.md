---
id: 62
status: backlog
priority: High
blocked_by: [61]
assignee: "@amirhossein"
tags: [pb, l5, S5]
---

# Hypervolume convergence study

**Phase B — Multi-objective EA** · **L5 Search** · Estimate: 1 d

> **Owns (hidden behind this module):** Evidence that the search actually converged.

## Why this exists

A Pareto front without convergence evidence is an assertion. Hypervolume versus generation
is the standard demonstration, and it is a principal reason pymoo was chosen over Optuna's
sampler.

## Done when

- [ ] Hypervolume recorded per generation for every subset run
- [ ] Reference point chosen and documented once, applied consistently across runs
- [ ] Convergence plot produced per subset, thesis-ready
- [ ] A run whose hypervolume is still climbing at termination is flagged as under-converged

## Runnable check

```bash
python -m hydms.search.analyse --study hypervolume
```

## Traces to

`docs/PRD-inverse-design.md` — S5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
