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
- [x] The nearest known alloys are shown with their measured capacities. **Served since
      2026-09-24** by `GET /v1/neighbours?formula=…&k=…` (`hydms/delivery/neighbours.py`): the k
      nearest training compositions on the ElMD scale, nearest first, each with **every** training
      row measured on it. A lookup, not a prediction -- `"basis": "measured"`, no interval, no
      refusal; a bad query is an *invalid request*. The rows live in `novelty-reference.json`
      (893 rows over its 780 compositions), so the first neighbour **is** the answer's
      `novelty.nearest` (tested, ties included). The page draws `nearest_neighbours` with each
      neighbour's row measured closest to the asked temperature (`page.neighbours_figure`), and
      refuses to draw neighbours of another formula or from another version
- [x] The temperature sweep is available for the entered composition. **Served since
      2026-09-24**: `GET /v1/model` carries `trained_ranges.temperature_support` -- 50 K bins over
      the configured window, counted over the same 893 training rows as the capacity range, and
      stored in `domain-reference.json`. `page.sweep_view` draws `temperature_sweep` over it every
      25 K (`sweep_requests`, one batch), and a refused temperature is a **listed gap**, never a
      point on the curve
- [x] The artifact version answering the request is visible on the page -- on every view that
      has one, a refusal included
- [x] The app degrades honestly when the API is unreachable, and says so. `ServiceUnreachable` is
      raised, never swallowed; `unreachable_view` says the service is not answering, that no
      estimate is stale or cached, and carries no version, figure or verdict
- [ ] **Streamlit is pinned; it is not yet installed in `Project`.** Pinned 2026-09-24 at
      `1.56.0` (`app` extra `>=1.40,<1.57`, and in `requirements-lock.txt` with its five new
      dependencies). 1.57.0 is the first release to need `starlette>=0.40`, which the locked
      `fastapi` 0.115.0 excludes; 1.40.0 is the first that accepts the locked `pillow` 11. A
      `--dry-run --report` of 1.56.0 installs six packages and **changes none** -- the screen is in
      `docs/ENVIRONMENT.md`. Tick both this box and the first one when the closing check below
      passes:

      ```bash
      # Git Bash, repo root. Full paths on purpose: a bare `PY`/`py` is the Windows launcher,
      # which runs the machine's Python 3.13 (it did, 2026-09-25, and installed there instead).
      /c/Users/Asus/miniconda3/envs/Project/python.exe -m pip install --no-deps streamlit==1.56.0 altair==6.2.2 narwhals==2.26.0 pydeck==0.9.3 toml==0.10.2 watchdog==6.0.0
      /c/Users/Asus/miniconda3/envs/Project/python.exe -m pytest tests/delivery/test_app.py tests/delivery/test_app_script.py -v -p no:cacheprovider
      ```

      `tests/delivery/test_app_script.py` drives the real `app/main.py` through Streamlit's
      `AppTest` against a uvicorn service: load, an answer with neighbours and sweep, a refusal,
      an invalid request, an unreachable service. It skips wherever Streamlit is absent, so CI
      (which does not install the `app` extra) never runs it. The S7 exit check by eye is then
      `…/envs/Project/python.exe -m uvicorn hydms.delivery.api:app --port 8000` and
      `…/envs/Project/python.exe -m streamlit run app/main.py` -- `-m`, so the interpreter
      decides which Streamlit runs, not whichever `streamlit.exe` is first on PATH

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_app.py tests/delivery/test_app_script.py -q
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

- 2026-09-24 (night): **The two API additions landed, and both came out of the committed
  references rather than the artifact.** Neither needed a fit or a new version: the per-bin
  support and the measured rows are properties of the curated data, which is why the screen
  references (not `artifacts/v3`) are where they live, and why `v3` serves them unchanged.
  `DomainReference` gained `temperature_edges`/`temperature_counts` (a construction error unless
  they sum to `rows`); `NoveltyReference` gained per-composition `measurements`. Both
  `--emit`s reproduce every existing byte and add only the new keys. **Found while doing it:**
  `test_applicability.py`'s docstring has claimed since #48 that the committed domain reference
  is checked against `--emit`, and no test did -- added (4.7 s, unmarked, for the reason the
  novelty twin gives). The novelty twin's "1.19 s" is now 5.3 s, most of it `capacity_matrix`
  and predating this card; the docstring says so. **Contract:** `openapi.json` grew by 94
  pointers, every one an addition; `docs/API.md` re-probed against `v3` (every pre-existing
  exchange byte-identical, the model card's two reference digests moved because both references
  grew). A formula check both routes share moved into `contract.check_formula`, so
  `GET /v1/neighbours` and `POST /v1/predict` reject a blank formula with one sentence. What is
  left is the box above this card has always had: the Streamlit pin, then running the script.
  (by @assistant)
