import sqlite3
import pandas as pd
import os

def import_csv_to_db(csv_file, table_name, db_path='database/storage.db'):
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    # Replace spaces and special characters in column names
    df.columns = [col.replace(' ', '_').replace('%', 'percent') for col in df.columns]
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert data into table
    columns = ', '.join(f'"{col}"' for col in df.columns)
    placeholders = ', '.join(['?'] * len(df.columns))
    insert_query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
    
    # Convert dataframe to list of tuples
    data = [tuple(row) for row in df.values]
    
    # Execute insert
    cursor.executemany(insert_query, data)
    
    conn.commit()
    conn.close()
    print(f"Imported {len(data)} rows into {table_name} from {csv_file}")

if __name__ == '__main__':
    base_path = 'D:/Hydride_Machine_learning_project/N8N/data'
    
    # Import train, validation, and test datasets
    import_csv_to_db(os.path.join(base_path, 'Feature_Engineered_Train.csv'), 'train_data')
    import_csv_to_db(os.path.join(base_path, 'Feature_Engineered_Validation.csv'), 'validation_data')
    import_csv_to_db(os.path.join(base_path, 'Feature_Engineered_Test.csv'), 'test_data')