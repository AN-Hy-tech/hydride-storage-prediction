# Phase H — the open findings, in priority order

**An index, not a source.** One line and a pointer per finding; the card owns the detail and its
`priority:` owns the band. A *finding* is a card not `done` **or an unticked box on a `done` card**
([../CONTEXT.md](../CONTEXT.md)). Every such card sits in the top folder of
[../kanban-hardening/](../kanban-hardening/); closed cards are in `archived/`. **Nothing enforces
this file**, so distrust a row older than its card, and rebuild it from:

```bash
S=.claude/skills/kanban-ai/scripts; bash $S/list_all_cards.sh kanban-hardening/
grep -H "^priority:" kanban-hardening/[01]*.md
```

**Bands by blast radius, not size** (*Priority band*, [../CONTEXT.md](../CONTEXT.md)). P1 can make
something published wrong · P2 blocks the objective, a user-facing predictor · P3 blocks the
unfreeze · P4 is accepted debt with a named owner. Cheapest first within a band. Re-ranked
2026-09-26: #94 P1→P2 (it fails a batch, it publishes nothing wrong), #7's portable-artifact half
P4→P2, #68 P1→P4 (its prose half is fixed).

## P1 — can make something published wrong

| # | Finding | Cost | State |
|---|---|---|---|
| **104** | The seeded LOACO run is **not reproducible**: two runs moved three families (Mg −0.338 → −0.508, macro 0.273 → 0.256). Cause fixed 2026-09-26 (the label screen's forest now runs on one thread); AC-1 still matches `v3` | probes + 2 × 5 h | `doing`. Owed: a `train` probe pair and **the maintainer's** LOACO repeat (board `▶` block) |

## P2 — blocks the user-facing predictor

| # | Finding | Cost | State |
|---|---|---|---|
| **7** *(half)* | **No portable artifact:** `artifacts/` is gitignored, so `v3` exists on one machine and a fresh clone's service refuses to start | part of #7 | `backlog`, unblocked |
| **83** | Model card. Built and served (`/v1/evidence`, `app/pages/1_Model_card.py`, the transfer interval) | 1.5 d | `doing`. Owed: the per-row width table (its population is a decision) and the one-run-or-spread question, which waits on #104's repeat |

## P3 — blocks the unfreeze

**Empty since 2026-09-24:** all four unfreeze bullets hold. The freeze is held by the maintainer's
decision until S7 is finished and these findings are triaged ([FREEZE.md](FREEZE.md) § Unfreeze
condition). Reorganising this file is not that triage.

| # | Finding | Cost | State |
|---|---|---|---|
| **36** | The five ADRs; `docs/adr/README.md` reserves `0001`–`0005`. S8, **not** an unfreeze condition | 1 d | `backlog`, unblocked |

## P4 — accepted debt, named owner

| # | Finding | Owner / state |
|---|---|---|
| **102** | One decision (how a refusal names its offenders) is taken in 22 modules: four renderings, two truncation limits | 0.5 d, unblocked |
| **101** | Every PR carries two **skipped** checks shadowing the real ones; branch protection is 403; the fast lane has ~6 min headroom | unblocked |
| **95** | The freeze is unenforced on `main` (`check_freeze.py` is not there). Closes when PR #6 merges, after the lift | unblocked |
| **100** | A render test failed once after the slow tests. Mechanism removed; six full runs green; a red run now writes `reports/test-failures/`. Stays open by the maintainer's ruling until a failure is fixed | `doing` |
| **92** | The stage line and the stage map are checked by nobody | unblocked, six boxes |
| **91** | The prediction record, and replay as its consumer (HG-5, post-freeze) | startable, eight boxes |
| **7** *(rest)* | CI slow lane: full retrain, artifact upload, promotion. Four guarantees run on no push | unblocked, ten boxes |
| **68** | Nothing enforces the open-box-on-`done` convention; this file is the mitigation | box on a `done` card |
| **1** | The conda lock **cannot be re-solved** (`defaults` is 403, and supplies `python` and `numpy`); three remedies, **the maintainer's choice**. `matplotlib` installed twice | maintainer; boxes on a `done` card |
| **30** | LOACO has no resume and is silent until it ends; per-class intervals now exist (`loco-intervals.csv`), so the third box can be re-read | #83 owes the written limit |
| **14** | `Ce1Ni4Cr1` at 4.73 wt% (H/M 3.339) is an impossible label in `val`; L3 forbids removing it. Stated on #83's page | no action |

**Not on this list:** new unfreeze conditions (a finding gets a card marked *not an unfreeze
condition*, never a fifth bullet), decisions settled in PRD §7, and `~~struck~~` boxes (#34, #86),
which are closed and kept for their reasoning.
