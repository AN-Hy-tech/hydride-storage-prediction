---
id: 96
status: done
priority: P1
blocked_by: []
assignee: "@amirhossein"
tags: [ph, l3]
---

# An output flag that silently changes the fit

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 0.25 d

> **Owns (hidden behind this module):** Whether redirecting a command's output can change what it computes.

**This card is NOT an unfreeze condition.** It was found in review on #34 and moved here on
2026-09-12 when #34 closed, because both candidate fixes are in the surrogate seam and neither was
that card's to take. The unfreeze condition is fixed and stays fixed.

## Why this exists

`--report` on `hydms.surrogate.calibrate` is two things at once: the directory the run *writes*
its tables to, **and** the directory `deploy.py:163` *reads* `model-chosen.csv` from. So the
obvious, careful thing to do — point `--report` at a scratch directory so a probe run cannot
overwrite the committed tables — silently changes what is fitted. The chosen configuration is not
found, the code falls back to **CatBoost's own defaults**, and `--save` then persists that
smoke-test fit into an artifact version whose manifest note says `deployed fit`.

**It has already happened once.** On 2026-09-07, re-saving the deployed fit from a clean tree, the
first attempt produced a conformal correction of **+0.030990** instead of **+0.037355** and was
discarded. It was caught inside a minute, and only because the command announces it on stdout:

> so this fit uses CatBoost's own defaults … That is a smoke test of the calibration path, not the
> deployed band

That is the system behaving well. What it is not is a *check*: nothing fails, nothing exits
non-zero, and the manifest's `notes` field cannot record it — `notes` only distinguishes
`--no-screening`. A run left unattended, or read from a log after the fact, produces an artifact
that does not say it came from a default.

**The rule this breaks is already written down.** An artifact that does not say it came from a
default is an artifact somebody will promote. See
[[report-flag-is-also-an-input-path]] and
[[run-provenance-belongs-beside-the-numbers]] — an absent record must mean *unknown*, never
*"full"*.

## Done when

- [x] **Measure the blast radius before choosing a fix.** Grep every call site and every documented
      invocation of `--report`, in `docs/RUNNING-THE-FIT.md`, `docs/PHASE-H-RUNBOOK.md`, the
      workflows and the tests, and say which of them redirect it. If the answer is "nobody
      redirects it in anger", the cheap fix is the right one; if the slow lane (#7) redirects it,
      the flag split is
      — **Measured 2026-10-16: nobody redirects it.** No invocation of `calibrate --report` exists
      in `docs/RUNNING-THE-FIT.md`, `docs/PHASE-H-RUNBOOK.md`, `.github/workflows/ci.yml`, the
      tests, or #7 (which never names `calibrate`). Every other `--report` hit belongs to
      `train`, `loco`, `evaluate`, `select` or `gates`. Gate AC-1 calls `deployed_params` on the
      configured path directly and is not reachable through the flag. So the cheap fix
- [x] **Take one of the two fixes, and record why not the other.** Either (a) give the
      chosen-configuration read its own flag, so an output redirect cannot move an input; or
      (b) refuse `--save` outright when the configuration fell back to defaults. They are not
      equivalent: (a) makes the trap unreachable, (b) leaves it reachable but unable to produce a
      promotable artifact. (b) is smaller and also guards the case where `model-chosen.csv` is
      simply missing
      — **Took (b), checked before the fit.** `calibrate.main` now reads the configuration
      before the stamp and the featurisation, and `--save` with `params is None` exits 2 with a
      sentence naming the path it looked in. Not (a): nobody redirects the flag, so a second
      flag is surface with no caller; and (a) leaves the missing-table case open, which (b)
      closes. Not in `save_deployed` either: `hydms/pipeline/smoke.py` saves a deliberately
      cheap fit through it, and the guarantee belongs to the command that makes promotable
      versions, not to the store
- [x] **A test that fails on the old behaviour.** Point `--report` at a tmp directory with no
      `model-chosen.csv` and assert the chosen path — either that the configuration read still
      finds the real file, or that `--save` refuses. Asserting only the stdout sentence is not
      enough; the sentence is what exists today and the defect survived it
      — `tests/surrogate/test_calibrate.py`: absent, empty, and prefix-less `model-chosen.csv`
      each refuse with exit 2, write nothing, and never reach `provenance.begin`,
      `capacity_matrix`, `deployed_fit` or `save_deployed`; the three fail on the old code. Two
      more pin the open paths: defaults without `--save`, and `--save` with a configuration
- [x] **`docs/RUNNING-THE-FIT.md` says what `--report` does.** It is the operator's document and
      the operator is the person who will redirect the flag. One sentence naming both roles
      — Step 5 says it, and the trouble table carries the refusal sentence

## Runnable check

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.calibrate --target capacity --report $env:TEMP\probe
# today: prints the defaults warning, exits 0, and would persist on --save
```

## Traces to

`docs/PRD-inverse-design.md` — S1. Found on card #34 (the `--report` box, struck through there and
moved here). Card #23 owns the payload-set half of the same review.

## Narrative

- 2026-10-16: Closed with fix (b). The read of `model-chosen.csv` moved ahead of
  `provenance.begin`, so a refused `--save` costs no stamp, no featurisation and no fit — the
  operator loses seconds, not two minutes. A smoke run on defaults stays allowed: that is what
  the defaults path is for. One residue, not boxed: a redirected `--report` also reads the train
  run record from the scratch directory, so the calibrate record's `source_run_id` is empty
  there. That reads as *unknown*, which is the honest value, and a refused `--save` never gets
  that far. Verified in a Linux `uv` venv: the new file passes and fails on the old code; the
  fast lane's other failures there (four `test_cli`/HG-4, five L13 under pandas 3.0.6, one
  last-digit novelty reference) all reproduce on the unmodified base. (by @assistant)
- 2026-09-12: Moved off #34 at its close rather than created fresh, so the finding keeps its
  provenance: it was found on 2026-09-07 in review of the `v2` re-save, and the wrong fit it
  produced was real and discarded. Kept as its own card because the two candidate fixes disagree
  about *where* the guarantee belongs — in the flag's shape, or in the refusal — and that is a seam
  decision, not a bug fix. (by @assistant)
