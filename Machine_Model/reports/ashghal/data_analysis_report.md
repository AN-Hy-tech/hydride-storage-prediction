# Data Analysis Report
**Date:** 2025-07-01 (Updated)

## 1. Dataset Overview
- **Number of rows:** 1279
- **Initial Columns:** ['Composition', 'Alloy_class', 'Dataset', 'H2_W% (max)', 'temperature(K)', 'Citation']
- **Missing Values:** {'Composition': 0, 'Alloy_class': 0, 'Dataset': 0, 'H2_W% (max)': 0, 'temperature(K)': 0, 'Citation': 0}
- **Outliers:**
  - H2_W% (max): 133 outliers
  - temperature(K): 221 outliers
- **Unique Formulae:** 1149 unique compositions

## 2. Initial Observations
- **H2_W% (max) Range:** 0.1 to 7.19
- **Temperature(K) Range:** 195 to 773
- **Dominant Alloy Classes:** {'AB2': 368, 'AB5': 196, 'Mg': 148, 'MIC': 132, 'MEA': 110}

## 3. Data Preprocessing Decisions and Actions
### 3.1 Outlier Management
- **Decision:** Used non-capped data for augmentation to preserve natural distribution, with outliers identified (13 in Train, 2 in Validation, 9 in Test) but not capped.
- **Action:** Applied SMOGN data augmentation on Train set, focusing on 75th percentile (log_H2_W% (max) > 1.1537, H2_W% (max) > 2.17%), increasing Train size by 11% (761 to 847 rows) after filtering Composition column and H2_W% (max) > 6.72%. Augmented data saved in `data/augmented/train_augmented.csv`. Target distribution and feature correlations analyzed, saved in `reports/figures/data_augmented_analysis`. Detailed analysis in `reports/data_augmentation.md`.
### 3.2 Target Transformation
- **Action:** Log transformation applied to H2_W% (max) using `np.log1p` to address skewness, improving model performance.
- **Result:** Transformed target stored as `log_H2_W% (max)` for subsequent analyses.

### 3.3 Feature Extraction
- **Action:** Extracted features from Matminer package and Magpie, resulting in 163 features (including initial columns).
- **Details:** Features include physicochemical properties like Miedema energies, shear modulus, and Magpie statistical descriptors.

## 4. Feature Selection Process
### 4.1 Initial Filtering
- **Method:** 
  - Correlation threshold > 0.1 to retain features with significant linear relationship to the target.
  - Variance threshold > 0.01 to remove low-variance features.
  - Multicollinearity check to remove features with correlation > 90%, keeping those with higher target correlation.
- **Action:** Filtered out object-type features (except Composition).
- **Result:** Reduced from 163 features to 64 features plus target and Composition.

### 4.2 Data Splitting
- **Method:** Stratified splitting based on Composition, temperature(K), and log_H2_W% (max) using KBinsDiscretizer with 3 bins.
- **Details:** 
  - Total rows: 1279
  - Train: 761 rows (approx. 59.5%)
  - Validation: 189 rows (approx. 14.8%)
  - Test: 329 rows (approx. 25.7%)
- **Outcome:** Ensured balance and prevented data leakage, with no overlapping formulae across splits.

### 4.3 Feature Selection with Random Forest
- **Method:** 
  - Utilized Random Forest with 5-fold Cross-Validation, optimized with Optuna.
  - Best parameters: {'n_estimators': 125, 'max_depth': 10, 'min_samples_split': 5, 'min_samples_leaf': 2, 'max_features': 0.4829912251237406}
- **Validation Metrics (Log Scale):**
  - Cross-Validation R²: 0.7127 (± 0.1373)
  - Cross-Validation MSE: 0.0305 (± 0.0162)
  - Cross-Validation MAE: 0.1116 (± 0.0207)
- **Validation Metrics (Original Scale):**
  - Train R²: 0.8974
  - Train MSE: 0.1108
  - Train MAE: 0.1888
  - Validation R²: 0.7638
  - Validation MSE: 0.2565
  - Validation MAE: 0.2935
- **Overfitting Assessment:**
  - R² difference: 0.1336
  - MSE difference: -0.1458
  - MAE difference: -0.1047
- **Result:** Selected 20 features with importance > 0.01 (initially tested with 0.02 threshold, adjusted to 0.01 for optimal feature retention).

### 4.4 Selected Features
- **List of Top 20 Features:**
  Top feature names: ['MagpieData mean Column', 'VEC mean', 'MagpieData mean Number', 'MagpieData mode CovalentRadius', 'MagpieData mean MendeleevNumber', 'Mixing enthalpy', 'Mean cohesive energy', 'MagpieData mode Number', 'MagpieData mode NdValence', 'MagpieData mean NsValence', 'MagpieData avg_dev CovalentRadius', 'MagpieData avg_dev AtomicWeight', 'MagpieData mean CovalentRadius', 'MagpieData range Electronegativity', 'MagpieData mean SpaceGroupNumber', 'MagpieData avg_dev NValence', 'Shear modulus local mismatch', 'Miedema_deltaH_ss_min', 'MagpieData avg_dev MendeleevNumber', 'Shear modulus mean', 'MagpieData mean GSvolume_pa'] + temperature(k)
- **Top 3 Feature:** MagpieData mean Column : 0.3563209365346104 , MagpieData mean Number	: 0.1322719563730971, VEC mean : 0.1227755155976544
- **Analysis:** Features reflect a mix of statistical (MagpieData descriptors) and physicochemical properties (e.g., Miedema energies, shear modulus), aligning with hydrogen storage capacity determinants.

### 4.5 Database Update
- **Action:** Updated database (`hydride.db`) with selected features in tables `train_data`, `val_data`, and `test_data`.
- **Details:**
  - Train rows: 761
  - Validation rows: 189
  - Test rows: 329
- **Compatibility Fix:** Handled special characters (e.g., '%') in column names with quoted identifiers.
## 5. Evaluation and Recommendations
- **Dataset Validation:** Pre-modeling analysis conducted to ensure data quality, including target distribution, feature statistics, correlation with target (excluding non-numeric columns), and outlier detection for the 20 selected features. Target distribution data (log and original scales) extracted and saved in `reports\data\target_distributions`, with normality tests (p-value < 0.05 indicating non-normal distribution) and extreme outlier identification (> 4 Z-score) performed. SMOGN augmentation applied to Train set with Composition filter and H2_W% (max) <= 6.72%, distribution and correlations visualized in `reports/figures/data_augmented_analysis`, detailed analysis in `reports/data_augmentation.md`.
- **Model Performance:** 
  - Initial Random Forest models without scaling achieved R² of 0.71-0.76, with detailed results in `reports\rf_results.csv`.
  - Benchmarking of selected models with scaling showed CatBoost leading with R² 0.7107, improved to 0.7570 after optimization with feature importance threshold 2.0, results in `reports\catboost_optimized_results.csv`.
  - CatBoost with SMOGN data (847 rows) tested with thresholds 0.3 and 0.2, results in `reports/catboost_smogn_results.csv`.
- **Results Summary:**
  - **CatBoost (threshold 0.3, SMOGN)**: Cross-Validation R² 0.8069, Train R² 0.9843, Validation R² 0.7685, Test R² 0.7325, Validation MAE 0.3232%, Test MAE 0.4103%, Overfitting (Train-Val 0.2158, Train-Test 0.2518).
  - **CatBoost (threshold 0.2, SMOGN)**: Cross-Validation R² 0.8083, Train R² 0.9730, Validation R² 0.7864, Test R² 0.7312, Validation MAE 0.3160%, Test MAE 0.4171%, Overfitting (Train-Val 0.1866, Train-Test 0.2418).
- **Overfitting:** Reduced from 0.2518 to 0.2418 (Train-Test) with threshold 0.2, but Test MAE increased. Indicates need for further tuning or ensemble methods.
- **Recommendation:** Test CatBoost with threshold 3.0 by 7th July. Implement Stacking with CatBoost, ExtraTrees, XGBoost, and KernelNN if R² < 0.8. Validate on Test set by 10th July and allocate 4 days (12-16 July) for report finalization.

## 5. Benchmarking with Scaling
### 5.1 Methodology
- **Scaling:** Applied StandardScaler to all features to normalize ranges and improve model convergence.
- **Models Tested:** Ridge, Decision Tree, Extra Trees, Gradient Boosting, XGBoost, CatBoost, and Kernel Neural Network (SVR with RBF kernel).
- **Evaluation:** 5-fold Cross-Validation with R², MSE, and MAE metrics, plus fit time and overfitting assessment (R² difference between Train and Validation).

### 5.2 Results
- **Ridge:**
  - **R²:** 0.6044 (± 0.0852)
  - **MSE:** 0.0375 (± 0.0097)
  - **MAE:** 0.1371 (± 0.0080)
  - **Fit Time:** 7.32s
  - **Overfitting R²:** 0.0500
  - **Analysis:** Linear model performed moderately, limited by non-linear data structure and skewness. Low overfitting suggests simplicity, but R² indicates poor fit for complex relationships.
- **DecisionTree:**
  - **R²:** 0.4411 (± 0.4471)
  - **MSE:** 0.0529 (± 0.0460)
  - **MAE:** 0.1398 (± 0.0473)
  - **Fit Time:** 2.30s
  - **Overfitting R²:** 0.5230
  - **Analysis:** Weak performance with high variance (± 0.4471), indicating severe overfitting due to lack of regularization. Fast but unreliable alone.
- **ExtraTrees:**
  - **R²:** 0.6922 (± 0.1255)
  - **MSE:** 0.0293 (± 0.0141)
  - **MAE:** 0.1064 (± 0.0224)
  - **Fit Time:** 1.08s
  - **Overfitting R²:** 0.2074
  - **Analysis:** Strong bagging ensemble with good accuracy and moderate overfitting. Fastest ensemble model, suitable for quick iterations.
- **GradientBoosting:**
  - **R²:** 0.6673 (± 0.1068)
  - **MSE:** 0.0314 (± 0.0108)
  - **MAE:** 0.1171 (± 0.0134)
  - **Fit Time:** 1.28s
  - **Overfitting R²:** 0.1693
  - **Analysis:** Solid boosting performance with stable variance. Moderate overfitting, offering a balanced option between speed and accuracy.
- **XGBoost:**
  - **R²:** 0.6650 (± 0.2023)
  - **MSE:** 0.0317 (± 0.0208)
  - **MAE:** 0.1162 (± 0.0289)
  - **Fit Time:** 1.88s
  - **Overfitting R²:** 0.2364
  - **Analysis:** Comparable to GradientBoosting but with higher variance (± 0.2023), suggesting sensitivity to data splits. High overfitting indicates need for tuning.
- **CatBoost:**
  - **R²:** 0.7107 (± 0.1175)
  - **MSE:** 0.0275 (± 0.0134)
  - **MAE:** 0.1073 (± 0.0220)
  - **Fit Time:** 20.00s
  - **Overfitting R²:** 0.1967
  - **Analysis:** Best initial R² with good stability. Slow fit time (20s) reflects computational overhead, but manageable overfitting makes it a top contender.
- **KernelNN (SVR):**
  - **R²:** 0.6965 (± 0.0795)
  - **MSE:** 0.0289 (± 0.0105)
  - **MAE:** 0.1141 (± 0.0188)
  - **Fit Time:** 0.10s
  - **Overfitting R²:** 0.1112
  - **Analysis:** Competitive R² with high stability (± 0.0795) and minimal overfitting. Extremely fast, but potential for improvement with parameter tuning.

## 5. Evaluation and Recommendations
- **Dataset Validation:** Pre-modeling analysis conducted to ensure data quality, including target distribution, feature statistics, correlation with target (excluding non-numeric columns), and outlier detection for the 20 selected features. Target distribution data (log and original scales) extracted and saved in `reports\data\target_distributions`, with normality tests (p-value < 0.05 indicating non-normal distribution) and extreme outlier identification (> 4 Z-score) performed.
- **Data Augmentation:** Applied oversampling with minimal noise (1% std) on key features for samples with log_H2_W% (max) > 1.1537 (100 new samples), > 1.06 (150 new samples), and 0.693-0.916 (80 new samples). Augmented data saved in `data\augmented\augmented_train.csv`. Distribution and correlation report saved in `reports\data_augmentation_report.png`.
- **Model Performance:** 
  - Initial Random Forest models without scaling achieved R² of 0.71-0.76, with detailed results in `reports\rf_results.csv`.
  - Benchmarking with scaling showed CatBoost leading with R² 0.7107, improved to 0.7570 after optimization (threshold 2.0).
  - CatBoost on augmented data (threshold 4.0) achieved Cross-Validation R² 0.8732, Validation R² 0.8003, Test R² 0.7417, Test MAE 0.3939%.
- **Overfitting:** Reduced from 0.2860 to 0.2464 (Train-Test), but still high.
- **Recommendation:** Test Stacking with CatBoost, ExtraTrees, XGBoost, and KernelNN by 10th July to target R² > 0.8 and MAE < 0.3%. Validate on Test set by 10th July and allocate 4 days (12-16 July) for report finalization.
