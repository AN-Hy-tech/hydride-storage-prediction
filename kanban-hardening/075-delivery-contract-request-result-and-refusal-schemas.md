---
id: 75
status: backlog
priority: High
blocked_by: [28]
assignee: "@amirhossein"
tags: [ph, l6, S2]
---

# The delivery contract: request, result and refusal schemas

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The vocabulary every consumer of a prediction speaks — the app, the API, the batch path and the tests.

## Why this exists

Three consumers are about to be built on top of one prediction path. If each invents its
own shape for a result, the honest-interval guarantee becomes three guarantees that drift apart, and
HG-2 has nothing single to check.

The contract is defined before the callers exist, so that a result **cannot be constructed without**
its interval and its domain verdict. That is the structural half of HG-2: not a rule about what
callers should include, but a type that cannot represent a bare number.

## Done when

- [ ] `hydms/delivery/contract.py` defines the request, the result and the refusal
- [ ] A result carries: point estimate, interval, nominal level, domain verdict **with a reason**,
      ElMD distance to the nearest known alloy, model version, `refused`
- [ ] The result type **cannot be constructed** without an interval and a domain verdict
- [ ] A refusal carries a machine-readable reason code and a human-readable explanation
- [ ] Units and the target space (wt%, back-transformed from log1p) are explicit in the type, not
      implied by a field name
- [ ] Serialisable to JSON without loss, round-trip tested
- [ ] **The refusal codes are enumerated from the screens, never hand-written here.** Every screen
      declares `reasons` (#44) and `apply_screens` refuses a code outside that vocabulary, so the
      schema's code set is `ADMITTED` plus the union of the configured screens' `reasons` plus the
      shared `INDETERMINATE`. A literal list in this module is a second source of truth and will
      drift from the screens that actually emit them — which is exactly what `docs/QA-PROTOCOL.md`
      means by "every refusal reason code is reachable and asserted".

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_contract.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6, HG-2; `docs/PRD-inverse-design.md` — S2

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)

- 2026-09-04: #44 landed the screen contract. The reason vocabulary is declared per screen and
  enforced by the runner, so this card can derive its code set instead of restating it. (by @assistant)
