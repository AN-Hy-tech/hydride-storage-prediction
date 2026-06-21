# File: D:\Hydride_Machine_learning_project\Machine_Model\src\analyze_optimized_catboost.py
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import RobustScaler
from pymatgen.core import Composition, Element
from collections import Counter

# Paths
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data\selected_test.csv"
model_path = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna\catboost_model.pkl"
figures_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\model_analysis"
optimized_models_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_optuna"
os.makedirs(figures_path, exist_ok=True)

# Set seaborn style for better visualizations
sns.set(style="whitegrid", palette="pastel")

# Load data
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded selected train data with shape: {df_train.shape}")
print(f"Loaded selected val data with shape: {df_val.shape}")
print(f"Loaded selected test data with shape: {df_test.shape}")

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
formulas_test = df_test['formula']

# Load scaler
scaler_path = os.path.join(optimized_models_dir, 'scaler.pkl')
scaler = joblib.load(scaler_path)

# Scale features
X_train_scaled = scaler.transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# Load optimized CatBoost model
model = joblib.load(model_path)
print("Optimized CatBoost model loaded")

# Get learning rate
params = model.get_params()
learning_rate = params.get('learning_rate', 'Not specified')
print(f"Learning rate: {learning_rate}")

# Predict on train, val, test
y_pred_train = model.predict(X_train_scaled)
y_pred_train_original = np.expm1(y_pred_train)

y_pred_val = model.predict(X_val_scaled)
y_pred_val_original = np.expm1(y_pred_val)

y_pred = model.predict(X_test_scaled)
y_pred_original = np.expm1(y_pred)

# Calculate errors for train
train_mae_log = mean_absolute_error(y_train, y_pred_train)
train_rmse_log = np.sqrt(mean_squared_error(y_train, y_pred_train))
train_r2_log = r2_score(y_train, y_pred_train)

train_mae_orig = mean_absolute_error(y_train_original, y_pred_train_original)
train_rmse_orig = np.sqrt(mean_squared_error(y_train_original, y_pred_train_original))
train_r2_orig = r2_score(y_train_original, y_pred_train_original)
train_mape_orig = np.mean(np.abs((y_train_original - y_pred_train_original) / y_train_original)) * 100 if np.all(y_train_original != 0) else np.nan
train_me_orig = np.mean(y_train_original - y_pred_train_original)

print(f"Train MAE (log): {train_mae_log}, RMSE (log): {train_rmse_log}, R2 (log): {train_r2_log}")
print(f"Train MAE (orig): {train_mae_orig}, RMSE (orig): {train_rmse_orig}, R2 (orig): {train_r2_orig}, MAPE (orig): {train_mape_orig}, ME (orig): {train_me_orig}")

# Calculate errors for val
val_mae_log = mean_absolute_error(y_val, y_pred_val)
val_rmse_log = np.sqrt(mean_squared_error(y_val, y_pred_val))
val_r2_log = r2_score(y_val, y_pred_val)

val_mae_orig = mean_absolute_error(y_val_original, y_pred_val_original)
val_rmse_orig = np.sqrt(mean_squared_error(y_val_original, y_pred_val_original))
val_r2_orig = r2_score(y_val_original, y_pred_val_original)
val_mape_orig = np.mean(np.abs((y_val_original - y_pred_val_original) / y_val_original)) * 100 if np.all(y_val_original != 0) else np.nan
val_me_orig = np.mean(y_val_original - y_pred_val_original)

print(f"Val MAE (log): {val_mae_log}, RMSE (log): {val_rmse_log}, R2 (log): {val_r2_log}")
print(f"Val MAE (orig): {val_mae_orig}, RMSE (orig): {val_rmse_orig}, R2 (orig): {val_r2_orig}, MAPE (orig): {val_mape_orig}, ME (orig): {val_me_orig}")

# Calculate errors for test
mae_log = mean_absolute_error(y_test, y_pred)
rmse_log = np.sqrt(mean_squared_error(y_test, y_pred))
r2_log = r2_score(y_test, y_pred)

mae_orig = mean_absolute_error(y_test_original, y_pred_original)
rmse_orig = np.sqrt(mean_squared_error(y_test_original, y_pred_original))
r2_orig = r2_score(y_test_original, y_pred_original)
mape_orig = np.mean(np.abs((y_test_original - y_pred_original) / y_test_original)) * 100 if np.all(y_test_original != 0) else np.nan
me_orig = np.mean(y_test_original - y_pred_original)

print(f"Test MAE (log): {mae_log}, RMSE (log): {rmse_log}, R2 (log): {r2_log}")
print(f"Test MAE (orig): {mae_orig}, RMSE (orig): {rmse_orig}, R2 (orig): {r2_orig}, MAPE (orig): {mape_orig}, ME (orig): {me_orig}")

# Residuals for test
residuals = y_test - y_pred
residuals_orig = y_test_original - y_pred_original

# Plot residuals
plt.figure(figsize=(10, 6))
sns.histplot(residuals_orig, kde=True, color='skyblue', bins=30)
plt.title('Residuals Distribution (Original Scale)', fontsize=16)
plt.xlabel('Residuals', fontsize=14)
plt.ylabel('Frequency', fontsize=14)
plt.savefig(os.path.join(figures_path, 'residuals_hist.png'))
plt.close()

plt.figure(figsize=(10, 6))
plt.scatter(y_pred_original, residuals_orig, alpha=0.7, color='coral')
plt.axhline(0, color='black', linestyle='--', linewidth=2)
plt.title('Residuals vs Predicted (Original Scale)', fontsize=16)
plt.xlabel('Predicted Capacity', fontsize=14)
plt.ylabel('Residuals', fontsize=14)
plt.savefig(os.path.join(figures_path, 'residuals_scatter.png'))
plt.close()

# Scatter plot predicted vs actual for train
plt.figure(figsize=(10, 6))
plt.scatter(y_train_original, y_pred_train_original, alpha=0.6, color='green')
plt.plot([y_train_original.min(), y_train_original.max()], [y_train_original.min(), y_train_original.max()], 'r--', linewidth=2)
plt.title('Predicted vs Actual Capacity (Train Set)', fontsize=16)
plt.xlabel('Actual Capacity', fontsize=14)
plt.ylabel('Predicted Capacity', fontsize=14)
plt.savefig(os.path.join(figures_path, 'predicted_vs_actual_train.png'))
plt.close()

# Scatter plot predicted vs actual for val
plt.figure(figsize=(10, 6))
plt.scatter(y_val_original, y_pred_val_original, alpha=0.6, color='blue')
plt.plot([y_val_original.min(), y_val_original.max()], [y_val_original.min(), y_val_original.max()], 'r--', linewidth=2)
plt.title('Predicted vs Actual Capacity (Val Set)', fontsize=16)
plt.xlabel('Actual Capacity', fontsize=14)
plt.ylabel('Predicted Capacity', fontsize=14)
plt.savefig(os.path.join(figures_path, 'predicted_vs_actual_val.png'))
plt.close()

# Scatter plot predicted vs actual for test
plt.figure(figsize=(10, 6))
plt.scatter(y_test_original, y_pred_original, alpha=0.6, color='purple')
plt.plot([y_test_original.min(), y_test_original.max()], [y_test_original.min(), y_test_original.max()], 'r--', linewidth=2)
plt.title('Predicted vs Actual Capacity (Test Set)', fontsize=16)
plt.xlabel('Actual Capacity', fontsize=14)
plt.ylabel('Predicted Capacity', fontsize=14)
plt.savefig(os.path.join(figures_path, 'predicted_vs_actual_test.png'))
plt.close()

# Feature importance
feature_importances = model.get_feature_importance()
features = X_test.columns
importance_df = pd.DataFrame({'Feature': features, 'Importance': feature_importances})
importance_df = importance_df.sort_values(by='Importance', ascending=False).head(10)  # Top 10

# Plot feature importance
plt.figure(figsize=(12, 8))
sns.barplot(x='Importance', y='Feature', hue='Importance', data=importance_df, palette='viridis', legend=False)
plt.title('Top Feature Importances in Optimized CatBoost', fontsize=16)
plt.xlabel('Importance', fontsize=14)
plt.ylabel('Feature', fontsize=14)
plt.savefig(os.path.join(figures_path, 'feature_importance.png'))
plt.close()

# Correlation with target (using train data for stability)
df_train_top = df_train[importance_df['Feature'].tolist() + ['target']]
corr_matrix = df_train_top.corr()

# Plot correlation heatmap
plt.figure(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, linewidths=0.5)
plt.title('Correlation Matrix: Top Features and Target', fontsize=16)
plt.savefig(os.path.join(figures_path, 'correlation_heatmap.png'))
plt.close()

# Pairplot for top features and target
sns.pairplot(df_train_top, diag_kind='kde', plot_kws={'alpha': 0.6})
plt.suptitle('Pairplot: Top Features and Target', y=1.02, fontsize=16)
plt.savefig(os.path.join(figures_path, 'features_target_pairplot.png'))
plt.close()

# High capacity analysis (>3%)
high_capacity_mask = y_test_original > 3
num_high = np.sum(high_capacity_mask)
y_test_high = y_test_original[high_capacity_mask]
y_pred_high = y_pred_original[high_capacity_mask]

if len(y_test_high) > 0:
    mae_high = mean_absolute_error(y_test_high, y_pred_high)
    rmse_high = np.sqrt(mean_squared_error(y_test_high, y_pred_high))
    r2_high = r2_score(y_test_high, y_pred_high)
    mape_high = np.mean(np.abs((y_test_high - y_pred_high) / y_test_high)) * 100 if np.all(y_test_high != 0) else np.nan
    me_high = np.mean(y_test_high - y_pred_high)
    print(f"High Capacity (>3%, n={num_high}) MAE: {mae_high}, RMSE: {rmse_high}, R2: {r2_high}, MAPE: {mape_high}, ME: {me_high}")

    # Plot predicted vs actual for high capacity
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test_high, y_pred_high, alpha=0.6, color='red')
    plt.plot([y_test_high.min(), y_test_high.max()], [y_test_high.min(), y_test_high.max()], 'b--', linewidth=2)
    plt.title('Predicted vs Actual Capacity (>3%)', fontsize=16)
    plt.xlabel('Actual Capacity', fontsize=14)
    plt.ylabel('Predicted Capacity', fontsize=14)
    plt.savefig(os.path.join(figures_path, 'high_capacity_scatter.png'))
    plt.close()
else:
    print("No samples with capacity >3% in test set")

# Low capacity analysis (<1%)
low_capacity_mask = y_test_original < 1
num_low = np.sum(low_capacity_mask)
y_test_low = y_test_original[low_capacity_mask]
y_pred_low = y_pred_original[low_capacity_mask]

if len(y_test_low) > 0:
    mae_low = mean_absolute_error(y_test_low, y_pred_low)
    rmse_low = np.sqrt(mean_squared_error(y_test_low, y_pred_low))
    r2_low = r2_score(y_test_low, y_pred_low)
    mape_low = np.mean(np.abs((y_test_low - y_pred_low) / y_test_low)) * 100 if np.all(y_test_low != 0) else np.nan
    me_low = np.mean(y_test_low - y_pred_low)
    print(f"Low Capacity (<1%, n={num_low}) MAE: {mae_low}, RMSE: {rmse_low}, R2: {r2_low}, MAPE: {mape_low}, ME: {me_low}")

    # Plot predicted vs actual for low capacity
    plt.figure(figsize=(10, 6))
    plt.scatter(y_test_low, y_pred_low, alpha=0.6, color='orange')
    plt.plot([y_test_low.min(), y_test_low.max()], [y_test_low.min(), y_test_low.max()], 'g--', linewidth=2)
    plt.title('Predicted vs Actual Capacity (<1%)', fontsize=16)
    plt.xlabel('Actual Capacity', fontsize=14)
    plt.ylabel('Predicted Capacity', fontsize=14)
    plt.savefig(os.path.join(figures_path, 'low_capacity_scatter.png'))
    plt.close()
else:
    print("No samples with capacity <1% in test set")

# Material-based analysis
def parse_formula(formula):
    try:
        comp = Composition(formula)
        elements = {str(el) for el in comp.elements}
    except ValueError:
        elements = set()
    return elements

def get_average_property(elements, prop):
    if not elements:
        return np.nan
    vals = []
    for el_str in elements:
        try:
            elem = Element(el_str)
            val = getattr(elem, prop)
            if val is not None:
                vals.append(val)
        except:
            pass
    if vals:
        return np.mean(vals)
    return np.nan

df_analysis = pd.DataFrame({
    'formula': formulas_test,
    'actual_orig': y_test_original,
    'pred_orig': y_pred_original,
    'residual_orig': residuals_orig
})

df_analysis['elements'] = df_analysis['formula'].apply(parse_formula)
df_analysis['avg_atomic_number'] = df_analysis['elements'].apply(lambda els: get_average_property(els, 'Z'))
df_analysis['avg_electronegativity'] = df_analysis['elements'].apply(lambda els: get_average_property(els, 'X'))
df_analysis['avg_atomic_mass'] = df_analysis['elements'].apply(lambda els: get_average_property(els, 'atomic_mass'))

# Print correlations
print("Correlation between residuals and avg atomic number:", df_analysis['residual_orig'].corr(df_analysis['avg_atomic_number']))
print("Correlation between residuals and avg electronegativity:", df_analysis['residual_orig'].corr(df_analysis['avg_electronegativity']))
print("Correlation between residuals and avg atomic mass:", df_analysis['residual_orig'].corr(df_analysis['avg_atomic_mass']))

# Plot residuals vs material properties
plt.figure(figsize=(10, 6))
sns.scatterplot(x='avg_atomic_number', y='residual_orig', data=df_analysis, alpha=0.7, color='teal')
plt.title('Residuals vs Average Atomic Number', fontsize=16)
plt.xlabel('Average Atomic Number', fontsize=14)
plt.ylabel('Residuals (Original Scale)', fontsize=14)
plt.savefig(os.path.join(figures_path, 'residuals_vs_avg_atomic_number.png'))
plt.close()

plt.figure(figsize=(10, 6))
sns.scatterplot(x='avg_electronegativity', y='residual_orig', data=df_analysis, alpha=0.7, color='magenta')
plt.title('Residuals vs Average Electronegativity', fontsize=16)
plt.xlabel('Average Electronegativity', fontsize=14)
plt.ylabel('Residuals (Original Scale)', fontsize=14)
plt.savefig(os.path.join(figures_path, 'residuals_vs_avg_electronegativity.png'))
plt.close()

plt.figure(figsize=(10, 6))
sns.scatterplot(x='avg_atomic_mass', y='residual_orig', data=df_analysis, alpha=0.7, color='olive')
plt.title('Residuals vs Average Atomic Mass', fontsize=16)
plt.xlabel('Average Atomic Mass', fontsize=14)
plt.ylabel('Residuals (Original Scale)', fontsize=14)
plt.savefig(os.path.join(figures_path, 'residuals_vs_avg_atomic_mass.png'))
plt.close()

all_elements = [el for elems in df_analysis['elements'] for el in elems]
element_counts = Counter(all_elements)
common_elements = [el for el, count in element_counts.most_common(10)]
print("Common elements in test set:", common_elements)

# Metrics per common element
element_metrics = []
for el in common_elements:
    mask = df_analysis['elements'].apply(lambda x: el in x)
    if mask.sum() > 0:
        subset_actual = df_analysis.loc[mask, 'actual_orig']
        subset_pred = df_analysis.loc[mask, 'pred_orig']
        mae = mean_absolute_error(subset_actual, subset_pred)
        rmse = np.sqrt(mean_squared_error(subset_actual, subset_pred))
        r2 = r2_score(subset_actual, subset_pred) if len(subset_actual) > 1 else np.nan
        print(f"Element {el} (n={mask.sum()}): MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")
        element_metrics.append({'Element': el, 'MAE': mae, 'n': mask.sum()})

# Plot MAE per element
if element_metrics:
    metrics_df = pd.DataFrame(element_metrics)
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Element', y='MAE', hue='Element', data=metrics_df, palette='Set2', legend=False)
    plt.title('MAE per Common Element', fontsize=16)
    plt.xlabel('Element', fontsize=14)
    plt.ylabel('MAE', fontsize=14)
    plt.savefig(os.path.join(figures_path, 'mae_per_element.png'))
    plt.close()

# Plot boxplot of residuals per element (for top 5)
selected_elements = common_elements[:5]
data_for_box = []
labels = []
for el in selected_elements:
    mask = df_analysis['elements'].apply(lambda x: el in x)
    res = df_analysis.loc[mask, 'residual_orig']
    data_for_box.extend(res)
    labels.extend([el] * len(res))

box_df = pd.DataFrame({'Element': labels, 'Residuals': data_for_box})

plt.figure(figsize=(12, 6))
sns.boxplot(x='Element', y='Residuals', hue='Element', data=box_df, palette='Set3', legend=False)
plt.title('Residuals Distribution per Common Element', fontsize=16)
plt.xlabel('Element', fontsize=14)
plt.ylabel('Residuals (Original Scale)', fontsize=14)
plt.savefig(os.path.join(figures_path, 'residuals_per_element.png'))
plt.close()

# Analysis by number of elements
df_analysis['num_elements'] = df_analysis['elements'].apply(len)
unique_num = sorted(df_analysis['num_elements'].unique())

for num in unique_num:
    mask = df_analysis['num_elements'] == num
    if mask.sum() > 0:
        subset_actual = df_analysis.loc[mask, 'actual_orig']
        subset_pred = df_analysis.loc[mask, 'pred_orig']
        mae = mean_absolute_error(subset_actual, subset_pred)
        rmse = np.sqrt(mean_squared_error(subset_actual, subset_pred))
        r2 = r2_score(subset_actual, subset_pred) if len(subset_actual) > 1 else np.nan
        print(f"{num}-ary compounds (n={mask.sum()}): MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")

# Boxplot for residuals per num_elements
plt.figure(figsize=(10, 6))
sns.boxplot(x='num_elements', y='residual_orig', hue='num_elements', data=df_analysis, palette='coolwarm', legend=False)
plt.title('Residuals vs Number of Elements in Formula', fontsize=16)
plt.xlabel('Number of Elements', fontsize=14)
plt.ylabel('Residuals (Original Scale)', fontsize=14)
plt.savefig(os.path.join(figures_path, 'residuals_vs_num_elements.png'))
plt.close()

# Plot learning curve
evals_result = model.get_evals_result()
if evals_result:
    plt.figure(figsize=(10, 6))
    plt.plot(evals_result['learn']['RMSE'], label='Train RMSE')
    plt.plot(evals_result['validation']['RMSE'], label='Test RMSE')
    plt.title('Learning Curve: RMSE over Iterations', fontsize=16)
    plt.xlabel('Iterations', fontsize=14)
    plt.ylabel('RMSE', fontsize=14)
    plt.legend()
    plt.savefig(os.path.join(figures_path, 'learning_curve.png'))
    plt.close()
else:
    print("No evaluation results available for learning curve.")