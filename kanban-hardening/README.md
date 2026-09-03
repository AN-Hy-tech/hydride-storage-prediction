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

### Handoff — 2026-09-03 · S2 half done, #87 landed

**Where the phase is.** S0 and S1 are closed. S2 (data layer) is open and three of its nine cards are
`done`: **#9** (loaders), **#10** (the keyed merge) and **#87** (the canonical composition key and the
`Alloy_class` reconciliation). Thirteen cards on the board are done. The tree is green on everything
the project has — `pytest -q` (**304 passing**, up from 241), `ruff check hydms/ tests/ scripts/`,
`mypy`, `check_board.py`, `check_freeze.py`. Nothing is in `doing`.

**HG-1 still reports `1/13 leaks guarded in the pipeline`.** L9 is the only `green` row and #87 did
not move that number, on purpose — see *the L13 decision* below. That number is the honest measure of
how far the phase has got, and it is the one to quote.

**S3 (descriptor layer) is still unblocked and still the only thing worth running in parallel**
([../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §2). This note is written for whoever takes
the rest of **S2**.

---

#### The opening move

**#12 and #13 are both clear now, and #13 is the one to take.** #87 was the card the stage was queued
behind; with it done, `blocked_by` empties for both, and #13 (splits) unblocks four more cards while
#12 (alloy class) unblocks only #30:

```
#9 loaders ✔ → #10 keyed merge (L9) ✔ → #87 canonical key ✔ → #12 alloy class
→ #13 splits (L8) → #14 CleanLab, train-only (L3, L10) → #15 golden tests
```

**#13 also has the least left to invent.** The published split protocol — stratification on binned
target and temperature, rare-stratum merging by Euclidean distance, both `StratifiedShuffleSplit`
calls, seed 42 — is already reproduced end to end in
`tests/data/test_canonical.py::published_split`, and it returns **896 / 136 / 247 exactly**. Port from
that reproduction, which is known faithful, rather than from `split_data.py`, and swap the grouping
key. The before-and-after is already asserted there: 16 canonical compositions straddle under the raw
string, none under the key.

**#11 is still the cheap one to run alongside.** Blocked on #9 only, half a day, and both of its
answers are measured and boxed on the card: the transform is `log1p` exactly on all 1279 rows, and it
must be **recomputed rather than joined** from `hydride_prefeaturizing.csv`, which aligns with
`hydride_data.csv` only positionally — the very thing #10 exists to stop.

Ask the board rather than trusting that diagram — it is the runbook's plan, not the current state:

```bash
S=../.claude/skills/kanban-ai/scripts
bash $S/show_blocked.sh .
bash $S/list_all_cards.sh .
```

#### What #9, #10 and #87 built that the rest of S2 is expected to use

Three modules own three questions, so no later stage re-litigates any of them:

| You need | Call | Rather than |
|---|---|---|
| A raw frame you can trust | `load_hydride_data()`, `load_prefeaturized()`, `load_ml_hydpark()` | `pd.read_csv` and hoping |
| A composition as `{element: amount}` | `parse_formula(...)` | a second regex, or CBFV's |
| To declare a new file's shape | `SourceSchema` / `ColumnSpec`, then `validate()` | an `assert df.shape ==` |
| To attach features to the measurement table | `merge_features(spine, [FeatureBlock(...)])` | `pd.concat(axis=1)`, ever |
| **The identity of one material** | **`canonical_key(formula)`** | `str.strip()`, `sorted()`, or a `groupby` on `Composition` |
| **A group vector for a split or a fold** | **`group_keys(frame)`** | any of the above, per module |
| **The alloy class of every row** | **`alloy_classes(frame)`** | joining `Alloy_class` on the formula string |
| **The class of every composition, with evidence** | **`alloy_class_table(frame)`** | reconciling the conflicts again |

**Do not write a second formula parser, and do not write a second key.** `parse_formula` is asserted
at parity with CBFV over all 1279 + 772 formulae *and* rejects the four things CBFV waves through;
`canonical_key` is built on it, so both grammars stay one grammar. #20 still says
"formula parsing via `pymatgen.core.Composition`" — that line predates #9 and now carries a box
saying not to.

**The key rounds atomic fractions to four significant digits, and that number was measured, not
chosen.** It is the only resolution that both reproduces the **1115** compositions every document in
this repository states *and* keeps the widest gap it merges (3.46e-05) narrower than the closest gap
it does not (1.01e-04). `separation()` asserts exactly that over all 8920 comparable pairs in both raw
files, and the test suite demonstrates it going red at three digits. If you add a data source, run
`separation()` over the union before trusting the key on it.

**A key is a label, not an input.** Re-keying a key moves a final digit for 185 of 1784 formulae,
because rounded fractions no longer sum to one. It never lands on another material's key — that is
asserted — but nothing should be grouping on a key it computed twice.

**The class conflicts were five and are ten.** Five raw formula strings disagree with themselves;
canonicalisation adds five more by merging spellings the file labelled independently (`Ce1Mg12` is
`MIC`, `Mg12Ce1` is `Mg`, one material, 6.0 wt% at 598 K). All ten are resolved by
`ALLOY_CLASS_PRECEDENCE` — `AB5 ≻ AB2 ≻ AB ≻ A2B ≻ Mg ≻ HEA ≻ MEA ≻ LEA ≻ SS ≻ MIC`, the most
specific structural claim first — and **not** by a majority vote, which would count citations rather
than chemistry and get `Mg2Ni` wrong three rows to one. 13 of 1279 rows change label. #12 consumes
that; it does not decide it again.

#### What S1 built that S2 is still expected to use

`hydms/qa/` is not a test-support package. It holds the guards the data layer is meant to carry, and
the remaining S2 cards are expected to call them **in the pipeline**, not merely beside it:

| Card | Creates | Calls | Closes | State |
|---|---|---|---|---|
| #10 | `hydms/data/merge.py` | `assert_merge_is_keyed` | L9 | ✔ wired, `green` |
| #13 | `hydms/data/splits.py` | `assert_disjoint_groups` on `group_keys(frame)` | L8 | owed |
| #14 | `hydms/data/screening.py` | `assert_holdout_unchanged` (twice: `y` and `X`) | L3, L10 | owed |
| #12 | — (carries the class through #20's featuriser) | `assert_metadata_survives` | L13 | owed |

**The build will go red the first time you create one of those files, before you have written
anything wrong.** That is card #71's `unwired` state and it is deliberate. It fired exactly as
designed on #10: `hydms/data/merge.py` appeared, HG-1 went red with `L9 [unwired] #10 -- guarded in
name only`, and stayed red until the `live` hook was added to `hydms/qa/sentinels.py`. The fix is
never to delete the sentinel. If your card names its module differently from the `subject` string,
update that string in the same commit.

**What a good `live` hook looks like.** `_l9_live` in `hydms/qa/sentinels.py` runs the detector
against the **real** data — the 1279-row spine through #9's loader and two real per-composition
blocks — not against the miniature the reproductions use. It costs 0.07 s and `audit()` stays under
0.05 s. It is also tested for the failure that would otherwise be invisible:
`test_l9_goes_red_when_the_real_merge_stops_keying` monkeypatches `hydms.data.merge.merge_features`
with the archival positional concat and asserts the audit reports `broken`, which is what proves the
sentinel watches the real function rather than a copy of it. Do the same for L8, L3, L10 and L13.

```bash
conda run -n Project python -m hydms.gates run HG-1     # exits 1 until every leak is guarded
conda run -n Project python -c "from hydms.qa import audit; [print(f'{r.leak:4} {r.status:9} #{r.owed_by}  {r.title}') for r in audit()]"
```

#### Five things that will otherwise cost S2 an afternoon each

- **Measure the key before you assert on it. Three times now the prescribed thing was wrong.** #9's
  runbook line asked for a vacuous assertion; #10's card named `(formula, temperature)` as if it
  identified a row, and it does not; #87's card said five compositions carry conflicting class labels,
  and ten do. In all three cases the card was corrected in the same commit as the code. Run the
  measurement in a scratchpad probe *first* — the planning documents were written from the archival
  code's intent, and the intent is not always what the code or the data does.
- **#13's split sizes will not match REPORT.md, and that is the fix working.** `split_data.py` used
  0.20 / 0.10, not the 70/15/15 that REPORT §2.6 and the README both claim; the config already
  carries the real fractions. Grouping on the canonical key instead of the raw string moves the
  896/136/247 split, because **35 rows across 16 compositions** were previously allowed to straddle.
  An exact match would mean the grouping key did not change. Note also that four `(key, temperature)`
  pairs are new repeats after canonicalisation — two spellings of one material at one temperature —
  so a per-row deduplication added later must not silently drop one of them.
- **The L13 decision, because it is the one that looks like a mistake.** L13's sentinel exists now
  (`assert_metadata_survives`, the seventh detector) and reports **`pending`**, not `green`. Its
  subject is `hydms.descriptors.featurize`, which does not exist until S3. Pointing it at the data
  layer instead would have made it green today while guarding a different property — that the class
  *exists* — and left the archival drop itself unguarded. So `closed_by` moved from #87 to **#12**,
  which is the card that carries the class through featurisation and owes the `live` hook, and the
  runbook's S2 exit line (which said L13 goes green at S2) was corrected. **S2 now exits with L3, L8,
  L9 and L10 green and L13 pending.**
- **#14 owes two wirings, inherits a leak no stage closes, and now owns a bad row.** L10 — the
  recovered `Outliers_Management.py:60-72` clipped held-out *feature* values using their own residuals
  — is absent only because that script is not being ported. That is an accident, not a fix, and it
  returns the day #14 grows outlier handling. Its two concrete decisions: rows 687 and 694 are
  byte-identical across all six columns, and `Mg0853Ni0.125La0.022` is a **missing decimal point**
  (0.853 + 0.125 + 0.022 = 1.000) that parses as Mg-853 and featurises as essentially pure magnesium.
  It passes #9's schema and it passes CBFV; #87's key found it as the only atomic fraction below 1e-4
  in either raw file. `Machine_Model/` is read-only under the freeze, so correcting it means a
  documented correction layer, not an edit — and not a silent repair inside a loader.
- **`numpy` cannot be imported anywhere under `hydms/`** while the lint lane stays conda-free. mypy
  resolves it from the machine's 3.13 site-packages, whose `__init__.pyi` uses PEP 695 `type`
  statements that `python_version = "3.10"` rejects as a **syntax** error, aborting the whole run;
  `ignore_missing_imports` does not suppress it. #71 sidestepped it with stdlib `random`, #9 with
  `math` plus pandas, #10 and #87 with pandas alone — **pandas is fine, it is only `numpy` that is
  poisoned**, and note that `pandas.api.types` must be reached as `pd.api.types.…` because the mypy
  override lists `pandas` and not `pandas.*`. A *test* may import numpy freely; only `hydms/` is
  constrained. **The descriptor layer (#16–#20) cannot dodge it**, so whoever reaches S3 owns the real
  fix. The constraint is commented in `pyproject.toml`.

#### S2 is done when

`conda run -n Project python -m pytest tests/data -q` passes and the **L3, L8, L9 and L10** rows of
the audit read `green`, with **L13 `pending`** until the descriptor layer exists. L9 is there already;
three to go. HG-1 as a whole stays SKIPPED until S4 — L1, L2, L4, L5, L6, L7, L11 and L12 belong to
the surrogate layer — so do not read a skipped HG-1 as failure to finish S2. Read the per-leak table.

---

#### Findings from this session, and what was done with each

Three corrections made here, four findings sent to the cards that own them.

**Corrected in place, all three because the data disagreed with the plan** —
(1) #87's card and [../docs/PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) §S2 both said **five**
compositions carry conflicting class labels. Five is the count on the raw formula *string*; on the
canonical key it is **ten**, and the five raw ones are a strict subset. The card's own last box had
asked for exactly this confirmation, and the answer is the one it feared.
(2) The runbook's S2 exit check said the L13 sentinel goes green at S2 exit because #87 owes it. The
sentinel guards the featuriser, which is S3, so it reads `pending`; `closed_by` moved to #12.
(3) The runbook's leak-sentinel table listed L13 as deferred alongside L11 and L12. It now has a row.

**Decided rather than deferred** — the key's resolution and the reconciliation rule are both
judgement calls that would have been easy to leave implicit. Four significant digits, and precedence
over majority: both are argued from measurements in #87's `## Narrative`, which is where #36's ADRs
should read them from.

**Sent to the owning card** — **#12** (consume `alloy_classes()`, do not reconcile again; wire the
L13 `live` hook; `UNKNOWN` is not in the closed vocabulary and adding it is a decision), **#13** and
**#88** (group on `group_keys(frame)`, called, not re-derived — two ways of computing "the same
material" is two answers), **#14** (`Mg0853Ni0.125La0.022`), **#20** (use `parse_formula`, not
pymatgen; and creating `hydms/descriptors/featurize.py` turns HG-1 red until #12 wires L13).

**Carried forward, still true.** `ruff` and `mypy` run **outside** the `Project` environment on
purpose — neither imports the project's dependencies, and #68 established that the fast lane installs
nothing so it still reports when the environment is broken. `pytest --cov` does not run anywhere yet:
neither `pytest-cov` nor `coverage` is in `Project`, so the coverage floor is unenforceable and
installing them is **#86**'s decision, because adding a package invalidates `environment.lock.yml`.
`scripts/verify_environment.py` still fails at stage 1 with `HTTP 403 FORBIDDEN for channel
pkgs/main` (boxed on #1), and it is not a cheap check — it rebuilds a throwaway conda environment.

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
