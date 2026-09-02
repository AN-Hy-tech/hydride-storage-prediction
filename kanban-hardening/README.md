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

### Handoff — 2026-09-02 (night)

**S1 is closed.** **#71** landed and with it the last card of the QA foundation. Ten cards are done:
#1, #2, #8, #68, #72, #69, #70, #3, #5, #71. The tree is green on every check the project has:
`conda run -n Project python -m pytest -q`, `ruff check hydms/ tests/ scripts/`, `mypy`,
`check_board.py`, `check_freeze.py`. **S2 (data layer) and S3 (descriptor layer) are now unblocked
and are the only pair that may run in parallel** — see [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §2.

**What #71 gives you, and what it will do to you.** `hydms/qa/` holds the leak inventory as data,
six detectors, and one sentinel per leak. Ten of the thirteen leaks have a sentinel; L11, L12 and
L13 are recorded deferrals owed by #29, #26 and #87, each with a box on that card. Two things you
need to know before you touch S2 or S4:

- **The detectors are production code and your card is expected to call them.** `assert_merge_is_keyed`,
  `assert_disjoint_groups`, `assert_holdout_unchanged`, `assert_early_stopping_is_honest`,
  `assert_selection_is_nested`, `assert_selection_ignores_holdout`. Cards #10, #13, #14, #24, #26 and
  #88 each carry a box naming the one they owe. Every detector takes row labels, a record of what a
  fit saw, or a callable — never a fitted model — which is how all ten could be written and proved
  before any of the code they guard exists.
- **HG-1 will go red on you, on purpose, the first time you create a module a sentinel names.** Each
  sentinel declares the module its leak would reappear in (`hydms.data.merge`, `hydms.data.splits`,
  `hydms.data.screening`, `hydms.surrogate.model`, `hydms.surrogate.selection`,
  `hydms.surrogate.validation`). The moment one of those exists without a `live` hook in
  `hydms/qa/sentinels.py`, the gate fails with `L9 [unwired] #10 -- ... guarded in name only`. That is
  the mechanism, not a bug: a sentinel written six weeks early against a miniature becomes a real
  guard only when somebody points it at the real thing, and nobody was going to remember. If your
  card names its module differently, update the `subject` string in the same commit.

**HG-1 is SKIPPED today and that is the right answer.** `0/13 leaks guarded in the pipeline`.
`python -m hydms.gates run HG-1` exits 1. The reproductions going red proves the *detectors* work;
it says nothing about a pipeline that does not exist. The gate reports green only when all thirteen
are checked against real code, which is what makes [../docs/FREEZE.md](../docs/FREEZE.md)'s unfreeze
condition mean something.

**Findings, each now a box on the card that owns it.**

- **L10 is closed by no stage.** The runbook's S2 and S4 headers between them list every leak except
  L10, which is absent only because `Ashghal/Outliers_Management.py` is not being ported — an
  accident, not a fix. It returns the day #14 grows outlier handling. Boxed on **#14**, and the
  runbook now says so.
- **L11, L12 and L13 cannot be sentinelled yet.** Each needs a decision its owning card has not made:
  what the explainability record is (**#29**), what the weighting scheme is (**#26**), what the class
  join produces (**#87**). Each carries a box with the assertion it will have to make.
- **#71's own L9 wording was wrong**, and the runbook's and QA-PROTOCOL's with it. "A shuffled input
  frame makes the merge fail" is false of a *correct* keyed merge — joining by key is what makes row
  order irrelevant. The two real properties are order-invariance (reordering must not change the
  answer silently) and coverage (a row the merge cannot key must raise). All three documents now say
  that; #10's box does too.
- **`numpy` cannot be imported under `hydms/` while the lint lane stays conda-free.** mypy resolves
  it from the machine's 3.13 site-packages, whose `__init__.pyi` uses PEP 695 `type` statements that
  `python_version = "3.10"` rejects as a *syntax* error — which aborts the whole run, not just that
  file, and `ignore_missing_imports` does not suppress it. #71 sidestepped it with stdlib `random`
  for its one seeded shuffle. **The descriptor layer (#16–#20) cannot sidestep it**, so whoever gets
  there first owns the fix; the constraint is commented in `pyproject.toml` beside the override list.
  `pandas` needed adding to that list and has been.

**Corrections carried forward from #5's handoff.** `ruff` and `mypy` run **outside** the `Project`
environment, deliberately: neither imports the project's dependencies, and #68 established that the
fast lane installs nothing so it still reports when the environment is broken. #6 is two
independently-reporting jobs; **#86** carries a matching box.

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
