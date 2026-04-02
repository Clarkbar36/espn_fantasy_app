import streamlit as st
import pandas as pd
import altair as alt
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


@st.cache_data(ttl=3600)
def load_boxscore_data():
    engine = get_engine()
    return pd.read_sql("""
      SELECT bw."DATE", bw.period, bw."OBP", bw."R", bw."RBI", bw."SB", bw."TB", bw."ERA", bw."WHIP", bw."QS", bw."K", bw."SVHD", teams."teamName", teams."teamAbbrev"
      FROM boxscore_wide bw
      LEFT JOIN teams on bw."teamId" = teams."teamId"
    """, engine)


col1, col2, col3 = st.columns([1, 2, 3])

df = load_boxscore_data()

# Select categories to plot
all_categories = ['OBP', 'R', 'RBI', 'SB', 'TB', 'ERA', 'WHIP', 'QS', 'K', 'SVHD']
with col1:
    selected_stat = st.selectbox("Select stats to view", all_categories)

# Plot for each selected stat

# Calculate 10% below the minimum and 10% above the maximum of the 'period' column
min_stat = df[selected_stat].min()
max_stat = df[selected_stat].max()

# Define the range by taking 10% of the min and max values
y_min = min_stat - 0.05 * (max_stat - min_stat)
y_max = max_stat + 0.05 * (max_stat - min_stat)

# Convert DATE strings to datetime
df["DATE"] = pd.to_datetime(df["DATE"], format="%m-%d-%Y")

min_date = df["DATE"].min().date()
max_date = df["DATE"].max().date()

with col2:
    week_range = st.slider(
        "Select Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        step=timedelta(days=1)
    )

all_teams = sorted(df['teamName'].unique())
with col3:
# New team selector (below the columns for spacing)
    selected_teams = st.multiselect(
        "Select Teams",
        options=all_teams,
        default=all_teams  # Show all by default
    )

# Filter data
df_filtered = df[
    (df["DATE"].dt.date >= week_range[0]) &
    (df["DATE"].dt.date <= week_range[1]) &
    (df["teamName"].isin(selected_teams))
]

with st.container():
    # Create the Altair chart
    chart_title = f"{selected_stat}: {week_range[0]} - {week_range[1]}"
    if selected_stat in ["OBP", "ERA", "WHIP"]:
        y_axis_format = ".3f"  # 3 decimal places
    else:
        y_axis_format = None  # Default formatting

    chart = alt.Chart(df_filtered).mark_line(point=True).encode(
        x=alt.X("DATE:T", title="Date", axis=alt.Axis(format="%m-%d", tickCount="day")),
        y=alt.Y(
            f"{selected_stat}:Q",
            title=selected_stat,
            scale=alt.Scale(domain=[y_min, y_max]),
            axis=alt.Axis(format=y_axis_format) if y_axis_format else alt.Axis()
        ),
        color=alt.Color("teamAbbrev:N", legend=alt.Legend(title="Team")),
        tooltip=[
            alt.Tooltip("teamAbbrev:N", title="Team"),
            alt.Tooltip(f"{selected_stat}:Q", title=selected_stat),
            alt.Tooltip("DATE:T", title="Date", format="%m-%d-%Y")
        ]

    ).properties(
        title=chart_title,
        width=3000,
        height=750
    ).configure_title(
    fontSize=25,
    font='Helvetica'
)
    st.altair_chart(chart, use_container_width=True)
