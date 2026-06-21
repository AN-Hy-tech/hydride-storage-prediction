# Machine_Model — Hydride Storage Capacity ML Pipeline

Predicts hydrogen storage capacity (H₂ wt%) of hydride materials from chemical composition and operating temperature using an ensemble of tree-based regressors.

## Directory Layout

```
Machine_Model/
├── data/
│   ├── raw/                    # Source datasets (tracked in git)
│   └── database/               # Merged dataset (combined_dataset.csv)
├── notebooks/                  # Step-by-step analysis notebooks
├── src/                        # Reusable pipeline scripts
│   ├── merge_datasets.py       # Merge raw sources into combined dataset
│   ├── split_data.py           # Stratified train/val/test split
│   ├── extract_features_cbfv.py
│   ├── log_transform_target.py
│   ├── Feature_selection.py    # VIF, SHAP, Boruta selection
│   ├── Boruta_FeatEng.py
│   ├── CleanLab.py             # Label-quality screening
│   ├── Catboostmodel.py        # CatBoost training + Optuna tuning
│   ├── benchmark_model_selection.py  # Full benchmark across 12 models
│   └── Ashghal/                # Advanced analysis & stacking scripts
├── reports/                    # Output figures, CSVs, and markdown summaries
├── tests/                      # Pytest test scripts
├── requirements.txt
└── .gitignore
```

## Pipeline Steps

### 1. Data Preparation
```bash
python src/merge_datasets.py       # Merge HyStor + ML-HYDPARK → combined_dataset.csv
python src/split_data.py           # Stratified 70/15/15 train/val/test split
```

### 2. Feature Extraction
```bash
python src/extract_features_cbfv.py          # CBFV elemental descriptors
# matminer & JARVIS features: see notebooks/data_preprocessed_matminer.ipynb
```

### 3. Feature Selection
```bash
python src/Feature_selection.py    # VIF collinearity + mutual info + SHAP
python src/Boruta_FeatEng.py       # Boruta all-relevant selection
```

### 4. Benchmarking
```bash
python src/benchmark_model_selection.py      # Cross-validate 12 regressors
```

### 5. Optimization & Stacking
```bash
python src/Ashghal/Opt_and_Stack.py          # Optuna tuning + stacking ensemble
```

### 6. Analysis
```bash
python src/Ashghal/analyze_optimized_catboost.py
python src/Ashghal/analyze_stacking_model.py
```

## Models Evaluated

| Model | Type |
|-------|------|
| CatBoost | Gradient boosting |
| XGBoost | Gradient boosting |
| LightGBM | Gradient boosting |
| GradientBoosting | Gradient boosting |
| ExtraTrees | Bagging ensemble |
| RandomForest | Bagging ensemble |
| SVR | Kernel method |
| MLP | Neural network |
| AdaBoost | Boosting |
| Ridge / Lasso / ElasticNet | Linear |
| BayesianRidge | Bayesian linear |
| KNN | Instance-based |

## Setup

```bash
pip install -r requirements.txt
```

Packages requiring conda (recommended):
```bash
conda install -c conda-forge matminer pymatgen rdkit
```

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `Raw_Data_Analysis.ipynb` | EDA on raw dataset |
| `data_preprocessed_matminer.ipynb` | Matminer featurization |
| `Preprocessed_Data_Analysis.ipynb` | Post-featurization EDA |
| `identify_extream_outliers.ipynb` | Outlier detection & capping |
| `optimize_catboost_model.ipynb` | Optuna CatBoost tuning |
