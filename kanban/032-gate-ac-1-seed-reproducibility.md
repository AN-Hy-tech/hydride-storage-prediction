---
id: 32
status: backlog
priority: High
blocked_by: [5, 26]
assignee: "@amirhossein"
tags: [p1, l3, AC-1]
---

# GATE AC-1: seed reproducibility

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** That the same seed produces the same numbers.

## Why this exists

PRD acceptance criterion 1. Without this the whole reproducibility claim is unverified,
and the artifact manifest's recorded seeds are decorative.

## Done when

- [ ] Pipeline run twice with the same seed produces identical metrics
- [ ] Comparison is on the metrics table, not on model file bytes (which may differ)
- [ ] Any nondeterministic step is identified and either seeded or documented as unavoidable
- [ ] Registered as `AC-1` and run by the CI slow lane

## Runnable check

```bash
python -m hydms.gates run AC-1
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
