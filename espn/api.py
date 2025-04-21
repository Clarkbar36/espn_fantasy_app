from espn_api.baseball import League
from dotenv import load_dotenv
import os

load_dotenv()

def get_league():
    return League(league_id=int(os.getenv("LEAGUE_ID")),
                year=2025,
                espn_s2=os.getenv("ESPN_S2"),
                swid=os.getenv("SWID"),)

