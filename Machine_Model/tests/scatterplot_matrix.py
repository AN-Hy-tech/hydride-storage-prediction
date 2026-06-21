# File: D:\Hydride_Machine_learning_project\Machine_Model\tests\scatterplot_matrix.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# تنظیم ظاهر Seaborn
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 8
plt.rcParams['ytick.labelsize'] = 8

# مسیرها
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Feature_Engineered_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Feature_Engineered_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Feature_Engineered_test.csv"
output_combined_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\database\combined_dataset.csv"
output_plot_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\data_eng_aug_analysis\Feature Eng\scatterplot_matrix.png"

# ایجاد پوشه برای خروجی‌ها
os.makedirs(os.path.dirname(output_combined_path), exist_ok=True)
os.makedirs(os.path.dirname(output_plot_path), exist_ok=True)

# خواندن دیتاست‌ها
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded train data with shape: {df_train.shape}")
print(f"Loaded validation data with shape: {df_val.shape}")
print(f"Loaded test data with shape: {df_test.shape}")

# ترکیب دیتاست‌ها
df_combined = pd.concat([df_train, df_val, df_test], ignore_index=True)
print(f"Combined dataset shape: {df_combined.shape}")

# محاسبه H2_W% (max) برای تحلیل
df_combined['H2_W% (max)'] = np.expm1(df_combined['log_H2_W% (max)'])

# ذخیره دیتاست ترکیبی
df_combined.to_csv(output_combined_path, index=False)
print(f"Combined dataset saved to {output_combined_path}")

# انتخاب همه ویژگی‌ها (به جز Composition)
features = [col for col in df_combined.columns if col not in ['Composition', 'log_H2_W% (max)']]
print(f"Selected features for scatterplot matrix: {features}")

print(f"train data with describe: {df_train['log_H2_W% (max)'].describe()}")
print(f"validation data with describe: {df_val['log_H2_W% (max)'].describe()}")
print(f"test data with describe: {df_test['log_H2_W% (max)'].describe()}")

# تولید Scatterplot Matrix با corner=True
g = sns.pairplot(
    df_combined[features], 
    diag_kind='kde', 
    corner=True,  # فقط نیمه بالایی ماتریس
    plot_kws={'alpha': 0.5, 's': 20, 'color': 'teal'}, 
    diag_kws={'color': 'navy', 'fill': True}
)
g.fig.set_size_inches(20, 20)
g.fig.suptitle('Scatterplot Matrix of All Features and H2_W% (max)', y=1.02, fontsize=16)

# تنظیم لیبل‌ها و چرخش فقط برای محورهای فعال
for ax in g.axes.flatten():
    if ax is not None:  # چک کردن None بودن محور
        ax.set_xlabel(ax.get_xlabel(), rotation=45, ha='right')
        ax.set_ylabel(ax.get_ylabel(), rotation=45, ha='right')

plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Scatterplot matrix saved to {output_plot_path}")