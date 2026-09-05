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
#23's "persist the scaler, never refit" has nowhere to persist to without it.

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
- **Promotion is `current.json`.** Rollback is a pointer write, not a retrain (#7).

---

## 3. Stages

### S0 — Freeze and tooling · #72 · 1 d

**Goal:** the freeze exists and is enforced before any code moves.

- [x] Install the `ml-model-training` skill and review what it installed.
- [x] `git mv` cards 1–37, 44, 48, 49, 68 into `kanban-hardening/`. Ids unchanged.
- [x] Write [FREEZE.md](FREEZE.md) and this runbook.
- [x] Extend [../scripts/check_board.py](../scripts/check_board.py) — two boards, one id space, plus
      the freeze status rule.
- [x] Write [../scripts/check_freeze.py](../scripts/check_freeze.py) — the diff half of the freeze.
- [x] Write [../kanban-hardening/README.md](../kanban-hardening/README.md) — the board charter.
- [x] Create cards #69–#89; amend #12, #13, #14, #24, #26.
- [x] Wire the freeze check into `integrity.yml` — since absorbed, with `check_board.py`, into
      the `hygiene` job of [../.github/workflows/ci.yml](../.github/workflows/ci.yml) by card #6.
- [x] Repoint [../CLAUDE.md](../CLAUDE.md) and mark [../kanban/README.md](../kanban/README.md) frozen.

**Exit check**

```bash
python scripts/check_board.py --root .
python scripts/check_freeze.py --base origin/main
```

> **On the `ml-model-training` skill.** It is generic, MIT-licensed, and correct about scaler leakage.
> It is **silent** on group-aware splitting, nested CV, and early stopping on the scoring set, and its
> worked example is a plain `train_test_split` with no `random_state` and no grouping — which in this
> project would reintroduce L4, L7 and L8. Use it for model-fitting mechanics only. This project's
> authority order puts skills below the [../research/](../research/) memos; on any validation question
> the memos and this runbook win.

---

### S1 — QA foundation · #69, #70, #5, #71 · 2 d

**Goal:** somewhere to put every later test, and the sentinels that make the leaks un-reintroducible.

[../pyproject.toml](../pyproject.toml) declares `pytest`, `ruff` and `mypy` and **configures none of
them** — no `[tool.ruff]`, no `[tool.pytest.ini_options]`, no `[tool.mypy]`, no `conftest.py`, no
`tests/`.

- [x] **#69** Add the three tool config sections. Create `tests/` with `conftest.py` and shared
      fixtures. Set a coverage floor on `hydms/`.
- [x] **#69** Exclude the legacy tests with `testpaths = ["tests"]` + `norecursedirs` — **not** by
      touching `Machine_Model/`, which is deny-listed and archival. This is load-bearing:
      `Machine_Model/tests/test_catboost_smogn.py` is a 250-line training script that calls
      `optuna.create_study(...).optimize(n_trials=50)` at import time, so pytest would **run an Optuna
      study during collection**; and `test_check_database.py` asserts against a gitignored `hydride.db`
      that is absent from a clean clone.
- [x] **#69** Add an `api` extra. **Reuse the pins already in `requirements-lock.txt`** —
      `fastapi==0.115.0` and `uvicorn==0.30.6` are present as pollution from a removed service.
      **Do not regenerate the lock file:** [ENVIRONMENT.md](ENVIRONMENT.md) records a hand-applied
      `python-graphviz` → `graphviz` fix that regeneration silently undoes, killing the install at the
      end of the pip stage.
- [x] **#70** Write `docs/QA-PROTOCOL.md`.
- [x] **#5** The gate harness. Twelve criteria registered — the PRD's eight plus the four below —
      one module each under `hydms/gates/`, all reporting `SKIPPED` until the card that owns each
      one lands. It slots in here rather than in a stage of its own because #71 and every AC gate
      is blocked behind it.
- [x] **#71 (HG-1)** `hydms/qa/` and `tests/leaks/` — one sentinel per leak, each passing **only
      because the leak is absent**. Ten of the thirteen were written in S1; three were recorded
      deferrals, closed one at a time by the cards that could decide them. **#29 closed the last,
      L11, on 2026-09-05, and `DEFERRED` is now empty — thirteen of thirteen.** The empty tuple is
      kept rather than deleted: a gap nobody wrote down is indistinguishable from coverage, and the
      next leak this project finds should be recorded there on the day it is found.

| Leak | Sentinel | Detector |
|---|---|---|
| L1, L5 | The `eval_set` identity is the **validation** split; `use_best_model=True` with an empty or test eval set raises | `assert_early_stopping_is_honest` |
| L2, L4 | The model-selection record contains no held-out metric; the reported score comes from folds disjoint from the tuning folds | `assert_selection_is_nested` |
| L3, L10 | `y` **and** `X` for val and test are byte-identical before and after any screening stage | `assert_holdout_unchanged` |
| L6 | Re-running selection with held-out rows perturbed produces an identical feature set, order included | `assert_selection_ignores_holdout` |
| L7, L8 | No **canonical** composition appears in two splits, and none in two CV folds | `assert_disjoint_groups` |
| L9 | Reordering an input never changes the merged result silently, and a row the merge cannot key raises | `assert_merge_is_keyed` |
| L13 | `Alloy_class` survives featurisation: the column, every row, every label unchanged | `assert_metadata_survives` |
| L12 | Perturbing the target does not change any sample weight, twice over: shuffled-and-rescaled, then replaced by a ramp | `assert_weights_ignore_target` |
| L11 | The explainability record **names the rows it ran on**, and that name is not a held-out split. A record that names *nothing* is the same defect: it is the archival state, in which the figure existed and the population did not | `assert_explanation_is_not_held_out` |

Three things about the design are load-bearing; the reasoning is in #71's `## Narrative`:

- **The detectors live in `hydms/qa/`, not in `tests/`.** They are the guard the pipeline itself is
  meant to carry, so #10, #13, #14, #24, #26 and #88 each call the same function and the sentinel
  then tests the real guard rather than a parallel copy of it. Every detector takes row labels, a
  record of what a fit saw, or a callable — never a fitted model — which is what let all ten be
  written and proved before any of the code they guard exists.
- **The red demonstration is executable, not a ritual.** Each sentinel carries `Reproduction` pairs,
  a leaky case that must raise and a corrected twin that must not, and HG-1 runs every one of them.
  Weaken a detector and the gate names the leak.
- **A sentinel whose subject module appears without a `live` hook makes HG-1 red.** That is how a
  sentinel written against a miniature in S1 becomes a guard in S2–S4 without anyone remembering to
  wire it. Each owning card carries the box.

**Exit check:** `conda run -n Project python -m pytest tests/leaks -q` · `ruff check hydms/ tests/
scripts/` · `mypy` · `conda run -n Project python -m hydms.gates run HG-1` — the last **exits 1
until stage S4 closes**, reporting `N/13 leaks guarded in the pipeline` where N is however many
subjects have been built and wired so far (#10 made it 1; ask the gate rather than this line). Ten
reproductions going red proves the detectors work; it says nothing about a pipeline that does not
exist yet, and the gate refuses to let those two claims be confused.

---

### S2 — Data layer · #3, #9, #10, #11, #87, #12, #13, #14, #15 · 7 d

**Goal:** the merge is keyed, the split key is chemical, and CleanLab cannot touch held-out labels.
**Closes:** L3, L8, L9, L13 — and **L10 by watchfulness only.** No stage closes L10: it is absent
because `Ashghal/Outliers_Management.py` is not being ported, which is an accident rather than a
fix. The day #14 grows outlier handling is the day it can come back, so the L10 sentinel guards
the same module as L3 (card #71).

```
#3 config → #9 loaders → #10 keyed merge (L9) → #11 target transform
→ #87 canonical composition key (L8, L13) → #12 alloy class → #13 splits (L8)
→ #14 CleanLab, train-only (L3) → #15 golden tests
```

- [x] **#3** Config loader — relative paths, seeds, thresholds. No absolute path literal anywhere.
- [x] **#9** Raw loaders with schema validation. **The `len(skipped) == 0` assertion this line
      originally asked for is vacuous** — measured against the installed CBFV, `skipped` is empty on
      all 1279 rows. The defect is upstream of it: `CBFV.composition.parse_formula` validates
      nothing, returning `{'Xx': 2.0}` for a non-element, `{}` for `Mg0` and `{'Mg': -1.0}` for
      `Mg-1`. An unknown element is then dropped into the unread `skipped` list; an empty
      composition kills `generate_features` with `zero-size array to reduction operation maximum`.
      So the loader parses and rejects at the door, at parity with CBFV on all 1279 + 772 formulae.
- [x] **#10** Replace the positional `concat` with a keyed merge; assert the join covers every row.
      **The key this line implies is not a row identity.** The card said "formula, and temperature
      where the row is a measurement"; measured, 1279 rows carry only **1272** distinct
      `(Composition, temperature(K))` pairs, six of the seven repeats being independent replicates
      from different citations. So the spine's *index label* is the row identity, feature blocks are
      per-composition (1149 rows) and looked up from it, and a repeated block key is refused — that
      key, used row-wise, would have inflated the table to **1293** rows in silence. `merge_features`
      also refuses a column name arriving twice, which is `merge_datasets.py:49`, one line below the
      leak and the same defect in a different disguise.
- [x] **#11** Target transform. `to_model_space` / `to_wt_pct`, and the docstring that says which
      published metric is in which space. **The transform is `log1p` — measured, and the three
      candidates that were ruled out are wrong by more than 2.0 — but "equals `numpy.log1p`
      elementwise" holds only to one ulp.** `hydride_prefeaturizing.csv`'s column agrees to
      4.44e-16 and is bit-identical on 1005 of 1279 rows, because `log_transform_target.py:59`
      wrote it with `to_csv` and it came back through decimal text. Two more one-ulp effects
      compound (`math.log1p` vs `numpy.log1p`; the round trip itself), so the tolerance is 1e-12
      and **nothing in this project compares two target vectors with `==`**. That is also a third
      independent reason the column is a fixture rather than a source.
- [x] **#87** `hydms/data/canonical.py` — normalise element fractions to a stable key; use it as the
      split key **and** the CV group key; re-join `Alloy_class` on it; reconcile the compositions
      carrying conflicting class labels. **There are ten of those, not five.** Five is the count on
      the raw formula *string*; canonicalisation adds five more by merging spellings the file
      labelled independently (`Ce1Mg12` is `MIC`, `Mg12Ce1` is `Mg`). The rule is
      `ALLOY_CLASS_PRECEDENCE` — most specific structural claim first, not a majority vote, which
      counts citations rather than chemistry. The key rounds atomic fractions to **four significant
      digits**, which is the only resolution that both reproduces 1115 compositions and keeps the
      widest gap it merges (3.46e-05) narrower than the closest it does not (1.01e-04); `separation()`
      asserts that over both raw files and is demonstrated red at three digits.
- [x] **#12** Re-join `Alloy_class` on the canonical key, not the raw string. **Closed 2026-09-04,
      in two halves seven stages apart.** `hydms/data/metadata.py` declares the boundary in
      two lists — `metadata_columns()` (what a featuriser must carry: formula, class, dataset,
      citation, canonical key) and `non_feature_columns()` (that, **plus the target in both
      spaces**), with `refuse_non_features(X)` checking the matrix rather than the featuriser. All
      ten classes survive, 1279 rows in and out, 13 relabelled; AC-6 is feasible, the smallest
      class being `A2B` at 24 compositions of 1115. `UNKNOWN` is settled as a **refusal** — the
      class is complete on all 1279 rows and an eleventh label changes AC-6's fold count. The three
      boxes that named `hydms.descriptors.featurize` closed the day #20 created it:
      **`with_features`** is the join — `refuse_non_features` on the way in,
      `assert_metadata_survives` on the way out, by label and never by position — and the L13
      `live` hook runs it over **1,278 of the 1,279** curated rows, taking HG-1 to **5/13**. Writing
      it found a third disguise of `merge_datasets.py:49`: `temperature(K)` is a column of the raw
      file *and* one of the 22 features, so the prescribed `concat` returns that name twice, `int64`
      beside `float64`. The matrix's copy wins — it carries #19's cast — but only after the
      two are checked to agree, which is the only tie in the frame between a record and a matrix
      claiming to describe it.
- [x] **#13** The assertion becomes "no **canonical composition** spans two splits" — the current
      raw-string assertion passes while 35 rows leak. Landed: `hydms/data/splits.py` ports the
      protocol unchanged and changes only the unit. **893 / 131 / 255 rows over 780 / 111 / 224
      compositions**, against the published 896/136/247 — it cannot match, because the split now
      has 1115 units instead of 1149, and matching would have meant the key changed nothing.
      Fractions hold at 0.698 / 0.102 / 0.199. The **L8 sentinel is wired** and `audit()` reports
      it green. Two things worth knowing before touching it: the per-group mean is taken in
      **model space**, because a mean does not commute with `log1p` and the archival code
      averaged the log column; and the rare-stratum merge measures its distances against the
      counts as they were *before* any merging, so two rare strata never absorb each other.
- [x] **#14** CleanLab may **drop or reweight training rows only**. Val and test targets are
      immutable. **Closed 2026-09-05 by #24, which supplied the feature matrix.**
      `hydms/data/screening.py` drops training rows and refuses everything else: no label rewritten
      on *any* split (`CleanLab.py` rewrites training labels too, at `:64,80`), no held-out row
      touched, and `assert_holdout_unchanged` called three times from inside `screen` before it
      returns. **Reweighting is declined** — the only weighting the archival pipeline had is
      target-conditioned (L12) and choosing a policy is #26's. Two rows are dropped from training,
      both decided here: the byte-identical duplicate (found with `duplicated`, not by row number)
      and `Mg0853Ni0.125La0.022`, whose correction is unambiguous but must be applied upstream of
      the canonical key — boxed on #9. **L3 and L10 are wired and green.** The CleanLab call itself
      is `hydms.data.screening.label_issues` — added by #24, which supplies the matrix, but living
      here because *which rows are label-suspect* is this card's to own. It returns two of
      CleanLab's four columns: `predicted_label` is `CleanLab.py:90`'s leak in raw form and there is
      now no object a caller could reach one through. It runs **inside the folds**, called by the
      selector on the rows that selector owns; the per-split counts #15 and #37 read come from a
      separate pipeline-level `screen` over the whole frame. **#15 must re-measure `rows_out` and
      `removed` against that call.**
- [~] **#15** Data-layer golden tests. **Written and green; the card stays `backlog`, and
      `check_board.py` is what insisted.** `tests/data/test_golden.py` pins 34 facts as one record
      and reports a deviation as a table of fact/expected/actual rather than as a bare assertion.
      It separates *facts that must not move* (1279 rows, 1149 strings, 1115 compositions, the ten
      classes) from *facts that moved on purpose* — the split is pinned at 893/131/255 **with** the
      published 896/136/247 beside it under `split_rows.published_*`, so restoring the old number
      is a visible failure rather than a silent return to the leaky split. The card cannot leave
      backlog while #14 is unfinished, and that is right on the substance: when #24 lands,
      CleanLab starts flagging rows and `screened.rows_out` / `screened.removed` move. Re-measure
      those two then; nothing else should move, and if it does, that is the finding.

**Exit check:** `conda run -n Project python -m pytest tests/data -q` · the L3, **L8, L9** and L10
sentinels go green — L10 because its subject is #14's module. **As of 2026-09-04 five are
green** (`5/13 leaks guarded`), and `tests/data` is 226 tests over eight files. **L13 is the fifth,
and the original version of this line was wrong about it.** Its site is `extract_features_cbfv.py`,
so its sentinel guards the *featuriser*; #87 wrote the sentinel and #12 wires it, but the module it
names does not exist until S3. Pointing it at the data layer instead would have made it green in S2
while guarding a different property — that the class exists — and left the drop itself
unguarded. L13 therefore read `pending` through S2, read `unwired` — red — from the moment
#20 created `hydms/descriptors/featurize.py` on 2026-09-04, and went green the same day when #12
gave it a `live` hook over the real featuriser. Three states, no re-aiming, nobody remembering: that
is the design working. Read the per-leak table with:

```bash
conda run -n Project python -c "from hydms.qa import audit; [print(f'{r.leak:4} {r.status:9} #{r.owed_by}  {r.title}') for r in audit()]"
```

---

### S3 — Descriptor layer · #16–#22 · 6 d *(parallel with S2)*

**Goal:** ~~a two-table featuriser that matches CBFV exactly~~ → **a two-table featuriser that
matches CBFV exactly given CBFV's table.** #16 measured that the citable Oliynyk source and
CBFV's copy of it are not the same numbers, so "matches CBFV" had to be restated before AC-2
could mean anything. See below.

- [x] **#16** Element property tables with cited provenance — **two tables**: 15 `oliynyk` + 6 `jarvis`.
      A single-table reimplementation cannot pass AC-2 regardless of correctness.
      **Landed 2026-09-03, and it moved three things downstream:**
      **(a)** The JARVIS half is NIST's `Elements.json` itself — CBFV's `jarvis.csv` *is* that file,
      agreeing to 7.3e-12 — so it is public-domain and needs no reimplementation of the numbers.
      **(b)** The Oliynyk half was **revised** for its 2024 publication: 5 of the 13 needed
      properties agree with CBFV exactly, 8 do not, by up to 10 (`valence_d`, Ga/Ge). AC-2 is
      therefore a claim about the *code*, with CBFV's table supplied as test input from
      `tests/descriptors/data/cbfv_oliynyk_reference.csv`. #21 carries it.
      **(c)** Neither source covers all 55 elements: `gordy_en` is blank for 21 (the rare earths),
      and europium's JARVIS properties are `-9999` sentinels. Two of the 22 features are therefore
      not computable everywhere — #19 and #24/#25 carry it.
- [x] **#17** Weighted composition statistics — `hydms/descriptors/stats.py`.
      **Landed 2026-09-03. `dev` was confirmed; the finding was somewhere else.**
      **(a)** `dev` *is* the fraction-weighted mean absolute deviation about the
      fraction-weighted mean, exact to **0.0** against CBFV over both tables and every cell.
      The rival readings differ by 328.8 (fraction-weighted sd), 1172.2 (unweighted sd) and
      1094.9 (unweighted MAD) — leading figures, not trailing ones. Committed as a fixture,
      `tests/descriptors/data/cbfv_statistics_reference.csv`, so it stays checked without CBFV.
      **(b)** **The reduction must run down the leading axis.** The caller-natural
      `(n_compositions, arity)` batch reduced over its fast axis makes numpy sum *pairwise*,
      which reorders the additions and differs from CBFV by up to **2.794e-09 on jarvis —
      above AC-2's tolerance**. Transposed to `(arity, n_compositions)` and reduced over axis 0
      it is bit-identical. `statistics()` transposes internally; two tests state the property as
      arithmetic (padding a batch changes nothing *exactly*) so a rewrite cannot lose it.
      **(c)** Permutation and scale invariance, which §L2 of the QA protocol asks for, are
      **not exact** — here or in CBFV, which moves by 1.364e-12 when a formula string is merely
      reversed. Both are tested as `atol=rtol=1e-12`; the measured requirement is 4.3e-16 and
      5.3e-15. **(d)** `parse_formula` sorts elements by symbol and CBFV does not, which alone
      moves a cell by up to 3.638e-12 — three orders inside 1e-9, but it is why #21 can never
      be an equality. #21 carries (b) and (d).
- [x] **#18** Composite descriptors (`_divi_`, `_mult_`) — `hydms/descriptors/composites.py`.
      ~~**The live technical risk (R3):** whether the JARVIS composites are statistic-of-composite or
      composite-of-statistic is unresolved and must be settled numerically. Budget slack here.~~
      **R3 was already settled by #16, and not numerically** — the five composites are per-element
      **columns** of the JARVIS table, so a composite is a property of an element and the statistic
      is taken over it. **Landed 2026-09-04. The card's own work was a parse, a pin and an audit,
      and the audit found something.**
      **(a)** **Eleven of JARVIS's 156 composite columns are not the arithmetic their names claim.**
      All eleven are the `*_mult_voro_coord` family and all fail on exactly **Cs and Gd**, where
      each is `0.0` — formed as though `voro_coord` were 0 — while the `voro_coord` column stores
      `1.0` and `voro_coord_divi_mol_vol` uses that 1.0. The published file contradicts itself
      about two elements. The other 145 equal their parts **bit-exactly**, and so do all five of
      the selected composites on all 82 elements carrying them. Hence the rule the featuriser
      inherits: **read the published column, never a derived value** — it is what CBFV reads, so
      it is what parity means. `require_self_consistent()` is the guard; boxed on #20 and #25.
      **(b)** **`voro_coord = 1.0` for Cs and Gd is a placeholder and it reaches a selected
      feature.** Every other element sits between 3 and 12, gadolinium is hcp with twelve nearest
      neighbours, and Gd is in **18 of the 1,279** rows through `dev_voro_coord_divi_mol_vol`. Not
      a bug and not a parity problem — a limit the model card must state. Boxed on #83 and #25.
      **(c)** The rejected order is kept as a **negative test** rather than deleted: over the
      sixteen fixture formulae, composite-of-statistic misses CBFV by between **1.8%** and a factor
      of **65**, while statistic-of-composite agrees to **9.1e-13**. No flag was ever written; two
      code paths would have left less behind than one measurement and one failing assertion.
      **(d)** The naming grammar is a **parse, not a guess**, and that is measured: 156 of 438
      JARVIS columns carry an infix, `oliynyk` carries none, none carries two, every one splits
      into two real columns, and none splits two ways. A feature name arriving with its statistic
      still attached is refused rather than split into `avg_polzbl` and `atom_mass`.
- [x] **#19** The 22-feature contract — `hydms/descriptors/contract.py`.
      **Landed 2026-09-04, and it corrected three of its own instructions.**
      **(a)** "Two of the 22 are not computable everywhere" is **seven**: the card folded the six
      JARVIS features into one because they all fail on the same element. `dev_Gordy_electonegativity`
      is uncomputable on **266 of 1,279 rows / 236 of 1,115 compositions**; each JARVIS feature on the
      single europium row `Eu1Ni5`. `CONTRACT.computability()` answers per composition, naming the
      blocking element and distinguishing an absent element from an empty published cell.
      **(b)** **The Gordy hole is the citable edition's, not CBFV's** — CBFV's copy supplies
      `gordy_en` for all 21 elements Lee et al. 2024 leave blank. AC-2 runs against that table, so it
      will be green while the shipped featuriser cannot build the column for 266 rows. Second defect
      AC-2 structurally cannot see; boxed on #21, with the trade boxed on #24/#25.
      **(c)** The card guessed the loss falls on "AB5 and AB2". Measured, AB2 is the second *least*
      affected class (34/371, 9.2%); the pair is **AB5 (91/196) and MIC (54/127)**.
      **(d)** The training column order was never persisted — `Machine_Model/data/processed_data/`
      is not in the repository and all three committed listings of the 22 are sorted by three
      different keys — so the contract *declares* REPORT.md §3.2's SHAP order rather than recovering
      one, and `from_names()` regenerates the whole contract for #25. Every column is `float64`;
      `temperature(K)` is `int64` in the raw file and #20 owes the cast.
- [x] **#20** `featurize()` — the layer's public interface. `hydms/descriptors/featurize.py`.
      **Landed 2026-09-04, and it moved a module that was already done.**
      **(a)** **A batch of one was not the same arithmetic as a batch of many, from arity 8 up.**
      #17 established that the reduction must run down the leading axis because numpy sums the
      *fast* axis pairwise — but a batch of one, transposed, leaves the leading axis contiguous
      too, and numpy's contiguous sum switches to an eight-accumulator unrolled loop at exactly
      eight elements. Measured over 200 random compositions per arity: bit-identical to arity 7,
      and from **arity 8** a lone composition disagrees with itself inside a batch by up to
      **5.5e-12** on `avg` and `dev`. Three orders inside AC-2's tolerance, so no gate would ever
      have failed — it would have made a single-formula prediction (#82) and AC-4's round-trip
      (#33) disagree with the training matrix for the **eleven** curated rows of eight elements or
      more. Fixed in `stats.statistics` (a lone composition is duplicated, reduced as a pair and
      the copy discarded); #17's own test used arity 5 and is widened to 10.
      **(b)** **The refusal, counted in rows, is the number #24/#25 need.** The published 22
      cannot featurise **266 of the 1,279** curated rows — 265 for Gordy alone, `Eu1Ni5` for seven
      features at once — so the full contract cannot build the training matrix at all. Without
      `dev_Gordy_electonegativity` the remaining 21 cover **1,278 of 1,279**. One feature is the
      difference between 1,278 rows and 1,013.
      **(c)** **#21's requirement turned out to be a requirement on this interface.** "Parity given
      the same table" cannot be arranged from outside a function that resolves its own tables, so
      `featurize(..., tables=)` is a parameter — which forced `FeatureContract.computability(...,
      tables=)` too, because asking the *shipped* table whether a row is featurisable while reading
      CBFV's would refuse the 266 rows the gate exists to compare. `PropertyTable.of()` builds one.
      **(d)** **The value pin found nothing wrong.** All 22 columns against CBFV's own output over
      the sixteen fixture formulae, with CBFV's table supplied: worst **4.547e-13** absolute,
      **6.828e-15** relative. Assembly correct first time; the residue is #17's element order.
      **(e)** **HG-1 was red on purpose, for one day.** `L13 [unwired] #12`. Eight tests failed
      with it, including one whose docstring predicted its own death. The sentinel was not
      re-aimed: #12 closed the same day with the `live` hook and the `with_features` join, and
      HG-1 reads **5/13**, skipped rather than red.
- [x] **#21 GATE AC-2** — parity with CBFV to 1e-9 on all 1,279 formulae. **Hard gate.** If it fails,
      the reimplementation is wrong, not CBFV. **Two amendments from #16:** parity is measured against
      the reference table, not the shipped one; and no Eu-containing formula can be compared at all,
      because this layer refuses where CBFV returns a silently-zeroed number.
      **Green 2026-09-04, at 2.7285e-12 against 1e-9** — `dev_atom_mass_mult_therm_cond` at
      `Mg0.7Li0.2Cu0.1`, over **1,278 of the 1,279** rows, seven columns bit-identical, 1.5 s.
      **(a)** The exclusion is **derived from both sides**, not hard-coded: a row is dropped when
      this layer refuses it *or* when CBFV lists it in the `skipped` array `extract_features_cbfv.py`
      never read, and the result reports the two counts separately so their disagreeing would be
      visible. They coincide on one row. Measured here: **CBFV's `jarvis.csv` has no europium row at
      all** (82 elements, not 85) and emits a full row for `Eu1Ni5` regardless — `avg_atom_mass`
      48.911 is `(0×1 + 58.6934×5)/6`, so the all-zero vector is now arithmetic rather than
      inference. **(b)** The gate reads CBFV's *installed* Oliynyk table rather than the committed
      fixture. The two are bit-identical (measured, zero differing cells) but the gate imports CBFV
      anyway for the expected numbers, and a second source admits a skew it would report as a parity
      failure; a new test pins the fixture against the installed table so it cannot go stale.
      **(c)** Supplying CBFV's JARVIS copy as well changes the worst gap by **nothing** — same
      2.7285e-12, same cell — so the residue is #17's element order and not the 7.3e-12 between the
      two copies of NIST's file. **(d)** `_report.py` printed multi-line detail only for red rows, so
      the two lines this gate is *required* to print reached only the JSON. Any status now prints it;
      HG-1's per-leak listing was hidden by the same bug. **(e)** Six harness tests used the string
      `AC-2` to mean "a criterion nobody has written yet" and now take an `unwritten` fixture that
      asks the registry.
- [x] **#22** Featurisation throughput benchmark. **Landed 2026-09-04, and it found a 13x defect in
      the layer it measures.** `hydms/descriptors/benchmark.py`, [BENCHMARKS.md](BENCHMARKS.md).
      **(a)** The figure this project had quoted since #20 — *10,000 formulae in 0.31 s* — was
      measured over **four distinct formulae repeated 2,500 times**. The computability memo is keyed
      by element set, so that batch answered it four times instead of ten thousand. Ten thousand
      *distinct* candidates took **3.34 s**: 2,996/s, three times the card's feasibility floor rather
      than forty. **(b)** `cProfile` put **97%** of the wall clock in
      `FeatureContract.computability` → `PropertyTable.has`, **13.8 million calls for nineteen
      answers**: the servable-element set was cached only for the *shipped* tables, keyed by table
      name, and `featurize` always hands `computability` a resolved `tables=` mapping, so the cached
      branch was unreachable from the featuriser. Fixed by moving the memo onto the table
      (`PropertyTable.servable`); 10k distinct now takes **0.245 s** (13.6x), 100k **2.23 s**, the
      curated rows **0.022 s**, the whole suite 24.9 s → 17.9 s, AC-2 1.54 s → 1.28 s. No expected
      value moved. **(c)** The parser is **22%** of the remainder, which is why the card asked for the
      split — right about the principle, wrong about the culprit. **(d)** R6: a 1e6-point grid
      featurises in ~24 s and NSGA-II's whole 100k budget in 2.2 s, so **featurisation does not decide
      between Architectures A and B**; what does is the surrogate, and it is unmeasured. **(e)** The
      "file a note against #59" condition became a **test** — #59 is frozen and `check_freeze.py`
      denies edits under `kanban/` — failing the build below 1,000/s at batch 10,000.

**Exit check:** `conda run -n Project python -m hydms.gates run AC-2` — **green**, and it needs the `parity` extra: without CBFV it skips rather than passing, which is what CI does.
**S3 closed 2026-09-04**, seven cards: the layer's throughput is measured and its one hot spot is gone.

---

### S4 — Surrogate layer · #23–#34, #88 · 13 d

**Goal:** an honestly-validated, calibrated model with artifacts on disk.
**Closes:** L1, L2, L4, L5, L6, L7, L11, L12.

```
#23 scaler fit-once → #24 selection inside folds (L6) → #25 old-22 vs new-N
→ #88 group-aware nested CV (L4, L7) → #26 CatBoost, honest early stopping (L1, L5)
→ #27 MAPIE conformal → #28 predict() → #29 metrics + bootstrap CI → #30 LOACO CV
→ #31 AC-3 · #32 AC-1 · #33 AC-4 → #34 artifacts/v1
```

- [x] **#23** Scaler: fit once on train, persist, never refit. **Landed 2026-09-04.**
      `hydms.surrogate.fit_scaler(features, split)` is handed the whole matrix with #13's split
      assignment and selects the training rows itself; it refuses a split that holds nothing out.
      What it returns and what the artifact stores is a `FittedScaler` — the names, the medians
      and the IQRs, **not** the estimator — so there is no `fit` to reach and a scikit-learn
      upgrade cannot change what a saved `v1` does. `(x - centre) / scale` is bit-identical to
      `RobustScaler.transform` over all 1,278 x 21 values, measured. `transform` takes a
      `DataFrame`, requires exactly the fitted column set and returns it **in fitting order**:
      scikit-learn accepts a bare `ndarray` with only a `UserWarning`, which is where a permuted
      matrix becomes plausible, wrong numbers. Read it back with `scaler_from(bundle)`.
- [x] **#24** Port selection reading **CleanLab output**, run **inside the training folds** (L6).
      **Landed 2026-09-05**, closing #14 in the same commit. `hydms/surrogate/selection.py` ports the
      *live* selector — `Boruta_FeatEng.py`'s three stages, not REPORT §3.3's five, which exist in
      neither file — with every threshold from `pipeline.yaml`. `select_features(frame, train)`
      slices to `train` in its first statement and never reads the frame again, which is the whole
      of the L6 fix; `select_across_folds(frame, split)` takes the whole matrix with #13's
      assignment and runs one selection per outer fold of #88's `grouped_folds`. It returns
      `consensus()`, `union()` and `stability()` rather than "the selected features": selection
      inside the folds has one answer per fold and collapsing them is #25's decision. HG-1: **9/13**.
      Three measurements the card asked for, and two of them contradicted its own boxes:
      **(a)** `avg_is_alkaline` is *not* dropped by the variance filter — a zero IQR is not
      constancy, the column has 75 distinct values over the 893 training rows and variance 0.0707,
      and Boruta confirms it. On the real matrix the variance filter drops **nothing at all**.
      **(b)** The `dev_Gordy_electonegativity` trade is settled: **drop the feature, keep the rows.**
      Carrying it costs 193 of 893 training rows, concentrated in AB5 (46.9 %) and MIC (42.5 %) —
      the classes AC-6 scores. Over the 700 rows where the comparison is controlled it *is*
      confirmed, but twelve of the thirteen confirmed features are the same either way; its absence
      is taken up by `dev_gilmor_number_of_valence_electron` and `temperature(K)`. It displaces
      rather than adds.
      **(c)** **A pass costs 676 s of Boruta** plus 14 s of CleanLab on the real matrix, so a
      five-fold run is an hour and `python -m hydms.surrogate.select` is a **slow-lane** command.
      The L6 live hook therefore runs the real selector under `SENTINEL_BUDGET` — ten iterations,
      fifty trees, screening off, every other threshold configured — and a `slow`-marked test checks
      that claim at the real budget rather than asserting it.
      **The first real five-fold run has been done** (~50 min, tables in the gitignored
      `reports/selection/`, publishing them is #25's job) and it produced the finding the whole card
      exists to expose: **every one of the 21 candidates is selected by some fold, and only 14 by
      all five** — `range_Atomic_Weight` by exactly one. "The 22 features" was never a stable
      object. Two numbers boxed onward: per-fold selection is *larger* than the whole-split run
      (16–20 against 14), because fewer rows make Boruta less able to reject — so the new N and the
      old 22 were not produced under the same statistical power (#25 — **and that reading was
      confounded**: the 14 came from the *unscreened* probe, and #25's screened whole-split pass
      selects 18, inside the folds' own range); and CleanLab removes between **15 and 144** of a
      fold's ~710 training rows depending on the fold, a 23 % swing in training size before the
      model sees anything (#26).
- [x] **#25** Run selection once; publish the old-22 vs new-N comparison. **Landed 2026-09-05.**
      The declared set is `hydms.descriptors.contract.SELECTED`, the **consensus 14** — the features
      all five outer folds chose — regenerated by `FeatureContract.from_names`. `CONTRACT` is
      untouched and stays the published 22: the archival record, the candidate pool, and what AC-2
      checks parity across. Two contracts, not two versions of one.
      **(a)** **The readings nest: consensus 14 ⊂ 22-candidate 16 ⊂ whole-split 18 ⊂ pool 21.** The
      union is the whole pool, so the permissive reading performs no selection at all; a threshold
      would be a cut chosen after seeing where the features fell. The serious alternative was the
      *refit* reading — nested CV estimates the procedure, the deployed model refits the procedure
      on all training rows, which would publish the 18 — rejected because Chapter 3 reports the
      feature set **as a finding**, and a set from one fit carries no evidence about its own
      stability. All of it is argued in `reports/feature_selection/old_vs_new.md`.
      **(b)** **#24's statistical-power reading was confounded, and the run this card owed fixed
      it.** Screened, the whole-split pass selects **18**, not the unscreened probe's 14 — inside
      the folds' 16–20. Row count and screening move together in all three runs, so the direction
      can be stated and the size cannot; and *within* the folds the row count does not order the
      answers at all (571 → 16, 704 → 18, 635 → 20), which is the real argument for the consensus.
      **(c)** **The 22-candidate run does not select the feature that defines the 22.** Same
      700-row pool, same seed, same budget as #24's controlled comparison, which confirmed
      `dev_Gordy_electonegativity`; the 71 rows screening drops reverse the verdict. The trade was
      settled on rows rather than importance, and this is why it had to be.
      **(d)** **The write-up is generated and checked.** `--emit-comparison` fits nothing — it
      rebuilds the document from the tables the slow runs left, in a second — and a test asserts
      the committed document is exactly what the committed tables produce. `reports/feature_selection/`
      is un-ignored so the evidence is versioned with the contract it justifies. Findings boxed
      onward: #26 (fit on `SELECTED`; per-fold selection inside the tuning loop is unaffordable at
      676 s a pass), #29 (say which feature set a number belongs to), #83 (the `voro_coord = 1.0`
      placeholder reaches 18 rows through a declared feature, and the set is not a stable object).
- [x] **#88** `hydms/surrogate/validation.py` — `StratifiedGroupKFold` on the canonical key (L7),
      **nested** so the reported score comes from an outer fold the tuner never saw (L4).
      **Landed 2026-09-04**, out of the order the arrows above draw: its `blocked_by` is #13 and
      #23 alone, and #24 waits on *it*. `nested_scores(features, split, contenders)` takes the
      whole matrix with #13's assignment and selects the training rows itself, refusing a split
      that holds nothing out — cross-validation never sees `val` or `test`, and a record carrying a
      metric under either name is refused for it. `grouped_folds` is the **only** fold generator in
      the project (a test asserts no other module imports a `KFold`), groups on
      `hydms.data.canonical.group_keys` and stratifies with #13's `stratify`, recomputed per fold
      set from the rows that set may see. **`leave_one_class_out` is #30's AC-6 protocol as an
      `outer=` argument**, not a second scoring path. Fold ids are issued for *content* — the set
      of compositions held out — so `tuned_on ∩ scored_on` is a real question rather than an empty
      one, and `tuned_on` is the folds the search actually read. HG-1: **8/13**.
- [x] **#26** CatBoost MultiQuantile with `use_best_model=True` and the **validation** split as
      `eval_set`. **Landed 2026-09-05.** `hydms/surrogate/model.py` is the model,
      `python -m hydms.surrogate.train` runs it through #88's protocol, and HG-1 was **12/13** at
      the time — L11 was the last leak, and #29 closed it on 2026-09-05.
      **The search space this card ported has since been narrowed, once, by measurement.** #26
      recorded that the `learning_rate` 1e-4 x `iterations` 30,000 corner cost 397 s against 7 s and
      scored worse, and left it ported because narrowing is a modelling decision. #29 measured the
      whole decade on one real inner fold: the best iteration goes as roughly `4.2 / learning_rate`
      — 813 at 0.005, 4,230 at 0.001, 8,501 at 0.0005, 13,991 at 0.0003 and **29,999 at 0.0001,
      which is the cap itself**, so the fit at the archival lower bound never converged. R² across
      that decade is 0.6800 to 0.6847: flat. Since `iterations` is sampled from 10,000, the bound is
      **5e-4** — the measured rate whose optimum still falls inside the smallest budget the space can
      hand a trial. Nineteen times the wall time for the same model, removed before the run this
      thesis quotes rather than after it.
      `fit_quantile_model(frame, train=, eval_on=, scored_on=, where=)` **cannot be called without
      naming the rows the result will be claimed about**, and its first statement hands those
      identities to `assert_early_stopping_is_honest`; there is no path through the module that
      fits without it, which is what lets the L1 and L5 sentinels point at the real function.
      `tests/surrogate/test_no_test_leak.py` asserts the blindness by **value** as well — the
      scored rows are `NaN` and the fit is expected to succeed — and that test found a real read
      on the way past, a target transformed over the whole frame, now scoped to the rows a fit
      owns. Fits inside the training split stop on one fold of the new `model.stopping_folds`,
      cut by `grouped_folds` so no composition spans the two sides; the final fit stops on `val`.
      Four measurements, three of which corrected something:
      **(a)** `early_stopping_rounds: 5000` was **paying four times over for an identical model** —
      26.9 s at 5000, 6.9 s at 500, 5.4 s at 200, and best iteration 1042 with R² 0.7050 in all
      three. `od_wait` only multiplies the trees grown after the optimum, which `use_best_model`
      discards. Now 500.
      **(b)** **The budget: 4,500 fits is 42 hours.** A real end-to-end probe ran 35 fits in
      **19.4 min** — 33 s a fit — so `optuna_trials` came down from 300 to **25**, projecting
      ~3.5 h. The nesting was untouched. The hours live in one corner of the ported space:
      `learning_rate` 1e-4 with `iterations` 30,000 costs **397 s** against 7 s at the fast corner,
      has not converged at iteration 29,999, and scores **worse** (R² 0.691 vs 0.705). The space is
      still ported verbatim; narrowing it is boxed onto #34, which pays the bill.
      **(c)** **One of the archival search's nine dimensions did nothing.** `bagging_temperature`
      is Bayesian-only and CatBoost's CPU default is not Bayesian: measured, temperatures 0.0 and
      1.0 give a bit-identical fit under the default and 0.1444 vs 0.1526 under `Bayesian`. `FIXED`
      pins the bootstrap. Two other beliefs were checked and were wrong — `depth=25` under
      `Lossguide` is accepted, and `od_type='IncToDec'` beside `early_stopping_rounds` is a
      redundancy rather than a conflict — and `MedianPruner(n_warmup_steps=10)` over ten folds
      **never pruned**, because every step index was below the warmup.
      **(d)** **The raw interval under-covers: 64.4 % against a nominal 80 %**, in every fold
      (0.57–0.70), with **zero crossings** on real rows. That is #27's gap, measured before #27
      starts. The probe's honest nested R² is **0.746** in weight percent, against REPORT.md's
      published 0.892.
      **L12 is closed and its sentinel written**: the fit is **unweighted**, `sample_weights` slices
      to the declared features in its first statement, and `assert_weights_ignore_target` perturbs
      the target twice — shuffled-and-rescaled, then replaced by a ramp — because the first
      perturbation alone passed `np.where(y > 9, 2, 1)` over a batch topping out at 5 wt%.
- [x] **#27** MAPIE conformal calibration. **Landed 2026-09-05.** The open question — CQR on the
      MultiQuantile model, one CatBoost per quantile, or `SplitConformalRegressor` around the
      median — is settled in favour of **CQR via MAPIE `prefit=True` with three one-column adapters
      over #26's single model**, and [LIBRARY-APIS.md](LIBRARY-APIS.md) now records the four
      source-level facts that decide it rather than a RISK block.
      **(a) The config contradicted itself and nothing raised.** `conformal.confidence_level: 0.90`
      sat beside `model.quantiles: [0.1, 0.5, 0.9]`, an 80 % band. MAPIE's prefit contract is exact
      — lower `(1-cl)/2`, upper `(1+cl)/2`, median 0.5 — and MAPIE *does not check it*, so the pair
      would have calibrated the wrong band silently. The **level** moved to 0.80, not the heads,
      because moving the heads refits the model and invalidates #26's 64.4 % baseline; `_validate`
      now refuses a file where the two disagree, which is what turned
      `test_an_alpha_passed_as_a_confidence_level_is_caught` from "accepted, reader warned" into a
      real refusal.
      **(b) The gap reproduced on a second partition.** Raw coverage on the 172 calibration rows is
      **0.6744** against nominal 0.80 — #26 measured 0.644 over its five nested folds, on different
      rows. The correction is **+0.037355** in model space; calibrated coverage on those rows is
      0.8081 and the mean width goes 0.6741 → 0.8951, a 33 % widening. **Zero crossings before and
      after**, as #26 found. **Corrected 2026-09-06, and the correction is the point.** These
      numbers read 0.6628, +0.030990 and 0.7317 → 0.9155 in this document, in card #27 and in three
      board handoffs until then, and all of those came from a calibration run made at 14:35 on
      2026-09-05 — **nine hours before `model-chosen.csv` existed**, so `_params` found no table and
      fitted on **CatBoost's own defaults**. It said so on stdout and nowhere else. The three
      `conformal*.csv` files behind them were never committed, so the only evidence for a number
      three documents quoted was an untracked file from a fit nobody would ship. Regenerated by
      `calibrate --save` against the deployed configuration.
      **(c) The artifact stores a number, not a calibrator.** `FittedConformal` holds one float and
      the accounting that says what it means; MAPIE is imported lazily inside the fit and a
      subprocess test asserts the prediction path never touches it. What buys the right to throw
      MAPIE away is a parity assertion at fit time — applying the stored constant reproduces
      `predict_interval` to 1e-12 — repeated independently in the test suite against MAPIE directly,
      the AC-2 pattern.
      **(d) The row cost, stated.** `model.calibration_folds: 5` carves 172 rows off the 873
      screened training rows, so the deployed model grows on **701** where the cross-validation that
      estimated its performance fitted on folds cut from all 893. `conformal-rows.csv` reports that
      asymmetry rather than leaving it to be inferred from two files.
      **(e) One constant, chosen a priori.** `symmetric_correction=True`. The two rules cannot be
      compared on evidence — calibration-set coverage is nominal by construction for both, and
      comparing them on test is leak L2 in a new place — so the one-sided miscoverage is a model-card
      diagnostic and is not acted on. MAPIE **1.5.0** is installed in `Project` and pinned; CI now
      installs `.[dev,uq]` so the parity and ordering tests cannot silently `importorskip` away.
- [x] **#28** `predict()` — the surrogate's public interface. `hydms/surrogate/predict.py`:
      `predict(formulas, temperatures)` → `[q0.1, q0.5, q0.9, lcb, interval_width]` in weight
      percent, over a `Surrogate` that `load_surrogate()` pins to one gate-checked artifact
      version. **(a) The heads keep `column_names`' spelling**, not the card's `p10/p50/p90`:
      `model.quantiles` is configuration, and `column_names` is the project's single place where a
      CatBoost column position becomes a name — the practical payoff is that `quantile_metrics`
      scores this frame unchanged, which is what #29 needs. **(b) `lcb` is read off
      `conformal.lower`**, not off column 0, so it is the bound the calibration actually targeted.
      **(c) `interval_width` is not the stored constant doubled** — the correction is constant in
      `log1p` space and `expm1` is convex, so three candidates at 250/400/600 K return three
      distinct widths. **(d) The scaler is never applied, and that is measured**: a second version
      stores a scaler that raises on `transform`, the test arms the trap and then demands identical
      numbers. Its consumer is #48's distance-based AD, not this path. **(e) The gate check is
      never relaxed** — `require_gates=False` is not forwarded and has no equivalent, which is
      strictly stronger than the promotion pointer, since `promote()` already refuses incomplete
      gates. **(f) `MODEL_PAYLOAD` and `model_from` were owed** and now sit beside `QuantileModel`,
      completing the `scaler_from` / `conformal_from` trio.
- [~] **#29** Evaluation metrics with bootstrap CIs. **Machinery landed 2026-09-05; the numbers are
      owed by the one run.** `hydms/surrogate/evaluate.py` bootstraps over **canonical compositions**
      rather than rows (a row resample would be a fourth meaning of "the same material"), reports R²,
      RMSE and MAE on **both** scales, breaks out per outer fold and per temperature band from a
      single split-level resample, and carries the too-narrow caveat as a **column** on every row
      with the cruder per-fold interval beside it. SHAP and PDP run on the deployed fit's own
      training rows — read off `model.record.fitted`, not re-derived from the split, because
      screening drops some of them — and **HG-1 is 13/13**.
      Three things were measured rather than assumed. **(a) There was nothing to bootstrap:**
      `_score_fold` computed `model.predict(scored)` and dropped the frame, so a nested run left
      behind five fold scores whose spread #24 had already measured to be confounded with training
      size. `Evaluation.out_of_fold` now keeps the row-level predictions, through a sink on
      `ScoringTask` that checks what arrives against the fold's own held-out labels — a contender
      handing back rows it was *fitted* on would score beautifully and nothing downstream could
      tell. **(b) SHAP over a MultiQuantile CatBoost is cheap, not expensive**, which is the
      opposite of what the card budgeted: the booster answers `get_feature_importance(
      type="ShapValues")` natively, returning `(rows, heads, features + 1)` in 0.02 s on a 200-tree
      fit over 708 rows. No `shap` dependency, and the cost of this card is not where it was
      expected. **(c) The two boxes that moved here from #34 are in**: no fit re-reads
      `pipeline.yaml` (the column names live on `ModelSettings`, and a test asserts zero reads),
      and the search space is narrowed — see the measurement under #26 below. **The narrowing
      roughly halves the run:** measured at `--trials 2` with screening on, the real command did 35
      fits in 10.4 min — **17.8 s a fit** against the 33 s #26 measured under the old space — so 381
      fits projects to **~1.9 h**, not 3.5.
      Two things verification found that the card had not predicted. **The *cruder* interval is the
      *tighter* one:** at the sentinel budget, R² wt% read `[0.6289, 0.7256]` over groups (width
      0.097), `[0.6247, 0.7262]` over rows (0.102) and `[0.6537, 0.7020]` over the five fold scores
      (**0.048**). The group correction is worth ~5 % of the width, small exactly as the
      13 %-fewer-units measurement predicted; the per-fold interval is **half the width of either**,
      so a reader picking the authoritative-looking number picks the most overconfident one. All
      three therefore ride in one table with `interval_from` on every row. **And a probe's tables
      are the same shape as a real run's:** the first `--emit` in that session produced a document
      from a two-trial probe that read as a finished result, because `train.py`'s
      `These numbers are a cost check, not a result` goes to stdout and #37 reads files. `train.py`
      now writes `model-run.csv` and `evaluate` leads with a warning banner unless it says the run
      was full — an **absent** record defaults to "unknown", never to the good case.
- [x] **The deployed fit was two different models, and is now one.** Found 2026-09-06, while
      settling #34's "persist versus refit" decision. `train.py` built a fit on every screened
      training row and computed SHAP and PDP on it; `calibrate.py` carved a calibration slice out of
      those same rows *first* and conformalised the model grown on the remainder. **873 rows against
      701** — two different models, so the committed explainability tables described a model with no
      band and the committed correction belonged to a model with no explanation. Neither was
      shippable and nothing in the code said so, because the drift lived between two files.
      `hydms/surrogate/deploy.py` is now the single definition — screen, carve, fit, calibrate —
      and both commands call it; `train.py` no longer builds a deployed fit at all and
      `model-shap.csv` and `model-pdp.csv` moved to the command that does. The L1 and L11 sentinels
      were re-aimed at it for the same reason: a sentinel pointed at a fit nothing ships is
      guarding in name only. **The out-of-fold numbers are untouched** — `nested_scores` scores five
      outer-fold models and no deployed fit takes any part in it — which is why this cost two
      minutes and not a second 1 h 41 m run.
- [ ] **#30 (AC-6)** Leave-one-alloy-class-out CV. Unblocked only because #87 restored `Alloy_class`.
- [x] **#31 AC-3** conformal coverage · **#32 AC-1** seed reproducibility · **#33 AC-4** known alloys
      round-trip. **All three landed 2026-09-06 and all three pass against `artifacts/v1`**, and the
      numbers below are now reproducible from the repository — the paragraph that recorded them as
      "observed in a shared tree, gates still `Pending` stubs" is superseded.
      **AC-3**: coverage **0.7795** against nominal 0.8 on 254 held-out `test` rows, raw coverage
      **0.6575** on the same heads with mean widths 0.8630 and 0.6485 wt%. Inside the 0.05 tolerance
      by 0.82 of a binomial standard error (0.0251 at this n), so it passes and does not pass by
      much. That raw number is worth carrying: #26's 64.4 % was a per-fold probe, and 0.6575 is the
      same finding on the split the thesis reports.
      **AC-4**: 30 predictions, **0.0000e+00** disagreement against a 1e-12 bar, over ten rows the
      model grew on across all ten alloy classes.
      **AC-1**: every metric identical across two fits at **1 thread and 20**, same 2,584 trees,
      same best iteration, same correction — see below.

      **#32's open decision is settled by measurement, and neither of its options was taken.** Both
      assumed the fit might not be thread-invariant. It is: fitting the deployed configuration at
      `thread_count` 1, 4 and 20 gives a **bit-identical** head matrix over all 1,279 rows. So
      `thread_count` stays out of `model.FIXED` — pinning it would change nothing measurable and
      cap a 1 h 41 m run's parallelism — **no re-save is owed**, and AC-1 *varies* the thread count
      because the stronger claim turned out to be free.

      **#33's knot is untied without weakening anything.** `load_surrogate` is two things —
      locating a version and assembling a `Surrogate` from a bundle — and only the first has an
      opinion about gates. `surrogate_from(bundle)` is now the second half; `hydms/gates/_artifact.py`
      loads with `require_gates=False` and runs that same assembly, so the only line of the delivery
      path a gate skips is the check whose input it is producing. `load_surrogate` grew no parameter.
- [ ] **#34** Train and publish `artifacts/v1`. Its "persist versus refit" decision is **settled**:
      neither. The deployed fit is rebuilt in two minutes from the committed `model-chosen.csv`, and
      rebuilding it cannot move a published number. **The certification mechanism landed 2026-09-06**
      — `python -m hydms.surrogate.promote` gates a candidate version and, only if everything
      passed, writes a new version carrying the report and moves the pointer. **Promotion itself is
      blocked, and not by missing work:** `promote` requires every registered criterion to have
      passed and 7 of 12 are unwritten, three of them (AC-5, AC-7, AC-8) frozen out of this phase
      entirely. On the rule as written, Phase H ends with a model that can never be promoted and a
      `predict()` that therefore refuses everything — which makes S6 and S7 unreachable. **That is
      an OPEN decision recorded on #34 with three candidate shapes**; it touches the store's central
      guarantee and is not the gate harness's to take.

**Exit check:** `conda run -n Project python -m hydms.gates run --fast` · all HG-1 sentinels green.

---

### S5 — Guard rails · #44, #48, #49 · 2.5 d

**Goal:** the interface can refuse instead of guessing. These three migrated out of the frozen PA
phase because a predictor with no domain check *is* the false-prediction machine this phase removes.

- [x] **#44** Screen interface — a verdict with a **reason**, never a silent drop. **Landed
      2026-09-04, before S4 opened**: it is blocked only by #3, and it is #48 and #49 that wait on
      the surrogate. `hydms.screens.apply_screens(candidates, screens)` runs every screen over the
      whole batch — each called exactly once, whatever the size — and returns one verdict table:
      `admitted`, then `<screen>.passed`, `<screen>.code`, `<screen>.reason` and any evidence
      columns the screen returned. **Nothing is filtered until `Verdicts.select()` is called.** The
      runner is the enforcement point: it refuses a screen that drops, adds or reorders a row, that
      writes into the batch (caught by a position-weighted content fingerprint, not a structural
      check), that returns a malformed verdict, or that emits a code it never declared. A screen
      that cannot judge answers `INDETERMINATE`, which is a **rejection** — fail-closed.
      `window.py` ships the worked screen; `temperature_window()` reads the 195–773 K bound from
      config and is the **outer** bound, never an applicability domain (#48 is that).
- [ ] **#48** Applicability-domain ceiling, derived from #30's LOACO result.
- [ ] **#49** ElMD novelty screen. Needs the `novelty` extra; its API is unverified in
      [LIBRARY-APIS.md](LIBRARY-APIS.md) — settle it in this card.

**Exit check:** `conda run -n Project python -m pytest tests/screens -q`

---

### S6 — Delivery: the deep module and the API · #75–#80 · 5 d

**The design rule:** one deep module owns prediction; the API and the UI are thin transports with no
ML logic in them.

```python
predict_capacity(formula: str, temperature_k: float) -> PredictionResult
```

`PredictionResult` carries the point estimate, the conformal interval and its nominal level, a domain
verdict **with a reason**, the ElMD distance to the nearest known alloy, the model version, and
`refused: bool`. Everything behind it — parsing, canonicalisation, featurisation, column order,
scaling, quantile assembly, conformal widening, the AD check — is hidden. An immutable
`ArtifactBundle` loads once at startup, version-stamped.

- [ ] **#75** `hydms/delivery/contract.py` — request / result / refusal schemas.
- [ ] **#76** `hydms/delivery/predict.py`. Use `codebase-design` / `software-design-philosophy`: this
      is the phase's one genuinely deep module, and the place a shallow pass-through would leak the
      whole pipeline into the API and the app.
- [ ] **#77 (HG-2)** The refusal path — unparseable formula, unknown element, T outside the trained
      range (195–773 K), outside the AD ceiling → a **structured refusal with a reason**, never a bare
      number.
- [ ] **#78** `hydms/delivery/api/` — FastAPI: `POST /v1/predict`, `POST /v1/predict/batch`,
      `GET /v1/health`, `GET /v1/model`. Use `backend-development`: validation at the boundary, **no ML
      in the route handler**, structured errors, a health check reporting the loaded artifact version,
      no silent fallback to an unversioned model.
- [ ] **#79 (HG-3)** API contract tests — OpenAPI snapshot + **transport parity** against
      `predict_capacity()`.
- [ ] **#80** `docs/API.md`. Use `grill-with-docs`; the interview must answer *"how does a caller tell
      a refusal from a genuinely low prediction?"* before the doc is written.

**Exit check:** `conda run -n Project python -m pytest tests/delivery -q` · HG-2 and HG-3 green.

---

### S7 — Delivery: the interface · #81–#84 · 3.5 d

**The deliverable.** Streamlit is an **HTTP client**, not an in-process caller, so the API stays the
single prediction path and HG-3 covers the UI too.

- [ ] **#81** App chart vocabulary in `hydms/figures/`. Use the `dataviz` skill. Five charts, each
      chosen because it makes a false prediction harder to believe:
      1. **Prediction band** — the point estimate drawn *inside* its conformal interval, width stated
         numerically. A wide band must look wide.
      2. **Domain strip** — where this composition sits against the training distribution and the AD ceiling.
      3. **Temperature sweep** — predicted wt% across the valid T range with the interval as a band.
         Only 39 test rows sit above 500 K; the chart must not hide that.
      4. **Nearest neighbours** — the k closest training alloys by ElMD with their *measured* capacities.
      5. **Parity plot** *(model card)* — predicted vs measured on the held-out test set, with the
         **LOACO** version beside it. The optimistic number and the honest number share a page.
- [ ] **#82** `app/main.py` — formula + temperature → capacity.
- [ ] **#83** `app/pages/` model card. **Must carry two things** or the UI recreates the problem it was
      built to fix: the material-vs-system caveat from PRD §4.4 (comparing a material wt% to a DOE
      system target is a two-step overstatement), and a link to `docs/REPORT-RECONCILIATION.md` so the
      old published figures are not quietly inherited.
- [ ] **#84** Batch CSV screening page.

**Exit check:** `conda run -n Project streamlit run app/main.py` plus the manual acceptance in §5.

---

### S8 — Evidence and close · #89, #85, #86, #35, #36, #37 · 5 d

- [ ] **#89** `docs/REPORT-RECONCILIATION.md` — the eight prose-vs-artifact contradictions, each with
      the CSV that refutes it. **REPORT.md is not corrected in place**; it is the archival record.
- [ ] **#85** ADR — the delivery seam and why the API owns no ML logic.
- [ ] **#86 (HG-4)** Extend the CI fast lane with the delivery suite, the freeze check, and
      ruff / mypy / coverage.
- [ ] **#35** `CONTEXT.md` glossary · **#36** five ADRs · **#37** Chapter 1 revision.
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
- **Naming a gate makes the run strict.** `run HG-2` exits non-zero while HG-2 is unimplemented —
  which is why the `## Runnable check` on #31, #32, #33, #71, #77 and #79 is honest from the day it
  is written. `run --all` tolerates skips, because CI that is red for the length of the phase is CI
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
and deliberately so (card #4).

| Gate | Card | Fails when |
|---|---|---|
| **HG-1** Leak sentinels | #71 | Any leak in §1 can be reintroduced without a test going red: a detector stopped firing, a sentinel's subject module exists with nothing wired to it, or a leak has neither a sentinel nor a recorded deferral. Green only when all thirteen are checked against the real pipeline |
| **HG-2** No bare numbers | #77 | Any prediction path returns a point estimate without an interval **and** a domain verdict |
| **HG-3** Transport parity | #79 | The API's answer differs from `predict_capacity()`'s for the same input |
| **HG-4** Hygiene | #86 | ruff, mypy, or the coverage floor fail on `hydms/` |
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
# from repo.anaconda.com/pkgs/main -- boxed on card #1.
python scripts/verify_environment.py

# Suite. 724 green as of 2026-09-04, after #4 and #44. Anything red is a real failure: the eight that were red
# earlier that day were the L13 sentinel reading `unwired` between #20 creating its subject and
# #12 wiring it, and both have landed.
conda run -n Project python -m pytest -q
conda run -n Project python -m pytest tests/leaks -q          # HG-1
# Lint and types run OUTSIDE the environment, deliberately: neither imports the project's
# dependencies, and card #68 fixed that the fast lane installs nothing (docs/QA-PROTOCOL.md §6).
ruff check hydms/ tests/ scripts/ && mypy
conda run -n Project python -m hydms.gates run --fast

# Pipeline: one command, no absolute paths (AC-1); same seed twice -> identical metrics
conda run -n Project python -m hydms.pipeline run --config hydms/config/pipeline.yaml

# API
conda run -n Project uvicorn hydms.delivery.api:app --port 8000
curl -s localhost:8000/v1/model
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"LaNi5","temperature_k":298}'
# expect: estimate + interval + level + domain verdict + elmd + model_version
curl -s -X POST localhost:8000/v1/predict -H 'content-type: application/json' \
     -d '{"formula":"Xx9Zz3","temperature_k":298}'
# expect: a structured refusal with a reason, HTTP 422 — never a number

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
  canonical key (`Ce0.07692Mg0.9231`, #87); what is left to check here is that the *prediction path*
  keys them rather than featurising the strings.
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
