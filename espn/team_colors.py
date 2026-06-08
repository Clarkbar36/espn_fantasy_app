from functools import lru_cache
import plotly.express as px

_PALETTE = px.colors.qualitative.Plotly


@lru_cache(maxsize=1)
def get_team_colors() -> dict:
    """Stable teamAbbrev -> hex color mapping, ordered alphabetically."""
    from espn.sql_io import get_engine
    import pandas as pd

    engine = get_engine()
    teams = pd.read_sql('SELECT "teamAbbrev" FROM teams ORDER BY "teamAbbrev"', engine)
    return {abbrev: _PALETTE[i % len(_PALETTE)] for i, abbrev in enumerate(teams['teamAbbrev'])}
