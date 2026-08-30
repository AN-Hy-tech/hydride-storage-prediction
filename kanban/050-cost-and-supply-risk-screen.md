---
id: 50
status: backlog
priority: Normal
blocked_by: [44]
assignee: "@amirhossein"
tags: [pa, l4, S9]
---

# Cost and supply-risk screen

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** What a candidate costs and how exposed its supply is.

## Why this exists

Cost is deterministic from composition, so it costs nothing to compute and immediately
makes the Pareto front more interesting than 'maximise wt%'.

Source: Theler, Kauwe & Sparks 2020, which gives elemental prices 1998-2015 **and** the
Herfindahl-Hirschman Index per element per year. HHI is the standard criticality metric and
gives a second screen — supply concentration — for free.

## Done when

- [ ] Price and HHI tables vendored with citation under `hydms/screens/data/`
- [ ] Cost per kg computed from the composition's mass fractions
- [ ] HHI aggregated to a composition-level supply-risk figure with the method documented
- [ ] Elements absent from the price table are flagged, never assigned a default price

## Runnable check

```bash
python -m pytest tests/screens/test_cost.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S9

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
