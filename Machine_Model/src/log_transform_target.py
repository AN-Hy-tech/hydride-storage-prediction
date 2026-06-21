# File: src/log_transform_target.py
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import shapiro, skew, kurtosis 

# Paths
input_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\raw\hydride_data.csv" 
output_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\raw\hydride_prefeaturizing.csv" 
figures_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\raw_data_analysis"
os.makedirs(figures_path, exist_ok=True)  # Ensure the directory exists

df = pd.read_csv(input_path)
print(f"Loaded data with shape: {df.shape}")

# Before transformation checks - Normality and Distribution
original_col = 'H2_W% (max)'
print("\nBefore Log Transformation - Normality and Distribution Checks:")
stat, p = shapiro(df[original_col].dropna())
print(f'Shapiro-Wilk Test: Statistic={stat:.4f}, p-value={p:.4f}')
print(f'Skewness: {skew(df[original_col].dropna()):.4f}')
print(f'Kurtosis: {kurtosis(df[original_col].dropna()):.4f}')

# Plot histogram before log transformation
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
sns.histplot(df['H2_W% (max)'], kde=True, bins=30)
plt.title('Distribution of H2_W% (max) Before Log Transformation')
plt.xlabel('H2_W% (max)')
plt.ylabel('Frequency')

# Apply log transformation
df['log_H2_W% (max)'] = np.log1p(df['H2_W% (max)'])
df = df.drop('H2_W% (max)', axis=1) 

# After transformation checks - Normality and Distribution
transformed_col = 'log_H2_W% (max)'
print("\nAfter Log Transformation - Normality and Distribution Checks:")
stat, p = shapiro(df[transformed_col].dropna())
print(f'Shapiro-Wilk Test: Statistic={stat:.4f}, p-value={p:.4f}')
print(f'Skewness: {skew(df[transformed_col].dropna()):.4f}')
print(f'Kurtosis: {kurtosis(df[transformed_col].dropna()):.4f}')

# Plot histogram after log transformation
plt.subplot(1, 2, 2)
sns.histplot(df['log_H2_W% (max)'], kde=True, bins=30)
plt.title('Distribution of log_H2_W% (max) After Log Transformation')
plt.xlabel('log_H2_W% (max)')
plt.ylabel('Frequency')

# Save the figure
figure_path = os.path.join(figures_path, 'figure_log_transform_histograms.png')
plt.tight_layout()
plt.savefig(figure_path)
plt.close()
print(f"Figure saved to {figure_path}")

df.to_csv(output_path, index=False)
print(f"Data with log-transformed target saved to {output_path}")
print("First 5 rows after transformation:")
print(df.head())