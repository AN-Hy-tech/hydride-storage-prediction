---
id: 81
status: backlog
priority: Normal
blocked_by: [29, 30, 76]
assignee: "@amirhossein"
tags: [ph, l6, S2, S10]
---

# App chart vocabulary: charts that resist false belief

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** How uncertainty and applicability are drawn, so that every page in the app says the same thing the same way.

## Why this exists

A number rendered large and alone reads as certain, whatever the caveat beside it. The
charts are not decoration on the prediction — they are most of how the interval and the domain verdict
actually reach the user.

Five charts, each chosen because it makes a specific false belief harder to hold. They are built once,
here, so the prediction page and the model card cannot drift into drawing the same quantity two
different ways.

## Done when

- [ ] **Prediction band** — the estimate drawn inside its conformal interval, with the width stated
      numerically. A wide interval must *look* wide; the axis may not rescale to hide it
- [ ] **Domain strip** — where this composition sits against the training distribution and the AD ceiling
- [ ] **Temperature sweep** — predicted wt% across the valid range with the interval as a band. Only 39
      test rows sit above 500 K; the chart must not conceal that thinning
- [ ] **Nearest neighbours** — the k closest training alloys by ElMD, with their *measured* capacities
- [ ] **Parity plot** — predicted versus measured on the held-out test set, with the leave-one-alloy-class-out
      version beside it at the same scale
- [ ] All five read correctly in both light and dark, and are colour-blind safe
- [ ] Every axis carries units; no chart shows a point estimate without its interval

## Runnable check

```bash
conda run -n Project python -m pytest tests/test_figures.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S2, S10

## Narrative

- 2026-09-02: Created for Phase H. The parity plot showing random-split and LOACO at the same
  scale is the one that matters most: it puts the optimistic number and the honest number on one page (by @assistant)
