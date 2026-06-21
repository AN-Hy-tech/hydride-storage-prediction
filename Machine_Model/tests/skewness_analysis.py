# File: D:\Hydride_Machine_learning_project\Machine_Model\tests\transformation_optimization.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import kendalltau, skew

# تنظیم ظاهر Seaborn
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 8
plt.rcParams['ytick.labelsize'] = 8

# مسیرها
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_features_test.csv"
output_train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Transformed_train.csv"
output_val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Transformed_val.csv"
output_test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\Transformed_test.csv"
output_plot_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\scatterplot pairmax\scatterplot_matrix_transformed_train.png"
output_transformation_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\transformation_report.csv"

# ایجاد پوشه برای خروجی‌ها
os.makedirs(os.path.dirname(output_train_path), exist_ok=True)
os.makedirs(os.path.dirname(output_plot_path), exist_ok=True)
os.makedirs(os.path.dirname(output_transformation_path), exist_ok=True)

# خواندن دیتاست‌ها
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

print(f"Loaded train data with shape: {df_train.shape}")
print(f"Loaded validation data with shape: {df_val.shape}")
print(f"Loaded test data with shape: {df_test.shape}")

# ترکیب دیتاست‌ها برای محاسبه تبدیل‌ها
df_combined = pd.concat([df_train, df_val, df_test], ignore_index=True)
print(f"Combined dataset shape: {df_combined.shape}")

# محاسبه H2_W% (max) برای تحلیل
df_combined['H2_W% (max)'] = np.expm1(df_combined['log_H2_W% (max)'])

# انتخاب همه ویژگی‌ها (به جز Composition و log_H2_W% (max))
features = [col for col in df_combined.columns if col not in ['Composition']]

# تابع برای آزمایش تبدیل‌ها با Kendall Tau
def evaluate_transformations(df, feature, target='log_H2_W% (max)'):
    results = []
    
    # بدون تبدیل
    corr, _ = kendalltau(df[feature], df[target])
    results.append(('None', corr, skew(df[feature])))
    
    # لگاریتم (برای مقادیر غیرمنفی)
    if df[feature].min() >= 0:
        transformed = np.log1p(df[feature])
        corr, _ = kendalltau(transformed, df[target])
        results.append(('Log', corr, skew(transformed)))
    
    # جذر (برای مقادیر غیرمنفی یا منفی با clip)
    transformed = np.sqrt(df[feature].clip(lower=0))
    corr, _ = kendalltau(transformed, df[target])
    results.append(('Sqrt', corr, skew(transformed)))
    
    # انعکاس و لگاریتم (برای چپ‌چول)
    max_val = df[feature].max()
    transformed = np.log1p(max_val - df[feature] + 1e-6)
    corr, _ = kendalltau(transformed, df[target])
    results.append(('Reflect_Log', corr, skew(transformed)))
    
    # تبدیل توان
    transformed = df[feature] ** 2
    corr, _ = kendalltau(transformed, df[target])
    results.append(('Power', corr, skew(transformed)))
    
    # انتخاب بهترین تبدیل (بالاترین مقدار مطلق همبستگی)
    best_transform = max(results, key=lambda x: abs(x[1]))
    return {
        'Feature': feature,
        'Best_Transform': best_transform[0],
        'Kendall_Correlation': best_transform[1],
        'Skewness': best_transform[2]
    }

# محاسبه بهترین تبدیل برای هر ویژگی
transformation_results = []
for feature in features:
    if feature != 'H2_W% (max)':
        result = evaluate_transformations(df_combined, feature)
        transformation_results.append(result)

# ذخیره گزارش تبدیل‌ها
transformation_df = pd.DataFrame(transformation_results)
transformation_df.to_csv(output_transformation_path, index=False)
print(f"Transformation report saved to {output_transformation_path}")

# تابع برای اعمال تبدیل‌ها روی دیتاست
def apply_transformations(df, transformation_results):
    df_transformed = df.copy()
    for result in transformation_results:
        feature = result['Feature']
        transform = result['Best_Transform']
        if feature in df_transformed.columns and feature != 'H2_W% (max)':
            if transform == 'Log':
                df_transformed[feature] = np.log1p(df[feature])
            elif transform == 'Sqrt':
                df_transformed[feature] = np.sqrt(df[feature].clip(lower=0))
            elif transform == 'Reflect_Log':
                max_val = df[feature].max()
                df_transformed[feature] = np.log1p(max_val - df[feature] + 1e-6)
            elif transform == 'Power':
                df_transformed[feature] = df[feature] ** 2
    return df_transformed

# اعمال تبدیل‌ها روی دیتاست‌های جداگانه
df_train_transformed = apply_transformations(df_train, transformation_results)
df_val_transformed = apply_transformations(df_val, transformation_results)
df_test_transformed = apply_transformations(df_test, transformation_results)

# محاسبه H2_W% (max) برای تحلیل
df_train_transformed['H2_W% (max)'] = np.expm1(df_train_transformed['log_H2_W% (max)'])
df_val_transformed['H2_W% (max)'] = np.expm1(df_val_transformed['log_H2_W% (max)'])
df_test_transformed['H2_W% (max)'] = np.expm1(df_test_transformed['log_H2_W% (max)'])

# ذخیره دیتاست‌های تبدیل‌شده
df_train_transformed.to_csv(output_train_path, index=False)
df_val_transformed.to_csv(output_val_path, index=False)
df_test_transformed.to_csv(output_test_path, index=False)
print(f"Transformed train data saved to {output_train_path}")
print(f"Transformed validation data saved to {output_val_path}")
print(f"Transformed test data saved to {output_test_path}")

# تولید Scatterplot Matrix برای دیتاست Train تبدیل‌شده
g = sns.pairplot(
    df_train_transformed[features], 
    diag_kind='kde', 
    corner=True, 
    plot_kws={'alpha': 0.5, 's': 20, 'color': 'teal'}, 
    diag_kws={'color': 'navy', 'fill': True}
)
g.fig.set_size_inches(20, 20)
g.fig.suptitle('Scatterplot Matrix of Transformed Train Features and H2_W% (max)', y=1.02, fontsize=16)

# تنظیم لیبل‌ها و چرخش
for ax in g.axes.flatten():
    if ax is not None:
        ax.set_xlabel(ax.get_xlabel(), rotation=45, ha='right')
        ax.set_ylabel(ax.get_ylabel(), rotation=45, ha='right')

plt.savefig(output_plot_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Transformed scatterplot matrix for train data saved to {output_plot_path}")