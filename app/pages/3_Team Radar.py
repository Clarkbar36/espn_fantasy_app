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


@st.cache_data(ttl=72000)
def load_radar_data():
    engine = get_engine()
    query = "SELECT * FROM total_powerscore LEFT JOIN teams on total_powerscore.teamId = teams.teamId"
    df = pd.read_sql(query, engine)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(DATE) FROM boxscore_wide"))
        period = result.scalar()
    return df, period


df, period = load_radar_data()

with st.container():
    # Select the team for which you want to display the radar chart
    team_selected = st.selectbox("Select Team", sorted(df['teamName'].unique()))

    # Filter the data for the selected team
    team_data = df[df['teamName'] == team_selected].iloc[0]

    # List of rank columns (no need for stat columns, only rank columns)
    rank_columns = ['OBP_rank', 'R_rank', 'RBI_rank', 'SB_rank', 'TB_rank', 'RC_rank', 'ERA_rank', 'WHIP_rank', 'QS_rank', 'K_rank', 'SVHD_rank']

    # Create a list of ranks for the radar chart
    ranks = [team_data[rank] for rank in rank_columns]

    # Categories for the radar chart (correspond to the stats)
    categories = ['OBP', 'R', 'RBI', 'SB', 'TB', 'RC', 'ERA', 'WHIP', 'QS', 'K', 'SVHD']

    # Create the radar chart using Plotly
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=ranks,
        theta=categories,
        fill='toself',
        name='',
    ))

    # Update layout for the radar chart
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[max(ranks), 1],  # This flips the direction: 1 (best) is center
                tickmode='linear',
                tick0=1,
                dtick=1,
            ),
            angularaxis=dict(
                direction='clockwise'
            )
        ),
        title=dict(text=f"{team_selected} - Radar Chart",
                    x=0.5,  # Center title
                    xanchor='center',
                    font=dict(size=24)),
        annotations=[
            dict(
                text=f"Updated through {period}",
                x=0.5,
                y=1.07,  # slightly above the plot
                xref='paper',
                yref='paper',
                showarrow=False,
                font=dict(size=16, color="gray"),
                xanchor='center'
            )],
        width=800,   # Increase width
        height=800,  # Increase height
    )

    # Display the radar chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)
