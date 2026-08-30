---
id: 53
status: backlog
priority: High
blocked_by: [22, 52]
assignee: "@amirhossein"
tags: [pa, l5, S3, R5]
---

# Enumerate proposer: stoichiometry grid over the simplex

**Phase A — Screen-and-Rank** · **L5 Search** · Estimate: 1 d

> **Owns (hidden behind this module):** How the candidate grid is laid out.

## Why this exists

Fraction grid 0.05, temperature grid 273-473 K in 25 K steps, element sets drawn from AB2
and AB5 membership in the training data.

Risk R5 is combinatorial blow-up: 54 elements taken 4 at a time is billions. Mitigation is
one family per run, 3-5 chemically motivated elements, coarse grid first. The candidate
budget comes from ticket 22's measured throughput, not from a guess.

**If the enumeration is still too large, that is the signal to move to Architecture B** —
not a defect.

## Done when

- [ ] Grid generated lazily as batches, never materialised whole in memory
- [ ] Candidate count estimated and reported *before* generation begins
- [ ] Exceeding the configured budget aborts with the count and a suggestion to narrow the spec
- [ ] Every candidate round-trips: formula string -> Composition -> fractions -> formula string

## Runnable check

```bash
python -m hydms.search.run --proposer enumerate --family AB2 --dry-run
```

## Traces to

`docs/PRD-inverse-design.md` — S3, R5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
