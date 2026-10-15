---
id: 79
status: done
priority: High
blocked_by: [78]
assignee: "@amirhossein"
tags: [ph, l6, HG-3, AC-4]
---

# GATE HG-3: API contract tests and transport parity

**Stage S6 — Delivery: contract and API** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** The guarantee that going over HTTP does not change the answer, and that the published contract does not change without someone noticing.

## Why this exists

AC-4 checks that known alloys round-trip through `predict()`. It says nothing about what
happens at the transport boundary, where a float can be truncated by serialisation, a column can be
reordered by a dict round-trip, and an interval can be dropped by a response model that forgot a field.

This gate extends AC-4 to the edge of the system: for the same input, the API's answer and
`predict_capacity()`'s answer must be the same answer. It also snapshots the OpenAPI document, so that
a breaking contract change is a visible diff rather than a surprise for whoever wrote a client.

## Done when

- [x] For a fixed set of inputs spanning normal, boundary and refused cases, the API result equals
      `predict_capacity()`'s result — including the interval bounds, to full precision
- [x] The OpenAPI document is snapshotted; a change to it fails the test until the snapshot is updated
      deliberately
- [x] Every refusal reason code in #77 is reachable through the API and asserted
- [x] Batch results are order-preserving and per-row refusals do not fail the whole request
- [x] Registered in the gate harness as HG-3

- [x] **422 carries two unrelated shapes, and the gate must measure both** (added 2026-09-12 by
      #78). A refusal and an invalid request are both 422 — the runbook fixes the first, #78's own
      card fixes the second — so the status establishes nothing and the *body* is the whole
      contract: an answer carries `refused`, a rejected request carries `error`, and they share no
      key. Assert that `answer_from()` rebuilds the first and **refuses** the second, because a
      client that reads an error body as an answer is the failure this pair can produce and it is
      silent. `hydms/delivery/api/service.py` states the split; `CONTEXT.md` has the term
- [x] **The API did not become a third door, and the gate should hold it that way** (added
      2026-09-12 by #78). #77 left the note that a batch endpoint accepting a frame with an
      alloy-class column would make `untrusted-family` reachable and require `NOT_ALWAYS` in
      `hg2_refusal_path.py` to say so. It does not accept one: the batch body declares exactly the
      contract's two fields under `extra="forbid"`. A transport-parity gate is the natural place to
      pin that the HTTP door accepts no field `predict_capacity()` does not

## Runnable check

```bash
conda run -n Project python -m hydms.gates run HG-3
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6, HG-3; `docs/PRD-inverse-design.md` — AC-4

## Narrative

- 2026-09-26: Moved verbatim from `CONTEXT.md`, entry **Refusal vs Invalid request**, where it stood as a *State of the term* block. The glossary now holds definitions only; card state lives here. (by @assistant)

  > *State of the term, not part of the definition:* **gate HG-3 measures the distinction at the
  > transport** (card #79, `done` 2026-09-12). Eight malformed bodies are sent over HTTP and each must
  > come back 422 carrying `error`, carrying no `refused`, and be **refused** by
  > `hydms.delivery.contract.answer_from()`; every refusal must come back carrying `refused`, carrying
  > no `error`, and rebuild through the same function into an object equal to the library's. So the
  > one-key split is executable rather than a convention — and the failure it exists to catch, a
  > client reading a rejected request as an answer, is the one that would otherwise be silent.
  >
  > **The client keeps it too** (card #82, 2026-09-24). `hydms.delivery.client` returns an
  > `InvalidRequest` (not a `Refusal`) for a 422 carrying `error`, and the prediction page words it
  > as "No material was judged". Both are tested over a real socket in `tests/delivery/test_app.py`.
  >
  > **A lookup has only the second kind** (card #82, 2026-09-24 night). `GET /v1/neighbours` judges
  > no material, so it has no refusal: a blank formula, an unreadable one or a `k` out of range is a
  > 422 carrying `error`, and an unreadable formula carries the novelty screen's own sentence — the
  > one `POST /v1/predict` *refuses* the same string with. Same words, different kind, because one
  > route judged a material and the other did not.

- 2026-09-02: Created for Phase H (by @assistant)

- 2026-09-12: **Landed.** `hydms/gates/hg3_transport_parity.py` replaces the `Pending`, over a new
  `hydms/delivery/api/openapi.py` and the contract it commits, `hydms/delivery/api/openapi.json`.
  `python -m hydms.gates run HG-3` — **PASSED in 4.52 s** against `v2`: 11 probes (3 answered, 8
  refused), 8 malformed requests, 257 candidates against the published limit of 256, 0 differences.
  22 tests in `tests/gates/test_hg3_transport_parity.py`, 15 in `tests/delivery/test_openapi.py` —
  **37 passed in 10.1 s**. `pytest tests/delivery` — **160 passed, 12.9 s**. The lanes on the final
  tree: `pytest -m "not slow"` — **1440 passed, 4 deselected, 12 min 3 s**; `python -m hydms.gates
  run --fast` — **7 passed, 0 failed, 2 skipped, 26.2 s** (was 6/3, the skips now AC-5 and HG-4
  alone); `run --all` — **8 passed, 0 failed, 4 skipped, 3.0 min**. ruff and mypy clean.
  What the card taught, in the order it was learned (by @assistant)

  **The probe set is HG-2's, and that is the design rather than a saving.** The card asks for "a
  fixed set of inputs spanning normal, boundary and refused cases", and #77 already built one and
  pinned what the *library* does with each. A second list here would drift from it, and then "the
  API agrees with the library" would be established over inputs nobody checked the library on. So
  `PROBES` and `NOT_ALWAYS` are imported whole, the vocabulary check is HG-2's rule restated at the
  transport, and `untrusted-family` stays `NEVER` at both doors from one record. What is this
  gate's own is the eight inputs `predict_capacity()` has no way to be asked: an unknown field, a
  formula that is not a string, a batch over the limit — a function with two parameters cannot be
  handed a ninth key.

  **The comparator was blind to an empty container, and it is used on every answer.** `_leaves`
  flattens a JSON document to `{pointer: scalar}`, and recursing into `{}` or `[]` emits *nothing*
  — so a key whose value is empty vanished from both sides and a response that dropped `screens: []`
  compared equal to one that kept it. Found by a test that expected the dropped key reported and
  got silence. An empty container is now its own leaf. Worth recording because this function is
  read twice: once on the OpenAPI document and once on **every served answer against the library's**,
  so a blind spot in it is a blind spot in the whole parity claim, and it would have passed forever.

  **The gate could not have run in CI, which is the one lane where its first half earns its keep.**
  CI installs `.[dev,uq,novelty]`; without `fastapi` the service cannot be built, so HG-3 would have
  reported SKIPPED on every push and `tests/delivery/test_api.py` would have skipped itself away
  beside it. The snapshot comparison is a fact about the *code* — it needs no artifact, and the fast
  lane has none — so it is both the half that must run on a push and the only half that can. `api`
  is now in the CI install line, argued there in the file's own terms: it is the third variation on
  the `uq` and `novelty` asymmetry against `parity`, permissively licensed, already pinned in
  `requirements-lock.txt`, and the skipped check is the only check of something otherwise invisible.
  The gate still skips — loudly, naming the extra — where the service genuinely cannot be started.

  **The snapshot is generated, and the diff is by pointer rather than by document.** A failure reads
  `/paths/~1v1~1predict/post/summary: committed '…', produced '…'`, because a check that prints two
  20 kB documents and leaves the reader to find the difference is a check nobody acts on. The file
  is rewritten by `python -m hydms.delivery.api.openapi --emit`, a test asserts the committed bytes
  are what that command produces, and it ships as package data for the same reason
  `screens/domain-reference.json` does. A FastAPI or pydantic upgrade *will* move it: that is a
  change to what a client reads, so it is meant to arrive as a diff somebody approves.

  **The batch limit is read from the running deployment, not imported.** `GET /v1/health` publishes
  `max_batch_rows` and the gate sends one more than whatever it publishes, so a service started with
  a narrower limit is measured at the width it actually runs. A limit a service publishes and does
  not enforce is a limit a client discovers by timing out.

  **Staged red eight ways, and every one of them is a real defect rather than a stand-in**
  (`docs/QA-PROTOCOL.md` §5): a summary changed in the committed document; no document committed at
  all; a request model that declares a `version` a caller could pin; one that ignores unknown fields
  instead of refusing them; an interval bound rounded on its way out (`/interval/lower`, both
  numbers, full precision); an error envelope given a `refused` key — the silent one, where a client
  branching on that key reads a rejected request as an answer; a batch returned in reverse order; a
  published limit not enforced. The two skips are staged too: no artifact, and no `api` extra.

  **What it does not establish, said in the module.** There is no socket. `TestClient` drives the
  ASGI application in-process, so real JSON is serialised and parsed but a proxy that rewrites a
  body or a gateway that truncates a float is outside what this repository can measure.
