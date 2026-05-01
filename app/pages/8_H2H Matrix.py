import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from espn.sql_io import get_engine, read_h2h_matchups, read_table
from espn.transform import build_h2h_record_matrix, build_h2h_category_matrix

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_h2h_data():
    engine = get_engine()
    h2h_df = pd.read_sql("SELECT * FROM h2h_matchups", engine)
    teams_df = read_table('teams')
    seasons = sorted(h2h_df['season'].unique(), reverse=True) if not h2h_df.empty else []
    return h2h_df, teams_df, seasons


h2h_df, teams_df, seasons = load_h2h_data()

st.title("Head-to-Head Matrix")

if h2h_df.empty:
    st.warning("No H2H matchup data available. Run update_db.py to populate the data.")
else:
    col1, col2 = st.columns([1, 3])

    with col1:
        selected_season = st.selectbox("Season", seasons)

    with col2:
        matrix_type = st.radio(
            "View type",
            ["Win-Loss Record", "Category Wins Total"],
            horizontal=True
        )

    completed_periods = h2h_df[h2h_df['season'] == selected_season]['period'].max()
    st.caption(f"Results through matchup period {completed_periods}")

    if matrix_type == "Win-Loss Record":
        st.markdown("Each cell shows the row team's record against the column team (W-L-T).")
        matrix = build_h2h_record_matrix(h2h_df, teams_df, season=selected_season)
    else:
        st.markdown("Each cell shows total stat categories the row team has won against the column team.")
        matrix = build_h2h_category_matrix(h2h_df, teams_df, season=selected_season)

    st.dataframe(matrix, use_container_width=True)
