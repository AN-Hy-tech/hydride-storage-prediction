---
id: 24
status: done
priority: High
blocked_by: [14, 20, 88]
assignee: "@amirhossein"
tags: [p1, l3, S1]
---

# Port feature selection, inside the folds, reading CleanLab output

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How the candidate features become the selected set, and the
> guarantee that the rows used to choose them are never the rows used to score them.
>
> *(The "282 candidates" this line used to name were CBFV's `magpie` output, which produces none of
> the 21 published descriptors — `extract_features_cbfv.py:31`, corrected by #8. The real candidate
> set is the feature contract, 21 after the `dev_Gordy_electonegativity` trade below.)*

## Why this exists

**Corrected for Phase H — the five-stage description was wrong.** `REPORT.md` 3.3 describes
VarianceThreshold, a correlation filter at |r| > 0.1, RandomForest importance > 0.005, Boruta, then
SHAP + VIF. This ticket originally repeated that. **It exists in neither selector.** There is no
correlation filter and no 0.005 threshold anywhere in the codebase, and SHAP is computed post-hoc for
reporting, never used as a filter. What actually exists:

- `Boruta_FeatEng.py` — **the live selector**, three stages: `VarianceThreshold(0.001)` with
  `temperature(K)` force-kept, then `BorutaPy` over a depth-6 RandomForest, then iterative VIF at
  threshold 30 protecting the must-keeps.
- `Feature_selection.py` — **dead code**: it reads `data/augmented/`, whose writer was deleted in
  `5c3bcb1`, and writes an output nothing consumes. Six stages, including MI and RFECV.

Port the live selector. Do not port a description.

**Two behavioural changes.** It reads CleanLab's output (ticket 14) rather than the raw splits, closing
the bypass. And it runs **inside the training folds** of ticket 88's protocol, not once over the whole
training set — the archival code fits Boruta and VIF on all 896 training rows and then reports a
cross-validated score over those same rows, so every fold's held-out data helped choose the features
being scored. That is leak **L6**, the PRD's second named leak.

Both changes mean the result may differ from the archived 22, which is the point; ticket 25 records the
difference.

## Done when

- [x] The three live stages ported with thresholds from config, not literals —
      `hydms/surrogate/selection.py`. `SelectionSettings.from_config()` reads every one of them
      out of `pipeline.yaml`; there is no threshold literal in the module
- [x] `temperature(K)` is force-kept through variance and VIF, as in the archival selector.
      `_restore` **appends**, as `:59-61` and `:71-73` do, because the L6 detector compares
      order as well as membership. VIF excludes the must-keeps from the *dropping*, not from
      the computation: `temperature(K)` still inflates the others' factors, exactly as `:88-97`
- [x] Input is CleanLab-screened training data. `select_features` calls
      `hydms.data.screening.label_issues` on its own rows and hands the verdict to `screen`.
      **#14's first box, ticked in this commit** — that is the `Boruta_FeatEng.py:23-25` bypass
- [x] **Selection runs inside the training folds** of ticket 88 — never once over the whole
      training set. `select_across_folds(frame, split)` takes the whole matrix with #13's
      assignment and selects the training rows itself, cuts #88's `grouped_folds`, and hands
      each fold's *training* labels to one `select_features` call. There is deliberately no
      single "the selected features" on the result: `consensus()`, `union()` and `stability()`
      report what the folds agreed about, and collapsing them is #25's decision
- [x] Val and test are untouched at every stage. Structural rather than asserted: the first
      statement of `select_features` is `owned = frame.loc[labels]` and `frame` is not read
      again, so no stage can reach a row the selector does not own however it is later rewritten
- [x] Perturbing test rows leaves the selected feature set identical — the L6 sentinel in
      ticket 71. Tested three ways: perturbed, **deleted entirely** (stronger — it catches a
      stage that computed over the whole frame and then subset), and the leaking twin, which
      must go red on the same fixture
- [x] That **L6 sentinel** is wired to this module — a `live` check in `hydms/qa/sentinels.py`
      calling `hydms.qa.assert_selection_ignores_holdout` on the real selector over the real
      1,278-row frame and the real 893 training labels. **HG-1 is 9/13**; only L1, L5, L11 and
      L12 remain, all owed by #26 and #29
- [x] **The training matrix is assembled by `hydms.data.metadata.with_features`, not by a
      `concat` here (#12).** `hydms.surrogate.select._matrix` does the join; the `temperature(K)`
      agreement check the card describes fires there, and the selector never assembles a matrix
      of its own
- [x] Stage-by-stage feature counts logged for the Chapter 1 revision — `Selection.trace()`,
      one row per stage with `features_in`, `features_out`, `dropped`, `restored` and a
      sentence. A test asserts it is a funnel: each stage starts where the last left off
- [x] The card's own description matches the code that exists, not `REPORT.md` 3.3. The module
      docstring names both selectors, says which is dead and why, and cites the archival line
      numbers for all three stages

- [x] **`avg_is_alkaline` is constant over the training split (from #23) — the premise was
      wrong, and the verdict is the opposite.** A zero inter-quartile span is not constancy.
      The column takes **75 distinct values** over the 893 training rows and its variance is
      **0.0707**, seventy times `selection.variance_threshold`, so `VarianceThreshold(0.001)`
      does **not** drop it — and would not drop it scaled either, since a `FittedScaler`
      substitutes a scale of 1.0 for a zero span and subtracting a median does not change a
      variance. Boruta then **confirms** it, at both the reduced and the configured budget, so
      it is a selected feature rather than a survivor. Recorded as a test on the real rows, not
      as a note: a narrative would not go red if the featuriser ever made the column genuinely
      constant. Related: on the real matrix the variance filter drops **nothing at all** — the
      lowest variance among the 21 is `dev_Covalent_Radius` at 0.0032, still triple the threshold
- [x] **Selection now has a cost to weigh that the old run never faced (from #19) — measured
      both ways, and the answer is drop the feature, keep the rows.** Carrying
      `dev_Gordy_electonegativity` costs **193 of 893 training rows (21.6 %)**, and the loss is
      concentrated exactly where AC-6 scores: AB5 67 of 143 (46.9 %), MIC 37 of 87 (42.5 %),
      against AB2 28 of 260 (10.8 %) and LEA none. Dropping it costs one row — the remaining 21
      cover 1,278 of 1,279, the exception being `Eu1Ni5`. **The controlled comparison** is over
      the 700 training rows where all 22 are computable, same seed, configured budget, only the
      column varying: with it Boruta confirms 13 features including it; without it, 14 — and
      **twelve of the thirteen are the same**. Its absence is taken up by
      `dev_gilmor_number_of_valence_electron` and by `temperature(K)`, which the 22-feature run
      confirms only through the must-keep. So the feature is real — Boruta selects it whenever
      it can — but it displaces rather than adds. A quarter of the training rows against a
      substitutable descriptor is not a close trade. `--all-features` runs the other way for #25

- [x] **What a pass costs, because it decides what may call this.** Measured on the real 893 x 21
      matrix: `label_issues` **14 s**, Boruta at the configured `max_iter` of 2000 **676 s**, the
      VIF loop under a second. `select_across_folds` is therefore an hour and is a **slow-lane**
      run. The L6 live hook cannot pay that twice inside a `Speed.FAST` gate, so it runs the real
      selector under `SENTINEL_BUDGET` — ten Boruta iterations over a fifty-tree forest, screening
      off, everything else configured. What that does and does not cover is written on the
      constant, and `test_the_configured_budget_reproduces_the_reduced_one_on_which_rows_it_reads`
      is the `slow` test that checks the claim at the real budget rather than asserting it

## Runnable check

```bash
# The port itself — fast.
conda run --no-capture-output -n Project python -m pytest tests/surrogate/test_selection.py -q -m "not slow"

# The real run: five outer folds at the configured Boruta budget. About an hour, and it
# writes the per-fold, stability and trace tables card #25 publishes from.
conda run --no-capture-output -n Project python -m hydms.surrogate.select --config hydms/config/pipeline.yaml
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-09-05: Landed, closing #14 in the same commit. `hydms/surrogate/selection.py` (the module the
  L6 sentinel names), `hydms/surrogate/select.py` (the runnable check), `label_issues` in
  `hydms/data/screening.py`, 34 tests. Suite **841** green, ruff and mypy clean, board and freeze OK,
  `run --fast` exits 0 with **HG-1 at 9/13** — L6 wired live. Four things worth keeping.

  **Two of the card's own boxes were wrong about the data, and measuring first is what caught it.**
  The `avg_is_alkaline` box predicted the variance filter would drop it; it does not, because a zero
  IQR is not constancy — the column has 75 distinct values and Boruta confirms it. The Gordy box asked
  for a measurement rather than a guess and got one: the feature is genuinely selected when available,
  which made the trade real rather than vacuous, and the controlled 700-row comparison is what then
  settled it against carrying the feature. Both verdicts are tests or module docstrings, not notes.

  **Boruta costs 676 seconds and that shaped the whole design.** It is why `SelectionSettings` exists
  at all — the L6 live hook has to run the real selector twice inside a FAST gate — and why
  `SENTINEL_BUDGET` is a named constant carrying its own coverage statement rather than a few
  keyword arguments at the call site. The alternative considered and rejected was pointing the
  sentinel at a subsample: that changes what is being checked, where a smaller iteration budget
  changes only how long the same stages run over the same rows.

  **Screening moved inside the folds, and that is a change to #14's shape, not just a call site.**
  A CleanLab verdict fitted over the whole training split would choose each outer fold's training
  rows with that fold's held-out rows in view — L6 one level down. The per-split counts #15 pins
  still come from a pipeline-level `screen` over the whole frame; that call describes the dataset,
  the fold-level one changes a model. **#15 must re-measure `screened.rows_out` and `removed`.**

  **The first real run is done, and the headline is that the feature set is not stable.** Five outer
  folds at the configured budget, ~50 min, tables in `reports/selection/` (gitignored; #25 publishes
  them). **Every one of the 21 candidates is selected by some fold; only 14 are selected by all
  five**, and `range_Atomic_Weight` by exactly one. Two more numbers went to other cards as boxes
  rather than being fixed here: per-fold selection is *larger* than the whole-split run — 16–20
  against 14, because fewer rows make Boruta less able to reject — which means the new N and the old
  22 were not produced under equal statistical power (#25); and CleanLab removes 15 to 144 of a
  fold's ~710 rows depending on the fold, so `outer-1` fits on 571 rows where `outer-2` fits on 704
  (#26).

  **`REPORT.md` 3.3's five-stage selector still does not exist, and now neither does a place to
  believe in it.** The module docstring names both archival selectors, says which is dead and why
  (`Feature_selection.py` reads a directory whose writer was deleted in `5c3bcb1`), and cites the
  line numbers for all three live stages. A future reader who reaches for the five stages will hit
  the correction before the code. (by @assistant)

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-02: Corrected for Phase H. The 'five-stage selection with a correlation filter' this card described is
  from REPORT.md 3.3 and matches neither selector: the live one (`Boruta_FeatEng.py`) has three stages
  and no correlation filter, and `Feature_selection.py` is dead code reading a directory whose writer
  was deleted in 5c3bcb1. Also now blocked on 88, because running selection inside the folds is what
  closes leak L6 (by @assistant)
