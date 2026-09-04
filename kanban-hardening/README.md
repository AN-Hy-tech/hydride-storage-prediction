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
when somebody points it at the real thing. #10, #13, #14 and #12 have since wired theirs, and the audit
reports **5 of 13 leaks guarded** — L3, L8, L9, L10, L13. It has now happened twice: #20 creating
`hydms/descriptors/featurize.py` turned L13 `unwired` and took eight tests red with it, and #12
closed it the same day. **Two cards still owe a wiring — #24 (L6) and #88 (L2, L4, L7)** — one owes
both a wiring and a sentinel, #26 (L1, L5, and L12 outright), and #29 owes L11 outright. Each
carries the box.
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

### Handoff — 2026-09-04 (latest) · #4 closed · written for S4, opening at #23

**Where the phase is.** Twenty-five cards done. #4 landed out of stage order because **#23 was
blocked by it** and S4 is a thirteen-card chain that starts there; `#23` is now unblocked and
nothing stands in front of it. Suite **661** green, ruff 0.8.4 and mypy 1.13.0 clean,
`check_board.py` and `check_freeze.py` OK, HG-1 `SKIPPED` at 5/13, AC-2 green, `run --fast` exits 0.

**Read the next handoff down as well** — the one written when #22 closed S3. It carries #22's 13×
finding and the four things S3 left for S4 that are not repeated here in full: `with_features` is
the only place the record and the matrix become one
frame, the full 22 cannot build a training matrix at all (266 of 1,279 rows refused, 265 for
`dev_Gordy_electonegativity` alone), `featurize` has a 5 ms per-call floor so featurise in batches,
and HG-1 goes from 5/13 to 11/13 across S4 with the sentinels already written.

#### What #4 built, that S4 is expected to use rather than re-invent

`hydms/artifacts/` — `manifest.py` records, `store.py` stores, and `save()` / `load()` are the only
doors. **#23 is the first caller**: the fitted `RobustScaler` is a payload in a version, not a
pickle beside a script.

```python
from hydms import artifacts
artifacts.save({"model": m, "scaler": s}, contract=CONTRACT, seeds={...}, gates=report)
bundle = artifacts.load()                 # the promoted version, gates checked
bundle["scaler"].transform(X)             # never .fit
```

- **A version is written once.** `save` stages `.v{N}.partial` and renames it into place, refuses an
  existing version, and never re-uses a number a dead run left behind. Do not write into a version
  directory by hand: every payload carries a SHA-256 and `load` re-hashes it.
- **The gate report is embedded verbatim, not re-formatted.** `save(gates=report)` takes either a
  `GateReport` or the mapping its `to_dict()` produced — the same object
  `python -m hydms.gates run` already writes to `artifacts/gate-results.json`.
- **A version whose recorded gates did not all pass will not load and cannot be promoted, and a
  `SKIPPED` gate counts.** That is stricter than `GateReport.ok`, deliberately: `ok` tolerates a
  skip under a broad selection so CI is not red for the length of the phase, and that leniency is
  right for a CI log and wrong for an artifact about to answer a prediction. **So a version saved
  today cannot load without `require_gates=False`** — pass it in #23 through #33 and expect to stop
  passing it at #34, which is blocked on #31/#32/#33 for exactly this reason.
- **The contract is not optional and is not decorative.** `save(contract=...)` refuses anything that
  is not a `FeatureContract` or its `as_manifest()` payload. Swapping two features in a stored
  manifest still loads the bundle — the payload bytes are untouched — and then raises `ContractError`
  from `bundle.contract()`, which is the AC-4 failure caught by #19's digest rather than by a person.
- **Promotion is `current.json`.** `promote(version)` refuses an unestablished one; rollback is
  `promote(older)`. That is card #7's contract, made structural here rather than in a workflow file.

#### The opening move

**#23, and S4 is thirteen cards of chain.** Fit the `RobustScaler` on train only, persist it into
the artifact version, and make the load path expose `transform` and not `fit`. Two things to settle
inside the card rather than around it:

- **Where the transform-only wrapper lives.** The card asks that `fit` raise on the loaded object.
  The store deliberately does not know what a scaler is — it stores objects — so the wrapper is
  `hydms/surrogate/`'s, and `save` stores the wrapped thing. Wrapping at load time would mean the
  store growing per-payload knowledge, which is the seam this board is shaped to keep closed.
- **#23's `blocked_by` is satisfied but #88 is not.** #88 (group-aware nested CV) is blocked by
  #23, and #23 needs a train split to fit on — that is #13's `hydms/data/splits.py`, which is done.
  Use it; do not derive a split inside the surrogate layer.

**And before you land a gate:** `tests/gates/` takes an `unwritten` fixture (`tests/gates/conftest.py`)
wherever it needs "a criterion nobody has written yet". Use it for #26, #28, #30, #31, #32, #33, #77,
#79 and #86 — naming a gate there is what card #21 had to undo.

**S4's exit check:** `conda run -n Project python -m hydms.gates run --fast` · all HG-1 sentinels green.

#### Findings of this session

- **`joblib` needed a mypy override.** It ships neither inline types nor a `py.typed` marker and the
  conda-free lint lane installs nothing, so `import joblib` under `hydms/` aborted the type check.
  Added to the existing `ignore_missing_imports` block in `pyproject.toml` with the reason beside it.
- **`versions()` sorts numerically, never lexicographically.** A string sort puts `v10` before `v9`
  and promotes the wrong artifact on the tenth retrain. One `int()`, one test, a real incident avoided.
- **`RECORDED_PACKAGES` is checked against `pyproject.toml` by a test,** not maintained by memory:
  a new core dependency that nothing records leaves "it used to reproduce" as the only evidence when
  AC-1 goes red after an upgrade.
- **`tests/screens/` is uncommitted work on #44 that this session did not touch.** Two modules
  under `hydms/screens/` — `protocol.py` and `window.py` — and their 63 tests are in the working
  tree and pass; the card is still `backlog` and the files are untracked. That is the difference between the **661** reported above
  and the **724** a bare `pytest` prints. It is #44's to land — S5's card, not S4's.

---

### Handoff — 2026-09-04 (earlier) · #22 closed, **S3 closed** · written for S4, opening at #23

**Where the phase is.** Twenty-four cards done and **the descriptor layer is finished**. Suite
**593** green, ruff 0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, HG-1
`SKIPPED` at 5/13, AC-2 green at 2.7285e-12 in 1.28 s. S2 and S3 have both closed as far as they can;
**everything left in this phase is a chain, and it starts at #23.**

**#22 was budgeted as a printout and returned a 13× defect in the layer it measures.** This is the
one thing to carry forward from it.

- **The number this project has been quoting since #20 was measured on four formulae.** *10,000
  formulae in 0.31 s* — in `featurize`'s docstring, in #20's narrative and in three handoffs below
  this one — came from `["LaNi5", "TiFe", "Mg2Ni", "Ti0.8Zr0.2Mn1.4V0.2Cr0.4"] * 2500`. Ten thousand
  rows, **four** distinct compositions. The computability verdict is memoised per element *set*, so
  that batch answered it four times instead of ten thousand. Ten thousand genuinely distinct
  candidates took **3.34 s** — 2,996/s, three times the card's feasibility floor rather than forty.
  **Those earlier handoffs are history; the number is now 0.245 s.**
- **97% of the wall clock was one cache that no caller could reach.** `cProfile`:
  `FeatureContract.computability` → `PropertyTable.has`, **13.8 million calls to answer nineteen
  questions**. The servable-element set was cached only for the *shipped* tables, keyed by table name
  — and `featurize._sources` always hands `computability` a resolved `tables=` mapping, so the cached
  branch was unreachable from the featuriser. Its comment said the uncached path was "affordable
  because the only caller is a gate that runs once". Every caller was on it. The memo now lives on
  the table (`PropertyTable.servable`, a `cached_property`) and `contract._servable` is a one-line
  forward. **10k distinct 3.3375 → 0.2448 s, 100k 21.03 → 2.23 s, curated 0.1602 → 0.0221 s, the
  suite 24.9 → 17.9 s, AC-2 1.54 → 1.28 s. No expected value in any test moved.**
- **A benchmark is only evidence if the workload is the one the decision is about.** That is why the
  candidates are asserted distinct *and* their element sets distinct — distinct strings alone would
  let the workload silently become a cache again — and why the parse half is timed separately. The
  parser turned out to be 22%, so the card's instruction was right about the principle and wrong
  about the culprit.

**What R6 now knows, and the sentence not to drop.** A 1e6-point grid featurises in ~24 s, 1e7 in
~4 min, NSGA-II's whole 100,000-evaluation budget in 2.2 s. **Featurisation does not decide between
Architecture A and Architecture B.** What decides it is unmeasured: one evaluation is featurisation
*plus* the scaler, the surrogate, the conformal interval and two screens — #23, #26, #27, #44, #48,
#49, none of which exists. [../docs/BENCHMARKS.md](../docs/BENCHMARKS.md) says so in bold, because
the failure mode of that document is somebody quoting 44,000 candidates/s as an end-to-end rate.
**Re-measure when #28's `predict()` lands and put the number there beside this one.**

#### The opening move

**#23, and S4 is thirteen cards of chain.** The fit-once scaler: fit on train, persist, never refit.
Four things not worth re-deriving:

- **`hydms.data.metadata.with_features` is the only place the record and the matrix become one
  frame.** #23, #24 and #26 each need a training matrix and none of them should write a `concat`.
  Boxed on #24, with the reason: `temperature(K)` is a column of the raw file **and** one of the 22
  features, so a plain concat returns that name twice, `int64` beside `float64`.
- **The full 22 cannot build a training matrix at all.** 266 of 1,279 rows are refused by the shipped
  tables, 265 for `dev_Gordy_electonegativity` alone; without that one feature the remaining 21 cover
  1,278. The trade is #24/#25's to make and AC-2 restates it in its own output every run.
- **Featurise in batches, and now there is a number for why.** `featurize` has a **5 ms per-call
  floor** — `require_self_consistent` re-auditing both tables' composite columns — which is 2% of a
  ten-thousand batch and 57% of a batch of one. Boxed on #44, where a per-candidate loop would make
  it a 200× cost. It was measured and deliberately *not* optimised: it moves no number #22 publishes.
- **HG-1 goes from 5/13 to 11/13 across S4**, and the sentinels are already written. #24 owes L6, #88
  owes L2/L4/L7, #26 owes L1/L5 — each is `pending` today only because its subject module does not
  exist. Expect the same shape as L13 in S3: the day the module appears the sentinel reads `unwired`
  and HG-1 goes **red on purpose** until the owning card gives it a `live` hook. Do not re-aim a
  subject to make it green.

**One card is still `doing`: #14**, and S4 is where it comes due — #24 consuming its output closes the
`Boruta_FeatEng.py:23-25` bypass and supplies the feature matrix CleanLab needs to produce
`label_issues` at all. **#15 is written, green, and stays `backlog` behind it**; when #24 lands,
`screened.rows_out` and `screened.removed` move and those two facts are re-measured. Nothing else in
`tests/data/test_golden.py` should move, and if it does, that is the finding.

**And before you land a gate:** `tests/gates/` takes an `unwritten` fixture (`tests/gates/conftest.py`)
wherever it needs "a criterion nobody has written yet". Use it for #26, #28, #30, #31, #32, #33, #77,
#79 and #86 — naming a gate there is what card #21 had to undo.

---

### Handoff — 2026-09-04 (earlier) · #21 closed, AC-2 green · written for #22, then S4

**Where the phase is.** Twenty-three cards done, and **S3 has one card left**. The suite is **577**
green, ruff 0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, HG-1 still
`SKIPPED` at 5/13, and the fast lane exits 0 with **AC-2 the first `PASSED` row the gate table has
ever carried**. The hard gate of S3 is answered: `2.7285e-12` against a tolerance of `1e-9`, over
1,278 of the 1,279 curated formulae, in 1.5 s.

**#21, and why a gate expected to be green was still a day's work.** #20 had already measured the
16-formula version at 4.547e-13, so the outcome was never in doubt. What the card actually bought is
everything around the number.

- **The exclusion is derived from both sides.** The card says no europium formula may be compared and
  that the exclusion must be *recorded*, not filtered. Hard-coding `"Eu"` would have satisfied the
  letter of that. A row is instead excluded when this layer refuses it — `computability` against the
  tables the gate is actually using — **or** when CBFV lists it in the `skipped` array that
  `extract_features_cbfv.py` never read, and the result prints the two counts separately, because
  the case worth seeing is the two *disagreeing*. Today they are the same single row. Measured on the
  way: **CBFV's `jarvis.csv` has no europium row at all** (82 elements, not 85), and CBFV emits a
  full row for `Eu1Ni5` anyway — `avg_atom_mass` 48.911 is `(0×1 + 58.6934×5)/6`. The all-zero
  property vector is now arithmetic rather than inference.
- **The gate reads CBFV's installed table, not the committed fixture** — a correction to two boxes
  and to the last handoff. The numbers are identical (zero differing cells, because the fixture was
  written with `repr(float)`), but the gate imports CBFV anyway to produce the expected values, and a
  second source of the *table* admits a skew between the two halves of one comparison that would
  surface as a parity failure rather than as the stale fixture it is. It also keeps package code out
  of `tests/`. The fixture gained a test that pins it against the installed table cell by cell.
- **Supplying CBFV's JARVIS copy as well changes nothing — 2.7285e-12 either way, same cell.** #16
  recorded the two copies of NIST's file agreeing to 7.3e-12 and the worst offender here is a JARVIS
  composite of magnitude ~4e3, so table skew was the reasonable suspect. It is not. The whole residue
  is #17's element order, and the card's "suspect the order before the arithmetic" is now measured.
- **A green gate has to be able to say what it did not establish.** Two of the card's boxes are about
  AC-2's blind spots and both are lines of the result — what was excluded, and that the *shipped*
  tables could not have featurised **266 of 1,279** rows at all. Writing them found that
  `_report.py` printed multi-line detail only for `FAILED` and `ERRORED`, so both lines lived only in
  the JSON. Any status prints it now; HG-1's per-leak listing had been invisible for the same reason.

**The thing to know before you touch `tests/gates/`.** Landing the first real gate broke six tests
that were never about it: `test_harness.py` and `test_cli.py` used the literal `AC-2` wherever they
meant "a criterion nobody has written yet", so a passing AC-2 turned four strictness tests and two
CLI tests into tests of featuriser parity. They now take the **`unwritten` fixture** in
`tests/gates/conftest.py`, which asks the registry which gates are still `Pending` and asserts the
answer is non-empty. **Use it when you land #26, #28, #30, #31, #32, #33, #77, #79 or #86** — do not
substitute another gate name, or the next card repeats this. Four doc comments that used AC-2 as the
standing example of an unimplemented gate were repointed at HG-2.

#### The opening move

**#22, and it is the last card in S3.** The featurisation throughput benchmark. It starts from
numbers already measured rather than from nothing: **10,000 formulae in one call take 0.31 s** and
the curated 1,278 take **0.21 s** (`featurize`'s module docstring quotes both), and this card added a
third — the whole AC-2 gate, which featurises 1,279 rows once and runs CBFV over them twice, takes
**1.5 s** end to end. What #22 owes is a benchmark that is a *check* rather than a printout: a
threshold that fails the build, a shape that says whether the cost is per-call or per-formula, and a
statement of what it is defending — the memo's practical check 3 warns against a per-formula loop,
and Architectures A and B both evaluate candidates in batches. `pyproject.toml` declares a `slow`
marker for tests that take more than a few seconds; decide whether this one earns it.

**Then S3 closes and S4 opens at #23**, the fit-once scaler. Two things there that are not worth
re-deriving:

- **`hydms.data.metadata.with_features` is the only place the record and the matrix become one
  frame.** #23, #24 and #26 each need a training matrix and none of them should write a `concat`.
  Boxed on #24. The reason is on that box too: `temperature(K)` is a column of the raw file *and* one
  of the 22 features, so a plain concat returns the name twice, `int64` beside `float64`.
- **The full 22 cannot build a training matrix at all** — 266 of 1,279 rows are refused by the
  shipped tables, 265 for `dev_Gordy_electonegativity` alone. Without that one feature the remaining
  21 cover 1,278. That trade is #24/#25's to make, and AC-2 says so in its own output every time it
  runs, precisely so a green gate is never read as "the featuriser can produce all 22 for every row".

**One card is still `doing`: #14.** It owes S4, not S3 — #24 consuming its output is what closes the
`Boruta_FeatEng.py:23-25` bypass and supplies the feature matrix CleanLab needs to produce
`label_issues` at all. #15 is written, green, and stays `backlog` behind it.

---

### Handoff — 2026-09-04 (earlier) · #12 closed · written for #21, then #22

**Where the phase is.** Twenty-two cards done and **the tree is green again**: 567 tests pass, ruff
0.8.4 and mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, HG-1 **skipped at 5/13**
rather than failing. The eight red tests the last handoff described were one fact and it closed the
way it was written down: #20 created the featuriser, the L13 sentinel went `unwired`, #12 pointed it
at the real thing. The subject string was never touched.

**#12, the second half.** It landed its data half on 2026-09-03 and could not finish: three boxes
named `hydms.descriptors.featurize`, which did not exist. All three closed here.
`hydms.data.metadata.with_features(record, features)` is the join — `refuse_non_features` on the
way in, `assert_metadata_survives` on the way out, by label, refusing every way that join has
silently gone wrong in this repository — and the L13 `live` hook runs it over the real featuriser
across **1,278 of the 1,279** curated rows. 11 new tests on the join, one on the end-to-end path,
and one that puts `extract_features_cbfv.py:19-21` back into the real seam and asserts the audit
reports L13 `broken` — the only thing that distinguishes a hook watching the pipeline from a hook
watching a copy of it.

**Three things it taught.**

- **The join needed a function, not a line.** The card prescribed `pd.concat([metadata, features],
  axis=1)` and the hook could have written it inline. That would have made the L13 sentinel guard
  four lines of `hydms/qa/sentinels.py` — the same mistake, in the other direction, as pointing
  L13 at the data layer would have been in S2. So the guard lives in the pipeline (the #14 pattern:
  `screen` calls its detector before it returns) and the sentinel re-runs it. Weakening the check
  inside the join cannot make HG-1 green.
- **Writing the join found that the prescribed `concat` was subtly wrong.** `temperature(K)` is a
  column of the raw file **and** one of the 22 features, so concatenating the record with the matrix
  returns a frame carrying that name **twice**, `int64` beside `float64`, and pandas hands it over
  without a word. `merge_datasets.py:49` is the archival answer —
  `df_merged.loc[:, ~df_merged.columns.duplicated()]`, keep whichever arrived first — which
  makes this the third disguise of one defect (#10 found the second, one line below the leak).
  `with_features` takes the **matrix's** copy, because that one carries #19's cast (313.5 K must not
  become 313), but only after checking the two agree exactly. That check is free — widening
  `int64` to `float64` is exact — and it is the only tie in the frame between a record and a
  matrix that claims to describe it: featurise at other temperatures and it refuses, by row.
- **The hook's coverage was a choice, and it is documented as one.** The full 22 featurise only
  **1,013** of the 1,279 rows (the Gordy hole, measured again here); without
  `dev_Gordy_electonegativity` it is **1,278**, everything but `Eu1Ni5`. The hook drops that one
  feature so it checks the file rather than three quarters of it, and its docstring says this is a
  statement about the *check's* coverage and **not** a decision about the feature set, which is
  #24/#25's to make. The rows it keeps come from asking `FeatureContract.computability`, the idiom
  `featurize`'s own docstring documents, so the refused row is named by the verdict rather than by a
  list in a sentinel. An empty selection raises rather than asserting over nothing: a vacuous pass
  is the shape of the leak this sentinel exists to catch.

**The seam S4 must use, not re-derive.** `with_features` is now the only place the record and the
matrix become one frame. #23, #24 and #26 each need a training matrix; none of them should write a
`concat`. It is boxed on #24, which is the first card that builds one.

#### The opening move

**#21, the hard gate of S3, and it is the only card that is both unblocked and load-bearing.**
Parity with CBFV to 1e-9 over all 1,279 formulae. It inherits three boxes from #20 — the
`tables=` seam and how to build the reference table, "compare in one batch and here is why", and the
news that a 16-formula version already passes at **4.547e-13**. Its remaining work is the other
1,263 formulae, a failure output that names the column and the worst-offending formula rather than a
boolean, and the line stating how many rows the *shipped* tables could not have featurised at all
— because AC-2 runs against CBFV's table, where neither the Gordy hole nor the wrong-axis
reduction is visible. Two amendments from #16 still stand: parity is measured against the reference
table, and **no Eu-containing formula can be compared at all**, because this layer refuses where
CBFV returns a silently-zeroed number.

**Then #22**, the throughput benchmark, which starts from the numbers already measured: 10,000
formulae in **0.31 s**, the curated 1,278 in **0.21 s**. After that S3 is closed and S4 opens at
#23.

**One card is still `doing`: #14.** It owes S4 rather than S3 — #24 consuming its output is what
closes the `Boruta_FeatEng.py:23-25` bypass and supplies the feature matrix CleanLab needs to produce
`label_issues` at all — so it is not in S3's way. #15 is written, green, and stays `backlog`
behind it.

---

### Handoff — 2026-09-04 (earlier) · #20 landed · written for #12, then #21

**Where the phase is.** Twenty-one cards done, and **the tree is red on purpose.** 554 tests,
**546 pass and 8 fail**; every one of the eight is the same fact — `hydms/descriptors/featurize.py`
now exists, so the L13 sentinel reads `unwired` and HG-1 fails at **4 of 13**. ruff 0.8.4 and mypy
1.13.0 clean, `check_board.py` and `check_freeze.py` OK. This was written down in advance on three
cards and it happened exactly as written. **Do not re-aim the sentinel's subject and do not delete
it.** #12 is `doing`, was blocked only on this module, and closes it.

**#20, the featuriser.** `featurize(formulas, temperatures, *, contract=None, tables=None)` →
`(n, 22)` of float64, in contract order, on the caller's index. 52 tests. No CSV in, no CSV out;
one parse pass, then 19 fancy-indexes and 19 batched reductions — 10,000 formulae in **0.31 s**.
Four things it taught, one of which changed a module that was already `done`.

- **A batch of one was not the same arithmetic as a batch of many, and only from eight elements
  up.** #17 established that the reduction must run down the *leading* axis because numpy sums the
  fast axis pairwise. But a batch of **one**, transposed, leaves the leading axis contiguous too —
  and numpy's contiguous sum switches from a plain loop to an eight-accumulator unrolled one at
  exactly eight elements. Measured over 200 random compositions per arity: identical to the bit up
  to arity 7, and from **arity 8** a lone composition disagrees with itself inside a batch by up to
  **5.5e-12** on `avg` and `dev`. That is three orders inside AC-2's 1e-9, so **no gate would ever
  have caught it**; what it would have done is make a single-formula prediction (#82) and AC-4's
  round-trip (#33) disagree with the training matrix, for the eleven curated rows of eight elements
  or more, silently. Fixed in `stats.statistics` — a lone composition is duplicated, the pair is
  reduced, the copy discarded — rather than worked around in the featuriser, because that is where
  the axis decision lives. #17's own test passed throughout because its arity was 5; it is now 10,
  and deleting the fix turns it red. No committed number moves: every existing pin is a batch.
- **The refusal is much bigger than "seven features are not always computable" sounds.** Counted as
  rows a caller loses, the published 22 cannot featurise **266 of the 1,279** curated rows — 265
  for `dev_Gordy_electonegativity` alone, and `Eu1Ni5` for seven features at once. So the full
  contract **cannot build the training matrix at all**. Drop Gordy and the remaining 21 cover
  **1,278 of 1,279**. One feature is the difference between 1,278 rows and 1,013, which is the
  decision #24/#25 are actually making; boxed there.
- **#21's requirement turned out to be a requirement on this module's interface.** "The featuriser
  reproduces CBFV *given the same table*" cannot be arranged from outside a function that resolves
  its own tables. So `tables=` is a parameter — and that forced the honest version of the verdict:
  `FeatureContract.computability(..., tables=)`, because asking the *shipped* table whether a row
  is featurisable while reading CBFV's numbers would refuse the 266 rows the gate exists to
  compare. `PropertyTable.of()` was added so a caller builds a table without reaching through a
  frozen dataclass's underscored field. This is the layer's existing convention, not a new one —
  `disagreements`, `require_coverage` and `require_self_consistent` all take their table.
- **The value pin found nothing wrong, which is worth saying out loud.** All 22 columns against
  CBFV's own output over the sixteen fixture formulae, with CBFV's own table supplied: worst
  **4.547e-13** absolute and **6.828e-15** relative. The assembly — right statistic, right
  property, right table, right column — was correct first time, and the residue is the element
  order #17 already measured.

**Two interface decisions that are not in the card and will look arbitrary later.** The frame comes
back on the **caller's index** (a `Series` keeps its labels, a list gets a `RangeIndex`), a repeated
label is refused, and a `temperature` Series whose index disagrees with the formulae's is refused
rather than zipped by position — all three because the metadata AC-6 needs is re-attached to this
matrix afterwards, and the way that goes wrong is leak L9. And **nothing is ever dropped**: an
unparseable formula, a hole, a non-finite temperature each raise, listing every offender with its
label, because a featuriser that quietly returns fewer rows than it was given is how a feature
matrix comes to be joined to the wrong compositions.

#### The opening move

**#12, and it is the only one.** It is `doing`, it is unblocked, and it is what turns the tree
green. Three boxes are owed and all three name the module that now exists: the class surviving
featurisation, its absence from `X`, and the **L13 `live` hook**. The shape is on the card. Two
practical notes: the join is `pd.concat([metadata, features], axis=1)` and is label-aligned by
construction, never positional; and a `live` hook that featurises real rows must either pick
well-covered formulae or pass a contract without `dev_Gordy_electonegativity`, because the full 22
refuse 266 of the 1,279.

**Then #21, the hard gate of S3.** It inherits three boxes from this card — the `tables=` seam and
how to build the reference table, "compare in one batch and here is why", and the news that a
16-formula version of the gate already passes at 4.547e-13. Its remaining work is the other 1,263
formulae, a failure output that names the column and the row, and the line stating how many rows
the *shipped* tables could not have featurised at all — because AC-2 runs against CBFV's table,
where neither the Gordy hole nor the wrong-axis reduction is visible. Then #22, the benchmark,
which starts from 0.31 s / 10k.

---

### Handoff — 2026-09-04 (earlier) · #18 landed · written for #20

**Where the phase is.** Twenty cards done. The tree is green: **502 tests**, ruff 0.8.4 and
mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, `gates run --fast` exit 0,
`audit()` unchanged at **4 of 13** — `hydms/descriptors/composites.py` is no sentinel's
subject either, and L13 still waits on `hydms.descriptors.featurize`, which is #20.

**#18, the composites.** `hydms/descriptors/composites.py`: `INFIXES` (two entries — the whole
spec), `decompose()`, `composite_properties()`, `disagreements()` and
`require_self_consistent()`. 21 tests. The card asked for the construction order, both orders
behind a flag, a declarative spec and six hand pins. The order was already settled by #16 and
the statistic already built by #17, so the real work was the thing the by-construction argument
*assumes* — that a column named `a_divi_b` is `a` divided by `b`. Checked across all 156
composite columns instead of the five in play:

- **Eleven of the 156 are not the arithmetic their names claim.** One family,
  `*_mult_voro_coord`, and two elements, **Cs and Gd**, where every one of them is `0.0` —
  formed as though `voro_coord` were 0, while the `voro_coord` column stores `1.0` and
  `voro_coord_divi_mol_vol` uses that 1.0 (Gd: `1/19.9 = 0.05025125628140704`, the stored
  value). NIST's file contradicts itself about two elements. No tolerance would have shown
  this: the disagreement is a relative **1.0**.
- **The other 145 — and all five selected composites — equal their parts bit-exactly.** Not to
  a tolerance; the same double, on every one of the 82 elements carrying them. Which is what
  makes the rule cheap and easy to lose: **read the published column, never a derived value.**
  It is what CBFV reads, so it is what parity means (#21). Today the two routes are identical
  for the five in the 22; the eleven are why it is a rule.
- **`voro_coord = 1.0` for Cs and Gd is a placeholder, and it reaches a selected feature.**
  Every other element in the table sits between 3 and 12, and gadolinium is hcp with twelve
  nearest neighbours. Gd is in **18 of the 1,279** rows, through
  `dev_voro_coord_divi_mol_vol`. Not a bug, not a parity problem — a limit to state. Boxed on
  **#83**; whether the feature survives re-selection is **#25**'s, boxed there with the eleven.

**Two smaller things worth having.**

- **The naming grammar is a parse, not a guess, and that is measured**: 156 of JARVIS's 438
  columns carry an infix, `oliynyk` carries **none**, no name carries two, every one splits
  into two names that are themselves columns, and none splits two ways. So `INFIXES` can be a
  spec rather than a branch table. The trap it guards: a *feature* name is not a *property*
  name — `avg_polzbl_divi_atom_mass` splits into `avg_polzbl` and `atom_mass`, and `decompose()`
  refuses it rather than featurising from the wrong pair.
- **The rejected order is kept as a failing assertion rather than deleted.** No flag was ever
  written: the card's "both orders behind a flag, loser deleted before merge" would have left
  nothing behind, and the measurement leaves a test. Over the sixteen fixture formulae
  composite-of-statistic misses CBFV by between **1.8%** (`avg_first_ion_en_mult_X`) and a
  factor of **65** (`dev_bp_divi_atom_mass`), while statistic-of-composite agrees to
  **9.1e-13**. Some of the gap is structural rather than large — `range(a)/range(b)` is not a
  range of anything, and `dev_voro_coord_divi_mol_vol` computed the wrong way on a two-element
  composition is exactly zero.

**The hand pins.** Six features × five statistics on `Mg2Ni1`, where the fractions are 2/3 and
1/3 and the closed forms fit on one line: `avg = (2a+b)/3`, `dev = (4/9)|a−b|`, `range = |a−b|`.
Every expected value is exact decimal arithmetic from the two element values — not numpy, not
the code under test — and the element values are asserted against the table first, so a table
revision breaks the test at the value it changed rather than at a statistic three lines later.
Agreement: **1.9e-16** relative at worst. If you need a second worked example, `Ti1Fe1` gives
`avg = (a+b)/2`, `dev = |a−b|/2`.

#### The opening move

**#20, `featurize()`.** The last card of the layer before the gates, and it now carries four
obligations rather than two:

1. **The `int64` → `float64` cast for `temperature(K)`** (#19). `assert_contract` refuses the
   integer column by name; a candidate at 313.5 K truncates to 313 in silence otherwise.
2. **Call `CONTRACT.computability(composition)` before building a row** (#19). Seven of the 22
   are not computable everywhere. The contract answers per composition and names the blocking
   element — **ask before you build, do not fill after.** A NaN here is one median-fill away
   from a number that looks like a measurement.
3. **Read the published composite column; call `require_self_consistent()` on the composite
   properties you featurise** (#18). Cheap, once per property set.
4. **The parser is `hydms.data.load.parse_formula`, not `pymatgen.core.Composition`** (#87).

And **creating `hydms/descriptors/featurize.py` turns HG-1 red before you write a wrong line** —
the L13 sentinel names that module as its subject and has no `live` hook yet, so `audit()` will
report `L13 [unwired] #12`. That is the mechanism working. **Do not re-aim the sentinel's
subject.** #12 owes the hook and is `doing` precisely because it waits on #20; the two halves
are boxed on the two cards. HG-1 goes green again at 5/13.

---

### Handoff — 2026-09-04 (earlier) · #19 landed · written for #18, then #20

**Where the phase is.** Nineteen cards done. The tree is green: **481 tests**, ruff 0.8.4 and
mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, `gates run --fast` exit 0,
`audit()` unchanged at **4 of 13** — `hydms/descriptors/contract.py` is no sentinel's subject
either, and L13 still waits on `hydms.descriptors.featurize`, which is #20.

**#19, the 22-feature contract.** `hydms/descriptors/contract.py`: `CONTRACT` over 22
`FeatureSpec`s carrying `(name, statistic, table, property)`, `assert_contract(df)`,
`FeatureContract.from_names()` for #25's regeneration, `as_manifest()`/`from_manifest()` for
#4, and `computability(composition)` — the verdict the card existed to deliver. 42 tests.
The card told you to record computability per composition; measuring it first corrected
**three** of its own claims:

- **"Two of the 22" is seven.** The card folded the six JARVIS features into one because
  they all fail on the same element. As columns they are six, and a caller asking "can I
  build this matrix?" needs six answers. `dev_Gordy_electonegativity` is uncomputable on
  **266 of 1,279 rows / 236 of 1,115 compositions**; each JARVIS feature on `Eu1Ni5` alone.
- **The Gordy hole belongs to the citable edition, not to CBFV — so AC-2 cannot see it.**
  CBFV's copy of the Oliynyk table supplies `gordy_en` for **all twenty-one** elements the
  2024 revision leaves blank (Ce 4.5734, Hf 6.3704, Pr 4.6395, …). #16 made CBFV's table
  AC-2's reference input by necessity, so the gate will be green throughout while the
  shipped featuriser cannot build that column for 266 rows. That is the **second** defect
  AC-2 structurally cannot detect, after #17's wrong-axis reduction, and for the same
  reason both times. Boxed on **#21**; the trade — carry the feature and lose 266 rows, or
  drop the feature and keep them — boxed on **#24** and **#25** with the numbers.
- **The loss falls on AB5 and MIC, not on "AB5 and AB2".** Rows losing at least one feature:
  AB5 91/196 (46.4%), MIC 54/127 (42.5%), HEA 26.0%, AB 24.4%, SS 18.4%, MEA 11.0%,
  A2B 9.4%, **AB2 34/371 (9.2%)**, Mg 7.4%, LEA 0/26. The card's sentence was a physical
  intuition about where rare earths live; the Laves phases are barely touched.

**Two things the card did not ask about and the next cards need.**

- **The training column order was never persisted.** I went looking for `selected_train.csv`
  to pin it and found `Machine_Model/data/processed_data/` is not in the repository at all,
  and that all three committed listings of the 22 are sorted by three different keys —
  `feature_selection_report.csv` by SHAP, `feature_importance.csv` alphabetically,
  `feature_target_pearson_corr.csv` by correlation. There is no history to be faithful to,
  so the contract *declares* REPORT.md §3.2's SHAP order and the test asserts it against
  that CSV. AC-4 is protected by there being one declaration, not by matching the past.
- **`temperature(K)` is `int64` in the raw file and `float64` in the contract.** Every column
  is `float64`; the cast is #20's, and `assert_contract` refuses the integer column by name.
  Not tidiness: a candidate at 313.5 K truncates to 313 in an integer column, silently.

**One thing that was confirmed rather than corrected.** The naming rule — a feature is
`f"{statistic}_{property}"`, with a 13-entry alias map for CBFV's Oliynyk spellings, the
JARVIS half needing none because CBFV's `jarvis.csv` *is* NIST's file — is provably
regenerable: **2,685 names over 5 statistics × 537 properties, all distinct**, and the two
tables share **no** property name. `from_names(CONTRACT.names) == CONTRACT` is a test, and
it is the path #25 takes.

#### The opening move

**#18, the composites.** Now the only unblocked S3 card, and still smaller than it looks:
#16 settled R3 (the composites are per-element **columns** of the JARVIS table, so the form
is statistic-of-composite by construction) and #19 has already resolved and tested every one
of the five against `hydms.descriptors.element_data` — `polzbl_divi_atom_mass`,
`atom_mass_mult_therm_cond`, `bp_divi_atom_mass`, `first_ion_en_mult_X`,
`voro_coord_divi_mol_vol`. What is left is reproducing the statistic over the column and
pinning each against a hand-computed value. It chooses nothing.

**Then #20**, which unblocks the rest of the layer and carries two obligations from this
card (the `int64` → `float64` cast, and calling `computability()` before building a row) plus
the L13 sentinel going red the moment `featurize.py` exists. That is planned; #12 owes the
hook.

---

### Handoff — 2026-09-03 (earlier still) · #17 landed · written for #19, then #18

**Where the phase is.** Eighteen cards done. The tree is green: **439 tests**, ruff 0.8.4 and
mypy 1.13.0 clean, `check_board.py` and `check_freeze.py` OK, `gates run --fast` exit 0,
`audit()` unchanged at **4 of 13** — `hydms/descriptors/stats.py` is no sentinel's subject, and
L13 still waits on `hydms.descriptors.featurize`, which is #20.

**#17, the composition statistics.** `statistics(weights, values) -> Statistics` over `avg`,
`dev`, `range`, `max`, `min`, plus 28 tests and a committed CBFV golden. The card told you to
measure `dev` rather than assume it, and measuring it **confirmed the card** — it is the
fraction-weighted mean absolute deviation, exact to 0.0 against CBFV. Three things it found
instead, and each is now somebody's:

- **The axis is the whole card.** Reducing the natural `(n_compositions, arity)` batch over its
  fast axis makes numpy sum pairwise; over the leading axis it accumulates sequentially, and a
  padded exact zero is then invisible. The wrong axis differs from CBFV by **2.794e-09 on
  jarvis — over AC-2's 1e-9** — while the right one is **bit-identical**. `statistics()`
  transposes internally so no caller can get it wrong, and the tests state it as arithmetic
  rather than as a shape.
- **AC-2 cannot see that defect.** On the 22 selected columns the wrong axis costs only
  2.274e-12 and passes. A featuriser with a real numerical fault would go green today and red
  the moment #25 re-runs selection. Boxed on **#21**, together with the reason parity can never
  be an equality: `parse_formula` sorts elements by symbol, CBFV keeps parse order, and that
  alone moves a cell by up to 3.638e-12.
- **`docs/QA-PROTOCOL.md` §L2 asks for two invariances that do not exist exactly.** Permutation
  and rescaling hold to `atol = rtol = 1e-12` (measured need: 4.3e-16 and 5.3e-15) and no
  tighter — CBFV moves by 1.364e-12 when a formula string is merely *reversed*, on 293 of 400
  real formulae. The protocol is right to ask; it just cannot have them to the bit.

**One thing was fixed in passing, because it blocked the card.**
`scripts/build_element_tables.py` demanded `--oliynyk` and `--jarvis` even to write a CBFV
fixture needing neither — and those are one-off downloads the repository does not keep, so
**#16's own AC-2 reference fixture was already unregenerable on a clean clone.** Both are now
optional and must be given together; `--cbfv-statistics` is #17's golden. Recorded on #16.

#### The opening move

**#19, the 22-feature contract.** Its blockers are done and it is the card the last two have
been piling findings onto: it must record computability **per composition**, because `gordy_en`
is empty for 21 of the 55 elements and every jarvis property of europium is a sentinel. #17
deliberately left the property axis outside `statistics()` so that decision lands here rather
than being forced by an array shape.

**#18, the composites, is also unblocked** and is smaller than it looks — #16 settled R3, so
#18 reproduces a statistic over a per-element column and chooses nothing. Both feed #20.

---

### Handoff — 2026-09-03 (earlier) · #6 and #16 landed · written for #17

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
