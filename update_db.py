from espn import get_league, newest_matchup, transform_matchups, write_table, powerscore

league = get_league()

matchup_id = newest_matchup(db = 'paychex.lg')

matchups = league.box_scores(matchup_period=matchup_id)

matchups_to_load = transform_matchups(matchups, matchup_id)

write_table(db = 'paychex.lg', data = matchups_to_load, table_name= 'boxscore_wide', append_type= 'append')

total_powerscore = powerscore('total')
write_table(db = 'paychex.lg', data = total_powerscore, table_name= 'total_powerscore', append_type= 'replace')

cum_powerscore = powerscore('cumulative')
write_table(db = 'paychex.lg', data = cum_powerscore, table_name= 'cum_powerscore', append_type= 'replace')

