# Graph Report - Hydride_Machine_learning_project  (2026-08-29)

## Corpus Check
- Large corpus: 245 files · ~642,539 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 195 nodes · 341 edges · 12 communities (11 shown, 1 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 1% AMBIGUOUS · INFERRED: 54 edges (avg confidence: 0.89)
- Token cost: 165,875 input · 0 output

## Community Hubs (Navigation)
- Inverse Design Screening Architectures
- Model Benchmark and Statistics
- Data Pipeline and CBFV Featurisation
- Generative Design and OOD Validation
- Raw Data Diagnostics and Physics Screens
- Optimised CatBoost and Dependency Stack
- Selected Features and SHAP Interpretation
- Boruta VIF Feature Selection
- CatBoost Training and Tuning
- CleanLab Outlier Screening
- Uncertainty Quantification Guard Rails
- Database Test Suite

## God Nodes (most connected - your core abstractions)
1. `Machine_Model Pipeline Guide` - 13 edges
2. `HydMS Project` - 12 edges
3. `Inverse Design Methods Memo` - 10 edges
4. `HydMS Project Report` - 9 edges
5. `22 Selected Features` - 9 edges
6. `Constrained Multi-Objective EA (Architecture B)` - 9 edges
7. `Machine_Model Dependency Stack` - 8 edges
8. `Generative-Model Data Scale Argument` - 8 edges
9. `13-Model Regression Benchmark` - 6 edges
10. `Baseline Stacking Ensemble` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Optuna Hyperparameter Optimisation` --references--> `optimize_catboost()`  [INFERRED]
  REPORT.md → Machine_Model/src/Catboostmodel.py
- `Bootstrap Confidence Intervals (2000 resamples)` --semantically_similar_to--> `Uncertainty Quantification Guard Rail`  [INFERRED] [semantically similar]
  REPORT.md → research/inverse-design-methods.md
- `CleanLab Label-Quality Screening` --references--> `manage_outliers()`  [INFERRED]
  REPORT.md → Machine_Model/src/CleanLab.py
- `Five-Stage Feature Selection Pipeline` --references--> `iterative_vif()`  [INFERRED]
  REPORT.md → Machine_Model/src/Feature_selection.py
- `Temperature Subgroup Performance` --references--> `get_temp_group()`  [INFERRED]
  REPORT.md → Machine_Model/src/benchmark_model_selection.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **HydMS Ordered Pipeline Stages** — machine_model_src_merge_datasets, machine_model_src_log_transform_target, machine_model_src_extract_features_cbfv, machine_model_src_cleanlab, machine_model_src_boruta_feateng, machine_model_src_feature_selection, machine_model_src_split_data, machine_model_src_benchmark_model_selection, machine_model_src_catboostmodel [EXTRACTED 1.00]
- **Inverse-Design Guard Rail Stack** — research_inverse_design_methods_uncertainty_quantification, research_inverse_design_methods_applicability_domain, research_inverse_design_methods_physics_filters, research_inverse_design_methods_novelty_check, research_inverse_design_methods_lower_confidence_bound_ranking, research_inverse_design_methods_enumerate_and_screen [EXTRACTED 1.00]
- **Physical Interpretation Descriptor Set** — report_avg_valence_d, report_avg_is_alkaline, report_avg_polzbl_divi_atom_mass, report_dev_zunger_radii_sum, report_temperature_k [EXTRACTED 1.00]

## Communities (12 total, 1 thin omitted)

### Community 0 - "Inverse Design Screening Architectures"
Cohesion: 0.09
Nodes (28): Capacity Prediction from Formula and Temperature, HydMS Project, HyStor Experimental Database, ML-HYDPARK v0.0.5 Dataset, Kauwe et al. - CBFV, Future Directions, HydMS Project Report, Wilson et al. 2024 - HyStor Database (+20 more)

### Community 1 - "Model Benchmark and Statistics"
Cohesion: 0.10
Nodes (24): argparse, json, Models Evaluated Table, bootstrap_ci(), optuna_stacking_objective(), weighted_score(), ExtraTrees Best Single Model, Stacking Ensemble (best overall) (+16 more)

### Community 2 - "Data Pipeline and CBFV Featurisation"
Cohesion: 0.20
Nodes (13): cbfv.composition, Split Data Summary, matplotlib.pyplot, numpy, os, pandas, CBFV Featurisation (Magpie + JARVIS), Stratified Train/Val/Test Split (+5 more)

### Community 3 - "Generative Design and OOD Validation"
Cohesion: 0.11
Nodes (21): Unique-Formulae Split Basis (1149 of 1279), get_temp_group(), Model Limitations, Temperature Subgroup Performance, Applicability Domain and Novelty Control, Baird et al. 2022 - DiSCoVeR, Beltrame et al. 2025 - dataset size and augmentation in hydrides, Conditional Generative Design (Architecture C) (+13 more)

### Community 4 - "Raw Data Diagnostics and Physics Screens"
Cohesion: 0.12
Nodes (16): Analysis Notebook Suite, SHAP Interpretation Limitations, Non-Standard Formula Inventory, Raw Data Summary (1279 x 6), Shapiro-Wilk Normality Test on H2 wt%, Hydrogen Storage Capacity (H2 wt%), log1p Target Transformation, Matminer Miedema and WenAlloys Features (+8 more)

### Community 5 - "Optimised CatBoost and Dependency Stack"
Cohesion: 0.15
Nodes (16): Machine_Model Pipeline Guide, boruta (dependency), CBFV (dependency), cleanlab (dependency), Machine_Model Dependency Stack, matminer (dependency), Optuna (dependency), shap (dependency) (+8 more)

### Community 6 - "Selected Features and SHAP Interpretation"
Cohesion: 0.15
Nodes (15): Feature Category Correlation Analysis, Expanded Material Science Linkage Summary, Mutual Information vs Pearson Analysis, Temperature Subgroup Performance Table, 22 Selected Features, avg_is_alkaline, avg_polzbl_divi_atom_mass, avg_valence_d (+7 more)

### Community 7 - "Boruta VIF Feature Selection"
Cohesion: 0.21
Nodes (11): boruta, iterative_vif(), iterative_vif(), random, re, 282 to 22 Feature Selection Funnel, Kursa & Rudnicki 2010 - Boruta, Five-Stage Feature Selection Pipeline (+3 more)

### Community 8 - "CatBoost Training and Tuning"
Cohesion: 0.19
Nodes (11): catboost, joblib, evaluate_model(), optuna_objective(), evaluate_model(), optimize_catboost(), objective(), optuna (+3 more)

### Community 9 - "CleanLab Outlier Screening"
Cohesion: 0.20
Nodes (7): cleanlab.regression.learn, manage_outliers(), CleanLab Outlier Removal, CleanLab Label-Quality Screening, Northcutt et al. 2021 - Confident Learning, sklearn.ensemble, sklearn.preprocessing

### Community 10 - "Uncertainty Quantification Guard Rails"
Cohesion: 0.29
Nodes (7): CatBoost (dependency), Angelopoulos & Bates 2023 - Conformal Prediction, CatBoost Native Uncertainty, Conformal Prediction Intervals, Lower-Confidence-Bound Ranking, MAPIE, Uncertainty Quantification Guard Rail

## Ambiguous Edges - Review These
- `Optuna-optimised CatBoost` → `Opt_and_Stack.py`  [AMBIGUOUS]
  README.md · relation: references
- `13-Model Regression Benchmark` → `Models Evaluated Table`  [AMBIGUOUS]
  Machine_Model/README.md · relation: references

## Knowledge Gaps
- **42 isolated node(s):** `ExtraTrees Best Single Model`, `CBFV Featurisation (Magpie + JARVIS)`, `CleanLab Outlier Removal`, `Raw Outlier Analysis`, `Non-Standard Composition Formats` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Optuna-optimised CatBoost` and `Opt_and_Stack.py`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `13-Model Regression Benchmark` and `Models Evaluated Table`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `HydMS Project` connect `Inverse Design Screening Architectures` to `Model Benchmark and Statistics`, `Data Pipeline and CBFV Featurisation`, `Boruta VIF Feature Selection`, `CatBoost Training and Tuning`, `CleanLab Outlier Screening`?**
  _High betweenness centrality (0.158) - this node is a cross-community bridge._
- **Why does `Inverse Design Methods Memo` connect `Inverse Design Screening Architectures` to `Data Pipeline and CBFV Featurisation`, `Generative Design and OOD Validation`?**
  _High betweenness centrality (0.155) - this node is a cross-community bridge._
- **Why does `Machine_Model Pipeline Guide` connect `Optimised CatBoost and Dependency Stack` to `Model Benchmark and Statistics`, `Data Pipeline and CBFV Featurisation`, `Boruta VIF Feature Selection`, `CatBoost Training and Tuning`, `CleanLab Outlier Screening`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **What connects `ExtraTrees Best Single Model`, `CBFV Featurisation (Magpie + JARVIS)`, `CleanLab Outlier Removal` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Inverse Design Screening Architectures` be split into smaller, more focused modules?**
  _Cohesion score 0.08994708994708994 - nodes in this community are weakly interconnected._