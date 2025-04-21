import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem;
        }
    </style>
""", unsafe_allow_html=True)

# Set up DB path
db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'paychex.lg.db')
conn = sqlite3.connect(db_path)

# Load data
query = '''SELECT team AS Team,
 PowerScore,
 OBP_rank AS'OBP Rank',
 R_rank AS 'R Rank',
 RBI_rank AS 'RBI Rank',
 SB_rank AS 'SB Rank',
 TB_rank AS 'TB Rank',
 RC_rank AS 'RC Rank',
 ERA_rank AS 'ERA Rank',
 WHIP_rank AS 'WHIP Rank',
 QS_rank AS 'QS Rank',
 K_rank AS 'K Rank',
 SVHD_rank AS 'SVHLD Rank'
 FROM total_powerscore'''
df = pd.read_sql(query, conn)

cursor = conn.cursor()

# Query to get the maximum value of a specific column, e.g., 'OBP' from the 'cumulative' table
cursor.execute("SELECT MAX(period) FROM boxscore_wide")

period = cursor.fetchone()[0]

conn.commit()
conn.close()

with st.container():
    # Display header
    st.title("Power Score Table")
    st.caption(f"Updated through Week {period}. Ranked stats (1 = best).")

    # Sort by PowerScore descending
    df_sorted = df.sort_values(by="PowerScore", ascending=True)

    # Round ranks for cleaner display
    rank_columns = [col for col in df.columns if col.endswith("_rank")]
    df_sorted[rank_columns] = df_sorted[rank_columns].round(1)

    # Show table
    st.dataframe(df_sorted, use_container_width=True, hide_index=True)
