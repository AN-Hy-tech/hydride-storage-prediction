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
| **L7** | `benchmark_model_selection.py:895`, `Catboostmodel.py:522` | Row-level `StratifiedKFold`, no groups — **141 of 896 train rows (15.7 %)** share a formula across folds |
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
      because the leak is absent**. Ten of the thirteen are written; three are recorded deferrals.

| Leak | Sentinel | Detector |
|---|---|---|
| L1, L5 | The `eval_set` identity is the **validation** split; `use_best_model=True` with an empty or test eval set raises | `assert_early_stopping_is_honest` |
| L2, L4 | The model-selection record contains no held-out metric; the reported score comes from folds disjoint from the tuning folds | `assert_selection_is_nested` |
| L3, L10 | `y` **and** `X` for val and test are byte-identical before and after any screening stage | `assert_holdout_unchanged` |
| L6 | Re-running selection with held-out rows perturbed produces an identical feature set, order included | `assert_selection_ignores_holdout` |
| L7, L8 | No **canonical** composition appears in two splits, and none in two CV folds | `assert_disjoint_groups` |
| L9 | Reordering an input never changes the merged result silently, and a row the merge cannot key raises | `assert_merge_is_keyed` |
| L13 | `Alloy_class` survives featurisation: the column, every row, every label unchanged | `assert_metadata_survives` |
| L11, L12 | **Deferred** — each needs a decision its owning card has not made. Boxed on #29, #26 | — |

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
- [~] **#14** CleanLab may **drop or reweight training rows only**. Val and test targets are
      immutable. **Contract and structural screening landed; the card is `doing`, not `done`.**
      `hydms/data/screening.py` drops training rows and refuses everything else: no label rewritten
      on *any* split (`CleanLab.py` rewrites training labels too, at `:64,80`), no held-out row
      touched, and `assert_holdout_unchanged` called three times from inside `screen` before it
      returns. **Reweighting is declined** — the only weighting the archival pipeline had is
      target-conditioned (L12) and choosing a policy is #26's. Two rows are dropped from training,
      both decided here: the byte-identical duplicate (found with `duplicated`, not by row number)
      and `Mg0853Ni0.125La0.022`, whose correction is unambiguous but must be applied upstream of
      the canonical key — boxed on #9. **L3 and L10 are wired and green.** What is owed to S4: #24
      consuming this stage's output, which is what closes the `Boruta_FeatEng.py:23-25` bypass and
      also supplies the feature matrix CleanLab needs to produce `label_issues` at all.
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
- [ ] **#21 GATE AC-2** — parity with CBFV to 1e-9 on all 1,279 formulae. **Hard gate.** If it fails,
      the reimplementation is wrong, not CBFV. **Two amendments from #16:** parity is measured against
      the reference table, not the shipped one; and no Eu-containing formula can be compared at all,
      because this layer refuses where CBFV returns a silently-zeroed number.
- [ ] **#22** Featurisation throughput benchmark.

**Exit check:** `conda run -n Project python -m hydms.gates run AC-2`

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

- [ ] **#23** Scaler: fit once on train, persist, never refit.
- [ ] **#24** Port selection reading **CleanLab output**, run **inside the training folds** (L6).
- [ ] **#25** Run selection once; publish the old-22 vs new-N comparison.
- [ ] **#88** `hydms/surrogate/validation.py` — `StratifiedGroupKFold` on the canonical key (L7),
      **nested** so the reported score comes from an outer fold the tuner never saw (L4).
- [ ] **#26** CatBoost MultiQuantile with `use_best_model=True` and the **validation** split as
      `eval_set` — CatBoost raises at fit time on an empty eval set, the mechanical guard against L1.
      `MultiQuantile` is CPU-only. Assert the quantile column order: position is the only thing
      identifying the columns.
- [ ] **#27** MAPIE conformal calibration. **MAPIE 1.x, not 0.x**: `fit()` → `conformalize()` →
      `predict_interval()`, `confidence_level` not `alpha`. Choose between CQR-on-MultiQuantile, one
      model per quantile, or `SplitConformalRegressor` around the median — see
      [LIBRARY-APIS.md](LIBRARY-APIS.md).
- [ ] **#28** `predict()` — the surrogate's public interface.
- [ ] **#29** Evaluation metrics with bootstrap CIs. SHAP/PDP on **train or a dedicated split, never
      test** (L11).
- [ ] **#30 (AC-6)** Leave-one-alloy-class-out CV. Unblocked only because #87 restored `Alloy_class`.
- [ ] **#31 AC-3** conformal coverage · **#32 AC-1** seed reproducibility · **#33 AC-4** known alloys
      round-trip.
- [ ] **#34** Train and publish `artifacts/v1`.

**Exit check:** `conda run -n Project python -m hydms.gates run --fast` · all HG-1 sentinels green.

---

### S5 — Guard rails · #44, #48, #49 · 2.5 d

**Goal:** the interface can refuse instead of guessing. These three migrated out of the frozen PA
phase because a predictor with no domain check *is* the false-prediction machine this phase removes.

- [ ] **#44** Screen interface — a verdict with a **reason**, never a silent drop.
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
- **Naming a gate makes the run strict.** `run AC-2` exits non-zero while AC-2 is unimplemented —
  which is why the `## Runnable check` on #21, #31, #32, #33, #71, #77 and #79 is honest from the day
  it is written. `run --all` tolerates skips, because CI that is red for the length of the phase is
  CI nobody reads.
- **Each gate declares its own lane.** `Speed.FAST` means answerable against the published artifact;
  `Speed.SLOW` means it needs a retrain. Cards #6 and #7 select on that rather than deciding it.

A run writes its results as JSON under the configured artifacts directory, behind a versioned
`schema` key. Card #4's manifest embeds that object under `gates` when it lands.

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

# Suite. 566 green as of 2026-09-04. Anything red is a real failure: the eight that were red
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
