---
id: 77
status: backlog
priority: High
blocked_by: [76]
assignee: "@amirhossein"
tags: [ph, l6, HG-2, R1]
---

# GATE HG-2: the refusal path — never a bare number

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** What the system does when it does not know — and the guarantee that it never answers as though it did.

## Why this exists

This is the card the whole phase exists for. A model that returns 2.1 wt% for a
composition it has never seen anything like is not merely inaccurate — it is *confidently* inaccurate,
and a user has no way to tell that apart from a good prediction.

Tree ensembles extrapolate as constants, which is risk R1 in the PRD: outside the training hull the
model produces a plausible flat number rather than an obvious failure. The interval and the domain
verdict are what make that visible, and a refusal is what makes it unmissable.

A refusal must carry a **reason**. "Cannot predict" sends the user away; "contains Tc, which appears in
no training alloy" tells them what to do next.

## Done when

- [ ] Unparseable formula → refusal, with the parse failure named
- [ ] Element absent from the training set → refusal, naming the element
- [ ] Temperature outside the trained range (195-773 K) → refusal, naming the range
- [ ] Outside the applicability-domain ceiling (#48) → refusal, reporting the distance and the ceiling
- [ ] Every refusal carries a machine-readable code **and** a human-readable reason
- [ ] **No path through `predict_capacity()` can return a point estimate without an interval and a
      domain verdict** — asserted exhaustively, not sampled
- [ ] Registered in the gate harness as HG-2
- [ ] **The unparseable-formula and unknown-element refusals carry `INDETERMINATE` (from #75).**
      Neither is a threshold any screen declares a code for, and the delivery vocabulary is derived
      from the screens rather than written down — so there is no `unparseable-formula` code to reach
      for, and inventing one here is precisely the second source of truth #75 exists to prevent.
      `INDETERMINATE` is the declared code for "this rule could not be evaluated on this candidate",
      it is a **rejection**, and #48's screen already emits it for a formula it cannot give a
      physical ceiling to. The distinguishing detail goes in the human-readable `explanation`. This
      gate must assert both refusals are reachable and that neither returns a number

- [ ] **A non-finite temperature raises instead of refusing, and that leaves one declared sentence
      unreachable** (added 2026-09-07 by #90). `PredictionRequest.__post_init__` runs `temperature_k`
      through `_finite()`, so `float('nan')` is a `ContractError` and can never become a `Refusal`.
      `hydms.screens.window.Window` nonetheless declares `INDETERMINATE` for "there was no number to
      compare" and writes a sentence for it — a sentence no caller can reach and no diff can show
      (`docs/REFUSALS.md`, § "One sentence this page cannot show"). Decide it rather than inherit it:
      either a malformed request is a caller error and raising is right, in which case say so where
      the window declares the code; or a caller who omitted a temperature deserves a refusal like any
      other, in which case this gate owns making it one. An unreachable branch that writes prose is
      exactly where a stale sentence hides

- [ ] **`untrusted-family` is declared, published and unreachable through `predict_capacity()`**
      (added 2026-09-11 by #76). The applicability screen judges it from an alloy-class label and
      the leave-one-class-out transfer measured for that family (#30). A user types a formula and a
      temperature; there is no label, and nothing in the package maps a novel composition to a
      family. Supplying the column with an unknown value is **worse** than omitting it — the screen
      answers `indeterminate` for a class it has no transfer estimate for, so every novel candidate,
      which is the entire point of the exercise, would be refused for the wrong reason. So #76
      omits it, and `docs/REFUSALS.md` documents a code the delivery path cannot produce. This gate
      owns saying which codes are reachable **through which entry point**: reachable from the batch
      CSV path (#84) and from screening a curated frame, not from a single prediction. A bare
      "every code is reachable" assertion here would be false or would have to quietly widen what
      "reachable" means

- [ ] **The null-check obligation is discharged by measurement, and this gate inherits the pin**
      (added 2026-09-11 by #76). Every object null is refused at three independent guards and every
      stringified null but one is refused by the grammar;
      `test_every_spelling_of_a_missing_value_is_refused_except_the_one_that_is_chemistry` pins it.
      **`"NaN"` is sodium and nitrogen to both parsers and must keep being answered** — if this gate
      adds a null blocklist, it refuses a real material. #84 owns the boundary where a missing value
      becomes text

## Runnable check

```bash
conda run -n Project python -m hydms.gates run HG-2
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6, HG-2; `docs/PRD-inverse-design.md` — S2, R1

## Narrative

- 2026-09-02: Created for Phase H. The distinction that matters to a user, and that the API
  documentation (#80) must answer: how do you tell a refusal from a genuinely low prediction? (by @assistant)
