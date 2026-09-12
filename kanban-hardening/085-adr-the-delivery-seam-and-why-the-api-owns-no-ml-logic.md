---
id: 85
status: backlog
priority: Normal
blocked_by: [78]
assignee: "@amirhossein"
tags: [ph, l7, S7]
---

# ADR: the delivery seam, and why the API owns no ML logic

**Stage S8 — Evidence and close** · **L7 Evidence** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The record of the delivery layer's one hard-to-reverse decision.

## Why this exists

Two decisions in this layer are expensive to undo and will look arbitrary to a reader who
was not present: that `predict_capacity()` is a deep module rather than a set of helpers the callers
compose, and that Streamlit talks HTTP to the API rather than calling the library in-process.

Both were chosen for the same reason — one prediction path, one set of guard rails, one thing for HG-3
to check. That reasoning belongs in an ADR, because the next person to touch this layer will otherwise
see the HTTP hop as pointless overhead and remove it.

## Done when

- [ ] An ADR under `docs/adr/` in the project's established format
- [ ] It records the decision, its context, the alternatives, and the consequences
- [ ] It names what would justify reversing it
- [ ] It is written from the `## Narrative` notes on #76, #78 and #82, not from memory
- [ ] It is listed alongside the five ADRs in #36
- [ ] **It argues the seam from both sides, not one** (added 2026-09-07 by #91). The title says the
      API owns no ML logic; the same seam also means **the library owns no I/O**. #91 writes a
      prediction record on every served answer and the writing is the service's job, because a
      `predict_capacity()` that writes to disk on every call is untestable, breaks the batch path,
      and would make #76's memoised bundle do I/O from a function with no reason to. That is a real
      trade-off with a real alternative — the library could own its own record and guarantee one
      exists however it is called — so it belongs in this ADR rather than in a second one. Two ADRs
      about one seam is how a seam ends up with two stories

- [ ] **Record the three decisions #76 was asked to make, and the reason each was forced**
      (added 2026-09-11 by #76). The card boxed all three "say which in the ADR (#85)", so they are
      owed here with their arguments, not just their outcomes:

      1. **The assembly order.** Null-check, featurise, predict, screen, resolve, answer — and a
         parse failure is caught where it raises and mapped to `INDETERMINATE`. "Screen before
         featurising" was not an available alternative: the applicability screen judges a
         *prediction*, so it cannot run before one exists, and screening first would have needed two
         passes and a second rule for merging them.
      2. **Novelty is in `delivery_screens()`, so ElMD is required to predict at all.** The stated
         cost was already paid: `pyproject.toml` calls `novelty` a prediction-path dependency, CI
         installs it, and the project is GPL-3.0-or-later because ElMD is. Leaving it out bought only
         a deployment where `PredictionResult.novelty` is permanently `None` — and no test would
         have shown it.
      3. **One cache or two.** The delivery bundle memoises by `(store, version)` *and*
         `hydms.surrogate.predict._LOADED` still memoises the surrogate. Two caches, one object:
         the bundle holds the surrogate the lower layer memoised rather than unpickling the booster
         twice, and `hydms.delivery.predict.clear_cache()` clears both. Neither caches the promotion
         pointer, so a rollback takes effect on the next call.

      There is a fourth the card did not ask for and the ADR should carry: **the library writes
      nothing.** `predict_capacity()` is pure, which is the seam #91 depends on

- [ ] **Record #78's two decisions, both forced by something outside it** (added 2026-09-12 by
      #78). **(a) A refusal and an invalid request share HTTP 422.** Not chosen: the runbook's
      acceptance check fixes a refusal at 422 and #78's own card fixes a malformed request there,
      and neither source could be bent, so the distinction moved into the body — `refused` versus
      `error`, sharing no key, with `answer_from()` refusing the second. State it, because the next
      person will read one 422 handling two things as sloppiness rather than as the resolution of a
      conflict between two authorities. **(b) The transport declares less than it can.** Pydantic
      could enforce a non-empty formula and a finite temperature; it must not, because
      `PredictionRequest` already does and two owners of one rule is how the sentence a caller is
      shown comes apart from the sentence the library would have given. The transport declares only
      what it alone can see — JSON types, unknown fields — which is the same "one owner per rule"
      argument as the seam itself, one level down

## Runnable check

```bash
python scripts/check_board.py --root .
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8; `docs/PRD-inverse-design.md` — S7

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
