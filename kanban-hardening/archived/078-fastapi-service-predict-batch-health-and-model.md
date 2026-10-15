---
id: 78
status: done
priority: High
blocked_by: [76, 77]
assignee: "@amirhossein"
tags: [ph, l6, S10]
---

# FastAPI service: predict, batch, health and model

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** The HTTP boundary: transport, validation, error shape, and which artifact version is answering.

## Why this exists

The interface needs a prediction path it does not own, so that the app and any script,
notebook or collaborator get the *same* answer through the *same* guard rails. An in-process Streamlit
call would give the app a private path that no contract test covers.

The route handler contains **no ML logic**. It validates, delegates to `predict_capacity()`, and shapes
the response. Everything else belongs to #76. A handler that reaches into the model is the shallow
design this phase is built to avoid — and it is how the app and the API start disagreeing.

## Done when

- [x] `POST /v1/predict` — one composition and temperature, returns the full result
- [x] `POST /v1/predict/batch` — many, with a documented size limit and per-row refusals. The limit
      is **256**, measured rather than picked: 66–78 ms a served prediction against `v2`, linear in
      the rows, so 256 is ~19 s here and ~38 s on a machine half this speed
- [x] `GET /v1/health` — liveness **and** the loaded artifact version (and `max_batch_rows`, which
      is the one policy a client must respect and has nowhere else to discover)
- [x] `GET /v1/model` — the model card as data: version, training date, honest metrics, trained
      ranges — plus the `reference_digests` #77's handoff asked for. "Honest metrics" is the
      recorded gate run and #30's per-family transfer R², each labelled with where it came from;
      there is no stored R² and none was invented
- [x] Request validation at the boundary; a malformed request is a 422 with a structured body
- [x] A refusal is distinguishable from an error and from a low prediction, in the status code and
      the body — **with one qualification, which is this card's own doing.** A refusal (422) is
      separated from a low prediction (200) and from a deployment error (500) by the status *and*
      the body. It is separated from an **invalid request** by the body alone, because the box
      above fixes a malformed request at 422 and `docs/PHASE-H-RUNBOOK.md` §6 fixes a refusal
      there too. The discriminator is one key: `refused` on an answer, `error` on a rejected
      request, and `answer_from()` refuses the second rather than half-reading it. Recorded in
      `CONTEXT.md` under *Refusal vs Invalid request*
- [x] **No ML logic in any route handler** — executable twice: no module under `api/` imports the
      surrogate, the descriptors, the screens or an array library, and no handler touches a private
      attribute of anything. The second is the one that matters, because the bundle a handler is
      handed already holds the model; both were staged red
- [x] The service refuses to start if no artifact version is resolvable — never a silent fallback.
      The lifespan resolves the bundle and does not guard the failure: `load_bundle`'s sentences
      name the fix, and wrapping them in a vaguer one of our own would cost an operator that

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_api.py
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6; `docs/PRD-inverse-design.md` — S10

## Narrative

- 2026-09-02: Created for Phase H. Built against the `backend-development` practices. Note
  `fastapi==0.115.0` and `uvicorn==0.30.6` are already pinned in `requirements-lock.txt` as leftovers
  from a removed service — reuse those pins rather than introducing new ones (by @assistant)

- 2026-09-12: **Landed.** `hydms/delivery/api/` (`service.py`, `schemas.py`, `__main__.py`) plus
  `hydms/delivery/modelcard.py`; 32 tests in 13.6 s. The pins were already there and nothing new
  entered the environment. What the card taught, in the order it was learned (by @assistant)

  **The card's two status-code boxes cannot both hold in their strong reading, and the collision is
  the design.** "A malformed request is a 422" and (from the runbook's own acceptance check) "a
  refusal is HTTP 422" put two unrelated things at one status. Neither source could be bent — the
  runbook is authority row 2 and its `curl` is the documented acceptance — so the split moved into
  the body: an answer carries `refused`, a rejected request carries `error`, and the two share no
  key at all. That is testable from both sides, and is asserted from both:
  `answer_from()` rebuilds the refusal and *refuses* the error body with its own sentence about a
  payload that "does not say whether it was refused". The 500 stays reserved for `DeliveryError`,
  which is the deployment failing and never a statement about a candidate.

  **The batch limit is a measurement, and the measurement found something for #84.** A served
  prediction costs **66–78 ms** against `v2` and splits 13 ms featurise / 22 ms surrogate / 34 ms
  screens — no hot spot, and none of it is *work*: it is per-call pandas overhead on a one-row
  frame, three times over. So the cost is linear in the rows with nothing amortised, 256 rows is
  ~19 s, and the limit is the largest round number that still returns inside a 60 s client timeout
  on a machine half this speed. The consequence belongs to #84 and is boxed there: a CSV of
  thousands cannot go through this loop, and the fix is a batched call in the *library*, not a
  cleverer handler.

  **`untrusted-family` is still `NEVER` at the request door, and the API did not become a third
  one.** #77's handoff flagged that an API batch endpoint accepting a frame with an alloy-class
  column would make that code reachable and require `NOT_ALWAYS` to say so. It does not: the batch
  body declares exactly the contract's two fields and `extra="forbid"` refuses anything else, so
  the HTTP door is the *same* door as `predict_capacity`'s and HG-2 needs no change. The reason
  that is worth stating is that it was a decision — a `frame` endpoint would have been easy and
  would have quietly widened the reachable vocabulary.

  **Declaring response models introduces exactly one risk, and it is closed by the mechanism that
  introduced it.** A model that forgets a field drops it silently on the way out, which is the
  narrowing #75 exists to prevent. `extra="forbid"` turns both directions of drift into a loud
  `ResponseValidationError` — staged red by adding an `lcb` key to `to_dict`, which produced
  `extra_forbidden` naming the field — and a second test walks each model's declared fields against
  the contract's own `to_dict()` keys. Two pydantic v2 details cost a line each: a field named
  `schema` shadows `BaseModel.schema` and warns, so it is declared under an alias; `model_version`
  no longer trips the protected namespace in 2.12.

  **The request models declare less than they could, on purpose.** Pydantic can enforce a non-empty
  formula and a finite temperature; it must not, because `PredictionRequest` already does and two
  owners of one rule is how the sentences a caller is shown come apart. So the transport declares
  only what it alone can see — JSON types, unknown fields, `extra="forbid"` (which is also what
  stops a caller naming its own `screens` or `version`, #75) — and everything semantic reaches the
  contract and comes back as the contract's own sentence.

  **A conforming client cannot send `NaN`.** `float('nan')` is not JSON and httpx serialises with
  `allow_nan=False`, so the contract's finiteness guard is reachable only from a client that emits
  the non-standard literal. The test types it as raw content rather than deleting the case: rare,
  real, and it would otherwise arrive as a 500 from inside the request type.

  **Two changes outside this package, both small and both argued.** `ArtifactBundle` grew a
  `manifest` — the training date and the gate record are the model card's, and re-reading the file
  per request would let an operator change what a running service claims about itself; it is `None`
  for a bundle assembled through the gate door, because an absent record must read as *unknown*
  and never as clean. And `trained_ranges` is keyed by each screen's `name`, not its `quantity`:
  that attribute holds the phrase a refusal writes into a sentence ("the trained temperature
  range"), and it would have become an addressable API key that changes whenever somebody improves
  the wording of a refusal.

  **"No ML in a route handler" needed two checks, and the first one is the weaker.** An import scan
  over `api/` catches a handler reaching for the featuriser. It does not catch the likelier defect:
  the handler is *handed* the bundle, and `bundle._surrogate.predict(...)` needs no import at all.
  The second test forbids a handler touching any private attribute, which works because #76 made
  everything a transport may report public on the bundle by design. Both staged red.
