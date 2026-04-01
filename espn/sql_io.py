import os
import pandas as pd
from sqlalchemy import create_engine, text


def get_engine():
    url = os.getenv('DATABASE_URL')
    # Fallback: read from file if env var not available (Railway workaround)
    if not url:
        try:
            with open('/tmp/db_url', 'r') as f:
                url = f.read().strip()
        except FileNotFoundError:
            pass
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return create_engine(url)
    return create_engine('sqlite:///db/paychex.lg.db')


def newest_matchup():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(period)+1 FROM boxscore_wide"))
        period = result.scalar()
    return period


def write_table(data, table_name, append_type):
    engine = get_engine()
    data.to_sql(table_name, engine, if_exists=append_type, index=False)


def upsert_by_date(data, table_name, date_value):
    """Insert rows, replacing any existing rows for the given date."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM {} WHERE \"DATE\" = :date".format(table_name)), {"date": date_value})
        conn.commit()
    data.to_sql(table_name, engine, if_exists='append', index=False)


def read_table(table_name):
    engine = get_engine()
    data = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    return data
