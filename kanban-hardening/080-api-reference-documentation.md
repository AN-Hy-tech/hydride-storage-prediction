---
id: 80
status: backlog
priority: Normal
blocked_by: [79]
assignee: "@amirhossein"
tags: [ph, l6, S10]
---

# API reference documentation

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What a caller needs to know to use a prediction correctly — including what the service will not tell them.

## Why this exists

An API reference that lists endpoints and field types is generated for free by OpenAPI.
What cannot be generated is the part that stops misuse: what the interval means, why the model refuses,
what the trained ranges are, and why comparing a material wt% to a DOE system target is an overstatement.

Written with the `grill-with-docs` skill. Its interview must answer one question before a word of the
document is written: **how does a caller tell a refusal from a genuinely low prediction?** If that
cannot be answered crisply, the contract is wrong and the document should not paper over it.

## Done when

- [ ] `docs/API.md` covers every endpoint with a real request and a real response
- [ ] It states what the interval is (conformal, at a named level) and what it is not
- [ ] It lists every refusal reason code and what a caller should do about each
- [ ] It states the trained ranges — temperature, elements, alloy families — and the applicability domain
- [ ] It carries the material-versus-system caveat for capacity comparisons
- [ ] It names the artifact version the examples were produced against
- [ ] The ADRs the interview produced are filed under `docs/adr/`

## Runnable check

```bash
python scripts/check_board.py --root .
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6; `docs/PRD-inverse-design.md` — S10, S7

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
