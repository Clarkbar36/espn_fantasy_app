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

HITTING_CATS = {
    'OBP': True,
    'R': True,
    'RBI': True,
    'SB': True,
    'TB': True,
    'RC': True,
}

PITCHING_CATS = {
    'ERA': False,
    'WHIP': False,
    'QS': True,
    'K': True,
    'SVHD': True,
}


@st.cache_data(ttl=72000)
def load_splits_data():
    engine = get_engine()
    query = 'SELECT * FROM total_powerscore LEFT JOIN teams ON total_powerscore."teamId" = teams."teamId"'
    df = pd.read_sql(query, engine)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT MAX("DATE") FROM boxscore_wide'))
        max_date = result.scalar()

    num_teams = len(df)

    # Calculate hitting PowerScore
    for stat, high_is_better in HITTING_CATS.items():
        df[f'{stat}_rank'] = df[stat].rank(ascending=not high_is_better, method='min')
    hitting_rank_cols = [f'{stat}_rank' for stat in HITTING_CATS]
    df['HittingScore'] = sum((num_teams + 1 - df[col]) for col in hitting_rank_cols)

    # Calculate pitching PowerScore
    for stat, high_is_better in PITCHING_CATS.items():
        df[f'{stat}_rank'] = df[stat].rank(ascending=not high_is_better, method='min')
    pitching_rank_cols = [f'{stat}_rank' for stat in PITCHING_CATS]
    df['PitchingScore'] = sum((num_teams + 1 - df[col]) for col in pitching_rank_cols)

    return df, max_date


df, max_date = load_splits_data()

st.title("Hitter / Pitcher Splits")
st.caption(f"Updated through {max_date}. Higher score = better. Ranks (1 = best).")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Hitting")
    hitting_cols = ['teamName', 'HittingScore'] + [f'{stat}_rank' for stat in HITTING_CATS]
    hitting_df = df[hitting_cols].copy()
    hitting_df.columns = ['Team', 'Score'] + [f'{stat}' for stat in HITTING_CATS]
    hitting_df = hitting_df.sort_values('Score', ascending=False)

    # Round ranks
    for col in hitting_df.columns[2:]:
        hitting_df[col] = hitting_df[col].astype(int)

    st.dataframe(hitting_df, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Pitching")
    pitching_cols = ['teamName', 'PitchingScore'] + [f'{stat}_rank' for stat in PITCHING_CATS]
    pitching_df = df[pitching_cols].copy()
    pitching_df.columns = ['Team', 'Score'] + [f'{stat}' for stat in PITCHING_CATS]
    pitching_df = pitching_df.sort_values('Score', ascending=False)

    # Round ranks
    for col in pitching_df.columns[2:]:
        pitching_df[col] = pitching_df[col].astype(int)

    st.dataframe(pitching_df, use_container_width=True, hide_index=True)

st.markdown("---")

# Scatter plot showing hitting vs pitching
st.subheader("Hitting vs Pitching Performance")

import altair as alt

scatter_df = df[['teamAbbrev', 'HittingScore', 'PitchingScore']].copy()

chart = alt.Chart(scatter_df).mark_circle(size=100).encode(
    x=alt.X('HittingScore:Q', title='Hitting Score'),
    y=alt.Y('PitchingScore:Q', title='Pitching Score'),
    tooltip=['teamAbbrev', 'HittingScore', 'PitchingScore']
).properties(
    width=600,
    height=400
)

text = chart.mark_text(
    align='left',
    baseline='middle',
    dx=7
).encode(
    text='teamAbbrev'
)

st.altair_chart(chart + text, use_container_width=True)
