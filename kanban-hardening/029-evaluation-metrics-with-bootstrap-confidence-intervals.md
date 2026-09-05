---
id: 29
status: doing
priority: Normal
blocked_by: [28]
assignee: "@amirhossein"
tags: [p1, l3, S6, R4]
---

# Evaluation metrics with bootstrap confidence intervals

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 1 d

> **Owns (hidden behind this module):** How model quality is measured and reported.

## Why this exists

The domain memo 3.3 item 5 warns that at n=239 a test R2 of 0.916 carries a wide interval,
and that a bare point estimate should not be reported.

This module produces every number that goes into the Chapter 1 revision, so it must report
intervals alongside point estimates by default — not as an option.

## Done when

- [x] R2, RMSE, MAE reported on both log and wt% scales
- [x] Bootstrap confidence intervals (2000 resamples) accompany every point metric
- [x] Metrics computed per split and per temperature subgroup — **and "per split" is a
      substitution worth naming.** The out-of-fold reading has only *one* split in it: every row
      of it is a training row, because that is what an out-of-fold prediction is. So the partition
      it is broken down by is the **outer fold** that held each row out. The `val`-and-`test`
      breakdown the phrase also suggests is a property of the **artifact** reading and arrives
      with #34 — it is not silently missing here, it is a different claim about a different object,
      and `subgroup_table`'s docstring says so where somebody reading the code will see it

- [x] **The per-fold table already carries its own row counts, and that is not decoration (from
      #26).** `hydms.surrogate.model` returns `rows_fitted` and `rows_scored` as metrics, so
      `Evaluation.per_fold` and `reports/model/model-per-fold.csv` put the fold sizes in the same
      table as the fold scores. Screening removes between 15 and 144 of a fold's ~710 training
      rows (#24), so part of any fold-to-fold spread is training size and not the model. A
      bootstrap CI over the folds that does not say so is a CI over two different things
- [x] Output is a structured table written to `reports/`, ready for the thesis
- [x] SHAP and PDP are computed on train or a dedicated split, **never on test**. Leak L11:
      `benchmark_model_selection.py:1375,1383,1394` computed both on `X_test`, which makes REPORT §6.1
      a test-set artefact
- [x] **L11 has no sentinel and this card owes one.** Once this card decides what the explainability
      record looks like, add the **L11 sentinel** to `hydms/qa/sentinels.py`: the record names no
      held-out split. Until it exists, HG-1 cannot report green

- [x] **Every reported number must name the feature set it belongs to (from #25).** There are now
      two, and they are not interchangeable: `SELECTED`, the consensus 14 a shipped model is fitted
      on, and the per-fold sets of **16-20** features that #25's five-fold run actually produced.
      A bootstrap interval over folds that each selected their own columns is an interval about a
      *procedure*; one over a fixed 14-column pipeline is about a model. Both are legitimate and
      they are different claims, so the record carries which — and the Chapter 1 revision (#37)
      quotes it from there rather than from a paragraph

- [x] **The bootstrap has no unit to resample until the predictions are kept.** Measured
      2026-09-05, before any code was written. `hydms/surrogate/model.py:_score_fold` computes
      `model.predict(scored)`, hands it straight to `quantile_metrics`, and **discards the
      frame**; nothing in `validation.py` retains a row-level prediction, and
      `Evaluation.per_fold` is one aggregate row per (model, fold). So the only thing
      resamplable today is **five fold scores** — and the box above says that spread is
      confounded with training size. 2000 resamples of five confounded numbers is not the
      interval the domain memo asks for. **The first change this card makes is to keep the
      out-of-fold predictions** `_score_fold` already computes, and hang an out-of-fold table
      off `Evaluation` for `evaluate` to read
- [ ] **The primary number is a bootstrap over the out-of-fold predictions, and it is a claim
      about the *procedure*.** Not five folds. This is the number R4 is about — #26's **probe**
      measured a nested R² of **0.746** wt% against REPORT.md's published **0.892**.
      **0.746 is a probe number**: a reduced-trial cost check whose own run prints `These
      numbers are a cost check, not a result`. No full run has ever been made in this project,
      so it is quoted as a direction, never as this project's honest score
- [x] **`--artifact current` is the *second* reading, and it cannot run yet.** `artifacts/`
      holds only `gate-results.json`: no version directory, no `current.json`, so
      `load_surrogate()` raises `PredictionError: nothing is promoted`. The artifact is #34,
      behind #31/#32/#33. Routing this card's primary number through the artifact would
      serialise the tail of S4 and make #37 wait on all of it; the out-of-fold route needs no
      artifact at all. Once #34 lands, a fixed model scored on held-out rows is a claim about
      **a model** rather than a procedure — a different and equally legitimate number, and the
      record says which, exactly as #25 forced for the feature set
- [x] **Do not spend the session measuring the bootstrap.** 2000 resamples over a few hundred
      rows is milliseconds. The cost in this card is SHAP over a MultiQuantile CatBoost, and
      that is a question for the explainability step, not the metrics step
- [x] **#26's tables are not on disk and cost ~3.5 h to regenerate.** `reports/model/` holds
      only #27's three conformal CSVs, because `/reports/*` is gitignored except
      `feature_selection/`. The `model-per-fold.csv` the fold-size box above builds on comes
      from a real `python -m hydms.surrogate.train` run. **Decided (Q4):** un-ignore
      `reports/model/` the way #25 un-ignored `reports/feature_selection/`, so #37 quotes
      committed tables rather than somebody's local run. The tables themselves arrive with #34's
      real run — see the Q9 box below

### Settled 2026-09-05 by a grilling session

- [x] **The bootstrap resamples canonical groups, never rows (Q2).** `hydms.data.canonical.group_keys`
      is *the seam* — #13 splits on it, #88 folds on it, #87 re-joins on it — and a row-level
      resample would be a fourth meaning of "the same material": leak L8's logic applied to
      intervals instead of splits. **Measured on the real matrix:** the training split is **893
      rows in 780 canonical groups**, group sizes 1–6, and **692 of the 780 are singletons**. So
      the correction is real but **small** — a 13 % reduction in independent units, not a halving.
      Taken on principle, not on magnitude, and the card says so rather than implying a big fix
- [x] **The caveat goes in the table, not in prose (Q5).** The out-of-fold predictions come from
      **five different models** whose training sets overlap, so they are not exchangeable draws
      from one procedure and there is no unbiased estimator of the variance of K-fold CV (Bengio &
      Grandvalet 2004). The interval is therefore **too narrow** — in a chapter whose whole
      argument is that the old numbers were too optimistic. It is a column or header row in the
      emitted table, because prose is what a session drops, as this one did with "probe"
- [x] **Carry the per-fold spread beside it as a second, cruder interval (Q5).**
      `Evaluation.per_fold` already exists so it costs nothing, and two intervals that disagree
      are more honest than one that looks authoritative
- [x] **One resample at the split level; every breakdown computed from it (Q6).** **83 of the 780
      groups span more than one temperature** (up to 6 distinct values), so a resampled group
      carries all its temperature rows with it. Resampling *within* a temperature bin would split
      those groups and break the seam locally. Subgroup *n* therefore varies between replicates —
      record the min and max subgroup *n* across replicates, so a bin that is thin in most of them
      is visible rather than implied
- [x] **Publish the group-versus-row comparison (Q7).** Both computed once, both reported, with
      the statement that the choice is principled rather than numerically forced. The #25
      precedent: publish the comparison that justifies a choice, so no later session re-litigates
      it from a paragraph
- [ ] **~~This card lands machinery, not published numbers (Q9).~~ REVERSED 2026-09-05 — this card
      produces the real numbers (Q12–Q15).** Q9 originally deferred the run to #34; that was
      overturned deliberately, and the reason it was overturned is the reason it must not drift
      back. **If #29 and #34 each run their own 3.5 h fit, the numbers in Chapter 1 describe a
      different model from the one that ships.** So there is **one run**: this card pays for it,
      writes the tables, and #34 promotes the artifact *from that same run*. Cost, measured:
      `cv_folds 5 x inner_cv_folds 3 x optuna_trials 25` = 375 tuning fits + 6 = **381 fits at
      ~33 s = ~3.5 h**
- [x] **Three of #34's boxes have the wrong owner now, because ownership followed the bill (Q13,
      Q14).** #34 justified owning both in its own words — "this card pays the 3.5-hour bill, so it
      owns the fix". The bill moved here, so they move here:
      **(i) the config re-read race.** `hydms.config.load` is uncached and `model._columns` calls
      it through `load_config()` on the whole scoring path — ~6 reads a fit, **~2,300 windows** in
      a 381-fit run in which a working-tree edit changes what the run believes. It has already
      fired once, killing a probe on trial 3, and **two sessions share this worktree**. Fix before
      the run: thread the target column into `ModelSettings` so `_columns` never falls back to
      disk, plus a test asserting `fit_quantile_model` reaches `hydms.config.load` **zero** times.
      A 3.5 h run that reads a half-edited config produces numbers that look fine and are wrong.
      **(ii) narrowing the search space.** The ported space pairs `learning_rate` 1e-4 with
      `iterations` 30,000: **397 s a fit against 7 s**, unconverged at iteration 29,999, and it
      scores *worse* (R² 0.691 vs 0.705). Narrow it — an upper bound on `iterations` or a lower
      bound on `learning_rate` — **before** the run this thesis quotes, with the reason written
      into `tests/surrogate/test_model.py::test_the_search_space_is_the_archival_one`, which is the
      test that must be updated deliberately. Narrowing afterwards would publish a model the
      project then changed, which is the mismatch (i) exists to prevent arriving by another door
- [ ] **Commit the machinery, then run from that commit (Q15).** A table produced from an
      uncommitted tree cannot be tied to the code that made it, and #34's manifest records a git
      SHA. Land and commit steps 1–2 plus the Q13 fix, run from that commit, and **stamp the SHA
      into the emitted tables**. If the run dies at hour three, nothing is lost but the run
- [ ] **The heavy run is the maintainer's to execute, not the agent's (standing rule, 2026-09-05).**
      This card's deliverable is therefore **machinery plus one documented command**, verified end
      to end against a sentinel-budget probe so that the 3.5 h is not spent discovering a crash.
      The card stays `doing` across the gap between the machinery landing and the numbers arriving;
      a box below names what is owed. Do not start a multi-hour fit unasked
- [x] **The explainability record names what it ran on, and the sentinel reads that (Q10).** SHAP
      and PDP run on **the training rows of the deployed fit**. The record carries an explicit
      `computed_on` column, and the L11 sentinel asserts its value is not in
      `hydms.surrogate.validation.HELD_OUT_SPLITS` — the project's single definition of a
      held-out name, asserted against rather than restated, the same one-seam logic as
      `group_keys`. No dedicated explainability split: it costs rows the deployed fit needs and
      buys nothing over training-row SHAP
- [x] **Out-of-fold predictions are a defaulted field on `Evaluation` (Q11).**
      `out_of_fold: pd.DataFrame`, defaulting empty, so every existing construction and both the
      L2 and L4 sentinels are untouched. `Evaluation`'s docstring already calls itself "the
      evidence a later reader checks it with", and this is exactly that evidence. Not a second
      return value from `nested_scores`, which would split one concept across two returns
- [ ] **OWED — the run, and only the run (2026-09-05).** Every box above this one is machinery and
      it is committed and verified end to end at a reduced budget. What is missing is the numbers.
      **Step-by-step operator guide: [../docs/RUNNING-THE-FIT.md](../docs/RUNNING-THE-FIT.md)** —
      the smoke test to run first, what each line of output means, the three exit codes, and how to
      stage the results without committing a probe. The short version, once, by the maintainer:

      ```
      conda run --no-capture-output -n Project python -m hydms.surrogate.train --target capacity
      conda run --no-capture-output -n Project python -m hydms.surrogate.evaluate --emit
      ```

      The first writes **eight** tables into `reports/model/`, which is now versioned; the second reads
      them and writes `evaluation-metrics.csv`, `evaluation-subgroups.csv` and `evaluation.md` in a
      second, stamping the git SHA into the document. Then commit `reports/model/` **by name** —
      never `git add -A` there, since the directory also holds #27's local probe CSVs — and #34
      promotes the artifact **from that same run**. Do not run `train` twice: one run is the whole
      reason this card took the bill off #34.
- [x] **The `(clean tree)` check cannot pass, and the defect is in this card's own emit step
      (found 2026-09-05 22:30, mid-run, by an audit session).** `RUNNING-THE-FIT.md` Step 6 check 2
      says the document must read `- Code: \`<sha>\` (clean tree)`, and Step 1 clears
      `reports/model/` so that it will. **But Step 4 then writes eight CSVs back into that
      directory, and `.gitignore` un-ignores it** (`!/reports/model/`, decided by this card), so by
      the time Step 5 runs, `git status --porcelain` is non-empty again — and
      `hydms.artifacts.manifest.describe_git` computes `dirty` as `bool(status)` over exactly that.
      **Every real run therefore stamps `(working tree dirty)`, and the check an operator is told
      to make is unsatisfiable by construction.** Commit `a101205` saw half of this — untracked
      counts as dirty — and fixed Step 1; it did not notice that the run re-dirties the tree before
      the stamp is read.

      **Not a reason to cancel a run.** `train.py` writes no git stamp at all — only
      `evaluate --emit` does, it fits nothing, and it can be re-run any number of times. The numbers
      are unaffected; what is wrong is the provenance line above them.

      The fix is a naming question before it is a code change: `dirty` currently answers *"did git
      report anything?"* when every caller asks *"can this output be tied to the code that produced
      it?"* — and the knowledge that a run's own results are not code lived only in `.gitignore` and
      in runbook prose, which is what this card already said prose is for losing.

      **Fixed the same session, under `/grill-with-docs`.** Four decisions, in order:
      **(1)** the exclusion lives *inside* `describe_git`, not as an `ignoring=` parameter and not
      as a second stamp computed in `evaluate.py` — a parameter is a decision declined and pushed
      onto every caller, and a second implementation would drift from `hydms.artifacts.store:490`,
      which stamps the same field into #34's manifest. **(2)** The field is **renamed**
      `dirty` → `code_modified`, and the document now reads `(code committed)` /
      `(uncommitted changes to code)`. Keeping the word "tree" while redefining it is the
      back-door leak: a reader who diffs `git status`, sees output and finds the stamp claiming
      otherwise would be right to distrust it. **(3)** `OUTPUT_PATHS = ("reports", "artifacts")`
      is **named, never pattern-matched** — a blanket "looks like output" rule is how a real
      uncommitted source edit eventually gets excused. **(4)** Landed *during* the run rather than
      after, because it touches no fitting code and a document regenerated later would disagree
      with the SHA stamped inside it.

      The exclusion is a git pathspec (`:(exclude,top)`), not Python filtering of porcelain:
      porcelain collapses an untracked directory to one line and spells renames `R old -> new`,
      so re-parsing it here would be a second, worse implementation of something git does exactly.
      `tests/artifacts/test_manifest.py::test_a_run_writing_its_own_output_does_not_report_modified_code`
      builds a real repository, writes into both output directories, and asserts both halves —
      output does not count, **and a genuine source edit still does**.
- [ ] **OWED — `train.py` records no git SHA, so nothing ties the eight tables to the commit that
      produced them.** Found while fixing the box above. `_run()` writes `probe`, `optuna_trials`,
      `screening`, folds, `feature_set`, `features` and `seed` into `model-run.csv` — but not the
      commit. The only SHA anywhere is the one `evaluate --emit` stamps, and that is **`HEAD` when
      the document was generated**, which is not necessarily `HEAD` when the fit ran. Q15 asked to
      "stamp the SHA into the emitted tables" and this is the half that was missed.

      **Not fixable for the 2026-09-05 run, and deliberately not attempted.** Adding a column to
      `_run()` now would change the shape of a table this run is already going to write in the old
      shape, and `read_run` would then be reading one shape from a run that wrote another — a way
      to break the cheap emit step of the very run it was meant to protect. It belongs to #34, or
      to whoever runs the next fit.

      **The caveat for this run, so #37 does not have to reconstruct it:** the fit was launched
      22:03:51 from `a101205`; `evaluate --emit` will stamp a later commit. Checked and recorded
      rather than assumed — `git diff a101205 HEAD` over `hydms/surrogate/{train,model,validation,
      selection,scaler}.py`, `hydms/data/`, `hydms/descriptors/` and `hydms/config/` is **empty**,
      so the later SHA differs only in `evaluate.py`, `manifest.py`, their tests and prose. The
      numbers are what `a101205` produced.
- [ ] **Boxed, not chased (Q8): the canonical count is off by one against a stated invariant.**
      CLAUDE.md says 1,149 formula strings collapse to **1,115** canonical compositions; the
      modelling matrix measures **1,114** groups over 1,278 rows. The populations genuinely differ
      — the matrix carries temperature duplicates the formula-string count does not — so this need
      not be a defect. Nothing currently checks it, which is how a real off-by-one would hide

## Runnable check

```bash
python -m hydms.surrogate.evaluate --artifact current
```

The command as written is the **artifact** reading, and it cannot run until #34 promotes a
version. It was kept rather than re-aimed to make the check green, so it **refuses by name**:
it says the artifact is #34's, that #34 is blocked on this card's run, and that the primary
number needs no artifact and is the same command without the flag. That is what the card
means by "both readings land behind this module".

The reading that works today, once the run has happened:

```bash
python -m hydms.surrogate.evaluate --emit
```

## Traces to

`docs/PRD-inverse-design.md` — S6, R4

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
- 2026-09-05: Opened. Nothing implemented; the session measured the card's own premises first and
  found two of them false. **(a)** The card asks for a 2000-resample bootstrap, but the pipeline
  keeps no row-level predictions to resample — `_score_fold` collapses `model.predict(scored)` into
  a metrics dict and drops the frame — so the only available bootstrap was over five fold scores
  whose spread the card itself warns is confounded with training size. **(b)** The card's runnable
  check names `--artifact current`, and no artifact exists: `artifacts/` holds only
  `gate-results.json`, and the version is #34's, three gates downstream. Taking the check literally
  would have made the primary number wait on #31/#32/#33/#34 and put #37 behind all of it. The
  decision is therefore to keep the out-of-fold predictions and make the row bootstrap over those
  the card's primary reading — a claim about the procedure, needing no artifact — and to keep the
  artifact-scored reading as the second one once #34 lands, labelled as a claim about a model. Both
  findings are boxed above. (by @assistant)
- 2026-09-05: Grilled before implementing. Eleven decisions settled and boxed above under *Settled
  by a grilling session*; three of them corrected something this session had itself got wrong.
  **(a)** The recommendation as first recorded said "~893 training rows resampled" — a row
  bootstrap, which would have been the only place in the project ignoring the `group_keys` seam.
  Corrected to canonical groups, and then *measured*: 780 groups over 893 rows with 692 singletons,
  so the objection is right on principle and worth only 13 % of the independent units. The
  magnitude is recorded because overselling it would be the mirror of the error it fixed.
  **(b)** This session propagated **0.746 without its "probe" qualifier** into the board handoff
  and into a box on this card, promoting a reduced-trial cost check to a result — the anti-pattern
  CLAUDE.md names in its own words. Fixed here, in the handoff, and in the `predict.py` and
  `conformal.py` docstrings, which stated 64.4 % just as flatly. **(c)** The claim that the
  out-of-fold route "decouples #29 from #34 entirely" was too strong: it decouples the code path,
  not the publishable numbers, which still need one real run that #34 pays for. **The verification
  finding behind all of it:** none of this layer's headline numbers — 0.746, 64.4 %, 0.6628,
  +0.030990 — is asserted by any test, and `git ls-files reports/` returns only
  `feature_selection/` while `git ls-files artifacts/` returns nothing. On a fresh clone every
  #26 and #27 number is unverifiable prose. That is what the Q4 and Q9 boxes exist to end.
  (by @assistant)
- 2026-09-05: **Q9 reversed by the maintainer, and four more decisions settled (Q12–Q15).** This
  card produces the real numbers rather than deferring them to #34. The argument that carried it is
  not cost but identity: **two independent 3.5 h runs would mean Chapter 1 reports a different
  model from the one that ships.** So there is one run — this card pays, #34 promotes from it, and
  #34 gained `blocked_by: 29`. Ownership followed the bill, so two of #34's boxes moved here: the
  **config re-read race** (~2,300 windows in a 381-fit run; it has already killed a probe on trial
  3, and two sessions share this worktree) and the **search-space narrowing** (the 1e-4 x 30,000
  corner costs 397 s against 7 s and scores worse). Both must land *before* the run — narrowing
  afterwards would publish a model the project then changed, which is the same mismatch arriving by
  another door. The machinery is committed before the run so its tables carry a SHA. **A standing
  rule was set at the same time: the maintainer executes multi-hour runs, not the agent**, so this
  card's deliverable is machinery plus one documented command, verified against a sentinel-budget
  probe, and the card stays `doing` across the gap until the numbers arrive. Note for whoever
  implements: the earlier Q9 box is struck through rather than deleted, because a reversed decision
  that leaves no trace is one a later session re-reverses. (by @assistant)
- 2026-09-05: **Steps 0–4 implemented in one session; HG-1 is 13/13 and the run is the only thing
  owed.** What landed, and the three things measurement changed.

  **(0) The two boxes that followed the bill from #34.** *The config race* is closed structurally
  rather than carefully: `ModelSettings` now carries the target and temperature **column names**,
  `from_config` resolves them once, and `_resolve` **refuses** rather than falling back to
  `pipeline.yaml` — a fallback that fires only sometimes is the same race with a smaller window and
  a smaller window is harder to find. `tests/surrogate/test_model.py` asserts
  `fit_quantile_model` reaches `hydms.config.load` **zero** times, counted by substituting the
  module's own binding. *The search space* was narrowed on a measurement rather than on #26's note:
  one real fit per learning rate on one real inner fold, everything else held, gave best iterations
  of 813 / 4,230 / 8,501 / 13,991 / **29,999** at 0.005 / 0.001 / 0.0005 / 0.0003 / 0.0001 — the
  last of those *is* the `iterations` cap, so the archival lower bound never converged, exactly as
  #26 reported from a different direction. **R² across that whole decade is 0.6800 to 0.6847:
  flat.** Since `iterations` is sampled from 10,000, the new bound is **5e-4** — the measured rate
  whose optimum still falls inside the smallest budget the space can hand a trial, rather than a
  round number. Nineteen times the wall time for the same model, removed. The full table is on
  `SEARCH_SPACE` and `test_the_search_space_is_the_archival_one_but_for_one_measured_bound` is the
  deliberate update the card asked for.

  **(1) Keeping the predictions needed a seam, not a return value.** `ScoringTask` gained a `keep`
  sink, defaulted to a no-op, and `nested_scores` supplies one per (contender, fold) that **checks
  what arrives against that fold's own held-out labels, in both directions** before keeping it. That
  check is the point: a contender handing back rows it was *fitted* on would look like out-of-fold
  predictions, would score beautifully, and nothing downstream could tell. `Evaluation.out_of_fold`
  is the defaulted field Q11 specified, so both sentinels and every existing construction are
  untouched.

  **(2) A card premise was wrong in the cheap direction.** The card says "the cost in this card is
  SHAP over a MultiQuantile CatBoost". Measured: the booster answers
  `get_feature_importance(type="ShapValues")` **natively** for `MultiQuantile`, returning
  `(rows, heads, features + 1)` — one exact TreeSHAP explanation per head, base value last — in
  **0.02 s** on a 200-tree fit over 708 rows. No `shap` dependency is needed (it is installed and is
  not used), and PDP over eleven quantile points cost 0.01 s a feature. The expensive step of this
  card was the search-space measurement, not the explainability one.

  **(3) A real bug the tests caught rather than a review.** The first `subgroup_table` passed
  *compressed* per-band arrays alongside replicate indices drawn against the **full** array, and
  died with `IndexError: index 30 is out of bounds for axis 0 with size 24`. The fix is the shape
  the design wanted anyway: the draws always index the full arrays and a band is a filter on them,
  with the band's own mask used for the point estimate only. A silent version of that bug — one that
  happened not to overflow — would have published intervals for the wrong rows.

  **Verified end to end twice, and both runs found something.** The whole path at the sentinel
  budget — nested run, out-of-fold table, both interval readings, subgroups, per-fold, deployed
  fit, SHAP, PDP, document — takes **19.6 s** and reproduces the card's own measured numbers
  exactly: **893 out-of-fold rows in 780 canonical groups over 5 folds**, `computed_on` = `train`,
  42 SHAP rows (14 features x 3 heads) and 414 partial-dependence points. The real command at
  `--trials 2` with screening on ran **35 fits in 10.4 min — 17.8 s a fit**, against the **33 s**
  #26 measured under the old space, so the narrowing roughly **halves the run**: 381 fits projects
  to **~1.9 h**, not 3.5. Both are probe numbers and neither is a result.

  **The finding worth keeping: the *cruder* interval is the *tighter* one.** At the sentinel
  budget the three readings of R² wt% came out as groups `[0.6289, 0.7256]` (width 0.097), rows
  `[0.6247, 0.7262]` (0.102) and per-fold `[0.6537, 0.7020]` (**0.048**). So the group correction
  is worth ~5 % of the width — small, exactly as the 13 %-fewer-units measurement predicted — while
  the per-fold interval is **half the width of either**. Q5 expected the two to disagree; it did
  not say which way. A reader who picks the authoritative-looking number picks the *most*
  overconfident one, which is the argument for carrying all three in one table with
  `interval_from` on every row rather than choosing for them.

  **Two smaller things running it found.** `python -m hydms.surrogate.evaluate` warned
  `found in sys.modules after import of package 'hydms.surrogate' ... this may result in
  unpredictable behaviour`: the module was re-exported from `hydms/surrogate/__init__.py` *and*
  is a `-m` entry point, so `-m` executed it twice. `train`, `calibrate` and `select` avoid this
  by being commands only; `evaluate` is both, so the re-export is what gave way, with the reason
  written into `__init__.py` beside the existing note about `SENTINEL_BUDGET`. And on the real
  two-trial tables the **group interval came out slightly *narrower* than the row one**
  (`[0.6860, 0.8019]` against `[0.6769, 0.8012]`), where at the sentinel budget it was slightly
  wider — so at this sample size the difference between the two units is inside Monte-Carlo
  noise. That is the strongest possible form of the card's own "principle, not magnitude"
  framing, and it is why both readings are published rather than one asserted.

  **A defect this session found by running its own output.** The first `--emit` produced a document
  from a two-trial probe that read as a finished result: `train.py` prints
  `These numbers are a cost check, not a result` to stdout, and stdout is not what #37 reads six
  weeks later. A probe's seven tables and a real run's seven tables are **the same shape**. So
  `train.py` now writes an eighth, `model-run.csv`, and `evaluate` leads the document with a
  warning banner unless it says the run was full — defaulting an *absent* record to "unknown"
  rather than to the good case, because that default is how a cost check becomes a thesis number.

  **Green on landing:** fast suite **1004** (was 961), ruff and mypy clean, `check_board.py` and
  `check_freeze.py` OK, gates exit 0 with AC-2 at 2.7285e-12 and **HG-1 `PASSED` 13/13**.

  **What #37 must not do with this card's output.** Every row of `evaluation-metrics.csv` carries
  `reading`, `feature_set` and `interval_caveat` as **columns**, and the caveat is a full sentence
  rather than a code, because a row is what gets quoted into a chapter and a qualifier one row up
  does not travel with it. (by @assistant)
