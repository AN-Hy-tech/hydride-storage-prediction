---
id: 45
status: backlog
priority: High
blocked_by: [44]
assignee: "@amirhossein"
tags: [pa, l4, S3, R5]
---

# Family stoichiometry screen (AB2, AB5)

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** What makes a composition a member of an alloy family.

## Why this exists

Memo 5.1 calls family stoichiometry **the highest-value single filter**: it collapses the
search space and guarantees candidates look like real hydride chemistry, rather than
arbitrary points on the simplex.

It is also the primary mitigation for risk R5 (combinatorial blow-up) — enforcing A:B ratios
is what keeps enumeration tractable.

## Done when

- [ ] AB2 and AB5 A:B ratio constraints implemented with a configurable tolerance
- [ ] A-site and B-site element sets declared in config, drawn from training-data membership
- [ ] Minimum non-zero fraction (0.01) enforced so no trace elements are emitted
- [ ] Maximum distinct element count enforced per family

## Runnable check

```bash
python -m pytest tests/screens/test_stoichiometry.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S3, R5

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
