---
id: 6
status: backlog
priority: High
blocked_by: [5]
assignee: "@amirhossein"
tags: [p0, l0, S1]
---

# CI fast lane: lint, tests and gates on cached artifacts

**Phase 0 — Foundation & provenance** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** The per-push feedback loop.

## Why this exists

Full CI from the start was chosen. Retraining the surrogate is not a per-push job, so the
pipeline splits: this fast lane runs on every push and must finish in minutes, using the
published artifact version rather than training a new one. The slow lane is ticket 7.

## Two jobs, and only one of them builds an environment

**Lint and type checks do not run inside the `Project` conda environment, and must not.**
Neither ruff nor mypy imports the project's dependencies — mypy reads `pyproject.toml`, and
the scientific stack is stubbed out by the `ignore_missing_imports` overrides there. Card #68
established the principle and `docs/QA-PROTOCOL.md` §6 states it: the fast lane installs
nothing and builds no environment, which is what keeps it under a minute and what keeps it
working when the environment is broken, unpinned or absent.

So this workflow is two jobs, and the split is the point:

| Job | Environment | Runs |
|---|---|---|
| **hygiene** | bare `setup-python`, `pip install ruff mypy` | `check_board.py`, `check_freeze.py` (already live in `integrity.yml`), `ruff`, `mypy` |
| **suite** | `Project` from the lockfile, cached by its hash | `pytest`, then `python -m hydms.gates run --fast` |

`hygiene` gives a red/green signal in under a minute even when the conda restore fails, which
is exactly the case where a single combined job would tell you nothing. Only `suite` pays for
the environment, and only because the test suite imports the scientific stack.

The gate lane is already declared: `--fast` selects the gates answerable against a published
artifact, `--slow` the ones needing a retrain, and each gate carries its own lane
(`hydms/gates/`, card #5). This workflow does not decide the split; it reads it.

## Done when

- [ ] `.github/workflows/ci.yml` runs on push and PR against `main`
- [ ] A **conda-free** `hygiene` job: `ruff check hydms/ tests/ scripts/` and `mypy`, on a bare
      `setup-python` with no lockfile restore
- [ ] A `suite` job: env from the lockfile (cached by its hash), `pytest`, then
      `python -m hydms.gates run --fast`
- [ ] `hygiene` reports independently of `suite` — a broken conda restore must not hide a
      lint or type failure, nor the reverse
- [ ] Conda env cached by lockfile hash so a warm `suite` run is under ~5 minutes
- [ ] The workflow fails on any gate failure, not only on test failures
- [ ] The lockfile is **not** regenerated to add tooling: `docs/ENVIRONMENT.md` records a
      hand-applied `python-graphviz` → `graphviz` fix that regeneration silently undoes

## Runnable check

The lane's own content, run locally — it fails on exactly what CI will fail on. `gh workflow
run ci.yml --ref main && gh run watch` confirms the workflow side once it is on `main`.

```bash
ruff check hydms/ tests/ scripts/ && mypy && conda run -n Project python -m pytest -q && conda run -n Project python -m hydms.gates run --fast
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Amended while landing #5. The card previously listed `ruff` and `mypy` as steps
  after "env from lockfile (cached)", which put them inside the `Project` environment. They
  were deliberately left out of it — they need no project dependencies, and #68 established
  that the fast lane installs nothing so it still reports when the environment is broken. Left
  unfixed, #86 would have inherited the assumption and made a conda restore a prerequisite for
  a lint result. Split into two independently-reporting jobs, and the runnable check replaced
  with the lane's own commands: `gh run watch` cannot fail before the workflow exists, which
  made it a check that could not go red (`docs/QA-PROTOCOL.md` §3). (by @assistant)
