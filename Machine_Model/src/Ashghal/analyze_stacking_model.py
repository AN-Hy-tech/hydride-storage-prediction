# File: D:\Hydride_Machine_learning_project\Machine_Model\src\analyze_stacking_model.py
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os

# مسیرها
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_test.csv"
stacking_model_path = r"D:\Hydride_Machine_learning_project\Machine_Model\models\optimized_stacking\stacking_model.pkl"
results_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\optimized_optuna\stacking_analysis_results.csv"
plots_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\optimization\stacking_plots"

# ایجاد پوشه برای خروجی‌ها
os.makedirs(plots_dir, exist_ok=True)

# خواندن دیتاست‌ها
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded train data with shape: {df_train.shape}")
print(f"Loaded val data with shape: {df_val.shape}")
print(f"Loaded test data with shape: {df_test.shape}")

# جدا کردن ویژگی‌ها و تارگت
X_train = df_train.drop(['target', 'formula', 'H2_W% (max)'], axis=1, errors='ignore')  
y_train = df_train['target']
y_train_original = np.expm1(y_train)
X_val = df_val.drop(['target', 'formula', 'H2_W% (max)'], axis=1, errors='ignore')
y_val = df_val['target']
y_val_original = np.expm1(y_val)
X_test = df_test.drop(['target', 'formula', 'H2_W% (max)'], axis=1, errors='ignore')
y_test = df_test['target']
y_test_original = np.expm1(y_test)

# اسکیل کردن ویژگی‌ها
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

from sklearn.preprocessing import normalize
X_train_scaled = normalize(X_train_scaled)
X_val_scaled = normalize(X_val_scaled)
X_test_scaled = normalize(X_test_scaled)

# لود مدل استاکینگ
stacking_model = joblib.load(stacking_model_path)
print("Stacking model loaded successfully.")

# تابع ارزیابی
def evaluate_model(y_true, y_pred, y_original, is_log=True):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    if is_log:
        y_true_orig = np.expm1(y_true)
        y_pred_orig = np.expm1(y_pred)
        mae_orig = mean_absolute_error(y_true_orig, y_pred_orig)
        mse_orig = mean_squared_error(y_true_orig, y_pred_orig)
        r2_orig = r2_score(y_true_orig, y_pred_orig)
        return mae, mse, r2, mae_orig, mse_orig, r2_orig
    return mae, mse, r2, mae, mse, r2

# پیش‌بینی روی train, val, test
y_train_pred_log = stacking_model.predict(X_train_scaled)
y_val_pred_log = stacking_model.predict(X_val_scaled)
y_test_pred_log = stacking_model.predict(X_test_scaled)

# ارزیابی
train_mae_log, train_mse_log, train_r2_log, train_mae_orig, train_mse_orig, train_r2_orig = evaluate_model(y_train, y_train_pred_log, y_train_original, is_log=True)
val_mae_log, val_mse_log, val_r2_log, val_mae_orig, val_mse_orig, val_r2_orig = evaluate_model(y_val, y_val_pred_log, y_val_original, is_log=True)
test_mae_log, test_mse_log, test_r2_log, test_mae_orig, test_mse_orig, test_r2_orig = evaluate_model(y_test, y_test_pred_log, y_test_original, is_log=True)

# ذخیره نتایج
results_df = pd.DataFrame({
    'Set': ['Train', 'Validation', 'Test'],
    'R2_Log': [train_r2_log, val_r2_log, test_r2_log],
    'MSE_Log': [train_mse_log, val_mse_log, test_mse_log],
    'MAE_Log': [train_mae_log, val_mae_log, test_mae_log],
    'R2_Orig': [train_r2_orig, val_r2_orig, test_r2_orig],
    'MSE_Orig': [train_mse_orig, val_mse_orig, test_mse_orig],
    'MAE_Orig': [train_mae_orig, val_mae_orig, test_mae_orig]
})
results_df.to_csv(results_path, index=False)
print(f"Stacking analysis results saved to {results_path}")

# رسم نمودارهای عملکرد
plt.figure(figsize=(15, 12))

# نمودار 1: Scatter Plot پیش‌بینی در مقابل واقعی (Validation)
plt.subplot(2, 2, 1)
sns.scatterplot(x=y_val_original, y=np.expm1(y_val_pred_log))
plt.plot([y_val_original.min(), y_val_original.max()], [y_val_original.min(), y_val_original.max()], color='red', linestyle='--')
plt.title('Validation: Predictions vs Actual (Original Scale)')
plt.xlabel('Actual H2_W% (max)')
plt.ylabel('Predicted H2_W% (max)')

# نمودار 2: Scatter Plot پیش‌بینی در مقابل واقعی (Test)
plt.subplot(2, 2, 2)
sns.scatterplot(x=y_test_original, y=np.expm1(y_test_pred_log))
plt.plot([y_test_original.min(), y_test_original.max()], [y_test_original.min(), y_test_original.max()], color='red', linestyle='--')
plt.title('Test: Predictions vs Actual (Original Scale)')
plt.xlabel('Actual H2_W% (max)')
plt.ylabel('Predicted H2_W% (max)')

# نمودار 3: Distribution of Errors (Test)
errors_test = y_test_original - np.expm1(y_test_pred_log)
plt.subplot(2, 2, 3)
sns.histplot(errors_test, kde=True, bins=30)
plt.title('Distribution of Errors (Test, Original Scale)')
plt.xlabel('Error (Actual - Predicted)')
plt.ylabel('Frequency')

# نمودار 4: R2 Comparison
sets = ['Train', 'Validation', 'Test']
r2_values = [train_r2_orig, val_r2_orig, test_r2_orig]
plt.subplot(2, 2, 4)
sns.barplot(x=sets, y=r2_values)
plt.title('R2 Scores (Original Scale)')
plt.ylabel('R2')

plt.tight_layout()
plt.savefig(os.path.join(plots_dir, 'stacking_performance_plots.png'))
plt.close()

# نمودار اضافی: MAE Comparison
plt.figure(figsize=(10, 6))
mae_values = [train_mae_orig, val_mae_orig, test_mae_orig]
sns.barplot(x=sets, y=mae_values)
plt.title('MAE Scores (Original Scale)')
plt.ylabel('MAE')
plt.savefig(os.path.join(plots_dir, 'stacking_mae_plot.png'))
plt.close()

# نمودار اضافی: MSE Comparison
plt.figure(figsize=(10, 6))
mse_values = [train_mse_orig, val_mse_orig, test_mse_orig]
sns.barplot(x=sets, y=mse_values)
plt.title('MSE Scores (Original Scale)')
plt.ylabel('MSE')
plt.savefig(os.path.join(plots_dir, 'stacking_mse_plot.png'))
plt.close()

print(f"Performance plots saved to {os.path.join(plots_dir, 'stacking_performance_plots.png')}")
print(f"MAE plot saved to {os.path.join(plots_dir, 'stacking_mae_plot.png')}")
print(f"MSE plot saved to {os.path.join(plots_dir, 'stacking_mse_plot.png')}")

# ذخیره مدل (اگر نیاز باشد)
joblib.dump(stacking_model, stacking_model_path)
print(f"Stacking model saved to {stacking_model_path}")