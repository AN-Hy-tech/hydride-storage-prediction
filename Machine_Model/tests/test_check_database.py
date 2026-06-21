import sqlite3
import os
import pytest

DB_PATH = r"D:\\Hydride_Machine_learning_project\\Machine_Model\\data\\database\\hydride.db"

def test_database_exists():
    assert os.path.exists(DB_PATH), f"Database file not found at {DB_PATH}"

def test_table_structure():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(hydrides)")
    columns = [col[1] for col in cursor.fetchall()]
    expected_columns = ['Composition', 'Alloy_class', 'Dataset', 'H2_W% (max)', 'temperature(K)', 'Citation']
    assert all(col in columns for col in expected_columns), "Table structure does not match expected columns"
    conn.close()

def test_row_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hydrides")
    row_count = cursor.fetchone()[0]
    assert row_count == 1279, f"Expected 1279 rows, but got {row_count}"
    conn.close()

def test_h2_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MIN([H2_W% (max)]), MAX([H2_W% (max)]), AVG([H2_W% (max)]) FROM hydrides")
    stats = cursor.fetchone()
    assert stats[0] == 0.1, f"Expected min H2_W% (max) to be 0.1, but got {stats[0]}"
    assert stats[1] == 7.19, f"Expected max H2_W% (max) to be 7.19, but got {stats[1]}"
    assert abs(stats[2] - 1.95) < 0.01, f"Expected avg H2_W% (max) to be ~1.95, but got {stats[2]}"
    conn.close()