---
id: 7
status: doing
priority: P2
blocked_by: [4, 6]
assignee: "@amirhossein"
tags: [p0, l0, S1]
---

# CI slow lane: full retrain, artifact upload and version promotion

**No stage — slots in where its blockers allow** · **L0 Foundation** · Estimate: 1 d

> **Owns (hidden behind this module):** How a new artifact version is produced and promoted.

## Why this exists

Retraining is expensive, so it is manually dispatched and scheduled weekly rather than run
per push. This is the promotion path: a full run produces `v{N+1}`, the gates run against
it, and it is promoted only on a full pass.

**Rollback:** promotion is a manifest pointer, so reverting to the previous version is a
one-line change, not a retrain.

## Done when

- [ ] `.github/workflows/retrain.yml` on `workflow_dispatch` and a weekly schedule
- [ ] Runs the full pipeline end-to-end from `data/raw/`
- [ ] Uploads `artifacts/v{N}/` as a workflow artifact
- [ ] `hydms.gates run --all` decides promotion to `current`
- [ ] A failed gate leaves the previous version as `current` and marks the run failed

- [ ] **This lane must run on `windows-latest`, and it is now the only lane that rebuilds the
      pinned environment.** #6 measured that `environment.lock.yml` cannot be restored on Linux:
      it pins conda build strings and is win-64 by construction — `vc`, `vs2015_runtime`, four
      `m2w64-*`, `ucrt`, `win_inet_pton`, 85 Windows build strings across 253 lines — and
      `requirements-lock.txt` carries `pywin32==308`. `docs/ENVIRONMENT.md` already said the
      solve fails on a different OS; the fast lane therefore installs from `pyproject.toml`
      instead and never touches the lockfile. The consequence lands here: **nothing in CI
      currently proves `Project` still recreates.** A lockfile that has quietly stopped working
      would not be discovered until someone needed it, which is precisely when it is most
      expensive. Budget for it — `windows-latest` bills at 2× minutes on a private repository,
      the environment is 8.2 GB against a 10 GB per-repository cache budget, and
      `docs/ENVIRONMENT.md` puts a cold rebuild appreciably over its warm 7 minutes. A weekly
      schedule is the right cadence for that cost; a per-push one is not

- [ ] **Budget this lane from a measured run, not from `--budget` (from #29's run, 2026-09-05).**
      A full retrain is **1 h 41 m** on the maintainer's machine — measured end to end, 22:03:51 to
      23:44:46, at the configured 25 trials. That is the number to size a CI timeout against, not
      the 3.5 h still written in older card prose, which predates #29's search-space narrowing.

      **And `train.py --budget` will over-project, so do not size the timeout with it.** It takes
      the mean of `model-fits.csv` and multiplies by 381. But that table holds only the **six
      scored fits** — five outer refits and the deployed one — which train on the full fold and are
      the most expensive fits in the job; a tuning fit trains on an inner fold. Nor does it model
      pruning, and Optuna pruned **2 to 19 of each fold's 25 trials** on the real run. Measured:
      mean scored fit 22.6 s, so `--budget` projects ~2.4 h against 1.6 h of actual tuning, ~45 %
      high. It gets the *fit count* exactly right; only its hours are wrong. Either widen what the
      log records to include tuning fits, or have this lane read the wall time a previous run
      actually took.

- [ ] **Run the four `@pytest.mark.slow` tests. Nothing in CI runs them any more** (from #86,
      2026-09-12). The fast lane's `suite` job was running the whole suite against a 20-minute
      cap it could not meet — the full run is 24 m 58 s — and the three pushes before #86 all
      died with "The job has exceeded the maximum execution time of 20m0s", with nothing wrong
      in any of them. #86 made that job `-m "not slow"`, which is what `pyproject.toml` has
      said the marker means since #69 wrote it. The deselected four, and what each stops
      checking on a push:

      | Test | Costs | What goes unchecked |
      |---|---|---|
      | `tests/selection/test_selection.py::test_the_configured_budget_reproduces_the_reduced_one_on_which_rows_it_reads` | ~11 min | That `SENTINEL_BUDGET` changes only how long Boruta iterates, not which rows it reads |
      | `tests/gates/test_ac1_reproducibility.py::test_the_deployed_fit_reproduces_itself_across_thread_counts` | ~3 min | AC-1's own claim, against two real fits at different thread counts |
      | `tests/data/test_golden.py::test_the_deployed_screening_removes_twenty_of_the_eight_hundred_and_ninety_three` | ~18 s | What the pipeline actually drops — the only test that pins it |
      | `tests/surrogate/test_loco.py::test_the_class_folds_are_the_ten_families_with_the_supports_88_measured` | — | That every alloy class stays estimable, before a 4.7 h run finds out |

      Add `python -m pytest -m slow` to this lane. Until then the honest statement is that
      those four are checked on the maintainer's machine and nowhere else — which is a
      **regression #86 introduced deliberately**, to stop a lane that never reached the gates
      at all, and it is this card's to repay

- [ ] **This lane must install from `requirements-lock.txt`, and that is now a measured
      requirement rather than a tidiness one** (from #93, 2026-09-12). The fast lane installs
      `pip install -e ".[dev,uq,novelty,api]"`, which resolves `pyproject.toml`'s **floors**. On
      2026-09-12 `catboost>=1.2` resolved to **1.2.10** while the `Project` environment holds
      **1.2.8**, and the two fit different trees: on the same fixture the raw interval coverage
      moved from 49/56 to 44/56, the tree count from 7 to 9, and two of three probe candidates
      went from an ordinary band to a **crossed** one. #93 reproduced every runner digit in a
      Windows venv built on the resolved versions, and then isolated it: with scikit-learn and
      pandas restored to the `Project` versions and CatBoost left at 1.2.10 the numbers did not
      move, so the cause is **`catboost>=1.2` alone** and it is the wheel, not the platform.

      The consequence for this card is direct: **a retrain that installs from floors is not a
      retrain of the published pipeline.** The box above already says this lane is the only one
      that rebuilds the pinned environment — this is the second reason, and the sharper one. The
      first reason was that nothing proves `Project` still recreates; this one is that the
      numbers a floor-resolved lane produces are *not the artifact's numbers*, and promoting a
      version fitted by a wheel nobody pinned would put a silently different model behind
      `current`.

      For the fast lane the same fact is a *reporting* obligation rather than a defect — it
      installs from floors on purpose, for reasons its own header sets out at length, and #93's
      two tests now assert only what holds under both resolutions. But the lane's summary should
      say which versions it resolved, because the first question to ask of a CI-only failure is
      `Successfully installed`, and today that is four screens deep in a log

- [ ] **The version this lane fits drops `SCALER_PAYLOAD`** (decided 2026-09-12 on #23; boxed on
      #34 until that card closed and moved it here on 2026-09-12). `DeployedFit.payloads` in
      `hydms/surrogate/deploy.py` names three keys under the rule that each is "declared by the
      module that reads it back, so this mapping cannot name a key nothing loads".
      `SCALER_PAYLOAD` breaks that rule: `scaler_from` has no production call site, because #26
      fits on raw features and #48 landed as a *capacity* ceiling that reads no scaled matrix.
      #23 weighed keeping it as insurance against a future refit-on-candidates and rejected
      that — the insurance only pays for a consumer that scales, and #48 measured that the
      distance consumer is not coming back.

      **Why this card and not #34.** #34 wrote `artifacts/v3` on 2026-09-12 and it carries
      `model`, `conformal` **and `scaler`**, exactly as `v2` does. `promote` copies the payload
      set of the version it certifies; it fits nothing, so it cannot drop a key. **Only a fit can,
      and the next fit is this lane's retrain.**

      Three things it touches, none of them optional:

      - `DeployedFit.payloads` stops emitting the key, and `DeployedFit.scaler` stops being fitted
        for persistence. `fit_scaler`, `FittedScaler` and `scaler_from` all **stay** — `TRAIN` is
        imported by `hydms.screens.domain`, `selection.py` fits one in the moment for VIF, and the
        refuse-on-`fit` behaviour is what makes "never refit" enforceable if a consumer ever does
        appear.
      - `tests/artifacts/` and the manifest name the payload; both have to stop expecting it for a
        version written after this change, **while still reading `v1`, `v2` and `v3`**, which keep
        it. A version is sealed when written — this is a change to the *next* contract, never a
        rewrite of a sealed one.
      - `CONTEXT.md`'s **Artifact version** entry. It has been corrected once already, on
        2026-09-12, because it promised that "the next version written" would hold three things
        and `v3` holds four. Nothing tests that file, so it changes when this lands or it stays
        wrong again.

      Not an unfreeze condition.

- [x] **The promoted version travels with the repository, through Git LFS** (P2 half, decided
      2026-10-16 by @amirhossein: LFS over a Release asset, a raw commit or a workflow artifact).
      `.gitignore` admits `artifacts/current.json` and `artifacts/v<N>/`, still ignores
      `gate-results.json` and `save()`'s `.v<N>.partial` staging; `.gitattributes` sends
      `artifacts/v<N>/*.joblib` through LFS and leaves both JSON files plain text. `load()` raises
      `PayloadNotFetched` ("run `git lfs pull`") on an LFS pointer instead of `PayloadCorrupt`
      ("re-run the pipeline"), and the gates' `candidate()` maps it to `NoCandidate`, so the fast
      lane, which checks out without LFS, stays SKIPPED rather than ERRORED.
      `tests/artifacts/test_portability.py` pins the routing against the store's own names and,
      once a version is committed, checks that every payload is a pointer, not a raw pickle.
- [ ] **Commit `v3` from the maintainer's machine** — the only copy. `git lfs install`, then
      `git add artifacts/current.json artifacts/v3` and push. The three skipped tests in
      `test_portability.py` then run. Afterwards: load `v3` on Linux from a fresh clone (it was
      pickled on Windows under CatBoost 1.2.8), and rewrite CLAUDE.md's *promoted model is on one
      machine* invariant

## Runnable check

```bash
gh workflow run retrain.yml --ref main
```

## Traces to

`docs/PRD-inverse-design.md` — S1

## Narrative

- 2026-10-16: Portable-artifact half. Chose LFS for the payloads and plain git for the JSON
  because the two have different readers: `read_manifest` and `current()` run on a bare
  interpreter in CI, and must not need an LFS fetch to say what a version is. An unfetched
  pointer had been indistinguishable from tampering, because both fail the digest check; the
  `PayloadCorrupt` message then told the reader to retrain, which is the wrong fix. That is why it
  is a separate exception. **The risk left open:** a machine without `git lfs install` commits the
  pickle raw, and git raises no error. `test_every_committed_payload_is_an_lfs_pointer` is the
  only thing that catches it. The `v[0-9]*` rule admits *every* version, including one that is
  not promoted; nothing refuses that commit except review. (by @assistant)

- 2026-09-26: Moved verbatim from `CONTEXT.md`, entry **Artifact version**, where it stood as a *State of the term* block. The glossary now holds definitions only; card state lives here. (by @assistant)

  > *State of the term, not part of the definition:* **the scaler is on its way out of this list**
  > (card #23, decided 2026-09-12; removal boxed on #7 since #34 closed). `v1`, `v2` and `v3` carry a
  > `scaler` payload and always will — a version is sealed when written — but nothing reads it back
  > at inference. The justification for keeping it named exactly one consumer, #48's applicability
  > domain, and #48 landed as a *capacity* ceiling that reads no scaled matrix.
  >
  > **Corrected 2026-09-12, the day after this block was written, by the thing it predicted.** It
  > said "the next version written holds a model, its correction and a manifest". The next version
  > written was **`v3`**, promoted that evening, and it holds all four. The sentence was wrong about
  > *which act changes a payload set*: **`promote` copies the payloads of the version it certifies —
  > it fits nothing — so only a fit can drop a key.** The next *fit* is card #7's retrain, which is
  > where the box now lives and where this entry changes with it. Until then the definition above is
  > true of every version that exists.
  >
  > *Keep the correction rather than the clean sentence.* Nothing tests this file, so a prediction
  > written into it is a claim no diff can go red on; this one survived exactly one day, and it
  > survived because the version that falsified it was written by a command nobody thought of as
  > writing a version.

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
