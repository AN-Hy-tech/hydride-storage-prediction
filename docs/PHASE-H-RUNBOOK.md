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

**Closed work is one line per stage; the detail is archived verbatim** in
[archive/PHASE-H-STAGES-CLOSED.md](archive/PHASE-H-STAGES-CLOSED.md) (S0–S6 from 2026-09-13, S7–S8
from 2026-09-26). What is still open is ranked in [PHASE-H-FINDINGS.md](PHASE-H-FINDINGS.md).

| Stage | Cards | What it established | Where it is now |
|---|---|---|---|
| **S0** — Freeze and tooling | #72 | The freeze exists and is enforced by `check_board.py` + `check_freeze.py` before any code moved | [FREEZE.md](FREEZE.md) |
| **S1** — QA foundation | #69, #70, #5, #71 | `tests/`, the three tool configs, the gate harness, and **HG-1's one sentinel per named leak** — the mechanism that makes §1's inventory un-reintroducible | [QA-PROTOCOL.md](QA-PROTOCOL.md), gate HG-1 |
| **S2** — Data layer | #3, #9, #10, #11, #87, #12, #13, #14, #15 | Schema-validated loaders, the **keyed** merge that replaced the positional `concat` (L9), the canonical composition key (L8), stratified unique-formula splits, CleanLab as a screening *stage* | `hydms/data/` |
| **S3** — Descriptor layer | #16–#22 | Cited element-property tables, weighted composition statistics, the **22-feature contract**, and AC-2 parity with CBFV to 1e-9 | `hydms/descriptors/`, [BENCHMARKS.md](BENCHMARKS.md) |
| **S4** — Surrogate layer | #23–#34, #88, #97, #98, #104–#106 | Scaler fit once and never refit (L1), selection inside the folds (L4), CatBoost multiquantile with honest early stopping (L7), MAPIE conformal calibration, LOACO with its per-row predictions, a run record beside every run, and the **deployed artifact `v3`** | `hydms/surrogate/`, `hydms/provenance.py`, [RUNNING-THE-FIT.md](RUNNING-THE-FIT.md) |
| **S5** — Guard rails | #44, #48, #49 | The screen interface — a verdict with a reason, never a silent drop — the applicability-domain ceiling, and the ElMD novelty distance | `hydms/screens/` |
| **S6** — Delivery: contract + API | #75–#80, #90 | The request/result/refusal contract, `predict_capacity` over an **immutable artifact bundle**, gate HG-2 (never a bare number), the FastAPI service, HG-3 transport parity, and the published `docs/API.md` | `hydms/delivery/`, [API.md](API.md) |
| **S7** — Delivery: interface | #81, #82, #84 · **#83 open** | Streamlit is an **HTTP client**, so the API stays the single prediction path and HG-3 covers the UI. The chart vocabulary (a chart is a *description* that cannot be built dishonest), the prediction page, and batch CSV screening over `predict_many` (limit 4,096 rows) | `hydms/figures/`, `app/`, `hydms/delivery/` |
| **S8** — Evidence and close | #89, #85, #86, #35, #37, #103 · **#36 open** | The REPORT reconciliation (twelve disagreements), ADR 0006 (the delivery seam), HG-4 and the CI fast lane, the glossary, the Chapter 1 revision, and the committed artifact score | [REPORT-RECONCILIATION.md](REPORT-RECONCILIATION.md), [chapter1-revision.md](chapter1-revision.md), [adr/](adr/) |

**Still owed by S7 and S8.**

- [ ] **#83** model card. Must carry the material-vs-system caveat (PRD §4.4) and the link to
      `docs/REPORT-RECONCILIATION.md`; both are on it. Owed: the per-row width table and the
      one-run-or-spread question, which waits on #104's repeat.
- [ ] **#36** the five ADRs, into `0001`–`0005` (`docs/adr/README.md` records the reservation).
- [ ] **Lift the freeze:** set `freeze: lifted` in [FREEZE.md](FREEZE.md) with the closing date. All
      four conditions hold since 2026-09-24; **the maintainer holds the freeze until S7 is finished.**

**Exit check (S7):** `conda run -n Project streamlit run app/main.py` plus the manual acceptance in §5.

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
| **HG-2** No bare numbers | #77 | A contract type gains a default for `interval` or `domain`; any `return` in `predict_capacity`, `predict_many` or `_answer` stops being a `Refusal` or a `PredictionResult` (or, for the first two, the checked delegation between them), or `predict_many` stores anything else as an answer;
 a probe comes back without a code, a sentence, or the thing its refusal is about — named *outside* the echo of the formula that was typed, since every sentence here quotes its input and `'Xx'` is in `'Xx2'`; a declared code stops being reachable through either door with nothing saying why; or a code with no input at the request door becomes reachable there. Skips, loudly, where no artifact is on disk or where every probe was refused |
| **HG-3** Transport parity | #79 | The API's answer differs from `predict_capacity()`'s for the same input at any JSON pointer; a served body cannot be rebuilt by `answer_from()` into an equal object; a batch reorders its rows, fails whole over a refused row, or does not enforce the limit it publishes; a rejected request carries `refused`, or `answer_from()` reads one as an answer; the committed OpenAPI document is not what the code produces; the request model declares a field `PredictionRequest` does not, or stops forbidding unknown ones; `/v1/health` or `/v1/model` names a version other than the one that answered. Skips, loudly, where no artifact is on disk or the `api` extra is absent — the document and the door are checked first either way |
| **HG-4** Hygiene | #86 | ruff or mypy fail on `hydms/ tests/ scripts/`, or the coverage floor in `[tool.coverage.report]` is not met. Runs the tools rather than reading a log — ruff is 0.045 s and a warm mypy 2.33 s, so re-asking is cheaper than trusting. Skips, loudly, where a tool is absent from `PATH`, where there is no `pyproject.toml` to lint by, or where no `pytest --cov` has been run; and **refuses to report a coverage number from data older than the newest file under `hydms/`**, because `pytest --cov` writes its data only when the run ends, so a gate running inside that suite would otherwise score the previous run |
| AC-1 | #32 | Same seed does not reproduce identical metrics |
| AC-2 | #21 | The featuriser does not match CBFV to 1e-9 on all 1,279 formulae |
| AC-3 | #31 | Conformal coverage does not match its nominal level |
| AC-4 | #33 | Known alloys do not round-trip through `predict()` |
| AC-6 | #30 | Leave-one-alloy-class-out R² is not reported beside the random-split number |

---

## 5. Verification

The measurement history behind each count below is archived in
[archive/PHASE-H-STAGES-CLOSED.md](archive/PHASE-H-STAGES-CLOSED.md); only the latest is kept here.

```bash
# Board and freeze integrity (stdlib only, no environment needed)
python scripts/check_board.py --root .
python scripts/check_freeze.py --base origin/main

# NOT a cheap check: rebuilds a throwaway env from both lock files (~8 GB, 15-20 min). It cannot
# pass on this machine: the `defaults` channel is permanently 403 and supplies python and numpy.
# The three remedies are the open box on card #1 -- do not start a re-solve unasked.
python scripts/verify_environment.py

# Suite. Two commands, two numbers: never compare them, and say which one you quote.
#   FULL:      1650 passed, 0 failed, 1 h 15 min 4 s, 2026-09-25 at f427089, quiet machine.
#   FAST LANE: 1583 passed / 4 deselected with --cov (89.42 %), 53 min 7 s, 2026-09-24, quiet.
#              2026-09-26: 1765 passed, 10 red, all the smoke module meeting #104's refusal;
#              smoke is 19/19 since its fix, and the lane was not rerun whole.
# Say whether the machine was quiet (#100: a concurrent session's edit mid-run produced a green
# that tested nothing). Check before and print Get-Date either side:
#     Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Select ProcessId, CreationDate, CommandLine
# A red run writes reports/test-failures/<start>-pid<N>.txt (tracebacks, other python processes,
# files modified mid-run). Read it before re-running. There is no skip: if
# test_the_committed_document_is_what_the_code_produces skips, the LOCO tables are missing.
# Do NOT pass -q: pyproject sets it, and a second hides `N passed`.
# CI runs only the fast lane (20-minute cap); the four slow tests run here or nowhere until #7.
conda run -n Project python -m pytest
conda run -n Project python -m pytest -m "not slow" --cov   # what CI actually runs
conda run -n Project python -m pytest tests/leaks               # HG-1

# Lint and types run OUTSIDE the environment (docs/QA-PROTOCOL.md §6). A green mypy here is not
# evidence about CI, which has none of the project's packages: after adding an import under
# hydms/, ask a bare interpreter with only mypy (same version as the workflow; test_tooling.py
# asserts they match):
#     python -m venv /tmp/barelint && /tmp/barelint/bin/python -m pip install mypy==1.13.0
#     /tmp/barelint/bin/python -m mypy
ruff check hydms/ tests/ scripts/ && mypy
# `run` with no selection exits 2 -- a selection is a decision, so name one.
conda run -n Project python -m hydms.gates run --all           # 8 passed, 0 failed, 4 skipped (3.0 min)

# Smoke (#73): the chain check, every stage over a committed 235-row fixture in ~12 s. It says
# nothing about accuracy; `--digest` prints what a same-seed rerun must reproduce. The real run is
# docs/RUNNING-THE-FIT.md, which is hours.
conda run -n Project python -m hydms.pipeline.smoke
conda run -n Project python -m hydms.pipeline.smoke --digest

# The published contract: builds the OpenAPI document from the code and diffs the committed
# hydms/delivery/api/openapi.json (exit 1 with the moved pointers). `--emit` rewrites it.
conda run -n Project python -m hydms.delivery.api.openapi

# API. Serves the PROMOTED version (`current` -> v3) and refuses to start without one -- so it
# refuses on a fresh clone, where gitignored artifacts/ is empty (#7).
conda run -n Project uvicorn hydms.delivery.api:app --port 8000
curl -s localhost:8000/v1/model
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"LaNi5","temperature_k":298}'
# expect: estimate + interval + level + domain verdict + elmd + model_version
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"Xx9Zz3","temperature_k":298}'
# expect: a structured refusal with a reason, HTTP 422 — never a number (code `indeterminate`).
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"","temperature_k":298}'
# expect: ALSO 422, but `error: invalid_request` and no `refused` key. The body, not the status,
# separates a declined material from an unreadable request.
curl -s localhost:8000/v1/health   # {"status":"ok","model_version":"v3","max_batch_rows":4096,...}

conda run -n Project streamlit run app/main.py
```

**Manual acceptance for the interface**

- A known training alloy returns the model's prediction for that row (AC-4 at the UI boundary).
- `Mg12Ce1` and `Ce1Mg12` return the **same** answer (L8). The library asserts it on all six known
  collision pairs (`tests/test_metamorphic.py`); this is the UI boundary.
- A plausible-but-far composition visibly widens the interval and flags the domain.
- Nonsense is refused with a reason, not answered.

---

## 6. Assumptions, risks, and what is deliberately out

- **Ids were preserved when cards migrated boards**; the two directories are a freeze boundary, not
  an id-space boundary. **#44, #48, #49 were pulled out of the frozen PA phase** — without them the
  interface has no refusal path.
- **Expect the headline numbers to fall, substantially** (risk R4). Per the PRD that is *a reported
  result, not a failure*.
- **Scope:** ≈ 50 developer-days for one developer. A rebuild, not a patch — the honest cost of the
  chosen scope, in tension with the word *emergency*.
- **Out of scope:** HYDPARK's ΔH/ΔS columns and `database/combined_dataset.csv` (frozen
  thermodynamics, #38–#43). `Machine_Model/**`, `REPORT.md` and the PRD are read, never rewritten.
- **Nothing this phase ships has been seen by CI:** `artifacts/` is gitignored (#7). **Check that a
  file reaches CI before writing a check that reads it.**
- **A gate can be green over a sentinel whose subject moved** — measured once, for 5 h 21 min.
  `docs/QA-PROTOCOL.md` §5 carries the rule.
- **A number only a gate message or an uncommitted file has held is not published.** That gap is
  where `REPORT.md` went wrong; #103 closed the artifact score's instance, and the near-ambient
  bin's near-zero R² is boxed on #83.
