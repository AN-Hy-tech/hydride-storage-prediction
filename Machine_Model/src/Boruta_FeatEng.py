# File: D:\Hydride_Machine_learning_project\Machine_Model\src\feature_selection.py
import pandas as pd
import numpy as np
from sklearn.feature_selection import VarianceThreshold
from sklearn.ensemble import RandomForestRegressor
from boruta import BorutaPy
import shap
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
import random
import re

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)
os.environ['PYTHONHASHSEED'] = '42'

# Paths updated to managed (no_outliers) data from Outliers_Management.py
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\test.csv"
output_selected_train = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_train.csv"
output_selected_val = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_val.csv"
output_selected_test = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_test.csv"
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

# Define the feature to always keep
must_keep = 'temperature(K)'

# Step 1: Remove constant features (variance=0)
var_thresh_zero = VarianceThreshold(threshold=0.001)
X_train_zero = var_thresh_zero.fit_transform(X_train)
selected_cols_zero = X_train.columns[var_thresh_zero.get_support()].tolist()
if must_keep not in selected_cols_zero and must_keep in X_train.columns:
    selected_cols_zero.append(must_keep)
X_train_zero = X_train[selected_cols_zero]
print(f"After zero variance filter: {X_train_zero.shape[1]} features")

# Step 2: Boruta for automated feature selection
rf = RandomForestRegressor(n_jobs=-1, max_depth=6, random_state=42)
boruta_selector = BorutaPy(rf, n_estimators='auto', verbose=2, random_state=42, max_iter=2000)
boruta_selector.fit(X_train_zero.values, y_train.values)

# Get selected features
selected_cols_boruta = X_train_zero.columns[boruta_selector.support_].tolist()
if must_keep not in selected_cols_boruta and must_keep in X_train_zero.columns:
    selected_cols_boruta.append(must_keep)
X_train_selected = X_train_zero[selected_cols_boruta]
print(f"After Boruta: {len(selected_cols_boruta)} features")

# Step 3: Iterative VIF for multicollinearity (threshold=30)
def iterative_vif(X, thresh=30.0, must_keep=None):
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
        
        # Filter out the must_keep feature for dropping consideration
        if must_keep is not None:
            vif_data_drop = vif_data[vif_data['Feature'] != must_keep]
            if vif_data_drop.empty:
                break  # Only must_keep left
            max_vif_drop = vif_data_drop['VIF'].max()
            if max_vif_drop <= thresh:
                break
            to_drop_idx = vif_data_drop['VIF'].idxmax()
            to_drop = vif_data_drop.loc[to_drop_idx, 'Feature']
        else:
            max_vif = vif_data['VIF'].max()
            if max_vif <= thresh:
                break
            to_drop = vif_data.loc[vif_data['VIF'].idxmax(), 'Feature']
        
        features.remove(to_drop)
    return X[features], features

X_train_vif, selected_cols_final = iterative_vif(X_train_selected, must_keep=must_keep)
print(f"After iterative VIF: {len(selected_cols_final)} features")

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
explainer = shap.TreeExplainer(rf, feature_perturbation='tree_path_dependent')
shap_values = explainer(X_train_final)
shap_importance = np.abs(shap_values.values).mean(axis=0)
importance_df = pd.DataFrame({'Feature': selected_cols_final, 'SHAP_Importance': shap_importance})
importance_df = importance_df.sort_values(by='SHAP_Importance', ascending=False).reset_index(drop=True)

# Save SHAP importance
importance_df.to_csv(report_path, index=False)
print(f"SHAP importance report saved to {report_path}")

# Plot SHAP summary with adjusted size
plt.figure(figsize=(10, len(selected_cols_final) * 0.4))  # Adjust height based on number of features
shap.summary_plot(shap_values, X_train_final, show=False, max_display=len(selected_cols_final))
plt.title('SHAP Summary Plot')
plt.tight_layout()
plt.savefig(shap_summary_path, bbox_inches='tight')
plt.close()
print(f"SHAP summary plot saved to {shap_summary_path}")

# Plot final feature importance (SHAP-based) as horizontal barplot for better label visibility
plt.figure(figsize=(12, len(importance_df) * 0.3))  # Adjust height based on number of features
sns.barplot(x='SHAP_Importance', y='Feature', data=importance_df, hue='Feature', legend=False, palette='viridis')
plt.title('SHAP Feature Importance (Final Selected Features)')
plt.xlabel('SHAP Importance')
plt.ylabel('Feature')
plt.tight_layout()
plt.savefig(importance_path, bbox_inches='tight')
plt.close()
print(f"SHAP importance plot saved to {importance_path}")

# Function to sanitize filenames
def sanitize_filename(name):
    invalid_chars = r'[\/:*?"<>|]'
    return re.sub(invalid_chars, '_', name)

# Expanded SHAP Analysis based on checklist

# 1. Extract from Summary Plot: Top 10 features, direction of effect, interaction signs
top_ten_features = importance_df['Feature'].iloc[:10].tolist()

# For direction: Compute mean SHAP for high values (above median) to determine if positive or negative
directions = {}
for feature in top_ten_features:
    median_val = np.median(X_train_final[feature])
    high_mask = X_train_final[feature] > median_val
    mean_shap_high = np.mean(shap_values.values[high_mask, selected_cols_final.index(feature)])
    direction = 'positive' if mean_shap_high > 0 else 'negative'
    directions[feature] = direction

# For interaction signs: Use vertical dispersion proxy (std dev of SHAP values normalized by importance)
interaction_indicators = {}
for feature in top_ten_features:
    shap_std = np.std(shap_values.values[:, selected_cols_final.index(feature)])
    norm_std = shap_std / shap_importance[selected_cols_final.index(feature)] if shap_importance[selected_cols_final.index(feature)] != 0 else 0
    indicator = 'yes' if norm_std > 0.5 else 'no'  # Arbitrary threshold for "unusual vertical dispersion"
    interaction_indicators[feature] = indicator

# Create summary extraction DF and save as CSV
summary_extract_df = pd.DataFrame({
    'Feature': top_ten_features,
    'Rank': list(range(1, 11)),
    'Direction (high values)': [directions[f] for f in top_ten_features],
    'Interaction Indicator': [interaction_indicators[f] for f in top_ten_features]
})
summary_extract_path = os.path.join(os.path.dirname(report_path), 'shap_summary_extraction.csv')
summary_extract_df.to_csv(summary_extract_path, index=False)
print(f"SHAP summary extraction saved to {summary_extract_path}")

# # 2. Dependence plots for each key feature with turning points description
# dependence_descriptions = {}
# for rank, feature in enumerate(top_ten_features, 1):
#     feature_safe = sanitize_filename(feature)
#     # Basic dependence plot with adjusted size
#     dep_plot_path = os.path.join(figures_path, f'dependence_plot_{feature_safe}.png')
#     plt.figure(figsize=(10, 6))
#     shap.dependence_plot(feature, shap_values.values, X_train_final.values, feature_names=selected_cols_final, show=False)
#     plt.title(f'Dependence Plot for {feature}')
#     plt.tight_layout()
#     plt.savefig(dep_plot_path, bbox_inches='tight')
#     plt.close()
#     print(f"Dependence plot for {feature} saved to {dep_plot_path}")
    
#     # Simple description of turning points/thresholds (e.g., detect sign changes or saturation)
#     feat_idx = selected_cols_final.index(feature)
#     sorted_idx = np.argsort(X_train_final[feature])
#     sorted_shap = shap_values.values[sorted_idx, feat_idx]
#     sorted_feat = X_train_final[feature].iloc[sorted_idx]
    
#     # Detect sign changes
#     sign_changes = np.where(np.diff(np.sign(sorted_shap)))[0]
#     thresholds = [sorted_feat.iloc[i+1] for i in sign_changes] if len(sign_changes) > 0 else []
    
#     # Detect saturation (where slope flattens, simple: where abs diff < threshold)
#     diffs = np.abs(np.diff(sorted_shap))
#     sat_points = np.where(diffs < 0.01 * np.max(diffs))[0]  # Arbitrary low change threshold
#     sat_ranges = []  # Could group consecutive, but simplify to count
#     description = f"Turning points (sign changes) at approx: {thresholds}. "
#     description += f"Saturation indicated in {len(sat_points)} regions (low change in SHAP)."
#     dependence_descriptions[feature] = description

# # Save dependence descriptions to CSV
# dep_desc_df = pd.DataFrame({'Feature': top_ten_features, 'Description': [dependence_descriptions[f] for f in top_ten_features]})
# dep_desc_path = os.path.join(os.path.dirname(report_path), 'dependence_descriptions.csv')
# dep_desc_df.to_csv(dep_desc_path, index=False)
# print(f"Dependence descriptions saved to {dep_desc_path}")

# # 3. If interaction suspected, repeat dependence with color, report interaction values
# interaction_reports = {}
# for feature in top_ten_features:
#     if interaction_indicators[feature] == 'yes':
#         feature_safe = sanitize_filename(feature)
#         # Interaction dependence plot with adjusted size
#         inter_dep_plot_path = os.path.join(figures_path, f'interaction_dependence_plot_{feature_safe}.png')
#         plt.figure(figsize=(10, 6))
#         shap.dependence_plot(feature, shap_values.values, X_train_final.values, feature_names=selected_cols_final, interaction_index='auto', show=False)
#         plt.title(f'Interaction Dependence Plot for {feature}')
#         plt.tight_layout()
#         plt.savefig(inter_dep_plot_path, bbox_inches='tight')
#         plt.close()
#         print(f"Interaction dependence plot for {feature} saved to {inter_dep_plot_path}")
        
#         # Compute interaction values (limited to this feature and top others for efficiency)
#         shap_interactions = explainer.shap_interaction_values(X_train_final)
#         feat_idx = selected_cols_final.index(feature)
#         mean_inter = np.abs(shap_interactions[:, feat_idx, :]).mean(axis=0)
#         inter_df = pd.DataFrame({'Interacting_Feature': selected_cols_final, 'Mean_Abs_Interaction': mean_inter})
#         inter_df = inter_df.sort_values('Mean_Abs_Interaction', ascending=False).iloc[1:]  # Exclude self
#         interaction_reports[feature] = inter_df

# # Save interaction reports if any
# if interaction_reports:
#     for feature, df in interaction_reports.items():
#         feature_safe = sanitize_filename(feature)
#         inter_report_path = os.path.join(os.path.dirname(report_path), f'interaction_report_{feature_safe}.csv')
#         df.to_csv(inter_report_path, index=False)
#         print(f"Interaction report for {feature} saved to {inter_report_path}")

# 4. Case studies: Waterfall for best/worst alloys (based on target value)
# Find indices for max and min target
best_idx = y_train.idxmax()
worst_idx = y_train.idxmin()

# Best case with adjusted size
best_waterfall_path = os.path.join(figures_path, 'waterfall_best.png')
plt.figure(figsize=(10, len(selected_cols_final) * 0.3))  # Adjust height based on number of features
shap.plots.waterfall(shap_values[best_idx], show=False)
plt.title(f'Waterfall Plot for Best Alloy: {composition_train.iloc[best_idx]}')
plt.tight_layout()
plt.savefig(best_waterfall_path, bbox_inches='tight')
plt.close()
print(f"Waterfall for best alloy saved to {best_waterfall_path}")

# Worst case with adjusted size
worst_waterfall_path = os.path.join(figures_path, 'waterfall_worst.png')
plt.figure(figsize=(10, len(selected_cols_final) * 0.3))  # Adjust height based on number of features
shap.plots.waterfall(shap_values[worst_idx], show=False)
plt.title(f'Waterfall Plot for Worst Alloy: {composition_train.iloc[worst_idx]}')
plt.tight_layout()
plt.savefig(worst_waterfall_path, bbox_inches='tight')
plt.close()
print(f"Waterfall for worst alloy saved to {worst_waterfall_path}")

