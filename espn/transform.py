import pandas as pd
from datetime import date

def get_teams(league):
    teams = league.teams
    owners_list = []
    for t in teams:
        owner_info = [{
            'teamId': t.team_id,
            'ownerID': t.owners[0]['id'],
            'teamName': t.team_name,
            'teamAbbrev': t.team_abbrev,
            'ownerName': t.owners[0]['firstName'].title().strip() + ' ' + t.owners[0]['lastName'].title().strip(),
        }]
        owners_list.append(owner_info[0])

    owners_df = pd.DataFrame(owners_list)
    return owners_df

def get_draft(league, lg_year):
    draft = league.draft
    draft_list = []
    for d in draft:
        pick_info = [{'year': lg_year,
                      'round': d.round_num,
                      'roundPick': d.round_pick,
                      'playerId': d.playerId,
                      'playerName': d.playerName,
                      'keeperStatus': d.keeper_status,
                      'teamName': d.team.team_name,
                      'teamID': d.team.team_id,
                      'ownerName': d.team.owners[0]['firstName'].title().strip() + ' ' + d.team.owners[0][
                          'lastName'].title().strip(),
                      'ownerID': d.team.owners[0]['id'],
                      }]
        draft_list.append(pick_info[0])

    draft_df = pd.DataFrame(draft_list)
    return draft_df

def create_team_df(team_stats, team_id, matchup_period):
    df = pd.DataFrame.from_dict(team_stats, orient='index', columns=['value', 'result'])
    df.reset_index(inplace=True)
    df.columns = ['stat', 'value', 'result']
    df['teamId'] = team_id
    df['period'] = matchup_period
    return df

 # Function to rank per week
def rank_week(group, categories):
    num_teams = len(group)
    for stat, high_is_better in categories.items():
        group[f'{stat}_rank'] = group[stat].rank(
            ascending=not high_is_better, method='min'
        )
    rank_cols = [f'{stat}_rank' for stat in categories]
    # Higher PowerScore = better (convert ranks so rank 1 gives most points)
    group['PowerScore'] = sum((num_teams + 1 - group[col]) for col in rank_cols)
    return group

def transform_matchups(matchups, matchup_id):
    matchup_dfs = []

    for match in matchups:
        away_team_df = create_team_df(match.away_stats, match.away_team.team_id, matchup_id)
        home_team_df = create_team_df(match.home_stats, match.home_team.team_id, matchup_id)

        # Combine both dataframes into a single one for the matchup
        matchup_dfs.append(pd.concat([away_team_df, home_team_df]))

    all_matchups = pd.concat(matchup_dfs, ignore_index=True)

    pivoted_matchups = all_matchups.pivot_table(
        index=['teamId', 'period'],  # group by these
        columns='stat',  # columns will be each stat
        values='value',  # values come from this column
        aggfunc='sum'  # just in case you have duplicates
    ).reset_index()

    pivoted_matchups['DATE'] = date.today().strftime("%m-%d-%Y")
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
        data = read_table(table_name='totals')

        cols = ['teamId'] + list(categories.keys())
        data = data[cols]
        num_teams = len(data)

        # Create rankings per stat (rank 1 = best)
        for stat, ascending in categories.items():
            data[f'{stat}_rank'] = data[stat].rank(ascending=not ascending, method='min')

        # Compute power score (higher = better)
        rank_cols = [f'{stat}_rank' for stat in categories]
        data['PowerScore'] = sum((num_teams + 1 - data[col]) for col in rank_cols)

        # Sort by power score (descending - higher is better)
        data = data.sort_values(by='PowerScore', ascending=False)

        return data
    else:
        data = read_table(table_name='cumulative')
        cols = ['teamId', 'period'] + list(categories.keys())
        data = data[cols]

        data = data.groupby("period", group_keys=False).apply(
            lambda g: rank_week(g, categories)
        )

        # Now it's safe to sort (higher PowerScore = better)
        data = data.sort_values(["period", "PowerScore"], ascending=[True, False])

        return data
