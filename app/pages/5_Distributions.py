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

st.subheader("Hitting Stats")

# Create box plots for hitting stats
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

# Box plot with faceting for independent scales
box = alt.Chart(hitting_df).mark_boxplot(extent='min-max').encode(
    y=alt.Y('Value:Q', title=None),
)

# Overlay points for all teams
points = alt.Chart(hitting_df).mark_circle(size=60, opacity=0.6).encode(
    y=alt.Y('Value:Q'),
    tooltip=['Team', 'Stat', 'Value']
)

# Highlight selected team
if highlight_team != "None":
    highlight_df = hitting_df[hitting_df['Team'] == highlight_team]
    highlight = alt.Chart(highlight_df).mark_circle(size=120, color='red').encode(
        y=alt.Y('Value:Q'),
        tooltip=['Team', 'Stat', 'Value']
    )
    hitting_chart = (box + points + highlight).facet(
        column=alt.Column('Stat:N', header=alt.Header(labelOrient='bottom', title=None))
    ).resolve_scale(y='independent')
else:
    hitting_chart = (box + points).facet(
        column=alt.Column('Stat:N', header=alt.Header(labelOrient='bottom', title=None))
    ).resolve_scale(y='independent')

st.altair_chart(hitting_chart, use_container_width=True)

st.subheader("Pitching Stats")

# Create box plots for pitching stats
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

# Box plot with faceting for independent scales
box_p = alt.Chart(pitching_df).mark_boxplot(extent='min-max').encode(
    y=alt.Y('Value:Q', title=None),
)

# Overlay points
points_p = alt.Chart(pitching_df).mark_circle(size=60, opacity=0.6).encode(
    y=alt.Y('Value:Q'),
    tooltip=['Team', 'Stat', 'Value']
)

# Highlight selected team
if highlight_team != "None":
    highlight_df_p = pitching_df[pitching_df['Team'] == highlight_team]
    highlight_p = alt.Chart(highlight_df_p).mark_circle(size=120, color='red').encode(
        y=alt.Y('Value:Q'),
        tooltip=['Team', 'Stat', 'Value']
    )
    pitching_chart = (box_p + points_p + highlight_p).facet(
        column=alt.Column('Stat:N', header=alt.Header(labelOrient='bottom', title=None))
    ).resolve_scale(y='independent')
else:
    pitching_chart = (box_p + points_p).facet(
        column=alt.Column('Stat:N', header=alt.Header(labelOrient='bottom', title=None))
    ).resolve_scale(y='independent')

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
