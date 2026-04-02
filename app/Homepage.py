import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from espn.sql_io import get_engine
from sqlalchemy import text

st.set_page_config(layout="wide")


def get_current_period():
    engine = get_engine()
    with engine.connect() as conn:
        period = conn.execute(text("SELECT MAX(period) FROM boxscore_wide")).scalar()
        max_date = conn.execute(text("SELECT MAX(\"DATE\") FROM boxscore_wide")).scalar()
        return period, max_date


period, max_date = get_current_period()

st.title("Paychex Baseball League Dashboard")
st.write(f"Data last updated through **{max_date}**")
st.write("Welcome to the 2026 season dashboard! Use the sidebar to explore different views of your team's performance.")
st.markdown("---")


st.subheader("Stat Race")
st.write(
    "Track the race for each stat category with a **bump chart** showing rank over time. "
    "See the current standings and watch how positions have changed throughout the season. "
    "Winner of each stat at season end gets paid out!"
)

st.subheader("Power Score")
st.write(
    "This ranking uses a roto-style approach, combining ranks from each stat category. "
    "A higher score means a more balanced and dominant team across all metrics. Use this to spot teams that might be over- or under-performing in head-to-head matchups."
)

st.subheader("Splits")
st.write(
    "Break down team performance into **Hitting** and **Pitching** scores. "
    "See which teams are one-dimensional vs. well-rounded with a scatter plot showing hitting vs. pitching performance. "
    "Teams in the top-right are elite in both; bottom-left are struggling across the board."
)

st.subheader("PowerScore Trends")
st.write(
    "Track how each team's PowerScore has changed **week-to-week** throughout the season. "
    "Use this to identify teams that are surging or fading as the season progresses."
)

st.subheader("Hot & Cold")
st.write(
    "See which teams are **trending up or down** based on recent performance. "
    "Compare each team's current PowerScore to last week, two weeks ago, and their season average. "
    "Quickly spot the hottest and coldest teams in the league."
)

st.subheader("Distributions")
st.write(
    "Visualize the **league-wide distribution** for each stat category using box plots. "
    "Highlight a specific team to see where they fall in each distribution and view their percentile rankings. "
    "Great for understanding if a team is an outlier or middle-of-the-pack in key categories."
)

st.subheader("Team Radar")
st.write(
    "Visualize each team's strengths and weaknesses using radar charts. "
    "Each axis represents a different stat category, and each team's line traces their **rank** in those stats. "
    "**The farther a point is from the center, the better the team ranks** (with 1st place being at the outer edge). "
    "Conversely, points closer to the center indicate lower rankings in that category. "
    "Use this to quickly spot your team's strongest and weakest areas based on **total season stats** so far."
)
