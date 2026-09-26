---
id: 5
status: done
priority: High
blocked_by: [2, 3]
assignee: "@amirhossein"
tags: [p0, l0, AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8]
---

# Gate harness: PRD acceptance criteria as runnable checks

**Stage S1 — QA foundation** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** What 'passing' means. Each PRD acceptance criterion becomes executable here.

## Why this exists

PRD section 10 fixes eight acceptance criteria *before* results are seen. This turns each
into a check that exits non-zero on failure, so they are enforced rather than remembered.

Individual gate implementations are separate tickets (21, 31, 32, 33, 41, 56); this builds
the harness, registry and reporting format they plug into.

## Done when

- [x] `hydms/gates/` with one module per criterion and a shared `Gate` protocol
- [x] `python -m hydms.gates run --all` executes every registered gate and prints a pass/fail table
- [x] Each gate returns a structured result (name, passed, measured value, threshold, message)
- [x] Gate results are written into the artifact manifest — **as far as the manifest exists.**
      Card #4 is unstarted, so a run writes the same object to `<artifacts>/gate-results.json`
      behind a versioned `schema` key. #4 embeds it under `gates` rather than inventing a
      second format; the schema string is what lets it know it can.
- [x] Unimplemented gates report `SKIPPED`, never `PASSED`

Delivered beyond the original list, because the gate cards behind this one need them:

- [x] `run --fast` / `--slow` — the lane split cards #6 and #7 select on, declared next to
      each check rather than in a workflow file
- [x] `run AC-2 …` — the invocation on the runnable check of #21, #31, #32, #33, #71, #77, #79
- [x] `list` — what the project has promised to check, and which card owes each check
- [x] An exit-code contract: 0 green, 1 a gate failed or a **named** gate was skipped,
      2 a bad invocation (unknown gate name, no selection, unreadable config)

## Runnable check

```bash
python -m hydms.gates run --all
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Built. Twelve criteria registered — the PRD's eight plus Phase H's four — all
  `SKIPPED`, which is the point: the registry is now the complete list of what this project
  has promised to check, and a run states in words what it did not establish. 69 tests green,
  ruff and mypy clean. Five things the build settled, each of which could have gone the other
  way (by @assistant)

  **A skip means different things depending on what was asked.** `run AC-2` exits non-zero
  while AC-2 is unimplemented — you asked a specific question and a skip is not an answer, so
  the runnable check on every gate card is honest from the day it is written. `run --all`
  exits zero and prints a `NOT CHECKED` banner instead, because a whole-registry run that is
  red for the length of the phase is a run nobody looks at. `--strict` turns the second into
  the first for a caller who wants it.

  **Discovery is by module, not by decorator.** A decorator only registers a gate if
  something imported its module, which makes the registry depend on import order; scanning
  the package directory makes "this criterion exists" a fact about the filesystem. A module
  that fails to import registers as `ERRORED`, not as absent — the count of registered gates
  must not be a fact about today's import luck.

  **A gate may only report on itself.** A result whose `name` differs from the gate that
  produced it is discarded as `ERRORED`. Without that, one gate could report a pass on
  another's behalf and the table would look complete; it is a two-line guard against the
  exact failure this harness exists to prevent.

  **The manifest does not exist yet.** Card #4 is unstarted, so the JSON report stands alone
  under `artifacts/` behind a `schema` key. Writing it also exposed that
  `hydms/config/pipeline.yaml` claimed its output directories were gitignored and four of the
  five were not — the first default run would have dropped an untracked file into the tree.
  Fixed in `.gitignore` rather than by moving the report somewhere less useful.

  **`docs/QA-PROTOCOL.md` §6 names a command the environment cannot run.** Neither
  `pytest-cov` nor `coverage` is installed in `Project`, so
  `conda run -n Project python -m pytest --cov` fails with `unrecognized arguments: --cov` and
  the coverage floor in `pyproject.toml` is currently unenforceable anywhere. Card #69
  declared them in the `dev` extra; nothing installed them. Left for **#86**, which owns the
  floor in CI, because installing into `Project` invalidates `environment.lock.yml` and that
  is a deliberate decision, not a side effect of this card.

  One test is worth naming: `test_the_registry_matches_the_runbook_gate_table` parses §4 of
  the runbook and asserts every documented gate→card pair against the registry, and that the
  only registered gates missing from that table are the frozen three. Prose and code cannot
  drift apart about who owes which gate without something going red.
