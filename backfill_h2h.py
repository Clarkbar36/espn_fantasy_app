"""Backfill H2H matchup data for previous seasons."""
from espn_api.baseball import League
from espn import collect_h2h_matchups, write_h2h_matchups
from dotenv import load_dotenv
import os
import sys

load_dotenv()

def backfill_season(year):
    print(f"Fetching {year} season data...")
    league = League(
        league_id=int(os.getenv("LEAGUE_ID")),
        year=year,
        espn_s2=os.getenv("ESPN_S2"),
        swid=os.getenv("SWID")
    )

    h2h_data = collect_h2h_matchups(league)

    if h2h_data.empty:
        print(f"  No completed matchups found for {year}")
        return

    print(f"  Found {len(h2h_data)} matchups across {h2h_data['period'].max()} periods")
    write_h2h_matchups(h2h_data, year)
    print(f"  Saved to database")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]
    else:
        years = [2025]

    for year in years:
        backfill_season(year)

    print("Done!")
