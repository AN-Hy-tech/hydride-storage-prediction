# HydMS Inverse Design — Board

> ## FROZEN
>
> **This board is not the active board.** An emergency hardening phase
> ([docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md)) has the inverse-design programme suspended.
> Every card here must stay `backlog`; `scripts/check_board.py` fails the build otherwise, and
> `scripts/check_freeze.py` rejects any change under `kanban/`.
>
> The active board is [../kanban-hardening/](../kanban-hardening/). What is frozen, why, and the
> exact unfreeze condition: [docs/FREEZE.md](../docs/FREEZE.md).
>
> **Cards 1–37, 44, 48, 49 and 68 moved to the hardening board**, ids unchanged — the two directories
> share one id space, so the `blocked_by` edges and the layer/phase tables below still resolve. The
> counts and day totals below describe the *original* 68-card board and are left as written; they are
> history, not a current inventory.

67 tickets decomposed from [`docs/PRD-inverse-design.md`](../docs/PRD-inverse-design.md), plus
**#68** added since (the fast-lane seed, which the decomposition could not see until the board
existed). Every ticket is ≤ 1 day, ends in a runnable check, and traces back to a PRD user story,
acceptance criterion or risk.

**Total: 60.5 developer-days. Critical path: 20.5 days.**
The gap between the two is parallelism — for one developer the number is 60.5.

> The PRD estimated 36–51 days. Decomposition surfaced ~9 days the phase-level estimate did
> not carry, most of it the *full CI from the start* decision (tickets 5–7) and the data-layer
> defects the audit found (tickets 10, 12, 14). This is the honest number.

---

## Why tickets are cut by layer, not by phase

The PRD's phases (0 → F → 1 → T → A → B) are a **schedule**. Cutting tickets along a schedule is
a temporal decomposition, which forces the same knowledge to be shared across the split — the
subtlest form of information leakage.

Architectures A and B differ only in how candidates are **proposed** and how results are
**selected**. What happens in between is identical:

| | Proposes | Evaluates | Selects |
|---|---|---|---|
| **A** | enumerate a grid | LCB, cost, novelty, physics verdicts | sort by LCB |
| **B** | NSGA-II evolve | **identical** | non-dominated sort |

So the deep module is **the evaluator** (ticket 51), and **Search is a seam** (ticket 52) with
two implementations. Cut by phase, the filters, the ElMD call, the cost table and the LCB
computation would each be written for A and rewritten for B — and the second copy would drift.

Phases still exist. They are the *order* the layers are built in, carried as a tag.

---

## Layers

Each layer owns one kind of knowledge. Nothing outside it needs to know that knowledge.

| Layer | Owns | Cards | Days |
|---|---|---:|---:|
| **L0 Foundation** | environment, config, artifact store, gates, CI | 8 | 6.5 |
| **L1 Data** | source schemas, merge keys, split protocol, CleanLab | 8 | 6.0 |
| **L2 Descriptors** | element property tables, statistics, the 22-feature contract | 8 | 6.5 |
| **L3 Surrogate** | model choice, scaler, quantiles, conformal calibration | 17 | 12.5 |
| **L4 Screens** | physics windows, AD ceiling, novelty, cost + HHI | 9 | 8.5 |
| **L5 Search** | *how candidates are proposed* — Enumerate ∥ Evolve | 11 | 10.5 |
| **L6 Delivery** | Streamlit, ranked CSV, thesis figures | 4 | 6.5 |
| **L7 Evidence** | glossary, ADRs, the Chapter 1 revision | 3 | 3.5 |

## Phases

| Phase | Cards | Days | Ends with |
|---|---:|---:|---|
| **P0** — Foundation & provenance | 9 | 7.0 | CI running; feature provenance resolved |
| **P1** — Hardening Chapter 1 | 29 | 24.0 | `artifacts/v1` promoted; Chapter 1 revision written |
| **PT** — Thermodynamics | 6 | 4.0 | ΔH/ΔS surrogates + van 't Hoff map |
| **PA** — Screen-and-Rank | 15 | 13.5 | Ranked AB₂/AB₅ candidate list + app |
| **PB** — Multi-objective EA | 9 | 12.0 | Pareto fronts + convergence + stability |

---

## Phase 1 is Chapter 1 hardening — and it has two halves

**Code half** (tickets 9–34): fix the four broken pipeline links, remove the three validation
leaks, re-run selection once, produce a calibrated surrogate and promote `artifacts/v1`.

**Prose half** (ticket 37): the written account — what exists, what was wrong, and the corrected
numbers beside the published ones.

The prose is **blocked on the code** (37 ← 25, 29, 30, 34). You cannot honestly write "here is
what was wrong and here is the corrected number" before the corrected number exists. That
ordering is also what turns the audit into a contribution rather than an apology.

---

## Gates

PRD §10's acceptance criteria are executable, not remembered. Each is a ticket, registered in
the harness (ticket 5) and enforced by CI.

| Gate | Ticket | Checks |
|---|---|---|
| AC-1 | 32 | same seed → identical metrics |
| AC-2 | 21 | featuriser matches CBFV to 1e-9 on all 1,279 formulae |
| AC-3 | 31 | conformal coverage matches nominal |
| AC-4 | 33 | known alloys round-trip through `predict()` |
| AC-5 | 41 | predicted ΔS clusters near −130 J/(mol H₂·K) |
| AC-6 | 30 | leave-one-alloy-class-out R² reported |
| AC-7 | 57 | no candidate published without ElMD distance **and** interval width |
| AC-8 | 56 | ≥ half the top-20 inside the AD ceiling and the VEC window |

CI splits fast/slow because retraining is not a per-push job:
**fast lane** (ticket 6) runs lint, tests and gates against the published artifact on every push;
**slow lane** (ticket 7) retrains on dispatch and weekly, and promotes a version only on a full
gate pass. Promotion is a manifest pointer, so rollback is a one-line change, not a retrain.

---

## Two hard gates that block everything behind them

- **#8 — Provenance spike.** Resolves which element-property table produces each of the 22
  features. `extract_features_cbfv.py:31` says `elem_prop='magpie'`, but the selected names are
  Oliynyk- and JARVIS-style. **You cannot reimplement a table you have not identified.** If any
  of the 22 is unaccounted for, tickets 16–21 stay blocked.
- **#21 — Featuriser parity (AC-2).** If the reimplementation does not reproduce CBFV to 1e-9,
  every downstream model trains on subtly different features than `REPORT.md` describes. If this
  fails, the reimplementation is wrong — not CBFV.

---

## Start here

Two tickets have no blockers:

1. **#1** — Pin and lock the `Project` conda environment
2. **#2** — Scaffold the `hydms` package with pyproject and GPL-3.0 licence

Then **#8** (the provenance spike) as early as possible — it is on nothing's critical path but it
gates the entire descriptor layer, so a failure discovered late is expensive.

## Critical path (20.5 days)

```
#2  scaffold        →  #3  config        →  #9  loaders      →  #10 keyed merge
→ #13 splits        →  #14 CleanLab      →  #24 selection    →  #25 old-vs-new
→ #26 CatBoost MQ   →  #27 MAPIE         →  #28 predict()    →  #30 LOCO CV
→ #48 AD ceiling    →  #51 EVALUATOR     →  #52 Proposer     →  #59 pymoo problem
→ #60 constraints   →  #61 subset sweep  →  #62 hypervolume  →  #66 Pareto app
```

Note that #30 (leave-one-alloy-class-out) sits on the critical path because #48 derives the
applicability-domain ceiling from it. The honest validation number is not a reporting
afterthought — it is an input to the search.

---

## Using the board

```bash
S=.claude/skills/kanban-ai/scripts

bash $S/view_board.sh kanban/            # full board by status
bash $S/show_blocked.sh kanban/          # what is waiting on what
bash $S/search_by_tag.sh kanban/ l4      # one layer
bash $S/search_by_tag.sh kanban/ p1      # one phase
bash $S/search_by_tag.sh kanban/ AC-3    # everything touching one acceptance criterion
bash $S/search_by_tag.sh kanban/ R1      # everything mitigating one risk
bash $S/list_all_cards.sh kanban/        # id|status|blocked_by|title
```

Move a card by editing `status` in its frontmatter: `backlog → todo → doing → done`.
Before moving to `doing`, every id in `blocked_by` must be `done`.
Append to `## Narrative` when something is learned — those notes are the record of *why*, and
they are what ticket 37 and the ADRs will be written from.
