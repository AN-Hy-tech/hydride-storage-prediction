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
when somebody points it at the real thing. #10, #13 and #14 have since wired theirs, and the audit
reports **4 of 13 leaks guarded** — L3, L8, L9, L10. **Three cards still owe a wiring — #12 (L13,
the moment #20 creates the featuriser), #24 (L6) and #88 (L2, L4, L7)** — one owes both a wiring and
a sentinel, #26 (L1, L5, and L12 outright), and #29 owes L11 outright. Each carries the box.
Read the per-leak table with:

```bash
conda run --no-capture-output -n Project python -c "from hydms.qa import audit; [print(f'{r.leak:4} {r.status:9} #{r.owed_by}  {r.title}') for r in audit()]"
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

### Handoff — 2026-09-03 (later) · #6 and #16 landed · written for #17

**Where the phase is.** Seventeen cards done. Two landed since the handoff below, and both were
worth more than their card text promised.

**#6, the CI fast lane.** `.github/workflows/ci.yml`, two independently-reporting jobs, green in
32 s + 56 s. `integrity.yml` is absorbed into it and deleted. Three things to know:

- **CI now runs on every push to every branch.** The old workflow filtered `push: branches: [main]`,
  so the freeze check and the board check had not run once across the eight Phase H commits on this
  branch. If you push, you will get a result.
- **The `suite` job is not the `Project` environment and cannot be.** `environment.lock.yml` is
  win-64 by construction, so a Linux runner cannot restore it; the job runs
  `pip install -e ".[dev]"` instead. The consequence is #7's: nothing in CI proves the lockfile
  still recreates, and only `windows-latest` ever could.
- **`ruff` and `mypy` are pinned exactly** (`0.8.4`, `1.13.0`) to the machine lane's versions. Not
  caution — a floor resolved newer on the first run and raised RUF100 on a `# noqa` the older ruff
  requires, which makes the two versions mutually unsatisfiable. Bumping them is a deliberate commit.

**#16, the element property tables.** `hydms/descriptors/element_data.py` over two committed CSVs
built from their publishers by `scripts/build_element_tables.py`; `data/SOURCES.md` is the record.
**The numpy wall is down** — the mypy override is applied with its cost stated in `pyproject.toml`,
and numpy may now be imported under `hydms/`. Read `SOURCES.md` before #17; four findings change
what the rest of S3 is:

| Finding | Who inherits it |
|---|---|
| CBFV's `jarvis.csv` **is** NIST's `Elements.json` (7.3e-12), and the five composites are per-element **columns** — so **R3 is settled**, statistic-of-composite by construction | **#18** inherits the answer, not the question; its budgeted slack is free |
| The Oliynyk table was **revised for 2024** — 8 of 13 needed properties disagree with CBFV, up to 10.0 | **#21**: AC-2 means "reproduces CBFV *given the same table*", supplied from `tests/descriptors/data/` |
| `gordy_en` is blank for **21 of the 55** elements (nearly the rare earths); europium's JARVIS properties are `-9999` | **#19** must record computability per *composition*; #24/#25 may have to re-run selection |
| CBFV answers for `Eu1Ni5` anyway, substituting an all-zero property vector — row 516 of the published matrix is that row | **#89**, as a data-integrity disagreement |

**The tree is green:** 411 tests, ruff and mypy clean, both CI jobs green, `audit()` still reports
4 of 13 leaks guarded (no sentinel changed hands — `element_data.py` is not a subject any sentinel
names; L13 still waits on `hydms.descriptors.featurize`, which is #20).

#### The opening move

**#17, weighted composition statistics.** It is the only S3 card whose blockers are all done. It
takes property vectors from `element_data.PropertyTable.vector()` and must reproduce CBFV's `avg`,
`dev` and `range` — and note that `dev` is CBFV's own definition, not a standard deviation, so
measure it against CBFV rather than assuming. #19 (the feature contract) is also unblocked and can
run beside it.

---

### Handoff — 2026-09-03 · S2 closed as far as it can close · written for S3

**Where the phase is.** S0, S1 and **S2** are done with S2 as far as the data layer can go alone.
Six of S2's nine cards are `done` — **#3** (config), **#9** (loaders), **#10** (keyed merge),
**#11** (target transform), **#87** (canonical key) and **#13** (splits). **#15**'s file is written
and green, but its card is held in `backlog` by the board's own rule and by the substance: two of its
pinned facts move when #24 lands. The other two are `doing`, and both wait on a *later* stage rather
than on anything in S2 — **#12** needs the featuriser S3 builds, **#14** needs the feature matrix
S4's #24 supplies. Fifteen cards on the board are done.

`audit()` reports **4 of 13 leaks guarded against the real pipeline** — L3, L8, L9 and L10, which is
exactly the set the runbook's S2 exit check names. The tree is green: 391 tests, ruff and mypy clean,
`check_board.py` and `check_freeze.py` both OK.

#### The opening move, and why it is the only one

**#16, the element property tables.** Everything else in S3 is downstream of it: #17 needs property
vectors to take statistics over, #18 needs #17, #19 and #20 need all three, and #21 — the parity gate
that blocks every card downstream of selection — cannot run until #20 exists.

```
#8 provenance ✔ → #16 tables → #17 statistics → #18 composites → #20 featurize()
                             ↘ #19 the 22-feature contract ↗          ↓
                                                              #21 GATE AC-2 · #22 throughput
```

And #16 carries two boxes added on the way out of S2 that will otherwise cost you the first morning.
Read them before you write a line.

#### The wall S3 hits in its first hour, and the tested way through

**NumPy cannot currently be imported anywhere under `hydms/`.** mypy runs *outside* the `Project`
environment by design — that is the conda-free lint lane (#68, `docs/QA-PROTOCOL.md` §6), and its
whole value is that it still gives a red/green signal when the environment is broken or absent. The
cost is that mypy resolves numpy from the machine's 3.13 site-packages, whose `__init__.pyi` uses PEP
695 `type` statements that `python_version = "3.10"` rejects as a **syntax** error. That aborts the
*entire* run — `Found 1 error in 1 file (errors prevented further checking)` — not just the importing
file, and `ignore_missing_imports` does not suppress it, because it is not a missing import.

#71 sidestepped it with stdlib `random`. #11 sidestepped it with `math.log1p`, at a measured cost of
one ulp against `numpy.log1p`. **The descriptor layer cannot sidestep it**, and #16 now carries a
remedy that was actually run rather than reasoned about: a `follow_imports = "skip"` override for
`numpy` and `numpy.*`, verified on 2026-09-03 by adding a numpy-importing module under
`hydms/descriptors/` and getting `Success: no issues found in 40 source files`. It is deliberately
**not applied** — choosing it, and writing what it costs into `pyproject.toml`, is #16's decision.
The cost: numpy becomes `Any`, so mypy stops checking dtype and shape mistakes in the layer with the
most array code. That is the same trade already made for pandas, scipy and scikit-learn, which is an
argument for it and not a reason to skip stating it.

#### What S2 built that S3 is expected to *use*, not re-derive

Five seams. Each exists because two modules would otherwise disagree about the same thing.

- **`hydms.data.load.parse_formula`** is the grammar. Not CBFV's, which validates nothing —
  measured: `Xx2` → `{'Xx': 2.0}`, `Mg0` → `{}`, `Mg-1` → `{'Mg': -1.0}` — and not
  `pymatgen.core.Composition`, which #20's own card rules out. Three parsers would mean three ideas
  of what a formula is, and the differences would surface as compositions that featurise but cannot
  be keyed.
- **`hydms.data.canonical.group_keys`** is what makes two rows the same material. Splits group on
  it, #88's folds group on it, the class join uses it. Call it; never re-derive it.
- **`hydms.data.target.to_model_space` / `to_wt_pct`** are the only two transform entry points, and
  a named `Series` carries its space in its name — `H2_W% (max)` in, `log_H2_W% (max)` out, and a
  second transform *refuses* rather than producing `log_log_`. If S3 ever needs the target, it goes
  through these.
- **`hydms.data.metadata.metadata_columns()`** is the list a featuriser must carry through, and
  **`non_feature_columns()`** is that list plus the target in both spaces.
  **`refuse_non_features(X)` is meant to be called on what #20 returns.** The two lists differ by
  exactly the target, and the difference is the point: a featuriser dropping `Alloy_class` costs
  AC-6; a feature matrix *containing* `H2_W% (max)` costs everything at once and looks like an
  excellent model rather than like a bug.
- **`hydms.data.splits.assign_splits`** returns `train`/`val`/`test` per row and checks its own
  disjointness before returning, so a caller cannot receive a leaking split.

#### Four things that will otherwise cost an afternoon each

1. **Creating `hydms/descriptors/featurize.py` turns the build red before you write a wrong line.**
   The L13 sentinel names that module as its subject and has no `live` hook, so HG-1 will report
   `L13 [unwired] #12 -- guarded in name only` the moment the file exists. That is the mechanism, not
   a bug: **do not re-aim the sentinel's `subject` to make it green.** #12 owes the hook —
   `assert_metadata_survives(before, after, columns=metadata_columns())` on the real featurisation
   path — and #12 is `doing` precisely because it is waiting for #20. Coordinate; #20's card carries
   the box and #12's carries the other half.
2. **The featuriser sources from two tables, not one.** `extract_features_cbfv.py:31` says
   `elem_prop='magpie'`, and magpie produces **none** of the 21 published descriptors. The real set
   is 15 `oliynyk` + 6 `jarvis` + `temperature(K)`, resolved empirically by #8 and written up in
   [../hydms/descriptors/FEATURE_PROVENANCE.md](../hydms/descriptors/FEATURE_PROVENANCE.md). A
   single-table reimplementation cannot pass #21 no matter how correct its Oliynyk half is.
3. **The dataset contains 55 elements, not 54.** `REPORT.md` §2.3 and the PRD's dataset table both
   say 54; counted from the parsed compositions of all 1279 rows it is 55, seven of them appearing
   exactly once (N, Eu, Lu, Pb, Au, Os, Re). #16's coverage check was written against 54 and has been
   corrected; a table validated against the wrong number passes while one element silently has no
   properties.
4. **Nothing in this project compares two float vectors with `==`, and #21's 1e-9 is not an
   accident.** #11 measured three independent one-ulp effects on the target alone: the published
   `log_H2_W% (max)` column round-tripped through decimal text and differs from `log1p` of the target
   on 274 of 1279 rows; `math.log1p` and `numpy.log1p` differ on this data; and `expm1(log1p(y))`
   returns `y` exactly on only 794 rows. Parity to 1e-9 is loose enough to survive all of that and
   tight enough that a wrong property table cannot hide.

#### S3 is done when

`#21` is green — every one of the 22 columns agreeing with CBFV to 1e-9 over all 1279 formulae, with
a failure message that names the column and the worst-offending formula rather than a boolean — and
`#22` has written a throughput number into `docs/BENCHMARKS.md`. Along the way, `hydms/descriptors/`
imports CBFV nowhere: it is unlicensed, which is why the layer is being reimplemented, and it stays a
`parity` extra used only by the gate that diffs against it.

Expect **HG-1 to go red during S3 and stay red until #12 closes.** That is planned. It goes green
again at `5/13`.

#### Findings from this session, and what was done with each

| Finding | Where it went |
|---|---|
| The published `log` column is `log1p` only to one ulp — it was written by `to_csv` and read back through decimal text, bit-identical on 1005 of 1279 rows | Card #11's boxes and `hydms/data/target.py`'s docstring; `ROUND_TRIP_TOLERANCE = 1e-12` |
| `REPORT.md` §4.2's Overfitting footnote subtracts a weight-percent number from a log-space one, and the code computes something else again | A tenth disagreement, boxed on **#89** |
| `alloy_class_table` ordered labels by `ALLOY_CLASS_PRECEDENCE.index` *before* validating them, so a bad label crashed with `tuple.index(x): x not in tuple` and `reconcile_class`'s refusal was unreachable | Fixed in #87's module — the refusal is the decision #12 was making, and a bare `ValueError` is not a refusal |
| Nothing stopped the target reaching the feature matrix | `non_feature_columns()` and `refuse_non_features()`, card #12 |
| The card's `UNKNOWN` alloy class would be a label with no members that still changes AC-6's fold count | Settled as a **refusal** at the door, card #12 |
| `Mg0853Ni0.125La0.022` is a missing decimal point whose correction must be applied *upstream of the canonical key*, which screening is not | Dropped from training and named in `MALFORMED_FORMULAE`; the correction-layer decision boxed on **#9** |
| A golden record that stops covering a stage reports agreement it never checked | `diff()` treats an absent fact as a difference, card #15 |
| NumPy still aborts the whole mypy run; a `follow_imports = "skip"` override was tested and works | Boxed on **#16**, unapplied — the trade is that card's to make |
| The dataset has 55 elements, not the 54 #16's coverage check named | Corrected on **#16**; already recorded as #89's ninth disagreement |
| A runbook line I had *just* written said `tests/data` is 89 tests; it is 215 over eight files | Corrected in the same commit. Prose rots the moment it is written, including new prose |

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
