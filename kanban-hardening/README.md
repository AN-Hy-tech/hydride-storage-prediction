# The hardening board — Phase H

**This is the active board.** [../kanban/](../kanban/) is frozen; see [../docs/FREEZE.md](../docs/FREEZE.md).

This file owns the board's *own logic* — how cards are organised here, how the two boards share one
id space, and where to start. It does not restate what lives elsewhere:

| Looking for | Read |
|---|---|
| Why this phase exists, the leak inventory, the stage order and steps | [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) |
| What is frozen, why, and the unfreeze condition | [../docs/FREEZE.md](../docs/FREEZE.md) |
| The frozen inverse-design programme | [../docs/PRD-inverse-design.md](../docs/PRD-inverse-design.md), [../kanban/README.md](../kanban/README.md) |
| What a card *is now* | the card itself — it outranks every document above on its own status |
| What a card must prove before it is done | [../docs/QA-PROTOCOL.md](../docs/QA-PROTOCOL.md) |

---

## Two directories, one id space

Cards live in two directories that are validated together:

| Directory | Ids | State |
|---|---|---|
| `kanban-hardening/` | 1–37, 44, 48, 49, 68, 69–89 | **Active** |
| `../kanban/` | 38–43, 45–47, 50–67 | **Frozen** — every card must stay `backlog` |

**The directories are a freeze boundary, not an id-space boundary.** `blocked_by` reaches across
them, ids are unique across both, and `scripts/check_board.py` loads them as a single graph. Ids were
preserved when cards migrated: renumbering would have broken every `blocked_by` edge, every
`Traces to` link, and the `## Narrative` notes that the ADRs and card #37 are written from.

Three cards were pulled out of the frozen PA phase — **#44** (screen interface), **#48**
(applicability-domain ceiling), **#49** (ElMD novelty). They are not inverse-design work: they are
what lets the interface **refuse** to answer instead of guessing.

**The next free id is #90.** Scan both directories for `max(id) + 1`.

---

## Layers

Unchanged from the original board — each layer owns one kind of knowledge, and nothing outside it
needs to know that knowledge.

| Layer | Owns | Cards here |
|---|---|---|
| **L0 Foundation** | environment, config, artifact store, gates, CI, **test infrastructure** | 1–7, 68, 69–74, 86 |
| **L1 Data** | source schemas, merge keys, the canonical composition key, split protocol, CleanLab | 9–15, 87 |
| **L2 Descriptors** | element property tables, statistics, the 22-feature contract | 8, 16–22 |
| **L3 Surrogate** | model choice, scaler, quantiles, conformal calibration, the validation protocol | 23–34, 88 |
| **L4 Screens** | the screen verdict, the AD ceiling, novelty | 44, 48, 49 |
| **L6 Delivery** | the prediction contract, the API, the app, the chart vocabulary | 75–84 |
| **L7 Evidence** | glossary, ADRs, the reconciliation, the Chapter 1 revision | 35, 36, 37, 85, 89 |

L5 Search is entirely frozen — it is how *candidates are proposed*, which is inverse design.

---

## Stage → card map

The runbook executes these in order. S2 and S3 are the only pair that may run in parallel.

| Stage | Cards | Days |
|---|---|---:|
| **S0** Freeze & tooling | 72 | 1 |
| **S1** QA foundation | 69, 70, 5, 71 | 2 |
| **S2** Data layer | 3, 9, 10, 11, 87, 12, 13, 14, 15 | 7 |
| **S3** Descriptor layer | 16, 17, 18, 19, 20, 21, 22 | 6 |
| **S4** Surrogate layer | 23, 24, 25, 88, 26, 27, 28, 29, 30, 31, 32, 33, 34 | 13 |
| **S5** Guard rails | 44, 48, 49 | 2.5 |
| **S6** Delivery: contract + API | 75, 76, 77, 78, 79, 80 | 5 |
| **S7** Delivery: interface | 81, 82, 83, 84 | 3.5 |
| **S8** Evidence & close | 89, 85, 86, 35, 36, 37 | 5 |

Cards **4, 6, 7, 73, 74** are foundation and CI work that slots in where its blockers allow rather
than sitting in one stage. **#5** (the gate harness) was the same kind of card and has landed inside
S1, where it belonged: every gate card on the board was blocked behind it.

---

## Gates

Nine are live in this phase — four new, five inherited from the PRD's acceptance criteria. The full
table with failure conditions is in [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §4.

All of them are registered in the gate harness (#5), together with the three frozen criteria, so the
registry is the complete list of what the project has promised to check rather than the subset it can
currently check. Ask it rather than this table: `python -m hydms.gates list`.

| Gate | Card | | Gate | Card |
|---|---|---|---|---|
| **HG-1** leak sentinels | 71 | | AC-1 seed reproducibility | 32 |
| **HG-2** no bare numbers | 77 | | AC-2 featuriser parity | 21 |
| **HG-3** transport parity | 79 | | AC-3 conformal coverage | 31 |
| **HG-4** hygiene | 86 | | AC-4 known-alloy round-trip | 33 |
| | | | AC-6 leave-one-class-out | 30 |

AC-5 is thermodynamic and AC-7/AC-8 are inverse-design; all three stay frozen with their cards.

**Two hard gates block everything behind them.** #21 (featuriser parity) gates every card downstream
of selection — if the reimplementation does not reproduce CBFV to 1e-9, the reimplementation is
wrong, not CBFV. And #71 (leak sentinels) is what makes the phase durable: without it, nothing stops
the next session reintroducing a leak the phase just removed.

---

## Start here

Ask the board rather than trusting a list — a list here goes stale the moment a card moves.

```bash
S=../.claude/skills/kanban-ai/scripts
bash $S/show_blocked.sh .          # what is waiting on what
bash $S/view_board.sh .            # everything by status
bash $S/list_all_cards.sh .        # id | status | blocked_by | title
```

### Handoff — 2026-09-02 (evening)

**S1 is one card from closed.** The gate harness (**#5**) has landed — the last thing standing
between the board and **#71**. Nine cards are done: #1, #2, #8, #68, #72, #69, #70, #3, #5. The
tree is green on every check the project currently has: **69 tests**, `ruff check hydms/ tests/
scripts/`, `mypy`, `check_board.py`, `check_freeze.py`.

**What #5 gives you.** `python -m hydms.gates list` is now the authoritative answer to "what has
this project promised to check" — twelve criteria, the PRD's eight plus this phase's four, one
module each under [../hydms/gates/](../hydms/gates/), every one `SKIPPED` and naming the card that
owes it. Three behaviours to know before writing a gate. **Naming a gate makes the run strict:**
`run AC-2` exits non-zero while AC-2 is unimplemented, which is what makes the `## Runnable check`
on #21, #31, #32, #33, #71, #77 and #79 honest from the day it is written; `run --all` tolerates
skips and prints a `NOT CHECKED` banner instead, because CI that is red for the length of the phase
is CI nobody reads. **A gate that raises is red, not absent** — so is a module that will not import.
**A gate may only report on itself**, or one could report a pass on another's behalf and the table
would look complete. Each gate also declares its own CI lane (`FAST` = answerable against the
published artifact, `SLOW` = needs a retrain), so cards #6 and #7 read the split rather than
deciding it.

**Corrections made, so you do not inherit them.** Card **#6** had `ruff` and `mypy` running inside
the `Project` conda environment. They were deliberately left outside it — neither imports the
project's dependencies, and #68 established that the fast lane installs nothing so it still reports
when the environment is broken. #6 is now two independently-reporting jobs, a conda-free `hygiene`
job and a `suite` job that pays for the environment, and its runnable check is the lane's own
commands rather than `gh run watch`, which could not fail before the workflow existed. The same
mistake was in [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §5 and is fixed there;
**#86** carries a matching box so it cannot re-acquire the assumption.

**Findings, and what was done with each.** Three came out of #5, and none was left in a commit
message where nothing checks it. (1) `pytest --cov` **does not run anywhere** — neither `pytest-cov`
nor `coverage` is installed in `Project`, so the coverage floor in `pyproject.toml` is currently
unenforceable. It is declared in the `dev` extra and nothing installed it. Two boxes on **#86**,
which owns the floor, plus notes in the runbook §5 and
[../docs/QA-PROTOCOL.md](../docs/QA-PROTOCOL.md) §6 where the command was printed as though it
worked — adding a package to `Project` invalidates `environment.lock.yml`, so this is a decision,
not a `pip install`. (2) Card **#4**'s artifact manifest does not exist yet, so a gate run writes its
results to `artifacts/gate-results.json` behind a versioned `schema` key; #4 embeds that object under
`gates` rather than inventing a second format. (3) `hydms/config/pipeline.yaml` claimed its output
directories were gitignored and **four of the five were not** — the first default gate run would have
dropped an untracked file into the tree. Fixed in `.gitignore` in the same commit, because that one
was a defect this card's own output would have created.

**Also unblocked:** #6 (now that #5 has landed), and #4, #9, #16, #19, #44 as before. #9 → #10 → #87
is the S2 chain leading to the canonical composition key; #16 opens the S3 descriptor work in
parallel with it.

#### Starting #71 — the leak sentinels

Take **#71** next: it closes S1, and it is the difference between removing thirteen leaks and
*keeping* them removed. Read [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §1 first — the
thirteen leaks with their exact line numbers in `Machine_Model/src/` are the definition of done for
S2 through S4, and the two absent from the PRD are the severe ones: `CleanLab.py:90` rewriting
held-out labels, and the positional `concat` at `merge_datasets.py:46`. The shape of the work is
`tests/leaks/`, one file per leak, each marked `leak` so `pytest -m leak` selects the gate, plus
swapping the `Pending` in [../hydms/gates/hg1_leak_sentinels.py](../hydms/gates/hg1_leak_sentinels.py)
for a real check once the suite exists. Two constraints make this harder than it looks and are worth
accepting up front. First, **most of the code these sentinels guard has not been written yet** — the
keyed merge is #10, the canonical key is #87, the honest early stopping is #26 — so a sentinel
written today must assert against the *contract* the later card will meet, and several will start as
`xfail` or as tests over a fixture rather than over `hydms`; say which is which in the card, because
an `xfail` nobody revisits is a leak with a test's name on it. Second, and non-negotiable: **each
sentinel must be seen red with its leak deliberately reintroduced**, and that demonstration recorded
in the card's `## Narrative` ([../docs/QA-PROTOCOL.md](../docs/QA-PROTOCOL.md) §1 and §5). A sentinel
nobody has watched fail is an assumption, not a check — which is exactly the failure mode #5 was
built to make impossible, and it would be a poor joke to reintroduce it in the card that inherits
the harness.

---

## Using the board

Unchanged from the original board's rules:

- Move a card by editing its `status`: `backlog` → `todo` → `doing` → `done`.
- **Before moving a card to `doing`, every id in its `blocked_by` must be `done`.** CI enforces this.
- Append to `## Narrative` when a card teaches you something, ISO-dated, `(by @...)`. Those notes are
  the record of *why*, and they are what the ADRs (#36) and the Chapter 1 revision (#37) are written
  from.
- New cards carry: `id`, `status`, `priority`, `blocked_by`, `assignee`, `tags`; an
  `> **Owns (hidden behind this module):**` blockquote; `## Why this exists`; `## Done when`;
  a single-command `## Runnable check`; `## Traces to`; and `## Narrative`.
- Tags lead with the phase, then the layer, then traces: `ph, l3, HG-1, AC-6`.

`scripts/check_board.py` will reject a dangling `blocked_by`, a dependency cycle, an id that does not
match its filename prefix, an illegal status, a card on the frozen board that has left `backlog`, and
any relative Markdown link that does not resolve.

---

## A note on the `ml-model-training` skill

Installed for this phase and useful for model-fitting mechanics. It is **silent** on group-aware
splitting, nested cross-validation, and early stopping on the scoring set, and its worked example is a
plain `train_test_split` with no `random_state` and no grouping — which in this project would
reintroduce leaks L4, L7 and L8. This project's authority order puts skills below the
[../research/](../research/) memos; on any validation question the memos and the runbook win.
