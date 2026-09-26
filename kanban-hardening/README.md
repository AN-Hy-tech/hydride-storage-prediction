# The hardening board — Phase H

**This is the active board.** [../kanban/](../kanban/) is frozen; see [../docs/FREEZE.md](../docs/FREEZE.md).
**The top folder holds every card with open work:** each card not `done`, and each `done` card
that still carries an unticked box (a *finding*, [../CONTEXT.md](../CONTEXT.md)). Closed cards are in
[archived/](archived/), same ids, same frontmatter.

> ## ▶ Next action — as of 2026-09-26 (the docs compaction; #83 and #104 `doing`)
>
> **Take the open findings in band order, cheapest first:** **#99** (P1, 0.25 d), then **#96**
> (P1, 0.25 d), then **#94** (P2, 0.25 d; one crossed band still fails a whole `predict_many`
> batch). The ranked list is [../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md).
> **#83** waits on the per-row width table (its population is a decision) and on #104's repeat.
>
> **The LOACO repeat (#104; heavy, the maintainer runs it).** About five hours each, one after the
> other, on an idle machine with sleep disabled (`docs/RUNNING-THE-FIT.md` Step 10). Run A writes
> the committed tables, run B a gitignored scratch directory, then the diff. Only
> `loco-chosen.csv`'s `seconds` column may differ. **Anything else moving is a new #104 finding,
> not a failed run.** Commit A's tables either way, then the regeneration chain in Step 10.
>
> ```powershell
> & "C:\Users\Asus\miniconda3\envs\Project\python.exe" -u -m hydms.surrogate.loco --target capacity | Tee-Object -FilePath .\reports\_loco-run-a.log
> & "C:\Users\Asus\miniconda3\envs\Project\python.exe" -u -m hydms.surrogate.loco --target capacity --report .\reports\_loco-b | Tee-Object -FilePath .\reports\_loco-run-b.log
> foreach ($t in 'loco-per-class','loco-summary','loco-out-of-fold','loco-chosen') { git diff --no-index --stat "reports/loco/$t.csv" "reports/_loco-b/$t.csv" }
> ```
>
> **Traps.** `apidoc-examples.json` stores the over-limit request *shortened*, with
> `candidates_total` beside it; do not "fix" it back to 4,097 rows. Any change to a table the
> Evidence Reader serves changes `evidence_sha256`: re-run `apidoc --probe --emit` after
> `loco --emit` or `evaluate`.
>
> **This block is one handoff, never a log.** Replace it when you close a card, and move the one it
> replaces to the top of [../docs/archive/HANDOFFS-PHASE-H.md](../docs/archive/HANDOFFS-PHASE-H.md)
> in the same commit. The cards win on sight.

| Looking for | Read |
|---|---|
| What is still wrong, in priority order | [../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md) |
| Why the phase exists, the leaks, the stage order, the gates | [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) |
| What is frozen and the unfreeze condition | [../docs/FREEZE.md](../docs/FREEZE.md) |
| What a card must prove before it is done | [../docs/QA-PROTOCOL.md](../docs/QA-PROTOCOL.md) |
| Why a past decision went the way it did | [../docs/archive/HANDOFFS-PHASE-H.md](../docs/archive/HANDOFFS-PHASE-H.md) |

---

## Two directories, one id space

| Directory | Ids | State |
|---|---|---|
| `kanban-hardening/` (+ `archived/`) | 1–37, 44, 48, 49, 68–106 | **Active** |
| `../kanban/` | 38–43, 45–47, 50–67 | **Frozen** — every card stays `backlog` |

`blocked_by` reaches across both; `scripts/check_board.py` loads them, subfolders included, as one
graph. Ids were preserved when cards migrated. #44, #48 and #49 were pulled out of the frozen PA
phase because they are what lets the interface refuse. **Next free id: #107** (2026-09-26) —
scan both directories for `max(id) + 1` rather than trust this line.

## Layers

| Layer | Owns | Cards |
|---|---|---|
| **L0 Foundation** | environment, config, artifact store, gates, CI, test infrastructure | 1–7, 68, 69–74, 86 |
| **L1 Data** | schemas, merge keys, canonical composition key, splits, CleanLab | 9–15, 87 |
| **L2 Descriptors** | element property tables, statistics, the 22-feature contract | 8, 16–22 |
| **L3 Surrogate** | model, scaler, quantiles, conformal calibration, validation protocol | 23–34, 88 |
| **L4 Screens** | the screen verdict, the AD ceiling, novelty | 44, 48, 49, 90 |
| **L6 Delivery** | the prediction contract, the API, the app, the charts | 75–84, 91 |
| **L7 Evidence** | glossary, ADRs, reconciliation, Chapter 1 | 35, 36, 37, 85, 89 |

L5 Search is entirely frozen: proposing candidates is inverse design.

## Stage → card map

| Stage | Cards | Days |
|---|---|---:|
| **S0** Freeze & tooling | 72 | 1 |
| **S1** QA foundation | 69, 70, 5, 71 | 2 |
| **S2** Data layer | 3, 9, 10, 11, 87, 12, 13, 14, 15 | 7 |
| **S3** Descriptor layer | 16, 17, 18, 19, 20, 21, 22 | 6 |
| **S4** Surrogate layer | 23, 24, 25, 88, 26, 27, 28, 29, 30, 31, 32, 33, 34, 97, 98, 104, 105, 106 | 13 |
| **S5** Guard rails | 44, 48, 49 | 2.5 |
| **S6** Delivery: contract + API | 75, 76, 77, 78, 79, 80 | 5 |
| **S7** Delivery: interface | 81, 82, 83, 84, 100 | 3.5 |
| **S8** Evidence & close | 89, 85, 86, 35, 36, 37, 99, 101, 102, 103 | 5 |
| **No stage** | 1, 2, 4, 6, 7, 8, 68, 73, 74, 90, 91, 92, 93, 94, 95, 96 | — |

Days are the original plan, deliberately not re-added. **Cards from #90 on were found during the
phase, and none is an unfreeze condition.** The stage is the bold line under a card's title; the
`S1`…`S12` in `tags:` are PRD user stories, not stages ([../CONTEXT.md](../CONTEXT.md) § The board).
Nothing checks this table against the cards yet; that is #92.

## Gates

Registered in the harness (#5) with the three frozen criteria; ask it: `python -m hydms.gates list`.
Failure conditions: [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §4.

| Gate | Card | | Gate | Card |
|---|---|---|---|---|
| **HG-1** leak sentinels | 71 | | AC-1 seed reproducibility | 32 |
| **HG-2** no bare numbers | 77 | | AC-2 featuriser parity | 21 |
| **HG-3** transport parity | 79 | | AC-3 conformal coverage | 31 |
| **HG-4** hygiene | 86 | | AC-4 known-alloy round-trip | 33 |
| | | | AC-6 leave-one-class-out | 30 |

AC-5, AC-7 and AC-8 stay frozen with their cards. **HG-1 will interrupt you:** a sentinel goes red
the moment its subject module exists with nothing wired to it. All thirteen leaks are guarded and
`hydms.qa.sentinels.DEFERRED` is empty; record the next leak there on the day it is found.

---

## Using the board

```bash
S=../.claude/skills/kanban-ai/scripts
bash $S/list_all_cards.sh .        # the open cards: id | status | blocked_by | title
bash $S/show_blocked.sh .          # what is waiting on what
bash $S/list_all_cards.sh archived # the closed ones
```

- Move a card by editing `status`: `backlog` → `todo` → `doing` → `done`. **Every `blocked_by` id
  must be `done` before `doing`**; CI enforces it.
- **On close, move the card to `archived/` only if it has no unticked box.** A `done` card with an
  open box stays here. Relative links gain one `../` on the move; `check_board.py` finds any you miss.
- **`priority:` is a band, `P1`…`P4`** ([../CONTEXT.md](../CONTEXT.md), *Priority band*), not the
  kanban-ai default `High` / `Normal`. Set it when you file a card, and keep
  [../docs/PHASE-H-FINDINGS.md](../docs/PHASE-H-FINDINGS.md) in step; nothing checks either.
- Append to `## Narrative` when a card teaches you something, ISO-dated, `(by @...)`, newest first.
  The ADRs and Chapter 1 are written from those notes.
- A new card carries `id`, `status`, `priority`, `blocked_by`, `assignee`, `tags` (phase, layer,
  traces: `ph, l3, HG-1, AC-6`); an `> **Owns (hidden behind this module):**` line; `## Why this
  exists`; `## Done when`; a one-command `## Runnable check`; `## Traces to`; `## Narrative`.

`scripts/check_board.py` rejects a dangling `blocked_by`, a cycle, an id that does not match its
filename, an illegal status, a frozen card off `backlog`, and a relative link that does not resolve.
**It does not read checkboxes** (#68). The open-box convention is enforced by readers only, which is
what the findings index is for. The ML-skills caveat is in [../CLAUDE.md](../CLAUDE.md).
