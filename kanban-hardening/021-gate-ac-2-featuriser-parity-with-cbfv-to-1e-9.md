---
id: 21
status: backlog
priority: High
blocked_by: [5, 20]
assignee: "@amirhossein"
tags: [p1, l2, AC-2, R3]
---

# GATE AC-2: featuriser parity with CBFV to 1e-9

**Phase 1 — Hardening Chapter 1** · **L2 Descriptors** · Estimate: 1 d

> **Owns (hidden behind this module):** Proof that the reimplementation is faithful.

## Why this exists

This is the gate that makes the CBFV replacement trustworthy. If the reimplemented
featuriser does not reproduce CBFV's numbers on the training set, every downstream model
would be trained on subtly different features than `REPORT.md` describes.

**If this fails, the reimplementation is wrong — not CBFV.**

## Done when

- [ ] All 1279 training formulae featurised by both CBFV (in the `Project` env) and `hydms.descriptors`
- [ ] Every one of the 22 columns agrees to within 1e-9 absolute
- [ ] Failure output names the column and the worst-offending formula, not just a boolean
- [ ] Registered in the gate harness as `AC-2` and run by CI

- [ ] **Parity cannot be a claim about the numbers, only about this code (from #16).** The
      published Oliynyk table is a *revised* edition of the one CBFV ships: of the thirteen
      properties the selected features need, five agree exactly and eight do not -- up to 10 in
      `valence_d` (Ga, Ge), 2.0 in `gilman_no_of_valence_electrons` (Lu), 0.54 in
      `covalent_radius` (Th, U). Comparing our featuriser's output against CBFV's while the
      tables differ measures the tables, not the code. This gate must read: **the featuriser
      reproduces CBFV to 1e-9 given the same table**, with
      `tests/descriptors/data/cbfv_oliynyk_reference.csv` supplied as that table. It is test
      input for this gate and must never become package data -- CBFV carries no licence, which
      is the whole reason the descriptor layer exists

- [ ] **No europium-containing formula may be compared at all.** CBFV drops Eu from its JARVIS
      index and answers anyway, substituting an all-zero property vector; `element_data.py`
      raises. A refusal and a number are not comparable, so `Eu1Ni5` must be excluded from the
      parity set **explicitly and with the reason recorded**, not filtered out quietly

## Runnable check

```bash
python -m hydms.gates run AC-2
```

## Traces to

`docs/PRD-inverse-design.md` — AC-2, R3

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
