import pandas as pd




def create_team_df(team_stats, team_name, matchup_period):
    df = pd.DataFrame.from_dict(team_stats, orient='index', columns=['value', 'result'])
    df.reset_index(inplace=True)
    df.columns = ['stat', 'value', 'result']
    df['team'] = team_name
    df['period'] = matchup_period
    return df

 # Function to rank per week
def rank_week(group, categories):
    for stat, high_is_better in categories.items():
        group[f'{stat}_rank'] = group[stat].rank(
            ascending=not high_is_better, method='min'
        )
    rank_cols = [f'{stat}_rank' for stat in categories]
    group['PowerScore'] = group[rank_cols].sum(axis=1)
    return group

def transform_matchups(matchups, matchup_id):
    matchup_dfs = []

    for match in matchups:
        away_team_df = create_team_df(match.away_stats, match.away_team.team_name, matchup_id)
        home_team_df = create_team_df(match.home_stats, match.home_team.team_name, matchup_id)

        # Combine both dataframes into a single one for the matchup
        matchup_dfs.append(pd.concat([away_team_df, home_team_df]))

    all_matchups = pd.concat(matchup_dfs, ignore_index=True)

    pivoted_matchups = all_matchups.pivot_table(
        index=['team', 'period'],  # group by these
        columns='stat',  # columns will be each stat
        values='value',  # values come from this column
        aggfunc='sum'  # just in case you have duplicates
    ).reset_index()

    return pivoted_matchups

def powerscore(type):
    from espn import read_table
    # Define the categories
    categories = {
        'OBP': True,
        'R': True,
        'RBI': True,
        'SB': True,
        'TB': True,
        'RC': True,
        'ERA': False,
        'WHIP': False,
        'QS': True,
        'K': True,
        'SVHD': True
    }
    if type == 'total':
        data = read_table(db='paychex.lg', table_name='totals')

        cols = ['team'] + list(categories.keys())
        data = data[cols]

        # Create rankings per stat
        for stat, ascending in categories.items():
            data[f'{stat}_rank'] = data[stat].rank(ascending=not ascending, method='min')  # lower rank is better

        # Compute power score
        rank_cols = [f'{stat}_rank' for stat in categories]
        data['PowerScore'] = data[rank_cols].sum(axis=1)

        # Sort by power score
        data = data.sort_values(by='PowerScore')

        return data
    else:
        data = read_table(db='paychex.lg', table_name='cumulative')
        cols = ['team', 'period'] + list(categories.keys())
        data = data[cols]

        data = data.groupby("period", group_keys=False).apply(
            lambda g: rank_week(g, categories)
        )

        # Now it's safe to sort
        data = data.sort_values(["period", "PowerScore"])

        return data
