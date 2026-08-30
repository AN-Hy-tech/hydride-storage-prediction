---
id: 39
status: backlog
priority: Normal
blocked_by: [34]
assignee: "@amirhossein"
tags: [pt, l3, S11]
---

# Parameterise surrogate training by target

**Phase T — Thermodynamics** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** That the training code is about *a* target, not about capacity specifically.

## Why this exists

The capacity model and the thermodynamics models differ only in which column they predict.
Encoding that as a config key rather than a second copy of the training script is what makes
user story S11 true: a future student swaps the target without rewriting the pipeline.

**Deletion test:** if this refactor does not remove a would-be duplicate training script, it
is not pulling its weight.

## Done when

- [ ] Target column, transform and loss come from config, not from literals
- [ ] The capacity model retrains through the parameterised path with identical results to v1
- [ ] Adding a new target requires a config block and no new training code
- [ ] No duplicated training script exists for thermodynamics

## Runnable check

```bash
python -m hydms.surrogate.train --target capacity --verify-against v1
```

## Traces to

`docs/PRD-inverse-design.md` — S11

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
