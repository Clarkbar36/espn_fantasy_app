import os
import pandas as pd
from sqlalchemy import create_engine, text


def get_engine():
    url = os.getenv('DATABASE_URL')
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


def read_table(table_name):
    engine = get_engine()
    data = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    return data
