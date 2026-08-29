# Machine Learning for Hydride Property Prediction

**Confidence**: 🟢 Medium-high — methodology claims are cited; treat uncited numbers as indicative.

The governing fact: **this is a ~1,279-row tabular regression problem with fewer distinct chemistries than rows.**
Almost every wrong answer in this domain comes from ignoring that.

## Featurization

**Composition-based only** — no structure. The pipeline uses CBFV (Magpie + JARVIS) plus matminer
(Miedema, WenAlloys), producing `avg_*`, `dev_*`, `range_*` statistics over elemental properties weighted by
stoichiometry.

- **Magpie** — the standard elemental-property descriptor set ([Ward et al. 2016, *npj Comput. Mater.* 2, 16028](https://doi.org/10.1038/npjcompumats.2016.28)).
- **matminer** — featurizer library ([Ward et al. 2018, *Comput. Mater. Sci.* 152, 60](https://doi.org/10.1016/j.commatsci.2018.05.018)).

**What these descriptors cannot encode**, and must be stated as limitations:
1. **No structure.** Phase (C14 vs C15 Laves), lattice parameters, interstitial site geometry — all invisible.
   Two polymorphs with identical composition are identical to the model.
2. **Many-to-one.** Composition → descriptor is not invertible. This forbids feature-space inverse design
   (see `modules/generative-ai-inverse-design.md`).
3. **No processing history.** Ball-milling, annealing, activation state all affect measured capacity and are absent.

## Model families — why gradient-boosted trees win here

Not fashion; the evidence is direct:

- [Grinsztajn, Oyallon & Varoquaux, NeurIPS 2022](https://neurips.cc/virtual/2022/poster/55627) — 45 datasets,
  tree-based models remain state-of-the-art on medium-sized (~10k sample) tabular data even before counting
  their speed advantage, traced to differing inductive biases.
- [Dunn et al. 2020, *npj Comput. Mater.* 6, 138](https://doi.org/10.1038/s41524-020-00406-3) — Matbench;
  descriptor-based classical ML stays competitive below ~10⁴ samples, graph/deep networks pull ahead above it.
- [De Breuck et al. 2021, *npj Comput. Mater.* 7](https://doi.org/10.1038/s41524-021-00552-2) — MODNet, built
  specifically because mainstream ML needs large data; beats graph networks on small datasets.

At 1,279 rows, CatBoost/ExtraTrees/stacking is the correct choice. Deep nets, GNNs, transformers and
"materials foundation models" are not obviously better here and carry far more overfitting risk. If asked to
add one, the honest answer is usually *no* — and to spend the effort on validation instead.

## Validation pitfalls — the section that matters most

For a thesis, these determine whether results survive examination.

1. **Random splits leak.** Duplicate and near-duplicate compositions across train/test inflate scores.
   This repo already splits on **unique formulae**, which is genuinely better than much published hydride ML.
2. **Formula-disjoint is still interpolation.** A formula-disjoint random split measures interpolation across
   the *sampled* chemical space, not extrapolation to new families. [Li et al. 2025, *Commun. Mater.* 6, 9](https://doi.org/10.1038/s43246-024-00731-w)
   analysed 700+ OOD tasks and found heuristic criteria "mostly test interpolation rather than true extrapolation".
3. **Cross-family generalisation fails.** [Beltrame et al. 2025, *Metals* 15, 1221](https://doi.org/10.3390/met15111221)
   expanded a hydride dataset ~400 → 806 entries and found high accuracy only when training and testing *within*
   one hydride family (e.g. AB₂), with **limited generalizability across material classes**. Data augmentation
   helped only on the smallest datasets and not in underrepresented pressure regimes.
   → **Report leave-one-alloy-class-out CV alongside random-split R², and expect it to be much worse.**
   [Durdy et al. 2022, *Digital Discovery* 1, 763](https://doi.org/10.1039/d2dd00039c) covers leave-one-cluster-out.
4. **Selection and tuning inside the CV loop.** Feature selection (Boruta, SHAP, VIF) and hyperparameter search
   run on the full training set before splitting leak information. The defensible pattern is nested CV, or at
   minimum an explicit statement that selection preceded splitting and what that costs.
5. **Small test sets are high-variance.** At n=239, a test R² of 0.916 has a wide confidence interval.
   Report intervals (bootstrap) rather than a bare point estimate.
6. **Tuning against the test set.** Reporting the best of 13 models × 100 Optuna trials by test score turns the
   test set into a validation set. Model selection must use validation; test is touched once.

## Label noise and outliers

Experimental hydride data is noisy — different labs, methods, purities, activation states. Confident learning
([CleanLab](https://doi.org/10.1613/jair.1.12125), Northcutt, Jiang & Chuang 2021, *JAIR* 70, 1373) estimates
label noise and flags suspect entries; this pipeline uses it to drop ~10 train / 5 val / 8 test samples.
**There is a physics explanation for that noise, and it is better than "some experiments are wrong".** Sloping
PCT plateaus make measured capacity depend on the measurement's upper pressure, and the dataset carries
temperature but **not** pressure. Multi-element alloys — every HEA and BCC solid solution here — are
intrinsically prone to sloping plateaus. See `modules/metal-hydride-families.md`. Activation state and
processing history are a second unobserved confounder that composition-based features cannot see.

Be careful: removing "outliers" that are actually real measurements in underrepresented regimes will flatter
metrics while making the model worse where it matters. Report what was removed and why.

## Uncertainty and applicability domain

Not optional for a thesis that makes recommendations:
- **Conformal prediction** — distribution-free finite-sample coverage on any point model
  ([Angelopoulos & Bates 2023](https://doi.org/10.1561/2200000101)); [MAPIE](https://github.com/scikit-learn-contrib/MAPIE), [crepes](https://pypi.org/project/crepes/).
- **CatBoost native** — `RMSEWithUncertainty`, `MultiQuantile`, virtual ensembles ([docs](https://catboost.ai/docs/en/concepts/loss-functions-regression)).
- **NGBoost** — [Duan et al., ICML 2020](https://proceedings.mlr.press/v119/duan20a.html).
- **Applicability domain** — Element Mover's Distance to training set ([ElMD](https://github.com/lrcfmd/ElMD));
  [DiSCoVeR](https://doi.org/10.1039/d1dd00028d) trades performance against novelty.

## Published ML-on-hydride work

Dataset sizes in this field are small; be honest about it rather than implying otherwise.
- **HyStor** — 1,282 alloys with max capacity at a given absorption temperature, 54 elements, 200–800 K,
  adding LEA/MEA/HEA classes ([Wilson et al. 2024, *Int. J. Hydrogen Energy* **90**, 460–469](https://doi.org/10.1016/j.ijhydene.2024.09.390)).
- **ML-HydPARK** — cleaned CSV derived from DOE's HydPARK ([Zenodo](https://zenodo.org/records/7324809)).
- [Prediction of hydrogen storage in metal hydrides and complex hydrides, *Int. J. Hydrogen Energy* 2024](https://www.sciencedirect.com/science/article/abs/pii/S0360319924053242) — supervised ML approach.
- [FIND platform, Lu et al. 2025, *J. Mater. Inform.*](https://doi.org/10.20517/jmi.2025.56) — forward/inverse
  navigation for hydrogen storage alloys, ~6,000 records, VAE + genetic algorithm.
- [Liu et al. 2025, "Machine learning-driven alloy digital design for hydrogen storage: a review",
  *Digital Twin* **2**](https://doi.org/10.1080/27525783.2025.2511889).

A test R² of ~0.9 on a formula-disjoint split is a good result at this scale — but it is a statement about
interpolation within the sampled space, and should be presented that way.
