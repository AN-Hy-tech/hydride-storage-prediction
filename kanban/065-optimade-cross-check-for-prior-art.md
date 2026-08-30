---
id: 65
status: backlog
priority: Normal
blocked_by: [49]
assignee: "@amirhossein"
tags: [pb, l4, S4, R7]
---

# OPTIMADE cross-check for prior art

**Phase B — Multi-objective EA** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** Whether a proposed candidate is already known to the wider literature.

## Why this exists

PRD 4.3 link 5. Lu et al. reported '27 unreported alloy compositions' — a claim that is
only meaningful because they checked.

OPTIMADE queries AFLOW, COD, Materials Cloud, Materials Project, NOMAD, odbx and OQMD
through one interface, so this is one client rather than four.

## Done when

- [ ] OPTIMADE query per Pareto-optimal candidate, results cached to avoid repeat calls
- [ ] Hits reported as confirmatory evidence, never as an automatic rejection — these are DFT databases of *ordered* compounds and disordered solid solutions often have no entry
- [ ] Network failures degrade to `UNKNOWN`, never to `NOVEL`
- [ ] Results joined into the candidate output alongside the ElMD distance

## Runnable check

```bash
python -m hydms.screens.optimade --check reports/pareto/AB2.csv
```

## Traces to

`docs/PRD-inverse-design.md` — S4, R7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
