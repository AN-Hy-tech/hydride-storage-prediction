# Phase H — the closed stages, in full

**This file is history, not status.** It is §3 of [../PHASE-H-RUNBOOK.md](../PHASE-H-RUNBOOK.md) for
stages **S0 through S6**, exactly as that file carried it on 2026-09-13, moved here when every card
in those seven stages reached `done`. Nothing was corrected or summarised on the way in — only the
relative links were re-pointed for the new depth.

**Why it moved.** The runbook is read at the *start* of a session, to answer "what may I work on and
what must I not break". A closed stage answers neither: its checklists are ticked, its exit checks
have run, and its cards are the authority on what they did. Keeping 1,030 lines of finished work in
front of that question cost every session that asked it.

**What is still live** — S7 and S8, the gate table, the verification block — stayed in the runbook.
Its §3 now carries a one-line summary per closed stage and points here.

**Read this for the reasoning, never for the state.** Where a line here contradicts a card, the card
wins. The boxed notes are the valuable part: they record *why* a stage was shaped the way it was, and
several of them are the only written account of a decision.

---

### S0 — Freeze and tooling · #72 · 1 d

**Goal:** the freeze exists and is enforced before any code moves.

- [x] Install the `ml-model-training` skill and review what it installed.
- [x] `git mv` cards 1–37, 44, 48, 49, 68 into `kanban-hardening/`. Ids unchanged.
- [x] Write [FREEZE.md](../FREEZE.md) and this runbook.
- [x] Extend [scripts/check_board.py](../../scripts/check_board.py) — two boards, one id space, plus
      the freeze status rule.
- [x] Write [scripts/check_freeze.py](../../scripts/check_freeze.py) — the diff half of the freeze.
- [x] Write [kanban-hardening/README.md](../../kanban-hardening/README.md) — the board charter.
- [x] Create cards #69–#89; amend #12, #13, #14, #24, #26.
- [x] Wire the freeze check into `integrity.yml` — since absorbed, with `check_board.py`, into
      the `hygiene` job of [.github/workflows/ci.yml](../../.github/workflows/ci.yml) by card #6.
- [x] Repoint [CLAUDE.md](../../CLAUDE.md) and mark [kanban/README.md](../../kanban/README.md) frozen.

**Exit check**

```bash
python scripts/check_board.py --root .
python scripts/check_freeze.py --base origin/main
```

> **On the `ml-model-training` skill.** It is generic, MIT-licensed, and correct about scaler leakage.
> It is **silent** on group-aware splitting, nested CV, and early stopping on the scoring set, and its
> worked example is a plain `train_test_split` with no `random_state` and no grouping — which in this
> project would reintroduce L4, L7 and L8. Use it for model-fitting mechanics only. This project's
> authority order puts skills below the [research/](../../research/) memos; on any validation question
> the memos and this runbook win.

---

### S1 — QA foundation · #69, #70, #5, #71 · 2 d

**Goal:** somewhere to put every later test, and the sentinels that make the leaks un-reintroducible.

[pyproject.toml](../../pyproject.toml) declares `pytest`, `ruff` and `mypy` and **configures none of
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
      **Do not regenerate the lock file:** [ENVIRONMENT.md](../ENVIRONMENT.md) records a hand-applied
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
      the canonical key — #9 decided against a correction layer (2026-09-12); the row is dropped and named. **L3 and L10 are wired and green.** The CleanLab call itself
      is `hydms.data.screening.label_issues` — added by #24, which supplies the matrix, but living
      here because *which rows are label-suspect* is this card's to own. It returns two of
      CleanLab's four columns: `predicted_label` is `CleanLab.py:90`'s leak in raw form and there is
      now no object a caller could reach one through. It runs **inside the folds**, called by the
      selector on the rows that selector owns; the per-split counts #15 and #37 read come from a
      separate pipeline-level `screen` over the whole frame. **#15 must re-measure `rows_out` and
      `removed` against that call.**
- [x] **#15** Data-layer golden tests. **Written green, held in `backlog` by `check_board.py`
      until #14 landed, and closed once the re-measure below was taken.** `tests/data/test_golden.py` pins 34 facts as one record
      and reports a deviation as a table of fact/expected/actual rather than as a bare assertion.
      It separates *facts that must not move* (1279 rows, 1149 strings, 1115 compositions, the ten
      classes) from *facts that moved on purpose* — the split is pinned at 893/131/255 **with** the
      published 896/136/247 beside it under `split_rows.published_*`, so restoring the old number
      is a visible failure rather than a silent return to the leaky split. The card cannot leave
      backlog while #14 is unfinished, and that is right on the substance: when #24 lands,
      CleanLab starts flagging rows and `screened.rows_out` / `screened.removed` move.
      **The re-measure was taken, and the answer was better than "those two moved".** They did
      *not* move — `measure()` calls `screen()` without `label_issues=`, so GOLDEN's 1277 / 2 are
      the structural findings alone and stay structural. What CleanLab's verdict does is recorded
      as a **second record**, `DEPLOYED_SCREENING`, measured on the 893 training rows the deployed
      fit is actually offered: **kept 873, removed 20, flagged 18**, with
      `removed_before_cleanlab: 2` beside it so the whole-frame 2 and this 2 are shown to be the
      same two rows rather than assumed to be. It is reconciled against
      `reports/model/conformal-rows.csv`, which records the same 893 and 20 for that run, and
      `screened.label_quality_findings: 0` asserts the separation instead of commenting on it —
      if anyone starts passing a verdict into `measure()`, it goes red. The two are answers to
      different questions: what the *stage* removes with no judgement, and what the *pipeline*
      removes with one.

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
      the layer it measures.** `hydms/descriptors/benchmark.py`, [BENCHMARKS.md](../BENCHMARKS.md).
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
**State (2026-09-12): closed.** All thirteen boxes are ticked. **#34 promoted the artifact on
2026-09-12 at 17:37:26Z** — `promote --waive AC-5 --waive AC-7 --waive AC-8` certified `v2` with
**9 passed, 0 failed, 3 skipped, 0 errored in 175.56 s**, wrote **`artifacts/v3`** carrying the gate
report, and pointed `current` at it. `v2` remains on disk as the record of the fit: a manifest is
sealed when written, so the report could not be added to it and a certification necessarily produces
a new version.

~~The one open box is **#34**, and it is not waiting on anything S4 owns.~~ That was true from
2026-09-06 to 2026-09-12 and is worth keeping as the shape of the stage: promotion needed HG-2, HG-3
and HG-4, which #76–#79 (S6) and #86 (S8) build, and they are Phase H's own criteria so they must
not be waived. HG-2 landed with #77 on 2026-09-11, HG-3 with #79 on 2026-09-12 and HG-4 with #86 the
same day; they were `blocked_by` edges on #34 rather than a sentence here, because the board had
shown a `doing` card with every declared blocker `done`, which reads as "ready to close".

**Two boxes left the card rather than closing with it.** The `--report` trap went to **#96** (both
its candidate fixes are in the surrogate seam), and the `SCALER_PAYLOAD` removal went to **#7** —
because `v3` was written that evening and *carries* the scaler. `promote` copies the payload set of
the version it certifies; it fits nothing, so **only a fit can change the set**, and the next fit is
#7's retrain.

~~Nothing downstream is blocked on it.~~ **Nothing in the *delivery* chain is** — S6 and S7 run
without it, which is the claim that mattered. Three S8 cards do wait on it: #36 (the ADRs), #37
(Chapter 1) and, until 2026-09-11, #89. **#89's edge was fiction and has been cut**: its own
*Done when* names #29 and #30 as its sources and every one of them is a committed CSV, so the
reconciliation never needed a promoted version. That mattered more than bookkeeping — #83 (S7)
cannot tick "a link to `docs/REPORT-RECONCILIATION.md`" until #89 writes the file, so an S7 card was
sitting behind #34 behind #86 behind #79 by way of an edge nothing supported.

```
#23 scaler fit-once → #88 group-aware nested CV (L4, L7) → #24 selection inside folds (L6)
→ #25 old-22 vs new-N → #26 CatBoost, honest early stopping (L1, L5)
→ #27 MAPIE conformal → #28 predict() → #29 metrics + bootstrap CI → #30 LOACO CV
→ #31 AC-3 · #32 AC-1 · #33 AC-4 → #34 promote the artifact (v2)
```

**These arrows are prose; `blocked_by` is the graph, and where they disagreed the graph was right.**
This chain read `#24 → #25 → #88` until 2026-09-11, but #88 is blocked by `[13, 23]` and #24 by
`[14, 20, 88]`, so S4 opened at **#88**, not at the #24 the arrows pointed at. Ask the board which
card is startable — `bash $S/list_all_cards.sh kanban-hardening/` — and read this line for the
*shape* of the stage, never for its order.

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
      over #26's single model**, and [LIBRARY-APIS.md](../LIBRARY-APIS.md) now records the four
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
      numbers. Its consumer is #48's applicability domain, not this path — which #48 has since established is **not** distance-based. **(e) The gate check is
      never relaxed** — `require_gates=False` is not forwarded and has no equivalent, which is
      strictly stronger than the promotion pointer, since `promote()` already refuses incomplete
      gates. **(f) `MODEL_PAYLOAD` and `model_from` were owed** and now sit beside `QuantileModel`,
      completing the `scaler_from` / `conformal_from` trio.
- [x] **#29** Evaluation metrics with bootstrap CIs. **Machinery landed 2026-09-05; the run that
      owed the numbers happened, and `reports/model/` is committed.** `hydms/surrogate/evaluate.py` bootstraps over **canonical compositions**
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
- [x] **#30 (AC-6)** Leave-one-alloy-class-out CV. Unblocked only because #87 restored `Alloy_class`.
      **Built, run and closed 2026-09-06/07 — AC-6 is green.** `python -m hydms.surrogate.loco`
      is `train`'s protocol with `outer=leave_one_class_out` — one keyword argument, no second
      scoring path. What the module adds is the reporting layer, because AC-6 asks that the
      extrapolation number be published *alongside* the interpolation one and the ways a table can
      fail that are all about presentation: every class appears with `rows_scored` and
      `compositions_scored` beside its score, a class whose R2 is *undefined* (fewer than two
      held-out rows, or a constant held-out target) is marked `estimable=False` with the reason in
      words rather than dropped, and both the macro and the support-weighted averages are
      published because they answer different questions. **AC-6's gate is written and reads the
      committed tables rather than refitting** — a gate cannot pay the run, and one that fitted a
      cheaper version would certify a number nobody publishes — so the lane moved `SLOW` → `FAST`
      and `reports/loco/` is un-ignored, without which the gate would read an empty directory in
      CI. **The run happened once, on 2026-09-06, 18:16:09 to 22:23:13 — 4 h 07 m**, inside the
      4.7 h `--budget` ceiling (10 class folds x 3 inner x 25 trials, about 2.0x the random-split
      run) and roughly 7 % over the estimate scaled from it, so `--budget` was the better bound.
      **The result: macro transfer R2 0.2734 over ten estimable classes of ten, against the
      random-split 0.7459 — a gap of 0.4725.** Support-weighted **0.2153**, *below* the macro
      average; worst **Mg -0.3381**, best **SS 0.7626**. AC-6 went green on the committed tables
      with no code change, and the suite's one skip went with it. **Two findings the number
      carries, both boxed rather than fixed:** interval coverage degrades out of family and
      *unpredictably* so — Mg 0.1146 against the random-split 0.6293, while HEA reaches 0.8824 —
      which is the argument for #48 in one table, since conformal's guarantee is marginal and
      assumes an exchangeability that holding out a whole family breaks by construction; and the
      per-class scores carry **no interval**, deliberately, so a 19-row LEA fold weighs exactly as
      much in the macro mean as a 260-row AB2 one. Say so wherever the number is published.
      *(The card's own sentinel-budget probe, kept only because it falsified a sentence the module
      had already written: macro 0.2240, weighted 0.1664 — the weighted average sits* below *the
      macro one, not above it, so the document now computes the direction instead of predicting
      it.)*
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
- [x] **#34** Train and publish the deployed artifact version. **Done 2026-09-12: `current` →
      `v3`.** The account below is the decision history and is left standing, because the shape of
      the wall it describes is the reusable part. Its "persist versus refit" decision is
      **settled**:
      neither. The deployed fit is rebuilt in two minutes from the committed `model-chosen.csv`, and
      rebuilding it cannot move a published number. **The certification mechanism landed 2026-09-06**
      — `python -m hydms.surrogate.promote` gates a candidate version and, only if everything
      passed, writes a new version carrying the report and moves the pointer. **Promotion itself is
      blocked, and not by missing work:** `promote` requires every registered criterion to have
      passed and 7 of 12 are unwritten, three of them (AC-5, AC-7, AC-8) frozen out of this phase
      entirely. On the rule as written, Phase H ends with a model that can never be promoted and a
      `predict()` that therefore refuses everything — which makes S6 and S7 unreachable.
      **Settled 2026-09-06, and by none of the three shapes #34 proposed.** A promotion may now
      name a waiver: `promote --waive AC-5 --waive AC-7 --waive AC-8`. The waiver is an *act*
      recorded in `current.json`, not a property of a criterion and not a change to the rule — a
      `FAILED` gate is never waivable, `hydms/gates/` and `Manifest` are untouched, and the
      promoted version's embedded report still records all three as `SKIPPED`. Promotion is now
      blocked by **work rather than by a decision**: AC-6, HG-2, HG-3 and HG-4 are this phase's own
      (#30, #77, #79, #86) and must not be waived. **AC-6 came green on 2026-09-06** with the LOCO
      run, HG-2 with #77 on 2026-09-11 and HG-3 with #79 on 2026-09-12, so what remains is **HG-4
      alone** — built by #86, which is why #34 cannot close inside S4 and is not waiting on anything S4 owns. **The version to promote is
      `v2`, not `v1`** (re-saved 2026-09-07 from a clean tree; v1's manifest records
      `code_modified: true` and a manifest is sealed when written). Same model: correction
      +0.037355, the same `model-chosen.csv:outer-0` configuration, and the five regenerated
      report CSVs byte-identical to the committed ones.

      **Closed 2026-09-12T17:37:26Z.** HG-4 came green with #86 that morning, so the maintainer ran
      `promote --waive AC-5 --waive AC-7 --waive AC-8`: **9 passed, 0 failed, 3 skipped, 0 errored
      in 175.56 s** certifying `v2`, then `v3` written with the gate report embedded and `current`
      moved to it. The waiver stayed an *act* to the end — `v3`'s report still records AC-5, AC-7
      and AC-8 as `SKIPPED`, and the run printed *"NOT CHECKED: AC-5, AC-7, AC-8. This run
      establishes nothing about them."* **`artifacts/` is gitignored**, so `v3` exists on the
      maintainer's machine and nowhere else; a fresh clone has no model and that is #7's to fix.

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
- [x] **#48** Applicability-domain ceiling, derived from #30's LOACO result. **Landed 2026-09-07,
      and the decision it carried dissolved.** The card offered a per-family ceiling or one
      distance calibrated against the per-class curve; both assume the degradation is mediated by a
      composition distance, and it is not. Per-class transfer R2 against per-class isolation, n=10
      Spearman: **-0.2727** in element-fraction space, **-0.2848** in the model's own 14-feature
      space — and inverted at the ends, since the two *least* isolated families score among the
      best. The feature-space figure is what closes it for ElMD as well: the model reads fourteen
      numbers, so no metric over a space it never reads can be the mechanism behind its failures.
      **The ceiling is therefore a capacity, and it is computed rather than chosen**: 5.19 wt%, the
      highest level more than one alloy class reaches in training. Above it the corpus holds 21
      rows and every one is `Mg`, the family #30 measured at R2 -0.3381 with interval coverage
      0.1146. `hydms/screens/domain.py` declares five rejection codes — `OUT_OF_DOMAIN`,
      `ABOVE_PHYSICAL_CEILING`, `OUTSIDE_FEATURE_RANGE`, `UNTRUSTED_FAMILY`, `HIGH_UNCERTAINTY` —
      plus the shared `INDETERMINATE`, and every threshold is a `domain.*` config key.
      **The card's own prescribed physics constant was wrong and measuring it first is what caught
      it**: `H/M_max` = 2 puts **31 curated rows above their own physical ceiling**, because the
      rare earths form trihydrides and `Th4H15` reaches 3.75. The rule is `max(2.5, element-wise
      max)`, which leaves four, three of which are Ce-Ni data defects now boxed on #14.
- [x] **#49** ElMD novelty screen. **Landed 2026-09-07.** The `novelty` extra is installed —
      ElMD **0.5.15** into `Project`, and it moved nothing: numba, numpy and scipy were already
      there, so pip installed exactly one package and `requirements-lock.txt` gained one line.
      The API is settled in [LIBRARY-APIS.md](../LIBRARY-APIS.md), and the entry that matters is
      that on ElMD's default `mod_petti` metric the distance is a **closed form** —
      `sum(abs(cumsum(a - b)))` over a 103-slot Pettifor vector — so the whole batch is one
      `cdist` on cumulative vectors. Verified equal to ElMD's own answer to **3.6e-15** over
      the curated corpus, at ~37 M pairs/s, **46x** the warm pairwise loop.
      `hydms/screens/novelty.py` declares one rejection code, `BEYOND_KNOWN_CHEMISTRY`, plus
      the shared `INDETERMINATE`, and every candidate carries `novelty.distance` and
      `novelty.nearest` on its verdict row whether it passed or not — AC-7 is a reporting
      obligation, so the number rides on the verdict frame rather than on a second return path.

      **The threshold is computed, and it is not the applicability domain.** #48 established
      there is no transfer curve to calibrate against, so the ceiling is calibrated against the
      corpus's own internal spread: **11.7320**, the largest distance from a training
      composition to its nearest *other* training composition, set by `Li0.94Pd1` against
      `Ce1Ni1` and named in the reference so a reader can see what holds it up. It rejects
      **0 of 385 held-out rows**, which is the intended behaviour and is stated rather than
      hidden — the corpus is chemically homogeneous (the most novel held-out row,
      `Ca1Al1.8B0.2`, sits at 6.53 against a metric whose span is 102.0) and the card warned
      that a threshold fitted to look busy on this data would be fitted to noise.

      **Two ElMD defects were found and are load-bearing.** It does not raise on an
      unparseable formula — `ElMD("Xx2")` returns an empty composition whose distance to
      everything is finite and meaningless — so the screen checks normalisation itself and
      answers `INDETERMINATE`, fail-closed. And `ratio_vector` is **not reproducible across
      processes** for a formula of three or more elements: `_fuse` iterates
      `set(mol1) | set(mol2)`, so element insertion order follows the per-process randomised
      symbol hashes and the normalising sum differs by an ulp. Measured: **76 of 780 training
      compositions moved by 2.2e-16 between two processes**, every one of them multi-element.
      That is what made `--emit` irreproducible, so `vectors()` sums the parsed counts in
      sorted symbol order and a test pins the result against `ratio_vector` to 1e-12.

      **A QA pass on 2026-09-07 found a third defect, and it was the dangerous one.** The
      normalisation guard above catches ElMD dropping *every* symbol; it cannot catch ElMD
      dropping *some*. `_dictify` keeps what it recognises, so `ElMD("LaNi5Xx2")` **is**
      `LaNi5` — `ratio_vector` sums to exactly 1.0 and the distance to a real `LaNi5` is
      **0.0**. The screen admitted it, at distance zero, naming `LaNi5` as the nearest alloy:
      a typo answered as a material we already have, which is the precise silent failure #44
      exists to prevent. `TiFeQ` behaved the same way, and `str(pd.NA)` — `<NA>` — read as
      **nitrogen** and drew a confident 16.33. Total loss was loud and partial loss was
      silent, which is the wrong way round.

      The fix is a **second, independent parse**: `hydms.data.load.parse_formula`, this
      project's own grammar, already refuses every one of those strings by name, so
      `_vector()` now requires both parsers to agree on which elements are present and treats
      any disagreement as `INDETERMINATE`. Checked first, because rejecting there skips the
      48.6 us `ElMD(formula)` construction. It refuses nothing real — the two parsers agree
      on all **1,149** distinct curated formulas and all **780** reference compositions, and
      `--emit` still reproduces the committed reference byte-for-byte. The same pass closed
      two holes in `NoveltyReference.from_json`, which is the boundary where a bad reference
      must become a refusal: a slot outside the scale raised `IndexError` and a **negative**
      slot was silently wrapped by numpy onto Pettifor slot 102, relabelling an element; both
      are now `ScreenError`, as is a non-numeric ceiling, and every reference row is checked
      to be a distribution. `tests/screens/test_novelty.py` went 37 → 49 assertions.

      A follow-up pass the same day found the fix's own **reason** still telling the old
      story: every refusal, partial loss included, read "it parses to an empty formula",
      which is false of `LaNi5Xx2` and points whoever typed it at the wrong thing. L4 owes a
      verdict *with a reason*, so `_vector()` now returns the cause instead of a boolean and
      the verdict quotes `parse_formula`'s own words — `'LaNi5Xx2' names 'Xx', which is not a
      chemical element`. Suite 49 → 55.

      One case no guard can catch, recorded so it is not rediscovered: **`"NaN"` is a valid
      formula** — sodium and nitrogen — to both parsers. A missing value written out as that
      text is indistinguishable from chemistry; keeping missing values out of the formula
      column stays the caller's job.

**Exit check:** `conda run -n Project python -m pytest tests/screens -q`

Both of this stage's measured references are regenerated the same way, and in each case a test
asserts the committed file is what the command produces — the shape #30 used for `loco.md`. Run them
if the curated data or `reports/loco/` ever moves.

```bash
conda run -n Project python -m hydms.screens.domain  --emit   # domain-reference.json
conda run -n Project python -m hydms.screens.novelty --emit   # novelty-reference.json
```

---

### S6 — Delivery: the deep module and the API · #75–#80 (and #90, which has no stage of its own) · 5 d

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

- [x] **#75** `hydms/delivery/contract.py` — request / result / refusal schemas. **Landed
      2026-09-07.** The bare number is unspellable: `interval` and `domain` have no defaults and
      `None` is refused, and `refused` is a *property* on both answer types rather than a field.
      The reason codes are **derived** — `reason_codes()` over `delivery_screens()`, which is
      `temperature_window()` and `applicability_domain()` today and widens on its own when #49
      lands. An unparseable formula and an unknown element have no screen code and carry
      `INDETERMINATE`, which costs #76 an ordering choice and is boxed there and on #77.
- [x] **#90** `docs/REFUSALS.md` — the refusal catalogue. **Landed 2026-09-07.** No stage of its
      own; it slots in here because its blockers (#44, #48, #49, #75) were the last thing it needed.
      Twelve chosen probes run through the real screens and the real #75 contract, and the page is
      **generated** from that run — `python -m hydms.delivery.refusals --emit`, byte-identity
      asserted in the fast lane. It exists for the defect #49 found: a verdict that is right and a
      sentence that is false, which no assertion fits. Two halves *are* automatic — the emitted code
      set must equal `reason_codes()` exactly, and every probe declares the path it was chosen for.
      **Not a gate**: registration as HG-5 is boxed on #91, after the freeze lifts.
- [x] **#76** `hydms/delivery/predict.py` — the deep module. **Landed 2026-09-11.** One call over an
      immutable `ArtifactBundle`; the API and the app are transports above it. The order is
      **null-check, featurise, predict, screen, resolve, answer**, and it is forced rather than
      chosen: the applicability screen judges a *prediction*, so "screen before featurising" was
      never available and a parse failure is caught where it raises and mapped to `INDETERMINATE`
      with the featuriser's own sentence. Three decisions the card owed, all recorded on #85:
      **(a)** that order; **(b)** the ElMD novelty screen joins `delivery_screens()`, so the
      `novelty` extra is now required to predict — a bill `pyproject.toml` and the GPL-3.0 licence
      had already paid, and whose only alternative was `PredictionResult.novelty` permanently
      `None` in a deployment no test covers; **(c)** two caches over one artifact version, holding
      one `Surrogate`, both cleared together. The screen references are **digested, not pinned** —
      `v1`/`v2` are sealed and a re-save would look like a promotion — and the fit-time binding is
      boxed on #91. `resolve()` moved from #90's catalogue into `contract.py` and `_verdicts_for`
      into `predict.py`, so the production path no longer needs to import a document generator.
      Two smaller findings, boxed rather than fixed here: `untrusted-family` is declared and
      published but **unreachable through `predict_capacity()`** (a novel composition has no alloy
      class) → #77; and `"NaN"` is sodium-plus-nitrogen to both parsers and cannot be guarded once
      it is a string → #84 owns the CSV `na_values` decision.
      **QA pass, same day: the card's own guard was aimed one step away from its subject.**
      `ApplicabilityDomain` is deliberately partial — a column it cannot find does not raise, the
      rule just does not run and the screen answers `admitted` — so it is the one screen that can be
      half-run in silence, and the bundle is the only object positioned to notice. The check read
      *config*'s median head, which can only describe the screens `load_bundle` builds itself, the
      one case where it is redundant; a bundle assembled with an explicit `screens=` aimed at
      `q0.42` loaded silently. It also checked one of the two columns that matter: a screen aimed at
      a different `width` loses `high-uncertainty` — the only rule that judges the *band* this call
      is about to report — and the answer said nothing. `_check_columns` now reads each screen's own
      `prediction` and `width`; `alloy_class` stays deliberately unrequired, with a test saying so.
      Two more *wrong words* findings went to #77: a non-string formula is told "the formula is
      empty", and `docs/REFUSALS.md` catalogues the screens' `unreadable-formula` sentence, which
      this path cannot produce because `featurize` raises first. 28 tests, 4.9 s.
- [x] **#77 (HG-2)** The refusal path — a **structured refusal with a reason**, never a bare number.
      **Done 2026-09-11, and the delivery module ran against a real artifact for the first time.**
      `bundle_from()` is the same split #33 made on `load_surrogate`, one layer up, so the gate
      reaches `v2` through `_artifact.candidate` while `load_bundle` still refuses it (pinned by a
      test). Three claims: the contract forbids a bare number *structurally*; every `return` in
      `predict_capacity` is read **from its source** and must be a `Refusal` or a
      `PredictionResult` — which is the only form "exhaustively, not sampled" can take; and eleven
      probes run against the served version. The first two need no artifact, so **HG-2 can go red
      in CI where it cannot go green**. Two of the card's four named causes were not rules this
      system has: "element absent from the training set" is not judged by anything (`Tc2Ni` is
      *answered*, 4.17 against an 11.73 ceiling — #49 built novelty as a composition distance on
      purpose), and the AD ceiling is a capacity rather than a distance (#48). Reachability is now
      **per door** — request vs. curated frame — with `NOT_ALWAYS` separating "no fit can reach it"
      (red if it appears) from "this fit does not" (reported); `docs/REFUSALS.md` labels every row
      with its door and shows what a caller typing it receives instead. Staging the red case found
      a defect in the gate: the "names the range" check was satisfied by a *neighbouring* screen's
      sentence, #49's defect one layer up.
- [x] **#78** `hydms/delivery/api/` — FastAPI: `POST /v1/predict`, `POST /v1/predict/batch`,
      `GET /v1/health`, `GET /v1/model`. **Landed 2026-09-12.** The bundle resolves once, in the
      lifespan, so a store with nothing promoted is a server that does not come up rather than one
      that guesses — there is no lazy load in any request path. **Two things arrive at 422 and the
      body is the only thing that separates them**: a refusal carries `refused` and a rejected
      request carries `error`, which is the inherited obligation from #77 (a `ContractError` must
      not reach a client as a 500) discharged by one envelope, whoever noticed — pydantic or the
      contract. The request models declare only what the transport can see (JSON types, unknown
      fields, `extra="forbid"` so a caller cannot name its own screens or version, #75); every
      semantic rule stays with `PredictionRequest`, so a caller is shown the contract's own
      sentence rather than a second opinion. The batch limit is **256**, measured rather than
      chosen: a served prediction costs 66–78 ms against `v2` (13 ms featurise, 22 ms surrogate,
      34 ms screens) and is linear in the rows, so 256 is ~19 s here and ~38 s on a machine half
      this speed — inside the 60 s a client or proxy typically allows. `GET /v1/model` reports
      `reference_digests` (the other inherited obligation), the training date and the gate record
      from the version's manifest — which is now carried on the `ArtifactBundle`, `None` for a
      bundle the gate door assembled, because an absent record must read as unknown and never as
      clean. **No ML in a handler** is executable twice over: no module under `api/` may import the
      surrogate, the descriptors, the screens or an array library, and no handler may touch a
      private attribute of anything — the second closes the hole the first leaves, since the bundle
      it is handed already holds the model. Both were staged red. 32 tests, 13.6 s.
- [x] **#79 (HG-3)** API contract tests — OpenAPI snapshot + **transport parity** against
      `predict_capacity()`. **Landed 2026-09-12.** The gate sends **HG-2's own probe set** over HTTP
      rather than a second list of its own — a second list drifts, and then "the API agrees with the
      library" is established over inputs nobody checked the library on — and requires the served
      body to equal `to_dict()` **value for value**, reporting a difference by JSON pointer
      (`/interval/lower: the library 1.2345678901234, served 1.23`). The same probes in one batch
      must come back in order, each row equal to its own single-shot answer, which is
      order-preservation and per-row refusal in one comparison. Eight **rejected requests** are this
      gate's own, because `predict_capacity()` has no way to be asked them: an unknown field, a
      formula that is not a string, `NaN` typed as a literal, a batch over the published limit. Each
      must come back 422 carrying `error` and no `refused`, and `answer_from()` must **refuse** it —
      a client that reads an error body as an answer is the one failure in that pair that is silent.
      The **OpenAPI document is committed** at `hydms/delivery/api/openapi.json`, generated by
      `python -m hydms.delivery.api.openapi --emit`, and the comparison needs no artifact: it is the
      half that can go red on a push, and the reason CI now installs the `api` extra. 4.52 s against
      `v2`; 37 tests.
- [x] **#80** `docs/API.md`. **Landed 2026-09-12**, and the interview's required question had a
      crisp answer: **three ways, the third structural.** `200` vs `422`; `refused` false vs true;
      and `capacity` **present vs the key not existing at all** — `refused` is a property on both
      answer types rather than a field on either, so there is no way to spell a bare estimate and
      no way for a low answer to look like a decline. The page leads with `Mg2Ni` at 573 K, which
      is refused `high-uncertainty` for a 1.36 wt% band against the 1.12 limit — refused for
      *width*, not for a small number, which is the case a caller misreads.
      **The page is generated** (`python -m hydms.delivery.apidoc --emit`; 9 tests assert the
      committed bytes). Three sources kept apart because they fail differently: the code read live,
      the **committed OpenAPI document** for the route table (so this page and the contract HG-3
      guards cannot disagree), and a **committed fixture of real exchanges** for anything needing a
      fit. `--probe` is separated from `--emit` because `artifacts/` is gitignored and a generator
      that needed a model would be a check that never runs — **verified by renaming `artifacts/`
      away**, after which the check still passes and all 9 tests still run.
      Reachability is **measured, not hedged**: a 50 x 10 sweep through the request door against
      `v3` reaches 8 of 9 codes, `untrusted-family` being the one it cannot. The page explains why
      that differs from HG-2/HG-3's "unreached on this fit" without either being wrong — a dozen
      probes and a 500-request sweep answer different questions.

**Exit check:** `conda run -n Project python -m pytest tests/delivery` (do **not** add `-q`; pyproject already sets it and a second one hides the count; it is **179 passed in 11.7 s** as of 2026-09-12, up from 160 by #80's nineteen) · HG-2 and HG-3 green. **Both are** — `run --fast` is 7 passed / 0 failed / 2 skipped in 37 s, the two skips being AC-5 (frozen) and HG-4, whose coverage data predates the change and says so. **S6 is closed: #80 was the stage's last card.**

---

---

## S7 and S8, and runbook §5–§6, as they stood 2026-09-26

Moved verbatim when the runbook was compacted: closed cards became one-line rows and the suite-count history left §5. Links re-pointed only.

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
         cannot ship alone. The LOACO panel's rows are `reports/loco/loco-out-of-fold.csv`, 893 of
         them, committed 2026-09-25 by **#98** (`done`). Caption it with its run date: the seeded
         LOACO run is not reproducible run to run (**#104**).

      **The shape it landed in.** A chart is a *description* before it is an image:
      `hydms/figures/charts.py` builds `Figure` objects and imports no plotting library;
      `render.py` draws one in matplotlib. Every promise above is a construction error in the
      description — a predicted `Series` cannot exist without a band, a quantitative `Axis` cannot
      exist without a unit, a `Panel` refuses a series its axis would clip (so a builder widens the
      axis instead), and `Figure.shared` makes "at the same scale" checked rather than intended.
      Put in the renderer, each would have been a guarantee that runs only where a plotting library
      is installed. matplotlib is a new `figures` extra, already in both lock files, and **CI
      installs it**.
- [x] **#82** `app/main.py` — formula + temperature → capacity. **Done 2026-09-25.** The script ran
      under `Project` through Streamlit's `AppTest` (`tests/delivery/test_app_script.py`, 40 passed
      with `test_app.py`, 0 skipped); Streamlit 1.56.0 is installed and pinned. History below.
      The guarantees are in `hydms/delivery/client.py` (HTTP, stdlib `urllib`) and
      `hydms/delivery/page.py` (what the page shows), tested against uvicorn on a real socket.
      `app/main.py` is a thin Streamlit layer and **has never run**: Streamlit is not in `Project`,
      and an unpinned install would move `starlette` past what `fastapi` 0.115 accepts. That is a
      lock decision for the maintainer. The two API additions **landed 2026-09-24 night**:
      `GET /v1/neighbours` (the k nearest known alloys with every row measured on them — a
      lookup, not a prediction) and `trained_ranges.temperature_support` on `GET /v1/model`
      (training rows per 50 K bin). Both are read from the committed screen references, not the
      artifact, so `v3` serves them unchanged; `openapi.json` and `docs/API.md` are regenerated.
      **The one open box is the Streamlit pin**, then running the script.
- [ ] **#83** `app/pages/` model card. **Must carry two things** or the UI recreates the problem it was
      built to fix: the material-vs-system caveat from PRD §4.4 (comparing a material wt% to a DOE
      system target is a two-step overstatement), and a link to `docs/REPORT-RECONCILIATION.md` so the
      old published figures are not quietly inherited. **Unblocked 2026-09-26** by #105: read the
      run record through `hydms.provenance.read`/`result`, never the CSV, and caption a panel
      with `RunRecord.run_date_text`, which is *not recorded* for both committed runs.
      **Built 2026-09-26, `doing` on two boxes.** `hydms/evidence/reader.py` returns `Score`s
      and the service serves them (`GET /v1/evidence`, `/v1/evidence/parity`, the digest in
      `/v1/health`). `loco --emit` writes `loco-intervals.csv`. The page is
      `app/pages/1_Model_card.py` over `hydms/delivery/modelcard_page.py`. Both carry-overs are
      on it: the material-vs-system caveat and the reconciliation link. Owed: the per-row width
      table, and the one-run-or-spread question, which waits on #104's repeat.
- [x] **#84** Batch CSV screening page. **Done 2026-09-26.** The batched call is in the library:
      `hydms.delivery.predict.predict_many(requests, bundle=)` featurises, predicts and screens a
      whole list once, and `predict_capacity` is its one-row case. A bad formula refuses only its
      own row, because `FeaturisationError.rows` hands the offenders back as data, each with a
      sentence written for that row. Row *i* of a batch equals the lone call to 1e-12, and the
      test includes duplicates. Measured on `v3`, a served row costs **0.7–1.0 ms end to end,
      against 41 ms alone**. `MAX_BATCH_ROWS` was re-set from that measurement, **256 → 4,096**,
      and the response size (1.1 KB a row) is now the binding limit, not time. The page is
      `app/pages/2_Batch_screening.py` over `hydms/delivery/batch.py`, standard library only.
      Every uploaded row comes back, refused and unread rows say so in every number column,
      the summary comes before the download, and the version is on every row. A formula cell
      reading `NaN` is ambiguous (sodium nitride, or pandas' missing value), and the page asks
      which before it asks the model.

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
- [ ] **#100** A render test passes alone and fails after the slow tests. **Still `doing` on
      its traceback box, by the maintainer's ruling of 2026-09-25: it stays open until a session
      fixes the failure.** The failure was seen once, in a local
      full run, and never again. Six full-length runs since are green (the sixth, 2026-09-25: 1650 passed, 1 h 15 m, quiet
      machine), and CI never ran it red:
      run `34716528657` was #97's tie. So no traceback exists and none can be manufactured. What
      was done instead: `hydms/figures/render.py` no longer chooses a backend or imports `pyplot`
      (a subprocess test holds it that way), and the evidence can no longer be lost. **Every
      pytest session that ends red now writes `reports/test-failures/<start>-pid<N>.txt`**
      (gitignored). It holds each failure's traceback and captured output, the other Python
      processes alive at the run's start and end, and the source files modified while it ran.
      `FailureRecorder` in `tests/conftest.py`, six tests in `tests/test_failure_record.py`. A
      next session runs the full suite; a record naming `test_every_figure_renders_in_both_themes`
      is the traceback the fix starts from. Filed by #81,
      2026-09-12; **not an unfreeze condition**.
- [x] **#98** The LOACO run discards its own per-row predictions. Filed by #81, 2026-09-12;
      **not an unfreeze condition**. `hydms/surrogate/train.py:369` writes
      `evaluation.out_of_fold` as a table and `hydms/surrogate/loco.py:595` writes four tables
      without it, so the honest protocol leaves aggregates and the optimistic one leaves 893
      scored rows. The code change is small; the run is the maintainer's. It holds #83's parity
      figure shut. **2026-09-25: `doing`, code landed.** `loco` writes `loco-out-of-fold.csv` as
      a fifth table (outside the four `--emit` reads, so `loco.md` is unchanged) and exits 1
      without it rather than write a partial record. What remains is the run: the command is on
      the card and in `docs/RUNNING-THE-FIT.md` Step 10; the last one took 4 h 07 m. **The four review fixes the maintainer put before the run
      landed 2026-09-25** (stale file deleted on withholding, exit 1 read as four `wrote` lines
      and no traceback, a probe's rows refused via `loco-run.csv`, rows counted per class fold).
      **Done 2026-09-25:** the full run took 288.4 min (budget five hours, not four), wrote 893
      scored rows, and AC-6 passes at macro 0.2559 against 0.7459. **The seeded tables moved**
      (Mg −0.3381 → −0.5084, MEA, SS; macro 0.2734 → 0.2559; seven families identical), and
      that is **#104**. The domain reference, `docs/REFUSALS.md`, `docs/REPORT-RECONCILIATION.md`
      and `docs/API.md` were regenerated from it; no refusal verdict moved.
- [ ] **#104** The seeded LOACO run is not reproducible run to run. Filed by #98, 2026-09-25;
      **not an unfreeze condition**. Mg's search chose a different configuration; MEA and SS
      chose the same one and still scored differently, so both the tuning and the
      fixed-parameter scoring fit vary. AC-1 covers only the deployed fit. **Localised and fixed
      2026-09-26.** Screening off, the pair was identical, and so was a third probe from
      2026-09-25. (These took ~110 min each against that one's 12.3 min: the machine was busy.) Screening on, SS and Mg's objective moved. The cause is `label_issues`'
      `RandomForestRegressor(n_jobs=-1)`: its `predict` sums trees in thread-finishing order, and
      CleanLab's residual ranking turns that last-digit drift into a different drop set. It now
      runs on `n_jobs=1` and refuses a parallel estimator, with three tests. AC-1 still reproduces
      `v3`'s sealed metrics exactly. Owed: a `train --trials 1` pair and the full LOACO rerun.
- [x] **#105** One run record beside every run's tables. Filed 2026-09-26 from the architecture
      review (ADR 0007); **not an unfreeze condition**. **Done 2026-09-26.** `hydms/provenance.py`
      (standard library only) stamps a run **before** the fit (`started_at` with its UTC offset,
      the commit, `code_modified` at start, interpreter, `cpu_count`, CatBoost's thread count,
      `OMP`/`MKL` variables, eight `pkg_*` versions, a `run_id`) and writes one CSV row. `result()`
      is the one answer to "is this a result?": it refuses an absent record, an unreadable one, a
      probe, and a `probe` cell it cannot parse. `train`, `loco`, `evaluate` and `calibrate` write
      records. AC-6, `evaluate`, `loco --emit`, `domain.transfer_table` and the figures test read
      through it, and `tests/test_provenance.py` fails any serving, screening, figure or gate
      module that parses a record itself. **`domain --emit` now refuses a probe's transfer table**
      (exit 2, reference untouched); before, it would have served one. The committed
      `model-run.csv` and `loco-run.csv` were not rewritten: they read *not recorded* until the
      next real run replaces them. **So the next full LOACO run (#104's) is the first that carries
      a run date.**
- [x] **#106** Selection evidence is dated by a file's mtime. Split from #105's last box,
      2026-09-26; **not an unfreeze condition**. **Done 2026-09-26.** `select` stamps before the
      matrix and writes `selection<variant>-run.csv`. Only the default five-fold run writes
      `selection-run.csv`, and `--once`, `--all-features` and `--no-screening` are probes.
      `--emit-comparison` dates from that record, then from a published `provenance.csv`,
      otherwise *not recorded*. `_written_on` (the mtime) is gone. The committed
      `reports/feature_selection/` is untouched, and its byte test passes.
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
- [x] **#37 done 2026-09-24** as [chapter1-revision.md](../chapter1-revision.md), accepted by the
      author. The artifact score (R² 0.7071) and the test
      coverage (0.7795) were committed by **#103** in `reports/model/artifact-score.csv`,
      generated from the sealed gate record (`python -m hydms.evidence.artifact_score --probe
      --emit` after any promotion). **#36 is still `backlog`.**
- [ ] **#36** five ADRs · **#37** Chapter 1 revision. ~~#37 is unblocked on everything but #34.~~
      ~~**#37 waits on #34 *and* #89**~~ (edge added 2026-09-11). **#34 closed 2026-09-12, so #37
      waits on #89 alone, and #36 is unblocked outright.** The #89 edge stands and is the load-
      bearing one: #89's card says the reconciliation is "what card #37 is written from", and
      writing the chapter first would mean re-deriving those eight disagreements by hand, in prose
      nothing checks.
- [ ] Lift the freeze: set `freeze: lifted` in [FREEZE.md](../FREEZE.md), record the closing date, and the
      PA/PB board resumes. **All four conditions hold since 2026-09-24 (#37 `done`), and the
      maintainer is holding the freeze until S7 is finished.** See FREEZE.md §Unfreeze condition.

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
# below was last measured at **1650 passed, 0 failed on 2026-09-25 (1 h 15 min 4 s)** at f427089,
# the #100 check run (1531 in 26 min 45 s on 2026-09-13 before it) — the previous entry here was 1229 in 24 min 58 s on 2026-09-07, which the
# cards since have grown past. The FAST LANE (`-m "not slow"`, which
# deselects the four `@pytest.mark.slow` tests) reported **1440 passed / 4 deselected of 1444
# collected on 2026-09-12 (12 min 3 s)** — up from 1371/1375 the same day by #78's service and
# #79's gate, and from 1308/1312 after #90 on 2026-09-07. That is the figure the recent handoffs
# quote. **Latest: 1583 passed / 4 deselected WITH `--cov` (89.42 %) on 2026-09-24, 53 min 7 s on a
# quiet machine** (only that pytest process running), after #82's app tests and #89's evidence
# tests. **Fast lane on 2026-09-26: 1765 passed, 2 failed, 8 errors, 4 deselected in 52 min 54 s**
# (#83 session, machine shared with the session's own work). All ten were the smoke module
# meeting #104's new refusal. After `smoke.py`'s fix the module passes 19/19; the lane was not
# rerun whole. A handoff that
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
# A RED RUN WRITES ITS OWN RECORD (card #100, 2026-09-25): reports/test-failures/<start>-pid<N>.txt,
# named in the terminal summary. It holds every traceback and captured output, and the two answers
# the paragraph above asks for: the other python.exe processes alive at the start and end, and the
# files modified mid-run. Read it before re-running anything. A green run writes nothing there.
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
curl -s localhost:8000/v1/health   # {"status":"ok","model_version":"v3","max_batch_rows":4096,...}


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
- **Two measured results are published nowhere.** *(The first was published by #103 on 2026-09-24,
  in `reports/model/artifact-score.csv`.)* The deployed model's own held-out score, computed
  by AC-1 as a side effect, and the near-ambient temperature bin's near-zero R² in
  `evaluation-subgroups.csv`. Both are boxed on #83. The pattern is worth naming because this phase
  exists because of it: **a number that only a gate message or an uncommitted file has ever held is
  not published**, and the distance between "measured" and "published" is where REPORT.md went
  wrong in the first place.

---

## FREEZE.md below its deny-list, as it stood 2026-09-26

Moved verbatim when FREEZE.md was compacted. The four unfreeze conditions were not changed; only the evidence and history beside them moved. Links re-pointed only.

### Everything else is allowed

**The table above is the whole of the freeze.** `scripts/check_freeze.py` enforces a *deny*-list
— those five paths — and passes every other path in the repository. This section used to read as
an allow-list (`hydms/** · tests/** · app/** · kanban-hardening/** · scripts/** · .github/** ·
pyproject.toml · CLAUDE.md · README.md · docs/** except the PRD`), which a reader reasonably took
as exhaustive. It was not, and the gap was load-bearing: `environment.lock.yml`,
`environment.yml`, `requirements-lock.txt`, `CONTEXT.md` and `.graphifyignore` are all editable
and none of them was named, so a session reading only this file would have deferred card #1's
lock re-solve forever while a session reading only the script would have concluded this document
meant nothing.

**The deny-list is authoritative, and deliberately so** (decided 2026-09-12, card #72). A freeze
expressed as an allow-list has to be edited every time hardening work reaches a file nobody
listed in advance — which turns the one document that exists to *resist* widening into the most
frequently widened one, and makes each ordinary change an occasion to renegotiate the boundary.
Naming only what is protected inverts that: the five denied paths are the frozen programme and
its archival record, they are the freeze's entire purpose, and they do not grow as the phase
proceeds.

So: **do not add to `DENIED` to express a preference.** It is short on purpose. If a path needs
protecting it needs a reason of the same kind as the five — that it belongs to the frozen
programme or to the published record — not that changing it seems unwise.

### Three cards were pulled out of the freeze

**#44** (screen interface), **#48** (applicability-domain ceiling) and **#49** (ElMD novelty) were
tagged `pa` but are not inverse-design work: they are what lets the interface **refuse** to answer
instead of guessing. A predictor with no domain check is precisely the false-prediction machine this
phase exists to remove. They live in `kanban-hardening/`.

---

## Unfreeze condition

Fixed now, before results are seen, so it cannot be softened later. All four must hold:

- [x] **Every gate green.** HG-1 … HG-4 and the inherited AC-1, AC-2, AC-3, AC-4, AC-6.
      (AC-5 is thermodynamic and AC-7/AC-8 are inverse-design; they stay frozen.)
      **Met 2026-09-12: 9 passed, 0 failed, 3 skipped, 0 errored** — the three skips are exactly
      AC-5, AC-7 and AC-8, the three this bullet excludes in its own parenthesis, and they were
      named as waivers at the prompt rather than counted as passes. The four that must never be
      waived (AC-6, HG-2, HG-3, HG-4) came green with #30, #77, #79 and #86. Re-check with
      `python -m hydms.surrogate.promote --dry-run --waive AC-5 --waive AC-7 --waive AC-8`; it
      is ~3 minutes and fits nothing.
- [x] **An artifact version promoted** — card #34, **done 2026-09-12T17:37:26Z**. A trained
      model, scaler, feature contract and conformal calibration on disk, reachable by manifest
      pointer. *Written as `artifacts/v1` when this condition was fixed; the version to promote
      became **`v2`**, re-saved 2026-09-07 from a clean tree because v1's manifest records
      `code_modified: true` and a manifest is sealed when written. The requirement is unchanged —
      a promoted version — and is named by role here rather than by number so a re-save cannot
      look like a softening.* **What `current` points at is `v3`, and the role is still what is
      met:** a manifest is sealed when written, so the gate report could not be added to `v2`;
      `promote` wrote `v3` carrying the report and moved the pointer, leaving `v2` on disk as the
      record of the fit. `current.json` records the three waivers beside the pointer, which is
      where the decision to proceed lives — the embedded report still says `SKIPPED`.
      **Caveat that belongs here rather than only on the card: `artifacts/` is gitignored.** The
      promoted version exists on the maintainer's machine and nowhere else, so a fresh clone has
      no model and `predict()` refuses there. That is card #7's to fix and it does not reopen this
      bullet, which asks for a promoted version and not for a portable one.
- [x] **`docs/API.md` published** — card #80, **done 2026-09-12**. Every endpoint with a real
      request and a real response, what the interval is and is not, all nine reason codes with
      what a caller should do about each, the trained ranges, and the material-versus-system
      caveat. *It is **generated**, not written:* `python -m hydms.delivery.apidoc --emit`, with
      a test asserting the committed bytes are what the code produces. The examples are real
      exchanges captured against **`v3`** and carry that version on the page, because
      `--probe` needs an artifact and `--emit` must not — the same gitignored-path trap this
      file's own caveat above describes. Card #85's ADR landed with it at
      `docs/adr/0006-the-delivery-seam.md`, which #80's last box required.
- [x] **The Chapter 1 revision written** — card #37: what exists, what was wrong, what it is now.
      **Met 2026-09-24:** [chapter1-revision.md](../chapter1-revision.md), accepted by the author.
      Its last box was closed by #103, which committed the artifact score.

When all four hold: set `freeze: lifted` in this file's frontmatter, record the closing date below,
and the PA/PB board resumes.

**Three of four hold as of 2026-09-12.** The one that remains is the Chapter 1 revision, **#37**.
It waited on **#89**, and #89 closed on 2026-09-24:
[REPORT-RECONCILIATION.md](../REPORT-RECONCILIATION.md) exists, so **#37 is unblocked**. Nothing left
in this condition needs a fit, a decision, or a run of the pipeline.

**#37 was drafted on 2026-09-24** ([chapter1-revision.md](../chapter1-revision.md)), and the bullet
above stays unticked. The card has one box open: three of the draft's numbers (the artifact score
and the test coverage) trace only to the gitignored `artifacts/`, and the card requires every claim
to trace to a report file. The fix needs no fit. It changes neither this condition nor its wording.

> **This list is not a plan, and it is not the measure of Phase H.** It says when the *frozen*
> programme may resume — nothing more. The phase's own objective is stated in §Why above: **a
> user-facing interface that predicts gravimetric capacity.** That is stage **S7** (#81–#84), it is
> not any of the four bullets, and the execution order in
> [PHASE-H-RUNBOOK.md](../PHASE-H-RUNBOOK.md) §2 puts it before S8 in a chain — *"S2 and S3 are the
> only parallelism worth taking. Everything else is a chain."*
>
> So "#89 and #37 are all that is left" is true **of this condition** and false of the phase.
> Reading a short unfreeze list as a to-do list is how the interface this freeze was declared to
> protect gets treated as optional. Ask the runbook what comes next; ask this file only whether the
> other board may reopen.

**All four hold as of 2026-09-24, and the freeze is held anyway, by the maintainer's decision.**
Meeting the condition *permits* lifting; it does not require it. The maintainer chose to keep
`freeze: in-force` until the interface (S7: #82, #83, #84) is finished and the open findings on
the hardening board have been triaged. The reason is the paragraph above: the interface is the
phase's objective, and reopening the inverse-design board now would split the effort. This is
not a new condition. The list above is unchanged and nothing is added to it. When the
maintainer decides to lift, the mechanical act is what the list says.

**Closed:** _(not yet — held by decision, 2026-09-24)_

---

## For the next session

If you are picking this up cold: the freeze is enforced, not remembered. `scripts/check_freeze.py`
runs on every pull request and `scripts/check_board.py` fails if a card under `kanban/` leaves
`backlog`. You do not need to hold this in your head — but you do need to know the freeze exists
before you wonder why your change was rejected.

The active board is [../kanban-hardening/](../../kanban-hardening/). Start there.
