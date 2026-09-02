---
id: 48
status: backlog
priority: High
blocked_by: [30, 44]
assignee: "@amirhossein"
tags: [pa, l4, S4, AC-8, R1]
---

# Applicability-domain ceiling

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** How far from known chemistry a prediction may be trusted.

## Why this exists

The Beltrame result means a candidate from an unfamiliar corner of composition space is
not merely uncertain — it is **out of scope**. Those are different things and the glossary
(35) keeps them distinct.

The ceiling is set from the leave-one-alloy-class-out result (30): the distance at which
measured cross-family performance degrades past what the thesis is willing to claim. It is
the primary structural mitigation for risk R1.

## Done when

- [ ] Ceiling derived from the LOCO result, not chosen arbitrarily; the derivation is documented
- [ ] Candidates beyond it are flagged `OUT_OF_DOMAIN`, distinct from `HIGH_UNCERTAINTY`
- [ ] Ceiling is a config value so risk-R1 iterations can tighten it and re-run
- [ ] Alloy-class assignability checked as a second, independent domain signal

## Runnable check

```bash
python -m pytest tests/screens/test_applicability.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S4, AC-8, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
