import sqlite3

def init_database():
    conn = sqlite3.connect('database/storage.db')
    cursor = conn.cursor()

    # Create table for user inputs and predictions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS storage_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            composition TEXT NOT NULL,
            temperature REAL NOT NULL,
            features TEXT,  -- Scaled features as JSON
            capacity REAL,  -- Predicted capacity (wt%)
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create tables for train, validation, and test datasets
    create_dataset_table = '''
        CREATE TABLE IF NOT EXISTS {} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Composition TEXT NOT NULL,
            MagpieData_maximum_Number REAL,
            MagpieData_minimum_Number REAL,
            MagpieData_mean_Number REAL,
            MagpieData_avg_dev_Number REAL,
            MagpieData_range_Number REAL,
            MagpieData_mode_Number REAL,
            MagpieData_maximum_AtomicWeight REAL,
            MagpieData_minimum_AtomicWeight REAL,
            MagpieData_mean_AtomicWeight REAL,
            MagpieData_mode_AtomicWeight REAL,
            MagpieData_avg_dev_AtomicWeight REAL,
            MagpieData_range_AtomicWeight REAL,
            Miedema_deltaH_inter REAL,
            Miedema_deltaH_ss_min REAL,
            Mixing_enthalpy REAL,
            Configuration_entropy REAL,
            Lambda_entropy REAL,
            Mean_cohesive_energy REAL,
            Shear_modulus_mean REAL,
            Shear_modulus_local_mismatch REAL,
            MagpieData_maximum_MeltingT REAL,
            MagpieData_minimum_MeltingT REAL,
            MagpieData_mean_MeltingT REAL,
            MagpieData_mode_MeltingT REAL,
            MagpieData_avg_dev_MeltingT REAL,
            MagpieData_range_MeltingT REAL,
            MagpieData_maximum_NValence REAL,
            MagpieData_minimum_NValence REAL,
            MagpieData_mean_NValence REAL,
            MagpieData_mode_NValence REAL,
            MagpieData_avg_dev_NValence REAL,
            MagpieData_range_NValence REAL,
            MagpieData_maximum_NUnfilled REAL,
            MagpieData_minimum_NUnfilled REAL,
            MagpieData_mean_NUnfilled REAL,
            MagpieData_mode_NUnfilled REAL,
            MagpieData_avg_dev_NUnfilled REAL,
            MagpieData_range_NUnfilled REAL,
            MagpieData_maximum_CovalentRadius REAL,
            MagpieData_minimum_CovalentRadius REAL,
            MagpieData_mean_CovalentRadius REAL,
            MagpieData_mode_CovalentRadius REAL,
            MagpieData_avg_dev_CovalentRadius REAL,
            MagpieData_range_CovalentRadius REAL,
            MagpieData_maximum_GSvolume_pa REAL,
            MagpieData_minimum_GSvolume_pa REAL,
            MagpieData_mean_GSvolume_pa REAL,
            MagpieData_mode_GSvolume_pa REAL,
            MagpieData_avg_dev_GSvolume_pa REAL,
            MagpieData_range_GSvolume_pa REAL,
            MagpieData_maximum_Electronegativity REAL,
            MagpieData_minimum_Electronegativity REAL,
            MagpieData_mean_Electronegativity REAL,
            MagpieData_mode_Electronegativity REAL,
            MagpieData_avg_dev_Electronegativity REAL,
            MagpieData_range_Electronegativity REAL,
            Alloy_class TEXT,
            T REAL NOT NULL,
            target REAL NOT NULL
        )
    '''
    cursor.execute(create_dataset_table.format('train_data'))
    cursor.execute(create_dataset_table.format('validation_data'))
    cursor.execute(create_dataset_table.format('test_data'))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()
    print("Database initialized successfully with dataset tables.")