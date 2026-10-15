# HydMS — Hydrogen Storage Capacity Prediction via Machine Learning

**[Read the full project report →](REPORT.md)**

> **Master's Thesis Project** · Faculty of Metallurgical and Materials Engineering · Shiraz University
Researcher: Amirhossein Nasiri
---

## What is this?

Metal hydrides can store hydrogen inside their crystal lattice — a promising path toward solid-state hydrogen energy storage. But measuring storage capacity experimentally is slow and expensive. This project builds a machine learning pipeline that predicts the **maximum H₂ storage capacity (wt%)** of any hydride alloy from its **chemical formula and operating temperature alone**.

The pipeline covers everything from raw data ingestion through multi-library feature extraction, outlier detection, feature selection, model benchmarking (13 algorithms), Bayesian hyperparameter optimization, and a stacking ensemble.

### Key results

> **Under audit — not yet reproduced.** The numbers below are what `Machine_Model/` originally
> published. An in-progress review (PR #6, "Freeze the inverse-design programme; open Phase H
> hardening") found the committed `stacking_results.csv` records **CV 0.344 / Val 0.377 / Test
> 0.376** for the same run — far below the table here — plus a label-leak bug and a pipeline that
> does not currently run end to end as committed. Read these as the historical, as-published
> figures, not as current, verified performance.

| Model | Val R² | Test R² | Test MAE |
|-------|--------|---------|----------|
| Stacking Ensemble *(best overall)* | **0.939** | 0.892 | 0.229 wt% |
| ExtraTrees *(best single model)* | 0.933 | **0.916** | 0.204 wt% |
| CatBoost Optuna-optimized | **0.969** | 0.951 | — |

---

## Project Structure

```
Hydride_Machine_learning_project/
└── Machine_Model/              # ML pipeline (training, evaluation, analysis)
    ├── src/                    # Source scripts — run these in order
    │   ├── merge_datasets.py           # 1. Merge HyStor + ML-HYDPARK datasets
    │   ├── log_transform_target.py     # 2. Log-transform the H₂ wt% target
    │   ├── extract_features_cbfv.py    # 3. CBFV featurisation (Magpie + JARVIS)
    │   ├── CleanLab.py                 # 4. CleanLab outlier removal
    │   ├── Boruta_FeatEng.py           # 5a. Boruta + SHAP feature engineering
    │   ├── Feature_selection.py        # 5b. VIF + correlation feature selection
    │   ├── split_data.py               # 6. Stratified train/val/test split
    │   ├── benchmark_model_selection.py # 7. 13-model benchmark + Optuna tuning
    │   └── Catboostmodel.py            # 8. Dedicated CatBoost optimisation
    ├── notebooks/              # Exploratory analysis & visualisation
    ├── data/raw/               # Raw datasets (HyStor, ML-HYDPARK)
    └── reports/                # Generated CSVs and TXT summaries
```

---

## Quickstart

### Requirements

- Python 3.9+
- [Conda](https://docs.conda.io/) recommended for scientific packages

### Step 1 — Install dependencies

```bash
cd Machine_Model
pip install -r requirements.txt
```

Some packages are best installed via conda:

```bash
conda install -c conda-forge matminer pymatgen rdkit
```

### Step 2 — Run the ML pipeline

Execute the scripts in `Machine_Model/src/` in order:

```bash
cd Machine_Model

# 1. Merge raw datasets
python src/merge_datasets.py

# 2. Log-transform the target variable
python src/log_transform_target.py

# 3. Extract compositional features (CBFV: Magpie + JARVIS)
python src/extract_features_cbfv.py

# 4. Remove label noise with CleanLab
python src/CleanLab.py

# 5. Feature engineering and selection (run both)
python src/Boruta_FeatEng.py
python src/Feature_selection.py

# 6. Stratified train / validation / test split
python src/split_data.py

# 7. Benchmark 13 models + Optuna hyperparameter tuning
python src/benchmark_model_selection.py

# 8. Optimise CatBoost specifically
python src/Catboostmodel.py
```

Alternatively, explore the pipeline interactively through the notebooks in `Machine_Model/notebooks/` (run them in alphabetical order).

---

## Methodology at a Glance

| Stage | Detail |
|-------|--------|
| **Datasets** | HyStor + ML-HYDPARK — 1,279 samples after merging & cleaning |
| **Featurisation** | CBFV (Magpie + JARVIS) + Matminer (Miedema + WenAlloys) → 282 features |
| **Outlier removal** | CleanLab `CleanLearning` wrapping `HistGradientBoostingRegressor` |
| **Feature selection** | VarianceThreshold → correlation filter → RandomForest → Boruta → SHAP → VIF → **22 features** |
| **Data split** | Stratified 70 / 10.6 / 19.3 % (train / val / test) — 896 / 136 / 247 samples |
| **Benchmarking** | 13 regressors + Stacking Ensemble; scored on log-scale and original wt% |
| **Optimisation** | Optuna (100 trials, TPE sampler) for 5 top models |
| **Ensemble** | StackingRegressor: ExtraTrees + CatBoost + GradientBoosting + RandomForest; Ridge meta-learner |
| **Interpretability** | SHAP TreeExplainer, Pearson & MI correlations, temperature subgroup analysis |

---

## Datasets

| File | Description |
|------|-------------|
| `Machine_Model/data/raw/hydride_data.csv` | Primary merged hydride dataset |
| `Machine_Model/data/raw/ML-HYDPARK_v0.0.5.csv` | ML-HYDPARK benchmark dataset |
| `Machine_Model/data/raw/HyStor_27_7_24 (1).xlsx` | HyStor experimental database |

---

## About

This project was developed as a **Master's thesis** in the **Department of Metallurgy and Materials Engineering** at **Shiraz University**. It demonstrates that physics-informed compositional descriptors, combined with modern ML methods, can predict hydrogen storage capacity with high accuracy — reducing the need for costly experimental screening.

For the complete methodology, results tables, statistical tests, and SHAP analysis, see **[REPORT.md](REPORT.md)**.

---

Copyright © 2026 Amirhossein Nasiri. Licensed under the [GNU General Public License v3.0 or later](LICENSE).
