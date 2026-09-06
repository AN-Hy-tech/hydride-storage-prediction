---
id: 48
status: backlog
priority: High
blocked_by: [30, 44]
assignee: "@amirhossein"
tags: [pa, l4, S4, AC-8, R1]
---

# Applicability-domain ceiling

**Phase A — Screen-and-Rank** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** How far from known chemistry a prediction may be trusted.

## Why this exists

The Beltrame result means a candidate from an unfamiliar corner of composition space is
not merely uncertain — it is **out of scope**. Those are different things and the glossary
(35) keeps them distinct.

The ceiling is set from the leave-one-alloy-class-out result (30): the distance at which
measured cross-family performance degrades past what the thesis is willing to claim. It is
the primary structural mitigation for risk R1.

## Done when

- [ ] Ceiling derived from the LOCO result, not chosen arbitrarily; the derivation is documented
- [ ] Candidates beyond it are flagged `OUT_OF_DOMAIN`, distinct from `HIGH_UNCERTAINTY`
- [ ] Ceiling is a config value so risk-R1 iterations can tighten it and re-run
- [ ] Alloy-class assignability checked as a second, independent domain signal
- [ ] **The ceiling is a `Screen` (#44) and it declares its own vocabulary.** `OUT_OF_DOMAIN` and
      `HIGH_UNCERTAINTY` are entries in `reasons`; `hydms.screens.apply_screens` refuses a code no
      screen declared, which is what lets #75 enumerate every refusal the API can emit rather than
      maintaining a second list. The shared `INDETERMINATE` is a **rejection**: a ceiling that could
      not be computed for a candidate must not admit it. Return the distance and the ceiling as
      extra columns — the runner prefixes and carries them as `<screen>.<column>`.

- [ ] **The numbers this card waits on now exist, and one of them changes what the ceiling is
      for** (measured 2026-09-06 by #30's real run; see `reports/loco/`). Macro transfer R2
      **0.2734** against the random-split **0.7459**, per class from **Mg -0.3381** to
      **SS 0.7626**. Two things follow for the derivation this card owes:

      **The ceiling cannot be a single distance if the families disagree this much.** The spread
      is not noise around a mean — it runs from worse-than-predicting-the-mean to better than
      several in-distribution subgroups, over supports of 19 to 260 rows. A scalar ElMD threshold
      fitted to the average would admit candidates near Mg and reject candidates near SS on the
      same evidence. Whether the ceiling is per-family, or a distance calibrated against the
      per-class curve, is this card's decision and the data to make it is now on disk.

      **The interval does not do this card's job, which is the argument for the card.**
      `loco-per-class.csv` carries `interval_coverage`: against the random-split out-of-fold
      **0.6293**, class folds give Mg **0.1146**, SS 0.1644, MIC 0.4713, AB 0.4746, MEA 0.5000.
      Coverage out of family is not just lower, it is unpredictably lower, and it is worst exactly
      where R2 is worst. Precisely: those are raw quantile-head bands, not the conformalised ones,
      and nothing has yet measured the conformal band out of family — but conformal coverage is
      marginal and assumes exchangeability, which a class holdout breaks by construction. So
      `HIGH_UNCERTAINTY` cannot stand in for `OUT_OF_DOMAIN`: a candidate can be out of family and
      carry a *narrow* band, which is the failure this screen exists to catch

## Runnable check

```bash
python -m pytest tests/screens/test_applicability.py -q
```

## Traces to

`docs/PRD-inverse-design.md` — S4, AC-8, R1

## Narrative

- 2026-08-30: Created during the layer decomposition of the PRD. Tickets are cut by architectural layer rather than by phase, because the PRD's phase list is a temporal decomposition and cutting along it would duplicate the evaluation stack between Architectures A and B. (by @assistant)

- 2026-09-04: #44 landed the contract this card implements. The vocabulary is declared per screen
  and enforced by the runner, so `OUT_OF_DOMAIN` vs `HIGH_UNCERTAINTY` stops being a naming
  convention and becomes something a test can assert. `temperature_window()` is the worked example
  of the config-driven threshold this card's third box asks for — and is explicitly *not* an
  applicability domain: it is the outer bound, and the AD ceiling is what this card adds. (by @assistant)
