---
id: 34
status: backlog
priority: High
blocked_by: [29, 31, 32, 33, 77, 79, 86]
assignee: "@amirhossein"
tags: [p1, l3, S1]
---

# Train and publish the deployed artifact version

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** The first promoted artifact version.

**The title said `v1` until 2026-09-11 and that was a trap.** `artifacts/v1` was fitted from a
modified tree — its manifest records `code_modified: true`, and a manifest is sealed when written,
so it can never be cleaned up. **`v2` is the version to promote** (re-saved 2026-09-07 from a clean
tree; same model, same `model-chosen.csv:outer-0` configuration, the five report CSVs byte-identical).
The card is renamed rather than the number corrected in place, because the id is the identity and
`v1` remains on disk as the candidate it always was.

## Why this exists

The moment Architecture A becomes possible. Everything downstream pins this version.

Promotion requires the gates to pass — this ticket is blocked on 31, 32 and 33 for exactly
that reason.

## Done when

- [x] **This card no longer pays for the fit — #29 does, and this card promotes *that* run
      (decided 2026-09-05, #29 Q12).** Two independent 3.5 h runs would mean the numbers in
      Chapter 1 describe a different model from the one that ships, so there is **one run**: #29
      pays for it and writes the tables, this card gates and promotes the artifact from it. Hence
      the new `blocked_by: 29`. **Two boxes below moved to #29 with the bill** — the config
      re-read race and the search-space narrowing — because this card owned them only on the
      stated ground that it "pays the 3.5-hour bill". They are struck through below rather than
      deleted, so the reasoning stays legible

- [x] **SETTLED 2026-09-06 — neither persist nor refit: the deployed fit was the wrong object.**
      The decision below was framed as "how does #34 get a model", and both its options assumed the
      thing to get was `train.py`'s `final_fit`. Measured before choosing: **that fit cannot carry a
      band.** `calibrate.py` carved a calibration slice out of the screened training rows *before*
      fitting and conformalised the model grown on the remainder; `train.py`'s fit had no carve, so
      its 873-row model had no correction that belonged to it while the 701-row model with the
      correction had no explanation. Two models, and the committed `model-shap.csv` and
      `model-pdp.csv` described the one nothing could ship — leak L11's shape arriving by another
      door, exactly as option A's objection feared, but already true and not caused by any refit.

      **So the question dissolved.** `hydms/surrogate/deploy.py` now holds the one definition of the
      deployed fit — screen, carve, fit, calibrate — and `python -m hydms.surrogate.calibrate --save`
      builds and persists it in about two minutes from the `model-chosen.csv` this repository
      already commits. `train.py` builds no deployed fit at all.

      **Option B's 1 h 41 m was measured to buy nothing.** `nested_scores` never touches a deployed
      fit (`--skip-final` already separated the two halves); `evaluate` reads only
      `model-out-of-fold`, `model-per-fold` and `model-run`, never the explainability tables; and
      `git diff a101205 HEAD` over `hydms/surrogate/`, `hydms/data/`, `hydms/descriptors/` and
      `hydms/config/` is empty. A re-run would have reproduced R² 0.7481 and changed nothing else.

      **What this card still owes:** the gate report. `save_deployed` writes the version with
      `gates=None`, which `hydms.artifacts.store.save` documents as the honest state for a model
      nobody has certified — it cannot be promoted and `predict()` refuses it. Turning that into
      `artifacts/v1` with the gates embedded, and pointing `current` at it, is this card and is
      unchanged.

- [ ] ~~**OPEN DECISION — this card's premise is broken: the run persisted no model
      (found 2026-09-05, after the fit).**~~ **SETTLED — see the box above.** Left in full because
      the reasoning that dissolved it is only legible beside the reasoning that framed it. The box above says this card "promotes *that* run".
      `train.py` **saves nothing** — `final_fit` is handed to SHAP and PDP and dropped; the only
      `store` hits in that file are argparse's `store_true`. So there is no model on disk to
      promote, and #31 and #33 need one too.

      **Left open on purpose, for a session that is not the one that just ran the fit.** Options:
      **(A)** refit outer-0's configuration from `model-chosen.csv` — 32.979 s per `model-fits.csv`,
      no second search needed; **(B)** add persistence to `train.py` and re-run, 1 h 41 m, so the
      promoted model is literally the one that made the numbers; **(C)** a hybrid that refits but
      gates promotion on proven equality.

      **What it turns on.** The out-of-fold numbers are safe either way — they came from the five
      outer-fold models, not the deployed fit. **`model-shap.csv` and `model-pdp.csv` are the
      stake**: those were computed on the deployed fit, so a refit that lands elsewhere leaves the
      committed explainability tables describing a model nobody ships — the same class of mismatch
      as leak L11. And the fit is seeded (`random_seed`, the stopping slice, the Optuna sampler)
      but **`model.FIXED` pins no `thread_count`**, while #7's slow lane runs on `windows-latest`.
      See the 2026-09-06 handoff in [README.md](README.md) for the full framing.

- [x] Full pipeline run from `data/raw/` produces `artifacts/v1/` — done 2026-09-06 by `calibrate --target capacity --save`; the version holds `model`, `conformal` and `scaler`, fitted at `5fd9be5` from a modified tree, and carries **no gate report**, which is honest
- [x] **Name the version explicitly when you promote.** `save_deployed` takes the next free `v<N>`,
      and every `--save` writes another one because a version is written once and never edited. So
      `artifacts/` may hold `v1`, `v2`, ... from repeated operator runs and only the manifest says
      which came from which configuration. Read `manifest.json`'s `notes` and `git` fields before
      choosing; a probe run says so in its notes
- [x] Manifest complete: git SHA, seeds, package versions, feature contract, gate results — all six, in the version `promote` writes; the candidate's manifest has the first five and honestly records `gates: null`
- [x] All Phase 1 gates pass and are recorded in the manifest. ~~**5 of 12 pass, 7 are
      unwritten**~~ — **measured 2026-09-12 by `promote --dry-run` against `v2`: 9 passed,
      0 failed, 3 skipped, 0 errored in 194.48 s.** The three skips are AC-5 (#41, Phase T),
      AC-7 (#57) and AC-8 (#56, Phase A) — every one of them frozen, and the exact three this
      card settled as `--waive`. **The four the runbook says must never be waived are all green**:
      AC-6, HG-2, HG-3 and HG-4, whose owing cards #30, #77, #79 and #86 have since closed. This
      is the first time every reachable criterion has been green at once.

      | Gate | Measured | Threshold | Card |
      |---|---|---|---|
      | AC-1 | 0 | 0 | #32 |
      | AC-2 | 2.72848e-12 | 1e-09 | #21 |
      | AC-3 | coverage 0.779528 | nominal 0.8, tolerance 0.05 | #31 |
      | AC-4 | 0 | 1e-12 | #33 |
      | AC-6 | LOCO R² 0.2734 vs random-split 0.7459 | both reported | #30 |
      | HG-1 | 13/13 leaks guarded | 13/13 | #71 |
      | HG-2 | 9/9 codes, 0 bare numbers | 9/9, 0 | #77 |
      | HG-3 | 0 differences over 11 probes, 8 rejections | every served value equal | #79 |
      | HG-4 | ruff clean, mypy clean, coverage 89.66 % | 80 % | #86 |

      Detail worth keeping from the run: AC-1's two fits agree on **every** metric — crossings
      0.000000, coverage 0.779528, width 0.862991, mae 0.311710, pinball 0.106554, r² 0.707064,
      rmse 0.542028 — at thread counts 1 and 20, with conformal correction **+0.037355**, 2584
      trees, best iteration 2583, grown on 701 rows with 172 carved for calibration. AC-3's raw
      coverage is **0.6575** against the calibrated 0.7795, which is the gap #27 exists to close,
      measured on rows nothing was fitted or calibrated on. HG-4's 89.66 % is the *local* figure;
      CI reports 88.77 % because nine tests skip there

- [ ] ~~**The full run is about 3.5 hours and the reason is one corner of the search space (from
      #26).**~~ **MOVED TO #29 (2026-09-05)** — the narrowing decision follows the bill, and #29
      now pays it. Narrowing must happen *before* the run Chapter 1 quotes, otherwise this card
      improves a model the thesis has already reported. Left here for its measurements:
      Measured: 33 s a fit on this machine, and the configured budget is
      `cv_folds` x `inner_cv_folds` x `optuna_trials` = 5 x 3 x 25 = 375 tuning fits plus six
      more. `optuna_trials` came down from the archival 300 — which would be 42 h — and the
      nesting was not touched. **Where the hours are**: the ported space pairs `learning_rate`
      down to 1e-4 with `iterations` up to 30,000, and at that corner one fit costs 397 s against
      7 s at the fast one, has not converged at iteration 29,999, and scores *worse* (R² 0.691
      against 0.705). #26 ported the space rather than narrowing it, because its instruction was
      to lower the trial count. **Narrowing it is a modelling decision and it belongs to this
      card**, which is the one that has to pay the bill: a lower bound on `learning_rate`, or an
      upper bound on `iterations`, would buy back most of the wall time for a model that is not
      worse. If it is narrowed, `tests/surrogate/test_model.py::test_the_search_space_is_the_archival_one`
      is what has to be updated, deliberately and with the reason in it
- [x] **The deployed configuration is chosen on an inner-fold number (from #26).** Kept, and the reading now lives in one place: `hydms.surrogate.deploy.deployed_params` moved out of `calibrate` when gate AC-1 needed the same answer, because *which configuration the deployed fit is fitted at* is part of the definition of the deployed fit and a second reader in the gate would be exactly the drift `deploy.py` was created to end. It still takes the `objective` minimum, still an inner-fold number, still never an outer score.
      `hydms.surrogate.train._deployed` takes the configuration whose own search achieved the best
      inner-fold pinball loss. The outer scores — the ones a run reports — take no part in it,
      which is what keeps picking a configuration from being leak L2 in a new place. Keep that
      property if this card chooses differently
- [x] **The version carries a conformal correction, and it is a number (from #27).** The payload
      key is `hydms.surrogate.conformal.CONFORMAL_PAYLOAD` and the value is a `FittedConformal`,
      read back with `conformal_from(bundle)` exactly as the scaler is with `scaler_from`. Two
      things this card owns and #27 could not: the calibration slice must be carved **before** the
      deployed fit — `calibration_slice(frame, kept.kept)` over the screened training rows, then
      `fit_quantile_model(train=fitting, eval_on=val, scored_on=test)`, which is what
      `hydms.surrogate.calibrate` does and what `final_fit` does *not* — and the row asymmetry must
      be published beside the score: at `calibration_folds: 5` the deployed model grows on ~701
      rows where the cross-validation that estimated its performance fitted on folds cut from ~893.
      **Never store a pickled MAPIE object**; `conformal_from` refuses one and says why.
      **Both halves of this box are now done, 2026-09-06** — `hydms.surrogate.deploy.deployed_fit`
      carves before it fits, and `deploy.rows_table` publishes the asymmetry into
      `conformal-rows.csv` beside the score. What is left here is the manifest, not the modelling
- [ ] ~~**A run re-reads `pipeline.yaml` from disk while it is running, so an edit lands
      mid-flight (measured 2026-09-05).**~~ **MOVED TO #29 (2026-09-05)**, by this box's own
      rule — "this card pays the 3.5-hour bill, so it owns the fix" — now that #29 pays it. It
      must land *before* #29's run. Left here in full, because the measurements are this card's: `hydms.config.load` is uncached and re-parses the file on
      every call, and `hydms.surrogate.model._columns` calls it through `load_config()` whenever
      `target_column` is `None` — which is the whole scoring path. Counted under `sentinel_settings()`:
      **210 reads in one nested run** of ~35 fits, so about six a fit, at **7.6 ms each**; the
      configured 381-fit run is therefore roughly **2,300 windows** in which a working-tree edit
      changes what the run believes. It has already fired once: a `--trials 8` probe died on trial 3
      with `unknown key(s) ['calibration_folds']` because #27 wrote the new YAML into the shared
      worktree after the process had imported the old `Model` dataclass. **This card pays the
      3.5-hour bill, so it owns the fix**: thread the target column into `ModelSettings` so
      `_columns` never falls back to disk, and record the config the run actually used in the
      manifest beside the git SHA and the seeds — `artifacts/store.py` records `load_config().seed`
      today and nothing else about the file. A guard in the project's grain is a test asserting that
      `fit_quantile_model` reaches `hydms.config.load` zero times
- [x] **Nothing records which commit a fit ran from, and this card owns the manifest that
      should (from #29, 2026-09-05).** `train.py`'s `_run()` writes trials, folds, seed and
      feature set into `model-run.csv` — but not the SHA. The only SHA anywhere is the one
      `evaluate --emit` stamps, which is `HEAD` **when the document was generated**, not when the
      fit ran. #29 found this while fixing the clean-tree stamp and deliberately did not patch it
      mid-run: adding a column would have changed the shape of a table the running fit was already
      going to write in the old shape, and `read_run` would have been reading one shape from a run
      that wrote another.

      **It has already bitten once, harmlessly, and the record exists so nobody re-derives it:**
      the 2026-09-05 run fitted from `a101205` and its document stamps `5f696d9`, because the
      stamp defect was fixed while the fit was running. `git diff a101205 5f696d9` over
      `hydms/surrogate/{train,model,validation,selection,scaler}.py`, `hydms/data/`,
      `hydms/descriptors/` and `hydms/config/` is **empty** — no fitting code moved. This card's
      manifest must record the run's own SHA rather than promotion-time `HEAD`, or the next
      occurrence will not be harmless.

      **Closed 2026-09-06, and by the candidate's manifest rather than by the promoted one.**
      `save_deployed` calls `artifacts.save` at the *end of the fit*, so `describe_git` stamps the
      commit the fit ran from — `artifacts/v1` records `5fd9be5`, `code_modified: true`, and
      `2026-09-05T21:57:01+00:00`. The version `promote` writes later is stamped at promotion time,
      which is the defect this box names, so **it does not rely on its own git block**: its `notes`
      carry the candidate's SHA, its modified-tree flag and its creation time verbatim, and the
      candidate stays on disk with its own manifest. Two hops from a promoted model back to the
      commit that fitted it, and neither is inferred.

- [x] **The gate report exists and is embedded by a command, not by hand:
      `python -m hydms.surrogate.promote` (landed 2026-09-06).** It reads a candidate version with
      `require_gates=False`, runs the whole registry against it, and — only if every criterion
      passed — writes a **new** version carrying the same payloads plus the report and points
      `current` at it. It fits nothing: the model comes from `calibrate --save`, two minutes.
      `--dry-run` runs the gates and writes nothing. Exit 0 certified, 1 unestablished, 2 bad
      invocation. A refusal writes no version and moves no pointer, which
      `tests/surrogate/test_promote.py` asserts on the directory listing rather than on the exit
      code — an exit code is what a script reads, the directory is what the next run inherits.

      **Why a second version and not an edit to `v1`:** a manifest is sealed when it is written, so
      the report of a run *against* `v1` cannot go into `v1`. That is option (C) from card #33's
      list, and its stated cost — two directories for one model — is paid here, where it belongs,
      rather than in the gates.

- [x] ~~**OPEN DECISION — `artifacts/v1` cannot be promoted during Phase H, and the reason is the
      store's own guarantee working correctly (found 2026-09-06).**~~ **SETTLED 2026-09-06, and
      none of the three shapes it offered was taken.** The framing is kept in full below because
      the answer is only legible against it. `hydms.artifacts.promote` refuses a version whose
      manifest records any criterion that did not `PASS`, and `Manifest.unestablished()` counts
      `SKIPPED` — deliberately, because a manifest saying "AC-6 was not checked" is exactly as
      much evidence as one saying "AC-6 failed". Measured by
      `python -m hydms.surrogate.promote --dry-run`: **5 passed, 7 skipped.**

      | Skipped | Card | Why it cannot be written in this phase |
      |---|---|---|
      | AC-5 | #41 | frozen with Phase T — there is no entropy model in Phase H |
      | AC-7 | #57 | frozen with Phase A — this phase publishes no candidate list |
      | AC-8 | #56 | frozen with Phase A — this phase runs no search |
      | AC-6 | #30 | **landable** — leave-one-alloy-class-out, unblocked and independent |
      | HG-2 | #77 | **landable** — needs #76, which is S6 |
      | HG-3 | #79 | **landable** — needs #78, which is S6 |
      | HG-4 | #86 | **landable** — S8 |

      Three shapes were offered: **(i)** a phase-scoped subset computed at promotion time,
      **(ii)** a fourth gate status `NOT APPLICABLE`, **(iii)** nothing changes and the delivery
      layer loads with `require_gates=False`.

      **What was implemented is narrower than any of them: a waiver is an act, not a property.**
      `promote(version, waive={name: reason})` names criteria one at a time, never by pattern,
      and writes them into `current.json` — the promotion pointer, which is where the decision
      to ship anyway belongs. `load()` honours a waiver **only for the version the pointer
      actually names**, so it cannot be inherited by an artifact nobody promoted under it, and
      it dies the moment the pointer moves. Four refusals hold it shut: a criterion that
      **FAILED** can never be waived (a waiver says "this was not checked and here is why"; it
      can never say "this was checked and did not hold"); a criterion that **PASSED** cannot be
      waived either, because a no-op entry rots the list into decoration; a **name the report
      does not record** is an error rather than a silent narrowing; and an **empty reason** is
      refused, because the reason is what makes it revisitable.

      **Why not (i).** It makes "in scope" something a session derives at promotion time, and a
      derived scope widens quietly. **Why not (ii)** — the one the gate harness makes cheapest,
      and therefore the one examined hardest. It moves the judgement inside the criterion, where
      it is invisible at the moment of promotion and one edit from being applied to a criterion
      that *is* applicable; worse, it corrupts the manifest, whose embedded report would stop
      being a record of what was measured. **Why not (iii).** `require_gates=False` in the
      delivery path erases the store's guarantee in one keyword that no artifact records. (The
      framing above also said (iii) defeats "the thing gate HG-2 exists to prevent" — that is
      **wrong** and is corrected here: HG-2 is the refusal path, that a result cannot be a bare
      number without an interval and a domain verdict. What (iii) defeats is
      `load(require_gates=True)`, which is `store.py`'s guarantee, not HG-2's.)

      **The manifest never learns about waivers, and that is the property the design turns on.**
      `Manifest.unestablished()` is unchanged, the promoted version's embedded report still
      records AC-5/AC-7/AC-8 as `SKIPPED`, and `hydms/gates/` is untouched. The artifact's
      account of what was *measured* is exactly as truthful after a waiver as before it.

      **What stops "out of scope" becoming "not done yet".** Not `scripts/check_board.py`:
      `artifacts/` is gitignored, so a rule written against a committed `current.json` would
      never see one — a guarantee nothing checks. `tests/artifacts/test_waiver_scope.py` instead
      **derives** the waivable set from the repository: every registered gate names its card,
      every card lives in exactly one board directory, and a criterion is out of this phase's
      reach if and only if its card is on the frozen board. Today that derivation yields exactly
      `{AC-5, AC-7, AC-8}` and the test pins it, so a card crossing between boards goes red and
      forces the question to be asked out loud.

      **This does not finish this card, and the measurement says exactly how far it gets.**
      `promote --dry-run --waive AC-5 --waive AC-7 --waive AC-8` against `artifacts/v1`, 210.9 s,
      now refuses with **4 of 12 unestablished — AC-6 (#30), HG-2 (#77), HG-3 (#79), HG-4
      (#86)** — down from 7, and every one of the four is Phase H's own work. What the decision
      buys is that the remaining work is now *sufficient*: before it, no amount of Phase H work
      could promote anything.

- [ ] `current` points at a certified version — **no longer blocked by a decision; blocked by
      work, which is the right kind of blocked.** The decision landed, so the command that
      finishes this card now exists and is:

      ```bash
      python -m hydms.surrogate.promote --waive AC-5 --waive AC-7 --waive AC-8
      ```

      It still refuses today, and correctly: AC-6, HG-2, HG-3 and HG-4 are skipped and every one
      of them is Phase H's to land (#30, then S6's #76–#79, then S8's #86). Run it with
      `--dry-run` after each of those closes to see the list shrink. Do **not** add any of those
      four to the waiver list — `tests/artifacts/test_waiver_scope.py` is the check that says
      why, and the command prints each waiver's owning card so the board it belongs to is
      visible at the prompt

- [ ] **The waiver summary counts wrong, and no test asserts the string** (found 2026-09-06 by
      running `promote --dry-run --waive AC-5 --waive AC-7 --waive AC-8` against `artifacts/v1`).
      `hydms/surrogate/promote.py` prints

      ```python
      f"{candidate} therefore has {len(report.results) - len(requested)} of "
      f"{len(report.results)} criteria left to establish. …"
      ```

      which is `12 - 3 = 9`. It subtracts the waivers from the **total** number of criteria rather
      than from the unestablished ones, so it ignores the five that have *passed*. The correct
      figure is `len(outstanding)` = **4** — AC-6, HG-2, HG-3, HG-4 — which the very next block
      prints correctly to stderr as "4 of 12 criteria are unestablished". One command, one run, six
      lines apart, two answers to the same question. This card's own narrative records the correct
      one, which is how the drift was caught. Fix the expression and assert the sentence: the
      project's own rule is that no number appears in prose that a test does not check

- [x] **DONE 2026-09-07 — `artifacts/v2` is the deployed fit with a clean provenance line.**
      `artifacts/v1`'s manifest records `git.code_modified: true` — honestly, because a concurrent
      session had uncommitted gate work in this shared checkout when `calibrate --save` ran.
      Nothing blocked a promotion on it and `promote` records "*from a modified tree*" in the
      pointer note rather than refusing, which is the right behaviour. But the note is permanent,
      so the fit was re-saved from the clean tree at `4a06011`:
      `calibrate --target capacity --save`, 0.7 min. **v2 records `code_modified: false`** and is
      the same model: correction **+0.037355**, identical to AC-1's, from the same
      `model-chosen.csv:outer-0` configuration, 172 calibration rows carved from 873 screened,
      701 grown on. **Promote v2, not v1.** v1 stays on disk — a version is written once and
      never edited, so the dirty one is not deleted, it is superseded

- [x] **The re-save doubled as a stronger reproducibility check than AC-1 runs.** AC-1 compares
      two fits on their *metrics table*; this run's five regenerated CSVs — `conformal.csv`,
      `conformal-coverage.csv`, `conformal-rows.csv`, `model-shap.csv`, `model-pdp.csv` — were
      diffed against the committed #29 tables and are **byte-identical**, SHAP and
      partial-dependence included. So the committed evidence behind Chapter 1 is reproducible at
      the file level from a clean checkout, not merely at the metric level

- [ ] **`--report` is both the output directory and where the deployed configuration is read
      from, and that is a trap** (found 2026-09-07, in review). Pointing `--report` at a scratch
      directory to avoid overwriting the committed tables makes `deploy.py:163` look for
      `model-chosen.csv` *there*, not find it, and fall back to **CatBoost's own defaults** — a
      smoke-test fit that `--save` then persists with the note `deployed fit`. It happened here:
      the first re-save produced a correction of **+0.030990** instead of +0.037355 and was
      discarded. The command *says* so on stdout ("so this fit uses CatBoost's own defaults …
      That is a smoke test of the calibration path, not the deployed band"), which is how it was
      caught within a minute, and the manifest's `notes` field is the wrong place to catch it
      because it only distinguishes `--no-screening`. Two candidate fixes, neither taken here
      because both belong to the seam rather than to this card: give the chosen-configuration
      read its own flag so an output redirect cannot move it, or refuse `--save` outright when
      the configuration fell back to defaults, on the same reasoning that makes a probe's
      artifact carry a note — **an artifact that does not say it came from a default is an
      artifact somebody will promote**

- [ ] **The next version's payload set drops `SCALER_PAYLOAD`** (decided 2026-09-12 on #23,
      boxed here because this card writes the next version). `DeployedFit.payloads` in
      `hydms/surrogate/deploy.py` names three keys under the rule that each is "declared by the
      module that reads it back, so this mapping cannot name a key nothing loads".
      `SCALER_PAYLOAD` breaks that rule: `scaler_from` has no production call site, because #26
      fits on raw features and #48 landed as a capacity ceiling reading no scaled matrix. #23
      weighed keeping it as insurance against a future refit-on-candidates and rejected that —
      the insurance only pays for a consumer that scales, and #48 measured that the distance
      consumer is not coming back.

      Three things this touches, none of them optional:

      - `DeployedFit.payloads` stops emitting the key, and `DeployedFit.scaler` stops being
        fitted for persistence. `fit_scaler`, `FittedScaler` and `scaler_from` all **stay** —
        `TRAIN` is imported by `hydms.screens.domain`, `selection.py` fits one in the moment for
        VIF, and the refuse-on-`fit` behaviour is what makes "never refit" enforceable if a
        consumer ever does appear.
      - `tests/artifacts/` and the manifest name the payload; both have to stop expecting it for
        a version written after this change, while still reading `v1`/`v2`, which keep it. A
        version is sealed when written — this is a change to the *next* contract, never a
        rewrite of a sealed one.
      - `CONTEXT.md`'s **Artifact version** entry reads "a model, its correction, its scaler and
        a manifest". Nothing tests that file, so it changes here or it stays wrong.

      Not an unfreeze condition.

## Runnable check

```bash
python -m hydms.pipeline run --promote && python -m hydms.gates run --all
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-09-06: The three blocking gates landed (#31, #32, #33) and this card's mechanism with them,
  and then the card met a wall that is not a bug: `promote` requires every registered criterion to
  have passed, and three of them belong to frozen phases. The interesting part is that the wall was
  invisible until a command actually tried to walk into it — the rule has been in
  `hydms/artifacts/store.py` since #4 and reads as obviously correct, and nothing before today ever
  asked it to certify anything. Recorded as an OPEN decision rather than solved, because the fix
  touches the store's central guarantee and the cheapest fix from inside the gate harness is
  probably the wrong one. (by @assistant)

- 2026-09-05: A `--trials 8` probe run died on trial 3 with `ConfigError: pipeline.yaml:model: unknown key(s) ['calibration_folds']`, and nothing was wrong with the code at any commit: the process had imported the pre-#27 `Model` dataclass and then re-read a post-#27 `pipeline.yaml` off the shared worktree. The interesting part is not the race but what it exposed — a run is not hermetic against its own configuration file. Measured while diagnosing it: one `load()` is 7.6 ms and a sentinel-budget nested run makes 210 of them, 21.6% of that run's wall time. At the configured budget that is ~2,300 re-reads spread over 3.5 hours. Recorded as a box above rather than fixed in place, because the fix changes what a published run records about itself and that is this card's subject. (by @assistant)
- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-06: **The wall came down, and the answer was none of the three shapes the card
  offered.** The framing set up a choice between a phase-scoped subset, a fourth gate status, and
  doing nothing — and all three share a premise worth naming: that the fix belongs either to the
  *criterion* (what it reports) or to the *rule* (what promotion demands). It belongs to neither.
  It belongs to the **act**. A promotion is already a recorded, dated, one-line decision written
  into `current.json`; the only thing missing was that it could not say what it was proceeding
  without.

  So `promote(version, waive={name: reason})` records that, and every constraint on it follows
  from asking what a waiver is allowed to *mean*. It may say a criterion was not checked — so a
  `FAILED` one is refused, and that single line is what separates this from
  `require_gates=False`. It must be revisitable — so an empty reason is refused, and the reason
  recorded is the gate's own skip message rather than prose typed at a prompt, because a
  `Pending` gate's `reason=` field is reviewed code and a command-line string is not. It must not
  rot — so waiving something that passed, or a name the report does not carry, is an error rather
  than a no-op. And it must not outlive the decision — so `load()` honours it only for the
  version the pointer actually names.

  **`hydms/gates/` and `Manifest` are untouched, and that was the target rather than a
  side-effect.** The handoff warned that a session fresh out of the gate harness would reach for
  the change that is cheapest there, and it was right about which change that is: a fourth status
  is about fifteen lines. It is also the one change that makes the manifest lie — the embedded
  report would stop being a record of what was measured, which is the exact property
  `manifest.py`'s docstring spends four paragraphs defending. The promoted version's report still
  says AC-5 was skipped. Someone reading the artifact learns what was measured; someone reading
  the pointer learns what was decided; neither file has to be read in light of the other.

  **One thing in the card's own framing was wrong and is corrected there:** option (iii) was said
  to defeat "the thing gate HG-2 exists to prevent". HG-2 is the refusal path — never a bare
  number. What (iii) defeats is `load(require_gates=True)`, which is the store's guarantee.
  Getting that wrong made (iii) look worse than it is; it is still rejected, but for the reason
  that actually applies.

  **Where the guard went, and why not where the first draft put it.** The obvious home for "is
  this waiver legitimate?" is `scripts/check_board.py`, which already reads both boards — and it
  was written there first, before `git ls-files artifacts/` returned nothing. `artifacts/` is
  gitignored, so a rule about a *committed* `current.json` would never once fire in CI: an
  unchecked guarantee dressed as a check. It moved to `tests/artifacts/test_waiver_scope.py`,
  which derives the waivable set instead of listing it — each gate's `card`, each card's board
  directory, and a pinned expectation of the result. Today that is exactly `{AC-5, AC-7, AC-8}`.
  A card crossing between boards turns it red, which is the only moment anyone would think to ask
  the question again.

  **This card is still open, and is now blocked by work rather than by a decision.** Waiving the
  three frozen criteria leaves AC-6, HG-2, HG-3 and HG-4 — #30, S6, S8 — every one of them Phase
  H's own. That is the honest outcome: the decision made the remaining work *sufficient*, where
  before it was not. (by @assistant)

- **The three gates this card waits on are now `blocked_by` edges, and the status went back to
  `backlog` (2026-09-11).** Everything above was already written down — the skipped-gate table in
  *Done when* names #77, #79 and #86 by id, and the runbook says three times that promotion needs
  HG-2, HG-3 and HG-4 — but the board's `blocked_by` recorded none of them, so
  `list_all_cards.sh` showed a card in `doing` with every declared blocker `done`: the one reading
  of the board that says "this is ready to close". It was not. HG-2 landed with #77; HG-3 and HG-4
  do not exist.

  **Why `backlog` and not `doing`.** `scripts/check_board.py` refuses `doing` *or* `done` while a
  blocker is unfinished, so the edge and the status could not both stay. `backlog` is the repo's
  own precedent for this shape — #15 was written green and held in `backlog` until #14 landed —
  and it is the truthful one: no work on this card can proceed until #79 and #86 build the gates
  `promote` will demand. The work that *has* landed is not lost; it is every ticked box above and
  the whole of this Narrative. **This is bookkeeping, not a reversal** — `python -m
  hydms.surrogate.promote` exists and works, and `v2` is the version it will be pointed at.
  (by @assistant)

- 2026-09-12: **An unmerged pull request answering this card's open decision was found and closed
  without merging.** PR #7 (`claude/persist-vs-refit-resolved-dk4iss`, opened 2026-09-05 21:15,
  two commits) recorded the persist-vs-refit question as *"resolved in favour of persist"* and
  wrote that conclusion onto six cards. It was opened the same evening the OPEN DECISION below was
  framed, and the session that settled it the next day never saw it — it targets `main`, which the
  Phase H branch has not merged into since 2026-08-30.

  **Nothing was ported, and that is the correct outcome rather than a loss.** Its answer is one
  side of the decision the box above dissolved: the deployed fit was the wrong object, so the
  question was not persist-or-refit at all. This card already keeps that framing in full, beside
  the measurement that ended it, for exactly the reason it gives. Porting the PR's text would have
  re-asserted a settled question's losing frame as though it were current.

  Worth recording *how* this nearly went the other way. The first check was
  `grep persist-vs-refit kanban-hardening/`, which found nothing and looked like proof the content
  had been dropped when the cards moved off the frozen board. It was proof of the opposite: the
  successor decision is on this card under different words, and on #36 as ADR candidate 7, *"one
  definition of the deployed fit"*. **A grep for the old vocabulary cannot find a question that was
  renamed by being answered.** See [[an-inherited-decision-can-dissolve]].
  (by @assistant)

- 2026-09-12: **The gate run is green and this card is one command from done.**
  `promote --dry-run` against `v2` (fitted at `4a06011`, 2026-09-06T21:31:41Z, `code_modified:
  false`, catboost 1.2.8 under the pinned environment) returns **9 passed, 0 failed, 3 skipped**
  in 194 s. It then refuses, correctly and by design: *"v2 is NOT promotable: 3 of 12 criteria are
  unestablished — AC-5 SKIPPED (card #41), AC-7 SKIPPED (card #57), AC-8 SKIPPED (card #56).
  A SKIPPED gate is a criterion nobody checked, and `hydms.artifacts.promote` refuses it for the
  same reason it refuses a failure. Nothing was written and the promotion pointer did not move."*

  **No fit is owed.** The heavy run this card was long assumed to need was already paid: Step 4's
  1 h 41 m produced `model-chosen.csv`, which is committed, and `reports/model/` carries its
  numbers; `artifacts/v2` is the deployed fit built from that configuration in about two minutes.
  `docs/RUNNING-THE-FIT.md` Step 9.5 says outright that promotion *"fits nothing"* apart from
  AC-1's two fits, which are the bulk of those 194 seconds. What remains is
  `promote --waive AC-5 --waive AC-7 --waive AC-8`, the path this card itself settled, which
  writes a new sealed version carrying the report and points `current` at it.

  Recorded here rather than executed: the promotion is the unfreeze condition's second bullet and
  writes the pointer three screens read, so it is the maintainer's to run. See
  [[the-maintainer-runs-the-heavy-fits]] — the rule is about *consequence*, not wall time, and a
  three-minute command that certifies an artifact is squarely inside it. (by @assistant)
