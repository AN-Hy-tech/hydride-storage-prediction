# File: D:\Hydride_Machine_learning_project\Machine_Model\src\optimize_and_stack_models.py
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import ExtraTreesRegressor, StackingRegressor, RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor
from sklearn.linear_model import Ridge
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.base import clone
from sklearn.pipeline import Pipeline
import warnings
from scipy.stats import ttest_rel
warnings.filterwarnings("ignore", category=UserWarning)

# Paths
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_test.csv"
optimized_results_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\optimized_optuna\optimized_models_results.csv"
stacking_results_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\optimized_optuna\stacking_results.csv"
comparison_report_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\comparison\comparison_report.md"
stacking_model_path = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_stacking\stacking_model.pkl"
plot_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\optimization\performance_plots.png"
optimized_models_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna"
os.makedirs(optimized_models_dir, exist_ok=True)
os.makedirs(os.path.dirname(optimized_results_path), exist_ok=True)

top_models = ['RandomForest', 'ExtraTrees', 'CatBoost', 'XGBoost', 'GradientBoosting']
print(f"Top 5 models for optimization: {top_models}")

# Load datasets
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded train data with shape: {df_train.shape}")
print(f"Loaded val data with shape: {df_val.shape}")
print(f"Loaded test data with shape: {df_test.shape}")

# Separate features and target
X_train = df_train.drop(['target', 'formula'], axis=1, errors='ignore')
y_train = df_train['target']
y_train_original = np.expm1(y_train)
X_val = df_val.drop(['target', 'formula'], axis=1, errors='ignore')
y_val = df_val['target']
y_val_original = np.expm1(y_val)
X_test = df_test.drop(['target', 'formula'], axis=1, errors='ignore')
y_test = df_test['target']
y_test_original = np.expm1(y_test)

# Scale features with RobustScaler
scaler = RobustScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# StratifiedKFold
binned_y = pd.qcut(y_train, q=5, labels=False, duplicates='drop')
kf = StratifiedKFold(n_splits=7, shuffle=True, random_state=42)
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

def optimize_model(model_name):
    pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10, interval_steps=3)
    study = optuna.create_study(direction='maximize', sampler=TPESampler(seed=42), pruner=pruner)
    
    if model_name == 'RandomForest':
        def objective(trial):
            params = {
                'max_depth': trial.suggest_int('max_depth', 2, 10),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 20),
                'max_features': trial.suggest_float('max_features', 0.5, 1.0),
                'random_state': 42,
                'n_jobs': -1,
                "oob_score": False,
            }
            max_estimators = trial.suggest_int('n_estimators', 100, 1000)
            cv_scores = []
            for i, (train_idx, val_idx) in enumerate(splits):
                X_tr = X_train.iloc[train_idx]
                X_v = X_train.iloc[val_idx]
                y_tr = y_train.iloc[train_idx]
                y_v = y_train.iloc[val_idx]
                scaler_fold = RobustScaler()
                X_tr_scaled = scaler_fold.fit_transform(X_tr)
                X_v_scaled = scaler_fold.transform(X_v)
                rf = RandomForestRegressor(**params, warm_start=True, n_estimators=1)
                min_val_error = float('inf')
                error_going_up = 0
                for n in range(1, max_estimators + 1):
                    rf.n_estimators = n
                    rf.fit(X_tr_scaled, y_tr)
                    y_v_pred = rf.predict(X_v_scaled)
                    val_error = mean_squared_error(y_v, y_v_pred)
                    if val_error < min_val_error:
                        min_val_error = val_error
                        error_going_up = 0
                    else:
                        error_going_up += 1
                        if error_going_up >= 10:
                            break
                score = r2_score(y_v, y_v_pred)
                cv_scores.append(score)
                trial.report(score, i)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            return np.mean(cv_scores)
        study.optimize(objective, n_trials=100)
        
    elif model_name == 'ExtraTrees':
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                'max_depth': trial.suggest_int('max_depth', 2, 10),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
                'max_features': trial.suggest_float('max_features', 0.5, 1.0),
                'random_state': 42,
                'n_jobs': -1,
                "criterion": "squared_error"
            }
            cv_scores = []
            for i, (train_idx, val_idx) in enumerate(splits):
                X_tr = X_train.iloc[train_idx]
                X_v = X_train.iloc[val_idx]
                y_tr = y_train.iloc[train_idx]
                y_v = y_train.iloc[val_idx]
                scaler_fold = RobustScaler()
                X_tr_scaled = scaler_fold.fit_transform(X_tr)
                X_v_scaled = scaler_fold.transform(X_v)
                model = ExtraTreesRegressor(**params)
                model.fit(X_tr_scaled, y_tr)
                y_v_pred = model.predict(X_v_scaled)
                score = r2_score(y_v, y_v_pred)
                cv_scores.append(score)
                trial.report(score, i)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            return np.mean(cv_scores)
        study.optimize(objective, n_trials=100)
        
    elif model_name == 'CatBoost':
        def objective(trial):
            params = {
                'learning_rate': trial.suggest_float('learning_rate', 0.0001, 0.1, log=True),
                'depth': trial.suggest_int('depth', 4, 12),
                'iterations': trial.suggest_int('iterations', 1000, 15000),
                'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 15),
                'bagging_temperature': trial.suggest_float('bagging_temperature', 0.0, 1.0),
                'random_strength': trial.suggest_float('random_strength', 1, 10),
                'random_seed': 42,
                'loss_function': 'RMSE',
                'verbose': 0,
                'early_stopping_rounds': trial.suggest_int('early_stopping_rounds', 500, 1000),
            }
            cv_scores = []
            for i, (train_idx, val_idx) in enumerate(splits):
                X_tr = X_train.iloc[train_idx]
                X_v = X_train.iloc[val_idx]
                y_tr = y_train.iloc[train_idx]
                y_v = y_train.iloc[val_idx]
                scaler_fold = RobustScaler()
                X_tr_scaled = scaler_fold.fit_transform(X_tr)
                X_v_scaled = scaler_fold.transform(X_v)
                model = CatBoostRegressor(**params)
                model.fit(X_tr_scaled, y_tr, eval_set=(X_v_scaled, y_v))
                y_v_pred = model.predict(X_v_scaled)
                score = r2_score(y_v, y_v_pred)
                cv_scores.append(score)
                trial.report(score, i)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            return np.mean(cv_scores)
        study.optimize(objective, n_trials=50)
        
    elif model_name == 'XGBoost':
        def objective(trial):
            params = {
                "objective": "reg:squarederror",
                'learning_rate': trial.suggest_float('learning_rate', 0.0001, 0.2, log=True),
                'max_depth': trial.suggest_int('max_depth', 4, 10),
                'n_estimators': trial.suggest_int('n_estimators', 1000, 15000),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-4, 1.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-4, 1.0, log=True),
                'random_state': 42,
                'n_jobs': -1
            }
            cv_scores = []
            for i, (train_idx, val_idx) in enumerate(splits):
                X_tr = X_train.iloc[train_idx]
                X_v = X_train.iloc[val_idx]
                y_tr = y_train.iloc[train_idx]
                y_v = y_train.iloc[val_idx]
                scaler_fold = RobustScaler()
                X_tr_scaled = scaler_fold.fit_transform(X_tr)
                X_v_scaled = scaler_fold.transform(X_v)
                model = XGBRegressor(**params, early_stopping_rounds=1000, eval_metric='rmse')
                model.fit(X_tr_scaled, y_tr, eval_set=[(X_v_scaled, y_v)], verbose=False)
                y_v_pred = model.predict(X_v_scaled)
                score = r2_score(y_v, y_v_pred)
                cv_scores.append(score)
                trial.report(score, i)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            return np.mean(cv_scores)
        study.optimize(objective, n_trials=100)
        
    elif model_name == 'GradientBoosting':
        def objective(trial):
            params = {
                'learning_rate': trial.suggest_float('learning_rate', 0.0001, 0.2, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'n_estimators': trial.suggest_int('n_estimators', 1000, 15000),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': None,
                'random_state': 42,
                'n_iter_no_change': trial.suggest_int('n_iter_no_change', 500, 1000),
                'validation_fraction': 0.1,
                'tol': 0.0001,
                "loss": "squared_error",
                "criterion": "friedman_mse",
            }
            cv_scores = []
            for i, (train_idx, val_idx) in enumerate(splits):
                X_tr = X_train.iloc[train_idx]
                X_v = X_train.iloc[val_idx]
                y_tr = y_train.iloc[train_idx]
                y_v = y_train.iloc[val_idx]
                scaler_fold = RobustScaler()
                X_tr_scaled = scaler_fold.fit_transform(X_tr)
                X_v_scaled = scaler_fold.transform(X_v)
                model = GradientBoostingRegressor(**params)
                model.fit(X_tr_scaled, y_tr)
                y_v_pred = model.predict(X_v_scaled)
                score = r2_score(y_v, y_v_pred)
                cv_scores.append(score)
                trial.report(score, i)
                if trial.should_prune():
                    raise optuna.TrialPruned()
            return np.mean(cv_scores)
        study.optimize(objective, n_trials=100)
    
    return study.best_params

# Function to get base model with params
def get_base_model(model_name, params):
    if model_name == 'RandomForest':
        return RandomForestRegressor(**params, random_state=42, n_jobs=-1)
    elif model_name == 'ExtraTrees':
        return ExtraTreesRegressor(**params, random_state=42, n_jobs=-1)
    elif model_name == 'CatBoost':
        return CatBoostRegressor(**params, random_seed=42, verbose=0)
    elif model_name == 'XGBoost':
        return XGBRegressor(**params, random_state=42, n_jobs=-1)
    elif model_name == 'GradientBoosting':
        return GradientBoostingRegressor(**params, random_state=42)

# Train base models with default params
base_models = {}
base_results = {}
all_test_preds_base = {}
for model_name in top_models:
    print(f"Training base {model_name}...")
    base_params = {}  # Defaults
    if model_name == 'CatBoost':
        base_params['loss_function'] = 'RMSE'
    elif model_name == 'XGBoost':
        base_params['objective'] = 'reg:squarederror'
    model = get_base_model(model_name, base_params)
    model.fit(X_train_scaled, y_train)
    y_train_pred = model.predict(X_train_scaled)
    y_val_pred = model.predict(X_val_scaled)
    y_test_pred = model.predict(X_test_scaled)
    all_test_preds_base[model_name] = y_test_pred
    base_models[model_name] = model
    
    train_mae_log, train_mse_log, train_rmse_log, train_r2_log = evaluate_model(y_train, y_train_pred, 'log')
    val_mae_log, val_mse_log, val_rmse_log, val_r2_log = evaluate_model(y_val, y_val_pred, 'log')
    test_mae_log, test_mse_log, test_rmse_log, test_r2_log = evaluate_model(y_test, y_test_pred, 'log')
    
    train_mae_orig, train_mse_orig, train_rmse_orig, train_r2_orig = evaluate_model(y_train, y_train_pred, 'orig')
    val_mae_orig, val_mse_orig, val_rmse_orig, val_r2_orig = evaluate_model(y_val, y_val_pred, 'orig')
    test_mae_orig, test_mse_orig, test_rmse_orig, test_r2_orig = evaluate_model(y_test, y_test_pred, 'orig')
    
    cv_r2 = cross_val_score(model, X_train_scaled, y_train, cv=splits, scoring='r2').mean()
    
    base_results[model_name] = {
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
        'Test_MAE_Orig': test_mae_orig
    }

# Optimize and train models
optimized_models = {}
optimized_results = {}
best_params_dict = {}
all_test_preds_opt = {}

for model_name in top_models:
    print(f"Optimizing {model_name}...")
    best_params = optimize_model(model_name)
    best_params_dict[model_name] = best_params
    
    model = get_base_model(model_name, best_params)
    
    model.fit(X_train_scaled, y_train)
    joblib.dump(model, os.path.join(optimized_models_dir, f"{model_name}_optimized.pkl"), compress=3)
    optimized_models[model_name] = model
    
    y_train_pred = model.predict(X_train_scaled)
    y_val_pred = model.predict(X_val_scaled)
    y_test_pred = model.predict(X_test_scaled)
    all_test_preds_opt[model_name] = y_test_pred
    
    train_mae_log, train_mse_log, train_rmse_log, train_r2_log = evaluate_model(y_train, y_train_pred, 'log')
    val_mae_log, val_mse_log, val_rmse_log, val_r2_log = evaluate_model(y_val, y_val_pred, 'log')
    test_mae_log, test_mse_log, test_rmse_log, test_r2_log = evaluate_model(y_test, y_test_pred, 'log')
    
    train_mae_orig, train_mse_orig, train_rmse_orig, train_r2_orig = evaluate_model(y_train, y_train_pred, 'orig')
    val_mae_orig, val_mse_orig, val_rmse_orig, val_r2_orig = evaluate_model(y_val, y_val_pred, 'orig')
    test_mae_orig, test_mse_orig, test_rmse_orig, test_r2_orig = evaluate_model(y_test, y_test_pred, 'orig')
    
    cv_r2 = cross_val_score(model, X_train_scaled, y_train, cv=splits, scoring='r2').mean()
    
    optimized_results[model_name] = {
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
        'Test_MAE_Orig': test_mae_orig
    }

# Save optimized results
optimized_df = pd.DataFrame.from_dict(optimized_results, orient='index')
optimized_df.to_csv(optimized_results_path)

# Statistical comparison base vs optimized (on test set, orig scale)
stat_results = []
for model_name in top_models:
    base_pred = np.expm1(all_test_preds_base[model_name])
    opt_pred = np.expm1(all_test_preds_opt[model_name])
    base_sq_err = (base_pred - y_test_original) ** 2
    opt_sq_err = (opt_pred - y_test_original) ** 2
    t_stat, p_val = ttest_rel(base_sq_err, opt_sq_err)
    stat_results.append({'Model': model_name, 'p_value': p_val})

stat_df = pd.DataFrame(stat_results)
stat_df.to_csv(os.path.join(os.path.dirname(optimized_results_path), 'stat_comparison.csv'), index=False)

# Generate OOF meta features for ridge optimization
oof_meta_train = np.zeros((X_train.shape[0], len(top_models)))
for j, model_name in enumerate(top_models):
    best_params = best_params_dict[model_name]
    base_model = get_base_model(model_name, best_params)
    for train_idx, val_idx in splits:
        X_tr = X_train.iloc[train_idx]
        X_v = X_train.iloc[val_idx]
        y_tr = y_train.iloc[train_idx]
        scaler_fold = RobustScaler()
        X_tr_scaled = scaler_fold.fit_transform(X_tr)
        X_v_scaled = scaler_fold.transform(X_v)
        model_fold = clone(base_model)
        model_fold.fit(X_tr_scaled, y_tr)
        oof_meta_train[val_idx, j] = model_fold.predict(X_v_scaled)

# Model diversity validation (correlation of predictions)
predictions_train = {name: model.predict(X_train_scaled) for name, model in optimized_models.items()}
corr_matrix = pd.DataFrame(predictions_train).corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
plt.title('Model Prediction Correlation (Diversity Check)')
plt.savefig(os.path.join(os.path.dirname(plot_path), 'model_diversity_correlation.png'))
plt.close()

# Optimize Ridge meta-model
print("Optimizing Ridge meta-model...")
def optimize_ridge(X_meta_train, y_train):
    def objective(trial):
        params = {
            # 'max_iter': trial.suggest_int('max_iter', 100, 1000, log=True),
            'alpha': trial.suggest_float('alpha', 1e-3, 1e2, log=True),
            # 'fit_intercept': True,
            'solver': trial.suggest_categorical('solver', ['auto', 'svd', 'cholesky', 'lsqr', 'sag']),
        }
        cv_scores = cross_val_score(Ridge(**params), X_meta_train, y_train, cv=splits, scoring='r2', n_jobs=-1).mean()
        return cv_scores
    
    study = optuna.create_study(direction='maximize', sampler=TPESampler(seed=42))
    study.optimize(objective, n_trials=100)
    
    return study.best_params

best_ridge_params = optimize_ridge(oof_meta_train, y_train)

# Stacking model with optimized Ridge
estimators = []
for name in top_models:
    best_params = best_params_dict[name]
    base_model = get_base_model(name, best_params)
    pipe = Pipeline([('scaler', RobustScaler()), ('reg', base_model)])
    estimators.append((name, pipe))
stacking_model = StackingRegressor(estimators=estimators, final_estimator=Ridge(**best_ridge_params), cv=7, n_jobs=-1)
stacking_model.fit(X_train, y_train)
joblib.dump(stacking_model, stacking_model_path, compress=3)

# Evaluate Stacking
y_train_pred = stacking_model.predict(X_train)
y_val_pred = stacking_model.predict(X_val)
y_test_pred = stacking_model.predict(X_test)

train_mae_log, train_mse_log, train_rmse_log, train_r2_log = evaluate_model(y_train, y_train_pred, 'log')
val_mae_log, val_mse_log, val_rmse_log, val_r2_log = evaluate_model(y_val, y_val_pred, 'log')
test_mae_log, test_mse_log, test_rmse_log, test_r2_log = evaluate_model(y_test, y_test_pred, 'log')

train_mae_orig, train_mse_orig, train_rmse_orig, train_r2_orig = evaluate_model(y_train, y_train_pred, 'orig')
val_mae_orig, val_mse_orig, val_rmse_orig, val_r2_orig = evaluate_model(y_val, y_val_pred, 'orig')
test_mae_orig, test_mse_orig, test_rmse_orig, test_r2_orig = evaluate_model(y_test, y_test_pred, 'orig')

cv_r2 = cross_val_score(stacking_model, X_train, y_train, cv=5, scoring='r2').mean()

overfitting_train_val = train_r2_orig - val_r2_orig
overfitting_train_test = train_r2_orig - test_r2_orig
print(f"Stacking Overfitting Train-Val: {overfitting_train_val}, Train-Test: {overfitting_train_test}")

stacking_results = {
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

stacking_df = pd.DataFrame([stacking_results])
stacking_df.to_csv(stacking_results_path, index=False)

# Comparison with base
base_df = pd.DataFrame.from_dict(base_results, orient='index')
comparison_df = pd.concat([base_df, optimized_df], axis=1, keys=['Base', 'Optimized'])

# Generate Markdown report
with open(comparison_report_path, 'w') as f:
    f.write("# Comparison Report: Base vs Optimized Models\n\n")
    f.write(comparison_df.to_markdown())
    f.write("\n\n## Stacking Results\n")
    f.write(stacking_df.to_markdown())
    f.write("\n\n## Statistical Comparisons\n")
    f.write(stat_df.to_markdown())

# Performance plots
metrics = ['CV_R2_Mean', 'Test_R2_Orig', 'Test_MAE_Orig']
fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 6*len(metrics)))
for i, metric in enumerate(metrics):
    sub_df = comparison_df[[('Base', metric), ('Optimized', metric)]].copy()
    sub_df.columns = ['Base', 'Optimized']
    sub_df.plot(kind='bar', ax=axes[i])
    axes[i].set_title(f'{metric}: Base vs Optimized')
    axes[i].set_xticklabels(sub_df.index, rotation=45, ha='right')
    axes[i].legend()

plt.tight_layout()
plt.savefig(plot_path)
plt.close()