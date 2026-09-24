---
id: 82
status: doing
priority: High
blocked_by: [78, 81]
assignee: "@amirhossein"
tags: [ph, l6, S10]
---

# Streamlit forward-prediction page

**Stage S7 — Delivery: the interface** · **L6 Delivery** · Estimate: 1 d

> **Owns (hidden behind this module):** The primary user journey: a composition and a temperature in, a trustworthy answer out.

## Why this exists

The deliverable. A researcher types a formula and a temperature and gets a capacity
prediction they can act on — meaning one they can also tell *not* to act on.

The app is an **HTTP client** of the service in #78, not an in-process caller. That keeps a single
prediction path under a single set of guard rails, so HG-3's parity gate covers the app for free. It
also means the app cannot accidentally acquire its own featurisation or its own scaler.

## Done when

- [ ] `app/main.py` takes a formula and a temperature and calls the API over HTTP. **Written,
      never executed** -- Streamlit is not installed in `Project` (the box below). The call path it
      uses, `hydms.delivery.client.ServiceClient`, is tested against a uvicorn server on a real
      loopback socket, and the script's imports are held to that client, the page model and
      `hydms.figures.render` by an AST test. Tick when the script has run
- [x] The result shows the estimate **inside** its interval, using the #81 prediction band.
      `hydms.delivery.page.prediction_view`: the headline is written from the estimate and both
      bounds together, and the figure is `prediction_band`, drawn against the *served* model
      card's trained range (`reference_from`), not the installed package's
- [x] The domain verdict is shown with its reason, not as a silent pass -- every screen, passed
      or not, one row each, an admitted answer included
- [x] A refusal renders as a refusal with its reason -- never as a blank, an error trace, or a zero.
      A refused `PageView` cannot carry a figure (it raises), its headline says "this is not a
      low capacity, it is no capacity at all", and a test strikes the formula and temperature out
      of it and finds no digit left. An *invalid request* (an empty formula) is a third kind, told
      apart from both: same `422`, and "No material was judged"
- [ ] The nearest known alloys are shown with their measured capacities. **The service does not
      serve them.** An answer carries one `novelty.nearest` name and no capacity; the k nearest
      with *measured* capacity and temperature need a route (e.g. `GET /v1/neighbours`) or a field
      on the answer. Either is a contract change: `openapi.json`, `docs/API.md` (`--probe` needs
      the deployed `v3`), HG-3. The page shows the one nearest name and distance meanwhile
- [ ] The temperature sweep is available for the entered composition. The predictions are
      fetchable today (`ServiceClient.predict_many`, chunked to the served batch limit), but
      `temperature_sweep` requires a **measured** `TemperatureSupport`, and `GET /v1/model` carries
      only `rows` and `rows_above`, not per-bin counts. Owed: the model card gains the support
      histogram of the rows the domain reference was measured on, then the page draws the sweep
- [x] The artifact version answering the request is visible on the page -- on every view that
      has one, a refusal included
- [x] The app degrades honestly when the API is unreachable, and says so. `ServiceUnreachable` is
      raised, never swallowed; `unreachable_view` says the service is not answering, that no
      estimate is stale or cached, and carries no version, figure or verdict
- [ ] **Streamlit is not in `Project`, and installing it is a lock change.** A dry run of
      `pip install "streamlit>=1.30"` (2026-09-24) resolves `streamlit-1.64.0` and would move
      `starlette` 0.38.6 -> **1.7.0** -- `fastapi` 0.115.0, locked, requires an older starlette --
      and `protobuf` 3.20.3 -> **7.x**. Choosing a streamlit pin that fits both lock files, and
      re-exporting them, is the maintainer's call (`docs/ENVIRONMENT.md`). Until then
      `app/main.py` has never run, and the S7 exit check cannot be performed

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_app.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S2, S10

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)

- 2026-09-24: **Landed the half that does not need Streamlit, and the half is where every
  guarantee lives.** Streamlit is in the `app` extra, CI does not install it, and `Project` does
  not have it -- so a page whose promises were written in Streamlit calls would be a page whose
  promises nothing checks. Split the way #81 split charts from rendering:
  `hydms/delivery/client.py` (the HTTP client -- stdlib `urllib`, so it needs no extra at all),
  `hydms/delivery/page.py` (what the page shows, as a `PageView`), and `app/main.py`, a thin
  Streamlit layer whose imports a test pins. 24 tests in `tests/delivery/test_app.py`, against a
  uvicorn server on a loopback socket rather than `TestClient` -- because `urllib` *raises* on a
  `422`, and a client that mishandled that would pass every `TestClient` test there is.
  **Four outcomes, never two confused:** answered, refused, invalid request (an unreadable request --
  same `422` as a refusal, nothing else in common) and unreachable. A body outside the contract
  (a `500`, a bare number, a `422` claiming `refused: false`) raises `ServiceError` rather than
  rendering. The fixture fit moved from `test_api.py` into `tests/delivery/conftest.py`
  unchanged, so both files serve the same deployment. **Two boxes are blocked on the service,
  not on the page**: neither the k nearest neighbours with measured capacities nor the
  temperature support is served, and adding either is an API contract change. The `app` extra's
  streamlit pin fights the lock (box above). Left `doing`. (by @assistant)
