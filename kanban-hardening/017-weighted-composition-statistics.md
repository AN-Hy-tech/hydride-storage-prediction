---
id: 17
status: backlog
priority: High
blocked_by: [16]
assignee: "@amirhossein"
tags: [p1, l2, S12]
---

# Weighted composition statistics

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** How a per-element property becomes a per-composition number.

## Why this exists

The `avg_` / `dev_` / `range_` / `max_` / `min_` statistics over a fraction vector. This
is the whole of what CBFV does mathematically; the rest is table lookup.

Keep this module pure and total: fractions in, scalar out, no I/O.

## Done when

- [ ] `avg`, `dev`, `range`, `max`, `min` implemented over (fractions, property vector)
- [ ] Property tests: statistics are invariant to element ordering and to fraction rescaling
- [ ] `dev` matches CBFV's definition exactly (fraction-weighted mean absolute deviation) — confirmed against ticket 8's spike output
- [ ] Vectorised over a batch of compositions, not looped per composition

## Runnable check

```bash
python -m pytest tests/descriptors/test_stats.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S12

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
