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

## Runnable check

```bash
conda run -n Project python -m hydms.gates run HG-2
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6, HG-2; `docs/PRD-inverse-design.md` — S2, R1

## Narrative

- 2026-09-02: Created for Phase H. The distinction that matters to a user, and that the API
  documentation (#80) must answer: how do you tell a refusal from a genuinely low prediction? (by @assistant)
