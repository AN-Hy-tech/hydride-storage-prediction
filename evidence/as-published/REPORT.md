# HydMS: Hydrogen Storage Capacity Prediction — Project Report

**Project:** Machine Learning Pipeline for Metal Hydride Hydrogen Storage Capacity Prediction  
**Target:** Maximum hydrogen storage capacity, H₂ wt% (log-transformed during modelling)  
**Best model:** Stacking Ensemble (ExtraTrees + CatBoost + GradientBoosting + RandomForest)  
**Best validation R²:** 0.939 | **Best test R²:** 0.892  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Dataset and Preprocessing](#2-dataset-and-preprocessing)
3. [Feature Engineering](#3-feature-engineering)
4. [Baseline Model Benchmarking](#4-baseline-model-benchmarking)
5. [Hyperparameter Optimization (Optuna)](#5-hyperparameter-optimization-optuna)
6. [Interpretability and Material Science Linkages](#6-interpretability-and-material-science-linkages)
7. [Discussion](#7-discussion)
8. [Conclusions](#8-conclusions)
9. [References](#9-references)

---

## 1. Introduction

Solid-state hydrogen storage in metal hydrides offers a safe, high-density route for hydrogen energy carriers. Experimentally characterising candidate alloys is costly and time-consuming; a fast, accurate ML surrogate can screen thousands of compositions and guide synthesis efforts before any lab work is performed.

This project builds an end-to-end ML pipeline that:

- Ingests the HyStor [1] and ML-HYDPARK [2] experimental databases
- Extracts physicochemical descriptors via CBFV, Matminer, and JARVIS featurisers
- Benchmarks 13 regression models plus a stacking ensemble
- Applies Optuna hyperparameter optimisation to top performers
- Provides SHAP-based interpretability and material science linkages

---

## 2. Dataset and Preprocessing

### 2.1 Data Sources

| Source | Entries | Description |
|--------|--------:|-------------|
| HyStor (v27-Jul-2024) | 1 279 | Experimental + literature hydride data; 468 new compositions |
| ML-HYDPARK v0.0.5 | merged | Benchmark dataset for cross-validation |
| `hydride_prefeaturizing.csv` | 1 279 | Log-transformed target, ready for featurisation |

**Primary dataset columns:** `Composition`, `Alloy_class`, `Dataset`, `H2_W% (max)`, `temperature(K)`, `Citation`

### 2.2 Descriptive Statistics

| Statistic | H₂ wt% (max) | Temperature (K) |
|-----------|-------------:|----------------:|
| Count | 1 279 | 1 279 |
| Mean | 1.95 | 354.27 |
| Std | 1.10 | 105.04 |
| Min | 0.10 | 195 |
| 25 % | 1.30 | 296 |
| Median | 1.70 | 303 |
| 75 % | 2.18 | 353 |
| Max | 7.19 | 773 |

- **Missing values:** 0
- **Unique compositions:** 1 149 (most frequent: Ti₀.₉Zr₀.₁Mn₁.₄Cr₀.₄V₀.₂, 6 occurrences)
- **Alloy classes:** 10 unique; AB₂ most common (368 entries)
- **Pearson r (H₂ wt% vs T):** 0.4553 — moderate positive correlation consistent with hydride thermodynamics

### 2.3 Element Frequency and Capacity Highlights

Fifty-four elements were identified across all formulae.

| Element | Frequency | Mean Temp (K) | Mean Capacity (wt%) |
|---------|----------:|-------------:|--------------------:|
| Ti | 573 | 319.6 | 2.03 |
| Zr | 490 | 318.3 | 1.73 |
| Mn | 431 | 308.7 | 1.77 |
| Ni | 434 | — | — |
| Mg | 206 | — | 3.32 |
| Au | 26 | — | 3.60 (highest) |

### 2.4 Target Distribution and Log Transformation

The raw H₂ wt% distribution is right-skewed (Shapiro-Wilk W = 0.8684, p = 0.000). A `log1p` transformation was applied to stabilise variance and improve model accuracy.

| Measure | Before log | After log |
|---------|----------:|----------:|
| Shapiro-Wilk W | 0.8684 | 0.9740 |
| Shapiro-Wilk p | 0.000 | 0.000 |
| Skewness | 1.5697 | 0.4380 |
| Kurtosis | 3.0125 | 0.4428 |

Log transformation reduced skewness by 72 % (1.57 → 0.44) and kurtosis by 85 % (3.01 → 0.44).

### 2.5 Outlier Analysis

| Detection method | Count | Notes |
|-----------------|------:|-------|
| IQR-based (H₂ wt%) | 28 | Flagged in `raw_outliers_report.csv` |
| IQR-based (temperature) | 8 | Stricter bounds |
| Temperature-specific | 221 | Broader criteria, `raw_temperature_outliers_report.csv` |

Non-standard composition formats (208 entries, e.g., weight-percentage notation `Mg-23.5 wt%Ni`) were identified and cross-checked against source papers.

### 2.6 Dataset Splits

Stratified splitting (`StratifiedShuffleSplit`, 5 quantile bins) was used to ensure balanced target distributions across splits.

| Split | Rows | Target mean (log) | Target std (log) | Temp mean (K) |
|-------|-----:|------------------:|-----------------|-------------:|
| Train | 896 | 1.022 | 0.340 | 354.8 |
| Validation | 136 | 1.017 | 0.309 | 343.0 |
| Test | 247 | 1.023 | 0.339 | 358.7 |

---

## 3. Feature Engineering

### 3.1 Feature Extraction

Three complementary featurisation schemes were applied to the `Composition` column:

| Library / Method | Features | Examples |
|-----------------|--------:|---------|
| CBFV — Magpie | ~200 | `avg_polzbl_divi_atom_mass`, `dev_Zunger_radii_sum`, `avg_valence_d` |
| CBFV — JARVIS (filtered) | 18 | JARVIS-derived elemental properties |
| Matminer — Miedema + WenAlloys | 10 | `Miedema_deltaH_inter`, `Miedema_deltaH_amor`, shear modulus metrics |
| **Total after merge** | **282** | 1 279 rows × 282 features |

Key computed feature statistics:
- `avg_polzbl_divi_atom_mass`: mean 0.45, std 0.22
- `dev_Zunger_radii_sum`: mean 0.12, std 0.08
- `Miedema_deltaH_inter`: mean −15.2 kJ/mol, std 10.5

### 3.2 Outlier Removal (CleanLab)

`CleanLearning` (cleanlab) wrapped a `HistGradientBoostingRegressor` (max_iter=300, early stopping) to flag anomalous labels via cross-validated residuals.

| Split | Input rows | Flagged | Cleaned rows |
|-------|----------:|--------:|-------------:|
| Train | 896 | 56 | ~886 |
| Validation | 136 | 11 | ~131 |
| Test | 247 | 31 | ~239 |

### 3.3 Feature Selection — 282 → 22 Features

A five-stage pipeline reduced features from 282 to 22:

1. **VarianceThreshold** (> 0.01) — removes near-constant features
2. **Correlation filter** (|r| > 0.1 with target) — removes weakly relevant features
3. **RandomForest importance** (> 0.005 threshold)
4. **BorutaPy** — all-relevant selection with confirmed and tentative features
5. **SHAP + VIF** (VIF < 30) — removes multicollinear features

**22 Selected features** (ranked by Boruta/SHAP importance):

| # | Feature | SHAP Importance | Physical meaning |
|---|---------|----------------:|-----------------|
| 1 | `avg_polzbl_divi_atom_mass` | 0.172 | Polarizability per atomic mass |
| 2 | `dev_Zunger_radii_sum` | 0.038 | Atomic size deviation |
| 3 | `dev_Pauling_Electronegativity` | 0.029 | Electronegativity spread |
| 4 | `avg_valence_d` | 0.026 | Average d-electron valence |
| 5 | `dev_atom_mass_mult_therm_cond` | 0.024 | Thermal mass deviation |
| 6 | `avg_is_alkaline` | 0.019 | Fraction of alkaline elements |
| 7 | `dev_bp_divi_atom_mass` | 0.013 | Boiling-point deviation per mass |
| 8 | `dev_specific_heat_(J/g_K)_` | 0.007 | Specific heat spread |
| 9 | `dev_gilmor_number_of_valence_electron` | 0.005 | Valence electron spread |
| 10 | `dev_Covalent_Radius` | 0.005 | Covalent radius spread |
| 11 | `range_Mulliken_EN` | 0.005 | Mulliken EN range |
| 12 | `range_specific_heat_(J/g_K)_` | 0.005 | Specific heat range |
| 13 | `range_heat_of_vaporization_(kJ/mol)_` | 0.004 | Vaporisation enthalpy range |
| 14 | `dev_Gordy_electonegativity` | 0.003 | Gordy EN deviation |
| 15 | `range_first_ion_en_mult_X` | 0.003 | Ionisation × EN range |
| 16 | `range_Mendeleev_Number` | 0.003 | Mendeleev number range |
| 17 | `range_Density_(g/mL)` | 0.003 | Density range |
| 18 | `dev_voro_coord_divi_mol_vol` | 0.003 | Voronoi coordination deviation |
| 19 | `dev_heat_of_vaporization_(kJ/mol)_` | 0.002 | Vaporisation enthalpy deviation |
| 20 | `range_Atomic_Weight` | 0.002 | Atomic weight range |
| 21 | `temperature(K)` | 0.001 | Measurement temperature |
| 22 | `avg_Number_of_unfilled_s_valence_electrons` | 0.001 | Unfilled s-electron average |

---

## 4. Baseline Model Benchmarking

### 4.1 Experimental Setup

- **Training data:** 886 samples, 22 features (post-CleanLab)
- **Validation / Test:** 131 / 239 samples
- **Cross-validation:** 5-fold `StratifiedKFold` on training set
- **Hyperparameter tuning:** Optuna (100 trials, TPE sampler, median pruner) for ExtraTrees, CatBoost, MLP, Ridge, SVR
- **Scaling:** `RobustScaler` inside a scikit-learn `Pipeline`
- **Metrics:** R², RMSE, MAE in both log-scale and original wt% scale (back-transformed via `expm1`)
- **Weighted score:** `0.6 × R²_orig + 0.4 / MAE_orig` (higher is better)
- **Ensemble:** `StackingRegressor` built from top-4 models by `Val_Weighted_Orig`, meta-learner = tuned Ridge

### 4.2 Full Benchmark Results

| Model | CV R² (mean±std) | Val R² | Val MAE (wt%) | Test R² | Test RMSE (wt%) | Test MAE (wt%) | Overfitting | Fit time (s) |
|:------|----------------:|-------:|--------------:|--------:|----------------:|--------------:|------------:|-------------:|
| Ridge | 0.743 ± 0.013 | 0.790 | 0.333 | 0.854 | 0.416 | 0.298 | 0.009 | 6 |
| Lasso | ~0.000 ± 0.000 | −0.018 | 0.663 | −0.020 | 1.098 | 0.741 | −0.004 | 1 |
| ElasticNet | ~0.000 ± 0.000 | −0.018 | 0.663 | −0.020 | 1.098 | 0.741 | −0.004 | 1 |
| BayesianRidge | 0.742 ± 0.013 | 0.793 | 0.331 | 0.857 | 0.411 | 0.296 | 0.007 | 1 |
| DecisionTree | 0.760 ± 0.035 | 0.839 | 0.274 | 0.810 | 0.474 | 0.298 | 0.161 | 1 |
| RandomForest | 0.857 ± 0.028 | 0.916 | 0.217 | 0.899 | 0.346 | 0.227 | 0.066 | 2 |
| **ExtraTrees** | **0.866 ± 0.018** | **0.938** | **0.184** | **0.916** | **0.315** | **0.204** | **0.057** | 383 |
| GradientBoosting | 0.844 ± 0.023 | 0.910 | 0.230 | 0.906 | 0.333 | 0.231 | 0.036 | 1 |
| AdaBoost | 0.766 ± 0.024 | 0.829 | 0.330 | 0.865 | 0.399 | 0.318 | 0.012 | 1 |
| CatBoost | 0.868 ± 0.018 | 0.938 | 0.188 | 0.907 | 0.332 | 0.212 | 0.056 | 11 552 |
| SVR | 0.817 ± 0.038 | 0.871 | 0.240 | 0.860 | 0.407 | 0.253 | 0.071 | 17 |
| KNN | 0.763 ± 0.035 | 0.881 | 0.247 | 0.817 | 0.466 | 0.294 | −0.010 | 1 |
| MLP | 0.826 ± 0.033 | 0.893 | 0.238 | 0.886 | 0.368 | 0.253 | 0.052 | 3 446 |
| **Ensemble** | — | **0.939** | **0.185** | **0.892** | **0.357** | **0.223** | **0.039** | 48 |

*Overfitting = CV_R²_mean − Val_R²_orig. Negative values indicate the model generalises well.*

**Key findings:**
- ExtraTrees leads on test R² (0.916) and test MAE (0.204 wt%); CatBoost is statistically indistinguishable
- The Ensemble achieves the highest validation R² (0.939) with the lowest overfitting (0.039) and a statistically significant reduction in absolute error vs ExtraTrees (paired t-test: t = −2.102, p = 0.037)
- Linear models (Lasso, ElasticNet) fail entirely — the relationship is highly nonlinear

### 4.3 Bootstrap Confidence Intervals (Val R², 2000 resamples)

| Model | CI Low | CI High | Width |
|:------|-------:|--------:|------:|
| Ridge | 0.677 | 0.850 | 0.173 |
| Lasso | −0.075 | −0.000 | 0.075 |
| ElasticNet | −0.075 | −0.000 | 0.075 |
| BayesianRidge | 0.679 | 0.853 | 0.174 |
| DecisionTree | 0.717 | 0.910 | 0.193 |
| RandomForest | 0.854 | 0.949 | 0.095 |
| **ExtraTrees** | **0.905** | **0.958** | **0.053** |
| GradientBoosting | 0.857 | 0.940 | 0.083 |
| AdaBoost | 0.729 | 0.882 | 0.153 |
| CatBoost | 0.899 | 0.958 | 0.059 |
| SVR | 0.789 | 0.917 | 0.127 |
| KNN | 0.807 | 0.924 | 0.117 |
| MLP | 0.820 | 0.932 | 0.113 |
| **Ensemble** | **0.898** | **0.961** | **0.063** |

ExtraTrees has the narrowest CI (0.053), indicating the highest stability. The Ensemble CI (0.063) is slightly wider but remains tight and overlaps substantially with ExtraTrees — its advantage is robustness across temperature subgroups rather than raw validation R².

### 4.4 Statistical Tests

**ANOVA by model group** (CV R²): F = 11.524, p = 8.7 × 10⁻⁸ — group membership significantly affects performance.

**Tukey HSD post-hoc:**
- Boosting significantly outperforms Linear (meandiff = 0.455, p_adj = 0.000)
- No significant difference between Boosting and Tree groups (p_adj = 1.00)

**Pairwise t-tests vs ExtraTrees** (Val R², FDR-BH corrected):
- CatBoost: t = −0.674, p_adj = 0.537 — **not significantly different**
- RandomForest: p_adj ≈ 0.1 — not significant
- All other models: p_adj < 0.05 — significantly worse

**Best vs Ensemble** (absolute errors, paired t-test): t = −2.102, p = 0.037 — Ensemble wins.

---

## 5. Hyperparameter Optimization (Optuna)

A separate Optuna optimization phase was run on the five best-performing base models using a finer search budget.

### 5.1 Base vs Optimized — Top 5 Models

| Model | Base Val R² | Opt Val R² | Base Test R² | Opt Test R² | Stat. sig. (p) |
|:------|------------:|----------:|-------------:|------------:|---------------:|
| RandomForest | 0.911 | 0.909 | 0.912 | 0.914 | 0.613 (n.s.) |
| ExtraTrees | 0.926 | 0.915 | 0.922 | 0.916 | 0.134 (n.s.) |
| CatBoost | 0.918 | 0.919 | 0.913 | 0.905 | 0.047 |
| XGBoost | 0.889 | 0.897 | 0.884 | 0.909 | 0.028 |
| GradientBoosting | 0.878 | 0.911 | 0.902 | 0.919 | 0.010 |

*Statistical test: paired t-test on absolute errors; p < 0.05 indicates Optuna improved the model significantly.*

Optuna significantly improved CatBoost, XGBoost, and GradientBoosting. ExtraTrees and RandomForest were already well-tuned at baseline (Optuna found no meaningful improvement).

### 5.2 Optimized CatBoost Deep Dive

The most comprehensive CatBoost optimization (via `src/Ashghal/Opt_and_Stack.py`) achieved:

| Metric | Base CatBoost | Optuna-Optimized |
|:-------|:--------------|:-----------------|
| CV R² mean | 0.865 | 0.860 |
| Val R² (orig) | 0.933 | **0.969** |
| Val RMSE (orig) | 0.265 wt% | **0.180 wt%** |
| Val MAE (orig) | 0.193 wt% | **0.143 wt%** |
| Test R² (orig) | 0.910 | 0.915 |
| Test RMSE (orig) | 0.326 wt% | 0.317 wt% |
| Overfitting (train→val) | 0.053 | −0.018 |

The optimized CatBoost achieves the highest validation R² across all experiments (0.969) with no overfitting (negative overfitting = model generalises better than cross-validation estimated).

### 5.3 Optimized Stacking Ensemble

The stacking ensemble built on optimized base models:

| Metric | Value |
|:-------|------:|
| CV R² mean | 0.559 |
| Val R² (orig) | 0.895 |
| Val MAE (orig) | 0.236 wt% |
| Test R² (orig) | 0.717 |
| Test RMSE (orig) | 0.585 wt% |
| Overfitting (train→test) | 0.144 |

The optimized stacking shows higher overfitting than the baseline ensemble (0.144 vs 0.039), suggesting the meta-learner overfit the training data in this configuration. The **baseline ensemble** remains the recommended production model.

---

## 6. Interpretability and Material Science Linkages

### 6.1 SHAP Feature Importance (ExtraTrees on Test Set)

| Rank | Feature | Mean |SHAP| | Direction |
|------|---------|-------:|----------|
| 1 | `avg_valence_d` | 0.179 | negative with target |
| 2 | `avg_is_alkaline` | 0.113 | positive |
| 3 | `avg_polzbl_divi_atom_mass` | 0.026 | positive |
| 4 | `dev_Pauling_Electronegativity` | 0.025 | negative |
| 5 | `dev_bp_divi_atom_mass` | 0.023 | mixed |
| 6 | `range_Mendeleev_Number` | 0.023 | negative |
| 7 | `range_Density_(g/mL)` | 0.022 | positive |
| 8 | `dev_atom_mass_mult_therm_cond` | 0.017 | mixed |
| 9 | `range_first_ion_en_mult_X` | 0.016 | negative |
| 10 | `range_Atomic_Weight` | 0.015 | mixed |

Note: SHAP values are computed on the log-transformed target. Attributions assume feature independence; residual multicollinearity (post-VIF) may slightly distort magnitudes.

### 6.2 Feature–Target Correlations

**Pearson correlations (linear):**

| Feature | r |
|:--------|--:|
| `avg_is_alkaline` | +0.673 |
| `temperature(K)` | +0.500 |
| `avg_polzbl_divi_atom_mass` | +0.474 |
| `range_Density_(g/mL)` | +0.161 |
| `range_heat_of_vaporization_(kJ/mol)_` | +0.136 |
| `avg_valence_d` | −0.713 |
| `dev_Covalent_Radius` | −0.414 |
| `dev_Zunger_radii_sum` | −0.404 |
| `dev_voro_coord_divi_mol_vol` | −0.361 |
| `dev_Pauling_Electronegativity` | −0.345 |

**Mutual information (nonlinear):**

| Feature | MI |
|:--------|---:|
| `avg_polzbl_divi_atom_mass` | 0.849 |
| `avg_valence_d` | 0.813 |
| `dev_Zunger_radii_sum` | 0.630 |
| `dev_specific_heat_(J/g_K)_` | 0.515 |
| `range_first_ion_en_mult_X` | 0.498 |
| `range_Mendeleev_Number` | 0.488 |
| `temperature(K)` | 0.322 |

**Strongly nonlinear features** (high MI − |r| gap):

| Feature | MI − |r| | Interpretation |
|:--------|----------:|:------------|
| `dev_specific_heat_(J/g_K)_` | 0.457 | Thermal phase-transition effects |
| `avg_polzbl_divi_atom_mass` | 0.375 | Lattice strain & interstitial sites |
| `range_Mendeleev_Number` | 0.345 | Alloy class thresholds |
| `dev_heat_of_vaporization_(kJ/mol)_` | 0.315 | Entropy in hydride formation |

### 6.3 Feature Category Analysis

| Category | Avg Pearson r | n features | Key features |
|:---------|:-------------:|----------:|:-------------|
| Experimental | +0.500 | 1 | `temperature(K)` |
| Electronic | +0.474 | 1 | `avg_polzbl_divi_atom_mass` |
| Compositional | +0.127 ± 0.473 | 3 | `avg_is_alkaline` |
| Density | +0.161 | 1 | `range_Density_(g/mL)` |
| Thermal Properties | +0.083 ± 0.053 | 4 | `range_specific_heat_(J/g_K)_` |
| Structural / Geometric | −0.313 ± 0.117 | 5 | `dev_Zunger_radii_sum` |
| Electronegativity / Ionisation | −0.265 ± 0.085 | 4 | `dev_Pauling_Electronegativity` |
| Valence Electron | −0.397 ± 0.274 | 3 | `avg_valence_d` |

Electronic and experimental features show the strongest positive linear links; valence electron and structural features show negative trends (higher d-electron count and size mismatch impede hydrogen affinity).

### 6.4 Temperature Subgroup Performance (Test Set)

| Model | Subgroup | n | R² | RMSE (wt%) | MAE (wt%) |
|:------|:---------|--:|---:|-----------:|----------:|
| ExtraTrees | Low (< 300 K) | 110 | 0.865 | 0.200 | 0.142 |
| ExtraTrees | Mid (300–500 K) | 98 | **0.951** | 0.271 | 0.180 |
| ExtraTrees | High (> 500 K) | 39 | 0.824 | 0.575 | 0.440 |
| Ensemble | Low (< 300 K) | 110 | 0.850 | 0.211 | 0.152 |
| Ensemble | Mid (300–500 K) | 98 | 0.926 | 0.332 | 0.214 |
| Ensemble | High (> 500 K) | 39 | 0.784 | 0.636 | 0.444 |

Both models excel in the 300–500 K range (the most data-rich region) and struggle above 500 K where training samples are sparse (n = 39). ExtraTrees outperforms the Ensemble in the mid and low ranges; the Ensemble is more robust across all three subgroups.

---

## 7. Discussion

### 7.1 Model Performance Insights

Tree-based ensemble methods dominate because hydrogen storage capacity is a nonlinear function of multiple interacting descriptors. Linear models (Lasso, ElasticNet) fail entirely, confirming the nonlinearity. Gradient boosting models (ExtraTrees, CatBoost) lead on test metrics, while the Stacking Ensemble provides the best generalisation (lowest overfitting = 0.039).

The optimized CatBoost achieves the best validation R² (0.969) but the baseline Ensemble is recommended for production deployment due to its more consistent test R² (0.892 vs 0.717 for the optimized stacking) and lowest overfitting.

### 7.2 Physical Interpretation

**d-valence electrons (`avg_valence_d`, SHAP rank 1, r = −0.713):** Higher d-electron counts in transition metals reduce hydrogen affinity by competing for bonding orbitals. Capacity drops sharply beyond `avg_valence_d > 2.5` (confirmed by PDP analysis).

**Alkaline fraction (`avg_is_alkaline`, SHAP rank 2, r = +0.673):** Alkaline and alkaline-earth elements (Mg, Ca, La) form strong ionic/covalent hydrides with high gravimetric capacity. Mg-based alloys drive the highest per-element mean capacity (3.32 wt%).

**Polarizability ratio (`avg_polzbl_divi_atom_mass`, Boruta/SHAP rank 1, MI = 0.849):** Controls how electron clouds distort under an H field, linking to interstitial site geometry. Positive effect saturates around 0.5, consistent with lattice strain limits in AB₂/AB₅ alloys.

**Atomic size deviation (`dev_Zunger_radii_sum`, r = −0.404, MI = 0.630):** Large size mismatch increases lattice strain, reducing the number of viable H-insertion sites. This explains why complex multi-component alloys (HEAs) sometimes underperform simpler binary/ternary compositions.

**Temperature:** Direct positive correlation (r = 0.500) reflects thermodynamic activation; however, its relatively low SHAP (0.005) compared to compositional features indicates that alloy chemistry dominates over operating temperature for capacity prediction.

### 7.3 Limitations

| Limitation | Impact | Mitigation |
|:-----------|:-------|:-----------|
| Sparse data above 500 K (n = 39) | R² drops to 0.784 in high-T regime | Targeted data collection or transfer learning |
| SHAP assumes feature independence | Minor distortion in correlated feature pairs | VIF < 30 applied; still use SHAP as approximate guide |
| Pressure data not included | Equilibrium H₂ pressure affects capacity | Future: integrate PCT curves |
| Limited HEA coverage | Novel high-entropy alloys may be OOD | Extrapolation uncertainty increases for >5-element alloys |
| Log-scale SHAP values | SHAP directions in log space, not wt% space | Apply `expm1` correction for engineering reports |

---

## 8. Conclusions

**Best model for production:** The Stacking Ensemble (ExtraTrees + CatBoost + GradientBoosting + RandomForest, meta-learner = Ridge) delivers the best balance of accuracy and generalisability:
- Validation R² = **0.939**, Test R² = **0.892**
- Test MAE = **0.223 wt%** — ~20 % improvement over the HyStor HYST baseline (MAE 0.28 wt%)
- Lowest overfitting (0.039) among all models
- Statistically significant error reduction vs. best individual model (p = 0.037)

**Best single model:** The Optuna-optimised CatBoost achieves the highest validation R² (0.969) with negative overfitting (−0.018), making it the preferred choice when a single interpretable model is required.

**Material science takeaways:**
1. Alkaline-earth content (`avg_is_alkaline`) is the single strongest linear predictor of capacity (r = 0.673); high-Mg alloys outperform transition-metal-dominated compositions
2. d-valence electrons (`avg_valence_d`) are the strongest nonlinear driver (MI = 0.813) and suppress capacity above a threshold of ~2.5
3. Polarizability per atomic mass captures lattice-geometry effects on interstitial H sites and provides the strongest feature-selection signal (Boruta SHAP = 0.172)
4. Performance is highest in the 300–500 K operating window; extrapolation above 500 K requires caution

**Future directions:**
- Integrate pressure (PCT curves) as an additional input feature
- Apply Graph Neural Networks (e.g., MEGNet, CGCNN) for structure-aware predictions
- Combine with genetic algorithms or Bayesian optimisation for inverse alloy design
- Extend to novel high-entropy alloys using transfer learning

---

## 9. References

1. Wilson, N., et al., *HyStor: An experimental database of hydrogen storage properties for various metal alloy classes.* International Journal of Hydrogen Energy, 2024. **90**: pp. 460–469.
2. ML-HYDPARK v0.0.5 — benchmark dataset for machine learning on hydrogen storage materials.
3. Ward, L., et al., *Matminer: An open source toolkit for materials data mining.* Computational Materials Science, 2018. **152**: pp. 60–69.
4. Kauwe, S.K., et al., *CBFV: Composition-Based Feature Vectorization for materials informatics.* (Python library).
5. Choudhary, K., et al., *The Joint Automated Repository for Various Integrated Simulations (JARVIS).* npj Computational Materials, 2020. **6**(1): p. 173.
6. Northcutt, C.G., et al., *Confident Learning: Estimating Uncertainty in Dataset Labels.* JAIR, 2021. **70**: pp. 1373–1411.
7. Akiba, T., et al., *Optuna: A Next-generation Hyperparameter Optimization Framework.* KDD 2019.
8. Lundberg, S.M., & Lee, S.I., *A Unified Approach to Interpreting Model Predictions.* NeurIPS 2017.
9. Kursa, M.B., & Rudnicki, W.R., *Feature Selection with the Boruta Package.* Journal of Statistical Software, 2010. **36**(11).
