from espn import get_league, get_teams, get_draft, transform_matchups, write_table, powerscore, upsert_by_date
from datetime import date

league = get_league()

if date.today() == date(date.today().year, 3, 30) and len(league.draft) > 0:
    draft = get_draft(league, league.year)

    write_table(data=draft, table_name='draft', append_type='append')

teams = get_teams(league)

write_table(data=teams, table_name='teams', append_type='replace')

#matchup_id = newest_matchup()

matchups = league.box_scores(matchup_period=league.currentMatchupPeriod)

matchups_to_load = transform_matchups(matchups, league.currentMatchupPeriod)

today = date.today().strftime("%m-%d-%Y")
upsert_by_date(data=matchups_to_load, table_name='boxscore_wide', date_value=today)

total_powerscore = powerscore('total')
write_table(data=total_powerscore, table_name='total_powerscore', append_type='replace')

cum_powerscore = powerscore('cumulative')
write_table(data=cum_powerscore, table_name='cum_powerscore', append_type='replace')

## table for stats daily, for graphic

