import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from espn.sql_io import get_engine
from sqlalchemy import text

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_powerscore_data():
    engine = get_engine()
    query = '''SELECT "teamName" AS "Team",
     "PowerScore",
     "OBP_rank" AS "OBP Rank",
     "R_rank" AS "R Rank",
     "RBI_rank" AS "RBI Rank",
     "SB_rank" AS "SB Rank",
     "TB_rank" AS "TB Rank",
     "RC_rank" AS "RC Rank",
     "ERA_rank" AS "ERA Rank",
     "WHIP_rank" AS "WHIP Rank",
     "QS_rank" AS "QS Rank",
     "K_rank" AS "K Rank",
     "SVHD_rank" AS "SVHD Rank"
     FROM total_powerscore
    LEFT JOIN teams on total_powerscore."teamId" = teams."teamId"'''
    df = pd.read_sql(query, engine)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT MAX("DATE") FROM boxscore_wide'))
        period = result.scalar()
    return df, period


df, period = load_powerscore_data()

with st.container():
    # Display header
    st.title("Power Score Table")
    st.caption(f"Updated through {period}")
    st.markdown("""
    **PowerScore** measures overall team strength by summing each team's rank across all 11 scoring categories.
    A rank of 1 means best in the league for that stat. Lower ranks = better performance.
    The PowerScore inverts this so that **higher PowerScore = stronger team**.
    """)

    # Sort by PowerScore (higher = better)
    df_sorted = df.sort_values(by="PowerScore", ascending=False)

    # Round ranks for cleaner display
    rank_columns = [col for col in df.columns if col.endswith("_rank")]
    df_sorted[rank_columns] = df_sorted[rank_columns].round(1)

    # Show table
    st.dataframe(df_sorted, use_container_width=True, hide_index=True)
