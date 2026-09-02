---
id: 83
status: backlog
priority: High
blocked_by: [29, 30, 82]
assignee: "@amirhossein"
tags: [ph, l6, S6, R4]
---

# Model-card page: honest metrics and stated limits

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** What the model is, how well it actually does, and the three ways a reader is most likely to overstate it.

## Why this exists

The interface is where a reader will form a belief about how good this model is. If the
only numbers on offer are the random-split ones, they will form the optimistic belief — the same one
`REPORT.md` published and the artifacts in this repository contradict.

This page is the counterweight, and it must survive contact with a reader who does not want to read it.
Three overstatements to pre-empt: the random-split number as *the* number, a material wt% compared to a
DOE system target, and the published figures inherited as though nothing had changed.

## Done when

- [ ] Random-split metrics and **leave-one-alloy-class-out** metrics shown together, at the same scale
- [ ] Bootstrap confidence intervals shown, not just point metrics
- [ ] The training data described: rows, unique canonical compositions, alloy families, element coverage,
      temperature range
- [ ] The applicability domain stated in terms a reader can apply to their own candidate
- [ ] **The material-versus-system caveat** — comparing a material wt% to a DOE onboard-storage target is
      a two-step overstatement
- [ ] A link to `docs/REPORT-RECONCILIATION.md`, so the previously published figures are not silently inherited
- [ ] The known limits stated plainly, including no pressure data and therefore no reversible-versus-maximum
      capacity distinction
- [ ] The artifact version and training date

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_model_card.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S6, R4

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
