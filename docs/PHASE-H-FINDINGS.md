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
| **104** | The seeded LOACO run is **not reproducible run to run**: two full runs with seed 42 and an unchanged fit path agree on seven families and move three (Mg −0.338 → −0.508, macro 0.273 → 0.256). The transfer number is in the thesis, the domain screen and `docs/API.md`; no verdict moved. AC-1 covers only the deployed fit, so no gate saw it | 0.5 d + probes | `doing`. **Cause found and fixed 2026-09-26**: the label screen's forest predicted on many threads, and its sum drifts at the last digit. It now runs on one thread, and AC-1 still matches `v3` exactly. Owed: a `train` probe pair and the maintainer's full LOACO rerun |
| **99** | *"Only 39 test rows sit above 500 K"* is `REPORT.md`'s count over the archival 247-row test split. Measured now: **130 of 893**. Three production docstrings and two tests still carry the old number | 0.25 d | `backlog`, unblocked |
| **68** | `scripts/check_board.py` has **no done-card checkbox rule** and the prose said it did. **Prose half cleared 2026-09-13** — board README, `CLAUDE.md` and #81 corrected; the surviving claim count was two, not six. **Still owed:** nothing enforces the convention, and this index is a mitigation, not a check | done / 0.25 d left | box on a `done` card |
| **96** | `--report` on `surrogate.calibrate` is both an output *and* an input path: redirecting it silently falls back to CatBoost defaults, and `--save` then persists that as a `deployed fit`. It has produced a wrong conformal correction once already | 0.25 d | `backlog`, unblocked |
| **94** | A crossed band raises where it should refuse — a measured-23 %-likely crossing is passed through unclipped by design, and the delivery path's answer to it is an exception rather than a refusal. **Since #84, one crossed row fails a whole `predict_many` call**, so it fails a batch request and a page chunk of up to 4,096 rows. The route loop failed the same way before #84 | 0.25 d | `backlog`, unblocked |


## P2 — blocks the objective (a user-facing predictor)

| # | Finding | Cost | State |
|---|---|---|---|
| **84** | ~~Batch CSV screening page~~ | — | **`done` 2026-09-26.** `predict_many` is in the library, and the route calls it once. 0.7–1.0 ms a row served, so the limit is now 4,096. The page is `app/pages/2_Batch_screening.py`. Leaves #94's crossed band as the one way a batch still fails whole |
| **83** | Model card: honest metrics and stated limits. Seventeen boxes, and it is where #14's impossible label and #30's interval-free per-class scores are owed a written limit. Its reconciliation link can now be satisfied (#89 is `done`) | 1.5 d | `doing`. **Built 2026-09-26**: Evidence Reader, `/v1/evidence(/parity)`, the page (`app/pages/1_Model_card.py`), and the transfer interval. Owed: the per-row width table (population is a decision) and the OPEN one-run-or-spread question, which waits on #104's repeat |

## P3 — blocks the unfreeze

**Empty since 2026-09-24.** All four unfreeze bullets hold: the gates are green, `current` points
at `v3`, `docs/API.md` is published, and **#37** is `done` (the author accepted the Chapter 1
revision, and #103 committed the artifact score it cites). **The freeze is held by the maintainer's
decision** until S7 (#82–#84) is finished and the findings on this page have been triaged. See
[FREEZE.md](FREEZE.md) §Unfreeze condition.

Still open in S8, and not an unfreeze condition:

| # | Finding | Cost | State |
|---|---|---|---|
| **36** | The five ADRs. `docs/adr/README.md` reserves `0001`–`0005` for them and records why #85 took `0006` | 1 d | `backlog`, unblocked |

## P4 — accepted debt, named owner

| # | Finding | Owner | Note |
|---|---|---|---|
| **7** | The CI **slow lane**: full retrain, artifact upload, version promotion. Four guarantees currently run on **no push**. Also owes a *portable* artifact — `artifacts/` is gitignored, so `v3` exists on one machine and a fresh clone has no model | **unblocked** — #4 and #6 are both `done` | ten open boxes |
| **102** | One decision — how a refusal sentence names its offenders — is taken in **22 modules** independently and has drifted into **four** renderings and **two** truncation limits. `docs/REFUSALS.md` is generated from those sentences | 0.5 d | `backlog`, unblocked |
| **101** | CI: every PR carries two **skipped** checks that shadow the real ones by name; branch protection is **403 on this plan**; the fast lane has ~6 min of headroom against a cap that already killed three pushes. `f7e4fc8`'s red run **was #97's sort tie**, read 2026-09-24 from the job-logs API (no browser needed). Every red run on the branch is now accounted for | unblocked | filed 2026-09-13 |
| **95** | The freeze is **unenforced on `main`** — `check_freeze.py` does not exist there. PR #7 edited six frozen cards and was reported green. Closes when PR #6 merges, which is after the freeze lifts | unblocked | #101 supplies the 403 fact its second box needs |
| **100** | A render test passes alone and fails after the slow tests. The mechanism is removed (`figures/render.py` no longer touches `pyplot` or a global backend); **five full runs since are green, so no traceback exists** and the card's second box stays unticked on purpose. **Corrected 2026-09-24: it has never failed on CI either.** Run `34716528657`, the traceback it was waiting on, was #97's tie. **2026-09-25:** every session that ends red now writes its tracebacks, the other Python processes alive, and the files edited mid-run to `reports/test-failures/`. The maintainer ruled it stays open until the failure is fixed | `doing` | the next session spends one full run on a quiet machine; if red, the fix starts from the record |
| **92** | The stage line and the stage map are checked, not remembered. Nothing currently reads either | unblocked | six boxes |
| **91** | The prediction record, and replay as its consumer | blocked by #76, #78 (both `done`) — startable | eight boxes |
| **1** | Two boxes, both open: the conda lock **cannot be re-solved** (the `defaults` channel is 403 and supplies 95 of 248 packages, `python` and `numpy` among them) — three remedies, and the choice is **the maintainer's, do not start one unasked**. And `matplotlib` is installed **twice** in `Project`, with the export naming the version that is not running | maintainer | boxes on a `done` card |
| **30** | Three boxes, all deliberate: the 4.7-hour LOACO run has **no resume**; it is **silent**, so a hung run is indistinguishable from a working one until the end; and the per-class scores carry **no interval** — which the model card must not imply otherwise | #83 owes the written limit. Since 2026-09-26 `loco --emit` writes per-family intervals (`loco-intervals.csv`) and the page shows them, so #30's third box can be re-read against that | boxes on a `done` card |
| **14** | `Ce1Ni4Cr1` at 4.73 wt% is H/M 3.339 — an **impossible label sitting in `val`**, so it feeds early stopping and every validation figure. L3 forbids removing it, correctly. It is a **stated limit**, and #83's page states it (2026-09-26) | #83 | box on a `done` card, no action here |

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
