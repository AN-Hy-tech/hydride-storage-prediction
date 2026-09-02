---
id: 78
status: backlog
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

- [ ] `POST /v1/predict` — one composition and temperature, returns the full result
- [ ] `POST /v1/predict/batch` — many, with a documented size limit and per-row refusals
- [ ] `GET /v1/health` — liveness **and** the loaded artifact version
- [ ] `GET /v1/model` — the model card as data: version, training date, honest metrics, trained ranges
- [ ] Request validation at the boundary; a malformed request is a 422 with a structured body
- [ ] A refusal is distinguishable from an error and from a low prediction, in the status code and the body
- [ ] **No ML logic in any route handler**
- [ ] The service refuses to start if no artifact version is resolvable — never a silent fallback

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_api.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S6; `docs/PRD-inverse-design.md` — S10

## Narrative

- 2026-09-02: Created for Phase H. Built against the `backend-development` practices. Note
  `fastapi==0.115.0` and `uvicorn==0.30.6` are already pinned in `requirements-lock.txt` as leftovers
  from a removed service — reuse those pins rather than introducing new ones (by @assistant)
