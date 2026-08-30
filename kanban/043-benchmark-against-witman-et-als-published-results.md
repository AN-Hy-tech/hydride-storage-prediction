---
id: 43
status: backlog
priority: Normal
blocked_by: [40]
assignee: "@amirhossein"
tags: [pt, l3, S7]
---

# Benchmark against Witman et al.'s published results

**Phase T — Thermodynamics** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** How our thermodynamic model compares to the published state of the art.

## Why this exists

Turning the licence problem into a strength: rather than importing their pickles, compare
against their **published** numbers. That is a stronger thesis position and it sidesteps the
all-rights-reserved issue entirely.

Note the data-version difference (their v0.0.4, our v0.0.5) and the featuriser difference in
the write-up — this is a comparison, not a replication.

## Done when

- [ ] Our ΔH and ΔS metrics tabulated against Witman et al.'s reported values
- [ ] Differences in data version, featurisation and split protocol stated explicitly
- [ ] Written into `reports/` in a form the thesis can lift directly
- [ ] No import from, or redistribution of, the HEAhydrideMLv2 repository

## Runnable check

```bash
python -m hydms.surrogate.evaluate --target dH --benchmark witman2020
```

## Traces to

`docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
