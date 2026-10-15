# HydMS: Hydrogen Storage Capacity Prediction — Project Report

**Retracted — under audit.**

This report originally published a full methodology and results write-up: validation R² 0.939,
test R² 0.892, a 13-model benchmark, Optuna-tuned results, and SHAP-based interpretability
analysis. Those numbers are dropped from this file.

An in-progress review (PR #6, "Freeze the inverse-design programme; open Phase H hardening")
audited the forward pipeline behind this report and found:

- The committed `Machine_Model/reports/benchmarked_model/stacking_results.csv` records
  substantially lower scores for the same run than this report claimed.
- A label-leak bug in `Machine_Model/src/CleanLab.py`: validation and test ground-truth labels
  were overwritten with the model's own predictions.
- The pipeline cannot currently be run end to end as committed — a featurisation input with no
  producer in history, a reader of a deleted writer's directory, and a positional concat that
  silently misaligns rows.

In short: the published pipeline is not the committed pipeline, so these results are not
reproducible as stated and should not be cited as current performance.

The original text is preserved in git history (`git log --follow -- REPORT.md`) for anyone who
wants to see exactly what was claimed. This file will be replaced with a corrected report once the
Phase H hardening work (`kanban-hardening/`, tracked from PR #6) verifies real numbers against the
committed pipeline.
