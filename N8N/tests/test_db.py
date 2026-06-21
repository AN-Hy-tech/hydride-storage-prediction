import sqlite3
import pytest

def get_null_counts(table_name, conn):
    """Check for NULL values in each column of the given table."""
    cursor = conn.cursor()
    # Get all column names except 'id' and 'timestamp'
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall() if row[1] not in ['id']]
    
    null_counts = {}
    for col in columns:
        cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE "{col}" IS NULL')
        null_counts[col] = cursor.fetchone()[0]
    return null_counts

def test_dataset_counts_and_nulls():
    conn = sqlite3.connect('database/storage.db')
    cursor = conn.cursor()
    
    # Check row counts
    tables = ['train_data', 'validation_data', 'test_data']
    row_counts = {}
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        row_counts[table] = count
        assert count > 0, f"{table} is empty"
    
    # Check for NULL values
    critical_columns = ['Composition', 'T', 'target', 'Thousand_Div_T_WtPercent']
    for table in tables:
        null_counts = get_null_counts(table, conn)
        for col, count in null_counts.items():
            if col in critical_columns:
                assert count == 0, f"{count} NULL values found in {table}.{col}"
            if count > 0:
                print(f"Warning: {count} NULL values found in {table}.{col}")
    
    conn.close()
    print(f"Train rows: {row_counts['train_data']}, Validation rows: {row_counts['validation_data']}, Test rows: {row_counts['test_data']}")

if __name__ == '__main__':
    pytest.main([__file__])
    
    
    
# import pytest
# import sqlite3
# from database.db_utils import add_storage_data, check_storage_data, delete_storage_data, add_dataset_data, check_dataset_data, get_dataset_features

# def test_storage_data():
#     # Add test data to storage_data
#     add_storage_data("MgH2", 300.0, [100.0, 50.0, 300.0], 5.6)
    
#     # Check data
#     features, capacity = check_storage_data("MgH2", 300.0)
#     assert features == [100.0, 50.0, 300.0]
#     assert capacity == 5.6
    
#     # Delete data
#     delete_storage_data("MgH2", 300.0)
    
#     # Check deletion
#     features, capacity = check_storage_data("MgH2", 300.0)
#     assert features is None
#     assert capacity is None

# def test_empty_storage_check():
#     features, capacity = check_storage_data("Unknown", 500.0)
#     assert features is None
#     assert capacity is None

# def test_dataset_data():
#     # Sample data for train_data
#     data_dict = {
#         "Composition": "MgH2",
#         "T": 300.0,
#         "target": 5.6,
#         "MagpieData_maximum_Number": 28.0,
#         "Thousand_Div_T_WtPercent": 8.028
#         # Add other required columns with default values if needed
#     }
    
#     # Add data to train_data
#     add_dataset_data("train_data", data_dict)
    
#     # Check data
#     result = check_dataset_data("train_data", "MgH2", 300.0)
#     assert result is not None
#     assert result[1] == "MgH2"  # Composition is second column (after id)
#     assert result[59] == 300.0  # T is in position 59
#     assert result[61] == 5.6    # target is in position 61

# def test_get_dataset_features():
#     # Check features from train_data
#     features = get_dataset_features("train_data", "MgH2", 300.0, ["MagpieData_maximum_Number", "Thousand_Div_T_WtPercent"])
#     assert features is not None
#     assert features[0] == 28.0  # MagpieData_maximum_Number
#     assert features[1] == 8.028 # Thousand_Div_T_WtPercent