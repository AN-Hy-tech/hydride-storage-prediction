---
id: 31
status: done
priority: High
blocked_by: [5, 27]
assignee: "@amirhossein"
tags: [p1, l3, AC-3, R1]
---

# GATE AC-3: conformal coverage matches nominal

**Stage S4 — Surrogate layer** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Whether the intervals mean what they claim.

## Why this exists

If coverage is badly off, the LCB ranking signal is meaningless and every candidate list
downstream is untrustworthy. This gate is the reason Architecture A's ranking can be
believed at all — it is the load-bearing check for risk R1.

## Done when

- [x] Empirical coverage measured on the held-out test set — 254 rows of `test`, the one split nothing else in this project reads. `calibrate` deliberately reports on the calibration rows and refuses to look here, because a command that printed the test number beside a knob would invite the knob to be turned until it looked good; AC-3 is the one place it is read, it is read once, and nothing downstream of it adjusts anything
- [x] Gate passes when coverage is within tolerance of nominal — **and neither number is configuration.** The tolerance is `TOLERANCE = 0.05` in the gate module, on card #21's reasoning: a bar that can be widened by editing `pipeline.yaml` is not a gate. The nominal level is read from the **artifact's own correction**, not from the file, so a configuration edited after the fit cannot move the bar — and when the two disagree the result says so and tells you to re-calibrate before promoting
- [x] Failure reports measured vs nominal coverage, not just a boolean — and so does the **pass**, because a green gate whose number nobody can see is a green gate nobody can audit. Every result carries calibrated coverage, raw coverage on the same rows, both mean widths, and the binomial standard error at this `n`; a failure adds which direction the band is wrong in and what that means for the LCB every ranked list is sorted on (risk R1)
- [x] Registered as `AC-3` and run by CI (fast lane)

- [x] **There is a model to score now, and three of this card's numbers were untracked probes
      (2026-09-06).** `python -m hydms.surrogate.calibrate --save` builds the deployed fit — carved,
      calibrated, explained — and persists it. Two things follow that this card owns.
      **(a) AC-3 passed against it on 2026-09-06: coverage 0.7795 against a nominal 0.8**, off by
      0.0205 of an allowed 0.05, on 254 held-out `test` rows — raw coverage on the same heads is
      0.6575, the gap #27 exists to close, measured on rows nothing was fitted or calibrated on. The
      binomial standard error at this n is 0.0251, so the tolerance is about two of them: **it
      passes, and not by much.** **Caveat: that was measured in a shared working tree containing a
      concurrent session's uncommitted implementation of this gate** — at the commit carrying this
      box, `ac3_conformal_coverage.py` is still a `Pending` stub. Re-measure once that work lands
      rather than inheriting the number; what this session contributed is the version it scored.
      **(b) `conformal.csv`, `conformal-coverage.csv` and `conformal-rows.csv` sat untracked in
      `reports/model/` from 2026-09-05 to 2026-09-06**, written at 14:35 by a probe-budget run, nine
      hours before the real fit — while [PHASE-H-RUNBOOK.md](../../docs/PHASE-H-RUNBOOK.md) S4,
      [README.md](../README.md) and card #27 all quoted `conformal-rows.csv`'s 893/172/701 by value.
      Three committed documents citing a file no committed run produced. `calibrate --save`
      regenerates all three from a real fit and Step 8 of
      [RUNNING-THE-FIT.md](../../docs/RUNNING-THE-FIT.md) now stages them by name. **Check the
      regenerated numbers against what those three documents say** before ticking anything here: if
      they moved, the documents are wrong, not the run

      **Both halves are now closed (2026-09-06).**
      **(a) Re-measured from the committed implementation**, as this box asks, and the numbers are
      the same to the digit: **coverage 0.7795 against nominal 0.8**, off by 0.0205; raw coverage
      **0.6575** on the same heads; mean width 0.8630 wt% calibrated against 0.6485 raw; 254 rows;
      standard error 0.0251. It passes, and not by much — 0.82 of a standard error inside a bar
      that is two. `ac3_conformal_coverage.py` is no longer a stub and the number is reproducible
      from this commit.
      **(b) The three tables were checked against the three documents and none of them moved.**
      `conformal-rows.csv` still reads 893 / 20 screened out / 172 calibration / **701 grown on**,
      and `conformal.csv` still reads **+0.03735492530223672** at 172 calibration rows — the values
      PHASE-H-RUNBOOK.md S4, this board's README and card #27 quote. The probe and the real fit
      agreed because the carve is a seeded, group-aware cut of the screened training rows and the
      probe used the same seed; that is a coincidence of construction, not a licence to skip the
      check next time.

      **One number this gate reports that nothing else in the project had measured:** card #26's
      64.4 % raw coverage was a per-fold probe. The deployed fit's raw band on the **held-out test
      split** is 0.6575, which is the same finding on the split the thesis reports, and it is what
      makes the calibration's value a measurement rather than a claim.

## Runnable check

```bash
python -m hydms.gates run AC-3
```

## Traces to

`docs/PRD-inverse-design.md` — AC-3, R1

## Narrative

- 2026-09-06: The gate reports three numbers where the card asked for one, and the second is the
  reason. Calibrated coverage alone answers the criterion and says nothing about what the
  calibration bought; raw coverage on the same held-out rows turns a green gate into the evidence
  Chapter 1 needs — 0.6575 to 0.7795 against a nominal 0.80, on rows nothing was fitted or
  calibrated on. The third, the binomial standard error, exists because 254 rows is a small sample
  and a reader has to be able to tell a miscalibrated band from a noisy one; it is also where the
  0.05 tolerance comes from, being two of them. (by @assistant)
- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
