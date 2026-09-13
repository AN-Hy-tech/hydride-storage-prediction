---
id: 95
status: backlog
priority: Normal
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l0]
---

# The freeze is unenforced on the default branch

**Stage S8 — Evidence and close** · **L0 Foundation** · Estimate: 0.25 d

> **Owns (hidden behind this module):** Whether a pull request can reach `main` without meeting the freeze.

**This card is NOT an unfreeze condition.** It was found by #93's CI audit and is filed so it has
an owner, not to widen `docs/FREEZE.md`. The unfreeze condition is fixed and stays fixed.

## Why this exists

`docs/FREEZE.md` says the freeze "is enforced, not remembered", and on this branch that is true:
`scripts/check_freeze.py` runs in the `hygiene` job and rejects any change touching the five denied
paths. **On `main` it is not true**, and the gap is total rather than partial:

| | `feat/phase-h-emergency-hardening` | `main` |
|---|---|---|
| Workflow | `.github/workflows/ci.yml` | `.github/workflows/integrity.yml` |
| Board check | yes (`check_board.py`) | yes (`check_board.py`) |
| **Freeze check** | **yes** | **`scripts/check_freeze.py` does not exist** |

`main` carries exactly three scripts — `check_board.py`, `spike_feature_provenance.py`,
`verify_environment.py` — because it has not moved since 2026-08-30, and every piece of freeze
machinery was written on the hardening branch afterwards.

**This is not theoretical.** PR **#7** (`claude/persist-vs-refit-resolved-dk4iss`, opened
2026-09-05) targets `main`, edits **six cards** under `kanban/` — the first entry in
`check_freeze.py`'s `DENIED` tuple — and is reported **green and MERGEABLE**, because the only
check it faces is the one that does not look for this. A reviewer going by the check marks would
see nothing wrong. The freeze's own enforcement story is what makes that dangerous: a reader who
has been told the freeze is executable will trust a green tick more than they would trust prose.

## What the real fix is, and why this card is small

**Merging PR #6 closes this entirely**: it deletes `integrity.yml`, brings `ci.yml` with the
`hygiene` job, and brings `check_freeze.py` itself. So this card is not "port the freeze check to
`main`" — that work exists and is sitting in an open pull request. The card exists because **until
that merge, the gap is real and undocumented**, and #6 does not merge until the freeze lifts.

That ordering is the awkward part and should be stated rather than discovered: the freeze is
enforced everywhere the work happens, and unenforced on the branch the work has not reached yet.

## Done when

- [ ] `docs/FREEZE.md` says, in its *For the next session* section, that the freeze is enforced on
      the hardening branch and **not** on `main`, that a PR targeting `main` therefore faces no
      freeze check, and that this closes when #6 merges. One paragraph; this is the cheap half and
      the one that matters
- [ ] **Decide whether anything guards `main` before then.** Options, none of them obviously right:
      ~~a branch-protection rule requiring a check `main` cannot run~~ — **this option does not
      exist on this repository**: the protection API answers 403 on this plan, and if the plan ever
      changed, the `pull_request` event's skipped check runs would satisfy a required check by name
      anyway. Both measured 2026-09-13; **#101 owns the numbers and the reproducing commands** and
      this box does not copy them. So the decision is between the remaining two: cherry-picking
      `check_freeze.py` and a minimal workflow onto `main`, which edits the default branch during a
      freeze whose whole point is to stop drive-by edits; or accepting the gap on the grounds that
      exactly one PR targets `main` and it is being closed. **Record the reasoning either way** —
      the next person to notice this will otherwise re-open it
- [x] PR **#7** is closed unmerged, and the reason is on the cards rather than only in the PR
      thread. **Closed 2026-09-12T17:22:36Z** — `state=CLOSED`, `mergedAt=null`, so `main` was not
      touched. The branch `claude/persist-vs-refit-resolved-dk4iss` is deliberately **left on
      origin** at `d07a66e`: it is the fullest record of the original reasoning, and #34 keeps the
      framing precisely because the dissolution is only legible beside it. The rationale is also in
      the PR thread, but the cards are the authority. **#6 is now the only open PR.**
- [x] A check of the remaining open PRs against the deny-list, so this is answered as a set rather
      than one PR at a time: `gh pr list --state open --json number,files`. **Done 2026-09-12: the
      set is now one.** #6 is the hardening branch itself, targets `main`, and is the PR whose merge
      *closes* this card. Nothing else is open, so the two boxes below are the whole of the
      remaining exposure and it is bounded by a single pull request nobody intends to merge early.

## Runnable check

```bash
gh pr list --state open --json number,headRefName,baseRefName,mergeable
git ls-tree origin/main --name-only scripts/      # check_freeze.py absent == the gap is open
```

## Traces to

`docs/FREEZE.md` — the enforcement claim; card #72 owns the freeze charter and the two-board CI
enforcement this extends

## Narrative

- 2026-09-12: Created by the #93 session, from a question about red runs in the Actions tab. The
  red runs were all historical and needed nothing. **What the audit found instead was a green
  one** — a mergeable PR that edits the frozen board and faces no freeze check, because it targets
  a branch that predates the freeze. Worth keeping as a shape: "is anything red?" is a weaker
  question than "is anything green that should not be?", and only the second one finds a check that
  is *absent* rather than failing. See [[a-check-that-reads-a-gitignored-path-never-runs]] — same
  failure mode, different mechanism: there the check ran and read nothing, here the check does not
  exist on the branch being checked. (by @assistant)

- 2026-09-12 (later): PR #7 closed unmerged at 17:22:36Z, with the reasoning in the thread and on
  #34 and #36. **What is left of this card is the part that cannot be closed by an act**: `main`
  still has no freeze check, and it gets one only when #6 merges, which the freeze itself prevents
  until it lifts. So the honest state is not "fixed" but "bounded" — the exposure is one pull
  request, and that request is the fix. The first box, the paragraph in `docs/FREEZE.md`, is
  therefore the one that matters most and is the cheapest: until it is written, the only place this
  gap is recorded is a card, and a card is not what a reviewer reads before clicking merge.
  (by @assistant)

- 2026-09-13: #101's CI audit closed the first of this card's three options rather than answering
  the card: branch protection returns **403** on this plan, so "a branch-protection rule" is not
  something anyone here can choose. Recorded in the box rather than in a handoff, because the next
  person to reach this card would otherwise spend the same request finding out. (by @assistant)
