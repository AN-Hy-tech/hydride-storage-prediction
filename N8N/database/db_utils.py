import sqlite3
import json

def add_storage_data(composition, temperature, features, capacity, db_path='database/storage.db'):
    """Add user input and prediction to storage_data table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Convert features to JSON
    features_json = json.dumps(features)
    
    # Insert data
    cursor.execute('''
        INSERT INTO storage_data (composition, temperature, features, capacity)
        VALUES (?, ?, ?, ?)
    ''', (composition, temperature, features_json, capacity))
    
    conn.commit()
    conn.close()

def check_storage_data(composition, temperature, db_path='database/storage.db'):
    """Check if data exists in storage_data table based on composition and temperature."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT features, capacity FROM storage_data
        WHERE composition = ? AND temperature = ?
    ''', (composition, temperature))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        features, capacity = result
        return json.loads(features), capacity
    return None, None

def delete_storage_data(composition, temperature, db_path='database/storage.db'):
    """Delete data from storage_data table based on composition and temperature."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM storage_data
        WHERE composition = ? AND temperature = ?
    ''', (composition, temperature))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    if rows_affected > 0:
        print(f"Deleted {rows_affected} row(s) for composition {composition} and temperature {temperature} from storage_data.")
    else:
        print(f"No data found for composition {composition} and temperature {temperature} in storage_data.")

def add_dataset_data(table_name, data_dict, db_path='database/storage.db'):
    """Add data to train_data, validation_data, or test_data table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Prepare columns and values
    columns = ', '.join(f'"{col}"' for col in data_dict.keys())
    placeholders = ', '.join(['?'] * len(data_dict))
    values = tuple(data_dict.values())
    
    # Insert data
    insert_query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
    cursor.execute(insert_query, values)
    
    conn.commit()
    conn.close()

def check_dataset_data(composition, temperature, db_path='database/storage.db'):
    """Check if data exists in dataset tables and return target capacity if found."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['train_data', 'validation_data', 'test_data']
    for table in tables:
        cursor.execute(f'''
            SELECT target FROM {table}
            WHERE Composition = ? AND T = ?
        ''', (composition, temperature))
        result = cursor.fetchone()
        if result:
            conn.close()
            return result[0]  # Return target capacity
    conn.close()
    return None

def get_dataset_features(table_name, composition, temperature, feature_columns, db_path='database/storage.db'):
    """Retrieve specified features from the dataset table for a given composition and temperature."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns = ', '.join(f'"{col}"' for col in feature_columns)
    query = f'SELECT {columns} FROM {table_name} WHERE Composition = ? AND T = ?'
    cursor.execute(query, (composition, temperature))
    
    result = cursor.fetchone()
    conn.close()
    
    return result if result else None
