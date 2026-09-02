---
id: 82
status: backlog
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

- [ ] `app/main.py` takes a formula and a temperature and calls the API over HTTP
- [ ] The result shows the estimate **inside** its interval, using the #81 prediction band
- [ ] The domain verdict is shown with its reason, not as a silent pass
- [ ] A refusal renders as a refusal with its reason — never as a blank, an error trace, or a zero
- [ ] The nearest known alloys are shown with their measured capacities
- [ ] The temperature sweep is available for the entered composition
- [ ] The artifact version answering the request is visible on the page
- [ ] The app degrades honestly when the API is unreachable, and says so

## Runnable check

```bash
conda run -n Project python -m pytest tests/delivery/test_app.py -q
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S7; `docs/PRD-inverse-design.md` — S2, S10

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
