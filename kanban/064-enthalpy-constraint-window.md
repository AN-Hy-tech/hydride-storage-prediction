---
id: 64
status: backlog
priority: Normal
blocked_by: [42, 60]
assignee: "@amirhossein"
tags: [pb, l5, S8]
---

# Enthalpy constraint window

**Phase B — Multi-objective EA** · **L5 Search** · Estimate: 1 d

> **Owns (hidden behind this module):** The operating-conditions requirement a candidate must satisfy.

## Why this exists

ΔH enters Architecture B as a **hard constraint window first**, not a fourth objective.
Four-objective fronts are hard to present and harder to defend; promote ΔH to an objective
only if the three-objective front turns out thin.

With ΔS near-constant, a predicted ΔH nearly suffices to place a candidate on a
temperature/pressure map, so this constraint is what makes a candidate *usable* rather than
merely high-capacity.

## Done when

- [ ] ΔH window expressed as target operating temperature and pressure, converted via van 't Hoff
- [ ] Wired as a pymoo constraint using the ΔH model's interval, not its point estimate
- [ ] Front reported with and without the constraint, so its cost in capacity is visible
- [ ] A note recorded on whether the front is thin enough to justify promoting ΔH to a fourth objective

## Runnable check

```bash
python -m pytest tests/search/test_dh_constraint.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S8

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
