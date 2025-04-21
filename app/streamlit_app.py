import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'paychex.lg.db')
conn = sqlite3.connect(db_path)

# Load data
df = pd.read_sql("SELECT * FROM boxscore_wide", conn)

# Select categories to plot
all_categories = ['OBP', 'R', 'RBI', 'SB', 'TB', 'RC', 'ERA', 'WHIP', 'QS', 'K', 'SVHD']
selected_stats = st.multiselect("Select stats to view", all_categories, default=['TB'])

# Plot for each selected stat
for stat in selected_stats:
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("period:O", title="Period"),
        y=alt.Y(f"{stat}:Q", title=stat),
        color="team:N"
    ).properties(
        title=f"{stat} Over Time",
        width=1800,
        height=750
    )
    st.altair_chart(chart, use_container_width=True)
