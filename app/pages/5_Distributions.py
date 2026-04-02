import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

def make_stat_chart(source_df, stat, highlight_team, height=350):
    """Create a single stat distribution chart using Plotly."""
    values = source_df[stat].tolist()
    teams = source_df['teamName'].tolist()

    fmt = '.3f' if stat in ['OBP', 'ERA', 'WHIP'] else '.1f'

    # Calculate y-axis range with padding
    min_val, max_val = min(values), max(values)
    padding = (max_val - min_val) * 0.1
    y_range = [min_val - padding, max_val + padding]

    fig = go.Figure()

    # Box plot
    fig.add_trace(go.Box(
        y=values,
        name=stat,
        boxpoints=False,
        marker_color='steelblue',
        line_color='steelblue',
        hoverinfo='skip'
    ))

    # Individual team points
    fig.add_trace(go.Scatter(
        y=values,
        x=[stat] * len(values),
        mode='markers',
        marker=dict(size=10, color='steelblue', opacity=0.6),
        text=teams,
        hovertemplate='%{text}<br>' + stat + ': %{y:' + fmt + '}<extra></extra>',
        showlegend=False
    ))

    # Highlighted team point
    if highlight_team != "None":
        team_idx = teams.index(highlight_team) if highlight_team in teams else None
        if team_idx is not None:
            fig.add_trace(go.Scatter(
                y=[values[team_idx]],
                x=[stat],
                mode='markers',
                marker=dict(size=16, color='red'),
                text=[highlight_team],
                hovertemplate='%{text}<br>' + stat + ': %{y:' + fmt + '}<extra></extra>',
                showlegend=False
            ))

    fig.update_layout(
        height=height,
        margin=dict(l=40, r=10, t=10, b=40),
        yaxis=dict(range=y_range, title=None),
        xaxis=dict(title=None),
        showlegend=False
    )

    return fig


st.subheader("Hitting Stats")
cols = st.columns(len(HITTING_CATS))
for i, stat in enumerate(HITTING_CATS):
    with cols[i]:
        fig = make_stat_chart(df, stat, highlight_team)
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Pitching Stats")
cols = st.columns(len(PITCHING_CATS))
for i, stat in enumerate(PITCHING_CATS):
    with cols[i]:
        fig = make_stat_chart(df, stat, highlight_team)
        st.plotly_chart(fig, use_container_width=True)
