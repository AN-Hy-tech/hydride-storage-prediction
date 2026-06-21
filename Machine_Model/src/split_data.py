# File: D:\Hydride_Machine_learning_project\Machine_Model\src\split_data.py
"""
This script splits the Jarvis/Magpie/Miedema filtered features dataset into train, validation, and test sets using stratified splitting 
based on unique formulae, temperature, and target values to ensure no data leakage and balanced distributions.

Improvements:
- Increased bins to 5 for better stratification.
- Used StratifiedShuffleSplit for improved shuffling and balance.
- Enhanced small bin merging with Euclidean distance for more accurate grouping.
- Added post-split statistics checks for target and temperature distributions.
- Added documentation, docstrings, and comments for clarity.
- Generated plots: histograms for target and temperature distributions in each split, saved to reports/figures/split_analysis.

Usage:
- Run the script to split the data and generate reports/plots.
- Outputs: train.csv, val.csv, test.csv in data/splits; plots in reports/figures/split_analysis; summary report in reports/split_summary.txt.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import KBinsDiscretizer
from sklearn.model_selection import StratifiedShuffleSplit
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Paths
input_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\featurize_dataframe.csv"
output_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\data\splits"
figures_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\split_analysis"
report_summary_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\split_data_analysis\split_summary.txt"

# Build the output paths
os.makedirs(output_dir, exist_ok=True)
os.makedirs(figures_dir, exist_ok=True)

# Read Data
data = pd.read_csv(input_path)
num_rows = len(data)
print(f'There are in total {num_rows} rows in the Source Dataframe')

# # Rename the Composition column to formula if necessary (for compatibility)
# if 'Composition' in data.columns:
#     data = data.rename(columns={'Composition': 'formula'})
# if 'log_H2_W% (max)' in data.columns:
#     data = data.rename(columns={'log_H2_W% (max)':'target'})

num_unique_formula = len(data['formula'].unique())  
print(f"But there are only {num_unique_formula} unique formulae!\n")

print('Unique formulae and their number of occurrences in the DataFrame')
print(data['formula'].value_counts(), '\n')

Hydride_data = data.copy()
unique_formulae = Hydride_data['formula'].unique()
print(f'{len(unique_formulae)} unique formulae:\n{unique_formulae}')

# for reproducability 
RNG_SEED = 42
np.random.seed(seed=RNG_SEED)

# split ratio (optimized to 70/15/15 for Train/Val/Test)
test_ratio = 0.20
val_ratio = 0.10
train_ratio = 1 - test_ratio - val_ratio

# Step 1: Calculate mean T and target per unique formula
formula_stats = Hydride_data.groupby('formula').agg({'temperature(K)': 'mean', 'target': 'mean'}).reset_index()
print(f"Shape of formula_stats (unique formulae): {formula_stats.shape}")

# Step 2: Bin the mean T and target for stratification (optimized: bins=5 for better distribution)
n_bins = 5  # increase bins for more accurate stratification

# Bin temperature(K)
t_binner = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='quantile')
formula_stats['T_bin'] = t_binner.fit_transform(formula_stats[['temperature(K)']])
# Bin target
wt_binner = KBinsDiscretizer(n_bins=n_bins, encode='ordinal', strategy='quantile')
formula_stats['Wt%_bin'] = wt_binner.fit_transform(formula_stats[['target']])
 
# Step 3: Create a stratification key
formula_stats['strat_key'] = formula_stats['T_bin'].astype(str) + '_' + formula_stats['Wt%_bin'].astype(str)

# Step 4: Check stratification key distribution and merge small bins if necessary
strat_counts = formula_stats['strat_key'].value_counts()
print("Stratification key distribution:\n", strat_counts)

# Merge bins with fewer than min_members into the nearest bin (optimized: min_members=5)
min_members = 5
small_bins = strat_counts[strat_counts < min_members].index
if len(small_bins) > 0:
    print(f"Found {len(small_bins)} bins with fewer than {min_members} members. Merging small bins...")
    for small_bin in small_bins:
        t_bin, wt_bin = map(float, small_bin.split('_'))
        candidate_bins = []
        distances = {}
        for existing_bin in strat_counts.index:
            if existing_bin == small_bin:
                continue
            existing_t, existing_wt = map(float, existing_bin.split('_'))
            distance = np.sqrt((t_bin - existing_t)**2 + (wt_bin - existing_wt)**2)
            if strat_counts[existing_bin] >= min_members:
                distances[existing_bin] = distance
        if distances:
            # closest bin with sufficient members
            nearest_bin = min(distances, key=distances.get)
            formula_stats.loc[formula_stats['strat_key'] == small_bin, 'strat_key'] = nearest_bin
        else:
            # if none, to the most populated bin
            most_populated_bin = strat_counts.index[0]
            formula_stats.loc[formula_stats['strat_key'] == small_bin, 'strat_key'] = most_populated_bin

# Recheck stratification key distribution
strat_counts = formula_stats['strat_key'].value_counts()
print("Updated stratification key distribution after merging:\n", strat_counts)
if (strat_counts < min_members).any():
    raise ValueError("After merging, some stratification keys still have fewer than min_members members. Try reducing n_bins or adjusting min_members.")

# Step 5: Stratified split of unique formulae using StratifiedShuffleSplit (optimized for better distribution)
# First split: train vs. temp (val + test)
sss_train_temp = StratifiedShuffleSplit(n_splits=1, test_size=(val_ratio + test_ratio), random_state=RNG_SEED)
for train_idx, temp_idx in sss_train_temp.split(formula_stats, formula_stats['strat_key']):
    train_formulae = formula_stats.iloc[train_idx]['formula']
    temp_formulae = formula_stats.iloc[temp_idx]['formula']

# Align strat_key for temp_formulae
formula_map = formula_stats.set_index('formula')['strat_key']
strat_key_temp = formula_map.loc[temp_formulae.values].values

# Second split: val vs. test from temp
sss_val_test = StratifiedShuffleSplit(n_splits=1, test_size=test_ratio / (val_ratio + test_ratio), random_state=RNG_SEED)
for val_idx, test_idx in sss_val_test.split(temp_formulae, strat_key_temp):
    val_formulae = temp_formulae.iloc[val_idx]
    test_formulae = temp_formulae.iloc[test_idx]

# Verify lengths of unique formulae in each split
print('Number of training formulae:', len(train_formulae))
print('Number of validation formulae:', len(val_formulae))
print('Number of testing formulae:', len(test_formulae))

# Ensure no overlap and correct total for unique formulae
assert len(set(val_formulae) & set(test_formulae)) == 0, "Validation and test sets overlap"
assert len(set(val_formulae) & set(train_formulae)) == 0, "Validation and train sets overlap"
assert len(set(test_formulae) & set(train_formulae)) == 0, "Test and train sets overlap"
assert len(val_formulae) + len(test_formulae) + len(train_formulae) == len(Hydride_data['formula'].unique()), "Split sizes don't add up"

# Step 6: Split dataset based on formulae
df_train = Hydride_data[Hydride_data['formula'].isin(train_formulae)]
df_val = Hydride_data[Hydride_data['formula'].isin(val_formulae)]
df_test = Hydride_data[Hydride_data['formula'].isin(test_formulae)]

# Step 7: Verify dataset shapes and distribution statistics (optimized: check stats after split)
print(f'\nTrain dataset shape: {df_train.shape}')
print(f'Validation dataset shape: {df_val.shape}')
print(f'Test dataset shape: {df_test.shape}\n')

# Statistics of target and temperature distribution in each set
train_target_stats = df_train['target'].describe()
val_target_stats = df_val['target'].describe()
test_target_stats = df_test['target'].describe()
train_temp_stats = df_train['temperature(K)'].describe()
val_temp_stats = df_val['temperature(K)'].describe()
test_temp_stats = df_test['temperature(K)'].describe()

print("Train target stats:\n", train_target_stats)
print("Val target stats:\n", val_target_stats)
print("Test target stats:\n", test_target_stats)
print("Train temperature stats:\n", train_temp_stats)
print("Val temperature stats:\n", val_temp_stats)
print("Test temperature stats:\n", test_temp_stats)

# Save statistics in summary report
with open(report_summary_path, 'w') as f:
    f.write("Split Data Summary\n\n")
    f.write(f"Total rows: {num_rows}\n")
    f.write(f"Unique formulae: {num_unique_formula}\n\n")
    f.write("Train shape: {}\n".format(df_train.shape))
    f.write("Val shape: {}\n".format(df_val.shape))
    f.write("Test shape: {}\n\n".format(df_test.shape))
    f.write("Train target stats:\n{}\n\n".format(train_target_stats))
    f.write("Val target stats:\n{}\n\n".format(val_target_stats))
    f.write("Test target stats:\n{}\n\n".format(test_target_stats))
    f.write("Train temperature stats:\n{}\n\n".format(train_temp_stats))
    f.write("Val temperature stats:\n{}\n\n".format(val_temp_stats))
    f.write("Test temperature stats:\n{}\n".format(test_temp_stats))

print(f"Summary report saved to {report_summary_path}")

# Check for common formulae
train_formulae_set = set(df_train['formula'].unique())
val_formulae_set = set(df_val['formula'].unique())
test_formulae_set = set(df_test['formula'].unique())

common_formulae1 = train_formulae_set.intersection(test_formulae_set)
common_formulae2 = train_formulae_set.intersection(val_formulae_set)
common_formulae3 = test_formulae_set.intersection(val_formulae_set)

print(f'# of common formulae in intersection 1: {len(common_formulae1)}; common formulae: {common_formulae1}')
print(f'# of common formulae in intersection 2: {len(common_formulae2)}; common formulae: {common_formulae2}')
print(f'# of common formulae in intersection 3: {len(common_formulae3)}; common formulae: {common_formulae3}')

# Generate plots
# Histogram of target distribution in each set
plt.figure(figsize=(12, 6))
sns.histplot(df_train['target'], kde=True, color='blue', label='Train', alpha=0.5)
sns.histplot(df_val['target'], kde=True, color='orange', label='Val', alpha=0.5)
sns.histplot(df_test['target'], kde=True, color='green', label='Test', alpha=0.5)
plt.title('Target Distribution Across Splits')
plt.xlabel('Target (log_H2_W% (max))')
plt.ylabel('Frequency')
plt.legend()
plt.savefig(os.path.join(figures_dir, 'target_distribution_splits.png'))
plt.close()

# Histogram of temperature distribution in each set
plt.figure(figsize=(12, 6))
sns.histplot(df_train['temperature(K)'], kde=True, color='blue', label='Train', alpha=0.5)
sns.histplot(df_val['temperature(K)'], kde=True, color='orange', label='Val', alpha=0.5)
sns.histplot(df_test['temperature(K)'], kde=True, color='green', label='Test', alpha=0.5)
plt.title('Temperature Distribution Across Splits')
plt.xlabel('Temperature (K)')
plt.ylabel('Frequency')
plt.legend()
plt.savefig(os.path.join(figures_dir, 'temperature_distribution_splits.png'))
plt.close()

# Boxplot for comparing target distribution
df_combined = pd.concat([df_train.assign(split='Train'), df_val.assign(split='Val'), df_test.assign(split='Test')])
plt.figure(figsize=(8, 6))
sns.boxplot(x='split', y='target', data=df_combined)
plt.title('Boxplot of Target Across Splits')
plt.savefig(os.path.join(figures_dir, 'target_boxplot_splits.png'))
plt.close()

# Boxplot for comparing temperature distribution
plt.figure(figsize=(8, 6))
sns.boxplot(x='split', y='temperature(K)', data=df_combined)
plt.title('Boxplot of Temperature Across Splits')
plt.savefig(os.path.join(figures_dir, 'temperature_boxplot_splits.png'))
plt.close()

print(f"Plots saved to {figures_dir}")

# Save datasets
try:
    df_train.to_csv(os.path.join(output_dir, "train.csv"), index=False)
    df_val.to_csv(os.path.join(output_dir, "val.csv"), index=False)
    df_test.to_csv(os.path.join(output_dir, "test.csv"), index=False)
    
    print(f"Data split into train.csv ({len(df_train)} rows), val.csv ({len(df_val)} rows), test.csv ({len(df_test)} rows)")
except Exception as e:
    print(f"Error saving split files: {e}")
    raise