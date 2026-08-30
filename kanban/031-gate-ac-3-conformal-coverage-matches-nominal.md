---
id: 31
status: backlog
priority: High
blocked_by: [5, 27]
assignee: "@amirhossein"
tags: [p1, l3, AC-3, R1]
---

# GATE AC-3: conformal coverage matches nominal

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Whether the intervals mean what they claim.

## Why this exists

If coverage is badly off, the LCB ranking signal is meaningless and every candidate list
downstream is untrustworthy. This gate is the reason Architecture A's ranking can be
believed at all — it is the load-bearing check for risk R1.

## Done when

- [ ] Empirical coverage measured on the held-out test set
- [ ] Gate passes when coverage is within the configured tolerance of nominal
- [ ] Failure reports measured vs nominal coverage, not just a boolean
- [ ] Registered as `AC-3` and run by CI

## Runnable check

```bash
python -m hydms.gates run AC-3
```

## Traces to

`docs/PRD-inverse-design.md` — AC-3, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
