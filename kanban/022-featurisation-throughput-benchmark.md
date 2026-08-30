---
id: 22
status: backlog
priority: High
blocked_by: [20]
assignee: "@amirhossein"
tags: [p1, l2, R6]
---

# Featurisation throughput benchmark

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 0.5 d

> **Owns (hidden behind this module):** How many candidates per second the system can evaluate.

## Why this exists

Risk R6: NSGA-II makes far more surrogate calls than enumeration. Memo section 7 says to
measure this on day one because **it decides whether enumeration or evolution is the right
paradigm**, and it bounds how large Architecture A's grid can be.

Not a nice-to-have measurement — an input to the design of tickets 53 and 59.

## Done when

- [ ] Throughput measured for batch sizes 1, 100, 10k, 100k formulae
- [ ] Result recorded in `docs/BENCHMARKS.md` with the machine spec
- [ ] A candidate-budget estimate for Architecture A written from it
- [ ] If throughput is under ~1k/s at batch 10k, a note is filed against ticket 59 on feasibility

## Runnable check

```bash
python -m hydms.descriptors.benchmark --sizes 1,100,10000,100000
```

## Traces to

`docs/PRD-inverse-design.md` — R6

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
