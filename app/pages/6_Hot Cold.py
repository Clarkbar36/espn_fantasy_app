import streamlit as st
import pandas as pd
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

HITTING_CATS = ['OBP', 'R', 'RBI', 'SB', 'TB']
PITCHING_CATS = ['ERA', 'WHIP', 'QS', 'K', 'SVHD']
# For these stats, lower is better
LOWER_IS_BETTER = ['ERA', 'WHIP']


@st.cache_data(ttl=72000)
def load_hot_cold_data():
    engine = get_engine()

    # Get cumulative powerscore data
    query = '''
        SELECT cp.period, cp."PowerScore", t."teamName", t."teamAbbrev", cp."teamId"
        FROM cum_powerscore cp
        LEFT JOIN teams t ON cp."teamId" = t."teamId"
        ORDER BY cp.period
    '''
    df = pd.read_sql(query, engine)

    max_period = df['period'].max()

    # Calculate week-over-week PowerScore change
    results = []
    for team_id in df['teamId'].unique():
        team_df = df[df['teamId'] == team_id].sort_values('period')
        team_name = team_df['teamName'].iloc[0]
        team_abbrev = team_df['teamAbbrev'].iloc[0]

        current_score = team_df[team_df['period'] == max_period]['PowerScore'].values
        if len(current_score) == 0:
            continue
        current_score = current_score[0]

        # Last week's score
        prev_score = team_df[team_df['period'] == max_period - 1]['PowerScore'].values
        if len(prev_score) > 0:
            one_week_change = current_score - prev_score[0]
        else:
            one_week_change = 0

        # Two weeks ago score
        prev2_score = team_df[team_df['period'] == max_period - 2]['PowerScore'].values
        if len(prev2_score) > 0:
            two_week_change = current_score - prev2_score[0]
        else:
            two_week_change = one_week_change

        # Season average (average of all periods)
        season_avg = team_df['PowerScore'].mean()
        vs_avg = current_score - season_avg

        results.append({
            'Team': team_name,
            'Abbrev': team_abbrev,
            'Current': current_score,
            '1 Week': one_week_change,
            '2 Weeks': two_week_change,
            'vs Avg': vs_avg,
            'Trend': one_week_change  # Primary sort column
        })

    return pd.DataFrame(results), max_period


df, current_week = load_hot_cold_data()

st.title("Hot & Cold Teams")
st.caption(f"Week {current_week} - Showing PowerScore momentum. Positive = trending up.")

# Show warning if not enough data
if current_week < 2:
    st.info("Need at least 2 weeks of data to show trends. Check back after Week 2!")
elif current_week < 3:
    st.info("2-week trends will be available after Week 3.")

# Sort options
sort_by = st.radio("Sort by", ["1 Week Change", "2 Week Change", "vs Season Avg"], horizontal=True)

sort_col = {'1 Week Change': '1 Week', '2 Week Change': '2 Weeks', 'vs Season Avg': 'vs Avg'}[sort_by]
df_sorted = df.sort_values(sort_col, ascending=False)


def color_trend(val):
    if val > 2:
        return 'background-color: #1e5631; color: white'
    elif val > 0:
        return 'background-color: #4a7c59; color: white'
    elif val < -2:
        return 'background-color: #8b0000; color: white'
    elif val < 0:
        return 'background-color: #c45c5c; color: white'
    return ''


# Format the dataframe
display_df = df_sorted[['Team', 'Current', '1 Week', '2 Weeks', 'vs Avg']].copy()
display_df['Current'] = display_df['Current'].round(1)
display_df['1 Week'] = display_df['1 Week'].apply(lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}")
display_df['2 Weeks'] = display_df['2 Weeks'].apply(lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}")
display_df['vs Avg'] = display_df['vs Avg'].apply(lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}")

st.dataframe(display_df, use_container_width=True, hide_index=True)

# Hot and Cold sections
col1, col2 = st.columns(2)

with col1:
    st.subheader("Hottest Teams")
    hot_teams = df.nlargest(3, '1 Week')[['Team', '1 Week']]
    hot_teams['1 Week'] = hot_teams['1 Week'].apply(lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}")
    for _, row in hot_teams.iterrows():
        st.success(f"**{row['Team']}**: {row['1 Week']}")

with col2:
    st.subheader("Coldest Teams")
    cold_teams = df.nsmallest(3, '1 Week')[['Team', '1 Week']]
    cold_teams['1 Week'] = cold_teams['1 Week'].apply(lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}")
    for _, row in cold_teams.iterrows():
        st.error(f"**{row['Team']}**: {row['1 Week']}")
