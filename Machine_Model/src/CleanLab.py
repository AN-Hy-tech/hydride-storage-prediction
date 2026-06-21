# Outliers_Management_with_Cleanlab.py
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import HistGradientBoostingRegressor
from cleanlab.regression.learn import CleanLearning
import matplotlib.pyplot as plt

# Paths
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\test.csv"
processed_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed_data"
output_no_outliers_train_path = os.path.join(processed_dir, "no_outliers_train.csv")
output_no_outliers_val_path = os.path.join(processed_dir, "no_outliers_val.csv")
output_no_outliers_test_path = os.path.join(processed_dir, "no_outliers_test.csv")
output_outliers_train_path = os.path.join(processed_dir, "outliers_train.csv")
output_outliers_val_path = os.path.join(processed_dir, "outliers_val.csv")
output_outliers_test_path = os.path.join(processed_dir, "outliers_test.csv")
figures_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\outliers_analysis"

# Create directories
os.makedirs(processed_dir, exist_ok=True)
os.makedirs(figures_dir, exist_ok=True)

# Load datasets
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded train: {df_train.shape}")
print(f"Loaded val: {df_val.shape}")
print(f"Loaded test: {df_test.shape}")

# Define features
features = df_train.drop(['formula', 'target'], axis=1).columns

# Ensure features are float
df_train[features] = df_train[features].astype(float)
df_val[features] = df_val[features].astype(float)
df_test[features] = df_test[features].astype(float)

# Fit scaler on train
scaler = RobustScaler()
scaler.fit(df_train[features])

# Prepare data
X_train = scaler.transform(df_train[features])
y_train = df_train['target'].values
X_val = scaler.transform(df_val[features])
y_val = df_val['target'].values
X_test = scaler.transform(df_test[features])
y_test = df_test['target'].values

# Set a fixed seed for reproducibility
SEED = 42

# Use Cleanlab on train
model = HistGradientBoostingRegressor(random_state=SEED)
cl = CleanLearning(model, cv_n_folds=5, seed=SEED)
label_issues_df = cl.find_label_issues(X_train, y_train)

# Correct noisy targets in train
cleaned_y_train = np.where(label_issues_df['is_label_issue'], label_issues_df['predicted_label'], y_train)

# Compute threshold from clean residuals in train
clean_mask = ~label_issues_df['is_label_issue']
residuals_clean_signed = (label_issues_df['given_label'][clean_mask] - label_issues_df['predicted_label'][clean_mask])
mad = np.median(np.abs(residuals_clean_signed - np.median(residuals_clean_signed)))
robust_std = mad / 0.67448975
threshold = 3 * robust_std

# Fit model on train with cleaned y
model.fit(X_train, cleaned_y_train)

# Manage train
df_train_managed = df_train.copy()
outliers_mask_train = label_issues_df['is_label_issue']
df_train_managed['target'] = cleaned_y_train
outliers_train = df_train[outliers_mask_train]
print(f"Outliers in Train: {len(outliers_train)}")

# Function to manage val/test
def manage_outliers(df, X, y, dataset_name, model, threshold):
    y_pred = model.predict(X)
    residuals = np.abs(y - y_pred)
    outliers_mask = residuals > threshold
    managed_df = df.copy()
    managed_df['target'] = np.where(outliers_mask, y_pred, y)
    outliers = df[outliers_mask]
    print(f"Outliers in {dataset_name}: {len(outliers)}")
    return managed_df, outliers

# Manage val and test
df_val_managed, outliers_val = manage_outliers(df_val, X_val, y_val, "Validation", model, threshold)
df_test_managed, outliers_test = manage_outliers(df_test, X_test, y_test, "Test", model, threshold)

print(f"train shape after management: {df_train_managed.shape}")
print(f"val shape after management: {df_val_managed.shape}")
print(f"test shape after management: {df_test_managed.shape}")

# Save
outliers_train.to_csv(output_outliers_train_path, index=False)
outliers_val.to_csv(output_outliers_val_path, index=False)
outliers_test.to_csv(output_outliers_test_path, index=False)
df_train_managed.to_csv(output_no_outliers_train_path, index=False)
df_val_managed.to_csv(output_no_outliers_val_path, index=False)
df_test_managed.to_csv(output_no_outliers_test_path, index=False)
print("Saved")

# Plots for processed data
def plot_before_after(df_original, df_managed, dataset_name):
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.hist(df_original['target'], bins=20, alpha=0.7, label='Original')
    plt.title(f'{dataset_name} Original Target')
    plt.subplot(1, 2, 2)
    plt.hist(df_managed['target'], bins=20, alpha=0.7, label='Processed')
    plt.title(f'{dataset_name} Processed Target')
    plt.savefig(os.path.join(figures_dir, f'{dataset_name.lower()}_target_hist.png'))
    plt.close()

plot_before_after(df_train, df_train_managed, "Train")
plot_before_after(df_val, df_val_managed, "Val")
plot_before_after(df_test, df_test_managed, "Test")

def plot_residuals(X, y_original, y_managed, dataset_name, model):
    y_pred = model.predict(X)
    residuals_original = y_original - y_pred
    residuals_managed = y_managed - y_pred
    plt.figure(figsize=(10, 5))
    plt.scatter(y_pred, residuals_original, alpha=0.5, label='Original')
    plt.scatter(y_pred, residuals_managed, alpha=0.5, label='Processed')
    plt.axhline(0, color='r', linestyle='--')
    plt.title(f'{dataset_name} Residuals')
    plt.legend()
    plt.savefig(os.path.join(figures_dir, f'{dataset_name.lower()}_residuals.png'))
    plt.close()

plot_residuals(X_train, y_train, cleaned_y_train, "Train", model)
plot_residuals(X_val, y_val, df_val_managed['target'].values, "Val", model)
plot_residuals(X_test, y_test, df_test_managed['target'].values, "Test", model)