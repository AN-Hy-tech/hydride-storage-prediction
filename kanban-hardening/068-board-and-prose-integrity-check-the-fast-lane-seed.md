---
id: 68
status: done
priority: Normal
blocked_by: []
assignee: "@amirhossein"
tags: [p0, l0, S1]
---

# Board and prose integrity check — the fast-lane seed

**No stage — slots in where its blockers allow** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What "the plan is still coherent" means, and how CI decides it.

## Why this exists

The CI fast lane (ticket 6) is blocked behind the gate harness, which is blocked behind the
package and the config loader. That is correct sequencing, but it leaves the repository with
**no green/red signal at all** until several days of work land — and the artifacts that exist
right now can already be wrong in ways nobody would notice.

Three failure modes are silent and real:

- A `blocked_by` id that points at no card. The board looks fine; the dependency is fiction.
- A **cycle** in `blocked_by`. Every card in the loop waits forever and nothing reports why.
- A Markdown link that 404s. `CLAUDE.md` is a router — a dead link there sends every future
  session to a file that is not the one it wanted.

This checks exactly those, and nothing it cannot honestly check yet.

**It does not replace ticket 6, it seeds it.** When the harness exists, ticket 6 adds lint,
tests and `hydms.gates run --fast` as steps beside this one.

## Design note

Stdlib-only and dependency-free on purpose: this must still run when the conda environment is
broken, unpinned or absent — which, until ticket 1 lands, is the state of every fresh clone.
That constraint is what keeps the job under a minute with no install step.

## Done when

- [x] `scripts/check_board.py` validates card ids, statuses, blocker resolution, acyclicity
      and relative Markdown links
- [x] A card in `doing` or `done` with an unfinished blocker is a failure
- [x] `.github/workflows/integrity.yml` runs it on push, PR and dispatch against `main`
- [x] Negative-tested: a broken board produces a non-zero exit and names every violation
- [x] No `pip install` step; runs on a bare `setup-python`

## Runnable check

```bash
python scripts/check_board.py --root .
```

## Traces to

`docs/PRD-inverse-design.md` — S1 (the CI fast lane this seeds).
The board's own `blocked_by` rule in `kanban/README.md` § Using the board.

## Narrative

- 2026-08-30: Built while setting up the GitHub repository. Added outside the original PRD
  decomposition because the gap it fills only became visible once the board existed: tickets
  6 and 7 are the real CI, but both sit behind the harness, leaving the repo with no
  automated signal in the meantime. Negative-tested against a fixture board carrying a
  cycle, a dangling blocker, a bad status, an id/filename mismatch and a dead link — all
  five were caught. (by @assistant)
