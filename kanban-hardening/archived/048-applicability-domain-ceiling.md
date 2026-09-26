---
id: 48
status: done
priority: High
blocked_by: [30, 44]
assignee: "@amirhossein"
tags: [pa, l4, S4, AC-8, R1]
---

# Applicability-domain ceiling

**Stage S5 — Guard rails** · **L4 Screens** · Estimate: 1 d

> **Owns (hidden behind this module):** How far from known chemistry a prediction may be trusted.

## Why this exists

The Beltrame result means a candidate from an unfamiliar corner of composition space is
not merely uncertain — it is **out of scope**. Those are different things and the glossary
(35) keeps them distinct.

The ceiling is set from the leave-one-alloy-class-out result (30): the distance at which
measured cross-family performance degrades past what the thesis is willing to claim. It is
the primary structural mitigation for risk R1.

## Done when

- [x] Ceiling derived from the LOCO result, not chosen arbitrarily; the derivation is documented
- [x] Candidates beyond it are flagged `OUT_OF_DOMAIN`, distinct from `HIGH_UNCERTAINTY`
- [x] Ceiling is a config value so risk-R1 iterations can tighten it and re-run
- [x] Alloy-class assignability checked as a second, independent domain signal
- [x] **The ceiling is a `Screen` (#44) and it declares its own vocabulary.** `OUT_OF_DOMAIN` and
      `HIGH_UNCERTAINTY` are entries in `reasons`; `hydms.screens.apply_screens` refuses a code no
      screen declared, which is what lets #75 enumerate every refusal the API can emit rather than
      maintaining a second list. The shared `INDETERMINATE` is a **rejection**: a ceiling that could
      not be computed for a candidate must not admit it. Return the distance and the ceiling as
      extra columns — the runner prefixes and carries them as `<screen>.<column>`.

- [x] **The numbers this card waits on now exist, and one of them changes what the ceiling is
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

- [x] **A second, independent reason to refuse, and ElMD distance does not capture it** (added
      2026-09-06). A gradient-boosted tree predicts leaf averages of training targets, so it
      **cannot return a value above the target range it was trained on**. Measured over the 893
      training rows: Mg median **3.80 wt%** against **1.60** for every other class, Mg max
      **7.19** against a non-Mg max of **5.19**, with **21 of 96 Mg rows above the entire non-Mg
      range**. So a candidate can be *chemically close* to the training set by any composition
      metric and still sit in a capacity regime the model is structurally unable to reach. **A
      distance screen cannot see this, because it is a property of the target, not of the
      composition.**

      **The screen this implies is arithmetic, not learned, and it costs nothing to add.** The
      physical ceiling is `wt%_max = H/M_max * 1.008 / mean atomic mass` with `H/M_max` = 2 for
      ordinary interstitial dihydrides and 2.5 for BCC HEAs ([Sahlberg et al.
      2016](https://doi.org/10.1038/srep36770), lattice strain opening both tetrahedral and
      octahedral sites). Every term is computable from the formula alone, so it stays inside PRD
      2.3's enabling fact. A prediction above that ceiling is unphysical and must be refused
      rather than ranked; a prediction near the top of the *training* range while the composition
      implies a much higher ceiling is the extrapolation case this card is for. Whether that is a
      third `reasons` code or a qualifier on `OUT_OF_DOMAIN` is this card's decision -- but note
      it cannot be `INDETERMINATE`, which is a rejection for *uncomputable*, and this quantity is
      always computable.

      The fuller future-work programme behind this -- Miedema descriptors re-tested under the
      fixed merge, the H/M reparameterisation, structure proxies -- is boxed on #37, because it is
      the chapter's limitations section rather than this screen's contract

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

- 2026-09-07: **Landed, and the open decision dissolved rather than resolved.** The card offered
  two options — a per-family ceiling, or one distance calibrated against the per-class curve — and
  both assume the transfer degradation is mediated by a **composition distance**. It is not, and
  measuring that before choosing was the whole of the work.

  **The measurement.** Per class, the median nearest-neighbour distance from that family's
  compositions to every other family's, against the per-class transfer R2 in
  `reports/loco/loco-per-class.csv` (n = 10, Spearman):

  | isolation measured in | rho against transfer R2 | p |
  |---|---|---|
  | element-fraction space, L1, median | **-0.2727** | 0.446 |
  | element-fraction space, L1, mean | **-0.0182** | 0.960 |
  | the model's own 14-feature space, median | **-0.2848** | 0.425 |

  **There is no curve to calibrate against, and the ordering is not merely weak — it is
  inverted at the ends.** The two *least* isolated families, `A2B` and `LEA` (both 0.1667 in
  element space), score 0.7264 and 0.4995, among the best; the *most* isolated, `AB` at 0.6521,
  scores 0.4214, mid-table. A scalar threshold fitted to that would reject the families the model
  handles best, and ten per-family thresholds would each be set from a number distance does not
  predict.

  **The argument that closes it, rather than merely weakening it, is the feature-space row.**
  ElMD is not built yet (#49), so it is fair to ask whether a Pettifor-scale metric would order
  what an L1 metric does not. It cannot matter: **the model cannot see it.** A CatBoost fit reads
  fourteen numbers, and distance in the space it actually reads does not order its transfer
  failures either. No metric over a space the model never reads can be the mechanism behind that
  model's failures. So ElMD stays valuable — it is chemical novelty evidence, and AC-7 requires
  it — and it is *not* this ceiling. Boxed on #49.

  **What does order the failures is a property of the target.** Of everything measured, exactly
  one quantity reaches p < 0.05 at n = 10: `outside_rest`, the fraction of a family's
  compositions whose capacity lies outside the range every other family spans. Against per-class
  MAE, rho **+0.7006** (p 0.024); against per-class interval coverage, **-0.7006** (p 0.024). It
  is carried by `Mg`, and that is the finding rather than a weakness of it — the mechanism is
  arithmetic, not statistical. A gradient-boosted tree predicts leaf averages, so it cannot return
  a value outside the target range it was trained on.

  **So the ceiling is a capacity, and it is computed rather than chosen.** Counting the families
  holding training rows above each level (893 rows, reconciled classes):

  | above | rows | families |
  |---|---|---|
  | 3.00 wt% | 138 | 8 |
  | 4.00 wt% | 46 | 5 (Mg 40 of them) |
  | 5.00 wt% | 22 | 2 |
  | **5.19 wt%** | **21** | **1 — Mg** |
  | 6.00 wt% | 5 | 1 |

  At 5.19 wt% — the maximum of every non-`Mg` training row — cross-family evidence stops
  existing, and LOCO is what tells us the sole remaining family is the one the model cannot
  transfer into (R2 -0.3381, coverage 0.1146, MAE 1.577 against 0.24–0.49 elsewhere). That is
  literally the sentence the card asked for, *the level at which measured cross-family performance
  degrades past what the thesis is willing to claim*, read along the axis the evidence supports.
  It is not typed into a constant either: `DomainReference.measured` derives it as "the highest
  capacity more than one class reaches", so new data moves it, and a test asserts that on a
  synthetic corpus.

  **The card's own prescribed formula was wrong, and measuring it first is what caught it.** Box
  six specified `H/M_max` = 2, or 2.5 for BCC HEAs. Applied to the 1,278 curated rows, that bound
  puts **31 real materials above their own physical ceiling** — worst by 2.345 wt% — and a flat
  2.5 still puts 9 there. The constant is not a constant: rare earths form **tri**hydrides
  (`YH3`, `LaH3`, `CeH3`) and thorium reaches `Th4H15` at 3.75, so `Mg22Y3` at 6.48 wt%,
  `Mg4La1`, `Th7Co3` and every light-rare-earth `MIC` compound sit above a ceiling of 2. **A
  screen that calls its own training data unphysical is broken**, and this one would have shipped
  refusing the highest-capacity materials in the corpus — the exact population the ceiling exists
  to reason about.

  | rule | curated rows above their ceiling | worst excess |
  |---|---|---|
  | flat H/M 2.0 (as the card prescribed) | 31 | 2.345 wt% |
  | flat H/M 2.5 | 9 | 1.696 wt% |
  | element-wise max | 16 | 1.600 wt% |
  | **max(2.5, element-wise max)** | **4** | **1.047 wt%** |

  `HM_MAX` therefore carries the richest known binary hydride stoichiometry per element and the
  rule is `max(floor, element-wise max)`, with Sahlberg's 2.5 kept as the *floor* — where it is
  still doing real work, since it is what admits the BCC solid solutions whose constituents are
  all dihydride formers. **A composition-weighted average was measured and rejected**: it puts
  `LaNi5` at H/M 0.5 against a real 1.0, so it is not an upper bound at all. There is a test
  asserting that, because it is the obvious next idea.

  **Four rows remain above their ceiling and none is absorbed.** `Ce1Ni3Cr2` (5.19 wt%, implies
  H/M 3.606), `Ce1Ni4Zr1` (4.94, 3.807) and `Ce1Ni4Cr1` (4.73, 3.339) are data defects — `LaNi5H6`
  is H/M 1.0 and no AB5 intermetallic holds three and a half hydrogens per metal atom — and are
  boxed on #14. The fourth, `Ti1.1Cr1Mn1V0.255Fe0.045`, is over by **0.006 wt%**: it is Sahlberg's
  BCC limit to within the rounding of a published table, and loosening a physics bound to swallow
  it would be fitting the constant to its own residue. A test names all four, so tightening the
  bound onto a real material fails the build rather than passing quietly.

  **Both decisions the card left open, taken.** The capacity signal is a **separate code**
  (`ABOVE_PHYSICAL_CEILING`) rather than a qualifier on `OUT_OF_DOMAIN`, because the two need
  different answers from the API: one says *that is not possible*, the other says *we have no
  evidence there*. And `OUT_OF_DOMAIN` is a **capacity level**, not a distance — the third option
  the card did not list.

  **Uncertainty is reported, never substituted, and #30 measured both directions of that.** The
  card's argument was that a candidate can be out of family with a *narrow* band. The converse is
  in the same table and is just as sharp: `SS` is the **best** family by R2 (0.7626) with the
  second-*worst* coverage (0.1644), and `HEA` is the second worst by R2 (-0.0723) with the
  **best** coverage (0.8824). Accuracy and calibration come apart in both directions across
  families, so `HIGH_UNCERTAINTY` and `OUT_OF_DOMAIN` are separate codes and a test pins that
  neither collapses onto the other.

  **The bounding-box signal is nearly vacuous here, and saying so is part of the result.** Only
  **3 of 385** held-out rows fall outside any training feature span. The curated chemistry is
  homogeneous; the domain problem in this project is not unusual chemistry, it is unreachable
  capacity. It is kept because a candidate arriving from a search over the composition simplex is
  not drawn from this corpus and a range check costs one comparison — but nobody should quote it
  as the applicability domain doing work.

  **Where the measured reference lives, and why not in the bundle.** `domain-reference.json` sits
  beside the module, generated by `python -m hydms.screens.domain --emit` with a test asserting
  the committed bytes are what the code produces — the pattern #30 used for `loco.md`. It is not
  in the artifact bundle because the feature spans and capacity levels are properties of the
  *data* rather than of any one fit, and the transfer numbers come from `reports/loco/`, which is
  committed for the same reason AC-6's gate reads it rather than refitting. Whether the delivery
  path should pin a copy so a served version cannot drift from the data it was screened against is
  #76's call, and is boxed there.

  **One test was measured before being left unmarked.** `test_the_physical_ceiling_admits_the_
  curated_rows_it_should` reads and parses all 1,279 formulae in **0.27 s** — it featurises
  nothing — so it is not marked `slow`. Marking it would have put the one regression test guarding
  a physics bound against tightening onto real materials behind the lane CI deselects. 36 tests
  here, `tests/screens/` 99 green, ruff and mypy clean. (by @assistant)

- 2026-09-07: **A finding this card does not owe, recorded so it is not re-derived.** The
  `HIGH_UNCERTAINTY` threshold is 1.12 wt%, the standard deviation of the training target — a band
  wider than the marginal spread has told the caller nothing they did not know before asking. That
  is a defensible *derivation*, but it is not a *calibration*: **the per-row calibrated interval
  width distribution has never been measured.** `reports/model/conformal-coverage.csv` carries only
  its mean (0.8951 wt%), and no committed table holds the widths themselves, so nobody can yet say
  what fraction of real predictions this threshold refuses. It is a config value precisely so that
  can be fixed without a code change. The measurement belongs with the model card (#83), which has
  to state the band's behaviour anyway. (by @assistant)

- 2026-09-07: **A consequence this card did not expect: the persisted scaler has lost its only
  named consumer.** Two surrogate-layer docstrings justified keeping `FittedScaler` in the artifact
  bundle by naming this card — "the distance-based work downstream (the applicability domain, card
  #48)" and "the scaler stays in the bundle because the applicability domain (card #48) is
  distance-based and needs it". The domain turned out not to be distance-based, and it reads no
  scaled matrix. Grepped to be sure: `scaler_from` and `SCALER_PAYLOAD` are written by `deploy.py`
  and read back by nothing at inference; `selection.py`'s scaler is fitted in the moment, not the
  persisted payload. Both docstrings now say that plainly rather than being reworded around it, and
  the decision — whether the *next* version's bundle should still carry it — is boxed on **#23**,
  which owns the payload. `artifacts/v2` is sealed and unaffected either way. **When a card's
  finding removes a reason, go and find the sentences that were resting on it**; a grep for
  "distance-based" found four live claims and two of them were load-bearing. (by @assistant)

