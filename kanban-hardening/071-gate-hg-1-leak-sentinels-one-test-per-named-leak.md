---
id: 71
status: backlog
priority: High
blocked_by: [5, 69]
assignee: "@amirhossein"
tags: [ph, l0, HG-1, R4]
---

# GATE HG-1: leak sentinels, one test per named leak

**Stage S1 — QA foundation** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** The guarantee that a leak this phase removed stays removed.

## Why this exists

Thirteen leaks are catalogued in `docs/PHASE-H-RUNBOOK.md` §1. Removing them is stages S2
to S4. **Keeping them removed is this card**, and it is what makes the phase durable rather than a
one-time cleanup: without it, nothing stops a later session reintroducing the exact defect the phase
just spent forty days eliminating.

Each sentinel must pass **only because the leak is absent**. A test that would still pass with the leak
present is not a sentinel — it is decoration. Write each one so that deliberately reintroducing the
defect turns it red, and prove that by doing so once during development.

## Done when

- [ ] **L1, L5** — the CatBoost `eval_set` identity is asserted to be the *validation* split;
      `use_best_model=True` with an empty or test eval set must raise
- [ ] **L2, L4** — the model-selection record contains no test-split metric, and the reported score
      comes from folds disjoint from the tuning folds
- [ ] **L3** — `y` for val and test is byte-identical before and after the CleanLab stage
- [ ] **L6** — re-running selection with test rows perturbed produces an identical feature set
- [ ] **L7, L8** — no canonical composition appears in two splits, and none in two CV folds
- [ ] **L9** — a deliberately shuffled input frame makes the merge fail, not pass silently
- [ ] Each sentinel has been shown to go **red** when its leak is reintroduced
- [ ] Registered in the gate harness as HG-1

## Runnable check

```bash
conda run -n Project python -m pytest tests/leaks -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1, HG-1; `docs/PRD-inverse-design.md` — R4

## Narrative

- 2026-09-02: Created for Phase H. The PRD names three leaks; the audit found thirteen. L3
  (CleanLab overwriting held-out labels) and L9 (positional concat) are the two that were not in the
  PRD and are the most severe (by @assistant)
