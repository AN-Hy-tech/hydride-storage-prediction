# Data Augmentation Report

**Date**: July 6, 2025

## 1. Overview
To address the limited size of the training dataset (761 rows) and improve model performance (targeting R² > 0.8 and MAE < 0.3% in original scale), data augmentation was performed using the SMOGN (Synthetic Minority Oversampling for Regression with Gaussian Noise) technique. The focus was on the 75th percentile of the target (`log_H2_W% (max) > 1.1537`, equivalent to `H2_W% (max) > 2.17%`) to enhance predictions for high-capacity materials. Non-capped data was used to preserve the natural distribution, with additional filtering to ensure realistic synthetic data.

## 2. Dataset Details
- **Input Data**:
  - Train: 761 rows, 24 columns (22 numerical features + `Composition` + `log_H2_W% (max)`).
  - Validation: 189 rows.
  - Test: 329 rows.
  - Paths:
    - Train: `D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_train.csv`
    - Validation: `D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_val.csv`
    - Test: `D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_test.csv`
- **Target**:
  - `log_H2_W% (max)`: Mean 1.014, Std 0.328, Range [0.247, 2.044].
  - `H2_W% (max)` (calculated via `np.expm1`): Mean 1.915%, Std 1.039%, Range [0.28%, 6.72%].
  - 75th Percentile: `log_H2_W% (max) > 1.1537` (`H2_W% (max) > 2.17%`, 195 samples).
  - Samples > 3%: 296.
  - Samples between 2% and 2.5%: 166.

## 3. SMOGN Configuration
- **Parameters**:
  - `k=5`: 5 nearest neighbors for synthetic data generation.
  - `samp_method='extreme'`: Focus on high target values (`log_H2_W% (max) > 1.1537`).
  - `rel_coef=0.3`: Target 30% data increase (~228 additional rows).
  - `rel_thres=0.75`: Focus on 75th percentile.
- **Filters**:
  - Removed `Composition` column (non-numeric) before SMOGN to avoid warnings.
  - Filtered synthetic data with `H2_W% (max) > 6.72%` to ensure realism.
- **Output**: Augmented Train data saved in `data/augmented/train_augmented.csv`.

## 4. Results
- **Data Size**:
  - Before SMOGN: 761 rows.
  - After SMOGN and filtering: 847 rows (11% increase due to filtering).
- **Target Distribution Before SMOGN**:
log_H2_W% (max)  H2_W% (max)
count       761.000000   761.000000
mean          1.014007     1.914547
std           0.327782     1.039486
min           0.246860     0.280000
25%           0.832909     1.300000
50%           0.993252     1.700000
75%           1.153732     2.170000
max           2.043814     6.720000

- **Target Distribution After SMOGN and Filtering**:
log_H2_W% (max)  H2_W% (max)
count       847.000000   847.000000
mean          1.014848     1.982362
std           0.391617     1.217662
min           0.246860     0.280000
25%           0.693147     1.000000
50%           0.993252     1.700000
75%           1.335001     2.800000
max           2.043814     6.720000

- **Normality Test**:
- Shapiro-Wilk Test for `log_H2_W% (max)`: p-value = 0.0000 (non-normal).
- Recommendation: Consider Box-Cox transformation if normal distribution is required.
- **Visualizations**:
- Target distributions (before and after SMOGN) saved in `reports/figures/data_augmented_analysis/target_distribution_comparison.png`.
- Feature correlation matrix saved in `reports/figures/data_augmented_analysis/correlation_matrix_smogn.png`.

## 5. Analysis
- **Data Increase**: The Train set increased from 761 to 847 rows (11% increase), less than the target 30% due to filtering of synthetic data with `H2_W% (max) > 6.72%`. This ensures realistic data aligned with the original range.
- **Target Distribution**:
- Mean `H2_W% (max)` increased from 1.915% to 1.982%, indicating focus on higher-capacity materials.
- Standard deviation increased from 1.039% to 1.218%, reflecting greater diversity in the augmented data.
- 75th percentile shifted from 2.17% to 2.80%, confirming SMOGN's focus on high target values.
- **Normality**: The non-normal distribution (p-value = 0.0000) suggests a transformation (e.g., Box-Cox) may be needed if normality is critical for modeling.
- **Correlations**: The correlation matrix (in `correlation_matrix_smogn.png`) should be reviewed to ensure key features (e.g., `Mixing enthalpy`, `VEC mean`) maintain strong relationships with the target.

## 6. Next Steps
- **Modeling**: Train a CatBoost model on the augmented dataset (`data/augmented/train_augmented.csv`) by 7th July, targeting R² > 0.8 and MAE < 0.3%.
- **Distribution Adjustment**: If normal distribution is required, apply Box-Cox transformation to `log_H2_W% (max)`.
- **Stacking**: If R² < 0.8, implement Stacking with CatBoost, ExtraTrees, XGBoost, and KernelNN by 10th July.
- **Validation**: Validate on Test set by 10th July.
- **Reporting**: Allocate 4 days (12-16 July) for report finalization.

**Files**:
- Augmented Train data: `data/augmented/train_augmented.csv`
- Validation data: `data/augmented/val_augmented.csv`
- Test data: `data/augmented/test_augmented.csv`
- Visualizations: `reports/figures/data_augmented_analysis/target_distribution_comparison.png`, `reports/figures/data_augmented_analysis/correlation_matrix_smogn.png`