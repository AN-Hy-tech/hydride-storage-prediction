# File: D:\Hydride_Machine_learning_project\Machine_Model\src\random_forest_with_smogn.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import optuna
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import os
from sklearn.model_selection import learning_curve

# مسیرها
train_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\data\\processed\\Feature_Engineered_Augmented_train.csv"
test_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\data\\processed\\Feature_Engineered_Augmented_test.csv"
output_params_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\reports\\random_forest_analysis\\random_forest_model_optimized.csv"
output_model_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\models\\random_forest_model.pkl"
results_path = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\reports\\random_forest_analysis\\random_forest_results.csv"
figures_dir = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\reports\\figures\\random_forest_analysis\\Model Results\\random_forest_analysis"

# ایجاد فولدر برای خروجی‌ها
os.makedirs(figures_dir, exist_ok=True)
os.makedirs(results_path, exist_ok=True)

# خواندن دیتاست‌ها
df_train = pd.read_csv(train_path)
df_test = pd.read_csv(test_path)

print(f"Loaded train data with shape: {df_train.shape}")
print(f"Loaded test data with shape: {df_test.shape}")

formula_train = df_train['Composition']
formula_test = df_test['Composition']


df_train = df_train.drop(['Composition'], axis=1, errors='ignore')
df_test = df_test.drop(['Composition'], axis=1, errors='ignore')


# جدا کردن ویژگی‌ها و تارگت
X_train = df_train.drop(['log_H2_W% (max)', 'H2_W% (max)'], axis=1, errors='ignore')
y_train = df_train['log_H2_W% (max)']
y_train_original = np.expm1(y_train)
X_test = df_test.drop(['log_H2_W% (max)','H2_W% (max)'], axis=1, errors='ignore')
y_test = df_test['log_H2_W% (max)']
y_test_original = np.expm1(y_test)

# فیلتر همبستگی ویژگی‌ها
corr_matrix = X_train.corr().abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.85)]
print(f"Features with high correlation (> 0.85) to drop: {to_drop}")
X_train = X_train.drop(to_drop, axis=1)
X_test = X_test.drop(to_drop, axis=1)
print(f"Features after the correlation filtering (trainset): {X_train.shape}")
print(f"Features after the correlation filtering (testset): {X_test.shape}")

# اسکیل کردن با StandardScaler
scaler = MinMaxScaler()
X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns).reset_index(drop=True)
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
    r2 = r2_score(y_true_orig, y_pred_orig)
    return mae, mse, r2

def calculate_overfitting(r2_train, r2_test):
    return r2_train - r2_test



def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 4, 8),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
        'max_features': trial.suggest_float('max_features', 0.4, 0.7),
        'criterion': 'absolute_error',
        'random_state': 42,
        'oob_score' : True
    }
    
    model = RandomForestRegressor(**params)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=kf, scoring='r2', n_jobs=-1)
    if cv_scores.mean() < 0:
        print(f"Warning: Negative R² detected in trial {trial.number}: {cv_scores.mean():.4f}")
    return cv_scores.mean()

# بهینه‌سازی
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=2)
best_params = study.best_params
best_score = study.best_value

print(f"Best parameters: {best_params}")
print(f"Best Cross-Validation R²: {best_score:.4f}")

import time
# آموزش مدل با پارامترهای بهینه
best_model = RandomForestRegressor(**best_params, random_state=42, )
start_time = time.time()
best_model.fit(X_train_scaled, y_train)
fit_time = time.time() - start_time

# انتخاب ویژگی‌ها با اهمیت > 0.3
importance_threshold = 4.0
feature_importance = pd.DataFrame({
    'feature': X_train.columns,
    'importance': best_model.feature_importances_ * 100
})
selected_features = feature_importance[feature_importance['importance'] > importance_threshold]['feature'].tolist()
X_train_selected = X_train_scaled[selected_features]
X_test_selected = X_test_scaled[selected_features]

print(f"Selected features (importance > 3.0): {selected_features}")

# آموزش دوباره مدل با ویژگی‌های انتخاب‌شده
start_time = time.time()
best_model.fit(X_train_selected, y_train)
fit_time = time.time() - start_time

kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_r2_log = cross_val_score(best_model, X_test_selected, y_test, cv=kf, scoring='r2')
cv_mse_log = -cross_val_score(best_model, X_test_selected, y_test, cv=kf, scoring='neg_mean_squared_error')
cv_mae_log = -cross_val_score(best_model, X_test_selected, y_test, cv=kf, scoring='neg_mean_absolute_error')
print(f"Cross-Validation (log scale) - R²: {cv_r2_log.mean():.4f} (± {cv_r2_log.std() * 2:.4f})")
print(f"Cross-Validation (log scale) - MSE: {cv_mse_log.mean():.4f} (± {cv_mse_log.std() * 2:.4f})")
print(f"Cross-Validation (log scale) - MAE: {cv_mae_log.mean():.4f} (± {cv_mae_log.std() * 2:.4f})")

# Predictions
y_train_pred = best_model.predict(X_train_selected)
y_test_pred = best_model.predict(X_test_selected)


# Calculate R² scores on log scale
r2_train_score = r2_score(y_train, y_train_pred)
r2_test_score = r2_score(y_test, y_test_pred)

mae_train, mse_train, r2_train = evaluate_model(y_train, y_train_pred, y_train_original, is_log=True)
mae_test, mse_test, r2_test= evaluate_model(y_test, y_test_pred, y_test_original, is_log=True)

overfitting_train_test = calculate_overfitting(r2_train, r2_test)


# # پیش‌بینی و ارزیابی
# # y_train_pred_log = best_model.predict(X_train_selected)
# # train_mse_log = mean_squared_error(y_train, y_train_pred_log)
# # train_mae_log = mean_absolute_error(y_train, y_train_pred_log)
# # train_r2_log = r2_score(y_train, y_train_pred_log)


# # y_test_pred_log = best_model.predict(X_test_selected)
# # test_mse_log = mean_squared_error(y_test, y_test_pred_log)
# # test_mae_log = mean_absolute_error(y_test, y_test_pred_log)
# # test_r2_log = r2_score(y_test, y_test_pred_log)

# y_train_orig = np.expm1(y_train)
# y_train_pred_orig = np.expm1(y_train_pred_log)
# train_mse_orig = mean_squared_error(y_train_orig, y_train_pred_orig)
# train_mae_orig = mean_absolute_error(y_train_orig, y_train_pred_orig)
# train_r2_orig = r2_score(y_train_orig, y_train_pred_orig)



# y_test_orig = np.expm1(y_test)
# y_test_pred_orig = np.expm1(y_test_pred_log)
# test_mse_orig = mean_squared_error(y_test_orig, y_test_pred_orig)
# test_mae_orig = mean_absolute_error(y_test_orig, y_test_pred_orig)
# test_r2_orig = r2_score(y_test_orig, y_test_pred_orig)

print(f"Scores: r2_train: {r2_train_score}, r2_test: {r2_test_score}")
print(f"Train  - mae: {mae_train:.4f}, mse: {mse_train:.4f}, R²: {r2_train:.4f}")
print(f"Test  - mae: {mae_test:.4f}, mse: {mse_test:.4f}, R²: {r2_test:.4f}")
print(f"Overfitting: {overfitting_train_test:.4} ")
# SHAP Analysis
explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_test_selected)
shap.summary_plot(shap_values, X_test_selected, feature_names=selected_features, show=False)
plt.savefig(os.path.join(figures_dir, 'shap_summary_rf_smogn.png'))
plt.close()


import plotly.graph_objects as go
import plotly.express as px

# # Plot 1: Learning Curve
# Learning Curves
train_sizes, train_scores, val_scores = learning_curve(
    best_model, X_train_selected, y_train, cv=5, scoring='r2', n_jobs=-1
)
plt.plot(train_sizes, train_scores.mean(axis=1), label='Train R²')
plt.plot(train_sizes, val_scores.mean(axis=1), label='Validation R²')
plt.xlabel('Training Size')
plt.ylabel('R²')
plt.legend()
plt.savefig(os.path.join(figures_dir, 'rf_learning_curve.png'))
plt.close()


# Plot 2: Predicted vs Actual Scatter
# scatter_df = pd.DataFrame({
#     'Actual': np.expm1(y_test),
#     'Predicted': np.expm1(y_test_pred)
# })
# fig = plt.scatter(scatter_df, x='Actual', y='Predicted', opacity=0.5, title='Predicted vs Actual Values Scatter')
# fig.add_trace(plt.Scatter(x=[0, scatter_df['Actual'].max()], y=[0, scatter_df['Actual'].max()], mode='lines', line=dict(color='red', dash='dash'), name='y=x'))
# fig.update_layout(xaxis_title='Actual Values (wt%)', yaxis_title='Predicted Values (wt%)', template='plotly_white')
# fig.savefig(os.path.join(figures_dir, 'rf_Scatter.html'))
# fig.close()

# # Plot 3: Error Distribution
# errors = np.expm1(y_test) - np.expm1(y_test_pred)
# error_df = pd.DataFrame({'Error': errors})
# fig = px.histogram(error_df, x='Error', nbins=50, title='Prediction Error Distribution', histnorm='density')
# fig.add_trace(go.Scatter(x=np.linspace(errors.min(), errors.max(), 100), 
#                          y=1/np.sqrt(2*np.pi*np.var(errors))*np.exp(-(np.linspace(errors.min(), errors.max(), 100)**2)/(2*np.var(errors))),
#                          mode='lines', name='KDE', line=dict(color='red')))
# fig.update_layout(xaxis_title='Error (log_wt%)', yaxis_title='Density', template='plotly_white')
# fig.write_html(os.path.join(figures_dir, 'rf_Error_Distribution.html'))
# fig.close()

# # Plot 4: Feature Importance
# importance_df = pd.DataFrame({
#     'Feature': X_train.columns,
#     'Importance': feature_importance
# }).sort_values('Importance', ascending=False).head(10)
# fig = px.bar(importance_df, x='Importance', y='Feature', title='Top 10 Features by Importance')
# fig.update_layout(xaxis_title='Importance (%)', yaxis_title='Feature', template='plotly_white')
# fig.write_html(os.path.join(figures_dir, 'feature_importance.html'))
# fig.close()

# ذخیره نتایج
results_df = pd.DataFrame({
    'Model Accuracy on Training (R², original scale)': [r2_train],
    'Model Accuracy (MSE, original scale)': [mse_train],
    'Model Accuracy (MAE, original scale)': [mae_train],
    'Model Accuracy on test (R², original scale)': [r2_test],
    'Model Accuracy (MSE, original scale)': [mse_test],
    'Model Accuracy (MAE, original scale)': [mae_test],
    'Cv_R2_mean' : [cv_r2_log.mean()],
    'Cv_R2_std' : [cv_r2_log.std()],
    'Cv_mae_mean' : [cv_mae_log.mean()],
    'Cv_mae_std' : [cv_mae_log.std()],
    'Cv_mse_mean' : [cv_mse_log.mean()],
    'Cv_mse_std' : [cv_mse_log.std()],
    'Overfitting R²': [overfitting_train_test],
    'Top Feature': [feature_importance.iloc[0]['feature']],
    'Top Feature Importance': [feature_importance.iloc[0]['importance']],
    # 'final_estimator': [best_model._make_estimator],
    # 'oob_score': [best_model.oob_score],
    # 'oob_prediction': [best_model._get_oob_predictions]
})
results_df.to_csv(results_path, index=False)
print(f"Model results saved to {results_path}")

# ذخیره مدل
# joblib.dump(best_model, output_model_path)
# print(f"Model saved to {output_model_path}")

# ذخیره پارامترها
# best_params_df = pd.DataFrame([best_params | {'best_r2': best_score}])
# best_params_df.to_csv(output_params_path, index=False)
# print(f"Optimized parameters saved to {output_params_path}")