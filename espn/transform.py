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

        # Keep only latest date per team/period to avoid duplicates
        data = data.sort_values('DATE').groupby(['teamId', 'period'], as_index=False).last()

        cols = ['teamId', 'period'] + list(categories.keys())
        data = data[cols]

        data = data.groupby("period", group_keys=False).apply(
            lambda g: rank_week(g, categories)
        )

        # Now it's safe to sort (higher PowerScore = better)
        data = data.sort_values(["period", "PowerScore"], ascending=[True, False])

        return data


def collect_h2h_matchups(league):
    """Collect all completed H2H matchup results for the season."""
    completed_periods = league.currentMatchupPeriod - 1
    if completed_periods < 1:
        return pd.DataFrame(columns=['season', 'period', 'home_team_id', 'away_team_id',
                                     'winner', 'home_cat_wins', 'away_cat_wins'])

    records = []
    for period in range(1, completed_periods + 1):
        box_scores = league.box_scores(matchup_period=period)
        for box in box_scores:
            if box.away_team is None:
                continue

            if box.home_wins > box.away_wins:
                winner = 'HOME'
            elif box.away_wins > box.home_wins:
                winner = 'AWAY'
            else:
                winner = 'TIE'

            records.append({
                'season': league.year,
                'period': period,
                'home_team_id': box.home_team.team_id,
                'away_team_id': box.away_team.team_id,
                'winner': winner,
                'home_cat_wins': box.home_wins,
                'away_cat_wins': box.away_wins,
            })

    return pd.DataFrame(records)


def build_h2h_record_matrix(h2h_df, teams_df, season=None):
    """Build a W-L-T record matrix from H2H matchup data."""
    if season is not None:
        h2h_df = h2h_df[h2h_df['season'] == season]

    teams = dict(zip(teams_df['teamId'], teams_df['teamName']))
    team_ids = list(teams.keys())

    h2h = {tid: {oid: {'w': 0, 'l': 0, 't': 0} for oid in team_ids} for tid in team_ids}

    for _, row in h2h_df.iterrows():
        home_id = row['home_team_id']
        away_id = row['away_team_id']

        if row['winner'] == 'HOME':
            h2h[home_id][away_id]['w'] += 1
            h2h[away_id][home_id]['l'] += 1
        elif row['winner'] == 'AWAY':
            h2h[home_id][away_id]['l'] += 1
            h2h[away_id][home_id]['w'] += 1
        else:
            h2h[home_id][away_id]['t'] += 1
            h2h[away_id][home_id]['t'] += 1

    matrix_data = []
    for tid in team_ids:
        row = {'Team': teams[tid]}
        for oid in team_ids:
            if tid == oid:
                row[teams[oid]] = '-'
            else:
                r = h2h[tid][oid]
                row[teams[oid]] = f"{r['w']}-{r['l']}-{r['t']}"
        matrix_data.append(row)

    return pd.DataFrame(matrix_data).set_index('Team')


def build_h2h_category_matrix(h2h_df, teams_df, season=None):
    """Build a total category wins matrix from H2H matchup data."""
    if season is not None:
        h2h_df = h2h_df[h2h_df['season'] == season]

    teams = dict(zip(teams_df['teamId'], teams_df['teamName']))
    team_ids = list(teams.keys())

    cat_wins = {tid: {oid: 0 for oid in team_ids} for tid in team_ids}

    for _, row in h2h_df.iterrows():
        home_id = row['home_team_id']
        away_id = row['away_team_id']
        cat_wins[home_id][away_id] += row['home_cat_wins']
        cat_wins[away_id][home_id] += row['away_cat_wins']

    matrix_data = []
    for tid in team_ids:
        row = {'Team': teams[tid]}
        for oid in team_ids:
            if tid == oid:
                row[teams[oid]] = '-'
            else:
                row[teams[oid]] = str(cat_wins[tid][oid])
        matrix_data.append(row)

    return pd.DataFrame(matrix_data).set_index('Team')
