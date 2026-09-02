---
id: 69
status: done
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

- [x] `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `norecursedirs` covering
      `Machine_Model`, so the legacy scripts can never be collected
- [x] `[tool.ruff]` and `[tool.mypy]` sections, scoped to `hydms/`
- [x] `tests/` exists with `conftest.py` and the fixtures later cards share
- [x] A coverage floor is set on `hydms/` (`fail_under = 80`); card #86 turns it into a build failure
- [x] An `api` extra is added **reusing the pins already in `requirements-lock.txt`**
      (`fastapi==0.115.0`, `uvicorn==0.30.6`)
- [x] `requirements-lock.txt` is **not** regenerated — see the trap in `docs/ENVIRONMENT.md`
- [x] `pytest` on a clean checkout collects zero tests from `Machine_Model/` and runs no Optuna study

## Runnable check

```bash
conda run -n Project python -m pytest -q && ruff check hydms/ tests/ scripts/ && mypy
```

`pytest` runs inside `Project`, because the suite imports the pinned scientific stack. **`ruff` and
`mypy` deliberately do not** — they are static tools that need no project environment, and card #68
established that the CI fast lane stays free of conda entirely. Installing them into `Project` would
drift it from `requirements-lock.txt` for no benefit.

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S1, HG-4

## Narrative

- 2026-09-02: Created for Phase H. The legacy-test exclusion is the load-bearing part: it is
  configuration, not a rename, because `Machine_Model/` is archival and the freeze denies edits to it (by @assistant)

- 2026-09-02: Done. Two things worth knowing.

  **`norecursedirs` replaces pytest's defaults, it does not extend them.** The first version of this
  config listed only `Machine_Model` and `graphify-out`, which silently dropped `.*` — and `pytest .`
  immediately started collecting the vendored skill suites under `.claude/`, which error on import.
  The defaults are now re-listed verbatim in `pyproject.toml` and asserted by a test in
  `tests/test_tooling.py`, because nothing about a green run would otherwise reveal the loss.

  **`tomllib` is 3.11+ and the pinned interpreter is 3.10.13.** The tooling test falls back to `tomli`,
  which `Project` already carries; the `dev` extra declares it under an environment marker. Any later
  card that reads TOML needs the same fallback.

  `ruff` and `mypy` are on PATH outside `Project` (0.8.4 and 1.13.0, both above the declared floors)
  and were left there on purpose — see the runnable check above. mypy is clean across all 13 source
  files; ruff is clean after fixing one dead variable left by the `check_freeze.py` refactor and two
  pre-existing findings in `check_board.py`. (by @assistant)
