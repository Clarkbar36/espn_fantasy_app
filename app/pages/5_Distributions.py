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

def make_stat_chart(source_df, stat, highlight_team, height=300):
    """Create a single stat distribution chart."""
    # Get values for this stat
    values = source_df[stat].tolist()
    teams = source_df['teamName'].tolist()
    stat_df = pd.DataFrame({'Value': values, 'Team': teams, 'Stat': stat})

    fmt = '.3f' if stat in ['OBP', 'ERA', 'WHIP'] else '.1f'

    # Add padding to y-axis scale
    y_scale = alt.Scale(padding=20)

    box = alt.Chart(stat_df).mark_boxplot(extent='min-max', size=30).encode(
        x=alt.X('Stat:N', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Value:Q', title=None, scale=y_scale),
        tooltip=alt.value(None)
    )

    points = alt.Chart(stat_df).mark_circle(size=60, opacity=0.6).encode(
        x=alt.X('Stat:N'),
        y=alt.Y('Value:Q', scale=y_scale),
        tooltip=['Team', alt.Tooltip('Value:Q', format=fmt)]
    )

    layers = [box, points]

    if highlight_team != "None":
        highlight_df = stat_df[stat_df['Team'] == highlight_team]
        if not highlight_df.empty:
            highlight = alt.Chart(highlight_df).mark_circle(size=150, color='red').encode(
                x=alt.X('Stat:N'),
                y=alt.Y('Value:Q', scale=y_scale),
                tooltip=['Team', alt.Tooltip('Value:Q', format=fmt)]
            )
            layers.append(highlight)

    return alt.layer(*layers).properties(height=height)


st.subheader("Hitting Stats")
hit_container = st.container(key=f"hitting_container_{highlight_team}")
with hit_container:
    cols = st.columns(len(HITTING_CATS))
    for i, stat in enumerate(HITTING_CATS):
        with cols[i]:
            chart = make_stat_chart(df, stat, highlight_team)
            st.altair_chart(chart, use_container_width=True, theme=None)

st.subheader("Pitching Stats")
pitch_container = st.container(key=f"pitching_container_{highlight_team}")
with pitch_container:
    cols = st.columns(len(PITCHING_CATS))
    for i, stat in enumerate(PITCHING_CATS):
        with cols[i]:
            chart = make_stat_chart(df, stat, highlight_team)
            st.altair_chart(chart, use_container_width=True, theme=None)
