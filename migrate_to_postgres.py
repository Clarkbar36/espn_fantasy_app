"""
Migrate data from local SQLite to PostgreSQL.

Usage:
  1. Get your DATABASE_URL from Railway dashboard
  2. Run: DATABASE_URL="postgresql://..." uv run python migrate_to_postgres.py
"""
import os
from sqlalchemy import create_engine
import pandas as pd

TABLES = ['teams', 'draft', 'boxscore_wide', 'total_powerscore', 'cum_powerscore']

# Source: local SQLite
sqlite_engine = create_engine('sqlite:///db/paychex.lg.db')

# Target: PostgreSQL from DATABASE_URL
pg_url = os.environ.get('DATABASE_URL')
if not pg_url:
    raise ValueError("Set DATABASE_URL environment variable to your Railway PostgreSQL URL")

if pg_url.startswith('postgres://'):
    pg_url = pg_url.replace('postgres://', 'postgresql://', 1)

pg_engine = create_engine(pg_url)

print("Migrating tables from SQLite to PostgreSQL...\n")

for table in TABLES:
    try:
        df = pd.read_sql(f"SELECT * FROM {table}", sqlite_engine)
        row_count = len(df)
        df.to_sql(table, pg_engine, if_exists='replace', index=False)
        print(f"  {table}: {row_count} rows migrated")
    except Exception as e:
        print(f"  {table}: SKIPPED ({e})")

print("\nDone!")
