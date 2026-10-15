# This Project: HydMS

**Confidence**: 🟢 High — read directly from the repo's own `README.md`, `REPORT.md` and `Machine_Model/src/` on 2026-08-29.

> **2026-10-15:** `Machine_Model/` was removed (card #107; readable at commit `4348f6ff96`). The
> pipeline below is history. The code is `hydms/`, the data `data/raw/`, and REPORT.md with the
> tables that disprove it is `evidence/as-published/`.

Master's thesis, Faculty of Metallurgical and Materials Engineering, Shiraz University.
Predicting **maximum H₂ storage capacity (wt%)** of hydride alloys from **chemical formula + temperature alone**.

## The pipeline as actually built

Scripts in `Machine_Model/src/`, run in this order:

| # | Script | Does |
|---|---|---|
| 1 | `merge_datasets.py` | Merge HyStor + ML-HYDPARK |
| 2 | `log_transform_target.py` | Log-transform H₂ wt% target (back-transform via `expm1`) |
| 3 | `extract_features_cbfv.py` | CBFV featurisation (Magpie + JARVIS) + matminer (Miedema, WenAlloys) → 282 features |
| 4 | `CleanLab.py` | Confident-learning label-noise removal |
| 5a | `Boruta_FeatEng.py` | Boruta + SHAP |
| 5b | `Feature_selection.py` | VarianceThreshold → correlation → RF importance → Boruta → SHAP + VIF |
| 6 | `split_data.py` | Stratified split on **unique formulae** |
| 7 | `benchmark_model_selection.py` | 13 regressors + Optuna + stacking |
| 8 | `Catboostmodel.py` | Dedicated CatBoost optimisation |

## Numbers to get right

- **Dataset**: 1,279 samples after merge and cleaning. 282 features → **22 selected**.
- **Split**: 896 / 136 / 247 raw → **886 / 131 / 239** post-CleanLab (train / val / test).
- **CV**: 5-fold `StratifiedKFold` on the training set.
- **Tuning**: Optuna, 100 trials, TPE sampler, median pruner — for ExtraTrees, CatBoost, MLP, Ridge, SVR.
- **Scaling**: `RobustScaler` inside a scikit-learn `Pipeline` — **not** `StandardScaler`.
- **Ensemble**: `StackingRegressor` over the top-4 by `Val_Weighted_Orig`; meta-learner is a tuned Ridge.
- **Weighted score**: `0.6 × R²_orig + 0.4 / MAE_orig`.

### Headline results

| Model | Val R² | Test R² | Test MAE |
|---|---|---|---|
| Stacking ensemble | 0.939 | 0.892 | 0.229 wt% |
| ExtraTrees (best single) | 0.933 | **0.916** | 0.204 wt% |
| CatBoost (Optuna) | 0.969 | 0.951 | — |

**Do not quote these as generalisation estimates without a caveat.** They are formula-disjoint random-split
numbers, which measure interpolation across the sampled chemical space — not extrapolation to new alloy
families. See `modules/ml-for-hydrides.md` and the leave-one-class-out point in
`modules/generative-ai-inverse-design.md`.

## The 22 features

Dominated by one: `avg_polzbl_divi_atom_mass` (SHAP 0.172, ~4.5× the next). Then `dev_Zunger_radii_sum` (0.038),
`dev_Pauling_Electronegativity` (0.029), `avg_valence_d` (0.026), `avg_is_alkaline` (0.019).
`temperature(K)` ranks 21st by SHAP (0.001) — worth flagging as a discussion point, since temperature is
physically decisive for *where on the PCT isotherm* a measurement sits.

All 22 are composition-averaged statistics (`avg_*`, `dev_*`, `range_*`) plus temperature. They carry
**no structural information** — the composition→descriptor map is many-to-one and non-invertible.

## Working on this repo

- Prose conventions: `README.md` and `REPORT.md` at root document the built model. `research/` holds
  literature reviews and design memos for work that does not exist yet.
- `.claude/` is gitignored — skills and research notes there are not tracked.
- The datasets live in `data/raw/`; committed evidence in `reports/`; REPORT.md as published in `evidence/as-published/`.

## How to be useful here

1. **Check the claim against the repo before repeating it.** The report is detailed and specific; guessing
   at numbers when they are written down two directories away is the main failure mode.
2. **Respect the small-N regime.** Almost every "just use a neural network / transformer / foundation model"
   instinct is wrong at 1,279 rows. See `modules/ml-for-hydrides.md`.
3. **Separate material-level from system-level capacity.** A wt% figure for an alloy is not a storage-system
   figure and cannot be compared to DOE system targets. See `modules/hydrogen-storage-fundamentals.md`.
4. **This is a thesis.** Defensibility and honest error bars beat a higher R². Where a result is fragile,
   say so — that is a contribution, not a weakness.
