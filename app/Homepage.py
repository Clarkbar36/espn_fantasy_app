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

# Debug: show which database we're connected to
db_url = os.getenv('DATABASE_URL', 'SQLite (no DATABASE_URL set)')
st.caption(f"DB: {db_url[:30]}..." if len(db_url) > 30 else f"DB: {db_url}")

st.title("Paychex Baseball League Dashboard")
st.write(f"Data last updated through **Week {period}** ({max_date})")
st.write("Welcome to the 2026 season dashboard! Use the sidebar to explore different views of your team's performance.")
st.markdown("---")

st.subheader("Stat Chart")
st.write(
    "Track cumulative totals for each stat week by week. "
    "As the season unfolds, this chart will highlight the frontrunners in key categories like OBP, Runs, ERA, and more. "
    "Use it to see where your team stands in the race for end-of-season stat awards."
)

st.subheader("Power Score")
st.write(
    "This ranking uses a roto-style approach, combining ranks from each stat category. "
    "A lower score means a more balanced and dominant team across all metrics. Use this to spot teams that might be over- or under-performing in head-to-head matchups."
)

st.subheader("Team Radar")
st.write(
    "Visualize each team's strengths and weaknesses using radar charts. "
    "Each axis represents a different stat category, and each team's line traces their **rank** in those stats. "
    "**The farther a point is from the center, the better the team ranks** (with 1st place being at the outer edge). "
    "Conversely, points closer to the center indicate lower rankings in that category. "
    "Use this to quickly spot your team's strongest and weakest areas based on **total season stats** so far."
)
