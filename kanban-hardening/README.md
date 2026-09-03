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
module exists with nothing wired to it. It has already happened once: creating `hydms/data/merge.py`
turned the build red with `L9 [unwired] #10 -- guarded in name only` before a wrong line had been
written, and stayed red until #10 added the `live` hook in `hydms/qa/sentinels.py`. That is the
mechanism working: a sentinel written six weeks early against a miniature becomes a real guard only
when somebody points it at the real thing. **Five cards still owe a wiring — #13, #14, #24, #26,
#88** — and three owe a sentinel outright — #29 (L11), #26 (L12), #87 (L13). Each carries the box.
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

### Handoff — 2026-09-03 · S2 open, #10 landed

**Where the phase is.** S0 and S1 are closed. S2 (data layer) is open and two of its nine cards are
`done`: **#9** (loaders) and **#10** (the keyed merge). Twelve cards on the board: #1, #2, #3, #5,
#8, #9, #10, #68, #69, #70, #71, #72. The tree is green on everything the project has — `pytest -q`
(**241 passing**), `ruff check hydms/ tests/ scripts/`, `mypy`, `check_board.py`, `check_freeze.py`.
Nothing is in `doing`.

**L9 is the first leak in the phase to reach `green`.** HG-1 now reports `1/13 leaks guarded in the
pipeline` — up from `0/13`, where it had sat since #71 landed. That number is the honest measure of
how far the phase has actually got, and it is the one to quote.

**S3 (descriptor layer) is still unblocked and still the only thing worth running in parallel**
([../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §2). This note is written for whoever takes
the rest of **S2**.

---

#### The opening move

**#87, the canonical composition key.** #10 is done, so #87 is clear, and it is the card the rest of
the stage is queued behind — #12 and #13 both name it in `blocked_by`, and #14 and #15 sit behind
#13:

```
#9 loaders ✔ → #10 keyed merge (L9) ✔ → #87 canonical key (L8, L13) → #12 alloy class
→ #13 splits (L8) → #14 CleanLab, train-only (L3, L10) → #15 golden tests
```

**#11 is the cheap one to run alongside it.** It is blocked on #9, not on #87, it is estimated at
half a day, and both of its answers are already measured and boxed on the card: the transform is
`log1p` exactly, on all 1279 rows, and it must be **recomputed rather than joined** from
`hydride_prefeaturizing.csv` — that file aligns with `hydride_data.csv` only positionally, which is
the very thing #10 exists to stop.

Ask the board rather than trusting that diagram — it is the runbook's plan, not the current state:

```bash
S=../.claude/skills/kanban-ai/scripts
bash $S/show_blocked.sh .
bash $S/list_all_cards.sh .
```

#### What #9 and #10 built that the rest of S2 is expected to use

`hydms/data/load.py` owns **what a valid row is** and `hydms/data/merge.py` owns **how blocks are
joined to it**, so no later stage re-litigates either:

| You need | Call | Rather than |
|---|---|---|
| A raw frame you can trust | `load_hydride_data()`, `load_prefeaturized()`, `load_ml_hydpark()` | `pd.read_csv` and hoping |
| A composition as `{element: amount}` | `parse_formula(...)` | a second regex, or CBFV's |
| To declare a new file's shape | `SourceSchema` / `ColumnSpec`, then `validate()` | an `assert df.shape ==` |
| To attach features to the measurement table | `merge_features(spine, [FeatureBlock(...)])` | `pd.concat(axis=1)`, ever |

**Do not write a second formula parser.** `parse_formula` is asserted at parity with CBFV over all
1279 + 772 formulae *and* rejects the four things CBFV waves through — a non-existent element, a zero
amount, a negative amount, and a parenthesised annotation read as an element. #87 needs a parser; it
needs this one.

**The loader normalises nothing, deliberately.** 34 formula strings carry a trailing space and 9 an
internal one; all 43 are returned exactly as stored. Stripping them would move the unique-formula
count from 1149 to 1142 silently — which is #87's collapse to make and to account for, in three steps
rather than one. The measured breakdown is boxed on #87.

**The merge takes its key as a parameter, so #87 does not have to change it.** `merge_features` joins
a `FeatureBlock` to the spine on whatever column the caller names. When the canonical key exists, hand
it that column; nothing in `hydms/data/merge.py` moves. What the module *fixes* is the direction of
the join: the spine keeps its rows, its order and its index, and a block is looked up from it.

#### What S1 built that S2 is still expected to use

`hydms/qa/` is not a test-support package. It holds the guards the data layer is meant to carry, and
the remaining S2 cards are expected to call them **in the pipeline**, not merely beside it:

| Card | Creates | Calls | Closes | State |
|---|---|---|---|---|
| #10 | `hydms/data/merge.py` | `assert_merge_is_keyed` | L9 | ✔ wired, `green` |
| #13 | `hydms/data/splits.py` | `assert_disjoint_groups` | L8 | owed |
| #14 | `hydms/data/screening.py` | `assert_holdout_unchanged` (twice: `y` and `X`) | L3, L10 | owed |

**The build will go red the first time you create one of those files, before you have written
anything wrong.** That is card #71's `unwired` state and it is deliberate. It fired exactly as
designed on #10: `hydms/data/merge.py` appeared, HG-1 went red with `L9 [unwired] #10 -- guarded in
name only`, and stayed red until the `live` hook was added to `hydms/qa/sentinels.py`. The fix is
never to delete the sentinel. If your card names its module differently from the `subject` string,
update that string in the same commit.

**What a good `live` hook looks like, now that there is one to copy.** `_l9_live` in
`hydms/qa/sentinels.py` runs the detector against the **real** data — the 1279-row spine through
#9's loader and two real per-composition blocks — not against the miniature the reproductions use.
It costs 0.07 s and `audit()` stays under 0.05 s. It is also tested for the failure that would
otherwise be invisible: `test_l9_goes_red_when_the_real_merge_stops_keying` monkeypatches
`hydms.data.merge.merge_features` with the archival positional concat and asserts the audit reports
`broken`, which is what proves the sentinel watches the real function rather than a copy of it. Do
the same for L8, L3 and L10.

```bash
conda run -n Project python -m hydms.gates run HG-1     # exits 1 until every leak is guarded
conda run -n Project python -c "from hydms.qa import audit; [print(f'{r.leak:4} {r.status:9} #{r.owed_by}  {r.title}') for r in audit()]"
```

#### Five things that will otherwise cost S2 an afternoon each

- **Measure the key before you assert on it. Twice now the prescribed key was wrong.** #9's runbook
  line asked for a vacuous assertion; #10's card named `(formula, temperature)` as if it identified a
  row, and it does not — 1279 rows carry 1272 distinct pairs, and keying on it would have inflated
  the table to 1293 in silence. #87 is *about* a key, so this applies to it more than to any other
  card on the board. Run the measurement in a scratchpad probe first.
- **#13's split sizes will not match REPORT.md, and that is the fix working.** `split_data.py` used
  0.20 / 0.10, not the 70/15/15 that REPORT §2.6 and the README both claim; the config already
  carries the real fractions. Grouping on the canonical key instead of the raw string moves the
  896/136/247 split, because 35 rows were previously allowed to straddle. An exact match would mean
  the grouping key did not change.
- **#87 owes a sentinel, not just a key.** L13 (`Alloy_class` destroyed at
  `extract_features_cbfv.py:19-21`) is a recorded deferral against #87, and HG-1 cannot go green
  until it exists. Five compositions carry conflicting class labels and need a stated rule, recorded
  in the narrative — a merge will not decide it for you. Two further reconciliations are boxed there:
  the curated file's ten `Alloy_class` values and ML-HydPARK's nine `Material_Class` values are
  neither subset nor superset of one another (#9), and the raw-string class-conflict count is *also*
  five, which either confirms the canonical number or hides a larger set (#10).
- **#14 owes two wirings and inherits a leak no stage closes.** L10 — the recovered
  `Outliers_Management.py:60-72` clipped held-out *feature* values using their own residuals — is
  absent only because that script is not being ported. That is an accident, not a fix, and it returns
  the day #14 grows outlier handling. It also now owns one concrete decision: `hydride_data.csv` rows
  687 and 694 are byte-identical across all six columns, and #14 is the only stage entitled to drop a
  row. All boxes are on the card.
- **`numpy` cannot be imported anywhere under `hydms/`** while the lint lane stays conda-free. mypy
  resolves it from the machine's 3.13 site-packages, whose `__init__.pyi` uses PEP 695 `type`
  statements that `python_version = "3.10"` rejects as a **syntax** error, aborting the whole run;
  `ignore_missing_imports` does not suppress it. #71 sidestepped it with stdlib `random`, #9 with
  `math` plus pandas, #10 with pandas alone — **pandas is fine, it is only `numpy` that is poisoned**,
  and note that `pandas.api.types` must be reached as `pd.api.types.…` because the mypy override
  lists `pandas` and not `pandas.*`. **The descriptor layer (#16–#20) cannot dodge numpy**, so
  whoever reaches S3 owns the real fix. The constraint is commented in `pyproject.toml`.

#### S2 is done when

`conda run -n Project python -m pytest tests/data -q` passes and the **L3, L8, L9, L10 and L13**
rows of the audit read `green`. L9 is there already; four to go. HG-1 as a whole stays SKIPPED until
S4 — L1, L2, L4, L5, L6, L7, L11 and L12 belong to the surrogate layer — so do not read a skipped
HG-1 as failure to finish S2. Read the per-leak table.

---

#### Findings from this session, and what was done with each

Two corrections made here, four findings sent to the cards that own them.

**Corrected in place** — [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §S2's #10 line and
the card's own first `## Done when` box both named a merge key the data does not support. Measured:
1279 rows, **1272** distinct `(Composition, temperature(K))` pairs; seven repeats, six of them
independent replicates with different targets and different citations. Both now say what the module
actually does — the spine's index label is the row identity, blocks are per-composition and looked up
from it, and a repeated block key is refused. The runbook's `0/13 leaks guarded` line was also stale
the moment L9 went green and now tells you to ask the gate instead of reading a number out of prose.

**Fixed in passing, because #10's own output would otherwise reproduce it** — `merge_datasets.py:49`,
one line below the leak: `df_merged.loc[:, ~df_merged.columns.duplicated()]` silently keeps the first
of two identically-named columns from different featurisers. `merge_features` refuses and names them.

**Sent to the owning card** — **#1** (`scripts/verify_environment.py` now fails at stage 1 with
`HTTP 403 FORBIDDEN for channel pkgs/main`; the lock lists `defaults`, and the rebuild claim on that
card is currently unrepeatable from this machine), **#11** (compute the log target, never join it —
`hydride_prefeaturizing.csv` has no key to join on), **#14** (rows 687 and 694 are byte-identical;
that is a decision, and this is the stage entitled to make it), **#87** (recount the `(key,
temperature)` collisions after canonicalisation, and confirm the five class conflicts are the same
five under both keys).

**Carried forward, still true.** `ruff` and `mypy` run **outside** the `Project` environment on
purpose — neither imports the project's dependencies, and #68 established that the fast lane installs
nothing so it still reports when the environment is broken. `pytest --cov` does not run anywhere yet:
neither `pytest-cov` nor `coverage` is in `Project`, so the coverage floor is unenforceable and
installing them is **#86**'s decision, because adding a package invalidates `environment.lock.yml`.
`hydms/data/load.py` is still **not** a sentinel subject, which is why #9 left the audit unchanged
while #10 moved it.

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
