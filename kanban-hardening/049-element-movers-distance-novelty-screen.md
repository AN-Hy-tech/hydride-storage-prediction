---
id: 49
status: backlog
priority: High
blocked_by: [44]
assignee: "@amirhossein"
tags: [pa, l4, S4, AC-7]
---

# Element Mover's Distance novelty screen

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** How chemically far a candidate is from everything already known.

## Why this exists

PRD 4.3 link 5: 'novel' must be a number, not an assertion. ElMD gives chemically
intuitive composition-to-composition distances along a modified Pettifor scale.

ElMD is **GPL-3.0**, which is compatible with the decided GPL-3.0 licence for this project —
recorded here so the choice is not revisited by mistake.

## Done when

- [ ] ElMD distance computed from each candidate to its nearest training composition
- [ ] Nearest neighbour's formula reported alongside the distance, so novelty is inspectable
- [ ] Distances computed batched; a per-candidate loop over the training set would be too slow
- [ ] GPL-3.0 dependency noted in `pyproject.toml` and in ADR 2

## Runnable check

```bash
python -m pytest tests/screens/test_novelty.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S4, AC-7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
