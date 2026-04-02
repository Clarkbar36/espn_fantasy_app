import streamlit as st
import pandas as pd
import altair as alt
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

HITTING_CATS = ['OBP', 'R', 'RBI', 'SB', 'TB', 'RC']
PITCHING_CATS = ['ERA', 'WHIP', 'QS', 'K', 'SVHD']


@st.cache_data(ttl=3600)
def load_distribution_data():
    engine = get_engine()
    query = 'SELECT * FROM totals LEFT JOIN teams ON totals."teamId" = teams."teamId"'
    df = pd.read_sql(query, engine)
    with engine.connect() as conn:
        result = conn.execute(text('SELECT MAX("DATE") FROM boxscore_wide'))
        max_date = result.scalar()
    return df, max_date


df, max_date = load_distribution_data()

st.title("Stat Distributions")
st.caption(f"Updated through {max_date}. See where each team falls in the league distribution.")

# Team selector to highlight
highlight_team = st.selectbox("Highlight Team", ["None"] + sorted(df['teamName'].unique().tolist()))

def make_stat_chart(data_df, stat, highlight_team, width=120, height=350):
    """Create a single stat distribution chart."""
    stat_data = data_df[data_df['Stat'] == stat]

    box = alt.Chart(stat_data).mark_boxplot(extent='min-max', size=30).encode(
        y=alt.Y('Value:Q', title=None),
    )

    points = alt.Chart(stat_data).mark_circle(size=60, opacity=0.6).encode(
        y=alt.Y('Value:Q'),
        tooltip=['Team', alt.Tooltip('Value:Q', format='.3f' if stat in ['OBP', 'ERA', 'WHIP'] else '.1f')]
    )

    if highlight_team != "None":
        highlight_data = stat_data[stat_data['Team'] == highlight_team]
        highlight = alt.Chart(highlight_data).mark_circle(size=150, color='red').encode(
            y=alt.Y('Value:Q'),
            tooltip=['Team', alt.Tooltip('Value:Q', format='.3f' if stat in ['OBP', 'ERA', 'WHIP'] else '.1f')]
        )
        chart = box + points + highlight
    else:
        chart = box + points

    return chart.properties(width=width, height=height, title=stat)


st.subheader("Hitting Stats")

# Create data for hitting stats
hitting_data = []
for stat in HITTING_CATS:
    for _, row in df.iterrows():
        hitting_data.append({
            'Stat': stat,
            'Value': row[stat],
            'Team': row['teamName'],
            'Abbrev': row['teamAbbrev']
        })

hitting_df = pd.DataFrame(hitting_data)

# Create individual charts and concatenate horizontally
hitting_charts = [make_stat_chart(hitting_df, stat, highlight_team) for stat in HITTING_CATS]
hitting_chart = alt.hconcat(*hitting_charts).resolve_scale(y='independent')

st.altair_chart(hitting_chart, use_container_width=True)

st.subheader("Pitching Stats")

# Create data for pitching stats
pitching_data = []
for stat in PITCHING_CATS:
    for _, row in df.iterrows():
        pitching_data.append({
            'Stat': stat,
            'Value': row[stat],
            'Team': row['teamName'],
            'Abbrev': row['teamAbbrev']
        })

pitching_df = pd.DataFrame(pitching_data)

# Create individual charts and concatenate horizontally
pitching_charts = [make_stat_chart(pitching_df, stat, highlight_team) for stat in PITCHING_CATS]
pitching_chart = alt.hconcat(*pitching_charts).resolve_scale(y='independent')

st.altair_chart(pitching_chart, use_container_width=True)

# Table showing percentiles for highlighted team
if highlight_team != "None":
    st.subheader(f"{highlight_team} Percentiles")

    team_row = df[df['teamName'] == highlight_team].iloc[0]
    all_stats = HITTING_CATS + PITCHING_CATS

    percentile_data = []
    for stat in all_stats:
        team_val = team_row[stat]
        # For ERA/WHIP, lower is better so invert percentile
        if stat in ['ERA', 'WHIP']:
            pct = (df[stat] > team_val).sum() / len(df) * 100
        else:
            pct = (df[stat] < team_val).sum() / len(df) * 100
        percentile_data.append({
            'Stat': stat,
            'Value': round(team_val, 3) if stat in ['OBP', 'ERA', 'WHIP'] else round(team_val, 1),
            'Percentile': f"{pct:.0f}%",
            'Category': 'Hitting' if stat in HITTING_CATS else 'Pitching'
        })

    pct_df = pd.DataFrame(percentile_data)
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Hitting**")
        st.dataframe(pct_df[pct_df['Category'] == 'Hitting'][['Stat', 'Value', 'Percentile']], hide_index=True)
    with col2:
        st.write("**Pitching**")
        st.dataframe(pct_df[pct_df['Category'] == 'Pitching'][['Stat', 'Value', 'Percentile']], hide_index=True)
