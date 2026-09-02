---
id: 69
status: backlog
priority: High
blocked_by: [2]
assignee: "@amirhossein"
tags: [ph, l0, HG-4]
---

# Test infrastructure: pytest, ruff, mypy and the coverage floor

**Stage S1 — QA foundation** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Where tests live, how they are discovered, and which lint and type rules the package is held to.

## Why this exists

`pyproject.toml` declares `pytest`, `ruff` and `mypy` in the `dev` extra and **configures none of
them** — there is no `[tool.pytest.ini_options]`, no `[tool.ruff]`, no `[tool.mypy]`, no `conftest.py`
and no `tests/` directory anywhere. Every card after this one has a runnable check that needs somewhere
to live.

Test discovery is not merely absent, it is hazardous. `Machine_Model/tests/test_catboost_smogn.py`
matches pytest's default `test_*.py` pattern but is a 250-line training script with no test functions:
it calls `optuna.create_study(...).optimize(objective, n_trials=50)` at module scope, so a bare
`pytest` would **run an Optuna study during collection**. `test_check_database.py` asserts against
`data/database/hydride.db`, which is gitignored and absent from a clean clone. Neither is fixed by
editing them — `Machine_Model/` is archival and deny-listed by the freeze. They are excluded by
configuration instead.

## Done when

- [ ] `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `norecursedirs` covering
      `Machine_Model`, so the legacy scripts can never be collected
- [ ] `[tool.ruff]` and `[tool.mypy]` sections, scoped to `hydms/`
- [ ] `tests/` exists with `conftest.py` and the fixtures later cards share
- [ ] A coverage floor is set and enforced on `hydms/`
- [ ] An `api` extra is added **reusing the pins already in `requirements-lock.txt`**
      (`fastapi==0.115.0`, `uvicorn==0.30.6`)
- [ ] `requirements-lock.txt` is **not** regenerated — see the trap in `docs/ENVIRONMENT.md`
- [ ] `pytest` on a clean checkout collects zero tests from `Machine_Model/` and runs no Optuna study

## Runnable check

```bash
conda run -n Project python -m pytest -q && conda run -n Project ruff check hydms/
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1, HG-4

## Narrative

- 2026-09-02: Created for Phase H. The legacy-test exclusion is the load-bearing part: it is
  configuration, not a rename, because `Machine_Model/` is archival and the freeze denies edits to it (by @assistant)
