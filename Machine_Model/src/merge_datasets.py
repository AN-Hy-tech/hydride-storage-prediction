# File: D:\Hydride_Machine_learning_project\Machine_Model\src\merge_features.py
import pandas as pd
import numpy as np
import os
from sklearn.feature_selection import mutual_info_regression  # اضافه‌شده برای MI
from scipy.stats import shapiro  # اضافه‌شده برای normality
import matplotlib.pyplot as plt  # اضافه‌شده برای CDF
import seaborn as sns  # اضافه‌شده برای CDF

# Paths
matminer_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\preprocessed_features_matminer.csv"
cbfv_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\cbfv_extracted_features.csv"
jarvis_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\jarvis_filtered_features.csv"
output_merged_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\featurize_dataframe.csv"

# Create directory if not exists
os.makedirs(os.path.dirname(output_merged_path), exist_ok=True)

# Load datasets
df_matminer = pd.read_csv(matminer_path)
df_jarvis = pd.read_csv(jarvis_path)
df_cbfv = pd.read_csv(cbfv_path)

print(f"Loaded Matminer data with shape: {df_matminer.shape}")
print(f"Loaded CBFV data with shape: {df_cbfv.shape}")
print(f"Loaded Jarvis data with shape: {df_jarvis.shape}")

desired_columns_Miedema = [
    'Miedema_deltaH_ss_min','Miedema_deltaH_inter', 'Miedema_deltaH_amor'
]

missing_columns = [col for col in desired_columns_Miedema if col not in df_matminer.columns]
if missing_columns:
    print(f"Warning: The following columns are missing in df_matminer: {missing_columns}")
    raise ValueError(f"Missing columns in df_matminer: {missing_columns}")

# انتخاب ستون‌های مورد نظر
df_matminer_selected = df_matminer[desired_columns_Miedema]

# Reset indices to ensure alignment
df_matminer_selected = df_matminer_selected.reset_index(drop=True)
df_cbfv = df_cbfv.reset_index(drop=True)
df_jarvis = df_jarvis.reset_index(drop=True)

# Concatenate along columns (axis=1) to combine features
df_merged = pd.concat([df_jarvis, df_cbfv, df_matminer_selected], axis=1)

# Drop duplicates if any (after concat)
df_merged = df_merged.loc[:, ~df_merged.columns.duplicated()]

print(f"Merged data shape: {df_merged.shape}")

# Assume target is 'log_H2_W% (max)' or 'target' - adjust if needed
target_col = 'log_H2_W% (max)' if 'log_H2_W% (max)' in df_merged.columns else 'target'

# Correlation with target (Pearson) - Top 10 positive and negative
corr = df_merged.corr(numeric_only=True)[target_col].sort_values(ascending=False)
print("\nPearson Correlation with Target (Top 10 Positive):")
print(corr.head(10))
print("\nPearson Correlation with Target (Top 10 Negative):")
print(corr.tail(10))

# Mutual Information with target - Top 10
X = df_merged.select_dtypes(include=[np.number]).drop(columns=[target_col])
y = df_merged[target_col]
mi = mutual_info_regression(X, y)
mi_df = pd.DataFrame(mi, index=X.columns, columns=['Mutual Info']).sort_values(by='Mutual Info', ascending=False)
print("\nMutual Information with Target (Top 10):")
print(mi_df.head(10))

# Normality Test for target
stat, p = shapiro(df_merged[target_col].dropna())
print(f"\nShapiro-Wilk Normality Test for Target: Statistic={stat:.4f}, p-value={p:.4f}")

# Cumulative Distribution Function (CDF) Plot for target
plt.figure(figsize=(8, 6))
sns.ecdfplot(df_merged[target_col])
plt.title('Cumulative Distribution Function of Target')
plt.xlabel(target_col)
plt.ylabel('Cumulative Probability')
cdf_figure_path = os.path.join(os.path.dirname(output_merged_path), 'cdf_target.png')
plt.savefig(cdf_figure_path)
plt.close()
print(f"CDF figure saved to {cdf_figure_path}")

# Save merged data
df_merged.to_csv(output_merged_path, index=False)
print(f"Merged features saved to {output_merged_path}")
