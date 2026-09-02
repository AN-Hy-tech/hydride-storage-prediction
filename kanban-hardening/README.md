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
wrong, not CBFV. And #71 (leak sentinels) is what makes the phase durable.

**#71 has landed, and it will interrupt you.** It is the one gate that goes red at a moment you did
not choose: each sentinel names the module its leak would reappear in, and HG-1 fails as soon as that
module exists with nothing wired to it. Creating `hydms/data/merge.py` turns the build red with
`L9 [unwired] #10 -- guarded in name only` until you add the `live` hook in `hydms/qa/sentinels.py`.
That is the mechanism working: a sentinel written six weeks early against a miniature becomes a real
guard only when somebody points it at the real thing. Six cards owe a wiring — #10, #13, #14, #24,
#26, #88 — and three owe a sentinel outright — #29 (L11), #26 (L12), #87 (L13). Each carries the box.
Read the per-leak table with:

```bash
conda run -n Project python -c "from hydms.qa import audit; [print(f'{r.leak:4} {r.status:9} #{r.owed_by}  {r.title}') for r in audit()]"
```

---

## Start here

Ask the board rather than trusting a list — a list here goes stale the moment a card moves.

```bash
S=../.claude/skills/kanban-ai/scripts
bash $S/show_blocked.sh .          # what is waiting on what
bash $S/view_board.sh .            # everything by status
bash $S/list_all_cards.sh .        # id | status | blocked_by | title
```

### Handoff — 2026-09-03 · S2 open, #9 landed

**Where the phase is.** S0 and S1 are closed. S2 (data layer) is open and its first card, **#9**, is
`done`. Eleven cards: #1, #2, #3, #5, #8, #9, #68, #69, #70, #71, #72. The tree is green on
everything the project has — `pytest -q` (212 passing), `ruff check hydms/ tests/ scripts/`, `mypy`,
`check_board.py`, `check_freeze.py`. Nothing is in `doing`.

**S3 (descriptor layer) is still unblocked and still the only thing worth running in parallel**
([../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §2). This note is written for whoever takes
the rest of **S2**.

---

#### The opening move

**#10, the keyed merge.** #9 is done, so #10 and #11 are both clear; everything after them is a
chain:

```
#9 loaders ✔ → #10 keyed merge (L9) → #11 target transform → #87 canonical key (L8, L13)
→ #12 alloy class → #13 splits (L8) → #14 CleanLab, train-only (L3, L10) → #15 golden tests
```

(#11 is blocked on #9 rather than on #10, so it can run alongside the merge — and #9 has already
measured its answer for it: the transform is `log1p`, exactly, on all 1279 rows. The box is on #11.)

Ask the board rather than trusting that diagram — it is the runbook's plan, not the current state:

```bash
S=../.claude/skills/kanban-ai/scripts
bash $S/show_blocked.sh .
bash $S/list_all_cards.sh .
```

#### What #9 built that the rest of S2 is expected to use

`hydms/data/load.py` owns **what a valid row is**, so no later stage re-litigates it:

| You need | Call | Rather than |
|---|---|---|
| A raw frame you can trust | `load_hydride_data()`, `load_prefeaturized()`, `load_ml_hydpark()` | `pd.read_csv` and hoping |
| A composition as `{element: amount}` | `parse_formula(...)` | a second regex, or CBFV's |
| To declare a new file's shape | `SourceSchema` / `ColumnSpec`, then `validate()` | an `assert df.shape ==` |

**Do not write a second formula parser.** `parse_formula` is asserted at parity with CBFV over all
1279 + 772 formulae *and* rejects the four things CBFV waves through — a non-existent element, a zero
amount, a negative amount, and a parenthesised annotation read as an element. #87 needs a parser; it
needs this one.

**The loader normalises nothing, deliberately.** 34 formula strings carry a trailing space and 9 an
internal one; all 43 are returned exactly as stored. Stripping them would move the unique-formula
count from 1149 to 1142 silently — which is #87's collapse to make and to account for, in three steps
rather than one. The measured breakdown is boxed on #87.

#### What S1 built that S2 is still expected to use

`hydms/qa/` is not a test-support package. It holds the guards the data layer is meant to carry, and
three S2 cards are expected to call them **in the pipeline**, not merely beside it:

| Card | Creates | Calls | Closes |
|---|---|---|---|
| #10 | `hydms/data/merge.py` | `assert_merge_is_keyed` | L9 |
| #13 | `hydms/data/splits.py` | `assert_disjoint_groups` | L8 |
| #14 | `hydms/data/screening.py` | `assert_holdout_unchanged` (twice: `y` and `X`) | L3, L10 |

**The build will go red the first time you create one of those files, before you have written
anything wrong.** That is card #71's `unwired` state and it is deliberate: a sentinel written against
a miniature guards nothing until it is pointed at the real module, and nobody was going to remember
to do it. The fix is never to delete the sentinel — it is to add the `live` callable in
`hydms/qa/sentinels.py`. If your card names its module differently from the `subject` string, update
that string in the same commit.

`hydms/data/load.py` is **not** a sentinel subject, which is why landing #9 left the audit unchanged
at ten `pending` and three `deferred`.

```bash
conda run -n Project python -m hydms.gates run HG-1     # exits 1 until every leak is guarded
conda run -n Project python -c "from hydms.qa import audit; [print(f'{r.leak:4} {r.status:9} #{r.owed_by}  {r.title}') for r in audit()]"
```

#### Four things that will otherwise cost S2 an afternoon each

- **#13's split sizes will not match REPORT.md, and that is the fix working.** `split_data.py` used
  0.20 / 0.10, not the 70/15/15 that REPORT §2.6 and the README both claim; the config already
  carries the real fractions. Grouping on the canonical key instead of the raw string moves the
  896/136/247 split, because 35 rows were previously allowed to straddle. An exact match would mean
  the grouping key did not change.
- **#87 owes a sentinel, not just a key.** L13 (`Alloy_class` destroyed at
  `extract_features_cbfv.py:19-21`) is a recorded deferral against #87, and HG-1 cannot go green
  until it exists. Five compositions carry conflicting class labels and need a stated rule, recorded
  in the narrative — a merge will not decide it for you. #9 added a second reconciliation #87 owes:
  the curated file's ten `Alloy_class` values and ML-HydPARK's nine `Material_Class` values are
  neither a subset nor a superset of one another.
- **#14 owes two wirings and inherits a leak no stage closes.** L10 — the recovered
  `Outliers_Management.py:60-72` clipped held-out *feature* values using their own residuals — is
  absent only because that script is not being ported. That is an accident, not a fix, and it returns
  the day #14 grows outlier handling. Both boxes are on the card.
- **`numpy` cannot be imported anywhere under `hydms/`** while the lint lane stays conda-free. mypy
  resolves it from the machine's 3.13 site-packages, whose `__init__.pyi` uses PEP 695 `type`
  statements that `python_version = "3.10"` rejects as a **syntax** error, aborting the whole run;
  `ignore_missing_imports` does not suppress it. #71 sidestepped it with stdlib `random` and #9 with
  `math` plus pandas — **pandas is fine, it is only `numpy` that is poisoned**, and note that
  `pandas.api.types` must be reached as `pd.api.types.…` because the mypy override lists `pandas`
  and not `pandas.*`. **The descriptor layer (#16–#20) cannot dodge numpy**, so whoever reaches S3
  owns the real fix. The constraint is commented in `pyproject.toml` beside the mypy override list.

#### S2 is done when

`conda run -n Project python -m pytest tests/data -q` passes and the **L3, L8, L9, L10 and L13**
rows of the audit read `green`. HG-1 as a whole stays SKIPPED until S4 — L1, L2, L4, L5, L6, L7, L11
and L12 belong to the surrogate layer — so do not read a skipped HG-1 as failure to finish S2. Read
the per-leak table.

---

#### Findings from this session, and what was done with each

One correction made here, four findings sent to the cards that own them.

**Corrected in place** — [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §S2 told #9 to
"assert `len(skipped) == 0` where the legacy code silently discarded CBFV failures". Measured against
the installed CBFV, `skipped` is **empty** on all 1279 rows: the assertion would have passed while
proving nothing. The defect is upstream of `skipped` — CBFV's parser accepts a non-existent element,
a zero amount and a negative amount, and reads `(M)` in `Hf2Cu (M)` as an element. An unknown element
then lands in the unread `skipped` list and an empty composition kills `generate_features` with
`zero-size array to reduction operation maximum`. The runbook line now says what to guard instead.

**Sent to the owning card** — #86 (decide `openpyxl`, or the HyStor spreadsheet stays unread — the
same decision as `pytest-cov`), #89 (the file has **55** elements; REPORT §2.3 and the PRD say 54),
#11 (the transform is `log1p`, measured elementwise, not `log(10y)`), #87 (whitespace alone accounts
for 1149 → 1142 of the collapse to 1115; reuse `parse_formula`; the two class vocabularies are not
nested).

**Carried forward, still true.** `ruff` and `mypy` run **outside** the `Project` environment on
purpose — neither imports the project's dependencies, and #68 established that the fast lane installs
nothing so it still reports when the environment is broken. `pytest --cov` does not run anywhere yet:
neither `pytest-cov` nor `coverage` is in `Project`, so the coverage floor is unenforceable and
installing them is **#86**'s decision, because adding a package invalidates `environment.lock.yml`.

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
