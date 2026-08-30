---
id: 61
status: backlog
priority: High
blocked_by: [60]
assignee: "@amirhossein"
tags: [pb, l5, S5]
---

# Element-subset outer loop

**Phase B — Multi-objective EA** · **L5 Search** · Estimate: 1 d

> **Owns (hidden behind this module):** How multiple chemistries are explored without mixed-integer encoding.

## Why this exists

The simplification that makes B tractable: fix the element subset per run, sweep subsets
in an outer loop.

It also makes every result interpretable — each front reads as 'the best achievable in
Ti-Cr-Mn-V' rather than an unreadable mixture of chemistries.

## Done when

- [ ] Outer loop enumerates chemically motivated subsets from the family's training membership
- [ ] One Pareto front produced per subset, stored separately and comparably
- [ ] Runs are independently resumable; a crash does not lose completed subsets
- [ ] A combined view ranks subsets by hypervolume so the best chemistries are identifiable

## Runnable check

```bash
python -m hydms.search.sweep --family AB2 --artifact current
```

## Traces to

`docs/PRD-inverse-design.md` — S5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
