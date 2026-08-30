---
id: 41
status: backlog
priority: High
blocked_by: [5, 40]
assignee: "@amirhossein"
tags: [pt, l3, AC-5]
---

# GATE AC-5: predicted entropy clusters near -130 J/(mol H2 K)

**Phase T — Thermodynamics** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** A physics sanity check on the entropy model.

## Why this exists

ΔS for metal-hydrogen systems is dominated by the loss of gas-phase H2 entropy and sits
near -130 J/(mol H2 K) across systems. A model that does not reproduce that is broken,
regardless of its R2.

This is the cheapest physics check in the project and it catches target-column and
sign-convention errors that metrics alone would not.

## Done when

- [ ] Predicted ΔS distribution summarised (median, IQR) over the test split
- [ ] Gate passes when the central tendency falls inside the configured window around -130
- [ ] Failure reports the observed distribution, not just a boolean
- [ ] Registered as `AC-5` and run by CI

## Runnable check

```bash
python -m hydms.gates run AC-5
```

## Traces to

`docs/PRD-inverse-design.md` — AC-5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
