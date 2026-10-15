---
id: 74
status: done
priority: Normal
blocked_by: [20, 28, 69]
assignee: "@amirhossein"
tags: [ph, l0]
---

# Metamorphic tests for featurize() and predict()

**No stage — slots in where its blockers allow** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The invariants that must hold between two related inputs, where no ground truth exists to assert against.

## Why this exists

Most of the featuriser and surrogate have no oracle: there is no independent source of
truth for what `avg_polzbl_divi_atom_mass` should be for an arbitrary alloy. Metamorphic tests get
around that by asserting relationships between inputs rather than absolute values.

They also catch the class of bug that AC-4 exists for — column reordering, scaler refits, silent
coercion — at a point far earlier than a round-trip gate, and on inputs the training set never contained.

## Done when

- [x] **Permutation invariance** — asserted on all six `known_collisions` pairs, and on both sides of
      the pipe: identical features *and* identical intervals. The second is not implied by the first
      — it is what catches a prediction path that keys, caches or dispatches on the raw string
- [x] **Scale invariance** — `Mg1Al1` / `Mg0.5Al0.5` bit-identical. Generalised, and the
      generalisation is **not** bit-identical; see the narrative
- [x] **Whitespace** — five spellings of `Pr1Co5` (trailing, leading, internal space, tab) featurise
      and predict identically
- [x] **Case — measured, and the card's box is wrong.** `lani5`, `LANI5` and `laNi5` *raise*, and
      that is correct rather than a gap; see the narrative. The test asserts the refusal and that it
      names the offending row
- [x] **Temperature — recorded, not wished for.** The response moves, rises net across the trained
      range, and is **not monotone**: 5 of 39 steps fall on a fixture whose target is monotone in T
      by construction. Nothing asks CatBoost for a monotone fit
- [x] **Column-order independence — measured: the same number.** `QuantileModel._batch` selects the
      fitted names out of the frame, so a shuffled order, an extra column and a dropped column give
      the same prediction, the same prediction, and a `ModelError` respectively
- [x] Each test states which failure it is designed to catch, in its own docstring, as a
      `Catches: ...` line

## Runnable check

```bash
conda run -n Project python -m pytest tests/test_metamorphic.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1

## Narrative

- 2026-09-02: Created for Phase H. The permutation and scale cases are drawn from real
  cross-split collisions found in the data: `Ce1Mg12`/`Mg12Ce1` and `Mg1Al1`/`Mg0.5Al0.5` (by @assistant)

- 2026-09-07: **Closed. Two of the six boxes said something the measurement contradicted.**

  **Case is a refusal, and the box that asked for invariance was asking for a defect.** Element
  symbols are case-sensitive *by definition*: `Co` is cobalt and `CO` is carbon and oxygen. A
  case-folding parser would silently turn one material into another, so `parse_formula` raises —
  `'lani5' has an unexpected character 'l' at position 0`, `'LANI5' names 'L', which is not a
  chemical element` — and `featurize` refuses the whole batch rather than returning fewer rows. The
  test records that and asserts the message names the offending spelling. Pairing case with
  whitespace in one box is what made it look like one property; they are opposites.

  **Scale invariance is exact for integer rescalings and one ulp off otherwise.** `La3Ni15`,
  `La2Ni10` and `La0.5Ni2.5` are bit-identical to `La1Ni5`; `La0.2Ni1` differs by **2.776e-17** on a
  value near 0.1667, because `0.2 / 1.2` and `1 / 6` are different binary numbers. So the assertion
  is invariance to within this project's 1e-12, and there is a *separate* exact assertion one layer
  down — that the one-ulp pair still predicts identically, which is a claim about the booster's
  thresholds rather than about IEEE-754 division. Asserting equality on the featuriser would have
  been asserting a property of division.

  **Temperature is not monotone, and that is the recorded behaviour.** The fixture's target rises
  with T by construction and carries only Gaussian noise, and five of thirty-nine steps still fall.
  `monotone_constraints` exists in CatBoost and this project does not set it. The count is
  deliberately not asserted — one fit at one budget — but the *existence* of reversals is, so a
  future run that is monotone is a finding somebody looks at rather than a silent change.

  **One test catches nothing and is the most valuable in the file.** The response is piecewise
  constant and **flat outside the fitted range** — past the largest threshold it learned, every
  input reaches the same leaf. That is risk R1 itself, and it is the measurement the whole
  interval-and-verdict argument rests on. Asserting it means the day it stops being true, the
  justification written all over this repository stops being true with it.

  14 tests, 1.9 s including a real CatBoost fit persisted through the artifact store and read back
  — **not** marked `slow`, because a metamorphic test the fast lane deselects catches a reordered
  column nowhere. ruff and mypy clean. (by @assistant)
