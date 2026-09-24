# Phase H — Emergency Hardening & Forward-Prediction Delivery

**The implementation runbook.** Nine stages, executed in order. Each names its cards, its steps, and
the one command that says whether it is done.

- **The board** is [../kanban-hardening/](../kanban-hardening/). Cards are authoritative for what the
  work *is now*; this file is authoritative for the *order* and for why the phase exists.
- **The freeze** is [FREEZE.md](FREEZE.md). It is enforced by CI, not remembered.
- **The frozen programme** is [PRD-inverse-design.md](PRD-inverse-design.md) and
  [../kanban/](../kanban/). Neither is edited while this phase runs.

---

## 0. Why this phase exists

The objective is a **user-facing interface that predicts gravimetric capacity** (formula + temperature
→ H₂ wt%). Building it on the current pipeline would put numbers in front of users that this project
cannot defend.

[PRD-inverse-design.md](PRD-inverse-design.md) §2.2 records three validation leaks. A fresh audit of
`Machine_Model/src/` found **thirteen**, plus three findings worse than "optimistic by an unknown
margin". Those three are stated in [FREEZE.md](FREEZE.md) § Why; the full leak inventory is §1 below.

**Outcome:** a reproducible pipeline, a calibrated surrogate reporting an interval and a domain
verdict, an HTTP API with a documented contract, a Streamlit interface over that API, and a QA regime
that fails the build if any leak reappears.

---

## 1. The leak inventory

This table is the definition of done for stages S2–S4. Line numbers refer to the archival pipeline in
`Machine_Model/src/`, which is **read, never rewritten** (PRD §7.2).

| # | Site | Effect |
|---|---|---|
| **L1** | `Catboostmodel.py:604-606` — `final_model.fit(combined_pool, eval_set=test_pool, …)` | The **test set chooses the stopping iteration**, then is reported as held-out at `:684-686`. The plot legend at `:612` says "Test RMSE". *PRD leak 1* |
| **L2** | `benchmark_model_selection.py:335-336` — `nlargest(4, 'Val_Weighted_Orig')` | Ensemble members chosen on validation; the headline **Val R² 0.939** and its bootstrap CI are reported on that same set. *PRD leak 3* |
| **L3** | `CleanLab.py:90` via `:96-97` — `managed_df['target'] = np.where(mask, y_pred, y)` applied to **val and test** | Test ground truth replaced by model predictions; replaced points have residual exactly zero by construction. **Not in the PRD** |
| **L4** | `benchmark_model_selection.py:1156` vs `:1168`; `Catboostmodel.py:588` vs `:642-660` | The same `splits` object tunes and then scores — no nested CV |
| **L5** | `Catboostmodel.py:576-582`, `:654-658`; recovered `Opt_and_Stack.py:110-125,189,222-224` | Every CV fold early-stops on the fold it is scored on |
| **L6** | `Boruta_FeatEng.py:57-113`; `Feature_selection.py:47-109` | Selection fit on all 896 training rows before CV. *PRD leak 2* |
| **L7** | `benchmark_model_selection.py:895`, `Catboostmodel.py:522` | Row-level `StratifiedKFold`, no groups — **141 of 896 train rows (15.7 %)** share a formula across folds. Re-measured by #88 on the reproduced 893-row split and under the **canonical** key: **181 rows (20.3 %)**, against 144 under the raw string |
| **L8** | `split_data.py:48,55` — the split key is the **raw formula string** | 1149 raw strings collapse to **1115 normalised compositions**; **16 of them (35 rows) span two splits**. `Ce1Mg12`/`Mg12Ce1`, `Pr1Co5`/`Pr1Co5␠`, `Mg1Al1`/`Mg0.5Al0.5` |
| **L9** | `merge_datasets.py:46` — positional `concat` after `reset_index(drop=True)` | Silent row misalignment. Highest-severity **correctness** defect |
| **L10** | recovered `Ashghal/Outliers_Management.py:60-72` | Clips val/test **feature values** using their own residuals |
| **L11** | `benchmark_model_selection.py:1375,1383,1394` | PDP and SHAP computed on `X_test` — REPORT §6.1 is a test-set artefact |
| **L12** | `Catboostmodel.py:516-518` — `weights = np.where(np.expm1(y) > 3, 2.0, 1.0)` | Target-conditioned weights with a hand-tuned threshold |
| **L13** | `extract_features_cbfv.py:19-21` drops every object column but `Composition` | Destroys `Alloy_class`. **Blocks leave-one-alloy-class-out CV (#30)** — the PRD's most important validation number. #87 gives the class a composition to be re-joined on and writes its sentinel; **#12 closes it** by carrying the class through featurisation |

Two blockers that are not leaks:

- `elem_prop='magpie'` at `extract_features_cbfv.py:31` produces **none** of the 21 published
  descriptors. The real set is 15 `oliynyk` + 6 `jarvis` + `temperature(K)`, resolved by card #8 in
  [../hydms/descriptors/FEATURE_PROVENANCE.md](../hydms/descriptors/FEATURE_PROVENANCE.md).
- REPORT §3.3's "five-stage selection with a correlation filter" **exists in neither selector**.
  Card #24 repeated that description and has been corrected.

---

## 2. Execution order

```
S0  Freeze & tooling          ───────────────────────────►  (nothing blocks it)
S1  QA foundation             ──►  needs S0
S2  Data layer                ──►  needs S1
S3  Descriptor layer          ──►  needs S0   (parallel with S2)
S4  Surrogate layer           ──►  needs S2 + S3
S5  Guard rails               ──►  needs S4
S6  Delivery: contract + API  ──►  needs S5
S7  Delivery: interface       ──►  needs S6
S8  Evidence & close          ──►  needs S7
```

S2 and S3 are the only parallelism worth taking. Everything else is a chain.

**Five cards sit outside that list** — #4, #6, #7, #73, #74 — foundation and CI work that slots in
where its blockers allow. #4 is the one S4 waits on, and it landed 2026-09-04, before S4 opened:
#23's "persist the scaler, never refit" has nowhere to persist to without it. **#73 and #74 landed
2026-09-07**, after S4 closed rather than during S1, which is what "slots in where its blockers
allow" means in practice: both need `predict()` (#28), so neither could have been written earlier.
#73 is the end-to-end smoke run — `python -m hydms.pipeline.smoke`, 12.1 s over a committed
235-row fixture — and it runs the **live** stage order, not the archival one its card's arrows
describe; #74 is the metamorphic suite. Both are in the fast lane and neither is marked `slow`.

- **`artifacts/v{N}/`** holds one `manifest.json` and one `<name>.joblib` per saved object.
  `hydms.artifacts.save()` and `.load()` are the only doors. A version is staged under a dotted
  name and renamed into place, so a run that dies part-way leaves nothing that looks like a
  version, and an existing version is never overwritten — later phases pin what they consume.
- **The manifest records five things**: the git SHA and whether the tree was dirty, every seed,
  the resolved versions of the packages that determine a fit, the feature contract with its own
  digest, and the gate results embedded verbatim as `hydms.gates` wrote them.
- **A version whose recorded gates did not all pass does not load and cannot be promoted**, and a
  `SKIPPED` gate counts. That is stricter than the harness's own `ok` flag on purpose — see §4.
  `require_gates=False` is the deliberate, visible escape for a card that has just written a
  version and wants it back; the delivery path never passes it.
- **Promotion is `current.json`, and it is the only place a criterion may be set aside.** Rollback
  is a pointer write, not a retrain (#7). A promotion may also record **waivers** — criteria it
  knowingly proceeds without, named one at a time and never by pattern. A `FAILED` criterion is
  never waivable; the manifest never learns about a waiver, so an artifact's account of what was
  *measured* is unaffected; and a waiver dies when the pointer moves. It exists because AC-5, AC-7
  and AC-8 belong to frozen phases and no Phase H work makes them green (#34). Which criteria a
  frozen phase owns is derived from the board by `tests/artifacts/test_waiver_scope.py`, not
  remembered.

---

## 3. Stages

**S0–S6 are closed and their detail has moved.** Every card in the seven stages of the table below
reached `done`; **S7 and S8 follow it in full.** The closed stages' checklists, exit checks and
boxed reasoning are in
[archive/PHASE-H-STAGES-CLOSED.md](archive/PHASE-H-STAGES-CLOSED.md), verbatim. What is left here is
one line each, so the shape of the phase is still readable in one screen.

| Stage | Cards | What it established | Where it is now |
|---|---|---|---|
| **S0** — Freeze and tooling | #72 | The freeze exists and is enforced by `check_board.py` + `check_freeze.py` before any code moved | [FREEZE.md](FREEZE.md) |
| **S1** — QA foundation | #69, #70, #5, #71 | `tests/`, the three tool configs, the gate harness, and **HG-1's one sentinel per named leak** — the mechanism that makes §1's inventory un-reintroducible | [QA-PROTOCOL.md](QA-PROTOCOL.md), gate HG-1 |
| **S2** — Data layer | #3, #9, #10, #11, #87, #12, #13, #14, #15 | Schema-validated loaders, the **keyed** merge that replaced the positional `concat` (L9), the canonical composition key (L8), stratified unique-formula splits, CleanLab as a screening *stage* | `hydms/data/` |
| **S3** — Descriptor layer | #16–#22 | Cited element-property tables, weighted composition statistics, the **22-feature contract**, and AC-2 parity with CBFV to 1e-9 | `hydms/descriptors/`, [BENCHMARKS.md](BENCHMARKS.md) |
| **S4** — Surrogate layer | #23–#34, #88 | Scaler fit once and never refit (L1), selection inside the folds (L4), CatBoost multiquantile with honest early stopping (L7), MAPIE conformal calibration, LOACO, and the **deployed artifact `v3`** | `hydms/surrogate/`, [RUNNING-THE-FIT.md](RUNNING-THE-FIT.md) |
| **S5** — Guard rails | #44, #48, #49 | The screen interface — a verdict with a reason, never a silent drop — the applicability-domain ceiling, and the ElMD novelty distance | `hydms/screens/` |
| **S6** — Delivery: contract + API | #75–#80, #90 | The request/result/refusal contract, `predict_capacity` over an **immutable artifact bundle**, gate HG-2 (never a bare number), the FastAPI service, HG-3 transport parity, and the published `docs/API.md` | `hydms/delivery/`, [API.md](API.md) |

---

### S7 — Delivery: the interface · #81–#84 · 3.5 d

**The deliverable.** Streamlit is an **HTTP client**, not an in-process caller, so the API stays the
single prediction path and HG-3 covers the UI too.

- [x] **#81** App chart vocabulary in `hydms/figures/`. **Done 2026-09-12.** Five charts, each
      chosen because it makes a false prediction harder to believe:
      1. **Prediction band** — the point estimate drawn *inside* its conformal interval, width stated
         numerically. A wide band must look wide.
      2. **Domain strip** — where this composition sits against the training distribution and the AD ceiling.
      3. **Temperature sweep** — predicted wt% across the valid T range with the interval as a band.
         ~~Only 39 test rows sit above 500 K~~ — that is `REPORT.md`'s count over the archival
         **247-row test split**, which this protocol no longer has. Measured against
         `reports/model/model-out-of-fold.csv`: **130 of 893** scored rows sit above 500 K. The
         claim is unchanged (15.8% then, 14.6% now); only the number was inherited. The string
         still stands in four docstrings and two tests — that is **#99**.
      4. **Nearest neighbours** — the k closest training alloys by ElMD with their *measured* capacities.
      5. **Parity plot** *(model card)* — predicted vs measured, with the **LOACO** version beside it
         at the same scale. `parity()` refuses fewer than two readings, so the optimistic panel
         cannot ship alone — **and the LOACO panel has no data**: `train` writes
         `evaluation.out_of_fold`, `loco` does not, so `reports/loco/` holds ten class averages and
         no scored rows. That is **#98**, and it needs a run.

      **The shape it landed in.** A chart is a *description* before it is an image:
      `hydms/figures/charts.py` builds `Figure` objects and imports no plotting library;
      `render.py` draws one in matplotlib. Every promise above is a construction error in the
      description — a predicted `Series` cannot exist without a band, a quantitative `Axis` cannot
      exist without a unit, a `Panel` refuses a series its axis would clip (so a builder widens the
      axis instead), and `Figure.shared` makes "at the same scale" checked rather than intended.
      Put in the renderer, each would have been a guarantee that runs only where a plotting library
      is installed. matplotlib is a new `figures` extra, already in both lock files, and **CI
      installs it**.
- [ ] **#82** `app/main.py` — formula + temperature → capacity. **`doing` since 2026-09-24.**
      The guarantees are in `hydms/delivery/client.py` (HTTP, stdlib `urllib`) and
      `hydms/delivery/page.py` (what the page shows), tested against uvicorn on a real socket.
      `app/main.py` is a thin Streamlit layer and **has never run**: Streamlit is not in `Project`,
      and an unpinned install would move `starlette` past what `fastapi` 0.115 accepts. That is a
      lock decision for the maintainer. Neighbours and the sweep's support counts are **not
      served**, so those two boxes need an API contract change first.
- [ ] **#83** `app/pages/` model card. **Must carry two things** or the UI recreates the problem it was
      built to fix: the material-vs-system caveat from PRD §4.4 (comparing a material wt% to a DOE
      system target is a two-step overstatement), and a link to `docs/REPORT-RECONCILIATION.md` so the
      old published figures are not quietly inherited.
- [ ] **#84** Batch CSV screening page.

**Exit check:** `conda run -n Project streamlit run app/main.py` plus the manual acceptance in §5.

---

### S8 — Evidence and close · #89, #85, #86, #35, #36, #37 · 5 d

- [x] **#89** `docs/REPORT-RECONCILIATION.md`. **Done 2026-09-24.** Generated by
      `python -m hydms.evidence.reconciliation --emit`, **twelve** disagreements rather than eight.
      The audit's eight were never enumerated, so the table is a re-measurement. Every quotation
      is tested to occur in `REPORT.md` verbatim and every refuting value is read from its CSV.
      The headline finding: two committed CSVs describe two different ensembles.
      *Original entry follows:* the eight prose-vs-artifact contradictions, each with
      the CSV that refutes it. **REPORT.md is not corrected in place**; it is the archival record.
      **Unblocked since 2026-09-11** — `blocked_by` is now `[29, 30]`, the two cards that produced
      the honest numbers it sets beside the published ones, and both are `done`. It is the one piece
      of S8 that can be written today, and two later cards want it: #83's model card links to it and
      #37 is written from it.
- [x] **#85** ADR — the delivery seam and why the API owns no ML logic. **Landed 2026-09-12**
      with #80, as `docs/adr/0006-the-delivery-seam.md`. It argues **both** directions: the API
      owns no ML logic, *and* the library owns no I/O — and the second is the one a future reader
      will push on, because #91's rejected alternative (the library owning its own prediction
      record) is a real guarantee. The cost is stated plainly rather than hidden: **a script that
      imports the library leaves no record.**
      It carries the five decisions #76 and #78 owed it, each with the argument that forces it:
      the assembly order (screen-before-featurise does not exist — the domain screen reads a
      prediction); novelty in `delivery_screens()` (the cost was already paid by `pyproject.toml`
      and the GPL); one cache or two; 422 shared between a refusal and an invalid request (two
      authorities, neither bendable, so the split moved into the body); and the transport
      declaring less than it can (one owner per rule, one level down).
      **It is `0006`, not `0001`:** `0001`–`0005` are reserved for #36's five, whose done-when
      names that glob. `docs/adr/README.md` records the reservation and #36's standing decision
      that the card is not renamed.
- [~] **#86 (HG-4)** Extend the CI fast lane with the delivery suite, the freeze check, and
      ruff / mypy / coverage. **Gate written and CI wired 2026-09-12; one box open.** It found
      that **CI has never completed the `suite` job on this branch** — every push run is
      `cancelled` or `failure`, the newest annotated *"exceeded the maximum execution time of
      20m0s"* — because the job ran the full 24 m 58 s suite against a 20-minute cap. It now
      runs `-m "not slow"`, which is what `pyproject.toml` has said the marker means since #69.
      It also found CI's `mypy` red on six `import-not-found` errors that **cannot reproduce on
      the maintainer's machine**, because this interpreter has fastapi and pydantic and the
      runner does not. Coverage is **88.43 %** against the 80 % floor. The open box is the
      timeout itself, and it waits on **#93**: the first completed `suite` job
      (`34696231293`, 13 m 40 s against a 20-minute cap) reported two failures that pass on the
      maintainer's machine. ~~That is a claim about the surrogate's arithmetic on other
      hardware, not about the lane.~~ **It was not about hardware** — see #93.

- [~] **#93** The two CI-only failures. Filed by #86; **not an unfreeze condition**, but #86's
      last box waits on it. **Diagnosed 2026-09-12, and the answer is the `pip install` line, not
      the runner.** `suite` installs from `pyproject.toml`'s floors rather than
      `requirements-lock.txt`, and `catboost>=1.2` resolved to **1.2.10** against the `Project`
      environment's **1.2.8**. A venv on the resolved versions reproduces both failures **on the
      maintainer's own Windows box**, to every digit the runner printed, so neither failure needs
      a CI round trip to see. Both tests were asserting more than the code guarantees:
      `test_calibration_moves_coverage_toward_nominal` compared a constant — calibrated coverage
      on the calibration rows is the conformal rank over n, `46/56`, identical on every
      configuration — against the *raw* coverage, which is the fitted half and moved 49/56 →
      44/56; and `test_the_width_is_the_calibrated_span_and_varies_row_to_row` demanded positive
      widths from three extrapolation candidates when `quantile_metrics` measures quantile
      crossing at **23 % of rows** and `conformal.py` states that CQR cannot repair one. Restated
      as what is guaranteed; **no tolerance was widened and AC-3 inherits nothing**. The lane's
      environment obligation lands on **#7**, and what the delivery layer should *say* about a
      crossed band lands on **#94**.

- [ ] **#94** A crossed band raises where it should refuse. Filed by #93; **not an unfreeze
      condition**. `hydms.delivery.contract.Interval` raises `ContractError` on `upper < lower`
      and nothing between the surrogate and that boundary looks at the sign, so a crossed
      candidate is a loud failure rather than a refusal carrying a reason code.
- [ ] **#100** A render test passes alone and fails after the slow tests — **intermittent, and the
      renderer no longer has the state it would need to be order-dependent.** Four full-length
      runs after the filing are green (134, 1530, 1530 again, and **1531 in 26 m 45 s post-repair
      on a quiet machine**), so no traceback exists and none can be manufactured. `hydms/figures/render.py` no longer chooses a
      backend or imports `pyplot`, and a subprocess test holds it that way. The card stays `doing`
      on one box — the traceback — which only a future red run can tick. Filed by #81,
      2026-09-12; **not an unfreeze condition**, and `High`.
      `tests/test_figures.py::test_every_figure_renders_in_both_themes` passes on its own (55),
      in the fast lane (1526) and beside the four `slow` tests (134) — and fails in a full run.
      ~~the trigger is one of the four `slow` tests~~ was the filing hypothesis and is **refuted**:
      both halves are green and only the whole is red. **CI runs `-m "not slow"` and will never
      report it.** The traceback was discarded by a truncating pipeline and no subset reproduces,
      so a full 29-minute run redirected to a file is the price of the next step.
- [ ] **#98** The LOACO run discards its own per-row predictions. Filed by #81, 2026-09-12;
      **not an unfreeze condition**. `hydms/surrogate/train.py:369` writes
      `evaluation.out_of_fold` as a table and `hydms/surrogate/loco.py:595` writes four tables
      without it, so the honest protocol leaves aggregates and the optimistic one leaves 893
      scored rows. The code change is small; the run is the maintainer's. It holds #83's parity
      figure shut.
- [ ] **#99** A REPORT.md number is quoted as current in four docstrings. Filed by #81,
      2026-09-12; **not an unfreeze condition**. *"Only 39 test rows sit above 500 K"* is
      `REPORT.md:394`'s count over the archival test split; the measured figure is 130 of 893.
      The claim is unaffected and the number is not; `REPORT.md` itself is not touched, which is
      #89's business.
- [ ] **#96** An output flag that silently changes the fit. Moved off #34 at its close, 2026-09-12;
      **not an unfreeze condition**. `calibrate --report` is both where a run writes its tables and
      where `deploy.py:163` reads `model-chosen.csv`, so redirecting it to a scratch directory falls
      back to CatBoost's own defaults and `--save` persists that as `deployed fit`. It produced a
      correction of +0.030990 instead of +0.037355 on 2026-09-07 and was discarded.
- [x] **#35** `CONTEXT.md` glossary. **Closed 2026-09-06** by the review session — the terms are
      in it because conflating them has already cost this project something.
- [~] **#37 drafted 2026-09-24** as [chapter1-revision.md](chapter1-revision.md): `doing`, one box
      open. The artifact score (R² 0.7071) and the test coverage (0.7795) are quoted from the
      gitignored `artifacts/v3/manifest.json` and marked † in the chapter. A committed report of
      them is owed (currently a box on #83, which is blocked by #82). **#36 is still `backlog`.**
- [ ] **#36** five ADRs · **#37** Chapter 1 revision. ~~#37 is unblocked on everything but #34.~~
      ~~**#37 waits on #34 *and* #89**~~ (edge added 2026-09-11). **#34 closed 2026-09-12, so #37
      waits on #89 alone, and #36 is unblocked outright.** The #89 edge stands and is the load-
      bearing one: #89's card says the reconciliation is "what card #37 is written from", and
      writing the chapter first would mean re-deriving those eight disagreements by hand, in prose
      nothing checks.
- [ ] Lift the freeze: set `freeze: lifted` in [FREEZE.md](FREEZE.md), record the closing date, and the
      PA/PB board resumes.

---

## 4. Gates

Inherits **AC-1 … AC-4** and **AC-6**. AC-5 is thermodynamic and AC-7/AC-8 are inverse-design; all
three stay frozen.

**The harness exists** (card #5). All twelve criteria are registered — the frozen three included, so
the registry is the complete list of what this project has promised to check rather than the list it
is currently able to check:

```bash
conda run -n Project python -m hydms.gates list          # every gate, its lane, its owning card
conda run -n Project python -m hydms.gates run --all     # the whole registry
conda run -n Project python -m hydms.gates run --fast    # the per-push lane (card #6)
conda run -n Project python -m hydms.gates run AC-2      # one gate; a skip here exits non-zero
```

Three properties are worth knowing before you write a gate:

- **A skip is never a pass.** An unimplemented criterion reports `SKIPPED`, the table prints a
  `NOT CHECKED` banner naming every one of them, and `--strict` turns any skip into a failure.
- **Naming a gate makes the run strict.** `run HG-4` exits non-zero while HG-4 is unimplemented —
  which is why the `## Runnable check` on #31, #32, #33, #71 and #86 is honest from the day it
  is written. **HG-3 is no longer one of them either**: `run HG-3` exits 0 against a version on disk,
  and `SKIPPED` (exit 1) in a checkout with none — the OpenAPI comparison and the request-door check
  still run there and can still fail. **HG-2 is the same**: `run HG-2` exits 0 against a version on disk, and
  `SKIPPED` (exit 1) in a checkout with none, which is the honest answer — the structural half
  still runs there and can still fail. `run --all` tolerates skips, because CI that is red for the length of the phase is CI
  nobody reads. **AC-2 is the first gate for which this is no longer true**: `run AC-2` exits 0, in
  an environment that has CBFV. Without CBFV it reports `SKIPPED` and exits 1, which is the honest
  answer — CI's `suite` job installs no `parity` extra on purpose, so the criterion is established
  on the machine lane and CI records that it did not establish it.
- **Each gate declares its own lane.** `Speed.FAST` means answerable against the published artifact;
  `Speed.SLOW` means it needs a retrain. Cards #6 and #7 select on that rather than deciding it.

A run writes its results as JSON under the configured artifacts directory, behind a versioned
`schema` key, beside the version directories. `hydms.artifacts.save(..., gates=report)` embeds
that same object under a version's manifest, and a version whose recorded gates did not all pass
will neither load nor promote — a skip counts, which is stricter than the harness's own `ok` flag
and deliberately so (card #4). The one exception is a **waiver** named at promotion time, which
lives in `current.json` and never in the report; see §2's artifact-store bullets and card #34.

| Gate | Card | Fails when |
|---|---|---|
| **HG-1** Leak sentinels | #71 | Any leak in §1 can be reintroduced without a test going red: a detector stopped firing, a sentinel's subject module exists with nothing wired to it, or a leak has neither a sentinel nor a recorded deferral. Green only when all thirteen are checked against the real pipeline |
| **HG-2** No bare numbers | #77 | A contract type gains a default for `interval` or `domain`; any `return` in `predict_capacity` stops being a `Refusal` or a `PredictionResult`; a probe comes back without a code, a sentence, or the thing its refusal is about — named *outside* the echo of the formula that was typed, since every sentence here quotes its input and `'Xx'` is in `'Xx2'`; a declared code stops being reachable through either door with nothing saying why; or a code with no input at the request door becomes reachable there. Skips, loudly, where no artifact is on disk or where every probe was refused |
| **HG-3** Transport parity | #79 | The API's answer differs from `predict_capacity()`'s for the same input at any JSON pointer; a served body cannot be rebuilt by `answer_from()` into an equal object; a batch reorders its rows, fails whole over a refused row, or does not enforce the limit it publishes; a rejected request carries `refused`, or `answer_from()` reads one as an answer; the committed OpenAPI document is not what the code produces; the request model declares a field `PredictionRequest` does not, or stops forbidding unknown ones; `/v1/health` or `/v1/model` names a version other than the one that answered. Skips, loudly, where no artifact is on disk or the `api` extra is absent — the document and the door are checked first either way |
| **HG-4** Hygiene | #86 | ruff or mypy fail on `hydms/ tests/ scripts/`, or the coverage floor in `[tool.coverage.report]` is not met. Runs the tools rather than reading a log — ruff is 0.045 s and a warm mypy 2.33 s, so re-asking is cheaper than trusting. Skips, loudly, where a tool is absent from `PATH`, where there is no `pyproject.toml` to lint by, or where no `pytest --cov` has been run; and **refuses to report a coverage number from data older than the newest file under `hydms/`**, because `pytest --cov` writes its data only when the run ends, so a gate running inside that suite would otherwise score the previous run |
| AC-1 | #32 | Same seed does not reproduce identical metrics |
| AC-2 | #21 | The featuriser does not match CBFV to 1e-9 on all 1,279 formulae |
| AC-3 | #31 | Conformal coverage does not match its nominal level |
| AC-4 | #33 | Known alloys do not round-trip through `predict()` |
| AC-6 | #30 | Leave-one-alloy-class-out R² is not reported beside the random-split number |

---

## 5. Verification

```bash
# Board and freeze integrity (stdlib only, no environment needed)
python scripts/check_board.py --root .
python scripts/check_freeze.py --base origin/main

# NOT one of the cheap checks: this rebuilds a throwaway conda env from both lock files,
# roughly 8 GB and 15-20 minutes. Run it by hand after touching an environment file, never
# in a routine pass. As of 2026-09-03 it fails at stage 1 on this machine with an HTTP 403
# from repo.anaconda.com/pkgs/main; re-probed 2026-09-12 and the 403 is permanent, not an
# outage. `python` and `numpy` themselves come from the blocked `defaults` channel (95 of 248
# conda packages do), so this command cannot pass here until the lock is re-solved. The three
# remedies and their costs are the open box on card #1 -- do not start a re-solve unasked.
python scripts/verify_environment.py

# Suite. TWO numbers live here and they are different commands; do not compare them. The FULL run
# below was last measured at **1531 passed, 0 skipped on 2026-09-13 (26 min 45 s)** on a quiet
# machine, post-#100 — the previous entry here was 1229 in 24 min 58 s on 2026-09-07, which the
# cards since have grown past. The FAST LANE (`-m "not slow"`, which
# deselects the four `@pytest.mark.slow` tests) reported **1440 passed / 4 deselected of 1444
# collected on 2026-09-12 (12 min 3 s)** — up from 1371/1375 the same day by #78's service and
# #79's gate, and from 1308/1312 after #90 on 2026-09-07. That is the figure the recent handoffs
# quote. **Latest: 1583 passed / 4 deselected WITH `--cov` (89.42 %) on 2026-09-24, 53 min 7 s on a
# quiet machine** (only that pytest process running), after #82's app tests and #89's evidence
# tests. A handoff that
# states one of these must say which.
#
# AND IT MUST SAY WHETHER THE MACHINE WAS QUIET, which card #100 learned the expensive way on
# 2026-09-13: two sessions spent this 29-minute command concurrently, ~18 minutes of it
# simultaneously, and one of them landed a source edit WHILE the other's run was still going. pytest
# imports test modules at collection but a production module whenever the code first reaches it, so
# that run tested the old test body against the new renderer — a combination nobody wrote, and a
# green that meant nothing. Before a run you intend to quote:
#     Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select ProcessId, CreationDate, CommandLine
# and print Get-Date either side of the command, so an mtime inside that window tells you the run is
# not a measurement. Contention costs only a minute or two of wall time here (26 m 45 s quiet against
# 28 m 24 s contended), so the number that misleads you is the PASS, not the duration.
# Anything red is a real failure. Do NOT pass -q: pyproject already sets
# it, and a second one hides the `N passed` line every handoff quotes. THERE IS NO SKIP, and that
# is new: test_the_committed_document_is_what_the_code_produces was waiting on the 4.7-hour LOCO
# run, which happened on 2026-09-06, so it now asserts the committed reports/loco/loco.md against
# what `loco --emit` builds. A skip reappearing there means the tables have gone missing, not that
# a test is quarantined.
#
# THE FULL RUN IS NOT WHAT CI RUNS, as of card #86 (2026-09-12). CI's `suite` job runs
# `-m "not slow"` because the full run does not fit its 20-minute cap and never did — every
# push run on this branch was `cancelled` or `failure`, the newest annotated "exceeded the
# maximum execution time of 20m0s". So the FULL run below is the maintainer's command and the
# only place the four slow tests are executed at all until card #7's slow lane exists.
# Measured 2026-09-12 WITH `--cov`: 1443 passed in 37 m 52 s, TOTAL coverage 88.43 % against
# the 80 % floor in [tool.coverage.report]. `--cov` needs pytest-cov, which card #86 installed
# into `Project` (pytest-cov 7.1.0 + coverage 7.16.0, no existing pin moved).
conda run -n Project python -m pytest
conda run -n Project python -m pytest -m "not slow" --cov   # what CI actually runs
conda run -n Project python -m pytest tests/leaks               # HG-1
# Lint and types run OUTSIDE the environment, deliberately: neither imports the project's
# dependencies, and card #68 fixed that the fast lane installs nothing (docs/QA-PROTOCOL.md §6).
#
# A GREEN `mypy` HERE IS NOT EVIDENCE ABOUT CI, and card #86 found that out the expensive way
# on 2026-09-12: the hygiene job was failing on six `import-not-found` errors for fastapi,
# uvicorn and pydantic that cannot occur on this machine, because this interpreter happens to
# have them installed and a bare runner does not. The overrides in pyproject now cover them.
# When you add an import under `hydms/` that is not in `[[tool.mypy.overrides]]`, ask the lane
# the way the lane asks it — a bare interpreter, nothing installed but mypy:
#     python -m venv /tmp/barelint && /tmp/barelint/bin/python -m pip install mypy==1.13.0
#     /tmp/barelint/bin/python -m mypy
# Keep the version equal to the workflow's; `tests/test_tooling.py` asserts the `dev` extra and
# the workflow name the same ruff and the same mypy, so a bump is one commit touching both.
ruff check hydms/ tests/ scripts/ && mypy
# `run` with no selection exits 2 -- a selection is a decision, so name one.
conda run -n Project python -m hydms.gates run --all           # 8 passed, 0 failed, 4 skipped (3.0 min)

# Pipeline: one command, no absolute paths (AC-1); same seed twice -> identical output.
# This is the SMOKE run (card #73), not a retrain: every stage over a committed 235-row fixture
# in about 12 s, answering "does the chain connect" and nothing about accuracy. `--digest` prints
# only what a second run with the same seed must reproduce. The real run is `hydms.surrogate.train`
# and `hydms.surrogate.calibrate` (docs/RUNNING-THE-FIT.md), which is hours.
conda run -n Project python -m hydms.pipeline.smoke
conda run -n Project python -m hydms.pipeline.smoke --digest

# The published contract, and the cheapest check in this block: it builds the OpenAPI document
# from the code and compares it to the committed `hydms/delivery/api/openapi.json`, exiting 1 and
# printing the pointers that moved when they differ. `--emit` rewrites the file; commit the diff
# deliberately, because it is what a client author reads. Gate HG-3 runs the same comparison, and
# this is the half of it that needs no artifact and no environment beyond the `api` extra.
conda run -n Project python -m hydms.delivery.api.openapi

# API. It resolves the PROMOTED version at startup and refuses to start if there is none. Until
# 2026-09-12 this command exited with `load_bundle`'s own sentence -- "nothing is promoted in
# artifacts" -- and that was card #34 working, not a fault. **#34 closed that evening: `current`
# points at `v3`, so the service now starts.** It still refuses on a fresh clone, because
# `artifacts/` is gitignored and the promoted version is on one machine. The two checks below
# were run against the real `v2` through the gate door on 2026-09-12 and produced exactly what
# they say they will. `python -m hydms.delivery.api` is the same thing with the uvicorn line
# remembered for you.
conda run -n Project uvicorn hydms.delivery.api:app --port 8000
curl -s localhost:8000/v1/model
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"LaNi5","temperature_k":298}'
# expect: estimate + interval + level + domain verdict + elmd + model_version
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"Xx9Zz3","temperature_k":298}'
# expect: a structured refusal with a reason, HTTP 422 — never a number.
# Measured against `v2` on 2026-09-12: code `indeterminate`, and the sentence is the
# featuriser's own — "'Xx9Zz3' names 'Xx', which is not a chemical element".
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"","temperature_k":298}'
# expect: ALSO 422, and a different body — `error: invalid_request`, no `refused` key. The
# status cannot separate a declined material from an unreadable request; the body is what does.
curl -s localhost:8000/v1/health   # {"status":"ok","model_version":"v2","max_batch_rows":256}

conda run -n Project streamlit run app/main.py
```

> **`pytest --cov` does not run here yet.** Neither `pytest-cov` nor `coverage` is installed in
> `Project`, so the coverage floor in `pyproject.toml` is unenforceable anywhere today — the command
> exits with `unrecognized arguments: --cov`. Both are declared in the `dev` extra and nothing
> installed them. Where they get installed is card **#86**'s decision, because adding a package to
> `Project` invalidates `environment.lock.yml`.

**Manual acceptance for the interface**

- A known training alloy returns the model's prediction for that row (AC-4 at the UI boundary).
- `Mg12Ce1` and `Ce1Mg12` return the **same** answer — L8 fixed, visibly. They already share one
  canonical key (`Ce0.07692Mg0.9231`, #87), and since #74 the *prediction path* is asserted on all
  six known collision pairs as well (`tests/test_metamorphic.py`), so what is left here is the UI
  boundary rather than the library.
- A plausible-but-far composition visibly widens the interval and flags the domain.
- Nonsense is refused with a reason, not answered.

---

## 6. Assumptions, risks, and what is deliberately out

- **Ids were preserved when cards migrated boards.** Renumbering from 1 would break every `blocked_by`
  edge, every `Traces to` link, and the `## Narrative` notes the ADRs and #37 are written from — and
  `check_board.py` enforces exactly that integrity. The two directories are a **freeze boundary, not
  an id-space boundary**; blockers reach across them and are checked as one graph.
- **#44, #48, #49 were pulled out of the frozen PA phase.** Without them the interface has no refusal path.
- ~~**#18 is the live technical risk (R3).**~~ **Closed 2026-09-04, and it never was one.** #16
  settled R3 from the source data before #18 started — a composite is a table column, so the form
  is statistic-of-composite by construction — and #18's measurement of the rejected order (1.8% to
  65x off CBFV) only confirms it. What #18 found instead is that eleven of the table's 156
  composite columns are not their own arithmetic. #21 is still gated by #20, not by this.
- **Expect the headline numbers to fall, substantially.** Risk R4 anticipates it; given L2 and the
  contradicting CSVs, the fall will be large. Per the PRD that is *a reported result, not a failure*.
- **Scope:** ~31 board-days of existing cards + 4 migrated + ~15 new ≈ **50 developer-days** for one
  developer. That is a rebuild, not a patch, and it sits in tension with the word *emergency*. It is
  the honest cost of the chosen scope.
- **Out of scope:** `ML-HYDPARK_v0.0.5.csv`'s ΔH/ΔS columns and `database/combined_dataset.csv` stay
  unused — they belong to the frozen thermodynamics work (#38–#43). `Machine_Model/**`, `REPORT.md`
  and the inverse-design PRD are read, never rewritten.

**Three gaps this phase will close only if somebody decides to** (added 2026-09-06, from a review;
each is boxed on a card, and none is a defect in what was built):

- **`artifacts/` is gitignored, so nothing this phase ships has ever been seen by CI.** The model,
  its manifest and `current.json` exist on one machine. This is not only a reproducibility risk
  (card #7 owns that half) — it is also why two checks had to move after being written: the
  waiver-scope rule left `check_board.py` because a rule about a *committed* `current.json` could
  never fire, and `reports/loco/` had to be un-ignored so AC-6 would not read an empty directory in
  CI. **Check whether a file reaches CI before writing a check that reads it** is now a two-instance
  pattern, and it is the stated reason HG-1's mechanical subject check is deferred on #71.
- **A gate can be green over a sentinel whose subject moved.** Measured: five hours twenty-one
  minutes in which L11 guarded `model.final_fit` while the shipped object was
  `deploy.deployed_fit`, with HG-1 reporting 13/13 throughout. `docs/QA-PROTOCOL.md` §5 now carries
  the rule; the mechanical check is deferred with its reason, because every available proxy is
  weaker than the structural fix that landed (one module both callers call).
- **Two measured results are published nowhere.** The deployed model's own held-out score, computed
  by AC-1 as a side effect, and the near-ambient temperature bin's near-zero R² in
  `evaluation-subgroups.csv`. Both are boxed on #83. The pattern is worth naming because this phase
  exists because of it: **a number that only a gate message or an uncommitted file has ever held is
  not published**, and the distance between "measured" and "published" is where REPORT.md went
  wrong in the first place.
