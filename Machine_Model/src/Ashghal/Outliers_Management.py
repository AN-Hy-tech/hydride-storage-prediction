# Outliers_Management.py
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import RobustScaler
from sklearn.linear_model import TheilSenRegressor

# Paths
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits\test.csv"
output_outliers_train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\outliers_train.csv"
output_outliers_val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\outliers_val.csv"
output_outliers_test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\outliers_test.csv"
output_no_outliers_train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\no_outliers_train.csv"
output_no_outliers_val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\no_outliers_val.csv"
output_no_outliers_test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\augmented\no_outliers_test.csv"
figures_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\outliers_analysis"

# Create directories
os.makedirs(os.path.dirname(output_outliers_train_path), exist_ok=True)
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

# Fit scaler and quantiles on train
scaler = RobustScaler()
scaler.fit(df_train[features])

train_quantiles = df_train[features].quantile([0.05, 0.95])

# Scale train and fit TheilSenRegressor
X_train_scaled = scaler.transform(df_train[features])
theilsen = TheilSenRegressor(max_iter=20000)
theilsen.fit(X_train_scaled, df_train['target'])

# Compute threshold from train residuals using MAD for robustness
y_pred_train = theilsen.predict(X_train_scaled)
residuals_train_signed = df_train['target'] - y_pred_train
mad = np.median(np.abs(residuals_train_signed - np.median(residuals_train_signed)))
robust_std = mad / 0.67448975  # Approximate normal std
threshold = 3 * robust_std

# Function to identify and manage outliers using train-fitted models and quantiles
def identify_and_manage_outliers(df, dataset_name, scaler, theilsen, threshold, train_quantiles):
    X_scaled = scaler.transform(df[features])
    y_pred = theilsen.predict(X_scaled)
    residuals_signed = df['target'] - y_pred
    residuals = np.abs(residuals_signed)
    outliers_mask = residuals > threshold
    outliers = df[outliers_mask]
    
    managed_df = df.copy()
    for col in features:
        q1 = train_quantiles.loc[0.05, col]
        q3 = train_quantiles.loc[0.95, col]
        managed_df.loc[outliers_mask, col] = np.clip(managed_df.loc[outliers_mask, col], q1, q3)
    
    print(f"Outliers in {dataset_name}: {len(outliers)}")
    return managed_df, outliers

# Manage outliers
df_train_managed, outliers_train = identify_and_manage_outliers(df_train, "Train", scaler, theilsen, threshold, train_quantiles)
df_val_managed, outliers_val = identify_and_manage_outliers(df_val, "Validation", scaler, theilsen, threshold, train_quantiles)
df_test_managed, outliers_test = identify_and_manage_outliers(df_test, "Test", scaler, theilsen, threshold, train_quantiles)

print(f"train shape after outlier management : {df_train_managed.shape}")
print(f"val shape after outlier management : {df_val_managed.shape}")
print(f"test shape after outlier management : {df_test_managed.shape}")

# Save
outliers_train.to_csv(output_outliers_train_path, index=False)
outliers_val.to_csv(output_outliers_val_path, index=False)
outliers_test.to_csv(output_outliers_test_path, index=False)
df_train_managed.to_csv(output_no_outliers_train_path, index=False)
df_val_managed.to_csv(output_no_outliers_val_path, index=False)
df_test_managed.to_csv(output_no_outliers_test_path, index=False)
print("Saved")