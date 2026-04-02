import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from espn.sql_io import get_engine

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem;
        }
    </style>
""", unsafe_allow_html=True)

# Stats where lower is better
LOWER_IS_BETTER = ['ERA', 'WHIP']


@st.cache_data(ttl=3600)
def load_boxscore_data():
    engine = get_engine()
    return pd.read_sql("""
      SELECT bw."DATE", bw.period, bw."OBP", bw."R", bw."RC", bw."RBI", bw."SB", bw."TB", bw."ERA", bw."WHIP", bw."QS", bw."K", bw."SVHD", teams."teamName", teams."teamAbbrev"
      FROM boxscore_wide bw
      LEFT JOIN teams on bw."teamId" = teams."teamId"
    """, engine)


st.title("Stat Race")
st.caption("Track the race for each stat category. Winner of each stat at season end gets paid out.")

col1, col2 = st.columns([1, 3])

df = load_boxscore_data()

# Convert DATE strings to datetime and normalize to date only (remove time component)
df["DATE"] = pd.to_datetime(df["DATE"], format="%m-%d-%Y").dt.normalize()

# Keep only one record per team per date (latest)
df = df.sort_values('DATE').drop_duplicates(subset=['DATE', 'teamAbbrev'], keep='last')

# Select categories to plot
all_categories = ['OBP', 'R', 'RC', 'RBI', 'SB', 'TB', 'ERA', 'WHIP', 'QS', 'K', 'SVHD']
with col1:
    selected_stat = st.selectbox("Select Stat", all_categories)

min_date = df["DATE"].min().date()
max_date = df["DATE"].max().date()

with col2:
    week_range = st.slider(
        "Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        step=timedelta(days=1)
    )

# Filter by date range
df_filtered = df[
    (df["DATE"].dt.date >= week_range[0]) &
    (df["DATE"].dt.date <= week_range[1])
]

# Calculate rank for each date (1 = best)
ascending = selected_stat in LOWER_IS_BETTER
df_filtered = df_filtered.copy()
df_filtered['Rank'] = df_filtered.groupby('DATE')[selected_stat].rank(
    ascending=ascending, method='min'
).astype(int)

# Get latest standings for leaderboard
latest_date = df_filtered['DATE'].max()
latest_standings = df_filtered[df_filtered['DATE'] == latest_date].sort_values('Rank')

num_teams = df_filtered['teamName'].nunique()

# Layout: leaderboard on left, bump chart on right
chart_col, leader_col = st.columns([4, 1])

with leader_col:
    st.subheader("Standings")
    for _, row in latest_standings.iterrows():
        rank = int(row['Rank'])
        team = row['teamAbbrev']
        val = row[selected_stat]
        fmt = f"{val:.3f}" if selected_stat in ['OBP', 'ERA', 'WHIP'] else f"{val:.0f}"
        medal = ""
        if rank == 1:
            medal = " :first_place_medal:"
        elif rank == 2:
            medal = " :second_place_medal:"
        elif rank == 3:
            medal = " :third_place_medal:"
        st.markdown(f"**{rank}.** {team} ({fmt}){medal}")

with chart_col:
    # Create bump chart
    fig = go.Figure()

    teams = df_filtered['teamAbbrev'].unique()
    for team in teams:
        team_data = df_filtered[df_filtered['teamAbbrev'] == team].sort_values('DATE')
        fig.add_trace(go.Scatter(
            x=team_data['DATE'],
            y=team_data['Rank'],
            mode='lines+markers',
            name=team,
            hovertemplate=f'{team}<br>Rank: %{{y}}<br>%{{x|%m-%d-%Y}}<extra></extra>'
        ))

    fig.update_layout(
        title=f"{selected_stat} Race",
        xaxis_title="Date",
        yaxis_title="Rank",
        xaxis=dict(tickformat='%m-%d', dtick='D1'),
        yaxis=dict(
            autorange='reversed',  # 1st place at top
            tickmode='linear',
            tick0=1,
            dtick=1,
            range=[num_teams + 0.5, 0.5]
        ),
        height=600,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)
