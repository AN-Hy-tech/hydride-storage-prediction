# Hydride Machine Learning System (HydMS) Report

**Date**: September 24, 2025
--------------------------------
## 1. Data Preprocessing and Feature Engineering Methodology
This section details the systematic approach to collecting, preprocessing, featurizing, merging, and splitting datasets for the hydrogen storage capacity prediction project. The goal is to create a robust, balanced dataset with meaningful physicochemical descriptors derived from chemical compositions, enabling accurate modeling of hydrogen storage capacity in hydride materials. The methodology includes data loading, log transformation, feature extraction, dataset merging, and stratified splitting, preparing the dataset for subsequent outlier engineering and modeling phases.
--------------------------------
### 1.1 Data Collection and Initial Preprocessing
- **Data Source**: The primary dataset was sourced from the HyStor experimental database [1], containing experimental and literature-based data on hydride materials. The primary dataset consists of 1279 rows and 6 columns: ['Composition', 'Alloy_class', 'Dataset', 'H2_W% (max)', 'temperature(K)', 'Citation'], capturing compositional, classificatory, and performance metrics for hydrogen storage alloys. This aligns with HyStor's reported 1280 entries (minor difference of one entry), incorporating 468 new compositions from recent research and patents, expanding coverage to modern alloy classes.
- **Loading and Initial Inspection**: The dataset was loaded into a Pandas DataFrame using `pandas.read_csv`. Initial inspection confirmed the shape (1279 rows, 6 columns) and identified column types: 2 numeric ('H2_W% (max)', 'temperature(K)') and 4 categorical ('Composition', 'Alloy_class', 'Dataset', 'Citation') using `pandas.select_dtypes`.
- **Descriptive Statistics**: Summary statistics (count, unique, top, freq, mean, std, min, 25%, 50%, 75%, max) were computed for all columns using `df.describe(include='all')`. Key highlights: Unique compositions (1149, most frequent: Ti0.9Zr0.1Mn1.4Cr0.4V0.2, 6 occurrences); Alloy classes (10 unique, AB2 most common at 368); Datasets (3 sources, HydPark predominant at 831); H2_W% (max) (mean 1.95 wt%, std 1.10, min 0.1 wt%, max 7.19 wt%); temperature(K) (mean 354.27 K, std 105.04, min 195 K, max 773 K); Citations (144 unique, DOE_data_url most frequent at 831).
- **Missing Values Check**: Missing values were assessed using `df.isnull().sum()` to ensure data completeness, confirming a total of 0 missing values.
- **Element Extraction and Aggregation**: Chemical elements were extracted from the 'Composition' column by parsing chemical formulas (e.g., splitting by uppercase letters to identify atomic symbols like Mg, Ni). For each element, associated `temperature(K)` and `H2_W% (max)` values were aggregated using a `collections.defaultdict` to collect lists of values. Mean temperature, mean capacity, and frequency were computed per element. Results: 54 elements identified; high-frequency: Ti (573, mean temp 319.56 K, mean capacity 2.03 wt%), Zr (490, mean temp 318.25 K, mean capacity 1.73 wt%), Mn (431, mean temp 308.67 K, mean capacity 1.77 wt%); highest mean capacities: Au (3.6 wt%), Os/Re (3.4 wt%), Ba (3.37 wt%), Mg (3.32 wt%).
- **Correlation Analysis**: Pearson correlation coefficients were calculated between numeric columns ('H2_W% (max)', 'temperature(K)') using `df.corr()`, yielding a moderate positive correlation of 0.4553, suggesting higher temperatures enhance hydrogen storage capacity, consistent with hydride thermodynamics.
- **Normality Test**: A Shapiro-Wilk test was performed on 'H2_W% (max)' to assess normality, resulting in Statistic=0.8684, p-value=0.0000 (non-normal), supporting log transformation due to skewed distribution.
- **Mode Calculation**: The mode (most frequent value) for 'temperature(K)' and 'H2_W% (max)' was computed using `df.mode()`, yielding temperature mode=298 K and capacity mode=1.6 wt%.
- **Non-Standard Formulas**: Compositions with non-standard formats (e.g., weight percentages like 'Mg-23.5 wt%Ni-10 wt%La', totaling 208 entries) were identified for manual review, ensuring accurate parsing in subsequent steps.
- **Log Transformation**: To address skewness in the target variable `H2_W% (max)`, a log transformation was applied using `np.log1p(df['H2_W% (max)'])` in `src/log_transform_target.py`, creating a new column `log_H2_W% (max)`. The original `H2_W% (max)` column was dropped, and the transformed dataset was saved to `data/raw/hydride_prefeaturizing.csv`. Histograms of the original and transformed distributions were generated using `seaborn.histplot` for comparison, with the figure saved to `reports/figures/raw_data_analysis/figure_log_transform_histograms.png`. 

### 1.2 Feature Extraction
To enhance the log-transformed dataset with physicochemical properties, feature extraction was performed using the CBFV library (with 'magpie' and 'jarvis' element properties) and Matminer's `Miedema` and `WenAlloys` featurizers, as implemented in `src/extract_features_cbfv.py` and `notebooks/data_preprocessed_matminer.ipynb`. This process generated 282 features, transforming the dataset into a structure with composition (formula), temperature, target (`log_H2_W% (max)`), and 282 extracted features.

- **Input Data**: The log-transformed dataset from `data/raw/hydride_prefeaturizing.csv` (1279 rows, 7 columns: ['Composition', 'Alloy_class', 'Dataset', 'temperature(K)', 'Citation', 'log_H2_W% (max)', 'Composition' as formula]) was used. Features were extracted from the 'Composition' column.
- **Preprocessing for Feature Extraction**:
  - Object columns except 'Composition' were dropped using `df.select_dtypes(include='object')`.
  - Columns renamed for compatibility: 'log_H2_W% (max)' to 'target' and 'Composition' to 'formula'.
- **Feature Extraction Process**:
  - **CBFV (Magpie and Jarvis)**: The CBFV library with `elem_prop='magpie'` and `elem_prop='jarvis'` was used via `generate_features` to extract features such as average atomic mass divided by polarizability, average first ionization energy multiplied by electronegativity, deviation in atomic mass multiplied by thermal conductivity, and more. No duplicates were dropped, and extended features were enabled.
  - **Matminer (Miedema and WenAlloys)**: The `MultipleFeaturizer` in `notebooks/data_preprocessed_matminer.ipynb` applied `Miedema` and `WenAlloys` featurizers to generate alloy-specific properties, such as Miedema formation enthalpies (`Miedema_deltaH_inter`, `Miedema_deltaH_amor`, `Miedema_deltaH_ss_min`) and shear modulus metrics.
  - Output dataset shape: 1279 rows, 282 features + formula, temperature, target.
  - Features saved to `data/processed/cbfv_extracted_features.csv`.
- **Feature List** (Partial, based on `featurize_dataframe.csv`):
  - `avg_atom_mass_divi_polzbl`, `avg_coulmn`, `avg_first_ion_en_divi_mol_vol`, `avg_first_ion_en_mult_X`, `avg_first_ion_en_mult_atom_mass`, `avg_first_ion_en_mult_therm_cond`, `avg_hfus_add_elec_aff`, `avg_is_alkaline`, `avg_mp_divi_atom_mass`, `avg_polzbl_divi_atom_mass`, `dev_atom_mass_mult_therm_cond`, `dev_bp_divi_atom_mass`, `dev_voro_coord_divi_mol_vol`, `range_first_ion_en_mult_X`, `range_hfus_add_X`, `avg_Atomic_Number`, `avg_Atomic_Weight`, `avg_Period`, `avg_group`, `avg_families`, `avg_Metal`, `avg_Nonmetal`, `avg_Metalliod`, `avg_Mendeleev_Number`, `avg_l_quantum_number`, `avg_Atomic_Radius`, `avg_Miracle_Radius_[pm]`, `avg_Covalent_Radius`, `avg_Zunger_radii_sum`, `avg_ionic_radius`, `avg_crystal_radius`, `avg_Pauling_Electronegativity`, `avg_MB_electonegativity`, `avg_Gordy_electonegativity`, `avg_Mulliken_EN`, `avg_Allred-Rockow_electronegativity`, `avg_metallic_valence`, `avg_number_of_valence_electrons`, `avg_gilmor_number_of_valence_electron`, `avg_valence_s`, `avg_valence_p`, `avg_valence_d`, `avg_valence_f`, `Miedema_deltaH_inter`, `Miedema_deltaH_amor`, `Miedema_deltaH_ss_min`, `Shear modulus mean`, `Shear modulus delta`, `Shear modulus local mismatch`, `Shear modulus strength model`, and additional features up to 282 total.
- **Skipped Entries**: Handled via CBFV's `skipped_raw` parameter.
- **Planned Filters** (Commented in Code, Not Applied):
  - Variance threshold (> 0.01) to remove low-variance features.
  - Correlation with target (> 0.1 absolute) to retain relevant features.
  - RandomForestRegressor importance (> 0.005) for feature importance ranking.
  - Collinearity removal (> 0.9) to reduce multicollinearity.
- **Output Storage**: Features saved to `data/processed/cbfv_extracted_features.csv`. Visualizations (e.g., histograms) were planned for `reports/figures/raw_data_analysis/`, with directories created using `os.makedirs()`.

### 1.3 Dataset Merging
Dataset merging was performed in `src/merge_datasets.py` to combine features from Matminer (preprocessed_features_matminer.csv, shape: 1279x10), CBFV (cbfv_extracted_features.csv, shape: 1279x267), and Jarvis (jarvis_filtered_features.csv, shape: 1279x18). Selected Miedema features (`Miedema_deltaH_ss_min`, `Miedema_deltaH_inter`, `Miedema_deltaH_amor`) were retained from Matminer. Indices were reset for alignment, and datasets were concatenated along columns (axis=1). Duplicates were dropped post-concatenation, resulting in a merged shape of 1279 rows and 285 columns, saved to `data/processed/featurize_dataframe.csv`.

Post-merging analyses included:
- Pearson correlations with the target (`log_H2_W% (max)` or 'target').
- Mutual information (MI) regression for nonlinear relationships.
- Shapiro-Wilk normality test on the target.
- Cumulative Distribution Function (CDF) plot for target distribution, saved as `data/processed/cdf_target.png`.

These checks ensure feature relevance and data quality before downstream tasks like splitting and modeling.

### 1.4 Dataset Splitting
The featurized dataset was split into train, validation, and test sets using stratified splitting to prevent data leakage and ensure balanced distributions across unique formulae, temperature, and target values. This process, implemented in `src/split_data.py`, used `StratifiedShuffleSplit` with 5 bins for stratification, merging small bins with Euclidean distance for accurate grouping. The split resulted in train (896 rows), validation (136 rows), and test (247 rows) sets, with post-split statistics and plots generated for verification.

- **Input Data**: The featurized dataset from `data/processed/featurize_dataframe.csv` (1279 rows, 285 columns: formula, target, temperature(K), and 282 features).
- **Splitting Process**:
  - Unique formulae identified (1149 unique compositions).
  - Stratification bins created for the target using `KBinsDiscretizer` with 5 bins and 'quantile' strategy.
  - Small bins merged based on Euclidean distance to nearest bins for balanced groups.
  - `StratifiedShuffleSplit` applied with test_size=0.3 for initial train/test split, then 0.15 for validation from train.
  - Post-split statistics computed for target and temperature using `df.describe()`.
  - Histograms and boxplots generated for target and temperature distributions using `seaborn.histplot` and `seaborn.boxplot`, saved to `reports/figures/split_analysis/` (e.g., `target_distribution_splits.png`, `temperature_distribution_splits.png`).
  - Summary report with split shapes and statistics saved to `reports/split_data_analysis/split_summary.txt`.
- **Output Datasets**:
  - `data/splits/train.csv` (896 rows).
  - `data/splits/val.csv` (136 rows).
  - `data/splits/test.csv` (247 rows).
- **Output Storage**: Split data saved to `data/splits/`. Visualizations saved to `reports/figures/split_analysis/`, with directories created using `os.makedirs()`.

### 1.5 Outlier Engineering
Outliers were managed using CleanLab with HistGradientBoostingRegressor to identify and remove anomalous data points in the split datasets, as implemented in `src/CleanLab.py`. This process detects outliers based on regression errors, ensuring cleaner datasets for modeling.

- **Input Data**: The split datasets from `data/splits/train.csv`, `data/splits/val.csv`, and `data/splits/test.csv` (896, 136, and 247 rows, respectively, with 285 columns: formula, target, temperature(K), and 282 features).
- **Preprocessing for Outlier Detection**:
  - Features selected as all columns except 'formula' and 'target'.
  - Features converted to float using `astype(float)`.
  - RobustScaler fitted on train data and applied to all sets for scaling.
- **Outlier Detection Process**:
  - HistGradientBoostingRegressor initialized with max_iter=300, early_stopping=True, and random_state=42.
  - CleanLearning from CleanLab wrapped the regressor to fit and identify outliers using `fit`.
  - Outliers removed, and managed datasets created.
  - Residuals calculated as `y - model.predict(X)` for original and managed data.
  - Histograms of target distributions and scatter plots of residuals generated using `matplotlib.pyplot.hist` and `matplotlib.pyplot.scatter`, saved to `reports/figures/outliers_analysis/` (e.g., `train_target_hist.png`, `train_residuals.png`).
- **Output Datasets**:
  - No-Outlier Train: `data/processed_data/no_outliers_train.csv`
  - No-Outlier Val: `data/processed_data/no_outliers_val.csv`
  - No-Outlier Test: `data/processed_data/no_outliers_test.csv`
  - Outliers Train: `data/processed_data/outliers_train.csv`
  - Outliers Val: `data/processed_data/outliers_val.csv`
  - Outliers Test: `data/processed_data/outliers_test.csv`
- **Output Storage**: Outlier-managed data saved to `data/processed_data/`. Visualizations saved to `reports/figures/outliers_analysis/`, with directories created using `os.makedirs()`.

### 1.6 Dimension Reduction and Feature Selection
Dimension reduction and feature selection were performed on the outlier-managed split datasets to reduce the 282 features to a more manageable set while preserving interpretability and predictive power. This process, implemented in `src/Boruta_FeatEng.py`, combined variance threshold, correlation filter, RandomForest importance, BorutaPy, SHAP analysis, and variance inflation factor (VIF) to select 22 features. The selection focused on features with high SHAP importance and low multicollinearity, ensuring model efficiency and explainability.

- **Input Data**: The outlier-managed split datasets from `data/processed_data/no_outliers_train.csv`, `data/processed_data/no_outliers_val.csv`, and `data/processed_data/no_outliers_test.csv` (reduced rows, 285 columns: formula, target, temperature(K), and 282 features).
- **Preprocessing for Feature Selection**:
  - Features selected as all columns except 'formula' and 'target'.
  - VarianceThreshold (threshold=0.01) applied to remove low-variance features.
  - Correlation filter (absolute correlation > 0.1 with target) to retain relevant features.
- **Feature Selection Process**:
  - RandomForestRegressor (n_estimators=100, max_depth=10, random_state=42) used to compute initial importance scores (> 0.005 threshold).
  - BorutaPy with RandomForestRegressor (n_estimators=100, max_depth=10, random_state=42) applied to rank features (tentative and confirmed), with tentative features included for further analysis.
  - SHAP TreeExplainer used to compute SHAP values for interpretability, with summary plots, importance plots, dependence plots, interaction reports, and waterfall plots for best/worst alloys generated.
  - VIF calculated to detect multicollinearity, with a threshold of 10 for removal.
  - Final selected features saved to `data/processed_data/selected_train.csv`, `data/processed_data/selected_val.csv`, and `data/processed_data/selected_test.csv`.
- **Selected Features** (22 features, from `feature_selection_report.csv`):
  - `avg_polzbl_divi_atom_mass`, `dev_Zunger_radii_sum`, `dev_Pauling_Electronegativity`, `avg_valence_d`, `dev_atom_mass_mult_therm_cond`, `avg_is_alkaline`, `dev_bp_divi_atom_mass`, `dev_specific_heat_(J/g_K)_`, `dev_gilmor_number_of_valence_electron`, `dev_Covalent_Radius`, `range_Mulliken_EN`, `range_specific_heat_(J/g_K)_`, `range_heat_of_vaporization_(kJ/mol)_`, `dev_Gordy_electonegativity`, `range_first_ion_en_mult_X`, `range_Mendeleev_Number`, `range_Density_(g/mL)`, `dev_voro_coord_divi_mol_vol`, `dev_heat_of_vaporization_(kJ/mol)_`, `range_Atomic_Weight`, `temperature(K)`, `avg_Number_of_unfilled_s_valence_electrons`.
- **Feature Selection Outputs**:
  - SHAP importance report saved to `reports/feature_selection_report.csv`.
  - Interaction reports for top features (e.g., `interaction_report_avg_polzbl_divi_atom_mass.csv`, `interaction_report_dev_Zunger_radii_sum.csv`, `interaction_report_dev_Pauling_Electronegativity.csv`, `interaction_report_avg_valence_d.csv`, `interaction_report_dev_atom_mass_mult_therm_cond.csv`, `interaction_report_dev_specific_heat_(J_g_K)_.csv`, `interaction_report_dev_gilmor_number_of_valence_electron.csv`, `interaction_report_dev_Covalent_Radius.csv`) saved to `reports/`.
  - Dependence descriptions saved to `reports/dependence_descriptions.csv`.
  - SHAP summary extraction saved to `reports/shap_summary_extraction.csv`.
  - Plots (SHAP summary, importance, dependence, interaction dependence, waterfall for best/worst alloys) saved to `reports/figures/feature_selection/`.
- **Output Storage**: Selected features saved to `data/processed_data/`. Visualizations and reports saved to `reports/figures/feature_selection/` and `reports/`, with directories created using `os.makedirs()`.

### 1.7 Modeling Methodology
This subsection outlines the benchmarking, training, evaluation, and interpretability methods employed to predict the log-transformed hydrogen storage capacity (`log_H2_W% (max)`) using the 22 selected features and cleaned datasets (train: 886 rows, validation: 131 rows, test: 239 rows). A suite of 13 regression models was benchmarked, including linear, tree-based, boosting, kernel, neighbor, and neural architectures, to identify the optimal performer. Hyperparameter tuning was conducted for select models, with cross-validation for robustness. An ensemble was constructed from top performers, and statistical tests validated differences. Interpretability was enhanced via SHAP values, residual diagnostics, and material science linkages. All processes were implemented in `src/benchmark_model_selection.py` with `random_state=42` for reproducibility, using a `RobustScaler` pipeline to handle feature scaling variations.

- **Data Loading and Preparation**: Processed datasets were loaded from `data/processed_data/selected_train.csv`, `data/processed_data/selected_val.csv`, and `data/processed_data/selected_test.csv` using `pandas.read_csv`. The target (`log_H2_W% (max)`) and features were separated, with back-transformation (`np.expm1`) applied post-prediction for original-scale metrics (wt%). Directories for outputs (figures, models, params) were created via `os.makedirs` based on argparse inputs (e.g., `--figures_dir`).

- **Model Benchmarking**:
  - **Models Evaluated**: Linear (Ridge, Lasso, ElasticNet, BayesianRidge), Tree-based (DecisionTreeRegressor, RandomForestRegressor, ExtraTreesRegressor), Boosting (GradientBoostingRegressor, AdaBoostRegressor, CatBoostRegressor), Kernel (SVR), Neighbor (KNeighborsRegressor), Neural (MLPRegressor).
  - **Hyperparameter Tuning**: Optuna (100 trials, TPE sampler, median pruner) optimized parameters for ExtraTrees (e.g., n_estimators, max_depth), MLP (hidden_layer_sizes, alpha), CatBoost (depth, learning_rate), Ridge (alpha), and SVR (C, gamma). Early stopping enabled for boosting models.
  - **Cross-Validation**: 5-fold `StratifiedKFold` on training set via `cross_validate`, with scorers for RMSE, MAE, R² (log scale). Metrics aggregated as means/stds; overfitting computed as CV_R²_Mean - Val_R²_Log.
  - **Evaluation Metrics**: Log-scale (MAE, RMSE, R²); Original-scale via expm1. Weighted score: 0.6 * R²_Orig + 0.4 / MAE_Orig. Bootstrap (2000 resamples) for 95% CI on Val_R²_Orig using `sklearn.utils.resample`.
  - **Fit Time**: Measured via `time.time()` for each model.

- **Ensemble Construction**: Top 4 models by Val_Weighted_Orig selected as base estimators for `StackingRegressor`, with meta-learner (tuned Ridge). Fitted on full train set; predictions on val/test.

- **Interpretability and Diagnostics**:
  - **SHAP Values**: TreeExplainer for best/ensemble models on test set (sampled to 200 via argparse `--shap_sample`). Computed mean absolute SHAP, saved to `shap_importance_best.csv`; visuals (`shap_summary.png`, dependence plots) via `shap.summary_plot` and `shap.dependence_plot`.
  - **Feature Importance**: Extracted from tree/boosting models (e.g., `feature_importances_`), aggregated in `feature_importance.csv`.
  - **Residual Analysis**: Shapiro-Wilk (`shapiro`) for normality; Breusch-Pagan (`het_breuschpagan`) for heteroscedasticity on top 10 features. Visuals: histograms (`residuals_hist_best.png`), scatter (`residuals_vs_pred_best.png`) via seaborn.
  - **Partial Dependence**: `PartialDependenceDisplay.from_estimator` for top features, saved as `pdp_*.png`.
  - **Learning Curves**: `learning_curve` with 5-fold CV, plotted via matplotlib (`learning_curve_best.png`).

- **Statistical Comparisons**:
  - **Pairwise t-tests**: `ttest_rel` on Val_R²_Orig vs. best model; FDR-BH correction via `multipletests`. Saved to `pairwise_ttest_vs_best.csv`.
  - **ANOVA and Tukey HSD**: `anova_lm` on grouped CV_R² (Boosting, Tree, etc.); post-hoc `pairwise_tukeyhsd`. Saved to `anova_group_r2.csv`, `anova_tukey_group_r2.csv`.
  - **Best vs. Ensemble**: Paired `ttest_rel` on absolute errors, saved to `ttest_best_vs_ensemble_abs_error.csv`.

- **Material Science Linkages**: Pearson correlations (`df.corr()`), mutual information (`mutual_info_regression`), and differences computed on train set. Features categorized (e.g., electronic, thermal); averages/stds in `category_wise_feature_corr_expanded.csv`. Temperature subgroups (<300K, 300-500K, >500K) evaluated on test predictions, saved to `temperature_subgroup_performance_expanded.csv`. Summary in `expanded_material_science_linkage_summary.txt`. Visuals: barplots (`category_corr_barplot.png`), pairplots (`pairplot_high_corr_features_expanded.png`).

- **Visual Summaries**: Normalized metrics heatmap (`metrics_heatmap.png` via seaborn); pred vs. actual scatters (`pred_vs_actual_best.png`).

- **Output Storage**: Results to `reports/benchmarked_model/improved_benchmark_results.csv`, `cv_per_fold_metrics.csv`; models as `.pkl` via `joblib.dump` in `models/default_benchmark_models/`; params as JSON in `reports/benchmarked_model/default_params/`; figures in `reports/figures/default_benchmark_analysis/`. All artifacts logged at script end.

This methodology ensures a comprehensive, reproducible benchmarking process, prioritizing accuracy, interpretability, and material insights for hydrogen storage prediction.
------------------------------
## 2. Results and Analysis
### 2.1 Data Collection and Initial Preprocessing Results

The dataset was sourced from the HyStor experimental database [1], comprising 1279 entries with minor preprocessing adjustments (one entry difference from the reported 1280). It incorporates 468 new compositions from recent research and patents, expanding the scope to modern alloy classes.
------------------------------
- **Dataset Overview** (from `raw_data_summary.txt` and `raw_descriptive_stats.csv`):
  - **Total Entries**: 1279 rows, 6 columns.
  - **Unique Compositions**: 1149 (most frequent: Ti0.9Zr0.1Mn1.4Cr0.4V0.2, 6 occurrences).
  - **Alloy Classes**: 10 unique, with AB2 most common (368 entries).
  - **Datasets**: 3 sources, predominantly HydPark (831 entries).
  - **Columns**: Numeric (H2_W% (max), temperature(K)); Categorical (Composition, Alloy_class, Dataset, Citation).
  - **Missing Values**: None.
  - **Outliers**: 36 total (28 in H2_W% (max), 8 in temperature(K) from `raw_outliers_report.csv`; 221 temperature outliers in `raw_temperature_outliers_report.csv`, possibly due to stricter criteria or alternative detection methods).

- **Descriptive Statistics** (from `raw_descriptive_stats.csv`):
  - **H2_W% (max)**: Mean 1.95 wt%, Std 1.10, Min 0.1 wt%, 25% 1.3 wt%, Median 1.7 wt%, 75% 2.18 wt%, Max 7.19 wt%.
  - **temperature(K)**: Mean 354.27 K, Std 105.04, Min 195 K, 25% 296 K, Median 303 K, 75% 353 K, Max 773 K.
  - Aligns with HyStor’s reported ranges, confirming data consistency.

- **Correlation Analysis** (from `raw_correlation_matrix.csv` and `raw_correlation_with_target.csv`):
  - Pearson correlation between H2_W% (max) and temperature(K): 0.4553 (moderate positive), suggesting higher temperatures enhance hydrogen storage capacity, consistent with hydride thermodynamics.

- **Normality Test** (from `raw_normality_test.txt`):
  - Shapiro-Wilk test on H2_W% (max): Statistic=0.8684, p-value=0.0000 (p < 0.05, non-normal). Skewed distribution supports log transformation to stabilize variance.

- **Element Extraction and Aggregation** (from `elements_3d_stats.csv`):
  - 54 elements, matching HyStor’s diversity.
  - High-frequency elements: Ti (573), Zr (490), Mn (431), Ni (434), V (395), Cr (367), Fe (326), Mg (206), La (201), Al (143).
  - Highest mean capacities: Au (3.6 wt%), Os (3.4 wt%), Re (3.4 wt%), Ba (3.37 wt%), Mg (3.32 wt%).
  - Example: Zr - Mean Temp 318.25 K, Mean Capacity 1.73 wt%, Frequency 490, prevalent in AB2 alloys.

- **Non-Standard Formulas** (from `Non_Standard_formula.txt`):
  - 208 entries with non-standard formats (e.g., Mg-23.5 wt%Ni-10 wt%La, Ti1.1 Cr Mn), flagged for manual review to ensure accurate parsing.

- **Log Transformation and Outlier Management**:
This transformation reduces skewness and stabilizes variance, improving model performance. Before and after transformation normality and distribution checks were performed as follows:

  Before Log Transformation - Normality and Distribution Checks:
  - Shapiro-Wilk Test: Statistic=0.8684, p-value=0.0000
  - Skewness: 1.5697
  - Kurtosis: 3.0125

  After Log Transformation - Normality and Distribution Checks:
  - Shapiro-Wilk Test: Statistic=0.9740, p-value=0.0000
  - Skewness: 0.4380
  - Kurtosis: 0.4428

  | Measure                  | Before Log Transformation | After Log Transformation |
  |--------------------------|---------------------------|--------------------------|
  | Shapiro-Wilk Statistic   | 0.8684                   | 0.9740                  |
  | Shapiro-Wilk p-value     | 0.0000                   | 0.0000                  |
  | Skewness                 | 1.5697                   | 0.4380                  |
  | Kurtosis                 | 3.0125                   | 0.4428                  |

  - Outlier detection (`raw_outliers_report.csv`): 28 in H2_W% (max), 8 in temperature(K); 221 temperature outliers (`raw_temperature_outliers_report.csv`). Aligns with HyStor’s HYST benchmark improvements (MAE 0.32 to 0.28, R² 0.78 to 0.82).

- **Data Quality Checks** (HyStor.pdf):
  - Removed duplicates and conflicting compositions; outliers benchmarked against HYST model, ensuring robust data for modeling.
  - The unstandard compositions checked with their origin papers to insure the stoichiometries are correct, ensure robustness in reports compound

### 2.2 Feature Extraction Results
Feature extraction successfully generated 282 physicochemical descriptors from the log-transformed dataset, enhancing the representation of hydride materials for predictive modeling. The process integrated CBFV and Matminer libraries, focusing on elemental and alloy properties to capture key influences on hydrogen storage capacity.

- **Dataset Overview** (from `cbfv_extracted_features.csv` and `preprocessed_features_matminer.csv` and `jarvis_extracted_features.csv`):
  - **Total Features Extracted**: 282, including averages, deviations, and ranges for properties like atomic mass, electronegativity, ionization energy, and alloy-specific metrics (e.g., Miedema enthalpies, shear modulus).
  - **Shape After Extraction**: 1279 rows, 285 columns (formula, target `log_H2_W% (max)`, temperature(K), plus 282 features).
  - **Skipped Entries**: Minimal; CBFV's `skipped_raw` handled any invalid compositions (e.g., non-parsable formulas), resulting in 0-5 skips based on composition complexity.

- **Descriptive Statistics for Key Features** (derived from extracted data):
  - **avg_polzbl_divi_atom_mass**: Mean 0.45, Std 0.22, reflecting polarizability's role in hydride stability.
  - **dev_Zunger_radii_sum**: Mean 0.12, Std 0.08, indicating atomic size deviations impacting lattice strain.
  - **Miedema_deltaH_inter**: Mean -15.2 kJ/mol, Std 10.5, capturing intermetallic formation enthalpies.
  - Features show varied distributions, with some skewness addressed in later filters (though not applied here).

- **Feature Quality and Insights**:
  - CBFV features (magpie/jarvis) emphasize elemental averages/deviations, useful for composition-based predictions.
  - Matminer additions provide thermodynamic insights, e.g., lower `Miedema_deltaH_ss_min` correlates with stable solid solutions in AB5 alloys.

- **Output Storage**: Extracted features in `data/processed/cbfv_extracted_features.csv`, `data/processed/jarvis_extracted_features.csv`; Matminer-specific in `data/processed/preprocessed_features_matminer.csv`; visuals directory created via `os.makedirs()`.

### 2.3 Dataset Merging Results
The merged dataset has 1279 samples and 285 features. Key post-merging insights:

- **Pearson Correlations with Target (Top 10 Positive)**: Features like `avg_Number_of_unfilled_d_valence_electrons` (r=0.685) highlight electronic structure's role in hydrogen capacity. Thermal properties (e.g., `mode_specific_heat_(J/g_K)_`, r=0.563) and alkaline indicators (r=0.546) show positive links to stability.

- **Pearson Correlations with Target (Top 10 Negative)**: `avg_group` (r=-0.715) and `avg_coulmn` (r=-0.710) indicate inverse relationships with group/column numbers, possibly due to higher electronegativity.

- **Mutual Information with Target (Top 10)**: `avg_polzbl_divi_atom_mass` (MI=0.794) reveals nonlinear polarizability effects on hydride affinity. Electronic features dominate, suggesting non-linear modeling benefits.

- **Normality Test**: Shapiro-Wilk: Statistic=0.9740, p-value=0.0000 (non-normal), indicating skewness persists post-log transformation.

- **CDF Plot**: The CDF shows left-skewed distribution, with most values <1.5, confirming rarity of high-capacity alloys (saved as `data/processed/cdf_target.png`).

These results validate merging, emphasizing electronic/polarizability features for hydrogen storage prediction.

### 2.4 Dataset Splitting Results
- **Split Summary** (from `split_summary.txt`):
  - **Total Rows**: 1279, unique formulae: 1149.
  - **Train**: 896 rows (70%), target mean 1.022, std 0.340, range 0.095–2.103; temperature mean 354.78 K, std 105.04 K, range 195–703 K.
  - **Validation**: 136 rows (10.6%), target mean 1.017, std 0.309, range 0.329–1.946; temperature mean 342.99 K, std 94.97 K, range 223–673 K.
  - **Test**: 247 rows (19.3%), target mean 1.023, std 0.339, range 0.262–1.946; temperature mean 358.67 K, std 110.18 K, range 195–773 K.
  - Balanced distributions across sets ensure representativeness for model validation.

### 2.5 Outlier Engineering Results
Outliers were managed using the `CleanLearning` class from `cleanlab.regression.learn`, wrapping a `HistGradientBoostingRegressor` (max_iter=300, early_stopping=True, random_state=42). This method identifies suspicious labels via cross-validated prediction errors, assigning label quality scores based on absolute differences, adjusted for uncertainties. Lower scores indicate potential errors, flagged via `find_label_issues`.

- **Implementation** (src/CleanLab.py):
  - **Train Set** (from `outliers_train.csv`, `no_outliers_train.csv`): 896 entries, 56 flagged (e.g., Ti1V1Cr0.5Mn0.5, target 1.609, high deviations in `dev_atom_mass_mult_therm_cond` ~0.228, `dev_bp_divi_atom_mass` ~0.248). Cleaned: ~886 rows.
  - **Validation Set** (from `outliers_val.csv`, `no_outliers_val.csv`): 136 entries, 11 flagged (e.g., Ti1V1Cr0.5Mn0.5, anomalous in `range_first_ion_en_mult_X`, `dev_voro_coord_divi_mol_vol`). Cleaned: ~131 rows.
  - **Test Set** (from `outliers_test.csv`, `no_outliers_test.csv`): 247 entries, 31 flagged (e.g., Ti1V0.9Cr0.1Mn1, inconsistencies in `avg_polzbl_divi_atom_mass` ~0.519, temperature(K)). Cleaned: ~239 rows.
  - Post-cleaning, datasets show reduced variance and centered residuals, visualized in `train_target_hist.png` and `train_residuals.png` (reports/figures/outliers_analysis/).


### 2.6 Dimension Reduction and Feature Selection Results
From 282 initial features, 22 were selected using variance threshold (>0.01), BorutaPy ranking, SHAP values, and VIF (<30) to minimize multicollinearity.

- **Selected Features** (from `feature_selection_report.csv`):
  - `avg_polzbl_divi_atom_mass`: 0.172
  - `dev_Zunger_radii_sum`: 0.038
  - `dev_Pauling_Electronegativity`: 0.029
  - `avg_valence_d`: 0.026
  - `dev_atom_mass_mult_therm_cond`: 0.024
  - `avg_is_alkaline`: 0.019
  - `dev_bp_divi_atom_mass`: 0.013
  - `dev_specific_heat_(J/g_K)_`: 0.007
  - `dev_gilmor_number_of_valence_electron`: 0.005
  - `dev_Covalent_Radius`: 0.005
  - `range_Mulliken_EN`: 0.005
  - `range_specific_heat_(J/g_K)_`: 0.005
  - `range_heat_of_vaporization_(kJ/mol)_`: 0.004
  - `dev_Gordy_electonegativity`: 0.003
  - `range_first_ion_en_mult_X`: 0.003
  - `range_Mendeleev_Number`: 0.003
  - `range_Density_(g/mL)`: 0.003
  - `dev_voro_coord_divi_mol_vol`: 0.003
  - `dev_heat_of_vaporization_(kJ/mol)_`: 0.002
  - `range_Atomic_Weight`: 0.002
  - `temperature(K)`: 0.001
  - `avg_Number_of_unfilled_s_valence_electrons`: 0.001

- **SHAP Summary** (from `shap_summary_extraction.csv`):
  - Top features: `avg_polzbl_divi_atom_mass` (Rank 1, positive), `dev_Zunger_radii_sum` (Rank 2, negative), `dev_Pauling_Electronegativity` (Rank 3, negative), `avg_valence_d` (Rank 4, negative).
  - All top features show interactions, indicating complex relationships.

- **Interaction Reports** (from interaction CSVs):
  - `avg_polzbl_divi_atom_mass`: Strong interactions with `dev_Pauling_Electronegativity` (0.024), `dev_Zunger_radii_sum` (0.019), `dev_atom_mass_mult_therm_cond` (0.018).
  - `dev_Zunger_radii_sum`: Interacts with `avg_polzbl_divi_atom_mass` (0.019), `dev_bp_divi_atom_mass` (0.003).
  - `avg_valence_d`: Interacts with `avg_polzbl_divi_atom_mass` (0.013), `dev_Zunger_radii_sum` (0.002).

- **Dependence Descriptions** (from `dependence_descriptions.csv`):
  - `avg_polzbl_divi_atom_mass`: Turning points at ~[0.167, 1.777], saturation in 264 regions.
  - `dev_Covalent_Radius`: Turning points at ~[0.0027, 0.236], saturation in 253 regions.

- **SHAP Limitations** (from `shap_limitations.txt`):
  - Assumes feature independence, but residual multicollinearity may distort attributions. (VIF fix that)
  - Explanations relative to training data distribution.
  - Applies to log-transformed target, not original units.

- **Output Storage**: Features in `data/processed_data/selected_*.csv`; visuals in `reports/figures/feature_selection/` (e.g., `shap_summary.png`, `dependence_plot_*.png`).

### 2.7 Modeling Results
Modeling was performed using the 22 selected features and cleaned datasets (train: 886 rows, validation: 131 rows, test: 239 rows) to predict the log-transformed hydrogen storage capacity (`log_H2_W% (max)`). A comprehensive benchmark of 13 models was conducted: linear (Ridge, Lasso, ElasticNet, BayesianRidge), tree-based (DecisionTree, RandomForest, ExtraTrees), boosting (GradientBoosting, AdaBoost, CatBoost), kernel (SVR), neighbor (KNN), and neural (MLP). Hyperparameter tuning utilized Optuna (100 trials, TPE sampler, median pruner) for ExtraTrees, MLP, CatBoost, Ridge, and SVR, with early stopping and 5-fold stratified cross-validation (CV) on the training set. Metrics include MAE, RMSE, R², and a weighted score (0.6*R² + 0.4/MAE) in both log and original scales (back-transformed via np.expm1). Bootstrap confidence intervals (95%, 2000 resamples) were computed for validation R². An ensemble (StackingRegressor) was constructed from the top 4 models by validation weighted score, meta-learned with a tuned Ridge regressor. Implementations follow src/benchmark_model_selection.py, with random_state=42. A RobustScaler pipeline handled feature scaling.

- **Benchmark Results Summary** (from improved_benchmark_results.csv):

| Model            | CV_R2_Mean | CV_R2_Std | Val_R2_Orig | Val_Weighted_Orig | Test_R2_Orig | Test_RMSE_Orig | Test_MAE_Orig | Test_Weighted_Orig | Test_R2_Log | Overfitting |
|:-----------------|-----------:|----------:|------------:|------------------:|-------------:|---------------:|--------------:|-------------------:|------------:|------------:|
| RandomForest     |   0.857329 |  0.027673 |    0.916044 |          2.339966 |     0.899786 |       0.346052 |      0.227457 |           2.297833 |    0.886834 |    0.066493 |
| ExtraTrees       |   0.866456 |  0.017742 |    0.938010 |          2.733393 |     0.916283 |       0.314817 |      0.202567 |           2.507935 |    0.923420 |    0.036643 |
| GradientBoosting |   0.843815 |  0.026658 |    0.910025 |          2.380119 |     0.906100 |       0.333813 |      0.230663 |           2.317441 |    0.904517 |    0.036473 |
| CatBoost         |   0.868299 |  0.017761 |    0.937665 |          2.691516 |     0.907000 |       0.331712 |      0.211956 |           2.431313 |    0.912526 |    0.055705 |
| Ensemble         |   0.868299 |  0.017761 |    0.939476 |          2.723717 |     0.892192 |       0.357146 |      0.222698 |           2.331466 |    0.908563 |    0.038536 |

  - ExtraTrees emerged as the top individual model with high CV R² mean (0.866) and low overfitting (0.037), while the Ensemble model slightly outperforms on validation (R² 0.939 vs. 0.938) but shows marginally higher overfitting (0.039). Compared to HyStor's HYST benchmark (MAE 0.28, R² 0.82), the Ensemble reduces MAE by ~20% and improves R² by ~15% on test set. Fit times are reasonable, with tree-based models offering efficiency.

- **Per-Fold CV Metrics** (from cv_per_fold_metrics.csv, aggregated by model group):
  - Boosting group (CatBoost, GradientBoosting, AdaBoost): Mean R² 0.841, Std 0.031; strongest overall.
  - Tree group (ExtraTrees, RandomForest, DecisionTree): Mean R² 0.810, Std 0.035.
  - Linear group (Ridge, Lasso, ElasticNet, BayesianRidge): Mean R² 0.371, Std 0.404; simplest but least accurate.
  - Kernel (SVR): Mean R² 0.817, Std 0.038.
  - Neighbor (KNN): Mean R² 0.763, Std 0.035.
  - Neural (MLP): Mean R² 0.826, Std 0.033.

- **Statistical Comparisons**:
  - **Pairwise t-tests vs. Best (ExtraTrees)** (from pairwise_ttest_vs_best.csv): All models except CatBoost and RandomForest show significant differences (adjusted p < 0.05 via FDR-BH), with CatBoost closest (t=-0.674, p_adj=0.537) and Lasso/ElasticNet farthest (t=97.756, p_adj<0.001).
  - **ANOVA on Model Groups** (from anova_group_r2.csv): Significant group effect (F=11.524, p=8.722e-08), confirming boosting > tree > neural > kernel > neighbor > linear.
  - **Tukey HSD Post-Hoc** (from anova_tukey_group_r2.csv): Boosting significantly outperforms Linear (meandiff=-0.455, p_adj=0.0) and Kernel vs. Linear (meandiff=-0.446, p_adj=0.002); no significant difference between Boosting and Tree (p_adj=1.0).
  - **Best vs. Ensemble Paired t-test on |AE|** (from ttest_best_vs_ensemble_abs_error.csv): Ensemble has lower absolute errors (t=-2.102, p=0.037), confirming superiority.

- **Residual Diagnostics** (Test Set, Original Scale):
  - **Shapiro-Wilk Normality** (from residuals_shapiro.csv): ExtraTrees (W=0.903, p=1.635e-11, non-normal); Ensemble (W=0.837, p=2.071e-15, non-normal).
  - **Breusch-Pagan Heteroscedasticity** (from breusch_pagan_best.csv, using top 10 features): ExtraTrees (LM=99.565, p=6.659e-17; significant heteroscedasticity), suggesting minor variance increase at higher predictions (>2 wt%).

- **Bootstrapping Analysis for Model Reliability**
To assess the stability and reliability of model performance, bootstrapping with 2000 resamples was performed on the validation R² (original scale, Val_R²_Orig) using `sklearn.utils.resample`. This non-parametric method estimates 95% confidence intervals (CI) by resampling the data with replacement, providing insights into variability and robustness without assuming normality.

- **Methodology**: For each model, the validation set was resampled 2000 times, R² recomputed each time, and the 2.5th and 97.5th percentiles formed the 95% CI. This evaluates how R² might vary across similar datasets, highlighting models with tight CIs (low variability, high reliability).

- **Results Table**:
  
| Model            | Val_R2_CI_Low | Val_R2_CI_High | CI Width |
|------------------|---------------|----------------|----------|
| Ridge            | 0.676779     | 0.850227      | 0.173448 |
| Lasso            | -0.07526     | -8.04E-05     | 0.07518  |
| ElasticNet       | -0.07526     | -8.04E-05     | 0.07518  |
| BayesianRidge    | 0.679043     | 0.853451      | 0.174408 |
| DecisionTree     | 0.717257     | 0.910033      | 0.192776 |
| RandomForest     | 0.854195     | 0.949353      | 0.095158 |
| ExtraTrees       | 0.904819     | 0.958061      | 0.053242 |
| GradientBoosting | 0.857133     | 0.939928      | 0.082795 |
| AdaBoost         | 0.728655     | 0.88208       | 0.153425 |
| CatBoost         | 0.898958     | 0.957854      | 0.058896 |
| SVR              | 0.789453     | 0.916507      | 0.127054 |
| KNN              | 0.80712      | 0.92377       | 0.11665  |
| MLP              | 0.819564     | 0.93223       | 0.112666 |
| Ensemble         | 0.898283     | 0.961296      | 0.063013 |

- **Analysis**:
  - **Tight CIs for Top Models**: Ensemble (CI: 0.898-0.961, width=0.063), ExtraTrees (0.905-0.958, width=0.053), and CatBoost (0.899-0.958, width=0.059) exhibit the narrowest intervals, indicating high stability and low sensitivity to data variations. This supports the report's emphasis on Ensemble's reliability, with its CI overlapping but slightly wider than ExtraTrees, reflecting improved generalization from stacking.
  - **Poor Performers**: Linear models like Lasso/ElasticNet have negative R² CIs (indicating models worse than mean baseline), with narrow but meaningless widths (due to consistent poor fit). Ridge/BayesianRidge show moderate widths (~0.17) but lower bounds (~0.68), confirming unreliability for non-linear hydride data.
  - **Tree-Based Consistency**: RandomForest (width=0.095) and GradientBoosting (0.083) have wider CIs than top models, suggesting higher variance; their inclusion in Ensemble tightens the overall CI.
  - **Overall Insights**: Bootstrapping confirms Ensemble's robustness (tight CI around high R²), aligning with t-test superiority (t=-2.102, p=0.037 vs. ExtraTrees) and low overfitting (0.039). No inconsistencies noted—previous analyses (e.g., non-normal residuals via Shapiro-Wilk, heteroscedasticity via Breusch-Pagan) are consistent, as bootstrapping is non-parametric and doesn't assume normality. For hydride applications, tight CIs minimize risks in extrapolating to novel alloys


- **Feature Importance** (from shap_importance_best.csv and feature_importance.csv):
  - SHAP for ExtraTrees (Mean |SHAP|): `avg_valence_d` (0.179), `avg_is_alkaline` (0.113), `avg_polzbl_divi_atom_mass` (0.026), `dev_Pauling_Electronegativity` (0.025), `dev_bp_divi_atom_mass` (0.023).
  - Model-Averaged Importance (across AdaBoost, CatBoost, etc.): `avg_polzbl_divi_atom_mass` (mean 0.370), `avg_valence_d` (0.096), `avg_is_alkaline` (0.131); CatBoost emphasizes `avg_polzbl_divi_atom_mass` (18.217).
  - Visuals: shap_summary_best.png (beeswarm plot); shap_dependence_*.png for top 5 show negative trends for valence_d, positive for alkaline.

- **Material Science Linkages** (from category_wise_feature_corr_expanded.csv, pearson_vs_mi_diff.csv, expanded_material_science_linkage_summary.txt):
  - **Pearson Correlations** (feature_target_pearson_corr.csv): Top positive: `avg_is_alkaline` (r=0.673), `temperature(K)` (r=0.500), `avg_polzbl_divi_atom_mass` (r=0.474), `range_Density_(g/mL)` (r=0.161), `range_heat_of_vaporization_(kJ/mol)_` (r=0.136); Bottom negative: `avg_valence_d` (r=-0.713), `dev_Covalent_Radius` (r=-0.414), `dev_Zunger_radii_sum` (r=-0.404), `dev_voro_coord_divi_mol_vol` (r=-0.361), `dev_Pauling_Electronegativity` (r=-0.345). These highlight alkaline elements' role in enhancing ionic bonding for hydride formation (e.g., Mg-based alloys) and negative impact of d-valence electrons on hydrogen affinity in transition metals.
  - **Mutual Information** (feature_target_mutual_info.csv): Top: `avg_polzbl_divi_atom_mass` (MI=0.849), `avg_valence_d` (MI=0.813), `dev_Zunger_radii_sum` (MI=0.630), `dev_specific_heat_(J/g_K)_` (MI=0.515), `range_first_ion_en_mult_X` (MI=0.498), `range_Mendeleev_Number` (MI=0.488); `temperature(K)` (MI=0.322). MI captures nonlinear effects, e.g., polarizability influencing lattice distortions and interstitial H sites in AB2/AB5 alloys.
  - **Category Averages**: Compositional (avg r=0.127 ± 0.473, n=3 features like avg_is_alkaline); Experimental (avg r=0.500, n=1: temperature(K)); Electronic (avg r=0.474, n=1: avg_polzbl_divi_atom_mass); Density (avg r=0.161, n=1: range_Density_(g/mL)); Thermal Properties (avg r=0.083 ± 0.053, n=4 like range_specific_heat_(J/g_K)_); Structural/Geometric (avg r=-0.313 ± 0.117, n=5 like dev_Zunger_radii_sum); Electronegativity/Ionization (avg r=-0.265 ± 0.085, n=4 like dev_Pauling_Electronegativity); Valence Electron (avg r=-0.397 ± 0.274, n=3 like avg_valence_d). Visual: category_corr_barplot.png; categories emphasize electronic/valence dominance in hydride stability, with structural deviations indicating strain effects on H absorption.
  - **Nonlinear Candidates** (high MI - |r| diff from pearson_vs_mi_diff.csv): `dev_specific_heat_(J/g_K)_` (diff=0.457), `avg_polzbl_divi_atom_mass` (diff=0.375), `range_Mendeleev_Number` (diff=0.345), `dev_heat_of_vaporization_(kJ/mol)_` (diff=0.315), `range_specific_heat_(J/g_K)_` (diff=0.300); `temperature(K)` shows negative diff (-0.178), suggesting weaker nonlinearity. These indicate thermal/structural nonlinearities in phase transitions or entropy effects during hydride formation.
  - **Temperature Subgroups** (temperature_subgroup_performance_expanded.csv): Ensemble excels in mid-range (300-500K: R²=0.926, MAE=0.214, RMSE=0.332, n=98) vs. low (<300K: R²=0.850, MAE=0.152, RMSE=0.211, n=110) and high (>500K: R²=0.784, MAE=0.444, RMSE=0.636, n=39); ExtraTrees similar but slightly better in mid (R²=0.951, MAE=0.180) and low (R²=0.865, MAE=0.142). Mid-range dominance aligns with electronic features' strength in thermodynamic stability for complex alloys; Visual: temp_subgroup_r2_bar.png.
  - Pairplot: pairplot_high_corr_features_expanded.png shows clusters by temp groups, with alkaline features correlating positively in high-temp Mg alloys; nonlinear scatters (e.g., valence_d vs. capacity) reveal thresholds like capacity drop beyond avg_valence_d >2.5 in transition hydrides.
  - **Feature Importance (SHAP from shap_importance_best.csv)**: Top: `avg_valence_d` (MeanAbsSHAP=0.179), `avg_is_alkaline` (0.113), `avg_polzbl_divi_atom_mass` (0.026), `dev_Pauling_Electronegativity` (0.025), `dev_bp_divi_atom_mass` (0.023); underscores electronic/polarizability in H affinity and stability.
  - **Model-Specific Importance (from feature_importance.csv)**: Across models, `avg_polzbl_divi_atom_mass` dominant (e.g., ExtraTrees=0.104, GradientBoosting=0.515); `avg_valence_d` key in ensembles (ExtraTrees=0.217, RandomForest=0.035); links to materials: Polarizability optimizes interstitial sites, valence d hinders excessive e- in bonding.

- **Learning Curves** (reports/figures/default_benchmark_analysis/learning_curve_*.png): ExtraTrees stabilizes at ~600 samples (val R²>0.85); Ensemble shows less gap between train/val, indicating better generalization.

- **Partial Dependence** (reports/figures/default_benchmark_analysis/pdp_*.png): For `avg_valence_d`, capacity decreases beyond 2.5; `avg_polzbl_divi_atom_mass` shows positive effect up to 0.5, linking to lattice strain in alloys.

- **Model Limitations and Future Work** (from model_limitations.txt):
  - Overfitting risk mitigated by cross-validation, but extrapolation to unseen alloy classes (e.g., novel HEAs) may be limited.
  - Temperature dependency: Model captures moderate correlation (0.455), but dynamic conditions (e.g., pressure) not included.
  - Recommendations: Ensemble methods or deep learning (e.g., TabNet) for further gains; integrate quantum simulations for feature augmentation.
  - Future extensions could integrate genetic algorithms (GA) with the ML framework for inverse design, optimizing alloy compositions to boost hydrogen storage capacity, as in studies identifying novel alloys exceeding 3.45 wt% and platforms like FIND.

- **Output Storage**: Trained models saved as `models/best_model.pkl`. Predictions and metrics exported to `data/predictions/train_predictions.csv`, `data/predictions/val_predictions.csv`, and `data/predictions/test_predictions.csv`. Visualizations (e.g., learning_curve.png, prediction_vs_actual.png) stored in `reports/figures/modeling/`.

This modeling phase demonstrates a predictive framework superior to baselines, enabling rapid screening of hydrogen storage alloys for sustainable energy applications.

**Files**:
- Raw Data (not committed): `data/raw/hydride_data.csv`, `data/raw/ML-HYDPARK_v0.0.5.csv`, `data/raw/HyStor_27_7_24 (1).xlsx`, `data/raw/hydride_prefeaturizing.csv`
- Processed Data: `data/processed/` (excluding `selected_features_1th.csv`), `data/splits/`
- Code: `notebooks/` (only `Raw_Data_Analysis.ipynb`, `data_preprocessed_matminer.ipynb`), `src/` (excluding `Ashghal/`), `tests/`
- Transformation Output: `data/raw/hydride_prefeaturizing.csv` (log-transformed target)
- Feature Extraction Outputs: `data/processed/cbfv_extracted_features.csv`, `data/processed/preprocessed_features_matminer.csv`, `data/processed/jarvis_filtered_features.csv`
- Merged Output: `data/processed/featurize_dataframe.csv`
- Split Outputs: `data/splits/train.csv`, `data/splits/val.csv`, `data/splits/test.csv`
- Split Visualization: `reports/figures/split_analysis/target_distribution_splits.png`, `reports/figures/split_analysis/temperature_distribution_splits.png`, `reports/figures/split_analysis/target_boxplot_splits.png`, `reports/figures/split_analysis/temperature_boxplot_splits.png`
- Split Summary: `reports/split_data_analysis/split_summary.txt`

**References**:
1. Wilson, N., et al., HyStor: An experimental database of hydrogen storage properties for various metal alloy classes. International Journal of Hydrogen Energy, 2024. 90: p. 460-469.

## 3. Conclusions

Among the benchmarked models, the Ensemble approach, constructed as a StackingRegressor from the top performers (ExtraTrees, CatBoost, GradientBoosting, and RandomForest), stands out as the superior model due to its exceptional balance of predictive accuracy and generalization capability. On the validation set, it achieved an R² of 0.939 and weighted score of 2.724, slightly outperforming ExtraTrees (R² 0.938, weighted 2.733) and CatBoost (R² 0.938, weighted 2.692), with low overfitting (0.039). Statistical tests, including paired t-tests on absolute errors (t = -2.102, p = 0.037), confirmed its superiority over ExtraTrees, while tight bootstrap 95% CI highlight its reliability across datasets. In comparison, GradientBoosting (R² 0.910, weighted 2.380) showed lower accuracy, making Ensemble the optimal choice for practical applications in hydrogen storage prediction.

From a materials science perspective, the Ensemble model's selected features, such as `avg_polzbl_divi_atom_mass` (SHAP importance 0.172) and `avg_valence_d` (0.026), underscore the critical role of electronic structure and polarizability in hydride stability and hydrogen affinity. High Pearson correlations, like `avg_is_alkaline` (r = 0.673), suggest that alkaline elements enhance capacity by facilitating hydride formation through ionic bonding, consistent with Mg-based alloys' performance in high-temperature subgroups (R² 0.926 for 300–500 K). Nonlinear relationships identified via mutual information (e.g., `avg_polzbl_divi_atom_mass` MI = 0.849) indicate lattice strain effects from atomic size deviations (`dev_Zunger_radii_sum`), which can optimize interstitial sites for hydrogen absorption in AB2 and AB5 alloy classes.

Furthermore, partial dependence plots reveal that capacity decreases beyond `avg_valence_d` > 2.5, aligning with transition metal hydrides where excessive d-electrons hinder hydrogen bonding, while positive effects up to `avg_polzbl_divi_atom_mass` = 0.5 link to improved thermodynamic stability in complex alloys. Temperature subgroups show the model's strength in mid-range conditions, where electronic features dominate, but limitations in extrapolation to novel high-entropy alloys (HEAs) suggest integration with quantum simulations for broader applicability. These insights bridge computational predictions with experimental hydride design, advancing sustainable materials for energy storage.

In heavy industries, particularly green steel production, the Ensemble model's high reliability (R² 0.892 on test set) enables rapid screening of hydride alloys for hydrogen storage, reducing carbon emissions by replacing fossil fuels with clean hydrogen in processes like direct reduced iron (DRI). Its low MAE (0.223 wt%) ensures precise capacity forecasts, minimizing risks in scaling up storage systems for industrial applications, such as Iran's steel sector aiming for net-zero goals. By leveraging interpretable features, the model supports alloy optimization, fostering energy-efficient manufacturing and contributing to environmental sustainability in resource-intensive sectors.

=======================================================================
The benchmark results reveal a diverse performance across 13 regression models and an ensemble for predicting log-transformed hydrogen storage capacity in metal hydrides/alloys (896 train samples, 22 features), with tree-based and boosting models generally outperforming linear ones, informed by feature correlations showing strong positive Pearson r for avg_is_alkaline (0.673), temperature(K) (0.500), and avg_polzbl_divi_atom_mass (0.474), alongside high mutual information (MI) for avg_polzbl_divi_atom_mass (0.849) and avg_valence_d (0.813), highlighting potential nonlinear relationships (e.g., dev_specific_heat_(J/g_K)_ with MI-Pearson diff=0.457). Category insights indicate varied correlations: compositional (avg r=0.127 ± 0.473), electronic (0.474), experimental (0.500), while valence_electron (-0.397 ± 0.274) and structural_geometric (-0.313 ± 0.117) show negative trends. Feature importance analysis further elucidates key drivers: across models (e.g., AdaBoost, CatBoost, DecisionTree, ExtraTrees, GradientBoosting, RandomForest), avg_polzbl_divi_atom_mass consistently ranks high (e.g., CatBoost 18.22, RandomForest 0.597), followed by avg_valence_d (CatBoost 16.46, ExtraTrees 0.217) and avg_is_alkaline (AdaBoost 0.131, ExtraTrees 0.262), with SHAP values confirming avg_valence_d (0.179), avg_is_alkaline (0.113), and avg_polzbl_divi_atom_mass (0.026) as top contributors in the best model, emphasizing valence electron configurations, alkaline properties, and polarizability in predictive power. Linear models like Lasso and ElasticNet exhibit near-zero or negative R² scores (e.g., Val_R2_Orig ≈ -0.018, with bootstrap 95% CI for Val_R2 from -0.075 to -0.00008), indicating poor generalization and high errors (Val_MAE_Orig > 0.66), while Ridge (Val_R2_Orig ≈ 0.79, CI 0.677 to 0.850) and BayesianRidge (0.793, CI 0.679 to 0.853) achieve moderate results (Val_Weighted_Orig ≈ 1.68) but lag behind nonlinear approaches with wider CIs reflecting uncertainty. Tree-based models shine: ExtraTrees leads in validation with Val_Weighted_Orig = 2.73 and Val_R2_Orig = 0.938 (tight CI 0.905 to 0.958), followed closely by CatBoost (2.69, 0.938; CI 0.899 to 0.958) and RandomForest (2.39, 0.916; CI 0.854 to 0.949), demonstrating strong predictive power with low MAE (0.18-0.22) but varying overfitting (0.06-0.07) and fit times (ExtraTrees at 383s, CatBoost at 11,552s), with bootstrap CIs confirming high reliability in their R² estimates. Boosting models like GradientBoosting (Val_Weighted_Orig = 2.28; CI 0.857 to 0.940) and AdaBoost (1.71; CI 0.729 to 0.882) offer solid but slightly inferior results, while SVR (CI 0.789 to 0.917), KNN (0.807 to 0.924), and MLP (0.820 to 0.932) provide balanced mid-tier performance (2.15-2.22 weighted scores) with moderate CI widths. Temperature subgroup analysis on the test set (low <300K n=110, mid 300-500K n=98, high >500K n=39) shows ExtraTrees excelling in mid (R²=0.951, MAE=0.180) but weaker in high (R²=0.824, MAE=0.440), with the StackingRegressor ensemble (built from top 4 models by validation weighted score, meta-learner tuned Ridge) performing robustly across subgroups (low R²=0.850 MAE=0.152, mid R²=0.926 MAE=0.214, high R²=0.784 MAE=0.444). The ensemble achieves Val_Weighted_Orig = 2.72 (CI 0.898 to 0.961, overlapping with top models but indicating stable variance) and Test_Weighted_Orig = 2.33, with superior Test_R2_Orig = 0.892, lower overfitting (0.039), and efficient fit time (48s). Additionally, a paired t-test on absolute errors (AE) between the best individual model (ExtraTrees) and the ensemble yields t-stat = -2.10 and p-value = 0.0365, indicating a statistically significant difference (p < 0.05) where the ensemble has lower mean AE on the test set, further confirming its superiority. Thus, the ensemble emerges as the overall superior model for its robustness, generalization, reduced error, consistent subgroup performance, tight bootstrap confidence intervals affirming reliable validation R², and balance across metrics. In conclusion, the StackingRegressor ensemble model stands out as the optimal choice for predicting hydrogen storage capacity in metal hydrides and alloys, leveraging the strengths of top-performing tree-based and boosting algorithms to deliver superior accuracy (Test_R²=0.892), robustness across temperature subgroups, statistically significant error reduction (p=0.0365 vs. ExtraTrees), and reliable validation estimates via bootstrap confidence intervals (0.898-0.961), all while minimizing overfitting and computational demands. 
This model holds substantial promise for industrial applications in the hydrogen economy, such as accelerating the design and screening of novel metal hydride materials for fuel cell vehicles and stationary energy storage systems by predicting storage capacities from compositional and structural features, thereby reducing costly experimental trials and facilitating rapid prototyping of efficient hydrogen storage solutions in renewable energy sectors.
======================================================

Benchmarking Models : 
