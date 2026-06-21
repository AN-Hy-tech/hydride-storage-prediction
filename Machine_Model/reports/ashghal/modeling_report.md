# Modeling Report: Hydrogen Capacity Prediction
**Date:** 2025-07-03 (Updated)

## 1. Introduction
This report documents the data analysis, preprocessing, feature selection, and initial modeling efforts for predicting the maximum hydrogen weight percentage (`H2_W% (max)`) in hydride materials. The project leverages machine learning techniques to optimize predictive accuracy, with a focus on handling data quality and model performance under a 2-week deadline (until 2025-07-16).

## 2. Dataset Overview
- **Total Rows:** 1279
- **Initial Columns:** ['Composition', 'Alloy_class', 'Dataset', 'H2_W% (max)', 'temperature(K)', 'Citation']
- **Missing Values:** None (0 missing in all columns)
- **Outliers:**
  - `H2_W% (max)`: 133 outliers
  - `temperature(K)`: 221 outliers
- **Target Range:** `H2_W% (max)`: 0.1% to 7.19%
- **Temperature Range:** 195 K to 773 K
- **Dominant Alloy Classes:** {'AB2': 368, 'AB5': 196, 'Mg': 148, 'MIC': 132, 'MEA': 110}

## 3. Data Preprocessing and Quality Improvement
### 3.1 Outlier Management
- **Decision:** Outlier capping deemed unnecessary initially due to natural data diversity; management deferred to model tuning or scaling.
- **Action:** Extreme outliers (> 3 Z-score) identified (13 in Train, 2 in Validation, 9 in Test) 

### 3.2 Target Transformation
- **Action:** Applied log transformation (`np.log1p`) to `H2_W% (max)` to address skewness, resulting in `log_H2_W% (max)`.
- **Result:** Transformed target used for modeling, with original scale restored via `np.expm1` for interpretation.

### 3.3 Feature Extraction and Selection
- **Extraction:** Features extracted from Matminer and Magpie, initially 163 features.
- **Initial Filtering:** Reduced to 64 features plus target and Composition using correlation (> 0.1), variance (> 0.01), and multicollinearity (> 90%) checks.
- **Feature Selection:** Random Forest with 5-fold Cross-Validation and Optuna optimization selected 20-22 features (e.g., 'MagpieData mean Column', 'temperature(K)') based on importance > 0.01.
- **Data Splitting:** Stratified split into 761 Train (59.5%), 189 Validation (14.8%), and 329 Test (25.7%) rows to ensure balance.

### 3.4 Data Validation
- **Distribution Analysis:** Target distribution extracted and visualized, showing positive skewness. Normality tests (Shapiro, p-value < 0.05) confirmed non-normal distribution.
- **Capping Effect:** Visualized in `reports\figures\capping_effect`, reducing extreme values (e.g., 5-8% to ~3-4%).

## 4. Initial Modeling without Scaling
### 4.1 Random Forest (Initial)
- **Parameters:** Optimized with Optuna (n_estimators=92, max_depth=10, min_samples_split=8, min_samples_leaf=2, max_features=0.620938).
- **Results:**
  - Cross-Validation R²: 0.7127 (± 0.1373)
  - Validation R²: 0.7638
  - Overfitting R²: 0.1336
- **Analysis:** Good initial performance, with mild overfitting manageable via regularization.

### 4.2 Random Forest (Secondary)
- **Parameters:** Re-optimized with Optuna (n_estimators=145, max_depth=12, min_samples_split=5, min_samples_leaf=3, max_features=0.565, max_samples=0.999).
- **Results:**
  - Cross-Validation R²: 0.7100 (± 0.1157)
  - Validation R²: 0.7167
  - Overfitting R²: 0.1805
- **Analysis:** Slight performance drop (0.7167 vs 0.7638), with increased overfitting due to higher complexity.

### 4.3 Random Forest (Re-optimized)
- **Parameters:** Re-optimized with Optuna (n_estimators=121, max_depth=12, min_samples_split=5, min_samples_leaf=2, max_features=0.338, max_samples=0.936).
- **Results:**
  - Cross-Validation R²: 0.7155 (± 0.1044)
  - Validation R²: 0.7133
  - Overfitting R²: 0.1937
- **Analysis:** Improved stability (lower std), but overfitting increased. R² stable around 0.71-0.72.

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

## 5. Benchmarking with Scaling
### 5.1 Methodology
- **Scaling:** Applied StandardScaler to all features to normalize ranges and improve model convergence.
- **Models Tested:** Ridge, Decision Tree, Extra Trees, Gradient Boosting, XGBoost, CatBoost, and Kernel Neural Network (SVR with RBF kernel).
- **Evaluation:** 5-fold Cross-Validation with R², MSE, and MAE metrics, plus fit time and overfitting assessment (R² difference).

### 5.2 Results
- **Ridge:** R² 0.6044, MSE 0.0375, MAE 0.1371, Fit Time 7.32s, Overfitting 0.0500. Limited by linear assumptions.
- **DecisionTree:** R² 0.4411, MSE 0.0529, MAE 0.1398, Fit Time 2.30s, Overfitting 0.5230. Weak due to high overfitting.
- **ExtraTrees:** R² 0.6922, MSE 0.0293, MAE 0.1064, Fit Time 1.08s, Overfitting 0.2074. Strong bagging with good speed.
- **GradientBoosting:** R² 0.6673, MSE 0.0314, MAE 0.1171, Fit Time 1.28s, Overfitting 0.1693. Balanced option.
- **XGBoost:** R² 0.6650, MSE 0.0317, MAE 0.1162, Fit Time 1.88s, Overfitting 0.2364. High variance, needs tuning.
- **CatBoost:** R² 0.7107, MSE 0.0275, MAE 0.1073, Fit Time 20.00s, Overfitting 0.1967. Best accuracy, slowest.
- **KernelNN:** R² 0.6965, MSE 0.0289, MAE 0.1141, Fit Time 0.10s, Overfitting 0.1112. Fast with good stability.

### 5.3 Optimized CatBoost
- **Parameters:** Optimized with Optuna (learning_rate=0.1-0.25, depth=6-10, iterations=300-900, l2_leaf_reg=3-10, random_strength=5-20, early_stopping_rounds=100).
- **Parameters (threshold 0.3, SMOGN)**: Optimized with Optuna (learning_rate=0.0563, depth=8, iterations=755, l2_leaf_reg=5.44, bagging_temperature=0.639, random_strength=4.15, early_stopping_rounds=143).
- **Results:**
  - Cross-Validation R²: 0.7154
  - Train R²: 0.9804
  - Validation R²: 0.7570
  - Test R²: 0.6944
  - Validation MAE: 0.2815 (original scale)
  - Test MAE: 0.3700 (original scale)
  - Overfitting R²: Train-Val 0.2234, Train-Test 0.2860
  - Fit Time: 1.86s
  - Feature Importance: Top features include 'Mixing enthalpy' (7.73), 'VEC mean' (7.43), 'Mean cohesive energy' (7.23), 'MagpieData mode CovalentRadius' (7.22).
- **Analysis:** Improved performance over initial CatBoost (R² 0.7107 to 0.7570), but high overfitting (Train-Test 0.2860) indicates need for ensemble methods or further regularization. Feature importance threshold tested at 2.0 (21 features) and 3.0 (12 features).


- **Results (threshold 0.3, SMOGN)**:
  - Cross-Validation R²: 0.8069
  - Train R²: 0.9843
  - Validation R²: 0.7685
  - Test R²: 0.7325
  - Validation MAE: 0.3232 (original scale)
  - Test MAE: 0.4103 (original scale)
  - Overfitting R²: Train-Val 0.2158, Train-Test 0.2518
- **Parameters (threshold 0.2, SMOGN)**: Same as above.
- **Results (threshold 0.2, SMOGN)**:
  - Cross-Validation R²: 0.8083
  - Train R²: 0.9730
  - Validation R²: 0.7864
  - Test R²: 0.7312
  - Validation MAE: 0.3160 (original scale)
  - Test MAE: 0.4171 (original scale)
  - Overfitting R²: Train-Val 0.1866, Train-Test 0.2418
- **Analysis:** Threshold 0.2 improved Validation R² (0.7685 to 0.7864) and reduced Train-Val overfitting (0.2158 to 0.1866), but Test R² slightly decreased (0.7325 to 0.7312) and Test MAE increased (0.4103% to 0.4171%). Indicates potential noise from additional features and need for ensemble methods.

### 5.3 Optimized CatBoost on Augmented Data
- **Parameters:** Optimized with Optuna (learning_rate=0.07399, depth=8, iterations=826, l2_leaf_reg=7.9498, bagging_temperature=0.5626, random_strength=1.0149, early_stopping_rounds=64).
- **Results:**
  - Cross-Validation R²: 0.8732
  - Train R²: 0.9881
  - Validation R²: 0.8003
  - Test R²: 0.7417
  - Validation MAE: 0.2902% (original scale)
  - Test MAE: 0.3939% (original scale)
  - Overfitting R²: Train-Val 0.1878, Train-Test 0.2464
- **Analysis:** Significant improvement in Validation R² (0.7570 to 0.8003) due to data augmentation, but Test R² (0.7417) and MAE (0.3939%) still below targets. Feature importance threshold 4.0 selected 11 features, but removal of 'VEC mean' may have impacted performance.

 
## 6. Optimization and Next Steps
### 6.1 Data Augmentation
- **Approach:** Applied oversampling with minimal noise (1% std) on key features for samples with log_H2_W% (max) > 1.1537 (100 new samples), > 1.06 (150 new samples), and 0.693-0.916 (80 new samples). Augmented data saved in `data\augmented\augmented_train.csv`. Distribution and correlation report saved in `reports\data_augmentation_report.png`.
- **Outcome:** Increased train data to 1091 samples, achieving Validation R² 0.8003.

### 6.2 Stacking
- **Approach:** Implement Stacking with CatBoost, ExtraTrees, XGBoost, and KernelNN, using Ridge as meta-model, targeting R² > 0.8 and MAE < 0.3%.
- **Expected Outcome:** Results in `reports\stacking_augmented_results.csv`, model in `models\stacking_augmented_model.pkl`.

### 6.3 Next Steps
- **Stacking:** Complete by 10th July.
- **Validation:** Validate on Test set by 10th July.
- **Reporting:** Allocate 4 days (12-16 July) for report finalization.


## 7. Conclusion
The project has progressed through data preprocessing, feature selection, and initial modeling. Unscaled Random Forest models provided a baseline (R² 0.71-0.76), while scaled benchmarking highlighted CatBoost (R² 0.7107) as the top performer. The next phase will focus on optimizing CatBoost, with potential Stacking if needed, to approach 0.8 R², aligning with data limitations and timeline.
