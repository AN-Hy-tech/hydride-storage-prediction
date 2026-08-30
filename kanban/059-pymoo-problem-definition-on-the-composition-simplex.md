---
id: 59
status: backlog
priority: High
blocked_by: [51, 52]
assignee: "@amirhossein"
tags: [pb, l5, S5]
---

# pymoo problem definition on the composition simplex

**Phase B — Multi-objective EA** · **L5 Search** · Estimate: 2 d

> **Owns (hidden behind this module):** How the design problem is posed to an evolutionary algorithm.

## Why this exists

Architecture B as a second `Proposer`, not a second project. Decision variables are
fractions on the simplex for a **fixed element subset**, repaired to sum to 1.

Objectives: maximise LCB(capacity), minimise cost, maximise ElMD novelty — all already
computed by the evaluator (51).

ADR 5 records why the subset is fixed per run rather than encoded as mixed-integer: the
mixed encoding is fiddly and produces fronts that mix chemistries, which are far harder to
present and defend.

## Done when

- [ ] pymoo `Problem` with the simplex repair operator and three objectives
- [ ] Objectives read from the evaluator's output; no objective is computed twice
- [ ] Implements the `Proposer` protocol so the existing runner drives it unchanged
- [ ] A short smoke run converges on a toy 2-element case with a known answer

## Runnable check

```bash
python -m hydms.search.run --proposer evolve --family AB2 --generations 5 --dry-run
```

## Traces to

`docs/PRD-inverse-design.md` — S5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-08-30: **API check before implementation — subclass `Problem`, not `ElementwiseProblem`.**
  pymoo's documented getting-started example uses `ElementwiseProblem`, which calls `_evaluate`
  once per candidate. That directly violates PRD risk **R6**, which requires batched featurisation
  and forbids per-candidate loops; NSGA-II makes far more surrogate calls than enumeration does.
  The vectorised `Problem` base evaluates a whole population per call and is the right shape here.

  Also: pymoo minimises everything, so maximising the capacity lower confidence bound means
  returning `-lcb` — getting that backwards yields a confident, plausible, exactly wrong Pareto
  front. Constraints are feasible when `g <= 0`, so a VEC window becomes two of them (card #60).
  `seed=` is a `minimize()` argument, which is what card #63 varies. Details in
  `docs/LIBRARY-APIS.md`. (by @assistant)
