---
id: 63
status: backlog
priority: High
blocked_by: [61]
assignee: "@amirhossein"
tags: [pb, l5, S5]
---

# Multi-seed stability study

**Phase B — Multi-objective EA** · **L5 Search** · Estimate: 1 d

> **Owns (hidden behind this module):** Whether the front is a property of the problem or of the random seed.

## Why this exists

Evolutionary algorithms are stochastic. Repeated runs with different seeds showing similar
fronts is what distinguishes a result from an artefact — and it is the question an examiner
will ask.

## Done when

- [ ] Each subset run repeated across a configured set of seeds
- [ ] Front-to-front variation quantified, not merely plotted
- [ ] Candidates appearing across most seeds identified as robust and highlighted
- [ ] Instability, if found, is reported rather than resolved by picking the best seed

## Runnable check

```bash
python -m hydms.search.analyse --study seed-stability
```

## Traces to

`docs/PRD-inverse-design.md` — S5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
