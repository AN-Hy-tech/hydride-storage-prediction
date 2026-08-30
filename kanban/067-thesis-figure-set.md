---
id: 67
status: backlog
priority: Normal
blocked_by: [62, 63]
assignee: "@amirhossein"
tags: [pb, l6, S7]
---

# Thesis figure set

**Phase B — Multi-objective EA** · **L6 Delivery** · Estimate: 2 d

> **Owns (hidden behind this module):** The figures that carry the argument in the written thesis.

## Why this exists

One script, regenerated from published artifacts, so figures never drift from the numbers
they illustrate. Every figure traces to a report file produced by the pipeline.

## Done when

- [ ] Figure script regenerates every thesis figure from artifacts, with no manual steps
- [ ] Covers: corrected-vs-published metrics, LOCO per class, coverage calibration, Pareto fronts, hypervolume convergence, seed stability, novelty-vs-capacity
- [ ] Consistent styling, colourblind-safe palette, readable at print size
- [ ] Each figure's caption names the artifact version and report file it came from

## Runnable check

```bash
python -m hydms.figures build --artifact current
```

## Traces to

`docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
