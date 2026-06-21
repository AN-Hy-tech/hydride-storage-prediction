# File: D:\Hydride_Machine_learning_project\Machine_Model\src\analyze_top_models.py
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import learning_curve
from sklearn.preprocessing import RobustScaler
from sklearn.inspection import PartialDependenceDisplay
import os

# Paths
benchmark_results_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\benchmarked_model\benchmark_results.csv"
train_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_train.csv"
val_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_val.csv"
test_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\selected_test.csv"
models_dir = r"D:\Hydride_Machine_learning_project\Machine_Model\models\benchmark_models"
figures_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\figures\benchmark_analysis\Top_5"
os.makedirs(figures_path, exist_ok=True)

# Load benchmark to find top 5 using combined score
benchmark_df = pd.read_csv(benchmark_results_path)
max_mae = benchmark_df['Test_MAE_Orig'].max()
benchmark_df['Combined_Score'] = benchmark_df['Test_R2_Orig'] - (benchmark_df['Test_MAE_Orig'] / max_mae)
top_models = benchmark_df.sort_values(by='Combined_Score', ascending=False)['Model'].head(5).tolist()
print(f"Top 5 models (combined score): {top_models}")

# Load data
df_train = pd.read_csv(train_path)
df_val = pd.read_csv(val_path)
df_test = pd.read_csv(test_path)

X_train = df_train.drop(['target', 'formula'], axis=1, errors='ignore')
y_train = df_train['target']
y_train_original = np.expm1(y_train)
X_val = df_val.drop(['target', 'formula'], axis=1, errors='ignore')
y_val = df_val['target']
y_val_original = np.expm1(y_val)
X_test = df_test.drop(['target', 'formula'], axis=1, errors='ignore')
y_test = df_test['target']
y_test_original = np.expm1(y_test)

# Scale with RobustScaler
scaler = RobustScaler()
X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)
X_val_scaled = pd.DataFrame(scaler.transform(X_val), columns=X_val.columns)
X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

# Load models
loaded_models = {}
for model_name in top_models:
    model_path = os.path.join(models_dir, f"{model_name}_model.pkl")
    loaded_models[model_name] = joblib.load(model_path)
    print(f"Loaded {model_name} model")

# Function for subplots (learning curve, pred vs actual, residuals)
def plot_subplots(model, X_combined, y_combined, y_true, y_pred, model_name):
    fig, axs = plt.subplots(1, 3, figsize=(18, 6))
    
    # Learning Curve
    train_sizes, train_scores, val_scores = learning_curve(model, X_combined, y_combined, cv=5, n_jobs=-1, train_sizes=np.linspace(0.1, 1.0, 10), scoring='r2')
    axs[0].plot(train_sizes, np.mean(train_scores, axis=1), label='Train R²')
    axs[0].plot(train_sizes, np.mean(val_scores, axis=1), label='Val R²')
    axs[0].set_title(f'Learning Curve - {model_name}')
    axs[0].set_xlabel('Training Size')
    axs[0].set_ylabel('R²')
    axs[0].legend()
    axs[0].grid(True)
    
    # Pred vs Actual
    sns.scatterplot(x=y_true, y=y_pred, ax=axs[1])
    axs[1].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--')
    axs[1].set_title(f'Pred vs Actual (Test) - {model_name}')
    axs[1].set_xlabel('Actual (Orig)')
    axs[1].set_ylabel('Predicted (Orig)')
    
    # Residuals
    residuals = y_true - y_pred
    sns.histplot(residuals, kde=True, ax=axs[2])
    axs[2].set_title(f'Residuals (Test) - {model_name}')
    axs[2].set_xlabel('Residuals (Orig)')
    
    plt.tight_layout()
    plt.savefig(os.path.join(figures_path, f'{model_name}_subplots.png'))
    plt.close()

# Function to plot SHAP summary
def plot_shap_summary(model, X, model_name):
    if 'SVR' in model_name or 'KernelNN' in model_name:
        background = shap.kmeans(X, 50).data
        explainer = shap.KernelExplainer(model.predict, background)
    else:
        explainer = shap.Explainer(model, X)
    
    shap_values = explainer(X, check_additivity=False)
    shap.summary_plot(shap_values, X, show=False)
    plt.title(f'SHAP Summary - {model_name}')
    plt.savefig(os.path.join(figures_path, f'{model_name}_shap_summary.png'))
    plt.close()

# Function to plot feature importance
def plot_feature_importance(model, X, model_name):
    if hasattr(model, 'feature_importances_'):
        importance = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        plt.figure(figsize=(10, 8))
        sns.barplot(x=importance.values, hue=importance.index, legend=True)
        plt.title(f'Feature Importance - {model_name}')
        plt.xlabel('Importance')
        plt.savefig(os.path.join(figures_path, f'{model_name}_feature_importance.png'))
        plt.close()

# Function to plot partial dependence for top features
def plot_partial_dependence(model, X, features, model_name):
    fig, ax = plt.subplots(figsize=(12, 8))
    PartialDependenceDisplay.from_estimator(model, X, features, ax=ax)
    plt.title(f'Partial Dependence - {model_name}')
    plt.savefig(os.path.join(figures_path, f'{model_name}_partial_dependence.png'))
    plt.close()

# Analyze each top model
X_combined = pd.concat([X_train_scaled, X_val_scaled])
y_combined = pd.concat([y_train, y_val])
for model_name in top_models:
    model = loaded_models[model_name]
    
    # Predictions
    y_test_pred_log = model.predict(X_test_scaled)
    y_test_pred_orig = np.expm1(y_test_pred_log)
    
    # Subplots: Learning Curve, Pred vs Actual, Residuals
    plot_subplots(model, X_combined, y_combined, y_test_original, y_test_pred_orig, model_name)
    
    # SHAP
    plot_shap_summary(model, X_test_scaled, model_name)
    
    # Feature Importance
    plot_feature_importance(model, X_test, model_name)
    
    # Partial Dependence (top 3 features from importance)
    if hasattr(model, 'feature_importances_'):
        top_features = pd.Series(model.feature_importances_, index=X_test.columns).sort_values(ascending=False).head(3).index.tolist()
        plot_partial_dependence(model, X_test_scaled, top_features, model_name)

print("All analyses for top 5 models completed")