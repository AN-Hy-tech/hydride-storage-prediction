import pandas as pd
import numpy as np
from CBFV.composition import generate_features
import os

raw_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\raw\hydride_prefeaturizing.csv" 
output_extracted_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\cbfv_extracted_features.csv"
# output_filtered_path = r"D:\Hydride_Machine_learning_project\Machine_Model\data\processed\cbfv_filtered_features.csv"
# report_path = r"D:\Hydride_Machine_learning_project\Machine_Model\reports\data\cbfv\cbfv_filter_report.csv"

os.makedirs(os.path.dirname(output_extracted_path), exist_ok=True)
# os.makedirs(os.path.dirname(report_path), exist_o=True)

df_raw = pd.read_csv(raw_path)

print(f"Loaded raw data with shape: {df_raw.shape}")
print("Raw columns:", df_raw.columns.tolist())

object_cols = df_raw.select_dtypes(include='object').columns
cols_to_drop = [col for col in object_cols if col != 'Composition']
df_raw = df_raw.drop(columns=cols_to_drop)
print(f"Columns after dropping non-composition objects: {df_raw.columns.tolist()}")

rename_dict = {'log_H2_W% (max)' : 'target',
               'Composition' : 'formula'}
df_raw = df_raw.rename(columns=rename_dict)
print('\nDataFrame column names after renaming:')
print(df_raw.columns)


X_raw, y_raw, formulae_raw, skipped_raw = generate_features(df_raw, elem_prop='magpie', drop_duplicates=False, extend_features=True)

df_extracted = pd.concat([pd.DataFrame(formulae_raw, columns=['formula']), X_raw, pd.DataFrame(y_raw, columns=['target'])], axis=1)

df_extracted.to_csv(output_extracted_path, index=False)
print(f"Jarvis features extracted and saved to {output_extracted_path}")
print(f"Extracted shape: {df_extracted.shape}")

