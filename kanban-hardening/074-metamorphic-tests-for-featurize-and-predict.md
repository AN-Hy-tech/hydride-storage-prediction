---
id: 74
status: backlog
priority: Normal
blocked_by: [20, 28, 69]
assignee: "@amirhossein"
tags: [ph, l0]
---

# Metamorphic tests for featurize() and predict()

**Stage S1 — QA foundation** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The invariants that must hold between two related inputs, where no ground truth exists to assert against.

## Why this exists

Most of the featuriser and surrogate have no oracle: there is no independent source of
truth for what `avg_polzbl_divi_atom_mass` should be for an arbitrary alloy. Metamorphic tests get
around that by asserting relationships between inputs rather than absolute values.

They also catch the class of bug that AC-4 exists for — column reordering, scaler refits, silent
coercion — at a point far earlier than a round-trip gate, and on inputs the training set never contained.

## Done when

- [ ] **Permutation invariance** — `Mg12Ce1` and `Ce1Mg12` featurise identically, and predict identically
- [ ] **Scale invariance** — `Mg1Al1` and `Mg0.5Al0.5` featurise identically
- [ ] **Whitespace and case** — a trailing space or a case change in a formula string changes nothing
- [ ] **Temperature monotonicity** — where the trained model is monotone in temperature, the prediction
      is too; where it is not, the test records the actual behaviour rather than asserting a wish
- [ ] **Column-order independence** — feeding features in a shuffled column order either produces the
      same prediction or raises, never a silently different number
- [ ] Each test states which failure it is designed to catch

## Runnable check

```bash
conda run -n Project python -m pytest tests/test_metamorphic.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1

## Narrative

- 2026-09-02: Created for Phase H. The permutation and scale cases are drawn from real
  cross-split collisions found in the data: `Ce1Mg12`/`Mg12Ce1` and `Mg1Al1`/`Mg0.5Al0.5` (by @assistant)
