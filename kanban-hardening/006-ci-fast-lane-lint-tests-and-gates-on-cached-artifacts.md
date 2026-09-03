---
id: 6
status: doing
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
| **suite** | ~~`Project` from the lockfile, cached by its hash~~ → `pip install -e ".[dev]"`, pip-cached | `pytest`, then `python -m hydms.gates run --fast` |

**The `suite` row was wrong and is corrected above.** `environment.lock.yml` cannot be restored
on a Linux runner: it pins conda build strings and is win-64 by construction — `vc`,
`vs2015_runtime`, four `m2w64-*`, `ucrt`, `win_inet_pton` and 85 Windows build strings across 253
lines — and `requirements-lock.txt` carries `pywin32==308`. `docs/ENVIRONMENT.md` says it outright:
"on a different OS the solve will fail". See the narrative for what was chosen instead and what it
costs.

`hygiene` gives a red/green signal in under a minute even when the suite's install fails, which
is exactly the case where a single combined job would tell you nothing. Only `suite` pays for
an environment, and only because the test suite imports the scientific stack.

The gate lane is already declared: `--fast` selects the gates answerable against a published
artifact, `--slow` the ones needing a retrain, and each gate carries its own lane
(`hydms/gates/`, card #5). This workflow does not decide the split; it reads it.

## Done when

- [x] `.github/workflows/ci.yml` runs on push and PR against `main`. **It runs on every push to
      every branch, not only to `main`** — the old `integrity.yml` filtered `push: branches:
      [main]`, so the eight Phase H commits on this branch got no CI at all. The
      `pull_request` trigger is kept for forks (PR #1 was one) and suppressed for branches in
      this repository by a `head.repo.full_name` guard, so a PR'd branch is not built twice
- [x] A **conda-free** `hygiene` job: `ruff check hydms/ tests/ scripts/` and `mypy`, on a bare
      `setup-python` with no lockfile restore. It also absorbs `check_board.py` and
      `check_freeze.py`, and `integrity.yml` is deleted — the two workflows would otherwise mean
      two checkouts and two queue waits for the same fifteen-second answer. Both stdlib checks
      run *before* `pip install`, so a broken pip cannot hide a freeze violation
- [x] ~~A `suite` job: env from the lockfile (cached by its hash)~~ → **a `suite` job:
      `pip install -e ".[dev]"` on `setup-python` 3.10**, then `pytest`, then
      `python -m hydms.gates run --fast`. The lockfile is win-64 only; see the corrected job
      table above and the narrative
- [x] `hygiene` reports independently of `suite` — a broken install must not hide a lint or type
      failure, nor the reverse. Two jobs, no `needs:` edge between them
- [x] ~~Conda env cached by lockfile hash~~ → **pip cache keyed on `pyproject.toml`**, via
      `setup-python`'s `cache: pip`. Measured warm below
- [x] The workflow fails on any gate failure, not only on test failures — `run --fast` exits 1 on
      FAILED or ERRORED (`hydms/gates/__main__.py`), and no `continue-on-error` is set. It does
      **not** fail on SKIPPED, and must not: that is card #5's documented lane/named-gate
      asymmetry, and `--strict` here would hold CI red for the length of the phase
- [x] The lockfile is **not** regenerated to add tooling: `docs/ENVIRONMENT.md` records a
      hand-applied `python-graphviz` → `graphviz` fix that regeneration silently undoes. Neither
      lockfile is touched by this card

- [ ] **Owed to #7 — the pinned environment is now unexercised by CI.** No lane rebuilds
      `Project`. That is correct for a fast lane and wrong for the project: the environment that
      produced the published numbers is currently verified on one laptop and nowhere else, so a
      lockfile that has stopped recreating would not be discovered until someone tried. The slow
      lane owns this and must run on `windows-latest` — it is the only runner that can restore
      `environment.lock.yml` — which costs 2× minutes on a private repository. #7 carries the box

- [ ] **Owed to #86 — the coverage floor is still unenforceable, and this card moved it within
      reach.** `fail_under = 80` in `pyproject.toml` runs nowhere: `pytest-cov` is absent from
      `Project` (`docs/QA-PROTOCOL.md` §6) and installing it there would invalidate the lockfile.
      The `suite` job is pip-installed from the `dev` extra, which **does** carry `pytest-cov>=5.0`
      — so coverage is now installable in CI without touching the lockfile at all. Turning it on
      is #86's decision, not a flag added in passing. #86 carries the box

## Runnable check

The lane's own content, run locally — it fails on exactly what CI will fail on. The workflow side
is confirmed by the run the push itself triggers, which is why the trigger had to widen past
`main`: `gh run list --branch "$(git branch --show-current)"`.

```bash
python scripts/check_board.py --root . && python scripts/check_freeze.py --base origin/main && ruff check hydms/ tests/ scripts/ && mypy && conda run -n Project python -m pytest -q && conda run -n Project python -m hydms.gates run --fast
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
