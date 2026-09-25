# Chapter 1 revision: what exists, what was wrong, what it is now

> **Card #37, drafted and accepted by the author 2026-09-24.** Written from committed evidence only.
> Every number carries its source in the text or in the evidence table at the end. Terms follow `CONTEXT.md`. In particular, the
> three kinds of R² (*procedure*, *artifact* and *transfer* score) are never quoted in place of one
> another.

---

## 1.R.1 What exists

The forward model predicts the maximum **material** gravimetric hydrogen capacity (wt%) of a metal
hydride from its chemical formula and a temperature. It was trained on 1,279 measurements merged
from HyStor and ML-HydPARK, covering ten alloy families (AB₂, AB₅, AB, A₂B, Mg-based,
solid-solution, low-, medium- and high-entropy alloys, and multi-component intermetallics). Every
input descriptor is a composition statistic or the temperature. No structural descriptor is used.

The first version of this chapter, reproduced as `REPORT.md`, reported a stacking ensemble with
**validation R² 0.939, test R² 0.892 and test MAE 0.223 wt%**. Those figures are quoted below
**as published**. They describe a pipeline this revision found could not be re-run, and they are
contradicted by files that pipeline committed.

This revision does not patch that pipeline. It keeps `Machine_Model/src/` unedited as the record
behind the published numbers, and rebuilds the model in a separate package (`hydms/`) where each
defect found below is closed by a test that fails if it returns.

---

## 1.R.2 What was wrong

### Three findings that disqualified the published numbers

1. **The published numbers are contradicted by the pipeline's own committed outputs.** Two CSVs
   under `Machine_Model/reports/benchmarked_model/` describe two different ensembles.
   `improved_benchmark_results.csv` agrees with the report (validation 0.939, test 0.892).
   `stacking_results.csv` records CV R² 0.344, validation 0.377 and test 0.376. The report quotes
   one and never mentions the other.
2. **One script overwrote held-out ground truth with the model's own predictions.**
   `CleanLab.py:90` replaced flagged validation and test *labels* with predicted values, so the
   replaced rows score a residual of exactly zero by construction. It was harmless only because
   nothing downstream read its output.
3. **The pipeline could not be run end to end.** Four links are broken:
   - the script that produced `jarvis_filtered_features.csv` does not exist anywhere in the
     repository's history;
   - two scripts read directories that nothing writes;
   - one script's output is never read;
   - feature selection reads the splits from *before* outlier removal, contradicting the written
     method.

   Worse, `merge_datasets.py:46` joins its three feature tables by row position after resetting
   their indices. One skipped row would silently attach every descriptor to the wrong composition.

### Thirteen validation leaks

A leak here means held-out data influenced something before that data was scored. The original
audit named three. A line-by-line audit found thirteen, each with an exact site in the archival
code (`docs/PHASE-H-RUNBOOK.md` §1). The ones that move the headline numbers are:

| Leak | What happened | What it inflates |
|---|---|---|
| **L1** | The final CatBoost model chose its early-stopping iteration on the **test** set, which was then reported as held out | Every test-set figure for that model |
| **L2** | The ensemble's four members were chosen by validation score, and the ensemble was then scored on the same validation set | The headline validation R² 0.939 and its interval |
| **L4, L5** | One set of folds both tuned and scored the models (no nested CV), and every fold early-stopped on the rows it was scored on | All cross-validated scores |
| **L6** | Feature selection ran once on all 896 training rows, before cross-validation | All scores, and the claim that the 22 features are informative |
| **L7, L8** | Folds and splits grouped rows by the **raw formula string**, and not at all within folds. 1,149 strings are 1,115 materials (`La1Ni5` and `LaNi5` are one alloy). 35 rows of 16 materials straddled the train/test boundary, and 181 of 893 training rows (20.3 %) shared a material across folds | Every score, by testing on materials already seen in training |
| **L13** | Featurisation deleted the alloy-family column | Nothing directly, but it made cross-family validation impossible, so the most important number was never measured |

The rest are L3 (the label overwrite above), L9 (the positional merge), L10 (outlier clipping of
validation and test features using their own residuals), L11 (SHAP and partial dependence computed
on the test set, making §6.1 of the report a test-set artefact) and L12 (sample weights conditioned
on the target with a hand-tuned threshold).

### Twelve places the report disagrees with its own files

`docs/REPORT-RECONCILIATION.md` sets every checkable sentence of `REPORT.md` against the committed
file it cites. It is generated by code, and a test checks that every quotation occurs in the report
verbatim. It finds twelve disagreements. Besides the two ensembles above:

- The paired t-test reported as t = −2.102, p = 0.037 is recorded as t = −8.168, p = 1.65 × 10⁻¹⁴,
  against a *different* best model (CatBoost, not ExtraTrees).
- The ensemble is called "more robust across all three [temperature] subgroups". The report's own
  subgroup table shows ExtraTrees ahead in every one.
- CleanLab is said to have removed rows from the test set (~239 of 247). The scored test set has
  all 247.
- The report counts 54 elements; the data holds 55. One of them, europium, appears in a single row
  (`Eu1Ni5`). The featuriser gave that row an all-zero property vector: zero mass, zero
  polarizability.

None of the twelve is a leak. A leak can agree perfectly with its CSV. The table records which of
two numbers the pipeline actually produced. Whether either is worth quoting is the leak inventory's
question, and for every model-performance row the answer is no.

### Two problems that were neither leaks nor disagreements

- **The published descriptor set could not be produced by the published code.** The featurisation
  script requests CBFV's `magpie` property set, which yields none of the 21 published element
  descriptors. The real set is 15 Oliynyk and 6 JARVIS properties (resolved in
  `hydms/descriptors/FEATURE_PROVENANCE.md`).
- **The descriptor library has no licence.** CBFV declares no licence, so all rights are reserved
  by default, and it cannot be redistributed inside a GPL-3.0 deliverable. The element tables are
  now read from their published sources: NIST's JARVIS table, and the 2024 Oliynyk edition. The
  2024 edition differs from CBFV's copy on 8 of the 13 properties the features need.

---

## 1.R.3 What it is now

The rebuilt pipeline differs from the archival one in five ways that matter for the numbers:

1. **One definition of "the same material".** Rows are grouped by a canonical composition key
   (`hydms.data.canonical.group_keys`), never by the formula string. The split is 893 / 131 / 255
   rows over 780 / 111 / 224 compositions. It cannot match the published 896 / 136 / 247, because
   those came from formula strings.
2. **Nothing is scored on data that chose it.** Feature selection, hyperparameter search (Optuna,
   25 trials, 3 inner folds) and early stopping all run inside five group-aware outer folds. The
   outer fold's rows reach none of them.
3. **The label screen drops rows instead of rewriting them.** The archival script rewrote flagged
   labels on every split, training included. CleanLab now only removes flagged *training* rows. It
   rewrites no label on any split, and a check run on every call (the same detector gate HG-1 uses)
   confirms that validation and test rows leave it byte-identical.
4. **Every prediction carries an interval.** The model is a CatBoost multi-quantile regressor
   (10th, 50th and 90th percentiles) with a split-conformal correction for 80 % coverage. It is
   calibrated on 172 training rows carved out *before* fitting, so the correction is not computed
   on rows the model has already fitted.
5. **Every answer carries a domain verdict.** A prediction is returned with its interval and a set
   of screens, or refused with a reason code (`docs/REFUSALS.md`). The screens are the trained
   ranges, a physical capacity ceiling, a cross-family capacity rule, the measured transfer of the
   candidate's family, and an Element Mover's Distance to the nearest training composition.

Nine executable gates guard this (`python -m hydms.gates list`), and all nine passed at promotion
of artifact version `v3` on 2026-09-12. HG-1 fails the build if any of the thirteen leaks
reappears.

---

## 1.R.4 Published and corrected numbers, side by side

The corrected numbers are lower. That is the expected result of removing the leaks (PRD risk R4),
not a regression. They are also **not like-for-like** with the published ones: the split, the
feature set and the model all changed, because each was implicated in a leak. The right column
names the leaks that stood between the two figures.

| Quantity | As published | Now | Why they differ |
|---|---|---|---|
| R², the modelling procedure | Ensemble validation **0.939** (CI 0.898–0.961) | Procedure score **0.748** [0.689, 0.799], out-of-fold over five group-aware outer folds | L2 (members chosen on the scoring set), L4–L7 (no nesting, early stopping on the scored fold, selection before CV, no grouping). The published CI inherits the same contradiction as its point estimate |
| R², one model on held-out rows | Ensemble test **0.892** | Artifact score **0.707** on 254 held-out test rows | L1 (test chose the stopping iteration), L6, L8 (materials straddling the split). The committed `stacking_results.csv` records **0.376** for the ensemble, so the published figure is not the pipeline's own either |
| MAE, one model on held-out rows (wt%) | **0.223** | **0.312** (RMSE 0.542) | As above |
| R², an alloy family never trained on | Not measured (L13 made it impossible) | Transfer score **0.256**, macro over 10 families | Not a correction: a new measurement (§1.R.5) |
| Interval coverage, nominal 80 % | No interval | **0.780** on the test rows, mean width 0.863 wt% | New. Without the conformal correction the same quantile heads cover 0.658 |
| Features | 22 | 14 | L6. See §1.R.6 |
| Distinct materials | 1,149 | 1,115 (1,149 formula strings) | Both correct; they count different things. Grouping uses the 1,115 |
| Elements | 54 | 55 | Counted from every parsed composition |

The out-of-fold interval (0.689–0.799) is **too narrow**. Five models with overlapping training
sets leave K-fold CV without an unbiased variance estimator (Bengio & Grandvalet 2004). It prices
the sampling of materials, not of folds. The five per-fold scores span 0.688–0.832.

The procedure score and the artifact score differ by 0.04. Two reasons: the deployed model grows on
701 rows after the calibration carve and the screen, while each CV fold was cut from 893; and the
two readings score different rows.

For scale only: the HyStor authors' own HYST model reports MAE 0.29 wt% and R² 0.79 (Wilson et al.
2024). That is a different data release, split and protocol, so it bounds plausibility and is not a
comparison.

---

## 1.R.5 Leave-one-alloy-class-out

A random split measures interpolation: every family is present in training. The inverse-design
question is extrapolation: will the model rank a composition from a family it has not seen?
Beltrame et al. (2025) found that hydride models trained on a larger dataset (806 entries) were
accurate within a family, e.g. AB₂, and generalised poorly across families. This is the
measurement that tests the same claim here. Each of the ten families is held out in turn, and the
model is tuned and fitted on the other nine with the same nested protocol (`reports/loco/loco.md`).

| Protocol | R² | What it measures |
|---|---|---|
| Random group-aware split (per-fold mean, same protocol) | **0.746** | Interpolation |
| Leave-one-alloy-class-out, macro over 10 families | **0.256** | Extrapolation to a new family |
| Leave-one-alloy-class-out, weighted by rows | 0.197 | The same, weighted by how many rows each family brought |

| Family | R² | MAE (wt%) | Rows | Compositions |
|---|---|---|---|---|
| SS | 0.778 | 0.619 | 73 | 69 |
| A₂B | 0.726 | 0.315 | 29 | 21 |
| LEA | 0.500 | 0.240 | 19 | 19 |
| AB | 0.421 | 0.303 | 59 | 55 |
| AB₂ | 0.304 | 0.321 | 260 | 207 |
| MIC | 0.280 | 0.469 | 87 | 81 |
| MEA | 0.093 | 0.512 | 76 | 69 |
| AB₅ | 0.037 | 0.310 | 143 | 123 |
| HEA | −0.072 | 0.250 | 51 | 47 |
| Mg | −0.508 | 1.656 | 96 | 89 |

**The result reproduces the literature's warning on this dataset.** The model does not transfer
reliably to an unseen family. Four families score an R² at or below 0.12, and two below zero, i.e.
worse than predicting the held-out family's own mean. Small families (LEA, 19 rows; A₂B, 29) give
scores with wide sampling error and should be read with their row counts.

**The transfer score also moves between runs with the same seed, and the table above is the second
run.** The protocol was run twice with seed 42, committed on 2026-09-06 (`7149c4a`) and 2026-09-25
(`d8734ec`). Those are commit dates. Neither run recorded when it started: the run record gained a
run date only afterwards (card #105), and a commit date is not used as one. Seven of the ten
family scores came back identical. Three moved: MEA 0.113 → 0.093, SS 0.763 → 0.778, and Mg
−0.338 → −0.508. The macro average moved 0.273 → 0.256. Neither run is the right one: the
difference is run-to-run variation the fixed seed does not remove, and its source has not been
isolated yet (card #104). The ordering of the families, and every claim above that depends on it,
is the same in both runs.

This is why the delivered model refuses rather than guesses outside its domain. The per-family
transfer score feeds one of the domain screens, and inverse-design candidates are to be ranked by
the lower confidence bound, not the mean (PRD risk R1).

---

## 1.R.6 The published 22 features and the 14 now used

Feature selection was re-run inside the five outer folds (`reports/feature_selection/old_vs_new.md`).
The published set is now the **consensus 14**: the features all five folds selected.

- **Kept 14 of 22, dropped 8, added none.** The candidate pool was the published 22, so no feature
  could be added. Widening the pool to all 2,685 available descriptors is not a correction of this
  chapter.
- **One feature was dropped for cost, not relevance.** `dev_Gordy_electonegativity` cannot be
  computed from the citable 2024 Oliynyk table for 21 of the 55 elements. Those are mostly the
  rare earths that dominate AB₅, and keeping the feature would cost **266 of 1,279 rows (20.8 %)**.
  Offered that feature back, the selector rejects it on the rows it survives on.
- **Seven were dropped because the folds disagreed about them.** Every one of the 21 candidates is
  selected by at least one fold, but only 14 by all five. A feature one fold in five selects says
  more about which compositions were held out than about hydrogen storage. So "the 22 features" was
  never a stable object, and the 14 are a consensus, not a discovery.
- **The inverse-design premise survives.** Thirteen of the 14 are fraction-weighted element
  statistics; the fourteenth is temperature. A candidate is still featurised by a forward
  calculation, and descriptors are never inverted (PRD §2.3).
- **One caveat carries forward.** `dev_voro_coord_divi_mol_vol` is selected unanimously but is
  computed from a placeholder value for gadolinium, which is in 18 of 1,279 rows (1.4 %). It was
  kept, because removing a unanimously selected feature after seeing the result is the kind of
  decision this revision exists to remove, and it is stated here instead.

---

## 1.R.7 Limitations and future work

### Why the worst family is as bad as it is

**Mg fails partly by construction, not only by chemistry.** Over the 893 training rows, Mg-based
alloys have a median capacity of **3.80 wt%** against **1.60** for all other families combined, and
a maximum of **7.19** against a non-Mg maximum of **5.19**. **21 of the 96 Mg rows lie above the
entire non-Mg range**, and 43 lie above its 99th percentile (3.90 wt%). A gradient-boosted tree
predicts averages of training targets in its leaves, so it cannot produce a value above the range it
was trained on. Hold out the only high-capacity family, and those 21 rows are unreachable before any
question of learning arises. That is the model class meeting the fold design, and no tuning moves
it.

**The data omits a variable that controls the target.** Where the pressure–composition plateau
slopes, the measured maximum capacity depends on the upper pressure of the measurement. This
dataset records temperature but not pressure. High-entropy alloys and BCC solid solutions are
intrinsically prone to sloping plateaus. That limits any model built from these columns, and it is
a physical explanation for the label noise CleanLab flags.

**The near-ambient regime is the weakest.** Out-of-fold, rows at 195–293 K score R² **0.187**
(95 % CI −0.012 to 0.423). The four warmer temperature bins score 0.66–0.77. The interval includes
zero, and this is the regime a practical storage material must operate in.

**The interval is wide relative to the signal.** At 80 % coverage the calibrated band averages
0.863 wt%, about ±0.43 wt%. The model discriminates between families far better than between
small composition changes within one. For a screening tool that feeds an optimiser, that is usable
if it is stated. It is not precision.

The model predicts **material** capacity at maximum. It predicts neither usable capacity across a
pressure–temperature swing nor system capacity, and none of its outputs is comparable with a DOE
system target without that two-step qualification.

### Future work, ranked

All four items are composition-only, so they keep the forward-featurisation property inverse design
rests on.

1. **Re-test the Miedema descriptors under the corrected merge.** The Miedema formation enthalpies
   (`Miedema_deltaH_ss_min`, `_inter`, `_amor`) were in the archival candidate pool but joined by
   the positional merge (L9). Their failure to survive selection is therefore not evidence that they
   are uninformative; they may have been attached to the wrong compositions. Physically, they are
   the right quantity: Miedema's rule of reversed stability is the semi-empirical account of the
   cross-family behaviour the model is missing.
2. **Predict H/M and convert to wt% analytically.** H/M is bounded at roughly 0.5–2.5 across every
   family here, Mg included, so a held-out family stays inside the trained range, and the exact
   conversion does the extrapolation. No mean atomic mass is among the 14 features, so the model has
   never had the denominator of the wt% formula, and trees cannot divide.
3. **Add composition-derived proxies for structure**: mean atomic mass, atomic-size mismatch δ,
   valence electron concentration and mixing entropy. Real structural descriptors (C14 vs C15 Laves
   phase, lattice parameters) are predictive but unknown for an alloy not yet made, so using them
   would forfeit inverse design.
4. **A base learner that can extrapolate.** A linear or physics-informed base model with trees on
   the residuals addresses the range ceiling directly rather than around it.

**Considered and rejected:**
- *Generative models (VAE, GAN, diffusion).* Published materials generative models train on 10⁴–10⁶
  examples; this dataset has 1,279.
- *Graph neural networks and foundation models.* Descriptor-based models remain competitive below
  about 10⁴ samples (Matbench).
- *More hyperparameter trials.* They cannot move the range ceiling that causes the worst family.

**The protocol matters more than the list.** Each leave-one-alloy-class-out run costs about four
hours, and each run consumes the held-out families' independence. Trying change 1, looking, and then
trying change 2 would be selecting on the held-out families: leak L2 one layer up. So the whole
change set is fixed first, the acceptance rule is written before the run, and the protocol is run
**once**, with old and new numbers both reported.

---

## 1.R.8 Evidence

Every number in this section comes from a committed file the pipeline produced. The artifact score
and the test coverage were measured by gates AC-1 and AC-3 on the promoted version `v3`. They are
copied verbatim from its sealed manifest into `reports/model/artifact-gates.json`, which records the
manifest's SHA-256, and tabulated in `reports/model/artifact-score.csv` (card #103). The model
itself is still gitignored, so a fresh clone can check the recorded numbers but cannot re-score the
model (card #7 owes a portable artifact).

| Claim | Source |
|---|---|
| Published 0.939 / 0.892 / 0.223, CI 0.898–0.961 | `REPORT.md` §4.2–4.3 |
| Twelve disagreements, including the 0.344 / 0.377 / 0.376 ensemble and the t-test | `docs/REPORT-RECONCILIATION.md` (generated, byte-checked) |
| Thirteen leaks and their sites | `docs/PHASE-H-RUNBOOK.md` §1 |
| Three disqualifying findings | `docs/FREEZE.md` §Why |
| Split 893 / 131 / 255 over 780 / 111 / 224 compositions | card #13; `tests/data/test_splits.py` |
| Procedure score 0.748 [0.689, 0.799]; MAE 0.333; per-fold range; temperature bins | `reports/model/evaluation.md`, `evaluation-metrics.csv`, `evaluation-subgroups.csv` |
| Conformal correction +0.0374 (log1p), 172 calibration rows, 80 % nominal | `reports/model/conformal.csv` |
| Artifact score R² 0.7071, RMSE 0.5420, MAE 0.3117 on 254 test rows | gate AC-1; `reports/model/artifact-score.csv` (from `artifact-gates.json`, generated, byte-checked) |
| Coverage 0.7795 (raw 0.6575), mean width 0.8630 wt% | gate AC-3; `reports/model/artifact-score.csv` |
| Transfer score 0.256 macro, 0.197 weighted; per-family table; random-split 0.746 | `reports/loco/loco.md`, `loco-summary.csv`, `loco-per-class.csv` |
| 22 → 14 features, 266-row Gordy cost, fold stability | `reports/feature_selection/old_vs_new.md` and its CSVs |
| Gadolinium placeholder, 18 rows | card #83; `reports/feature_selection/old_vs_new.md` |
| Mg arithmetic (3.80 / 1.60 median, 7.19 / 5.19 max, 21 and 43 rows) | recomputed on 2026-09-24 from `reports/model/model-out-of-fold.csv` (target, canonical key) joined to `hydms.data.canonical.alloy_class_table(load_hydride_data())`; the class counts match `loco-per-class.csv` exactly |
| Element tables and the licence | `hydms/descriptors/element_data.py`, `data/SOURCES.md` |

### References

- Beltrame, G.; Dematteis, E.; Stavila, V.; Rizzi, P.; Baricco, M.; Palumbo, M. (2025).
  Application of Machine Learning and Data Augmentation Algorithms in the Discovery of Metal
  Hydrides for Hydrogen Storage. *Metals* **15**, 1221.
  [doi:10.3390/met15111221](https://doi.org/10.3390/met15111221)
- Bengio, Y.; Grandvalet, Y. (2004). No Unbiased Estimator of the Variance of K-Fold
  Cross-Validation. *Journal of Machine Learning Research* **5**, 1089–1105.
- Wilson, N. *et al.* (2024). HyStor: An experimental database of hydrogen storage properties.
  *International Journal of Hydrogen Energy*.
  [doi:10.1016/j.ijhydene.2024.09.390](https://doi.org/10.1016/j.ijhydene.2024.09.390)
