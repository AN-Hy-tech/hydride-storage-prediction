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
- [ ] **Six cards and the board README credit this script with a rule it does not have.** Found
      2026-09-13 by #100, which was itself *filed* on the belief. The claim, stated mechanically
      in #23, #29, #71, #94, #97, #100 and `kanban-hardening/README.md`, is that
      "`scripts/check_board.py` refuses a `done` card carrying an unticked box". It does not:

      | asked | answer |
      |---|---|
      | the script's own docstring | lists six promises; checkboxes are not among them |
      | `grep` for `- [ ]`, `unticked`, `unchecked` across `scripts/` and `tests/` | no rule anywhere |
      | `done` cards carrying unticked boxes today | **#1, #14, #30, #34, #86 — eleven boxes** |
      | `python scripts/check_board.py` | `OK   100 cards ... freeze in force.` |

      The README already describes the *practice* correctly at its 2026-09-07 handoff — "#30 moved
      to `done` ... its three unticked boxes are recorded findings, not work" — so the convention is
      deliberate and worth keeping: filing a new card instead of reopening a closed one preserves
      the closed card's history, and a `done` card's unticked boxes are how this board records a
      finding that is not work. **The error is only in calling it a check.** It is load-bearing
      where it appears — #97 and #100 both give it as the reason they exist as separate cards — so
      a session that believes it will keep spending cards on it, and nobody will notice the day a
      box that *is* work gets closed over, because nothing goes red.

      Left unticked rather than actioned, and deliberately so: the fix is a choice between
      implementing the rule and correcting seven files' prose, this card is `done`, and Phase H is
      frozen against work that is not in the runbook. **Not an unfreeze condition.**

      **Partly cleared 2026-09-13, by the documentation compaction.** The prose half was taken,
      because the compaction was rewriting those files anyway and leaving a known-false sentence in
      a file being rewritten is worse than finding it there. Corrected: `kanban-hardening/README.md`
      (§ Using the board now states outright that the script does not read checkboxes, and names
      the eleven boxes), `CLAUDE.md` (a new session anti-pattern), and **#81**, whose narrative gave
      the rule as its reason for filing #100 — appended as a dated correction rather than edited, per
      the board's own narrative rule. **#100 had already corrected itself** on 2026-09-13.

      Re-measured against the live board: the claim survives in **no card as a statement about the
      checker**. #23, #29 and #71 mention unticked boxes only as facts about other cards; #94 and
      #97 state the *convention* ("a finding nobody is going to see"), which is true. So the
      original count of six cards was an over-count, and the load-bearing instances were #81 and
      #100.

      **What is still owed is the other half: nothing enforces the convention.** The index at
      `docs/PHASE-H-FINDINGS.md` now makes the eleven boxes visible to a reader, which is a
      mitigation and not a check — it can itself go stale, and nothing tests it. Implementing the
      rule in `check_board.py` remains unchosen and is still not an unfreeze condition.

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
