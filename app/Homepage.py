import streamlit as st
import os
import sqlite3

st.set_page_config(layout="wide")

db_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'paychex.lg.db')

conn = sqlite3.connect(db_path)

cursor = conn.cursor()

# Query to get the maximum value of a specific column, e.g., 'OBP' from the 'cumulative' table
cursor.execute("SELECT MAX(period) FROM boxscore_wide")

period = cursor.fetchone()[0]

conn.commit()
conn.close()

st.title("🏟️ Paychex Baseball League Dashboard")
st.write(f"📊 Data last updated through **Week {period}**")
st.write("Welcome to the 2025 season dashboard! Use the sidebar to explore different views of your league’s performance.")
st.markdown("---")

st.subheader("📈 Stat Chart")
st.write(
    "Track cumulative totals for each stat week by week — every category is up for a prize. "
    "As the season unfolds, this chart will highlight the frontrunners in key categories like OBP, Runs, ERA, and more. "
    "Use it to see where your team stands in the race for end-of-season stat awards."
)

st.subheader("🏅 Power Score")
st.write(
    "This ranking uses a roto-style approach, combining ranks from each stat category. "
    "A lower score means a more balanced and dominant team across all metrics. Use this to spot teams that might be over- or under-performing in head-to-head matchups."
)

st.subheader("🧭 Team Radar")
st.write(
    "Visualize each team's strengths and weaknesses using radar charts. "
    "Each axis represents a different stat category, and each team's line traces their **rank** in those stats. "
    "**The farther a point is from the center, the better the team ranks** (with 1st place being at the outer edge). "
    "Conversely, points closer to the center indicate lower rankings in that category. "
    "Use this to quickly spot your team's strongest and weakest areas based on **total season stats** so far."
)
