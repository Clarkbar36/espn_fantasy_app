import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
import os

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem;
        }
    </style>
""", unsafe_allow_html=True)



db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'paychex.lg.db')

conn = sqlite3.connect(db_path)

# Load data
df = pd.read_sql("SELECT * FROM boxscore_wide", conn)

# Select categories to plot
all_categories = ['OBP', 'R', 'RBI', 'SB', 'TB', 'ERA', 'WHIP', 'QS', 'K', 'SVHD']
selected_stat = st.selectbox("Select stats to view", all_categories)

# Plot for each selected stat

# Calculate 10% below the minimum and 10% above the maximum of the 'period' column
min_stat = df[selected_stat].min()
max_stat = df[selected_stat].max()

# Define the range by taking 10% of the min and max values
y_min = min_stat - 0.05 * (max_stat - min_stat)
y_max = max_stat + 0.05 * (max_stat - min_stat)

week = df["period"].max()
with st.container():
    # Create the Altair chart
    chart_title = f"{selected_stat} - Over The Season (Updated through Week {week})"
    if selected_stat in ["OBP", "ERA", "WHIP"]:
        y_axis_format = ".3f"  # 3 decimal places
    else:
        y_axis_format = None  # Default formatting

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("period:O", title="Week"),
        y=alt.Y(
            f"{selected_stat}:Q",
            title=selected_stat,
            scale=alt.Scale(domain=[y_min, y_max]),
            axis=alt.Axis(format=y_axis_format) if y_axis_format else alt.Axis()
        ),
        color=alt.Color("team:N", legend=alt.Legend(title="Team"))
        ,
        tooltip=[
            alt.Tooltip("team:N", title="Team"),  # This ensures "Team" is capitalized in the tooltip
            alt.Tooltip(f"{selected_stat}:Q", title=selected_stat),
            alt.Tooltip("period:O", title="Week")
        ]

    ).properties(
        title=chart_title,
        width=3000,
        height=750
    )
    st.altair_chart(chart, use_container_width=True)
