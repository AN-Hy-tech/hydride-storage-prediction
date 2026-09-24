# Phase H — the open findings, in priority order

**This is an index, not a source.** Every row is one line plus a pointer; the card owns the detail
and wins on sight. It exists because Phase H's open work is currently spread across three places a
newcomer has no reason to look in — `backlog` cards, **unticked boxes on `done` cards**, and the
board's `▶ Next action` block — and the middle one is invisible to every tool this project has.

**Nothing enforces this file.** `scripts/check_board.py` validates the links and nothing else; it
does not read checkboxes (#68) and it has no opinion about priority. Treat a row older than the card
it names as wrong. Rebuild the raw material with:

```bash
S=.claude/skills/kanban-ai/scripts
bash $S/list_all_cards.sh kanban-hardening/ | grep -v '|done|'     # open cards
for f in kanban-hardening/[01]*.md; do                              # findings on closed cards
  grep -q '^status: done' "$f" && grep -q '^\s*-\s*\[ \]' "$f" && echo "$f"
done
```

**Priority is by blast radius, not by size.** P1 is anything that can make a *published* number or
sentence wrong. P2 is what blocks Phase H's stated objective — a user-facing predictor. P3 is what
blocks the unfreeze. P4 is accepted debt with a named owner. Within a band, cheapest first.

---

## P1 — can make something published wrong

| # | Finding | Cost | State |
|---|---|---|---|
| **97** | `comparison.py:703` sorted a tied key with pandas' default **unstable** quicksort. **Fixed 2026-09-24** with `kind="stable"`; the regenerated document is byte-identical, and a new test widens the tie until the old sort goes red. The only such sort in `hydms/` | done / runner | `doing` until `gh run list` is green, its last box |
| **99** | *"Only 39 test rows sit above 500 K"* is `REPORT.md`'s count over the archival 247-row test split. Measured now: **130 of 893**. Three production docstrings and two tests still carry the old number | 0.25 d | `backlog`, unblocked |
| **68** | `scripts/check_board.py` has **no done-card checkbox rule** and the prose said it did. **Prose half cleared 2026-09-13** — board README, `CLAUDE.md` and #81 corrected; the surviving claim count was two, not six. **Still owed:** nothing enforces the convention, and this index is a mitigation, not a check | done / 0.25 d left | box on a `done` card |
| **96** | `--report` on `surrogate.calibrate` is both an output *and* an input path: redirecting it silently falls back to CatBoost defaults, and `--save` then persists that as a `deployed fit`. It has produced a wrong conformal correction once already | 0.25 d | `backlog`, unblocked |
| **94** | A crossed band raises where it should refuse — a measured-23 %-likely crossing is passed through unclipped by design, and the delivery path's answer to it is an exception rather than a refusal | 0.25 d | `backlog`, unblocked |

## P2 — blocks the objective (a user-facing predictor)

| # | Finding | Cost | State |
|---|---|---|---|
| **82** | `app/main.py` as an **HTTP client** of the service, handing each `PredictionResult` to a `hydms.figures` builder. Must not acquire a matplotlib call of its own | 1 d | `backlog`, **unblocked — this is the opening move** |
| **84** | Batch CSV screening page. Needs a *batched call in the library*: a served prediction is 66–78 ms and linear in the rows, and the published limit is 256 | 1 d | blocked by #82 |
| **98** | `loco.py:595` writes four tables but not `evaluation.out_of_fold`, so LOACO leaves ten class averages and no scored rows — and `parity()` refuses fewer than two readings. **#83's parity panel cannot be built from committed evidence.** Needs a LOACO run, which is the maintainer's | 0.5 d + a run | `backlog`, unblocked |
| **83** | Model card: honest metrics and stated limits. Seventeen boxes, and it is where #14's impossible label and #30's interval-free per-class scores are owed a written limit | 1.5 d | blocked by #29, #30, #82, #89 |

## P3 — blocks the unfreeze

The unfreeze condition is four bullets and **three already hold**: the gates are green, `current`
points at `v3`, and `docs/API.md` is published. The fourth is **#37**, waiting on **#89 alone**.

| # | Finding | Cost | State |
|---|---|---|---|
| **89** | `REPORT.md` versus the artifacts it cites — the reconciliation table. Until it exists, cite the committed CSVs under `reports/`. Independent of S7, so it runs beside it | 1 d | **unblocked** — #29 and #30 are both `done` |
| **37** | Chapter 1 revision: what exists, what was wrong, what it is now. **The last unfreeze condition** | 1.5 d | blocked by #89 |
| **36** | The five ADRs. `docs/adr/README.md` reserves `0001`–`0005` for them and records why #85 took `0006` | 1 d | `backlog`, unblocked |

## P4 — accepted debt, named owner

| # | Finding | Owner | Note |
|---|---|---|---|
| **7** | The CI **slow lane**: full retrain, artifact upload, version promotion. Four guarantees currently run on **no push**. Also owes a *portable* artifact — `artifacts/` is gitignored, so `v3` exists on one machine and a fresh clone has no model | **unblocked** — #4 and #6 are both `done` | ten open boxes |
| **102** | One decision — how a refusal sentence names its offenders — is taken in **22 modules** independently and has drifted into **four** renderings and **two** truncation limits. `docs/REFUSALS.md` is generated from those sentences | 0.5 d | `backlog`, unblocked |
| **101** | CI: every PR carries two **skipped** checks that shadow the real ones by name; branch protection is **403 on this plan**; the fast lane has ~6 min of headroom against a cap that already killed three pushes | unblocked | filed 2026-09-13 |
| **95** | The freeze is **unenforced on `main`** — `check_freeze.py` does not exist there. PR #7 edited six frozen cards and was reported green. Closes when PR #6 merges, which is after the freeze lifts | unblocked | #101 supplies the 403 fact its second box needs |
| **100** | A render test passes alone and fails after the slow tests. The mechanism is removed (`figures/render.py` no longer touches `pyplot` or a global backend); **five full runs since are green, so no traceback exists** and the card's second box stays unticked on purpose | `doing` | do not spend a sixth run on it |
| **92** | The stage line and the stage map are checked, not remembered. Nothing currently reads either | unblocked | six boxes |
| **91** | The prediction record, and replay as its consumer | blocked by #76, #78 (both `done`) — startable | eight boxes |
| **1** | Two boxes, both open: the conda lock **cannot be re-solved** (the `defaults` channel is 403 and supplies 95 of 248 packages, `python` and `numpy` among them) — three remedies, and the choice is **the maintainer's, do not start one unasked**. And `matplotlib` is installed **twice** in `Project`, with the export naming the version that is not running | maintainer | boxes on a `done` card |
| **30** | Three boxes, all deliberate: the 4.7-hour LOACO run has **no resume**; it is **silent**, so a hung run is indistinguishable from a working one until the end; and the per-class scores carry **no interval** — which the model card must not imply otherwise | #83 owes the written limit | boxes on a `done` card |
| **14** | `Ce1Ni4Cr1` at 4.73 wt% is H/M 3.339 — an **impossible label sitting in `val`**, so it feeds early stopping and every validation figure. L3 forbids removing it, correctly. It is a **stated limit**, owed by #83 | #83 | box on a `done` card, no action here |

---

## What is deliberately not on this list

**The unfreeze condition does not grow.** Every card filed during Phase H says so on its own face,
and #101 and #95 repeat it. A finding found while working Phase H gets a card marked *"NOT an
unfreeze condition"*; it does not become a fifth bullet. See
[FREEZE.md](FREEZE.md) § Unfreeze condition for the four that are fixed.

**Settled decisions are not findings.** Generative models, descriptor inversion,
Optuna-instead-of-pymoo and patching the old pipeline in place are rejected with reasons in
`docs/PRD-inverse-design.md` §7. Bring new evidence or move on.

**Struck-through boxes are closed.** #34's three and #86's three read as open to a `grep` but are
each `~~struck~~` with the resolution beside them, kept so the reasoning that dissolved them stays
legible. They are history, and they are why the command at the top of this file needs a human
reading it rather than a count.
