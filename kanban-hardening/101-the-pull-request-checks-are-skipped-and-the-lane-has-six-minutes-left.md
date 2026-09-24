---
id: 101
status: backlog
priority: Normal
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l0]
---

# The pull-request checks are skipped, and the lane has six minutes left

**Stage S8 — Evidence and close** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Whether a green tick on this repository means a check ran.

**This card is NOT an unfreeze condition.** It was found by a CI audit on 2026-09-13 and is filed
so it has an owner, not to widen `docs/FREEZE.md`. The unfreeze condition is fixed and stays fixed.

## Why this exists

Three findings, all measured against GitHub rather than against the YAML. The workflow is green and
nothing here is a regression — each one is a way the green could stop meaning what it says.

### F1 — every pull request carries two skipped checks that shadow the real ones

`ci.yml` fires on both `push` and `pull_request`, and both jobs then carry

```yaml
if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository
```

The reasoning in the file is sound for compute — a same-repo branch is already covered by its own
push event, so the PR event would only duplicate it. The consequence is not: **the PR event still
creates check runs, and they resolve to `skipped`.** PR #6's rollup on 2026-09-13:

| check name | conclusion | run | created |
|---|---|---|---|
| Hygiene — board, freeze, ruff, mypy | SUCCESS | `34723036741` (push) | 22:32:33Z |
| Suite — pytest and the fast gates | SUCCESS | `34723036741` (push) | 22:32:33Z |
| Hygiene — board, freeze, ruff, mypy | **SKIPPED** | `34723038965` (pull_request) | 22:32:**36**Z |
| Suite — pytest and the fast gates | **SKIPPED** | `34723038965` (pull_request) | 22:32:**36**Z |

The skipped pair is **three seconds later** than the real pair and carries the **same two names**.
GitHub resolves a required status check by name to its most recent run, and a skipped required
check is treated as satisfied. So the day branch protection is switched on for these names, it is
satisfiable by a job that does nothing — and today, before that, a reviewer reading `gh pr checks 6`
sees `skipping 0s` twice and has to know which of the four rows to believe.

This is the shape of [[ask-what-is-green-that-should-not-be]]: the finished run's red is history,
and the dangerous state is an *absent* check rendering as a tick.

### F2 — branch protection cannot be turned on here at all

Card #95's second box offers three ways to guard `main` before #6 merges, the first being "a
branch-protection rule requiring a check `main` cannot run". **That option does not exist on this
repository.** Measured 2026-09-13:

```
GET /repos/AN-Hy-tech/hydride-storage-prediction/branches/main/protection
→ 403  "Upgrade to GitHub Pro or make this repository public to enable this feature."
```

The repository is `private: true` on a plan without protected branches. So #95's decision is
between the remaining two options only, and F1's required-check hazard is conditional on a plan
change rather than on a settings change. Both facts belong on #95, and this card's first job is to
put them there rather than leave them here.

### F3 — the fast lane has about six minutes of headroom, against a cap that has already killed three pushes

Measured across the seven most recent `suite` runs on 2026-09-12, reading the `pytest` step's own
start and end timestamps from the jobs API:

| run | pytest step | job total |
|---|---|---|
| `34723036741` | 12 m 43 s | 14 m 02 s |
| `34722328111` | 12 m 59 s | 14 m 26 s |
| `34721531780` | 12 m 17 s | 13 m 38 s |
| `34712675646` | 12 m 37 s | 14 m 24 s |
| `34711343772` | 12 m 49 s | 15 m 15 s |
| `34698963428` | 12 m 47 s | 14 m 10 s |
| `34696231293` | 12 m 44 s | (failed on tests, not time) |
| `34750116081` *(2026-09-13)* | **13 m 07 s** | 13 m 30 s |
| `34750680910` *(2026-09-13, `f7e4fc8`)* | 8 m 00 s | **failed on tests, not time** — a markdown-only commit; log unreachable from this machine |
| `35990733980` *(2026-09-24, #97)* | **13 m 10 s** | 14 m 46 s |

Stable — ±20 s across the seven 2026-09-12 runs. Against `timeout-minutes: 20` that is **roughly
six minutes, or 30 %, of headroom**, at about 0.53 s per test over 1,440 tests.

The eighth row is the day after, on a markdown-only change, and it is the **highest of the eight** —
but only 8 s above the previous maximum, so read it as the top of the noise band and **not** as a
trend. It is recorded because the point of this finding is that the band's *ceiling* is what meets
the cap, and one number is not a slope: the next session to measure should add a row rather than
re-derive the table.

**2026-09-24, two more rows.** The #97 run is
the new maximum, 3 s above the last — the ceiling is creeping, still inside noise. The other row
matters more: **`f7e4fc8` went red on tests** on a markdown-only commit, eight minutes in, and went
unnoticed for eleven days because the board said CI was green. It is the second intermittent red in
this lane after #97's own; #97 is now fixed and the next run is green, which fits but does not prove
that #97 was the cause. The log is readable in a browser: run `34750680910`. (by @assistant)

What makes it worth a number rather than a shrug is the history. The same margin closed silently
once already: the `suite` job timed out on **every push** for an unknown stretch before card #86,
and nobody read it as a timeout because `concurrency.cancel-in-progress` renders the death as
`cancelled`. Cards #82, #83, #84, #89, #91, #92, #94–#99 and #7 are still open; #83 alone carries
seventeen boxes. Six minutes is about 680 more tests.

**The cancels currently on this branch are genuine supersedes, not disguised timeouts** — checked,
and the five are 2 m 36 s, 3 m 42 s, 5 m 21 s, 5 m 44 s and 11 m 25 s, none near the cap. Stated so
the next reader does not re-audit it. See [[a-workflow-that-passes-locally-may-never-have-run]].

## Done when

- [x] **F2's two facts are written onto #95**, which owns the decision: that branch protection
      returns 403 on this plan, and that its first option is therefore unavailable. This is the
      cheap half and it unblocks someone else's card rather than this one. **Done 2026-09-13** —
      #95's second box now strikes the protection option with the 403 beside it, and carries F1's
      shadowing as a caveat against choosing that route if the plan ever changes.
- [ ] **Decide what happens to the `pull_request` trigger, and record why.** Three options, none
      free: (a) drop `pull_request` from `on:` — a private repository takes no fork PRs, so the
      guard protects against a case that cannot occur, and the duplicate names vanish; (b) keep it
      and rename the jobs per event, so a skipped check never shares a name with a real one;
      (c) keep it as-is and write the hazard into `docs/QA-PROTOCOL.md` so the next reader of a PR
      knows which rows to believe. (a) is smallest and (b) is the one that survives the repository
      going public
- [ ] **Say what the timeout should be, with the measurement beside it.** Either raise
      `timeout-minutes` on `suite` with the 14-minute median recorded next to the new number, or
      state the deliberate decision to hold it at 20 and let a future overrun be the signal that
      the slow lane (#7) is overdue. **Do not raise it silently** — the cap is the only thing that
      currently reports suite growth at all
- [ ] **Whichever is chosen, the `cancelled`-means-timeout trap is named once in the workflow.**
      One comment beside `concurrency:`. It has cost this project a real audit already and the
      file does not mention it. **And name its automation-facing twin**: `gh run watch <id>
      --exit-status` returns **exit 0 on a cancelled run** — measured 2026-09-13, when this card's
      own filing commit was superseded by the next push and the watcher reported success while the
      `suite` job had been killed mid-`pytest`. Anything that gates on that exit code reads a
      cancel as a pass, which is the same mistake as reading the Actions tab for red

## Runnable check

```bash
# F1 — the duplicate names and which is later
gh pr view 6 --json statusCheckRollup -q '[.statusCheckRollup[]|{name,conclusion}]'

# F2 — the plan, not the setting
gh api repos/AN-Hy-tech/hydride-storage-prediction/branches/main/protection

# F3 — the pytest step's own duration, not the run's
gh api repos/AN-Hy-tech/hydride-storage-prediction/actions/runs/<id>/jobs \
  -q '.jobs[]|select(.name|startswith("Suite"))|.steps[]|select(.name|startswith("pytest"))'
```

## Traces to

`docs/PRD-inverse-design.md` — AC-1. Found while compacting the Phase H documentation set
(2026-09-13). #95 owns the `main` half of F2; #7 owns the slow lane F3 is waiting for; #86 is where
the 20-minute cap and the `-m "not slow"` split were decided, and neither is reopened here.

## Narrative

- 2026-09-13: Filed from a CI audit run against the GitHub API rather than the workflow file, which
  is the only way F1 and F3 are visible — the YAML says what *should* happen and the jobs API says
  what did. F1 was the surprise: the `if:` guard reads as "don't run twice" and is in fact "run
  once and publish a second, later, empty result under the same name". Deliberately filed rather
  than fixed, because all three findings end in a decision with a cost — a trigger removed, a cap
  raised, a hazard accepted — and none of them is currently failing. (by @assistant)
