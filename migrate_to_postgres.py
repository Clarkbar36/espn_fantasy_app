"""
Migrate data from local SQLite to PostgreSQL.

Usage:
  1. Get your DATABASE_URL from Railway dashboard
  2. Run: DATABASE_URL="postgresql://..." uv run python migrate_to_postgres.py
"""
import os
from sqlalchemy import create_engine, text
import pandas as pd

TABLES = ['teams', 'draft', 'boxscore_wide', 'total_powerscore', 'cum_powerscore']

VIEWS = {
    'totals': '''
CREATE OR REPLACE VIEW totals AS
SELECT "teamId",
    SUM("AB") AS "AB", SUM("B_BB") AS "B_BB", SUM("B_SO") AS "B_SO", SUM("CS") AS "CS",
    SUM("ER") AS "ER", SUM("GDP") AS "GDP", SUM("H") AS "H", SUM("HBP") AS "HBP",
    SUM("HLD") AS "HLD", SUM("K") AS "K", SUM("OUTS") AS "OUTS", SUM("P_BB") AS "P_BB",
    SUM("P_H") AS "P_H", SUM("QS") AS "QS", SUM("R") AS "R", SUM("RBI") AS "RBI",
    SUM("RC") AS "RC", SUM("SAC") AS "SAC", SUM("SB") AS "SB", SUM("SF") AS "SF",
    SUM("SV") AS "SV", SUM("SVHD") AS "SVHD", SUM("TB") AS "TB",
    FLOOR(SUM("OUTS") / 3.0) + (SUM("OUTS")::integer % 3) * 0.1 AS "IP",
    CASE WHEN SUM("OUTS") > 0 THEN ROUND(((SUM("ER") * 27.0) / SUM("OUTS"))::numeric, 2) ELSE NULL END AS "ERA",
    CASE WHEN SUM("OUTS") > 0 THEN ROUND(((SUM("P_BB") + SUM("P_H")) / (SUM("OUTS") / 3.0))::numeric, 2) ELSE NULL END AS "WHIP",
    CASE WHEN (SUM("AB") + SUM("B_BB") + SUM("HBP") + SUM("SF")) > 0
        THEN ROUND(((SUM("H") + SUM("B_BB") + SUM("HBP"))::numeric / (SUM("AB") + SUM("B_BB") + SUM("HBP") + SUM("SF")))::numeric, 3)
        ELSE NULL END AS "OBP"
FROM boxscore_wide GROUP BY "teamId"
''',
    'cumulative': '''
CREATE OR REPLACE VIEW cumulative AS
SELECT "teamId", "DATE", period,
    SUM("AB") OVER (PARTITION BY "teamId" ORDER BY period) AS "AB",
    SUM("B_BB") OVER (PARTITION BY "teamId" ORDER BY period) AS "B_BB",
    SUM("B_SO") OVER (PARTITION BY "teamId" ORDER BY period) AS "B_SO",
    SUM("CS") OVER (PARTITION BY "teamId" ORDER BY period) AS "CS",
    SUM("ER") OVER (PARTITION BY "teamId" ORDER BY period) AS "ER",
    SUM("GDP") OVER (PARTITION BY "teamId" ORDER BY period) AS "GDP",
    SUM("H") OVER (PARTITION BY "teamId" ORDER BY period) AS "H",
    SUM("HBP") OVER (PARTITION BY "teamId" ORDER BY period) AS "HBP",
    SUM("HLD") OVER (PARTITION BY "teamId" ORDER BY period) AS "HLD",
    SUM("K") OVER (PARTITION BY "teamId" ORDER BY period) AS "K",
    SUM("OUTS") OVER (PARTITION BY "teamId" ORDER BY period) AS "OUTS",
    SUM("P_BB") OVER (PARTITION BY "teamId" ORDER BY period) AS "P_BB",
    SUM("P_H") OVER (PARTITION BY "teamId" ORDER BY period) AS "P_H",
    SUM("QS") OVER (PARTITION BY "teamId" ORDER BY period) AS "QS",
    SUM("R") OVER (PARTITION BY "teamId" ORDER BY period) AS "R",
    SUM("RBI") OVER (PARTITION BY "teamId" ORDER BY period) AS "RBI",
    SUM("RC") OVER (PARTITION BY "teamId" ORDER BY period) AS "RC",
    SUM("SAC") OVER (PARTITION BY "teamId" ORDER BY period) AS "SAC",
    SUM("SB") OVER (PARTITION BY "teamId" ORDER BY period) AS "SB",
    SUM("SF") OVER (PARTITION BY "teamId" ORDER BY period) AS "SF",
    SUM("SV") OVER (PARTITION BY "teamId" ORDER BY period) AS "SV",
    SUM("SVHD") OVER (PARTITION BY "teamId" ORDER BY period) AS "SVHD",
    SUM("TB") OVER (PARTITION BY "teamId" ORDER BY period) AS "TB",
    FLOOR(SUM("OUTS") OVER (PARTITION BY "teamId" ORDER BY period) / 3.0) +
        ((SUM("OUTS") OVER (PARTITION BY "teamId" ORDER BY period))::integer % 3) * 0.1 AS "IP",
    CASE WHEN SUM("OUTS") OVER (PARTITION BY "teamId" ORDER BY period) > 0
        THEN ROUND(((SUM("ER") OVER (PARTITION BY "teamId" ORDER BY period) * 27.0) /
            SUM("OUTS") OVER (PARTITION BY "teamId" ORDER BY period))::numeric, 2)
        ELSE NULL END AS "ERA",
    CASE WHEN SUM("OUTS") OVER (PARTITION BY "teamId" ORDER BY period) > 0
        THEN ROUND(((SUM("P_BB") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("P_H") OVER (PARTITION BY "teamId" ORDER BY period)) /
            (SUM("OUTS") OVER (PARTITION BY "teamId" ORDER BY period) / 3.0))::numeric, 2)
        ELSE NULL END AS "WHIP",
    CASE WHEN (SUM("AB") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("B_BB") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("HBP") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("SF") OVER (PARTITION BY "teamId" ORDER BY period)) > 0
        THEN ROUND(((SUM("H") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("B_BB") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("HBP") OVER (PARTITION BY "teamId" ORDER BY period))::numeric /
            (SUM("AB") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("B_BB") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("HBP") OVER (PARTITION BY "teamId" ORDER BY period) +
            SUM("SF") OVER (PARTITION BY "teamId" ORDER BY period)))::numeric, 3)
        ELSE NULL END AS "OBP"
FROM boxscore_wide
'''
}

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

print("\nCreating views...\n")

with pg_engine.connect() as conn:
    for view_name, view_sql in VIEWS.items():
        try:
            conn.execute(text(view_sql))
            conn.commit()
            print(f"  {view_name}: created")
        except Exception as e:
            print(f"  {view_name}: FAILED ({e})")

print("\nDone!")
