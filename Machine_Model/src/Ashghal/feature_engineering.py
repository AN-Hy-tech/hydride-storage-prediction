# File: D:\Hydride_Machine_learning_project\Machine_Model\src\feature_engineering.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# مسیرها
# مسیرها
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_test.csv"
output_train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Feature_Engineered_train.csv"
output_val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Feature_Engineered_val.csv"
output_test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Feature_Engineered_test.csv"
figures_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\data_eng_aug_analysis"
reports_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\data_eng_aug_analysis"

# ایجاد پوشه برای خروجی‌ها
os.makedirs(os.path.dirname(output_train_path), exist_ok=True)
os.makedirs(figures_path, exist_ok=True)
os.makedirs(reports_path, exist_ok=True)

# خواندن دیتاست‌ها
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)
print(f"Loaded train data with shape: {df_train.shape}")
print(f"Loaded val data with shape: {df_val.shape}")
print(f"Loaded test data with shape: {df_test.shape}")

# بررسی ستون‌ها
print("Train columns:", df_train.columns.tolist())


# تابع برای Feature Engineering
def engineer_features(df):
    df = df.copy()
    
    # حذف ویژگی‌های با چولگی شدید و همبستگی/اهمیت پایین
    # df = df.drop([f for f in features_to_drop if f in df.columns], axis=1, errors='ignore')
    
    # محاسبه H2_W% (max) برای گزارش
    # df['H2_W% (max)'] = np.expm1(df['log_H2_W% (max)'])
    
    # # تبدیل دستی برای ویژگی‌های با چولگی شدید
    # if 'Mixing enthalpy' in df.columns:
    #     df['Mixing enthalpy_log'] = np.log1p(df['Mixing enthalpy'].clip(lower=0))
    # if 'temperature(K)' in df.columns:
    #     df['temperature(K)_log'] = np.log1p(df['temperature(K)'])
    # if 'Miedema_deltaH_ss_min' in df.columns:
    #     df['Miedema_deltaH_ss_min_sqrt'] = np.square(df['Miedema_deltaH_ss_min'])


    if all(col in df.columns for col in ['temperature(K)', 'Miedema_deltaH_ss_min']):
        df['Thermal_Enthalpy_Interaction'] = df['temperature(K)'] * df['Miedema_deltaH_ss_min']
    if all(col in df.columns for col in ['MagpieData mean NsValence', 'MagpieData mean Number']):
        df['Valence_Electron_Concentration'] = df['MagpieData mean NsValence'] / df['MagpieData mean Number']
    if all(col in df.columns for col in ['MagpieData range Electronegativity', 'Shear modulus local mismatch']):
        df['Electromechanical_Mismatch'] = df['MagpieData range Electronegativity'] * df['Shear modulus local mismatch']
    if all(col in df.columns for col in ['MagpieData avg_dev CovalentRadius', 'MagpieData avg_dev AtomicWeight']):
        df['Atomic_Deviation_Ratio'] = df['MagpieData avg_dev CovalentRadius'] / df['MagpieData avg_dev AtomicWeight']
    if 'MagpieData range Electronegativity' in df.columns:
        df['Squared_Electronegativity_Range'] = df['MagpieData range Electronegativity'] ** 2
    if all(col in df.columns for col in ['MagpieData mean Column', 'MagpieData mean NsValence']):
        df['Group_Valence_Product'] = df['MagpieData mean Column'] * df['MagpieData mean NsValence']
    if all(col in df.columns for col in ['temperature(K)', 'MagpieData mean MendeleevNumber']):
        df['Temperature_Normalized_by_Mendeleev'] = df['temperature(K)'] / df['MagpieData mean MendeleevNumber']
    if all(col in df.columns for col in ['Miedema_deltaH_ss_min', 'Shear modulus local mismatch']):
        df['Mismatch_Enthalpy_Ratio'] = df['Miedema_deltaH_ss_min'] / df['Shear modulus local mismatch']
    if 'MagpieData avg_dev CovalentRadius' in df.columns:
        df['Covalent_Deviation_Squared'] = df['MagpieData avg_dev CovalentRadius'] ** 2
    if all(col in df.columns for col in ['MagpieData avg_dev AtomicWeight', 'MagpieData mean Number']):
        df['Atomic_Weight_Deviation_Product'] = df['MagpieData avg_dev AtomicWeight'] * df['MagpieData mean Number']
        
    
    # حذف H2_W% (max) برای ذخیره داده‌ها
    # df = df.drop(columns=['H2_W% (max)'], axis=1, errors='ignore') # 'Miedema_deltaH_ss_min', 'Mixing enthalpy', 'temperature(K)',
    
    return df

# اعمال Feature Engineering
df_train_engineered = engineer_features(df_train.copy())
df_val_engineered = engineer_features(df_val.copy())
df_test_engineered = engineer_features(df_test.copy())

print(f"Loaded train data with shape: {df_train_engineered.shape}")
print(f"Loaded val data with shape: {df_val_engineered.shape}")
print(f"Loaded test data with shape: {df_test_engineered.shape}")

# ذخیره داده‌های مهندسی‌شده
df_train_engineered.to_csv(output_train_path, index=False)
df_val_engineered.to_csv(output_val_path, index=False)
df_test_engineered.to_csv(output_test_path, index=False)
print(f"Engineered train data saved to {output_train_path}")
print(f"Engineered val data saved to {output_val_path}")
print(f"Engineered test data saved to {output_test_path}")

new_features = [col for col in df_train_engineered.columns if col not in df_train.columns and col != 'log_H2_W% (max)']
corr_engineered = df_train_engineered[new_features + ['log_H2_W% (max)']].corr()['log_H2_W% (max)'].drop('log_H2_W% (max)')
corr_engineered_df = pd.DataFrame({'Correlation': corr_engineered}).reset_index()
corr_engineered_df.to_csv(os.path.join(reports_path, 'new_features_correlation.csv'), index=False)

plt.figure(figsize=(12, 8))
sns.barplot(x='Correlation', hue='index', data=corr_engineered_df, palette='viridis', legend=True)
plt.title('Correlation of New Features with log_H2_W% (max)')
plt.xlabel('Correlation')
plt.ylabel('New Features')
plt.savefig(os.path.join(figures_path, 'new_features_correlation_plot.png'))
plt.close()

print(f"New features correlation saved to {reports_path}\\new_features_correlation.csv")
print(f"New features correlation plot saved to {figures_path}\\new_features_correlation_plot.png")