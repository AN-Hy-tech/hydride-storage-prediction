# File: D:\Hydride_Machine_learning_project\Machine_Model\tests\test_catboost_smogn.py
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import optuna
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import os

# مسیرها
train_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\data\\processed\\Feature_Engineered_Augmented_train.csv"
val_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\data\\processed\\Feature_Engineered_Augmented_val.csv"
test_path =r"D:\\Hydride_Machine_learning_project\\Machine_Model\\data\\processed\\Feature_Engineered_Augmented_test.csv"
output_params_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\reports\\catboost_smogn_test\\catboost_smogn_test_params.csv"
output_model_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\models\\catboost_smogn_test\\catboost_smogn_test_model.pkl"
results_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\reports\\catboost_eng_aug_results\\catboost_smogn_test_results.csv"
shap_plot_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\reports\\figures\\data_eng_aug_analysis\\Model Results\\shap_summary_test.png"
learning_curve_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\reports\\figures\\data_eng_aug_analysis\\Model Results\\catboost_learning_curve_test.png"

# ایجاد فولدر برای خروجی‌ها
os.makedirs(os.path.dirname(results_path), exist_ok=True)
os.makedirs(os.path.dirname(shap_plot_path), exist_ok=True)

# خواندن دیتاست‌ها
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded train data with shape: {df_train.shape}")
print(f"Loaded val data with shape: {df_val.shape}")
print(f"Loaded test data with shape: {df_test.shape}")

# حذف ستون Composition
df_train = df_train.drop(['Composition'], axis=1, errors='ignore')
df_val = df_val.drop(['Composition'], axis=1, errors='ignore')
df_test = df_test.drop(['Composition'], axis=1, errors='ignore')

# جدا کردن ویژگی‌ها و تارگت
X_train = df_train.drop(['log_H2_W% (max)', 'H2_W% (max)'], axis=1, errors='ignore')
y_train = df_train['log_H2_W% (max)']
y_train_original = np.expm1(y_train)
X_val = df_val.drop(['log_H2_W% (max)','H2_W% (max)'], axis=1, errors='ignore')
y_val = df_val['log_H2_W% (max)']
y_val_original = np.expm1(y_val)
X_test = df_test.drop(['log_H2_W% (max)','H2_W% (max)'], axis=1, errors='ignore')
y_test = df_test['log_H2_W% (max)']
y_test_original = np.expm1(y_test)


# Corrolation Matrix for pair features
corr_matrix = X_train.corr().abs()
corr_with_target = X_train.corrwith(y_train).abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = []
for i in range(len(upper.columns)):
    for j in range(i + 1, len(upper.columns)):
        if upper.iloc[i, j] > 0.85:
            feature_i = upper.columns[i]
            feature_j = upper.columns[j]
            # نگه‌داشتن ویژگی با همبستگی بیشتر با تارگت
            if corr_with_target[feature_i] > corr_with_target[feature_j]:
                to_drop.append(feature_j)
            else:
                to_drop.append(feature_i)
to_drop = list(set(to_drop))  # حذف تکراری‌ها
print(f"Features with high correlation (> 0.85) to drop: {to_drop}")

X_train = X_train.drop(to_drop, axis=1)
X_val = X_val.drop(to_drop, axis=1)
X_test = X_test.drop(to_drop, axis=1)


# اسکیل کردن با Standardization
scaler = MinMaxScaler()
X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns).reset_index(drop=True)
X_val_scaled = pd.DataFrame(scaler.transform(X_val), columns=X_val.columns).reset_index(drop=True)
X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns).reset_index(drop=True)


# تابع ارزیابی
def evaluate_model(y_true, y_pred, y_original, is_log=True):
    if is_log:
        y_true_orig = np.expm1(y_true)
        y_pred_orig = np.expm1(y_pred)
    else:
        y_true_orig = y_true
        y_pred_orig = y_pred
    mae = mean_absolute_error(y_true_orig, y_pred_orig)
    mse = mean_squared_error(y_true_orig, y_pred_orig)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true_orig, y_pred_orig)
    return mae, mse, rmse, r2

# تابع هدف برای بهینه‌سازی CatBoost
def objective(trial):
    params = {
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1),
        'depth': trial.suggest_int('depth', 3, 10),
        'iterations': trial.suggest_int('iterations', 500, 1000),
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 3, 8),
        'bagging_temperature': trial.suggest_float('bagging_temperature', 0.5, 1.0),
        'random_strength': trial.suggest_float('random_strength', 10, 30),
        'early_stopping_rounds': trial.suggest_int('early_stopping_rounds', 50, 200),
        'loss_function': 'MAE',
        'random_seed': 42,
        'verbose': 0
    }
    model = CatBoostRegressor(**params)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=kf, scoring='r2', n_jobs=-1)
    if cv_scores.mean() < 0:
        print(f"Warning: Negative R2 detected in trial {trial.number}: {cv_scores.mean():.4f}")
    return cv_scores.mean()

# بهینه‌سازی
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)
best_params = study.best_params
best_score = study.best_value

print(f"Best parameters: {best_params}")
print(f"Best Cross-Validation R²: {best_score:.4f}")

# آموزش مدل با پارامترهای بهینه
best_model = CatBoostRegressor(**best_params, random_seed=42, verbose=0)
best_model.fit(X_train_scaled, y_train, eval_set=(X_val_scaled, y_val), early_stopping_rounds=best_params['early_stopping_rounds'], verbose=0)

# انتخاب ویژگی‌ها با اهمیت > 3.0
importance_threshold = 2.0
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': best_model.get_feature_importance()
})
selected_features = feature_importance[feature_importance['importance'] > importance_threshold]['feature'].tolist()
X_train_selected = X_train_scaled[selected_features]
X_val_selected = X_val_scaled[selected_features]
X_test_selected = X_test_scaled[selected_features]

print(f"Selected features (importance > 3.0): {selected_features}")

# آموزش دوباره مدل با ویژگی‌های انتخاب‌شده
best_model.fit(X_train_selected, y_train, eval_set=(X_val_selected, y_val), early_stopping_rounds=best_params['early_stopping_rounds'], verbose=0)

# پیش‌بینی و ارزیابی
y_train_pred_log = best_model.predict(X_train_selected)
train_mse_log = mean_squared_error(y_train, y_train_pred_log)
train_mae_log = mean_absolute_error(y_train, y_train_pred_log)
train_r2_log = r2_score(y_train, y_train_pred_log)

y_val_pred_log = best_model.predict(X_val_selected)
val_mse_log = mean_squared_error(y_val, y_val_pred_log)
val_mae_log = mean_absolute_error(y_val, y_val_pred_log)
val_r2_log = r2_score(y_val, y_val_pred_log)

y_test_pred_log = best_model.predict(X_test_selected)
test_mse_log = mean_squared_error(y_test, y_test_pred_log)
test_mae_log = mean_absolute_error(y_test, y_test_pred_log)
test_r2_log = r2_score(y_test, y_test_pred_log)

y_train_orig = np.expm1(y_train)
y_train_pred_orig = np.expm1(y_train_pred_log)
train_mse_orig = mean_squared_error(y_train_orig, y_train_pred_orig)
train_mae_orig = mean_absolute_error(y_train_orig, y_train_pred_orig)
train_r2_orig = r2_score(y_train_orig, y_train_pred_orig)

y_val_orig = np.expm1(y_val)
y_val_pred_orig = np.expm1(y_val_pred_log)
val_mse_orig = mean_squared_error(y_val_orig, y_val_pred_orig)
val_mae_orig = mean_absolute_error(y_val_orig, y_val_pred_orig)
val_r2_orig = r2_score(y_val_orig, y_val_pred_orig)

y_test_orig = np.expm1(y_test)
y_test_pred_orig = np.expm1(y_test_pred_log)
test_mse_orig = mean_squared_error(y_test_orig, y_test_pred_orig)
test_mae_orig = mean_absolute_error(y_test_orig, y_test_pred_orig)
test_r2_orig = r2_score(y_test_orig, y_test_pred_orig)

print(f"Train (log scale) - MSE: {train_mse_log:.4f}, MAE: {train_mae_log:.4f}, R²: {train_r2_log:.4f}")
print(f"Validation (log scale) - MSE: {val_mse_log:.4f}, MAE: {val_mae_log:.4f}, R²: {val_r2_log:.4f}")
print(f"Test (log scale) - MSE: {test_mse_log:.4f}, MAE: {test_mae_log:.4f}, R²: {test_r2_log:.4f}")
print(f"Train (original scale) - MSE: {train_mse_orig:.4f}, MAE: {train_mae_orig:.4f}, R²: {train_r2_orig:.4f}")
print(f"Validation (original scale) - MSE: {val_mse_orig:.4f}, MAE: {val_mae_orig:.4f}, R²: {val_r2_orig:.4f}")
print(f"Test (original scale) - MSE: {test_mse_orig:.4f}, MAE: {test_mae_orig:.4f}, R²: {test_r2_orig:.4f}")


# Feature statistics
# feature_stats = model.calc_feature_statistics(data=X_test, target=y_test_original,
#                                                   feature=X_train.columns.tolist(), plot=False) 



# SHAP Analysis
explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_val_selected)
shap.summary_plot(shap_values, X_val_selected, feature_names=selected_features)
plt.savefig(shap_plot_path)
plt.close()
print(f"SHAP summary plot saved to {shap_plot_path}")

# Learning Curves
from sklearn.model_selection import learning_curve
train_sizes, train_scores, val_scores = learning_curve(
    best_model, X_train_selected, y_train, cv=5, scoring='r2', n_jobs=-1
)
plt.plot(train_sizes, train_scores.mean(axis=1), label='Train R²')
plt.plot(train_sizes, val_scores.mean(axis=1), label='Validation R²')
plt.xlabel('Training Size')
plt.ylabel('R²')
plt.legend()
plt.savefig(learning_curve_path)
plt.close()
print(f"Learning curve plot saved to {learning_curve_path}")

# ذخیره نتایج
results_df = pd.DataFrame({
    'Cross-Validation R² (log scale)': [best_score],
    'Train R² (log scale)': [train_r2_log],
    'Train MSE (log scale)': [train_mse_log],
    'Train MAE (log scale)': [train_mae_log],
    'Validation R² (log scale)': [val_r2_log],
    'Validation MSE (log scale)': [val_mse_log],
    'Validation MAE (log scale)': [val_mae_log],
    'Test R² (log scale)': [test_r2_log],
    'Test MSE (log scale)': [test_mse_log],
    'Test MAE (log scale)': [test_mae_log],
    'Train R² (original scale)': [train_r2_orig],
    'Train MSE (original scale)': [train_mse_orig],
    'Train MAE (original scale)': [train_mae_orig],
    'Validation R² (original scale)': [val_r2_orig],
    'Validation MSE (original scale)': [val_mse_orig],
    'Validation MAE (original scale)': [val_mae_orig],
    'Test R² (original scale)': [test_r2_orig],
    'Test MSE (original scale)': [test_mse_orig],
    'Test MAE (original scale)': [test_mae_orig],
    'Feature Importance': [dict(zip(selected_features, best_model.get_feature_importance()))]
})
results_df.to_csv(results_path, index=False)
print(f"Model results saved to {results_path}")

# ذخیره مدل
# joblib.dump(best_model, output_model_path)
# print(f"Model saved to {output_model_path}")

# ذخیره پارامترها
# best_params_df = pd.DataFrame([best_params | {'best_r2': best_score}])
# best_params_df('utilising catboost_smogn_test_params.csv', index=False)
# print(f"Optimized parameters saved to {output_params_path}")