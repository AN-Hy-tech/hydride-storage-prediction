---
id: 35
status: backlog
priority: High
blocked_by: [20, 28]
assignee: "@amirhossein"
tags: [p1, l7, S7]
---

# CONTEXT.md domain glossary

**Phase 1 — Hardening Chapter 1** · **L7 Evidence** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The project's vocabulary, pinned so that easily-conflated terms stay distinct.

## Why this exists

Glossary only — no implementation detail. Terms that must be pinned because conflating
them causes real errors:

- **Candidate** vs **Composition** vs **Formula**
- **Capacity** — always *maximum material* gravimetric wt%; never usable, never system-level
- **Surrogate** (inside the optimiser) vs **production model** (reported in `REPORT.md`)
- **Novelty** (ElMD distance) vs **uncertainty** (interval width) vs **applicability domain** (in/out of scope)
- **LCB** — the ranking signal; never the mean
- **Alloy family** and **family stoichiometry**

## Done when

- [ ] `CONTEXT.md` at repo root, glossary only
- [ ] Each term has a one-line definition and, where useful, an explicit contrast with what it is *not*
- [ ] The capacity definition states the material/system and maximum/usable distinctions
- [ ] No implementation detail, no decisions, no spec content

## Runnable check

```bash
test -f CONTEXT.md && grep -c '^### ' CONTEXT.md
```

## Traces to

`docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
