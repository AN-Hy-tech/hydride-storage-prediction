---
id: 96
status: backlog
priority: Normal
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

- [ ] **Measure the blast radius before choosing a fix.** Grep every call site and every documented
      invocation of `--report`, in `docs/RUNNING-THE-FIT.md`, `docs/PHASE-H-RUNBOOK.md`, the
      workflows and the tests, and say which of them redirect it. If the answer is "nobody
      redirects it in anger", the cheap fix is the right one; if the slow lane (#7) redirects it,
      the flag split is
- [ ] **Take one of the two fixes, and record why not the other.** Either (a) give the
      chosen-configuration read its own flag, so an output redirect cannot move an input; or
      (b) refuse `--save` outright when the configuration fell back to defaults. They are not
      equivalent: (a) makes the trap unreachable, (b) leaves it reachable but unable to produce a
      promotable artifact. (b) is smaller and also guards the case where `model-chosen.csv` is
      simply missing
- [ ] **A test that fails on the old behaviour.** Point `--report` at a tmp directory with no
      `model-chosen.csv` and assert the chosen path — either that the configuration read still
      finds the real file, or that `--save` refuses. Asserting only the stdout sentence is not
      enough; the sentence is what exists today and the defect survived it
- [ ] **`docs/RUNNING-THE-FIT.md` says what `--report` does.** It is the operator's document and
      the operator is the person who will redirect the flag. One sentence naming both roles

## Runnable check

```powershell
conda run --no-capture-output -n Project python -m hydms.surrogate.calibrate --target capacity --report $env:TEMP\probe
# today: prints the defaults warning, exits 0, and would persist on --save
```

## Traces to

`docs/PRD-inverse-design.md` — S1. Found on card #34 (the `--report` box, struck through there and
moved here). Card #23 owns the payload-set half of the same review.

## Narrative

- 2026-09-12: Moved off #34 at its close rather than created fresh, so the finding keeps its
  provenance: it was found on 2026-09-07 in review of the `v2` re-save, and the wrong fit it
  produced was real and discarded. Kept as its own card because the two candidate fixes disagree
  about *where* the guarantee belongs — in the flag's shape, or in the refusal — and that is a seam
  decision, not a bug fix. (by @assistant)
