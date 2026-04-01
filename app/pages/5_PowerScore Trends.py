import streamlit as st
import pandas as pd
import altair as alt
import sys
import os

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


@st.cache_data(ttl=72000)
def load_powerscore_trends():
    engine = get_engine()
    query = '''
        SELECT cp.period, cp."PowerScore", t."teamName", t."teamAbbrev"
        FROM cum_powerscore cp
        LEFT JOIN teams t ON cp."teamId" = t."teamId"
        ORDER BY cp.period
    '''
    return pd.read_sql(query, engine)


df = load_powerscore_trends()

st.title("PowerScore Trends")
st.caption("Track how each team's PowerScore has changed week-to-week. Higher = better.")

# Team filter
all_teams = sorted(df['teamName'].unique())
selected_teams = st.multiselect(
    "Select Teams",
    options=all_teams,
    default=all_teams
)

df_filtered = df[df['teamName'].isin(selected_teams)]

# Line chart
chart = alt.Chart(df_filtered).mark_line(point=True).encode(
    x=alt.X('period:O', title='Week', axis=alt.Axis(labelAngle=0)),
    y=alt.Y('PowerScore:Q', title='PowerScore'),
    color=alt.Color('teamAbbrev:N', legend=alt.Legend(title='Team')),
    tooltip=[
        alt.Tooltip('teamAbbrev:N', title='Team'),
        alt.Tooltip('period:O', title='Week'),
        alt.Tooltip('PowerScore:Q', title='PowerScore', format='.1f')
    ]
).properties(
    height=500
)

st.altair_chart(chart, use_container_width=True)

# Show current standings
st.subheader("Current Week Standings")
latest_period = df['period'].max()
latest_df = df[df['period'] == latest_period][['teamName', 'PowerScore']].sort_values('PowerScore', ascending=False)
latest_df.columns = ['Team', 'PowerScore']
latest_df['PowerScore'] = latest_df['PowerScore'].round(1)
st.dataframe(latest_df, use_container_width=True, hide_index=True)
