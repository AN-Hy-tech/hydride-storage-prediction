---
id: 86
status: doing
priority: High
blocked_by: [6, 72, 79]
assignee: "@amirhossein"
tags: [ph, l0, HG-4]
---

# GATE HG-4: CI fast lane with the delivery suite and hygiene

**Stage S8 — Evidence and close** · **L0 Foundation** · Estimate: 0.5 d

> **Owns (hidden behind this module):** What every push must survive before it is allowed to be called green.

## Why this exists

The fast lane today runs one stdlib-only script over the board and the prose. That was the
right seed while no package existed; it is not sufficient once a prediction service does.

This card brings the delivery suite, the freeze check, and the lint and type gates into the same lane —
without dragging in the conda rebuild, which stays in the slow lane precisely because the environment
takes minutes and around eight gigabytes to construct.

## Done when

- [x] The fast lane runs `check_board.py`, `check_freeze.py`, the test suite, ruff, mypy and the
      coverage floor. **Done 2026-09-12** — the first four were already there; this card added
      `--cov` to the pytest step and `-m "not slow"` beside it (see the timeout box)
- [x] ruff and mypy run in #6's **conda-free** `hygiene` job, not inside the `Project`
      environment — they need no project dependencies and #68 established that the fast lane
      builds none. **Already true, and it was silently broken.** See the mypy box below
- [x] **DECIDED 2026-09-12: `pytest-cov` is installed in both places, and the floor is 88.43 %.**
      Both halves were measured before deciding. Installing it into `Project` resolves to
      `pytest-cov 7.1.0` + `coverage 7.16.0` and **moves no existing pin** — every other
      requirement was already satisfied — so `requirements-lock.txt` gained two lines and
      nothing else, the same shape as #27's MAPIE and #49's ElMD. What made it worth doing
      rather than leaving to CI: gate HG-4 reads the coverage data, so a CI-only install would
      have left the gate permanently unanswerable on the maintainer's machine, which is where
      it is asked before a push. It is also categorically unlike `uq` and `novelty` — coverage
      is a *measurement* tool that no fit and no prediction path can reach, so installing it
      cannot move a published number. Measured over the full suite: **TOTAL 88.43 %**, against
      the 80 % floor, `1 failed, 1443 passed in 37 m 52 s` (the one failure was this card's own
      workflow edit tripping `test_the_smoke_run_is_in_the_ci_fast_lane`, fixed here).
      While the count was being taken, the lock file's header was found to say 209 against 210
      actual — #49 added ElMD without moving it. It now says 212 and `docs/ENVIRONMENT.md`
      agrees
- [ ] ~~`pytest-cov` is available wherever the floor is enforced.~~ *(superseded by the box
      above; the original text is kept so the reasoning that got there is not lost)* It is declared in the `dev`
      extra and installed nowhere: neither it nor `coverage` is in `Project` today, so
      `pytest --cov` fails outright and the floor in `pyproject.toml` is currently
      unenforceable. Decide where it gets installed rather than inheriting the gap.
      **#6 changed the shape of this decision.** The `suite` job is not the `Project`
      environment — the lockfile is win-64 only and cannot be restored on a Linux runner — so it
      runs `pip install -e ".[dev]"`, and the `dev` extra already carries `pytest-cov>=5.0`.
      Coverage is therefore installable in CI *without touching either lockfile*, which was the
      whole reason the decision was deferred. What is left to decide is only whether the floor
      is enforced in CI alone or locally too, and locally still means adding a package to
      `Project`. The `openpyxl` question below is no longer the same decision and should be
      made on its own merits
- [x] It runs the gates that do not require a retrain, against the published artifact.
      **Already true** (`hydms.gates run --fast`), and HG-4 has now joined that selection
- [ ] **It stays comfortably under the existing timeout. THE CENTRAL FINDING OF THIS CARD, and
      the one box still open.** It did not, and the failure was invisible from the repository:
      **CI has never once completed the `suite` job on this branch.** Every push run in
      `gh run list` is `cancelled` or `failure`, and the last one — with no superseding push to
      blame — carries the annotation *"The job has exceeded the maximum execution time of
      20m0s"*. The suite job caps at `timeout-minutes: 20`; the full run is **24 m 58 s**
      (runbook §5, measured 2026-09-07), so the lane could not have fitted since long before
      this card. Reading the log: it reaches 89 % quickly and then stalls **nine minutes** with
      no further output before the cancel. 89 % lands just before
      `tests/surrogate/test_selection.py`, whose `@pytest.mark.slow` Boruta-budget test is
      eleven minutes on a twenty-core machine and unbounded on a two-core runner.

      The fix is the one `pyproject.toml` already prescribed and nobody had applied:
      **`-m "not slow"`**. #69 wrote the marker as *"takes more than a few seconds; excluded
      from the CI fast lane"* and the workflow never excluded it. What that costs is real and
      is written into #7 as a box: the four slow tests are now checked on no push at all until
      #7's slow lane runs them.

      **Still unverified, and this is why the box is open and the card is `doing`:** no CI run
      has yet finished, so "comfortably under" is a prediction, not a measurement. Tick it
      against a green `suite` job, not against this reasoning
- [x] The conda rebuild remains in the slow lane. **Untouched** — the `suite` job still
      installs from `pyproject.toml` and never restores a lockfile (#6's measurement; the
      lockfile is win-64 by construction)
- [x] **DONE 2026-09-12, and the box was righter than it knew.** `summarise()` did not name the
      failing gate *even when called* — it reported only tallies. Its test looked like it
      checked the naming (`assert name in line`) and passed solely on the **echo of the
      input**: `report.selection` is the name you asked for. Measured against the real lane it
      read `gates --fast: green -- 7 passed, 0 failed, 2 skipped, 0 errored` while AC-5 and
      HG-4 were the skips, naming neither. `summarise()` now appends `errored:`, `failed:` and
      `skipped:` name lists; the CLI grew `--summary PATH`, which CI passes
      `$GITHUB_STEP_SUMMARY`; and a second test asks the question under `--fast`, striking the
      selection string out of the line before looking for the names. See
      [[strike-the-input-out-before-asking-if-a-sentence-names-it]] — the same shape, again
- [ ] ~~A failure names which gate failed, not merely that something did.~~ **`hydms.gates.__main__`
      already has `summarise(report)`, written for exactly this** — its docstring says "one line
      for a CI step summary or a commit comment" — and nothing calls it. #6 left it uncalled
      because writing it into `$GITHUB_STEP_SUMMARY` needs a `GateReport` object, and the CLI
      hands CI only an exit code and `artifacts/gate-results.json`. Either give the CLI a flag
      that writes the summary itself, or this line stays a test-only function pretending to
      serve CI
- [x] **DECIDED 2026-09-12: `openpyxl` is NOT added and the spreadsheet stays unread — but the
      reason in the box below is wrong, and the correction matters more than the decision.**
      Read with stdlib `zipfile` rather than trusted: the sheet is `A1:F1284`, so **1,283 data
      rows over six columns**, which is what the box says. What the box gets wrong is *"the
      same six columns as `hydride_data.csv`, which is its downstream"* used to imply the CSV
      is a copy missing four rows. It is not a copy: it is a **renormalisation**. The
      spreadsheet writes `CaNi5`, `CaAl1.8B.2 (M)`, `(Ti.75Zr.25)1.05Mn.8Cr1.05V.05Cu.1`; the
      CSV writes `Ca1Ni5`, `Ca1Al1.8B0.2`, with explicit `1` subscripts, leading zeros and the
      `(M)` marker gone. Of ~1,180 distinct compositions in the spreadsheet only **117** match
      a CSV string literally. Its header is `H2_W%` against the CSV's `H2_W% (max)`.

      So the decision stands and is now better grounded: a loader would not be "reading the
      same six columns", it would be a second and divergent view of the dataset that nothing
      reconciles, in a path the freeze denies edits to. **And the phrase "the four extra rows"
      — in this box, in #9's first box, and in `kanban-hardening/README.md` — is not a thing
      that can be identified**, because the join key was rewritten between the two files. Those
      three sites are corrected here. What became of the four rows, and what `(M)` meant, is a
      data-provenance question for #89, which already carries a HyStor row-count box; it is
      **not** a dependency decision and does not reopen this one
- [ ] ~~**Decide whether `openpyxl` is added, or the HyStor spreadsheet stays unread.**~~ Card #9 left
      `Machine_Model/data/raw/HyStor_27_7_24 (1).xlsx` without a loader because reading it needs
      `openpyxl`, which is in neither `environment.lock.yml` nor the machine interpreter, and adding
      a package invalidates the lock. The cost of saying no is low — the file is one sheet of 1283
      rows over the same six columns as `hydride_data.csv`, which is its downstream, and nothing in
      the repository has ever read it. This is the same decision as `pytest-cov` above, so make both
      once rather than twice
- [x] Registered in the gate harness as HG-4. **Implemented 2026-09-12** in
      `hydms/gates/hg4_hygiene.py`, replacing the `Pending`. Three legs — ruff, mypy, the
      coverage floor — all of them run even when one has already failed, because a red build
      that names one problem and hides two costs the next person two more round trips. Cheap
      enough to simply re-ask rather than parse a log: **ruff 0.045 s, warm mypy 2.33 s**, so
      it is `Speed.FAST` and carries no `slow` marker. `tests/gates/test_hg4_hygiene.py` makes
      it red on purpose against fake checkouts under `tmp_path` (QA protocol §5), which is the
      only way the red cases are observable at all in a repository that is green

- [x] **A failure mode the card did not anticipate, fixed here: `ruff` and `mypy` disagreed
      between the two lanes.** CI's hygiene job pins `ruff==0.8.4` / `mypy==1.13.0` by hand
      while the `dev` extra — which CI's `suite` job installs, and in which HG-4 now *runs*
      those tools — floored them at `>=0.6` / `>=1.10`. A floor would have let HG-4 go red in
      CI against a ruff the hygiene job never runs, for a failure nobody could reproduce. The
      `dev` extra now pins both exactly and `tests/test_tooling.py` asserts the two sites agree

- [x] **CI's mypy was failing and a local mypy could not see it.** The hygiene job was red with
      six `import-not-found` errors for `fastapi`, `fastapi.*`, `uvicorn` and `pydantic`, added
      to `hydms/` by #78 and #79 and never added to `[[tool.mypy.overrides]]`. It passed on the
      maintainer's machine **only because that interpreter happens to have those packages
      installed** — so a green local mypy was not evidence about CI at all, which is the one
      thing the conda-free lane exists to give. Reproduced exactly by running `mypy 1.13.0` in
      a bare venv, which is what the lane actually is; that reproduction also caught **two more**
      the same shape from this card's own `coverage` import. All four modules are now in the
      override list, in both the `x` and `x.*` spellings, and both interpreters report
      `Success: no issues found in 76 source files`

## Runnable check

```bash
python scripts/check_board.py --root . && python scripts/check_freeze.py --base origin/main
```

## Traces to

`docs/PHASE-H-RUNBOOK.md` — S8, HG-4

## Narrative

- 2026-09-02: Created for Phase H (by @assistant)
- 2026-09-02: Two prerequisites recorded while landing #5. The lint/type lane is conda-free
  (see #6's amendment the same day), and the coverage floor cannot be measured anywhere right
  now — `pytest-cov` and `coverage` are both absent from `Project`, so `pytest --cov` exits
  with `unrecognized arguments: --cov`. Installing into `Project` invalidates
  `environment.lock.yml`, so where the floor is measured is a decision this card owns.
  (by @assistant)
- 2026-09-12: Gate written, both decisions made, and **three failures found that the card did
  not know about** — one of which is the reason CI has never been green. In order of how much
  they cost to find:

  **1. The lane could never fit its own timeout.** Nothing in the repository said so. The
  evidence is only in `gh run list`, where every push run on this branch is `cancelled` or
  `failure`, and the newest one — the only one with no superseding push to explain it — is
  annotated *"The job has exceeded the maximum execution time of 20m0s"*. The full suite is
  24 m 58 s against a 20-minute cap. This had been true since before the card existed and was
  invisible to anyone reading files. **Read `gh run list` before believing a workflow works.**

  **2. A green local `mypy` was not evidence about CI.** The hygiene job was failing on six
  `import-not-found` errors that cannot occur on this machine, because this machine has
  fastapi and pydantic installed and the runner does not. The conda-free lane's whole promise
  is that it reports honestly on a bare interpreter, so the only faithful way to ask it is on
  a bare interpreter: `python -m venv` + `pip install mypy==1.13.0`, which reproduced all six
  in seconds and caught two more this card was about to introduce.

  **3. A test that looked like it checked the naming, checked the echo.** `summarise()`'s test
  asserted the gate's name appeared in its output; it did, because the output quotes the
  selection you passed. Under `--fast` the function named nothing at all. The repeat of a
  pattern already recorded in memory, found by *running the function and reading the string*
  rather than by reading its test.

  Two smaller things, both of the "a number nothing tests" kind: `requirements-lock.txt`'s
  header said 209 against 210 actual, uncorrected since #49; and the HyStor spreadsheet is not
  the CSV-minus-four-rows that three documents said it was, but a differently-normalised file
  sharing 117 of ~1,180 composition strings with it. (by @assistant)

- 2026-09-12: **Left `doing`, deliberately, with one box open.** The timeout box cannot be
  ticked from this machine — it needs a `suite` job that actually finishes, and none ever has.
  The next session should read the CI run for the pushed commit and either tick it or chase
  what it names. **It will name something:** the timed-out log shows two tests already
  `F`-ing in CI at roughly 84 % and 89 % — near `tests/surrogate/test_model.py` and
  `tests/surrogate/test_promote.py` — that pass locally. They are unidentified because no run
  has ever reached the summary line that would name them. They are not regressions from this
  card; they are the first thing anyone will see now that the lane gets far enough to report.
  (by @assistant)
