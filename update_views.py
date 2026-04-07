"""
Update PostgreSQL views without migrating data.

Usage:
  $env:DATABASE_URL="postgresql://..."; uv run python update_views.py
"""
import os
from sqlalchemy import create_engine, text

pg_url = os.environ.get('DATABASE_URL')
if not pg_url:
    raise ValueError("Set DATABASE_URL environment variable to your Railway PostgreSQL URL")

if pg_url.startswith('postgres://'):
    pg_url = pg_url.replace('postgres://', 'postgresql://', 1)

pg_engine = create_engine(pg_url)

# View names to drop first (in dependency order)
VIEWS_TO_DROP = ['season_cumulative', 'cumulative', 'totals']

print("Dropping existing views...\n")

with pg_engine.connect() as conn:
    for view_name in VIEWS_TO_DROP:
        try:
            conn.execute(text(f'DROP VIEW IF EXISTS {view_name} CASCADE'))
            conn.commit()
            print(f"  {view_name}: dropped")
        except Exception as e:
            print(f"  {view_name}: drop failed ({e})")

print("\nCreating views...\n")

# Define views inline to avoid importing migrate_to_postgres (which runs migration code)
VIEWS = {
    'totals': '''
CREATE VIEW totals AS
WITH period_finals AS (
    SELECT DISTINCT ON ("teamId", period)
        "teamId", "AB", "B_BB", "B_SO", "CS", "ER", "GDP", "H", "HBP",
        "HLD", "K", "OUTS", "P_BB", "P_H", "QS", "R", "RBI", "RC",
        "SAC", "SB", "SF", "SV", "SVHD", "TB"
    FROM boxscore_wide
    ORDER BY "teamId", period, "DATE" DESC
)
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
FROM period_finals GROUP BY "teamId"
''',
    'cumulative': '''
CREATE VIEW cumulative AS
WITH period_finals AS (
    SELECT DISTINCT ON ("teamId", period)
        "teamId", "DATE", period, "AB", "B_BB", "B_SO", "CS", "ER", "GDP", "H", "HBP",
        "HLD", "K", "OUTS", "P_BB", "P_H", "QS", "R", "RBI", "RC",
        "SAC", "SB", "SF", "SV", "SVHD", "TB"
    FROM boxscore_wide
    ORDER BY "teamId", period, "DATE" DESC
)
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
FROM period_finals
''',
    'season_cumulative': '''
CREATE VIEW season_cumulative AS
WITH period_finals AS (
    SELECT DISTINCT ON ("teamId", period)
        "teamId", period, "AB", "B_BB", "B_SO", "CS", "ER", "GDP", "H", "HBP",
        "HLD", "K", "OUTS", "P_BB", "P_H", "QS", "R", "RBI", "RC",
        "SAC", "SB", "SF", "SV", "SVHD", "TB"
    FROM boxscore_wide
    ORDER BY "teamId", period, "DATE" DESC
),
prior_period_totals AS (
    SELECT "teamId", period,
        COALESCE(SUM("AB") OVER w - "AB", 0) AS prior_AB,
        COALESCE(SUM("B_BB") OVER w - "B_BB", 0) AS prior_B_BB,
        COALESCE(SUM("ER") OVER w - "ER", 0) AS prior_ER,
        COALESCE(SUM("H") OVER w - "H", 0) AS prior_H,
        COALESCE(SUM("HBP") OVER w - "HBP", 0) AS prior_HBP,
        COALESCE(SUM("K") OVER w - "K", 0) AS prior_K,
        COALESCE(SUM("OUTS") OVER w - "OUTS", 0) AS prior_OUTS,
        COALESCE(SUM("P_BB") OVER w - "P_BB", 0) AS prior_P_BB,
        COALESCE(SUM("P_H") OVER w - "P_H", 0) AS prior_P_H,
        COALESCE(SUM("QS") OVER w - "QS", 0) AS prior_QS,
        COALESCE(SUM("R") OVER w - "R", 0) AS prior_R,
        COALESCE(SUM("RBI") OVER w - "RBI", 0) AS prior_RBI,
        COALESCE(SUM("RC") OVER w - "RC", 0) AS prior_RC,
        COALESCE(SUM("SB") OVER w - "SB", 0) AS prior_SB,
        COALESCE(SUM("SF") OVER w - "SF", 0) AS prior_SF,
        COALESCE(SUM("SVHD") OVER w - "SVHD", 0) AS prior_SVHD,
        COALESCE(SUM("TB") OVER w - "TB", 0) AS prior_TB
    FROM period_finals
    WINDOW w AS (PARTITION BY "teamId" ORDER BY period ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
)
SELECT
    bw."DATE", bw.period, bw."teamId",
    bw."R" + COALESCE(pt.prior_R, 0) AS "R",
    bw."RBI" + COALESCE(pt.prior_RBI, 0) AS "RBI",
    bw."SB" + COALESCE(pt.prior_SB, 0) AS "SB",
    bw."TB" + COALESCE(pt.prior_TB, 0) AS "TB",
    bw."K" + COALESCE(pt.prior_K, 0) AS "K",
    bw."QS" + COALESCE(pt.prior_QS, 0) AS "QS",
    bw."SVHD" + COALESCE(pt.prior_SVHD, 0) AS "SVHD",
    bw."RC" + COALESCE(pt.prior_RC, 0) AS "RC",
    CASE WHEN (bw."AB" + COALESCE(pt.prior_AB, 0) + bw."B_BB" + COALESCE(pt.prior_B_BB, 0) +
               bw."HBP" + COALESCE(pt.prior_HBP, 0) + bw."SF" + COALESCE(pt.prior_SF, 0)) > 0
        THEN ROUND(((bw."H" + COALESCE(pt.prior_H, 0) + bw."B_BB" + COALESCE(pt.prior_B_BB, 0) +
                     bw."HBP" + COALESCE(pt.prior_HBP, 0))::numeric /
                    (bw."AB" + COALESCE(pt.prior_AB, 0) + bw."B_BB" + COALESCE(pt.prior_B_BB, 0) +
                     bw."HBP" + COALESCE(pt.prior_HBP, 0) + bw."SF" + COALESCE(pt.prior_SF, 0)))::numeric, 3)
        ELSE NULL END AS "OBP",
    CASE WHEN (bw."OUTS" + COALESCE(pt.prior_OUTS, 0)) > 0
        THEN ROUND((((bw."ER" + COALESCE(pt.prior_ER, 0)) * 27.0) /
                    (bw."OUTS" + COALESCE(pt.prior_OUTS, 0)))::numeric, 2)
        ELSE NULL END AS "ERA",
    CASE WHEN (bw."OUTS" + COALESCE(pt.prior_OUTS, 0)) > 0
        THEN ROUND(((bw."P_BB" + COALESCE(pt.prior_P_BB, 0) + bw."P_H" + COALESCE(pt.prior_P_H, 0)) /
                    ((bw."OUTS" + COALESCE(pt.prior_OUTS, 0)) / 3.0))::numeric, 2)
        ELSE NULL END AS "WHIP"
FROM boxscore_wide bw
LEFT JOIN prior_period_totals pt ON bw."teamId" = pt."teamId" AND bw.period = pt.period
'''
}

with pg_engine.connect() as conn:
    for view_name, view_sql in VIEWS.items():
        try:
            conn.execute(text(view_sql))
            conn.commit()
            print(f"  {view_name}: created")
        except Exception as e:
            print(f"  {view_name}: FAILED ({e})")

print("\nDone! Now run update_db.py to regenerate total_powerscore and cum_powerscore tables.")
