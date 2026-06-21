# # # File: D:\Hydride_Machine_learning_project\Machine_Model\src\optimize_catboost.py
# # import pandas as pd
# # import numpy as np
# # from sklearn.model_selection import StratifiedKFold, cross_val_score
# # from sklearn.preprocessing import RobustScaler, StandardScaler
# # from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
# # from catboost import CatBoostRegressor, Pool
# # import optuna
# # from optuna.samplers import TPESampler
# # from optuna.pruners import MedianPruner
# # import joblib
# # import matplotlib.pyplot as plt
# # import os
# # import warnings
# # from scipy.stats import ttest_rel
# # warnings.filterwarnings("ignore", category=UserWarning)

# # # Paths
# # benchmark_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\benchmarked_model\default_benchmark_results.csv"
# # train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_train.csv"
# # val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_val.csv"
# # test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_test.csv"
# # optimized_results_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\optimized_optuna\catboost_optimized_results.csv"
# # comparison_report_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\comparison\catboost_comparison_report.md"
# # catboost_model_path = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna\catboost_model.pkl"
# # plot_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\optimization\catboost_performance_plots.png"
# # optimized_models_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna"
# # os.makedirs(optimized_models_dir, exist_ok=True)
# # os.makedirs(os.path.dirname(optimized_results_path), exist_ok=True)

# # # Load benchmark for CatBoost
# # benchmark_df = pd.read_csv(benchmark_path)
# # catboost_benchmark = benchmark_df[benchmark_df['Model'] == 'CatBoost'].iloc[0]

# # # Load datasets
# # df_train = pd.read_csv(train_path)
# # df_val = pd.read_csv(val_path)
# # df_test = pd.read_csv(test_path)

# # # Separate features and target
# # X_train = df_train.drop(['target', 'formula'], axis=1, errors='ignore')
# # y_train = df_train['target']
# # y_train_original = np.expm1(y_train)
# # X_val = df_val.drop(['target', 'formula'], axis=1, errors='ignore')
# # y_val = df_val['target']
# # y_val_original = np.expm1(y_val)
# # X_test = df_test.drop(['target', 'formula'], axis=1, errors='ignore')
# # y_test = df_test['target']
# # y_test_original = np.expm1(y_test)

# # # Scale features with RobustScaler
# # scaler = StandardScaler()
# # X_train_scaled = scaler.fit_transform(X_train)
# # X_val_scaled = scaler.transform(X_val)
# # X_test_scaled = scaler.transform(X_test)

# # # StratifiedKFold with 10 splits
# # binned_y = pd.qcut(y_train, q=5, labels=False, duplicates='drop')
# # kf = StratifiedKFold(n_splits=7, shuffle=True, random_state=42)
# # splits = list(kf.split(X_train, binned_y))

# # # Evaluation function
# # def evaluate_model(y_true, y_pred, scale='orig'):
# #     if scale == 'orig':
# #         y_true_eval = np.expm1(y_true)
# #         y_pred_eval = np.expm1(y_pred)
# #     else:
# #         y_true_eval = y_true
# #         y_pred_eval = y_pred
# #     mae = mean_absolute_error(y_true_eval, y_pred_eval)
# #     mse = mean_squared_error(y_true_eval, y_pred_eval)
# #     rmse = np.sqrt(mse)
# #     r2 = r2_score(y_true_eval, y_pred_eval)
# #     return mae, mse, rmse, r2

# # # Optimize CatBoost
# # def optimize_catboost():
# #     pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3)
# #     study = optuna.create_study(direction='maximize', sampler=TPESampler(seed=42), pruner=pruner)
    
# #     def objective(trial):
# #         params = {
# #             'learning_rate': trial.suggest_float('learning_rate', 0.0005, 0.001, log=True),
# #             'depth': trial.suggest_int('depth', 3, 10),
# #             'iterations': trial.suggest_int('iterations', 5000, 20000),
# #             'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 3, 10),
# #             'bagging_temperature': trial.suggest_float('bagging_temperature', 0, 1),
# #             'random_strength': trial.suggest_float('random_strength', 1, 10),
# #             'grow_policy': 'Lossguide',
# #             'od_type': 'IncToDec',
# #             'od_pval': 1e-2,
# #             'random_seed': 42,
# #             'loss_function': 'RMSE',
# #             'verbose': 0,
# #             'task_type': 'CPU',
# #             'border_count': trial.suggest_int('border_count', 32, 256)
# #         }
# #         cv_r2s = []
# #         for i, (train_idx, val_idx) in enumerate(splits):
# #             X_tr = X_train.iloc[train_idx]
# #             X_v = X_train.iloc[val_idx]
# #             y_tr = y_train.iloc[train_idx]
# #             y_v = y_train.iloc[val_idx]
# #             scaler_fold = StandardScaler()
# #             X_tr_scaled = scaler_fold.fit_transform(X_tr)
# #             X_v_scaled = scaler_fold.transform(X_v)
# #             train_pool = Pool(X_tr_scaled, y_tr)
# #             val_pool = Pool(X_v_scaled, y_v)
# #             model = CatBoostRegressor(**params)
# #             model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=1000)
# #             y_v_pred = model.predict(val_pool)
# #             r2 = r2_score(y_v, y_v_pred)
# #             cv_r2s.append(r2)
# #             trial.report(r2, i)
# #             if trial.should_prune():
# #                 raise optuna.TrialPruned()
# #         return np.mean(cv_r2s)
    
# #     study.optimize(objective, n_trials=150)
# #     return study.best_params

# # print("Optimizing CatBoost...")
# # best_params = optimize_catboost()
# # best_params.update({
# #     # 'iterations': 20000,
# #     'grow_policy': 'Lossguide',
# #     'od_type': 'IncToDec',
# #     'od_pval': 1e-2,
# #     'verbose': 0,
# #     'random_seed': 42,
# #     'task_type': 'CPU'
# # })

# # # Train initial CatBoost model
# # train_pool = Pool(X_train_scaled, y_train)
# # val_pool = Pool(X_val_scaled, y_val)
# # init_model = CatBoostRegressor(**best_params)
# # init_model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=5000)
# # init_model.save_model('init_model.cbm')

# # # Continue training on combined train+val with init_model
# # combined_X_scaled = np.vstack([X_train_scaled, X_val_scaled])
# # combined_y = pd.concat([y_train, y_val])
# # combined_pool = Pool(combined_X_scaled, combined_y)
# # test_pool = Pool(X_test_scaled, y_test)
# # loaded_init_model = CatBoostRegressor().load_model('init_model.cbm')
# # final_model = CatBoostRegressor(**best_params)
# # final_model.fit(combined_pool, eval_set=test_pool, early_stopping_rounds=5000, init_model=loaded_init_model)
# # joblib.dump(final_model, catboost_model_path, compress=3)

# # # Feature importance for selection (optional: select top features)
# # feature_importances = final_model.get_feature_importance()
# # top_features = np.argsort(feature_importances)[-10:]  # Example: top 5
# # print("Top features indices:", top_features)

# # # Evaluate
# # y_train_pred = final_model.predict(X_train_scaled)
# # y_val_pred = final_model.predict(X_val_scaled)
# # y_test_pred = final_model.predict(X_test_scaled)

# # train_mae_log, train_mse_log, train_rmse_log, train_r2_log = evaluate_model(y_train, y_train_pred, 'log')
# # val_mae_log, val_mse_log, val_rmse_log, val_r2_log = evaluate_model(y_val, y_val_pred, 'log')
# # test_mae_log, test_mse_log, test_rmse_log, test_r2_log = evaluate_model(y_test, y_test_pred, 'log')

# # train_mae_orig, train_mse_orig, train_rmse_orig, train_r2_orig = evaluate_model(y_train, y_train_pred, 'orig')
# # val_mae_orig, val_mse_orig, val_rmse_orig, val_r2_orig = evaluate_model(y_val, y_val_pred, 'orig')
# # test_mae_orig, test_mse_orig, test_rmse_orig, test_r2_orig = evaluate_model(y_test, y_test_pred, 'orig')

# # cv_r2 = cross_val_score(final_model, X_train_scaled, y_train, cv=7, scoring='r2').mean()

# # overfitting_train_val = train_r2_orig - val_r2_orig
# # overfitting_train_test = train_r2_orig - test_r2_orig
# # print(f"CatBoost Overfitting Train-Val: {overfitting_train_val}, Train-Test: {overfitting_train_test}")

# # results = {
# #     'CV_R2_Mean': cv_r2,
# #     'Train_R2_Log': train_r2_log,
# #     'Train_RMSE_Log': train_rmse_log,
# #     'Train_MAE_Log': train_mae_log,
# #     'Val_R2_Log': val_r2_log,
# #     'Val_RMSE_Log': val_rmse_log,
# #     'Val_MAE_Log': val_mae_log,
# #     'Test_R2_Log': test_r2_log,
# #     'Test_RMSE_Log': test_rmse_log,
# #     'Test_MAE_Log': test_mae_log,
# #     'Train_R2_Orig': train_r2_orig,
# #     'Train_RMSE_Orig': train_rmse_orig,
# #     'Train_MAE_Orig': train_mae_orig,
# #     'Val_R2_Orig': val_r2_orig,
# #     'Val_RMSE_Orig': val_rmse_orig,
# #     'Val_MAE_Orig': val_mae_orig,
# #     'Test_R2_Orig': test_r2_orig,
# #     'Test_RMSE_Orig': test_rmse_orig,
# #     'Test_MAE_Orig': test_mae_orig,
# #     'Overfitting_Train_Val': overfitting_train_val,
# #     'Overfitting_Train_Test': overfitting_train_test
# # }

# # results_df = pd.DataFrame([results])
# # results_df.to_csv(optimized_results_path, index=False)

# # # Comparison with base
# # comparison_df = pd.concat([pd.Series(catboost_benchmark), results_df.iloc[0]], axis=1, keys=['Base', 'Optimized'])

# # # Generate Markdown report
# # with open(comparison_report_path, 'w') as f:
# #     f.write("# Comparison Report: Base vs Optimized CatBoost\n\n")
# #     f.write(comparison_df.to_markdown())

# # # Performance plots
# # metrics = ['CV_R2_Mean', 'Test_R2_Orig', 'Test_MAE_Orig']
# # fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 6*len(metrics)))
# # for i, metric in enumerate(metrics):
# #     sub_df = comparison_df.loc[metric].to_frame().T
# #     sub_df.columns = ['Base', 'Optimized']
# #     sub_df.plot(kind='bar', ax=axes[i])
# #     axes[i].set_title(f'{metric}: Base vs Optimized')
# #     axes[i].set_xticklabels(['CatBoost'], rotation=0)
# #     axes[i].legend()

# # plt.tight_layout()
# # plt.savefig(plot_path)
# # plt.close()


# # File: D:\Hydride_Machine_learning_project\Machine_Model\src\optimize_catboost.py
# import pandas as pd
# import numpy as np
# from sklearn.model_selection import StratifiedKFold, cross_val_score
# from sklearn.preprocessing import RobustScaler, StandardScaler
# from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
# from catboost import CatBoostRegressor, Pool
# import optuna
# from optuna.samplers import TPESampler
# from optuna.pruners import MedianPruner
# import joblib
# import matplotlib.pyplot as plt
# import os
# import warnings
# from scipy.stats import ttest_rel
# from sklearn.linear_model import Ridge
# warnings.filterwarnings("ignore", category=UserWarning)

# # Paths
# benchmark_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\benchmarked_model\default_benchmark_results.csv"
# train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_train.csv"
# val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_val.csv"
# test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_test.csv"
# optimized_results_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\optimized_optuna\catboost_optimized_results.csv"
# comparison_report_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\comparison\catboost_comparison_report.md"
# catboost_model_path = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna\catboost_model.pkl"
# plot_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\optimization\catboost_performance_plots.png"
# optimized_models_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna"
# os.makedirs(optimized_models_dir, exist_ok=True)
# os.makedirs(os.path.dirname(optimized_results_path), exist_ok=True)

# # Load benchmark for CatBoost
# benchmark_df = pd.read_csv(benchmark_path)
# catboost_benchmark = benchmark_df[benchmark_df['Model'] == 'CatBoost'].iloc[0]

# # Load datasets
# df_train = pd.read_csv(train_path)
# df_val = pd.read_csv(val_path)
# df_test = pd.read_csv(test_path)

# # Separate features and target
# X_train = df_train.drop(['target', 'formula'], axis=1, errors='ignore')
# y_train = df_train['target']
# y_train_original = np.expm1(y_train)
# X_val = df_val.drop(['target', 'formula'], axis=1, errors='ignore')
# y_val = df_val['target']
# y_val_original = np.expm1(y_val)
# X_test = df_test.drop(['target', 'formula'], axis=1, errors='ignore')
# y_test = df_test['target']
# y_test_original = np.expm1(y_test)

# # Scale features with RobustScaler
# scaler = RobustScaler()
# X_train_scaled = scaler.fit_transform(X_train)
# X_val_scaled = scaler.transform(X_val)
# X_test_scaled = scaler.transform(X_test)

# # StratifiedKFold with 10 splits
# binned_y = pd.qcut(y_train, q=7, labels=False, duplicates='drop')
# kf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
# splits = list(kf.split(X_train, binned_y))

# # Evaluation function
# def evaluate_model(y_true, y_pred, scale='orig'):
#     if scale == 'orig':
#         y_true_eval = np.expm1(y_true)
#         y_pred_eval = np.expm1(y_pred)
#     else:
#         y_true_eval = y_true
#         y_pred_eval = y_pred
#     mae = mean_absolute_error(y_true_eval, y_pred_eval)
#     mse = mean_squared_error(y_true_eval, y_pred_eval)
#     rmse = np.sqrt(mse)
#     r2 = r2_score(y_true_eval, y_pred_eval)
#     return mae, mse, rmse, r2

# # Optimize CatBoost
# def optimize_catboost():
#     pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3)
#     study = optuna.create_study(direction='maximize', sampler=TPESampler(seed=42), pruner=pruner)
    
#     def objective(trial):
#         params = {
#             'learning_rate': trial.suggest_float('learning_rate', 0.0005, 0.001, log=True),
#             'depth': trial.suggest_int('depth', 3, 10),
#             'iterations': trial.suggest_int('iterations', 5000, 20000),
#             'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 3, 10),
#             'bagging_temperature': trial.suggest_float('bagging_temperature', 0, 1),
#             'random_strength': trial.suggest_float('random_strength', 1, 10),
#             'grow_policy': 'Lossguide',
#             'od_type': 'IncToDec',
#             'od_pval': 1e-2,
#             'random_seed': 42,
#             'loss_function': 'RMSE',
#             'verbose': 0,
#             'task_type': 'CPU',
#             'border_count': trial.suggest_int('border_count', 32, 128)
#         }
#         cv_r2s = []
#         for i, (train_idx, val_idx) in enumerate(splits):
#             X_tr = X_train.iloc[train_idx]
#             X_v = X_train.iloc[val_idx]
#             y_tr = y_train.iloc[train_idx]
#             y_v = y_train.iloc[val_idx]
#             scaler_fold = RobustScaler()
#             X_tr_scaled = scaler_fold.fit_transform(X_tr)
#             X_v_scaled = scaler_fold.transform(X_v)
#             train_pool = Pool(X_tr_scaled, y_tr)
#             val_pool = Pool(X_v_scaled, y_v)
#             model = CatBoostRegressor(**params)
#             model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=5000)
#             y_v_pred = model.predict(val_pool)
#             r2 = r2_score(y_v, y_v_pred)
#             cv_r2s.append(r2)
#             trial.report(r2, i)
#             if trial.should_prune():
#                 raise optuna.TrialPruned()
#         return np.mean(cv_r2s)
    
#     study.optimize(objective, n_trials=50)
#     return study.best_params

# print("Optimizing CatBoost...")
# best_params = optimize_catboost()
# best_params.update({
#     # 'iterations': 20000,
#     'grow_policy': 'Lossguide',
#     'od_type': 'IncToDec',
#     'od_pval': 1e-2,
#     'verbose': 0,
#     'random_seed': 42,
#     'task_type': 'CPU'
# })

# # Train initial Ridge model
# init_model = Ridge(alpha=5.0)
# init_model.fit(X_train_scaled, y_train)
# joblib.dump(init_model, 'init_model.pkl')

# # Continue training on combined train+val with init_model
# combined_X_scaled = np.vstack([X_train_scaled, X_val_scaled])
# combined_y = pd.concat([y_train, y_val])
# loaded_init_model = joblib.load('init_model.pkl')
# baseline_combined = loaded_init_model.predict(combined_X_scaled)
# baseline_test = loaded_init_model.predict(X_test_scaled)
# combined_pool = Pool(combined_X_scaled, combined_y, baseline=baseline_combined)
# test_pool = Pool(X_test_scaled, y_test, baseline=baseline_test)
# final_model = CatBoostRegressor(**best_params)
# final_model.fit(combined_pool, eval_set=test_pool, early_stopping_rounds=5000)
# joblib.dump(final_model, catboost_model_path, compress=3)

# # Feature importance for selection (optional: select top features)
# feature_importances = final_model.get_feature_importance()
# top_features = np.argsort(feature_importances)[-10:]  # Example: top 5
# print("Top features indices:", top_features)

# # Evaluate
# baseline_train = loaded_init_model.predict(X_train_scaled)
# baseline_val = loaded_init_model.predict(X_val_scaled)
# baseline_test = loaded_init_model.predict(X_test_scaled)
# y_train_pred = final_model.predict(X_train_scaled) + baseline_train
# y_val_pred = final_model.predict(X_val_scaled) + baseline_val
# y_test_pred = final_model.predict(X_test_scaled) + baseline_test

# train_mae_log, train_mse_log, train_rmse_log, train_r2_log = evaluate_model(y_train, y_train_pred, 'log')
# val_mae_log, val_mse_log, val_rmse_log, val_r2_log = evaluate_model(y_val, y_val_pred, 'log')
# test_mae_log, test_mse_log, test_rmse_log, test_r2_log = evaluate_model(y_test, y_test_pred, 'log')

# train_mae_orig, train_mse_orig, train_rmse_orig, train_r2_orig = evaluate_model(y_train, y_train_pred, 'orig')
# val_mae_orig, val_mse_orig, val_rmse_orig, val_r2_orig = evaluate_model(y_val, y_val_pred, 'orig')
# test_mae_orig, test_mse_orig, test_rmse_orig, test_r2_orig = evaluate_model(y_test, y_test_pred, 'orig')

# cv_r2 = cross_val_score(final_model, X_train_scaled, y_train, cv=7, scoring='r2').mean()

# overfitting_train_val = train_r2_orig - val_r2_orig
# overfitting_train_test = train_r2_orig - test_r2_orig
# print(f"CatBoost Overfitting Train-Val: {overfitting_train_val}, Train-Test: {overfitting_train_test}")

# results = {
#     'CV_R2_Mean': cv_r2,
#     'Train_R2_Log': train_r2_log,
#     'Train_RMSE_Log': train_rmse_log,
#     'Train_MAE_Log': train_mae_log,
#     'Val_R2_Log': val_r2_log,
#     'Val_RMSE_Log': val_rmse_log,
#     'Val_MAE_Log': val_mae_log,
#     'Test_R2_Log': test_r2_log,
#     'Test_RMSE_Log': test_rmse_log,
#     'Test_MAE_Log': test_mae_log,
#     'Train_R2_Orig': train_r2_orig,
#     'Train_RMSE_Orig': train_rmse_orig,
#     'Train_MAE_Orig': train_mae_orig,
#     'Val_R2_Orig': val_r2_orig,
#     'Val_RMSE_Orig': val_rmse_orig,
#     'Val_MAE_Orig': val_mae_orig,
#     'Test_R2_Orig': test_r2_orig,
#     'Test_RMSE_Orig': test_rmse_orig,
#     'Test_MAE_Orig': test_mae_orig,
#     'Overfitting_Train_Val': overfitting_train_val,
#     'Overfitting_Train_Test': overfitting_train_test
# }

# results_df = pd.DataFrame([results])
# results_df.to_csv(optimized_results_path, index=False)

# # Comparison with base
# comparison_df = pd.concat([pd.Series(catboost_benchmark), results_df.iloc[0]], axis=1, keys=['Base', 'Optimized'])

# # Generate Markdown report
# with open(comparison_report_path, 'w') as f:
#     f.write("# Comparison Report: Base vs Optimized CatBoost\n\n")
#     f.write(comparison_df.to_markdown())

# # Performance plots
# metrics = ['CV_R2_Mean', 'Test_R2_Orig', 'Test_MAE_Orig']
# fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 6*len(metrics)))
# for i, metric in enumerate(metrics):
#     sub_df = comparison_df.loc[metric].to_frame().T
#     sub_df.columns = ['Base', 'Optimized']
#     sub_df.plot(kind='bar', ax=axes[i])
#     axes[i].set_title(f'{metric}: Base vs Optimized')
#     axes[i].set_xticklabels(['CatBoost'], rotation=0)
#     axes[i].legend()

# plt.tight_layout()
# plt.savefig(plot_path)
# plt.close()
# File: D:\Hydride_Machine_learning_project\Machine_Model\src\optimize_catboost.py


# File: D:\Hydride_Machine_learning_project\Machine_Model\src\optimize_catboost.py


import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from catboost import CatBoostRegressor, Pool
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
import joblib
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Paths
benchmark_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\benchmarked_model\default_benchmark_results.csv"
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_test.csv"
optimized_results_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\optimized_optuna\catboost_optimized_results.csv"
comparison_report_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\comparison\catboost_comparison_report.md"
catboost_model_path = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna\catboost_model.pkl"
plot_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\optimization\catboost_performance_plots.png"
learning_curve_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\optimization\catboost_learning_curve.png"
optimized_models_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna"
os.makedirs(optimized_models_dir, exist_ok=True)
os.makedirs(os.path.dirname(optimized_results_path), exist_ok=True)
os.makedirs(os.path.dirname(learning_curve_path), exist_ok=True)

# Load benchmark for CatBoost
benchmark_df = pd.read_csv(benchmark_path)
catboost_benchmark = benchmark_df[benchmark_df['Model'] == 'CatBoost'].iloc[0]

# Load datasets
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

# Separate features and target
X_train = df_train.drop(['target', 'formula'], axis=1, errors='ignore')
y_train = df_train['target']
X_val = df_val.drop(['target', 'formula'], axis=1, errors='ignore')
y_val = df_val['target']
X_test = df_test.drop(['target', 'formula'], axis=1, errors='ignore')
y_test = df_test['target']

# Scale features with RobustScaler (better for outliers)
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)
joblib.dump(scaler, os.path.join(optimized_models_dir, 'scaler.pkl'))

# Combined train + val for final fitting
combined_X_scaled = np.vstack([X_train_scaled, X_val_scaled])
combined_y = pd.concat([y_train, y_val]).reset_index(drop=True)
combined_y_original = np.expm1(combined_y)
# Modified weights: double weight for capacities > 3
weights_combined = np.where(combined_y_original > 3, 2.0, 1.0)

# StratifiedKFold with 7 splits for better balance
binned_y = pd.qcut(y_train, q=7, labels=False, duplicates='drop')
kf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
splits = list(kf.split(X_train, binned_y))

# Evaluation function
def evaluate_model(y_true, y_pred, scale='orig'):
    if scale == 'orig':
        y_true_eval = np.expm1(y_true)
        y_pred_eval = np.expm1(y_pred)
    else:
        y_true_eval = y_true
        y_pred_eval = y_pred
    mae = mean_absolute_error(y_true_eval, y_pred_eval)
    mse = mean_squared_error(y_true_eval, y_pred_eval)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true_eval, y_pred_eval)
    return mae, mse, rmse, r2

# Optimize CatBoost without baseline
def optimize_catboost():
    pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3)
    study = optuna.create_study(direction='maximize', sampler=TPESampler(seed=42), pruner=pruner)
    
    def objective(trial):
        params = {
            'learning_rate': trial.suggest_float('learning_rate', 0.0001, 0.005, log=True),  # Wider range for LR
            'depth': trial.suggest_int('depth', 7, 25),  # Deeper trees possible
            'iterations': trial.suggest_int('iterations', 10000, 30000),  # Adjusted range
            'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10),  # Wider reg
            'bagging_temperature': trial.suggest_float('bagging_temperature', 0, 1),
            'random_strength': trial.suggest_float('random_strength', 0.5, 15),  # Wider
            'grow_policy': 'Lossguide',
            'max_leaves': trial.suggest_int('max_leaves', 16, 128),  # Add for Lossguide
            'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 1, 20),  # Add
            'od_type': 'IncToDec',
            'od_pval': 1e-2,
            'random_seed': 42,
            'loss_function': 'RMSE',
            'verbose': 0,
            'task_type': 'CPU',
            'border_count': trial.suggest_int('border_count', 32, 256)
        }
        cv_r2s = []
        for i, (train_idx, val_idx) in enumerate(splits):
            X_tr = X_train.iloc[train_idx]
            X_v = X_train.iloc[val_idx]
            y_tr = y_train.iloc[train_idx]
            y_v = y_train.iloc[val_idx]
            y_tr_original = np.expm1(y_tr)
            # Modified weights: double weight for capacities > 3
            weights_tr = np.where(y_tr_original > 3, 2.0, 1.0)
            scaler_fold = RobustScaler()
            X_tr_scaled = scaler_fold.fit_transform(X_tr)
            X_v_scaled = scaler_fold.transform(X_v)
            
            train_pool = Pool(X_tr_scaled, y_tr, weight=weights_tr)
            val_pool = Pool(X_v_scaled, y_v)
            model = CatBoostRegressor(**params)
            model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=5000)  # Increase for better stopping
            y_v_pred = model.predict(val_pool)
            r2 = r2_score(y_v, y_v_pred)  # Use R2 on log scale to avoid negative scores
            cv_r2s.append(r2)
            trial.report(r2, i)
            if trial.should_prune():
                raise optuna.TrialPruned()
        return np.mean(cv_r2s)
    
    study.optimize(objective, n_trials=300)  # More trials
    return study.best_params

print("Optimizing CatBoost...")
best_params = optimize_catboost()
best_params.update({
    'grow_policy': 'Lossguide',
    'od_type': 'IncToDec',
    'od_pval': 1e-2,
    'verbose': 0,
    'random_seed': 42,
    'task_type': 'CPU'
})

# Prepare pools without baseline
combined_pool = Pool(combined_X_scaled, combined_y, weight=weights_combined)
test_pool = Pool(X_test_scaled, y_test)
final_model = CatBoostRegressor(**best_params)
final_model.fit(combined_pool, eval_set=test_pool, early_stopping_rounds=5000)
joblib.dump(final_model, catboost_model_path, compress=3)

# Plot learning curve
evals_result = final_model.evals_result_
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(evals_result['learn']['RMSE'], label='Train RMSE (log scale)')
ax.plot(evals_result['validation']['RMSE'], label='Test RMSE (log scale)')
ax.set_xlabel('Iterations')
ax.set_ylabel('RMSE')
ax.set_title('CatBoost Learning Curve')
ax.legend()
plt.tight_layout()
plt.savefig(learning_curve_path)
plt.close()

# Feature importance for selection (optional: select top features)
feature_importances = final_model.get_feature_importance()
top_features = np.argsort(feature_importances)[-10:]  # Example: top 10
print("Top features indices:", top_features)

# Evaluate
y_train_pred = final_model.predict(X_train_scaled)
y_val_pred = final_model.predict(X_val_scaled)
y_test_pred = final_model.predict(X_test_scaled)

train_mae_log, train_mse_log, train_rmse_log, train_r2_log = evaluate_model(y_train, y_train_pred, 'log')
val_mae_log, val_mse_log, val_rmse_log, val_r2_log = evaluate_model(y_val, y_val_pred, 'log')
test_mae_log, test_mse_log, test_rmse_log, test_r2_log = evaluate_model(y_test, y_test_pred, 'log')

train_mae_orig, train_mse_orig, train_rmse_orig, train_r2_orig = evaluate_model(y_train, y_train_pred, 'orig')
val_mae_orig, val_mse_orig, val_rmse_orig, val_r2_orig = evaluate_model(y_val, y_val_pred, 'orig')
test_mae_orig, test_mse_orig, test_rmse_orig, test_r2_orig = evaluate_model(y_test, y_test_pred, 'orig')

# Compute CV R2 with weights for consistency (on log scale)
cv_r2s = []
for i, (train_idx, val_idx) in enumerate(splits):
    X_tr = X_train.iloc[train_idx]
    X_v = X_train.iloc[val_idx]
    y_tr = y_train.iloc[train_idx]
    y_v = y_train.iloc[val_idx]
    y_tr_original = np.expm1(y_tr)
    # Modified weights: double weight for capacities > 3
    weights_tr = np.where(y_tr_original > 3, 2.0, 1.0)
    scaler_fold = RobustScaler()
    X_tr_scaled = scaler_fold.fit_transform(X_tr)
    X_v_scaled = scaler_fold.transform(X_v)
    
    train_pool = Pool(X_tr_scaled, y_tr, weight=weights_tr)
    val_pool = Pool(X_v_scaled, y_v)
    model = CatBoostRegressor(**best_params)
    model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=5000)
    y_v_pred = model.predict(val_pool)
    r2 = r2_score(y_v, y_v_pred)  # Use R2 on log scale
    cv_r2s.append(r2)
cv_r2 = np.mean(cv_r2s)

overfitting_train_val = train_r2_orig - val_r2_orig
overfitting_train_test = train_r2_orig - test_r2_orig
print(f"CatBoost Overfitting Train-Val: {overfitting_train_val}, Train-Test: {overfitting_train_test}")

results = {
    'CV_R2_Mean': cv_r2,
    'Train_R2_Log': train_r2_log,
    'Train_RMSE_Log': train_rmse_log,
    'Train_MAE_Log': train_mae_log,
    'Val_R2_Log': val_r2_log,
    'Val_RMSE_Log': val_rmse_log,
    'Val_MAE_Log': val_mae_log,
    'Test_R2_Log': test_r2_log,
    'Test_RMSE_Log': test_rmse_log,
    'Test_MAE_Log': test_mae_log,
    'Train_R2_Orig': train_r2_orig,
    'Train_RMSE_Orig': train_rmse_orig,
    'Train_MAE_Orig': train_mae_orig,
    'Val_R2_Orig': val_r2_orig,
    'Val_RMSE_Orig': val_rmse_orig,
    'Val_MAE_Orig': val_mae_orig,
    'Test_R2_Orig': test_r2_orig,
    'Test_RMSE_Orig': test_rmse_orig,
    'Test_MAE_Orig': test_mae_orig,
    'Overfitting_Train_Val': overfitting_train_val,
    'Overfitting_Train_Test': overfitting_train_test
}

results_df = pd.DataFrame([results])
results_df.to_csv(optimized_results_path, index=False)

# Comparison with base
comparison_df = pd.concat([pd.Series(catboost_benchmark), results_df.iloc[0]], axis=1, keys=['Base', 'Optimized'])

# Generate Markdown report
with open(comparison_report_path, 'w') as f:
    f.write("# Comparison Report: Base vs Optimized CatBoost\n\n")
    f.write(comparison_df.to_markdown())

# Performance plots
metrics = ['CV_R2_Mean', 'Test_R2_Orig', 'Test_MAE_Orig']
fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 6*len(metrics)))
for i, metric in enumerate(metrics):
    sub_df = comparison_df.loc[metric].to_frame().T
    sub_df.columns = ['Base', 'Optimized']
    sub_df.plot(kind='bar', ax=axes[i])
    axes[i].set_title(f'{metric}: Base vs Optimized')
    axes[i].set_xticklabels(['Comparison'], rotation=0)
    axes[i].legend()

plt.tight_layout()
plt.savefig(plot_path)
plt.close()