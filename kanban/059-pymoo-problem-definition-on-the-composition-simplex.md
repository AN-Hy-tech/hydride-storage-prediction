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
