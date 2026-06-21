import sqlite3
import pytest

def test_dataset_schema():
    conn = sqlite3.connect('database/storage.db')
    cursor = conn.cursor()
    
    tables = ['train_data', 'validation_data', 'test_data']
    forbidden_columns = ['H_M_Ratio', 'Thousand_Div_T_WtPercent']
    
    for table in tables:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Check that forbidden columns are not present
        for col in forbidden_columns:
            assert col not in columns, f"Column {col} found in {table}"
        
        # Verify some expected columns are present
        expected_columns = ['Composition', 'T', 'target']
        for col in expected_columns:
            assert col in columns, f"Column {col} missing in {table}"
    
    conn.close()
    print("Database schema test passed: H_M_Ratio and Thousand_Div_T_WtPercent not found.")

if __name__ == '__main__':
    pytest.main([__file__])