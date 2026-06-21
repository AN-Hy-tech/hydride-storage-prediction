# File: D:\Hydride_Machine_learning_project\Machine_Model\src\feature_selection.py
import pandas as pd
import numpy as np
from sklearn.feature_selection import VarianceThreshold, mutual_info_regression, RFECV
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
import shap
import matplotlib.pyplot as plt
import seaborn as sns
import os
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings

# Paths updated to managed (no_outliers) data from Outliers_Management.py
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\no_outliers_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\no_outliers_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\no_outliers_test.csv"
output_selected_train = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_train.csv"
output_selected_val = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_val.csv"
output_selected_test = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_test.csv"
figures_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\feature_selection"
report_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\feature_selection_report.csv"
shap_summary_path = os.path.join(figures_path, 'shap_summary.png')
importance_path = os.path.join(figures_path, 'shap_importance_plot.png')

# Create directories
os.makedirs(figures_path, exist_ok=True)
os.makedirs(os.path.dirname(report_path), exist_ok=True)
os.makedirs(os.path.dirname(output_selected_train), exist_ok=True)

# Load managed data
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded managed train data with shape: {df_train.shape}")
print(f"Loaded managed val data with shape: {df_val.shape}")
print(f"Loaded managed test data with shape: {df_test.shape}")

# Separate features, target, and composition from train
X_train = df_train.drop(['target', 'formula'], axis=1)
y_train = df_train['target']
composition_train = df_train['formula']

# Step 1: Remove constant features (variance=0)
var_thresh_zero = VarianceThreshold(threshold=0)
X_train_zero = var_thresh_zero.fit_transform(X_train)
selected_cols_zero = X_train.columns[var_thresh_zero.get_support()]
X_train_zero = pd.DataFrame(X_train_zero, columns=selected_cols_zero)
print(f"After zero variance filter: {X_train_zero.shape[1]} features")

# Step 2: Remove low variance features (threshold=0.01)
var_thresh = VarianceThreshold(threshold=0.001)
X_train_var = var_thresh.fit_transform(X_train_zero)
selected_cols_var = X_train_zero.columns[var_thresh.get_support()]
X_train_var = pd.DataFrame(X_train_var, columns=selected_cols_var)
print(f"After low variance filter: {X_train_var.shape[1]} features")

# Step 3: Filter based on mutual info (> 0)
mi = mutual_info_regression(X_train_var, y_train, n_jobs=-1)
mi_df = pd.DataFrame({'Feature': selected_cols_var, 'MI': mi})
mi_df = mi_df[mi_df['MI'] > 0.001]
selected_cols_mi = mi_df['Feature'].tolist()
X_train_mi = X_train_var[selected_cols_mi]
print(f"After MI filter: {X_train_mi.shape[1]} features")

# Step 4: Iterative VIF for multicollinearity (threshold=30)
def iterative_vif(X, thresh=30.0):
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    features = X.columns.tolist()
    while True:
        vif_data = pd.DataFrame()
        vif_data['Feature'] = features
        vif_values = []
        for i in range(len(features)):
            try:
                vif = variance_inflation_factor(X[features].values, i)
                vif_values.append(vif if np.isfinite(vif) else np.inf)
            except:
                vif_values.append(np.inf)
        vif_data['VIF'] = vif_values
        max_vif = vif_data['VIF'].max()
        if max_vif <= thresh:
            break
        to_drop = vif_data.loc[vif_data['VIF'].idxmax(), 'Feature']
        features.remove(to_drop)
    return X[features], features

X_train_vif, selected_cols_vif = iterative_vif(X_train_mi)
print(f"After iterative VIF: {len(selected_cols_vif)} features")

# Step 5: Embedded feature selection using RF importances
rf = RandomForestRegressor(random_state=42, n_jobs=-1)
rf.fit(X_train_vif, y_train)
importances = rf.feature_importances_
threshold = np.mean(importances)
selected_cols_embed = [f for f, imp in zip(selected_cols_vif, importances) if imp >= threshold]
X_train_embed = X_train_vif[selected_cols_embed]
print(f"After embedded RF: {len(selected_cols_embed)} features")

# Cross-validate intermediate model
cv_scores = cross_val_score(rf, X_train_embed, y_train, cv=5, scoring='neg_mean_absolute_error')
print(f"Intermediate CV MAE: {-cv_scores.mean()}")

# Step 6: RFECV wrapper for optimal number of features
kf = KFold(n_splits=7, shuffle=True, random_state=42)
rfecv = RFECV(estimator=rf, step=3, cv=kf, scoring='neg_mean_absolute_error', n_jobs=-1)
rfecv.fit(X_train_embed, y_train)
selected_cols_final = [f for f, support in zip(selected_cols_embed, rfecv.support_) if support]
print(f"After RFECV: {len(selected_cols_final)} features")

# Apply selected features to train, val, test
df_train_selected = pd.concat([composition_train, df_train[selected_cols_final], y_train], axis=1)
df_val_selected = pd.concat([df_val['formula'], df_val[selected_cols_final], df_val['target']], axis=1)
df_test_selected = pd.concat([df_test['formula'], df_test[selected_cols_final], df_test['target']], axis=1)

# Save selected dataframes
df_train_selected.to_csv(output_selected_train, index=False)
df_val_selected.to_csv(output_selected_val, index=False)
df_test_selected.to_csv(output_selected_test, index=False)

print(f"Selected train data saved to {output_selected_train}")
print(f"Selected val data saved to {output_selected_val}")
print(f"Selected test data saved to {output_selected_test}")

# Evaluate selected features on val
X_val = df_val[selected_cols_final]
y_val = df_val['target']
rf.fit(df_train[selected_cols_final], y_train)
y_pred = rf.predict(X_val)
mae = mean_absolute_error(y_val, y_pred)
r2 = r2_score(y_val, y_pred)
print(f"Val MAE: {mae}, R2: {r2}")

# SHAP for explainability on final features
X_train_final = df_train[selected_cols_final]
explainer = shap.Explainer(rf, X_train_final.values)
shap_values = explainer(X_train_final.values, check_additivity=False)
shap_importance = np.abs(shap_values.values).mean(axis=0)
importance_df = pd.DataFrame({'Feature': selected_cols_final, 'SHAP_Importance': shap_importance})
importance_df = importance_df.sort_values(by='SHAP_Importance', ascending=False).reset_index(drop=True)

# Save SHAP importance
importance_df.to_csv(report_path, index=False)
print(f"SHAP importance report saved to {report_path}")

# Plot SHAP summary
shap.summary_plot(shap_values, X_train_final, show=False)
plt.title('SHAP Summary Plot')
plt.savefig(shap_summary_path)
plt.close()
print(f"SHAP summary plot saved to {shap_summary_path}")

# Plot final feature importance (SHAP-based)
plt.figure(figsize=(12, 8))
sns.barplot(x='SHAP_Importance', hue='Feature', data=importance_df, legend=True)
plt.title('SHAP Feature Importance (Final Selected Features)')
plt.savefig(importance_path)
plt.close()
print(f"SHAP importance plot saved to {importance_path}")