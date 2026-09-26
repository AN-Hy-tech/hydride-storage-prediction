---
id: 85
status: done
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

- [x] An ADR under `docs/adr/` in the project's established format
- [x] It records the decision, its context, the alternatives, and the consequences
- [x] It names what would justify reversing it
- [x] It is written from the `## Narrative` notes on #76, #78 and #82, not from memory
- [x] It is listed alongside the five ADRs in #36
- [x] **It argues the seam from both sides, not one** (added 2026-09-07 by #91). The title says the
      API owns no ML logic; the same seam also means **the library owns no I/O**. #91 writes a
      prediction record on every served answer and the writing is the service's job, because a
      `predict_capacity()` that writes to disk on every call is untestable, breaks the batch path,
      and would make #76's memoised bundle do I/O from a function with no reason to. That is a real
      trade-off with a real alternative — the library could own its own record and guarantee one
      exists however it is called — so it belongs in this ADR rather than in a second one. Two ADRs
      about one seam is how a seam ends up with two stories

- [x] **Record the three decisions #76 was asked to make, and the reason each was forced**
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

- [x] **Record #78's two decisions, both forced by something outside it** (added 2026-09-12 by
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

- 2026-09-12: **Landed as `docs/adr/0006-the-delivery-seam.md`, written alongside #80.** Both
  halves of the seam are argued, and the five decisions the two cards owed are recorded with
  their arguments rather than their outcomes — because in every case the argument is the thing
  that stops the decision being re-opened. (by @assistant)

  **It is `0006`, not `0001`, and that was a decision.** The format's rule is "scan for the
  highest and increment", and this card created `docs/adr/`, so it would ordinarily have taken
  `0001`. Card #36 declares its own done-when as `docs/adr/0001..0005-*.md`; taking the low
  numbers would have falsified that box and forced #36 to be edited to accommodate a file it has
  nothing to do with. So the five are **reserved**, recorded in `docs/adr/README.md` with the
  reasoning, and #36's later candidates take `0007` onward. That README also carries #36's own
  standing decision that the card is not renamed — *the ADRs are numbered, not counted* — so the
  next session does not re-take `0006` or re-open the renaming PR #7 proposed.

  **One box could not be satisfied as written, and the ADR says so in its own text rather than
  quietly.** "Written from the `## Narrative` notes on #76, #78 and #82" — #82 is `backlog` and
  its narrative records only its creation. #76's and #78's notes are rich and the ADR is built
  from them; the Streamlit half is written from #78's notes and `api/service.py`'s own docstring,
  and the ADR marks that paragraph as *a commitment made ahead of its code*. Recording it there
  rather than here because a reader of the ADR is the one who needs to know which half is
  evidenced by experience and which by intent.

  **The half that needed the most care is the one the title omits.** "The API owns no ML logic"
  is the easy direction; "the library owns no I/O" is where a future reader will push, because
  #91's alternative — the library owning its own prediction record, so a record exists however
  the prediction was obtained — is a *real* guarantee and not a small one. The ADR states the
  three reasons it lost and then states the cost plainly: **a script that imports the library
  leaves no record.** The mitigation is that `docs/API.md` recommends the HTTP door, not that the
  gap is absent.

  **What would justify reversing it** is three named conditions, not a gesture: a consumer that
  genuinely cannot speak HTTP (answer: make the library door canonical and move HG-3's parity
  burden onto it, not let callers assemble their own path); batch cost dominating for #84
  (answer: a batched entry point *in the library*, which changes the interface and not the seam);
  and the purity claim becoming false for some other reason, which dissolves #91's premise. And
  one non-reason, written down because it is what will actually be argued: that the HTTP hop
  looks like overhead. It is the overhead that buys one prediction path, and the 66-78 ms is
  measured and on the page.
