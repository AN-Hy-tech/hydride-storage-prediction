---
id: 31
status: backlog
priority: High
blocked_by: [5, 27]
assignee: "@amirhossein"
tags: [p1, l3, AC-3, R1]
---

# GATE AC-3: conformal coverage matches nominal

**Phase 1 — Hardening Chapter 1** · **L3 Surrogate** · Estimate: 0.5 d

> **Owns (hidden behind this module):** Whether the intervals mean what they claim.

## Why this exists

If coverage is badly off, the LCB ranking signal is meaningless and every candidate list
downstream is untrustworthy. This gate is the reason Architecture A's ranking can be
believed at all — it is the load-bearing check for risk R1.

## Done when

- [ ] Empirical coverage measured on the held-out test set
- [ ] Gate passes when coverage is within the configured tolerance of nominal
- [ ] Failure reports measured vs nominal coverage, not just a boolean
- [ ] Registered as `AC-3` and run by CI

- [ ] **There is a model to score now, and three of this card's numbers were untracked probes
      (2026-09-06).** `python -m hydms.surrogate.calibrate --save` builds the deployed fit — carved,
      calibrated, explained — and persists it. Two things follow that this card owns.
      **(a) AC-3 passes against it: coverage 0.7795 against a nominal 0.8**, off by 0.0205 of an
      allowed 0.05, on 254 held-out `test` rows — raw coverage on the same heads is 0.6575, which is
      the gap #27 exists to close, measured here on rows nothing was fitted or calibrated on. The
      binomial standard error at this n is 0.0251, so the tolerance is about two of them: **this
      passes, and it does not pass by much.** Reaching an unpromoted version is already solved —
      `hydms/gates/_artifact.py`, decided on #33 — so nothing here needs designing.
      **(b) `conformal.csv`, `conformal-coverage.csv` and `conformal-rows.csv` sat untracked in
      `reports/model/` from 2026-09-05 to 2026-09-06**, written at 14:35 by a probe-budget run, nine
      hours before the real fit — while [PHASE-H-RUNBOOK.md](../docs/PHASE-H-RUNBOOK.md) S4,
      [README.md](README.md) and card #27 all quoted `conformal-rows.csv`'s 893/172/701 by value.
      Three committed documents citing a file no committed run produced. `calibrate --save`
      regenerates all three from a real fit and Step 8 of
      [RUNNING-THE-FIT.md](../docs/RUNNING-THE-FIT.md) now stages them by name. **Check the
      regenerated numbers against what those three documents say** before ticking anything here: if
      they moved, the documents are wrong, not the run

## Runnable check

```bash
python -m hydms.gates run AC-3
```

## Traces to

`docs/PRD-inverse-design.md` — AC-3, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)
