---
id: 75
status: done
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

- [x] `hydms/delivery/contract.py` defines the request, the result and the refusal — plus
      `Interval`, `ScreenVerdict`, `DomainVerdict`, `Novelty`, and `answer_from()`, the one door
      back from JSON that #79's transport-parity gate needs on both sides of the comparison
- [x] A result carries all seven. `refused` is a **property, not a field**, on both answer types:
      a field can be set to `False` on a refusal and a property cannot
- [x] The result type **cannot be constructed** without an interval and a domain verdict — no
      default on either field (a `TypeError`), and `None` refused in `__post_init__` (a
      `ContractError`). Both are asserted: they are different callers, and the second is the one a
      real prediction path hits when the screens did not run
- [x] A refusal carries a code and an explanation, and carries **no number at all** — no `capacity`
      field, no `interval` field, and neither in its payload. A refusal with a number "for
      reference" is the bare number with a disclaimer, and every consumer eventually reads it
- [x] Units and the target space are fields on `Interval` and on `PredictionResult`, checked on
      construction and serialised — `UNIT = "wt%"`, `SPACE = "capacity"`. An interval in
      `log1p(capacity)` cannot be built at all
- [x] Serialisable to JSON without loss, round-trip tested by **equality of the reconstructed
      object** rather than by comparing dicts. Float equality after a `json` round trip is exact
      because `json` writes `repr`
- [x] **The refusal codes are enumerated from the screens, never hand-written here.** Every screen
      declares `reasons` (#44) and `apply_screens` refuses a code outside that vocabulary, so the
      schema's code set is `ADMITTED` plus the union of the configured screens' `reasons` plus the
      shared `INDETERMINATE`. A literal list in this module is a second source of truth and will
      drift from the screens that actually emit them — which is exactly what `docs/QA-PROTOCOL.md`
      means by "every refusal reason code is reachable and asserted". **Done** — `reason_codes()`
      is derived from `delivery_screens()`, and the test asserts the set *equals* what the screens
      declare and that adding a screen widens it, rather than naming the codes (which would be the
      second source of truth arriving in the test file instead)

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

- 2026-09-07: **Closed, and it opens S6.**

  **The derivation had a gap the card's box created, and `INDETERMINATE` closes it.** #77 refuses an
  unparseable formula and an unknown element, and neither is a threshold *any* screen declares a
  code for — so a code set that is exactly "ADMITTED + the screens' reasons + INDETERMINATE" has
  nothing to say about them. It is not a gap after all: `INDETERMINATE` is the declared code for
  "this rule could not be evaluated on this candidate", `hydms/screens/domain.py` **already** emits
  it for a formula it cannot give a physical ceiling to ("it does not parse, or it names an element
  the `oliynyk` table has no mass for"), and the parse error's own sentence goes in `explanation`.
  What that costs is an *ordering constraint* on the caller — screen before featurising, or catch
  `FeaturisationError` and map it — which is **boxed on #76 and #77** rather than assumed here.

  **`delivery_screens()` is `(temperature_window(), applicability_domain())` and #49 is absent.**
  That is visible rather than hidden: the day #49 lands and joins the tuple, the vocabulary widens
  on its own and nothing in this module changes. A test asserts exactly that, with a stand-in
  screen.

  **`novelty` has no default, and `None` means "not measured".** #49 is unstarted, so `None` is the
  honest value today — but a caller must *say* so. That is the distinction AC-7 will need when it
  asks every published candidate for a distance, and it is the same rule as "an absent record means
  unknown, never full".

  **A result may carry a rejecting verdict and still carry its number.** An admitted verdict is not
  required. That is the distinction #80's interview has to answer — "how does a caller tell a
  refusal from a genuinely low prediction?" — and collapsing the two would mean the only way to see
  what the model said about an out-of-domain candidate is to remove the screen.

  **One guard is unreachable and is kept anyway**, documented as such: the result's check that its
  interval is in the same unit and space, which `Interval.__post_init__` already makes impossible to
  violate. Same shape as `featurize`'s closing contract check, and for the same reason.

  42 tests, `tests/delivery/test_contract.py`, 1.0 s. The module imports no pandas and no numpy —
  it is a schema — so it stays cheap for the API process. ruff and mypy clean, under
  `hydms.delivery.*`'s stricter `disallow_any_generics` / `warn_return_any`. (by @assistant)
