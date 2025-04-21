import sqlite3
import pandas as pd

def newest_matchup(db):
    conn = sqlite3.connect(f'db/{db}.db')
    # Create a cursor object
    cursor = conn.cursor()

    # Query to get the maximum value of a specific column, e.g., 'OBP' from the 'cumulative' table
    cursor.execute("SELECT MAX(period)+1 FROM boxscore_wide")

    period = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return period

def write_table(db, data, table_name, append_type):
    # Connect to SQLite Database
    conn = sqlite3.connect(f'db/{db}.db')  # Replace with your database file path

    data.to_sql(table_name, conn, if_exists=append_type, index=False)

    # Commit and close the connection
    conn.commit()
    conn.close()

def read_table(db, table_name):
    # Connect to your SQLite DB
    conn = sqlite3.connect(f"db/{db}.db")

    # Load the cumulative table
    data = pd.read_sql(f"SELECT * FROM {table_name}", conn)

    conn.commit()
    conn.close()

    return data