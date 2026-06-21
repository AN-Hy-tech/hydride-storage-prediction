# import pandas as pd
# import numpy as np
# import os
# import time
# import json
# import warnings
# import joblib
# import matplotlib.pyplot as plt
# import seaborn as sns

# from scipy.stats import ttest_rel, shapiro
# from sklearn.linear_model import Ridge, Lasso, ElasticNet, BayesianRidge
# from sklearn.tree import DecisionTreeRegressor
# from sklearn.ensemble import (ExtraTreesRegressor, GradientBoostingRegressor,
#                               AdaBoostRegressor, RandomForestRegressor, StackingRegressor)
# from catboost import CatBoostRegressor
# # from lightgbm import LGBMRegressor
# from sklearn.svm import SVR
# from sklearn.neighbors import KNeighborsRegressor
# from sklearn.neural_network import MLPRegressor
# from sklearn.model_selection import StratifiedKFold, cross_validate, learning_curve
# from sklearn.preprocessing import RobustScaler
# from sklearn.pipeline import Pipeline
# from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, make_scorer
# from sklearn.inspection import PartialDependenceDisplay
# from sklearn.utils import resample

# # stats / post-hoc & diagnostics
# import statsmodels.api as sm
# import statsmodels.formula.api as smf
# from statsmodels.stats.anova import anova_lm
# from statsmodels.stats.multicomp import pairwise_tukeyhsd
# from statsmodels.stats.multitest import multipletests
# from statsmodels.stats.diagnostic import het_breuschpagan

# # SHAP
# import shap

# import argparse
# warnings.filterwarnings("ignore", category=UserWarning)

# # -----------------------------
# # Argument Parser and Paths
# # -----------------------------
# parser = argparse.ArgumentParser()
# parser.add_argument('--data_dir', default=r'D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data')
# parser.add_argument('--output_dir', default=r'D:\Hydride_Machine_learning_project\Machine_Model\reports\benchmarked_model')
# parser.add_argument('--figures_dir', default=r'D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\default_benchmark_analysis')
# parser.add_argument('--models_dir', default=r'D:\Hydride_Machine_learning_project\models\default_benchmark_models')
# parser.add_argument('--params_dir', default=r'D:\Hydride_Machine_learning_project\reports\benchmarked_model\default_params')
# parser.add_argument('--shap_sample', type=int, default=200, help='Max samples for SHAP to control runtime')
# args = parser.parse_args()

# os.makedirs(args.figures_dir, exist_ok=True)
# os.makedirs(args.models_dir, exist_ok=True)
# os.makedirs(args.params_dir, exist_ok=True)
# os.makedirs(args.output_dir, exist_ok=True)

# # -----------------------------
# # Data Loading
# # -----------------------------
# train_path = os.path.join(args.data_dir, 'selected_train.csv')
# val_path = os.path.join(args.data_dir, 'selected_val.csv')
# test_path = os.path.join(args.data_dir, 'selected_test.csv')

# df_train = pd.read_csv(train_path)
# df_val = pd.read_csv(val_path)
# df_test = pd.read_csv(test_path)

# print(f"Loaded selected train data with shape: {df_train.shape}")
# print(f"Loaded selected val data with shape: {df_val.shape}")
# print(f"Loaded selected test data with shape: {df_test.shape}")

# feature_cols = [col for col in df_train.columns if col not in ['target', 'formula']]
# X_train, y_train = df_train[feature_cols], df_train['target'].values
# X_val, y_val = df_val[feature_cols], df_val['target'].values
# X_test, y_test = df_test[feature_cols], df_test['target'].values

# # original scale
# y_train_original, y_val_original, y_test_original = np.expm1(y_train), np.expm1(y_val), np.expm1(y_test)

# has_temperature = 'temperature(K)' in df_train.columns
# if has_temperature:
#     temp_train, temp_val, temp_test = df_train['temperature(K)'], df_val['temperature(K)'], df_test['temperature(K)']
#     def get_temp_group(temp):
#         if temp < 300: return 'low'
#         elif temp <= 500: return 'mid'
#         else: return 'high'
#     temp_group_train = np.array([get_temp_group(t) for t in temp_train])
#     temp_group_val = np.array([get_temp_group(t) for t in temp_val])
#     temp_group_test = np.array([get_temp_group(t) for t in temp_test])

# binned_y = pd.qcut(y_train, q=10, labels=False, duplicates='drop')
# kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
# splits = list(kf.split(X_train, binned_y))

# # -----------------------------
# # Models
# # -----------------------------
# models = {
#     'Ridge': Ridge(random_state=42),
#     'Lasso': Lasso(random_state=42),
#     'ElasticNet': ElasticNet(random_state=42),
#     'BayesianRidge': BayesianRidge(),
#     'DecisionTree': DecisionTreeRegressor(random_state=42),
#     'RandomForest': RandomForestRegressor(random_state=42, n_jobs=-1),
#     'ExtraTrees': ExtraTreesRegressor(random_state=42, n_jobs=-1),
#     'GradientBoosting': GradientBoostingRegressor(random_state=42),
#     'AdaBoost': AdaBoostRegressor(random_state=42),
#     'CatBoost': CatBoostRegressor(random_state=42, verbose=0),
#     # 'LightGBM': LGBMRegressor(random_state=42, n_jobs=-1, verbosity=-1),
#     'SVR': SVR(kernel='rbf'),
#     'KNN': KNeighborsRegressor(n_jobs=-1),
#     'MLP': MLPRegressor(random_state=42, max_iter=5000, early_stopping=True)
# }

# # For ANOVA group-level comparisons
# model_groups = {
#     'Ridge': 'Linear', 'Lasso': 'Linear', 'ElasticNet': 'Linear', 'BayesianRidge': 'Linear',
#     'DecisionTree': 'Tree', 'RandomForest': 'Tree', 'ExtraTrees': 'Tree',
#     'GradientBoosting': 'Boosting', 'AdaBoost': 'Boosting',
#     'CatBoost': 'Boosting',
#     'SVR': 'Neighbor',
#     'KNN': 'Kernel',
#     'MLP': 'Neural'
# }

# # -----------------------------
# # Metrics
# # -----------------------------
# def rmse(y_true, y_pred):
#     return np.sqrt(mean_squared_error(y_true, y_pred))

# def weighted_score(y_true, y_pred):
#     r2 = r2_score(y_true, y_pred)
#     mae = mean_absolute_error(y_true, y_pred)
#     mae = mae if mae != 0 else 1e-6
#     return 0.6 * r2 + 0.4 / mae

# def evaluate_model(y_true, y_pred, scale='orig'):
#     if scale == 'orig':
#         y_true_eval, y_pred_eval = np.expm1(y_true), np.expm1(y_pred)
#     else:
#         y_true_eval, y_pred_eval = y_true, y_pred
#     mae = mean_absolute_error(y_true_eval, y_pred_eval)
#     mse = mean_squared_error(y_true_eval, y_pred_eval)
#     rmse_val = np.sqrt(mse)
#     r2 = r2_score(y_true_eval, y_pred_eval)
#     mae_adj = mae if mae != 0 else 1e-6
#     w_score = 0.6 * r2 + 0.4 / mae_adj
#     return mae, mse, rmse_val, r2, w_score

# def bootstrap_ci(y_true, y_pred, metric_func, n_boot=2000, ci=95):
#     np.random.seed(42)
#     boot_scores = [metric_func(*resample(y_true, y_pred)) for _ in range(n_boot)]
#     return np.percentile(boot_scores, (100 - ci) / 2), np.percentile(boot_scores, 100 - (100 - ci) / 2)

# # -----------------------------
# # Optuna 
# # -----------------------------
# import optuna
# from optuna.samplers import TPESampler
# from optuna.pruners import MedianPruner

# def optuna_objective(trial, model_name, X, y, cv_splits):
#     if model_name == 'ExtraTrees':
#         params = {
#             'n_estimators': trial.suggest_int('n_estimators', 500, 5000, step=50),
#             'max_depth': trial.suggest_int('max_depth', 5, 30),
#             'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
#             'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
#             'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
#             'bootstrap': trial.suggest_categorical('bootstrap', [True, False])
#         }
#         model = ExtraTreesRegressor(**params, random_state=42, n_jobs=-1)
#     elif model_name == 'MLP':
#         params = {
#             'hidden_layer_sizes': trial.suggest_categorical('hidden_layer_sizes',
#                                                             [(50,), (100,), (200,), (100,50), (300,200,100), (500,300,100)]),
#             'alpha': trial.suggest_float('alpha', 1e-5, 1e1, log=True),
#             'learning_rate_init': trial.suggest_float('learning_rate_init', 1e-6, 1e-2, log=True),
#             'activation': trial.suggest_categorical('activation', ['relu', 'tanh']),
#             'solver': trial.suggest_categorical('solver', ['adam', 'lbfgs']),
#             'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128, 256])
#         }
#         model = MLPRegressor(**params, random_state=42, max_iter=10000, early_stopping=True)
#     elif model_name == 'CatBoost':
#         params = {
#             'iterations': trial.suggest_int('iterations', 1000, 15000, step=250),
#             'learning_rate': trial.suggest_float('learning_rate', 0.0001, 0.1, log=True),
#             'depth': trial.suggest_int('depth', 4, 15),
#             'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 50, log=True),
#             'bagging_temperature': trial.suggest_float('bagging_temperature', 0, 5),
#             'random_strength': trial.suggest_float('random_strength', 0.5, 20),
#             'grow_policy': trial.suggest_categorical('grow_policy', ['SymmetricTree', 'Depthwise', 'Lossguide']),
#             'subsample': trial.suggest_float('subsample', 0.5, 1.0),
#             'loss_function': 'RMSE',
#             'border_count': trial.suggest_int('border_count', 32, 256)
            
#         }
#         model = CatBoostRegressor(**params, random_state=42, verbose=0, early_stopping_rounds=1000)
#     elif model_name == 'Ridge':
#         params = {'alpha': trial.suggest_float('alpha', 1e-4, 1e3, log=True)}
#         model = Ridge(**params, random_state=42)
#     elif model_name == 'SVR':
#         params = {
#             'C': trial.suggest_float('C', 0.1, 100, log=True),
#             'epsilon': trial.suggest_float('epsilon', 0.0001, 10.0, log=True),
#             'gamma': trial.suggest_categorical('gamma', ['scale', 'auto']),
#             'kernel': trial.suggest_categorical('kernel', ['rbf', 'poly', 'sigmoid'])
#         }
#         model = SVR(**params)
#     else:
#         raise ValueError(f"Model {model_name} not implemented.")

#     pipe = Pipeline([('scaler', RobustScaler()), ('reg', model)])
#     cv_results = cross_validate(pipe, X, y, cv=cv_splits, scoring='r2', n_jobs=-1)
#     return cv_results['test_score'].mean()

# # -----------------------------
# # Main Training Loop
# # -----------------------------
# scoring = {
#     'MAE': make_scorer(mean_absolute_error, greater_is_better=False),
#     'R2': 'r2',
#     'RMSE': make_scorer(rmse, greater_is_better=False),
#     'Weighted': make_scorer(weighted_score, greater_is_better=True)
# }

# results, feature_importances = [], {}
# all_val_preds, all_test_preds = {}, {}

# # store per-fold CV metrics for ANOVA/t-tests
# cv_fold_rows = []  # rows: {'Model','Fold','R2','RMSE','MAE','Weighted'}
# fold_indexer = list(range(1, 6))

# for name, base_model in models.items():
#     start_time = time.time()
#     if name in ['ExtraTrees', 'MLP', 'CatBoost', 'Ridge', 'SVR']:
#         print(f"Tuning {name} with Optuna...")
#         study = optuna.create_study(direction='maximize',
#                                     sampler=TPESampler(seed=42),
#                                     pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3))
#         study.optimize(lambda trial: optuna_objective(trial, name, X_train, y_train, splits),
#                        n_trials=100, timeout=7200, n_jobs=-1)
#         best_params = study.best_params
#         print(f"Best params for {name}: {best_params}")
#         base_model.set_params(**best_params)
#         with open(os.path.join(args.params_dir, f"{name}_tuned_params.json"), 'w') as f:
#             json.dump(best_params, f, indent=4)
#     else:
#         with open(os.path.join(args.params_dir, f"{name}_params.json"), 'w') as f:
#             json.dump(base_model.get_params(deep=True), f, indent=4)

#     pipe = Pipeline([('scaler', RobustScaler()), ('reg', base_model)])
#     cv_results = cross_validate(pipe, X_train, y_train, cv=splits, scoring=scoring, n_jobs=-1, return_estimator=False)

#     # capture per-fold metrics
#     r2_folds = cv_results['test_R2']
#     rmse_folds = -cv_results['test_RMSE']
#     mae_folds = -cv_results['test_MAE']
#     w_folds = cv_results['test_Weighted']
#     for i, (r2v, rmsev, maev, wv) in enumerate(zip(r2_folds, rmse_folds, mae_folds, w_folds)):
#         cv_fold_rows.append({'Model': name, 'Fold': i+1, 'R2': r2v, 'RMSE': rmsev, 'MAE': maev, 'Weighted': wv, 'Group': model_groups[name]})

#     cv_r2_mean = r2_folds.mean()
#     cv_r2_std = r2_folds.std()
#     cv_rmse_mean = rmse_folds.mean()
#     cv_mae_mean = mae_folds.mean()
#     cv_weighted_mean = w_folds.mean()

#     pipe.fit(X_train, y_train)

#     # save importances if available
#     if hasattr(pipe.named_steps['reg'], 'feature_importances_'):
#         importances = pipe.named_steps['reg'].feature_importances_
#         imp_df = pd.DataFrame({'Feature': feature_cols, 'Importance': importances}).sort_values('Importance', ascending=False)
#         imp_df.to_csv(os.path.join(args.figures_dir, f"{name}_feature_importance.csv"), index=False)
#         feature_importances[name] = imp_df

#     # preds
#     y_train_pred = pipe.predict(X_train)
#     y_val_pred = pipe.predict(X_val)
#     y_test_pred = pipe.predict(X_test)
#     all_val_preds[name] = y_val_pred
#     all_test_preds[name] = y_test_pred

#     # metrics (orig & log)
#     train_mae_orig, train_mse_orig, train_rmse_orig, train_r2_orig, train_w_orig = evaluate_model(y_train, y_train_pred, 'orig')
#     val_mae_orig, val_mse_orig, val_rmse_orig, val_r2_orig, val_w_orig = evaluate_model(y_val, y_val_pred, 'orig')
#     test_mae_orig, test_mse_orig, test_rmse_orig, test_r2_orig, test_w_orig = evaluate_model(y_test, y_test_pred, 'orig')

#     r2_low, r2_high = bootstrap_ci(y_val_original, np.expm1(y_val_pred), r2_score)
#     train_mae_log, train_mse_log, train_rmse_log, train_r2_log, _ = evaluate_model(y_train, y_train_pred, 'log')
#     val_mae_log, val_mse_log, val_rmse_log, val_r2_log, _ = evaluate_model(y_val, y_val_pred, 'log')
#     test_mae_log, test_mse_log, test_rmse_log, test_r2_log, _ = evaluate_model(y_test, y_test_pred, 'log')

#     overfitting = train_r2_orig - val_r2_orig
#     fit_time = time.time() - start_time

#     results.append({
#         'Model': name,
#         'CV_R2_Mean': cv_r2_mean,
#         'CV_R2_Std': cv_r2_std,
#         'CV_RMSE_Mean': cv_rmse_mean,
#         'CV_MAE_Mean': cv_mae_mean,
#         'CV_Weighted_Mean': cv_weighted_mean,
#         'Train_R2_Orig': train_r2_orig,
#         'Train_RMSE_Orig': train_rmse_orig,
#         'Train_MAE_Orig': train_mae_orig,
#         'Train_Weighted_Orig': train_w_orig,
#         'Val_R2_Orig': val_r2_orig,
#         'Val_RMSE_Orig': val_rmse_orig,
#         'Val_MAE_Orig': val_mae_orig,
#         'Val_Weighted_Orig': val_w_orig,
#         'Test_R2_Orig': test_r2_orig,
#         'Test_RMSE_Orig': test_rmse_orig,
#         'Test_MAE_Orig': test_mae_orig,
#         'Test_Weighted_Orig': test_w_orig,
#         'Train_R2_Log': train_r2_log,
#         'Val_R2_Log': val_r2_log,
#         'Test_R2_Log': test_r2_log,
#         'Overfitting': overfitting,
#         'Fit_Time (s)': fit_time,
#         'Val_R2_CI_Low': r2_low,
#         'Val_R2_CI_High': r2_high
#     })

#     joblib.dump(pipe, os.path.join(args.models_dir, f"{name}_model.pkl"), compress=3)

# # -----------------------------
# # Stacking Ensemble
# # -----------------------------
# results_df = pd.DataFrame(results)
# best_model_name = results_df.loc[results_df['Val_Weighted_Orig'].idxmax(), 'Model'] 
# top_models = results_df.nlargest(4, 'Val_Weighted_Orig')['Model'].tolist()
# estimators = [(m, joblib.load(os.path.join(args.models_dir, f"{m}_model.pkl"))) for m in top_models]

# # Lightweight Optuna tuning for Stacking's final_estimator (Ridge alpha)
# def optuna_objective_stacking(trial, estimators, X, y, cv_splits):
#     params = {'alpha': trial.suggest_float('alpha', 1e-2, 1e2, log=True)}
#     final_estimator = Ridge(**params, random_state=42)
#     model = StackingRegressor(estimators=estimators, final_estimator=final_estimator)
#     cv_results = cross_validate(model, X, y, cv=cv_splits, scoring='r2', n_jobs=-1)
#     return cv_results['test_score'].mean()

# print("Tuning Stacking Ensemble with Optuna (lightweight)...")
# study_ens = optuna.create_study(direction='maximize',
#                                 sampler=TPESampler(seed=42),
#                                 pruner=MedianPruner(n_startup_trials=3, n_warmup_steps=5, interval_steps=2))
# study_ens.optimize(lambda trial: optuna_objective_stacking(trial, estimators, X_train, y_train, splits),
#                    n_trials=100, timeout=3600, n_jobs=-1)
# best_params_ens = study_ens.best_params
# print(f"Best params for Stacking final_estimator: {best_params_ens}")
# with open(os.path.join(args.params_dir, "ensemble_tuned_params.json"), 'w') as f:
#     json.dump(best_params_ens, f, indent=4)

# final_estimator = Ridge(**best_params_ens, random_state=42)
# ensemble_model = StackingRegressor(estimators=estimators, final_estimator=final_estimator)

# start_time_ens = time.time()
# ensemble_model.fit(X_train, y_train)
# fit_time_ens = time.time() - start_time_ens
# ensemble_path = os.path.join(args.models_dir, 'ensemble_model.pkl')
# joblib.dump(ensemble_model, ensemble_path)

# y_train_pred_ens = ensemble_model.predict(X_train)
# y_val_pred_ens = ensemble_model.predict(X_val)
# y_test_pred_ens = ensemble_model.predict(X_test)
# all_val_preds['Ensemble'] = y_val_pred_ens
# all_test_preds['Ensemble'] = y_test_pred_ens

# train_mae_orig_ens, train_mse_orig_ens, train_rmse_orig_ens, train_r2_orig_ens, train_w_orig_ens = evaluate_model(y_train, y_train_pred_ens, 'orig')
# val_mae_orig_ens, val_mse_orig_ens, val_rmse_orig_ens, val_r2_orig_ens, val_w_orig_ens = evaluate_model(y_val, y_val_pred_ens, 'orig')
# test_mae_orig_ens, test_mse_orig_ens, test_rmse_orig_ens, test_r2_orig_ens, test_w_orig_ens = evaluate_model(y_test, y_test_pred_ens, 'orig')

# r2_low_ens, r2_high_ens = bootstrap_ci(y_val_original, np.expm1(y_val_pred_ens), r2_score)
# train_mae_log_ens, train_mse_log_ens, train_rmse_log_ens, train_r2_log_ens, _ = evaluate_model(y_train, y_train_pred_ens, 'log')
# val_mae_log_ens, val_mse_log_ens, val_rmse_log_ens, val_r2_log_ens, _ = evaluate_model(y_val, y_val_pred_ens, 'log')
# test_mae_log_ens, test_mse_log_ens, test_rmse_log_ens, test_r2_log_ens, _ = evaluate_model(y_test, y_test_pred_ens, 'log')

# overfitting_ens = train_r2_orig_ens - val_r2_orig_ens

# results.append({
#     'Model': 'Ensemble',
#     'CV_R2_Mean': np.nan,
#     'CV_R2_Std': np.nan,
#     'CV_RMSE_Mean': np.nan,
#     'CV_MAE_Mean': np.nan,
#     'CV_Weighted_Mean': np.nan,
#     'Train_R2_Orig': train_r2_orig_ens,
#     'Train_RMSE_Orig': train_rmse_orig_ens,
#     'Train_MAE_Orig': train_mae_orig_ens,
#     'Train_Weighted_Orig': train_w_orig_ens,
#     'Val_R2_Orig': val_r2_orig_ens,
#     'Val_RMSE_Orig': val_rmse_orig_ens,
#     'Val_MAE_Orig': val_mae_orig_ens,
#     'Val_Weighted_Orig': val_w_orig_ens,
#     'Test_R2_Orig': test_r2_orig_ens,
#     'Test_RMSE_Orig': test_rmse_orig_ens,
#     'Test_MAE_Orig': test_mae_orig_ens,
#     'Test_Weighted_Orig': test_w_orig_ens,
#     'Train_R2_Log': train_r2_log_ens,
#     'Val_R2_Log': val_r2_log_ens,
#     'Test_R2_Log': test_r2_log_ens,
#     'Overfitting': overfitting_ens,
#     'Fit_Time (s)': fit_time_ens,
#     'Val_R2_CI_Low': r2_low_ens,
#     'Val_R2_CI_High': r2_high_ens
# })
# results_df = pd.DataFrame(results)
# results_df.to_csv(os.path.join(args.output_dir, 'improved_benchmark_results.csv'), index=False)
# print("Benchmarking completed and results saved.")

# # save CV per-fold metrics
# cv_df = pd.DataFrame(cv_fold_rows)
# cv_df.to_csv(os.path.join(args.output_dir, 'cv_per_fold_metrics.csv'), index=False)

# # -----------------------------
# # 3) Statistical Analysis: Pairwise t-tests & ANOVA + Tukey
# # -----------------------------
# # Pairwise t-tests vs best (fold-wise R2)
# best_r2 = cv_df.loc[cv_df['Model'] == best_model_name, ['Fold','R2']].sort_values('Fold')['R2'].values
# ttest_rows = []
# for mdl in sorted(cv_df['Model'].unique()):
#     if mdl == best_model_name:
#         continue
#     r2_m = cv_df.loc[cv_df['Model'] == mdl, ['Fold','R2']].sort_values('Fold')['R2'].values
#     # Align length in case of any mismatch (shouldn't happen)
#     n = min(len(best_r2), len(r2_m))
#     stat, p = ttest_rel(best_r2[:n], r2_m[:n])
#     ttest_rows.append({'Model': mdl, 'Compared_To': best_model_name, 't_stat': stat, 'p_value_raw': p})
# ttest_df = pd.DataFrame(ttest_rows)
# if not ttest_df.empty:
#     ttest_df['p_value_adj'] = multipletests(ttest_df['p_value_raw'].values, method='fdr_bh')[1]
# ttest_df.to_csv(os.path.join(args.output_dir, 'pairwise_ttest_vs_best.csv'), index=False)

# # One-way ANOVA across model GROUPS on R2
# anova_input = cv_df[['Group','R2']].copy()
# anova_input['Group'] = anova_input['Group'].astype('category')
# ols_model = smf.ols('R2 ~ C(Group)', data=anova_input).fit()
# anova_table = anova_lm(ols_model, typ=2)
# anova_table.to_csv(os.path.join(args.output_dir, 'anova_group_r2.csv'))

# # Post-hoc Tukey HSD for groups
# tukey = pairwise_tukeyhsd(endog=anova_input['R2'], groups=anova_input['Group'], alpha=0.05)
# # Convert Tukey summary to DataFrame
# tukey_df = pd.DataFrame(data=tukey.summary().data[1:], columns=tukey.summary().data[0])
# tukey_df.to_csv(os.path.join(args.output_dir, 'anova_tukey_group_r2.csv'), index=False)

# # -----------------------------
# # 4) Visual Analysis & Diagnostics (Residuals, Heteroscedasticity),
# #    plus plots already included later
# # -----------------------------
# best_pipe = joblib.load(os.path.join(args.models_dir, f"{best_model_name}_model.pkl"))
# y_test_pred_best = best_pipe.predict(X_test)

# # Residuals
# resid_best = y_test_original - np.expm1(y_test_pred_best)
# resid_ens  = y_test_original - np.expm1(y_test_pred_ens)

# # Shapiro–Wilk normality
# shapiro_best = shapiro(resid_best)
# shapiro_ens  = shapiro(resid_ens)
# pd.DataFrame([
#     {'Model': best_model_name, 'W': shapiro_best.statistic, 'p_value': shapiro_best.pvalue},
#     {'Model': 'Ensemble', 'W': shapiro_ens.statistic,  'p_value': shapiro_ens.pvalue}
# ]).to_csv(os.path.join(args.output_dir, 'residuals_shapiro.csv'), index=False)

# # Breusch–Pagan heteroscedasticity test using a reduced exog (top features or predictions)
# top_exog_cols = []
# if best_model_name in feature_importances and not feature_importances[best_model_name].empty:
#     top_exog_cols = feature_importances[best_model_name]['Feature'].head(min(10, len(feature_cols))).tolist()
# else:
#     top_exog_cols = feature_cols[:min(10, len(feature_cols))]

# exog_best = sm.add_constant(pd.DataFrame(X_test[top_exog_cols]))
# bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(resid_best, exog_best)
# pd.DataFrame([{
#     'Model': best_model_name, 'LM_stat': bp_lm, 'LM_pvalue': bp_lm_p, 'F_stat': bp_f, 'F_pvalue': bp_f_p,
#     'Exog_Used': ';'.join(top_exog_cols)
# }]).to_csv(os.path.join(args.output_dir, 'breusch_pagan_best.csv'), index=False)

# # Residual plots
# plt.figure(figsize=(7,5))
# sns.histplot(resid_best, kde=True)
# plt.title(f'Residuals Distribution ({best_model_name})')
# plt.xlabel('Residual (Actual - Predicted)')
# plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'residuals_hist_best.png'))
# plt.close()

# plt.figure(figsize=(7,5))
# sns.residplot(x=np.expm1(y_test_pred_best), y=resid_best, lowess=True)
# plt.xlabel('Predicted (wt%)')
# plt.ylabel('Residual')
# plt.title(f'Residuals vs Predicted ({best_model_name})')
# plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'residuals_vs_pred_best.png'))
# plt.close()


# # -----------------------------
# # 6) Correlation analysis with target (materials-science linkage)
# # -----------------------------
# train_orig = df_train.copy()
# train_orig['target_orig'] = y_train_original

# # Pearson correlation (basic)
# corrs = train_orig[feature_cols + ['target_orig']].corr()['target_orig'].drop('target_orig').sort_values(ascending=False)
# corrs_df = corrs.reset_index().rename(columns={'index': 'Feature', 'target_orig': 'PearsonR'})
# corrs_df.to_csv(os.path.join(args.output_dir, 'feature_target_pearson_corr.csv'), index=False)

# plt.figure(figsize=(10,8))
# sns.heatmap(train_orig[feature_cols + ['target_orig']].corr(), cmap='coolwarm', center=0)
# plt.title('Feature-Target Correlation Heatmap (Train, original scale)')
# plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'feature_target_corr_heatmap.png'))
# plt.close()

# # -----------------------------
# # Expanded material science linkage
# # -----------------------------

# # Expanded material science linkage

# # Exclude 'temperature(K)' as it's experimental, not material property
# material_feature_cols = [col for col in feature_cols if col != 'temperature(K)']

# # Hardcoded categories based on material science linkages
# categories = {
#     'compositional': ['avg_is_alkaline', 'range_Atomic_Weight', 'range_Mendeleev_Number'],
#     'valence_electron': ['avg_valence_d', 'avg_Number_of_unfilled_s_valence_electrons', 'dev_gilmor_number_of_valence_electron'],
#     'structural_geometric': ['dev_Covalent_Radius', 'dev_Zunger_radii_sum', 'dev_voro_coord_divi_mol_vol', 'dev_atom_mass_mult_therm_cond', 'dev_bp_divi_atom_mass'],
#     'electronegativity_ionization': ['dev_Pauling_Electronegativity', 'dev_Gordy_electonegativity', 'range_Mulliken_EN', 'range_first_ion_en_mult_X'],
#     'thermal_properties': ['dev_specific_heat_(J/g_K)_', 'dev_heat_of_vaporization_(kJ/mol)_', 'range_specific_heat_(J/g_K)_', 'range_heat_of_vaporization_(kJ/mol)_'],
#     'density': ['range_Density_(g/mL)'],
#     'electronic': ['avg_polzbl_divi_atom_mass'],
#     'experimental': ['temperature(K)'] if has_temperature else [],
#     'other': []  # Any unassigned features would go here, but all are assigned
# }

# # Prepare original scale target for correlations
# train_orig = df_train.copy()
# train_orig['target_orig'] = y_train_original  # Assuming y_train_original is expm1(y_train)

# cat_corr_rows = []
# for cat, feats in categories.items():
#     if feats:
#         cat_mean_corr = train_orig[feats + ['target_orig']].corr()['target_orig'].drop('target_orig').mean()
#         cat_std_corr = train_orig[feats + ['target_orig']].corr()['target_orig'].drop('target_orig').std()
#         for feat in feats:
#             pearson_r = train_orig[feat].corr(train_orig['target_orig'])
#             cat_corr_rows.append({
#                 'Category': cat,
#                 'Feature': feat,
#                 'PearsonR': pearson_r,
#                 'Category_Mean_Corr': cat_mean_corr,
#                 'Category_Std_Corr': cat_std_corr
#             })
# cat_corr_df = pd.DataFrame(cat_corr_rows).sort_values('PearsonR', ascending=False)
# cat_corr_df.to_csv(os.path.join(args.output_dir, 'category_wise_feature_corr_expanded.csv'), index=False)

# # Visualize category-level average correlations
# cat_summary = cat_corr_df.groupby('Category')['PearsonR'].agg(['mean', 'std', 'count']).reset_index()
# plt.figure(figsize=(10, 6))
# sns.barplot(x='mean', y='Category', data=cat_summary, errorbar=None)
# plt.errorbar(x=cat_summary['mean'], y=cat_summary['Category'], xerr=cat_summary['std'], fmt='none', c='black', capsize=5)
# plt.xlabel('Average Pearson Correlation with Target')
# plt.title('Category-Level Correlation with Original Target')
# plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'category_corr_barplot.png'))
# plt.close()

# # Subgroup performance by temperature groups if available
# if has_temperature:
#     subgroup_rows = []
#     for mdl in [best_model_name, 'Ensemble']:
#         y_pred_sub = all_test_preds[mdl]
#         for subgroup in ['low', 'mid', 'high']:
#             idx = np.where(temp_group_test == subgroup)[0]
#             if len(idx) > 0:
#                 mae = mean_absolute_error(y_test_original[idx], np.expm1(y_pred_sub[idx]))
#                 rmse = np.sqrt(mean_squared_error(y_test_original[idx], np.expm1(y_pred_sub[idx])))
#                 r2 = r2_score(y_test_original[idx], np.expm1(y_pred_sub[idx]))
#                 count = len(idx)
#                 subgroup_rows.append({
#                     'Model': mdl, 
#                     'Temp_Subgroup': subgroup, 
#                     'Count': count,
#                     'MAE': mae, 
#                     'RMSE': rmse,
#                     'R2': r2
#                 })
#     subgroup_df = pd.DataFrame(subgroup_rows)
#     subgroup_df.to_csv(os.path.join(args.output_dir, 'temperature_subgroup_performance_expanded.csv'), index=False)
    
#     # Plot subgroup R2
#     plt.figure(figsize=(8, 5))
#     sns.barplot(x='Temp_Subgroup', y='R2', hue='Model', data=subgroup_df)
#     plt.title('R² Performance by Temperature Subgroup')
#     plt.tight_layout()
#     plt.savefig(os.path.join(args.figures_dir, 'temp_subgroup_r2_bar.png'))
#     plt.close()

# # High-correlation feature analysis (>0.3 or <-0.3 abs)
# corrs_df = pd.read_csv(os.path.join(args.output_dir, 'feature_target_pearson_corr.csv'))  # From previous section
# high_corr_feats = corrs_df[corrs_df['PearsonR'].abs() > 0.3]['Feature'].tolist()
# if len(high_corr_feats) > 1:
#     plot_df = train_orig[high_corr_feats + ['target_orig']].copy()
#     if has_temperature:
#         plot_df['Temp_Group'] = temp_group_train
#         sns.pairplot(plot_df, hue='Temp_Group', diag_kind='kde')
#     else:
#         sns.pairplot(plot_df, diag_kind='kde')
#     plt.suptitle('Pairplot of High-Correlation Features with Target', y=1.02)
#     plt.savefig(os.path.join(args.figures_dir, 'pairplot_high_corr_features_expanded.png'))
#     plt.close()

# # Nonlinear correlation check using mutual information (for potential nonlinear relationships)
# from sklearn.feature_selection import mutual_info_regression
# mi_scores = mutual_info_regression(train_orig[feature_cols], train_orig['target_orig'], random_state=42)
# mi_df = pd.DataFrame({'Feature': feature_cols, 'Mutual_Info': mi_scores}).sort_values('Mutual_Info', ascending=False)
# mi_df.to_csv(os.path.join(args.output_dir, 'feature_target_mutual_info.csv'), index=False)

# # Compare Pearson vs MI to detect nonlinear links
# corr_mi = corrs_df.merge(mi_df, on='Feature')
# corr_mi['Diff'] = corr_mi['Mutual_Info'] - corr_mi['PearsonR'].abs()  # High diff suggests nonlinearity
# corr_mi = corr_mi.sort_values('Diff', ascending=False)
# corr_mi.to_csv(os.path.join(args.output_dir, 'pearson_vs_mi_diff.csv'), index=False)

# # Text summary expansion
# summary_lines = []
# summary_lines.append("Expanded Material Science Linkage Summary")
# summary_lines.append("=========================================")
# summary_lines.append(f"Dataset: {len(df_train)} train samples, {len(feature_cols)} features")
# summary_lines.append(f"Target likely represents log-transformed hydrogen storage capacity (wt%) in metal hydrides/alloys")
# summary_lines.append("\nTop Linear Correlations (Pearson):")
# summary_lines.extend([f"- {row.Feature}: r={row.PearsonR:.3f}" for row in corrs_df.head(5).itertuples()])
# summary_lines.append("\nTop Mutual Information (potential nonlinear):")
# summary_lines.extend([f"- {row.Feature}: MI={row.Mutual_Info:.3f}" for row in mi_df.head(5).itertuples()])
# summary_lines.append("\nCategory Insights:")
# for _, row in cat_summary.iterrows():
#     summary_lines.append(f"- {row.Category}: avg r={row['mean']:.3f} ± {row['std']:.3f} (n={row['count']})")
# if has_temperature:
#     summary_lines.append("\nTemperature Subgroup Performance (Test Set):")
#     for _, sg in subgroup_df.iterrows():
#         summary_lines.append(f"- {sg.Model} in {sg.Temp_Subgroup}: R²={sg.R2:.3f}, MAE={sg.MAE:.3f} (n={sg.Count})")
# summary_lines.append("\nPotential Nonlinear Features (high MI - |Pearson| diff):")
# summary_lines.extend([f"- {row.Feature}: diff={row.Diff:.3f}" for row in corr_mi.head(3).itertuples()])
# summary_path = os.path.join(args.output_dir, 'expanded_material_science_linkage_summary.txt')
# with open(summary_path, 'w', encoding='utf-8') as f:
#     f.write("\n".join(summary_lines))

# print("Expanded material science linkage analysis complete.")

# # -----------------------------
# # 7) Learning curves (best & ensemble)
# # -----------------------------
# train_sizes, train_scores, val_scores = learning_curve(best_pipe, X_train, y_train, cv=5, n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 5))
# train_sizes_ens, train_scores_ens, val_scores_ens = learning_curve(ensemble_model, X_train, y_train, cv=5, n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 5))

# plt.figure(figsize=(8,6))
# plt.plot(train_sizes, train_scores.mean(axis=1), label='Train')
# plt.plot(train_sizes, val_scores.mean(axis=1), label='Validation')
# plt.xlabel('Training Examples'); plt.ylabel('R²'); plt.title(f'Learning Curve - {best_model_name}')
# plt.legend(); plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'learning_curve_best.png'))
# plt.close()

# plt.figure(figsize=(8,6))
# plt.plot(train_sizes_ens, train_scores_ens.mean(axis=1), label='Train')
# plt.plot(train_sizes_ens, val_scores_ens.mean(axis=1), label='Validation')
# plt.xlabel('Training Examples'); plt.ylabel('R²'); plt.title('Learning Curve - Ensemble')
# plt.legend(); plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'learning_curve_ensemble.png'))
# plt.close()

# # -----------------------------
# # 8) Partial Dependence (Best & Ensemble) for key features
# # -----------------------------
# if feature_importances:
#     key_features = list(feature_importances.get(best_model_name, pd.DataFrame(columns=['Feature']))) or feature_cols[:5]
#     if isinstance(key_features, list) and len(key_features)==0:
#         key_features = feature_cols[:5]
#     if isinstance(key_features, list):
#         key_features = list(feature_importances[best_model_name]['Feature'].head(min(5, len(feature_cols))).values) \
#             if best_model_name in feature_importances else feature_cols[:5]
# else:
#     key_features = feature_cols[:5]

# # Best model PDP
# for feat in key_features:
#     feat_idx = feature_cols.index(feat)
#     fig, ax = plt.subplots(figsize=(7,5))
#     PartialDependenceDisplay.from_estimator(best_pipe, X_test, features=[feat_idx], feature_names=feature_cols, ax=ax)
#     plt.tight_layout()
#     plt.savefig(os.path.join(args.figures_dir, f'pdp_best_{feat.replace("/", "-")}.png'))
#     plt.close()

# # Ensemble PDP
# for feat in key_features:
#     feat_idx = feature_cols.index(feat)
#     fig, ax = plt.subplots(figsize=(7,5))
#     PartialDependenceDisplay.from_estimator(ensemble_model, X_test, features=[feat_idx], feature_names=feature_cols, ax=ax)
#     plt.tight_layout()
#     plt.savefig(os.path.join(args.figures_dir, f'pdp_ensemble_{feat.replace("/", "-")}.png'))
#     plt.close()

# # -----------------------------
# # 4 & 9) SHAP explainability for best model
# # -----------------------------
# # sample to control runtime
# sample_n = min(args.shap_sample, len(X_test))
# rng = np.random.RandomState(42)
# sample_idx = rng.choice(np.arange(len(X_test)), size=sample_n, replace=False)
# X_shap = X_test.iloc[sample_idx].copy()

# reg = best_pipe.named_steps['reg']
# if isinstance(reg, (RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor, DecisionTreeRegressor)):
#     explainer = shap.TreeExplainer(reg)
# elif isinstance(reg, CatBoostRegressor):
#     explainer = shap.TreeExplainer(reg)
# else:
#     # fall back to KernelExplainer on a small background
#     bg = X_train.sample(min(100, len(X_train)), random_state=42)
#     explainer = shap.KernelExplainer(lambda x: best_pipe.predict(pd.DataFrame(x, columns=feature_cols)), bg.to_numpy())

# shap_values = explainer.shap_values(X_shap)

# # SHAP summary plot
# plt.figure()
# shap.summary_plot(shap_values, X_shap, show=False)
# plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'shap_summary_best.png'), bbox_inches='tight')
# plt.close()

# # SHAP top features table
# mean_abs = np.abs(shap_values).mean(axis=0)
# shap_imp = pd.DataFrame({'Feature': X_shap.columns, 'MeanAbsSHAP': mean_abs}).sort_values('MeanAbsSHAP', ascending=False)
# shap_imp.to_csv(os.path.join(args.output_dir, 'shap_importance_best.csv'), index=False)

# # SHAP dependence plots for top 5
# for feat in shap_imp['Feature'].head(5):
#     plt.figure()
#     shap.dependence_plot(feat, shap_values, X_shap, show=False)
#     plt.tight_layout()
#     plt.savefig(os.path.join(args.figures_dir, f'shap_dependence_{feat.replace("/", "-")}.png'), bbox_inches='tight')
#     plt.close()

# # -----------------------------
# # 7) Ensemble vs Best: paired t-test on per-sample absolute errors (test set)
# # -----------------------------
# abs_err_best = np.abs(y_test_original - np.expm1(y_test_pred_best))
# abs_err_ens  = np.abs(y_test_original - np.expm1(y_test_pred_ens))
# t_stat_ae, p_val_ae = ttest_rel(abs_err_best, abs_err_ens)
# pd.DataFrame([{'Test': 'Paired t-test |AE| (Best vs Ensemble)',
#                't_stat': t_stat_ae, 'p_value': p_val_ae,
#                'BestModel': best_model_name}]).to_csv(os.path.join(args.output_dir, 'ttest_best_vs_ensemble_abs_error.csv'), index=False)

# # -----------------------------
# # 2 & 4) Visual Summaries already in base script: Add Combined Metric Heatmap & Pred vs Actual
# # (Reproduced succinctly here to ensure files exist even if base script section is edited)
# # -----------------------------
# key_metrics = results_df[['Model', 'Val_Weighted_Orig', 'Test_R2_Orig', 'Test_RMSE_Orig',
#                           'Test_MAE_Orig', 'Overfitting', 'Fit_Time (s)', 'CV_R2_Std']].set_index('Model')

# # Normalize each column to [0, 1] range
# key_metrics_normalized = key_metrics.copy()
# for col in key_metrics_normalized.columns:
#     col_min = key_metrics_normalized[col].min()
#     col_max = key_metrics_normalized[col].max()
#     if col_max > col_min:
#         key_metrics_normalized[col] = (key_metrics_normalized[col] - col_min) / (col_max - col_min)
#     else:
#         key_metrics_normalized[col] = 0  # If all values are the same, set to 0

# plt.figure(figsize=(12, 8))
# sns.heatmap(key_metrics_normalized, annot=True, cmap='viridis')
# plt.title('Key Metrics Heatmap (Normalized [0,1])')
# plt.xticks(rotation=45, ha='right')
# plt.tight_layout()
# plt.savefig(os.path.join(args.figures_dir, 'metrics_heatmap.png'))
# plt.close()

# # Pred vs Actual for Best & Ensemble
# plt.figure(figsize=(7,6))
# sns.scatterplot(x=y_test_original, y=np.expm1(y_test_pred_best))
# plt.plot([min(y_test_original), max(y_test_original)], [min(y_test_original), max(y_test_original)], linestyle='--')
# plt.xlabel('Actual (wt%)'); plt.ylabel('Predicted (wt%)'); plt.title(f'Pred vs Actual - {best_model_name}')
# plt.tight_layout(); plt.savefig(os.path.join(args.figures_dir, 'pred_vs_actual_best.png')); plt.close()

# plt.figure(figsize=(7,6))
# sns.scatterplot(x=y_test_original, y=np.expm1(y_test_pred_ens))
# plt.plot([min(y_test_original), max(y_test_original)], [min(y_test_original), max(y_test_original)], linestyle='--')
# plt.xlabel('Actual (wt%)'); plt.ylabel('Predicted (wt%)'); plt.title('Pred vs Actual - Ensemble')
# plt.tight_layout(); plt.savefig(os.path.join(args.figures_dir, 'pred_vs_actual_ensemble.png')); plt.close()

# print("All analysis artifacts written to:")
# print(" - CSV tables in:", args.output_dir)
# print(" - Figures in:", args.figures_dir)





import pandas as pd
import numpy as np
import os
import time
import json
import warnings
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

from scipy.stats import ttest_rel
from sklearn.linear_model import Ridge, Lasso, ElasticNet, BayesianRidge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import (ExtraTreesRegressor, GradientBoostingRegressor,
                              AdaBoostRegressor, RandomForestRegressor, StackingRegressor)
from catboost import CatBoostRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import StratifiedKFold, cross_validate, learning_curve
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, make_scorer
from sklearn.inspection import PartialDependenceDisplay
from sklearn.utils import resample

# SHAP
import shap

import argparse
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner

warnings.filterwarnings("ignore", category=UserWarning)

# -----------------------------
# Argument Parser and Paths
# -----------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', default=r'D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data')
parser.add_argument('--output_dir', default=r'D:\Hydride_Machine_learning_project\Machine_Model\reports\benchmarked_model_so')
parser.add_argument('--figures_dir', default=r'D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\default_benchmark_analysis_so')
parser.add_argument('--models_dir', default=r'D:\Hydride_Machine_learning_project\models\default_benchmark_models_so')
parser.add_argument('--params_dir', default=r'D:\Hydride_Machine_learning_project\reports\benchmarked_model_so\default_params')
parser.add_argument('--shap_sample', type=int, default=200, help='Max samples for SHAP to control runtime')
args = parser.parse_args()

os.makedirs(args.figures_dir, exist_ok=True)
os.makedirs(args.models_dir, exist_ok=True)
os.makedirs(args.params_dir, exist_ok=True)
os.makedirs(args.output_dir, exist_ok=True)

# -----------------------------
# Data Loading
# -----------------------------
train_path = os.path.join(args.data_dir, 'selected_train.csv')
val_path = os.path.join(args.data_dir, 'selected_val.csv')
test_path = os.path.join(args.data_dir, 'selected_test.csv')

df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded selected train data with shape: {df_train.shape}")
print(f"Loaded selected val data with shape: {df_val.shape}")
print(f"Loaded selected test data with shape: {df_test.shape}")

feature_cols = [col for col in df_train.columns if col not in ['target', 'formula']]
X_train, y_train = df_train[feature_cols], df_train['target'].values
X_val, y_val = df_val[feature_cols], df_val['target'].values
X_test, y_test = df_test[feature_cols], df_test['target'].values

# original scale
y_train_original, y_val_original, y_test_original = np.expm1(y_train), np.expm1(y_val), np.expm1(y_test)

has_temperature = 'temperature(K)' in df_train.columns
if has_temperature:
    temp_train, temp_val, temp_test = df_train['temperature(K)'], df_val['temperature(K)'], df_test['temperature(K)']
    def get_temp_group(temp):
        if temp < 300: return 'low'
        elif temp <= 500: return 'mid'
        else: return 'high'
    temp_group_train = np.array([get_temp_group(t) for t in temp_train])
    temp_group_val = np.array([get_temp_group(t) for t in temp_val])
    temp_group_test = np.array([get_temp_group(t) for t in temp_test])

binned_y = pd.qcut(y_train, q=10, labels=False, duplicates='drop')
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
splits = list(kf.split(X_train, binned_y))

# -----------------------------
# Models
# -----------------------------
models = {
    'Ridge': Ridge(random_state=42),
    'Lasso': Lasso(random_state=42),
    'ElasticNet': ElasticNet(random_state=42),
    'BayesianRidge': BayesianRidge(),
    'DecisionTree': DecisionTreeRegressor(random_state=42),
    'RandomForest': RandomForestRegressor(random_state=42, n_jobs=-1),
    'ExtraTrees': ExtraTreesRegressor(random_state=42, n_jobs=-1),
    'GradientBoosting': GradientBoostingRegressor(random_state=42),
    'AdaBoost': AdaBoostRegressor(random_state=42),
    'CatBoost': CatBoostRegressor(random_state=42, verbose=0),
    'SVR': SVR(kernel='rbf'),
    'KNN': KNeighborsRegressor(n_jobs=-1),
    'MLP': MLPRegressor(random_state=42, max_iter=8000, early_stopping=True)
}

# Default params for recreation
default_model_params = {
    'Ridge': {'random_state': 42},
    'Lasso': {'random_state': 42},
    'ElasticNet': {'random_state': 42},
    'BayesianRidge': {},
    'DecisionTree': {'random_state': 42},
    'RandomForest': {'random_state': 42, 'n_jobs': -1},
    'ExtraTrees': {'random_state': 42, 'n_jobs': -1},
    'GradientBoosting': {'random_state': 42},
    'AdaBoost': {'random_state': 42},
    'CatBoost': {'random_state': 42, 'verbose': 0},
    'SVR': {'kernel': 'rbf'},
    'KNN': {'n_jobs': -1},
    'MLP': {'random_state': 42, 'max_iter': 8000, 'early_stopping': True}
}

# -----------------------------
# Metrics
# -----------------------------
def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))

def weighted_score(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    mae = mae if mae != 0 else 1e-6
    return 0.6 * r2 + 0.4 / mae

def evaluate_model(y_true, y_pred, scale='orig'):
    if scale == 'orig':
        y_true_eval, y_pred_eval = np.expm1(y_true), np.expm1(y_pred)
    else:
        y_true_eval, y_pred_eval = y_true, y_pred
    mae = mean_absolute_error(y_true_eval, y_pred_eval)
    mse = mean_squared_error(y_true_eval, y_pred_eval)
    rmse_val = np.sqrt(mse)
    r2 = r2_score(y_true_eval, y_pred_eval)
    mae_adj = mae if mae != 0 else 1e-6
    w_score = 0.6 * r2 + 0.4 / mae_adj
    return mae, mse, rmse_val, r2, w_score

def bootstrap_ci(y_true, y_pred, metric_func, n_boot=2000, ci=95):
    np.random.seed(42)
    boot_scores = [metric_func(*resample(y_true, y_pred)) for _ in range(n_boot)]
    return np.percentile(boot_scores, (100 - ci) / 2), np.percentile(boot_scores, 100 - (100 - ci) / 2)

# -----------------------------
# Optuna Objective for Base Models
# -----------------------------
def optuna_objective(trial, model_name, X, y, cv_splits):
    if model_name in ['Ridge', 'Lasso']:
        params = {'alpha': trial.suggest_float('alpha', 1e-3, 1e2, log=True)}
        model = models[model_name].__class__(**params, random_state=42)
    elif model_name == 'ElasticNet':
        params = {
            'alpha': trial.suggest_float('alpha', 1e-3, 1e2, log=True),
            'l1_ratio': trial.suggest_float('l1_ratio', 1.0, 10.0)
        }
        model = ElasticNet(**params, random_state=42)
    elif model_name == 'BayesianRidge':
        params = {
            'alpha_1': trial.suggest_float('alpha_1', 1e-7, 1e-5, log=True),
            'alpha_2': trial.suggest_float('alpha_2', 1e-7, 1e-5, log=True),
            'lambda_1': trial.suggest_float('lambda_1', 1e-7, 1e-5, log=True),
            'lambda_2': trial.suggest_float('lambda_2', 1e-7, 1e-5, log=True)
        }
        model = BayesianRidge(**params)
    elif model_name == 'DecisionTree':
        params = {
            'max_depth': trial.suggest_int('max_depth', 3, 20),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10)
        }
        model = DecisionTreeRegressor(**params, random_state=42)
    elif model_name in ['RandomForest', 'ExtraTrees']:
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 500, 5000, step=50),
            'max_depth': trial.suggest_int('max_depth', 5, 30),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
            'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
            'bootstrap': trial.suggest_categorical('bootstrap', [True, False])
        }
        model = models[model_name].__class__(**params, random_state=42, n_jobs=-1)
    elif model_name == 'GradientBoosting':
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 1000, 10000, step=50),
            'learning_rate': trial.suggest_float('learning_rate', 0.0001, 0.1, log=True),
            'max_depth': trial.suggest_int('max_depth', 3, 15),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
            'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
        }
        model = GradientBoostingRegressor(**params, random_state=42)
    elif model_name == 'AdaBoost':
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 1000, step=50),
            'learning_rate': trial.suggest_float('learning_rate', 0.001, 1.0, log=True)
        }
        model = AdaBoostRegressor(**params, random_state=42)
    elif model_name == 'CatBoost':
        params = {
            'iterations': trial.suggest_int('iterations', 1000, 15000, step=250),
            'learning_rate': trial.suggest_float('learning_rate', 0.0001, 0.1, log=True),
            'depth': trial.suggest_int('depth', 4, 16),
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 50, log=True),
            'bagging_temperature': trial.suggest_float('bagging_temperature', 0, 5),
            'random_strength': trial.suggest_float('random_strength', 0.5, 20),
            'grow_policy': trial.suggest_categorical('grow_policy', ['SymmetricTree', 'Depthwise', 'Lossguide']),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'loss_function': 'RMSE',
            'border_count': trial.suggest_int('border_count', 32, 256)
            
        }
        model = CatBoostRegressor(**params, random_state=42, verbose=0, early_stopping_rounds=1000)
    # elif model_name == 'SVR':
    #     params = {
    #         'C': trial.suggest_float('C', 0.1, 100, log=True),
    #         'epsilon': trial.suggest_float('epsilon', 0.00001, 100.0, log=True),
    #         'gamma': trial.suggest_categorical('gamma', ['scale', 'auto']),
    #         'kernel': trial.suggest_categorical('kernel', ['rbf', 'poly', 'sigmoid'])
    #     }
    #     model = SVR(**params)
    elif model_name == 'KNN':
        params = {
            'n_neighbors': trial.suggest_int('n_neighbors', 1, 50),
            'weights': trial.suggest_categorical('weights', ['uniform', 'distance']),
            'p': trial.suggest_int('p', 1, 2)
        }
        model = KNeighborsRegressor(**params, n_jobs=-1)
    elif model_name == 'MLP':
        params = {
            'hidden_layer_sizes': trial.suggest_categorical('hidden_layer_sizes',
                                                            [(50,), (100,), (200,), (100,50), (300,200,100), (500,300,100)]),
            'alpha': trial.suggest_float('alpha', 1e-5, 1e1, log=True),
            'learning_rate_init': trial.suggest_float('learning_rate_init', 1e-6, 1e-3, log=True),
            'activation': trial.suggest_categorical('activation', ['relu', 'tanh']),
            'solver': trial.suggest_categorical('solver', ['adam', 'lbfgs']),
            'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128, 256])
        }
        model = MLPRegressor(**params, random_state=42, max_iter=10000, early_stopping=True)
    else:
        raise ValueError(f"Model {model_name} not implemented for tuning.")

    pipe = Pipeline([('scaler', RobustScaler()), ('reg', model)])
    cv_results = cross_validate(pipe, X, y, cv=cv_splits, scoring='r2', n_jobs=-1)
    return cv_results['test_score'].mean()

# -----------------------------
# Optuna Objective for Stacking Final Estimator (Ridge)
# -----------------------------
def optuna_stacking_objective(trial, estimators, X, y, cv_splits):
    alpha = trial.suggest_float('alpha', 1e-3, 1e2, log=True)
    stacking_model = StackingRegressor(estimators=estimators, final_estimator=Ridge(alpha=alpha, random_state=42), cv=5, n_jobs=-1)
    pipe = Pipeline([('scaler', RobustScaler()), ('reg', stacking_model)])
    cv_results = cross_validate(pipe, X, y, cv=cv_splits, scoring='r2', n_jobs=-1)
    return cv_results['test_score'].mean()

# -----------------------------
# Main Training Loop - Phase 1: Default Models
# -----------------------------
scoring = {
    'MAE': make_scorer(mean_absolute_error, greater_is_better=False),
    'R2': 'r2',
    'RMSE': make_scorer(rmse, greater_is_better=False),
    'Weighted': make_scorer(weighted_score, greater_is_better=True)
}

default_results = []
default_pipes = {}
default_cv_folds = []  # For later t-tests

for name, base_model in models.items():
    start_time = time.time()
    pipe = Pipeline([('scaler', RobustScaler()), ('reg', base_model)])
    cv_results = cross_validate(pipe, X_train, y_train, cv=splits, scoring=scoring, n_jobs=-1, return_estimator=False)

    # Capture per-fold metrics
    r2_folds = cv_results['test_R2']
    rmse_folds = -cv_results['test_RMSE']  # Note: RMSE is negative in scoring
    mae_folds = -cv_results['test_MAE']
    w_folds = cv_results['test_Weighted']
    for i in range(len(r2_folds)):
        default_cv_folds.append({'Model': name, 'Fold': i+1, 'R2': r2_folds[i], 'RMSE': rmse_folds[i], 'MAE': mae_folds[i], 'Weighted': w_folds[i]})

    cv_r2_mean = r2_folds.mean()
    cv_r2_std = r2_folds.std()
    cv_rmse_mean = rmse_folds.mean()
    cv_mae_mean = mae_folds.mean()
    cv_weighted_mean = w_folds.mean()

    pipe.fit(X_train, y_train)
    default_pipes[name] = pipe

    y_train_pred = pipe.predict(X_train)
    y_val_pred = pipe.predict(X_val)
    y_test_pred = pipe.predict(X_test)

    train_mae_orig, _, train_rmse_orig, train_r2_orig, train_w_orig = evaluate_model(y_train, y_train_pred, 'orig')
    val_mae_orig, _, val_rmse_orig, val_r2_orig, val_w_orig = evaluate_model(y_val, y_val_pred, 'orig')
    test_mae_orig, _, test_rmse_orig, test_r2_orig, test_w_orig = evaluate_model(y_test, y_test_pred, 'orig')

    overfitting = train_r2_orig - val_r2_orig
    fit_time = time.time() - start_time

    default_results.append({
        'Model': name,
        'CV_R2_Mean': cv_r2_mean,
        'CV_R2_Std': cv_r2_std,
        'CV_RMSE_Mean': cv_rmse_mean,
        'CV_MAE_Mean': cv_mae_mean,
        'CV_Weighted_Mean': cv_weighted_mean,
        'Val_R2_Orig': val_r2_orig,
        'Val_MAE_Orig': val_mae_orig,
        'Overfitting': overfitting,
        'Fit_Time (s)': fit_time
    })

default_results_df = pd.DataFrame(default_results).sort_values(by=['CV_R2_Mean', 'CV_MAE_Mean'], ascending=[False, True])
default_results_df.to_csv(os.path.join(args.output_dir, 'default_model_results.csv'), index=False)

# Select top 5 default models for tuning
top_5_names = default_results_df['Model'].head(5).tolist()
print(f"Top 5 default models for tuning: {top_5_names}")

# -----------------------------
# Phase 2: Tune Top 5 with Optuna
# -----------------------------
tuned_results = []
tuned_pipes = {}
tuned_cv_folds = []

for name in top_5_names:
    start_time = time.time()
    print(f"Tuning {name} with Optuna...")
    study = optuna.create_study(direction='maximize',
                                sampler=TPESampler(seed=42),
                                pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3))
    study.optimize(lambda trial: optuna_objective(trial, name, X_train, y_train, splits),
                   n_trials=200, timeout=7200, n_jobs=-1)
    best_params = study.best_params
    print(f"Best params for {name}: {best_params}")
    with open(os.path.join(args.params_dir, f"{name}_tuned_params.json"), 'w') as f:
        json.dump(best_params, f, indent=4)

    # Recreate a new unfitted model with best params
    default_params = default_model_params.get(name, {})
    base_model = models[name].__class__(**{**default_params, **best_params})

    pipe = Pipeline([('scaler', RobustScaler()), ('reg', base_model)])
    cv_results = cross_validate(pipe, X_train, y_train, cv=splits, scoring=scoring, n_jobs=-1, return_estimator=False)

    r2_folds = cv_results['test_R2']
    rmse_folds = -cv_results['test_RMSE']
    mae_folds = -cv_results['test_MAE']
    w_folds = cv_results['test_Weighted']
    for i in range(len(r2_folds)):
        tuned_cv_folds.append({'Model': name, 'Fold': i+1, 'R2': r2_folds[i], 'RMSE': rmse_folds[i], 'MAE': mae_folds[i], 'Weighted': w_folds[i]})

    cv_r2_mean = r2_folds.mean()
    cv_r2_std = r2_folds.std()
    cv_rmse_mean = rmse_folds.mean()
    cv_mae_mean = mae_folds.mean()
    cv_weighted_mean = w_folds.mean()

    pipe.fit(X_train, y_train)
    tuned_pipes[name] = pipe

    y_train_pred = pipe.predict(X_train)
    y_val_pred = pipe.predict(X_val)
    y_test_pred = pipe.predict(X_test)

    train_mae_orig, _, train_rmse_orig, train_r2_orig, train_w_orig = evaluate_model(y_train, y_train_pred, 'orig')
    val_mae_orig, _, val_rmse_orig, val_r2_orig, val_w_orig = evaluate_model(y_val, y_val_pred, 'orig')
    test_mae_orig, _, test_rmse_orig, test_r2_orig, test_w_orig = evaluate_model(y_test, y_test_pred, 'orig')

    r2_low, r2_high = bootstrap_ci(y_val_original, np.expm1(y_val_pred), r2_score)
    mae_low, mae_high = bootstrap_ci(y_val_original, np.expm1(y_val_pred), mean_absolute_error)
    rmse_low, rmse_high = bootstrap_ci(y_val_original, np.expm1(y_val_pred), lambda yt, yp: np.sqrt(mean_squared_error(yt, yp)))

    overfitting = train_r2_orig - val_r2_orig
    fit_time = time.time() - start_time

    tuned_results.append({
        'Model': name,
        'CV_R2_Mean': cv_r2_mean,
        'CV_R2_Std': cv_r2_std,
        'CV_RMSE_Mean': cv_rmse_mean,
        'CV_MAE_Mean': cv_mae_mean,
        'CV_Weighted_Mean': cv_weighted_mean,
        'Train_R2_Orig': train_r2_orig,
        'Train_RMSE_Orig': train_rmse_orig,
        'Train_MAE_Orig': train_mae_orig,
        'Train_Weighted_Orig': train_w_orig,
        'Val_R2_Orig': val_r2_orig,
        'Val_RMSE_Orig': val_rmse_orig,
        'Val_MAE_Orig': val_mae_orig,
        'Val_Weighted_Orig': val_w_orig,
        'Test_R2_Orig': test_r2_orig,
        'Test_RMSE_Orig': test_rmse_orig,
        'Test_MAE_Orig': test_mae_orig,
        'Test_Weighted_Orig': test_w_orig,
        'Overfitting': overfitting,
        'Fit_Time (s)': fit_time,
        'Val_R2_CI_Low': r2_low,
        'Val_R2_CI_High': r2_high,
        'Val_MAE_CI_Low': mae_low,
        'Val_MAE_CI_High': mae_high,
        'Val_RMSE_CI_Low': rmse_low,
        'Val_RMSE_CI_High': rmse_high
    })

    joblib.dump(pipe, os.path.join(args.models_dir, f"{name}_tuned_model.pkl"), compress=3)

tuned_results_df = pd.DataFrame(tuned_results).sort_values(by=['CV_R2_Mean', 'CV_MAE_Mean'], ascending=[False, True])
tuned_results_df.to_csv(os.path.join(args.output_dir, 'tuned_model_results.csv'), index=False)

# -----------------------------
# Phase 3: Stacking with Tuned Top 5
# -----------------------------
estimators = [(name, tuned_pipes[name].named_steps['reg']) for name in top_5_names]

print("Tuning Stacking final estimator with Optuna...")
study_stack = optuna.create_study(direction='maximize',
                                  sampler=TPESampler(seed=42),
                                  pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3))
study_stack.optimize(lambda trial: optuna_stacking_objective(trial, estimators, X_train, y_train, splits),
                     n_trials=100,  timeout=3600, n_jobs=-1)
best_alpha = study_stack.best_params['alpha']
print(f"Best alpha for Stacking Ridge: {best_alpha}")

with open(os.path.join(args.params_dir, "stacking_tuned_params.json"), 'w') as f:
    json.dump({'alpha': best_alpha}, f, indent=4)

stacking_model = StackingRegressor(estimators=estimators, final_estimator=Ridge(alpha=best_alpha, random_state=42), cv=5, n_jobs=-1)

stack_pipe = Pipeline([('scaler', RobustScaler()), ('reg', stacking_model)])
cv_results_stack = cross_validate(stack_pipe, X_train, y_train, cv=splits, scoring=scoring, n_jobs=-1)

r2_folds_stack = cv_results_stack['test_R2']
rmse_folds_stack = -cv_results_stack['test_RMSE']
mae_folds_stack = -cv_results_stack['test_MAE']
w_folds_stack = cv_results_stack['test_Weighted']

cv_r2_mean_stack = r2_folds_stack.mean()
cv_r2_std_stack = r2_folds_stack.std()
cv_rmse_mean_stack = rmse_folds_stack.mean()
cv_mae_mean_stack = mae_folds_stack.mean()
cv_weighted_mean_stack = w_folds_stack.mean()

stack_pipe.fit(X_train, y_train)

y_train_pred_stack = stack_pipe.predict(X_train)
y_val_pred_stack = stack_pipe.predict(X_val)
y_test_pred_stack = stack_pipe.predict(X_test)

train_mae_orig_stack, _, train_rmse_orig_stack, train_r2_orig_stack, train_w_orig_stack = evaluate_model(y_train, y_train_pred_stack, 'orig')
val_mae_orig_stack, _, val_rmse_orig_stack, val_r2_orig_stack, val_w_orig_stack = evaluate_model(y_val, y_val_pred_stack, 'orig')
test_mae_orig_stack, _, test_rmse_orig_stack, test_r2_orig_stack, test_w_orig_stack = evaluate_model(y_test, y_test_pred_stack, 'orig')

r2_low_stack, r2_high_stack = bootstrap_ci(y_val_original, np.expm1(y_val_pred_stack), r2_score)
mae_low_stack, mae_high_stack = bootstrap_ci(y_val_original, np.expm1(y_val_pred_stack), mean_absolute_error)
rmse_low_stack, rmse_high_stack = bootstrap_ci(y_val_original, np.expm1(y_val_pred_stack), lambda yt, yp: np.sqrt(mean_squared_error(yt, yp)))

overfitting_stack = train_r2_orig_stack - val_r2_orig_stack

stack_results = {
    'Model': 'Ensemble',
    'CV_R2_Mean': cv_r2_mean_stack,
    'CV_R2_Std': cv_r2_std_stack,
    'CV_RMSE_Mean': cv_rmse_mean_stack,
    'CV_MAE_Mean': cv_mae_mean_stack,
    'CV_Weighted_Mean': cv_weighted_mean_stack,
    'Train_R2_Orig': train_r2_orig_stack,
    'Train_RMSE_Orig': train_rmse_orig_stack,
    'Train_MAE_Orig': train_mae_orig_stack,
    'Train_Weighted_Orig': train_w_orig_stack,
    'Val_R2_Orig': val_r2_orig_stack,
    'Val_RMSE_Orig': val_rmse_orig_stack,
    'Val_MAE_Orig': val_mae_orig_stack,
    'Val_Weighted_Orig': val_w_orig_stack,
    'Test_R2_Orig': test_r2_orig_stack,
    'Test_RMSE_Orig': test_rmse_orig_stack,
    'Test_MAE_Orig': test_mae_orig_stack,
    'Test_Weighted_Orig': test_w_orig_stack,
    'Overfitting': overfitting_stack,
    'Val_R2_CI_Low': r2_low_stack,
    'Val_R2_CI_High': r2_high_stack,
    'Val_MAE_CI_Low': mae_low_stack,
    'Val_MAE_CI_High': mae_high_stack,
    'Val_RMSE_CI_Low': rmse_low_stack,
    'Val_RMSE_CI_High': rmse_high_stack
}

pd.DataFrame([stack_results]).to_csv(os.path.join(args.output_dir, 'stacking_results.csv'), index=False)
joblib.dump(stack_pipe, os.path.join(args.models_dir, 'stacking_model.pkl'), compress=3)

# -----------------------------
# Best Model Selection (from tuned top 5)
# -----------------------------
best_model_name = tuned_results_df.loc[tuned_results_df['CV_R2_Mean'].idxmax(), 'Model']
best_pipe = tuned_pipes[best_model_name]
y_test_pred_best = best_pipe.predict(X_test)
y_test_pred_ens = stack_pipe.predict(X_test)

# -----------------------------
# Paired t-test on abs errors (Best vs Ensemble)
# -----------------------------
abs_err_best = np.abs(y_test_original - np.expm1(y_test_pred_best))
abs_err_ens = np.abs(y_test_original - np.expm1(y_test_pred_ens))
t_stat_ae, p_val_ae = ttest_rel(abs_err_best, abs_err_ens)
pd.DataFrame([{'Test': 'Paired t-test |AE| (Best vs Ensemble)',
               't_stat': t_stat_ae, 'p_value': p_val_ae,
               'BestModel': best_model_name}]).to_csv(os.path.join(args.output_dir, 'ttest_best_vs_ensemble_abs_error.csv'), index=False)

# -----------------------------
# Feature Importances (for tree-based tuned models)
# -----------------------------
feature_importances = {}
for name in top_5_names:
    pipe = tuned_pipes[name]
    if hasattr(pipe.named_steps['reg'], 'feature_importances_'):
        importances = pipe.named_steps['reg'].feature_importances_
        imp_df = pd.DataFrame({'Feature': feature_cols, 'Importance': importances}).sort_values('Importance', ascending=False)
        imp_df.to_csv(os.path.join(args.figures_dir, f"{name}_feature_importance.csv"), index=False)
        feature_importances[name] = imp_df

# -----------------------------
# Learning Curves (Best & Ensemble)
# -----------------------------
train_sizes, train_scores, val_scores = learning_curve(best_pipe, X_train, y_train, cv=5, n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 5))
train_sizes_ens, train_scores_ens, val_scores_ens = learning_curve(stack_pipe, X_train, y_train, cv=5, n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 5))

plt.figure(figsize=(8,6))
plt.plot(train_sizes, train_scores.mean(axis=1), label='Train')
plt.plot(train_sizes, val_scores.mean(axis=1), label='Validation')
plt.xlabel('Training Examples'); plt.ylabel('R²'); plt.title(f'Learning Curve - {best_model_name}')
plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(args.figures_dir, 'learning_curve_best.png'))
plt.close()

plt.figure(figsize=(8,6))
plt.plot(train_sizes_ens, train_scores_ens.mean(axis=1), label='Train')
plt.plot(train_sizes_ens, val_scores_ens.mean(axis=1), label='Validation')
plt.xlabel('Training Examples'); plt.ylabel('R²'); plt.title('Learning Curve - Ensemble')
plt.legend(); plt.tight_layout()
plt.savefig(os.path.join(args.figures_dir, 'learning_curve_ensemble.png'))
plt.close()

# -----------------------------
# Partial Dependence (Best & Ensemble)
# -----------------------------
key_features = feature_importances.get(best_model_name, pd.DataFrame({'Feature': feature_cols[:5] }))['Feature'].head(5).values

for feat in key_features:
    feat_idx = feature_cols.index(feat)
    fig, ax = plt.subplots(figsize=(7,5))
    PartialDependenceDisplay.from_estimator(best_pipe, X_test, features=[feat_idx], feature_names=feature_cols, ax=ax)
    plt.tight_layout()
    plt.savefig(os.path.join(args.figures_dir, f'pdp_best_{feat.replace("/", "-")}.png'))
    plt.close()

for feat in key_features:
    feat_idx = feature_cols.index(feat)
    fig, ax = plt.subplots(figsize=(7,5))
    PartialDependenceDisplay.from_estimator(stack_pipe, X_test, features=[feat_idx], feature_names=feature_cols, ax=ax)
    plt.tight_layout()
    plt.savefig(os.path.join(args.figures_dir, f'pdp_ensemble_{feat.replace("/", "-")}.png'))
    plt.close()

# -----------------------------
# SHAP for Best Model
# -----------------------------
sample_n = min(args.shap_sample, len(X_test))
rng = np.random.RandomState(42)
sample_idx = rng.choice(np.arange(len(X_test)), size=sample_n, replace=False)
X_shap = X_test.iloc[sample_idx].copy()

reg = best_pipe.named_steps['reg']
if isinstance(reg, (RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor, DecisionTreeRegressor, CatBoostRegressor)):
    explainer = shap.TreeExplainer(reg)
else:
    bg = X_train.sample(min(100, len(X_train)), random_state=42)
    explainer = shap.KernelExplainer(lambda x: best_pipe.predict(pd.DataFrame(x, columns=feature_cols)), bg.to_numpy())

shap_values = explainer.shap_values(X_shap)

plt.figure()
shap.summary_plot(shap_values, X_shap, show=False)
plt.tight_layout()
plt.savefig(os.path.join(args.figures_dir, 'shap_summary_best.png'), bbox_inches='tight')
plt.close()

mean_abs = np.abs(shap_values).mean(axis=0)
shap_imp = pd.DataFrame({'Feature': X_shap.columns, 'MeanAbsSHAP': mean_abs}).sort_values('MeanAbsSHAP', ascending=False)
shap_imp.to_csv(os.path.join(args.output_dir, 'shap_importance_best.csv'), index=False)

for feat in shap_imp['Feature'].head(5):
    plt.figure()
    shap.dependence_plot(feat, shap_values, X_shap, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(args.figures_dir, f'shap_dependence_{feat.replace("/", "-")}.png'), bbox_inches='tight')
    plt.close()

# -----------------------------
# Metrics Heatmap & Pred vs Actual
# -----------------------------
all_results_df = pd.concat([tuned_results_df, pd.DataFrame([stack_results])], ignore_index=True)
key_metrics = all_results_df[['Model', 'Val_Weighted_Orig', 'Test_R2_Orig', 'Test_RMSE_Orig',
                             'Test_MAE_Orig', 'Overfitting', 'Fit_Time (s)', 'CV_R2_Std']].set_index('Model')

key_metrics_normalized = key_metrics.copy()
for col in key_metrics_normalized.columns:
    col_min = key_metrics_normalized[col].min()
    col_max = key_metrics_normalized[col].max()
    if col_max > col_min:
        key_metrics_normalized[col] = (key_metrics_normalized[col] - col_min) / (col_max - col_min)
    else:
        key_metrics_normalized[col] = 0

plt.figure(figsize=(12, 8))
sns.heatmap(key_metrics_normalized, annot=True, cmap='viridis')
plt.title('Key Metrics Heatmap (Normalized [0,1])')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(args.figures_dir, 'metrics_heatmap.png'))
plt.close()

plt.figure(figsize=(7,6))
sns.scatterplot(x=y_test_original, y=np.expm1(y_test_pred_best))
plt.plot([min(y_test_original), max(y_test_original)], [min(y_test_original), max(y_test_original)], linestyle='--')
plt.xlabel('Actual (wt%)'); plt.ylabel('Predicted (wt%)'); plt.title(f'Pred vs Actual - {best_model_name}')
plt.tight_layout(); plt.savefig(os.path.join(args.figures_dir, 'pred_vs_actual_best.png')); plt.close()

plt.figure(figsize=(7,6))
sns.scatterplot(x=y_test_original, y=np.expm1(y_test_pred_ens))
plt.plot([min(y_test_original), max(y_test_original)], [min(y_test_original), max(y_test_original)], linestyle='--')
plt.xlabel('Actual (wt%)'); plt.ylabel('Predicted (wt%)'); plt.title('Pred vs Actual - Ensemble')
plt.tight_layout(); plt.savefig(os.path.join(args.figures_dir, 'pred_vs_actual_ensemble.png')); plt.close()