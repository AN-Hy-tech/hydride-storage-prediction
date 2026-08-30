---
id: 66
status: backlog
priority: Normal
blocked_by: [58, 62]
assignee: "@amirhossein"
tags: [pb, l6, S5, S10]
---

# Streamlit: Pareto front explorer

**Phase B — Multi-objective EA** · **L6 Delivery** · Estimate: 2 d

> **Owns (hidden behind this module):** How the trade-off is explored interactively.

## Why this exists

The front is a trade-off surface, so a static plot under-serves it. A collaborator should
be able to move a cost ceiling and watch which candidates survive.

Extends the existing app (58) rather than starting a second one.

## Done when

- [ ] Interactive Pareto scatter over capacity, cost and novelty with candidate selection
- [ ] Subset selector; hypervolume and seed-stability shown per subset
- [ ] Selecting a point opens the same candidate detail view as the screening page
- [ ] Convergence and stability plots embedded, not linked out

## Runnable check

```bash
streamlit run app/main.py
```

## Traces to

`docs/PRD-inverse-design.md` — S5, S10

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
