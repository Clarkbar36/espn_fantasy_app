# espn/__init__.py

# Optionally expose your functions at the package level
from .api import get_league
from .transform import get_teams, get_draft, transform_matchups, powerscore, collect_h2h_matchups, build_h2h_record_matrix, build_h2h_category_matrix
from .sql_io import get_engine, newest_matchup, write_table, read_table, upsert_by_date, write_h2h_matchups, read_h2h_matchups

__all__ = [
    "get_engine",
    "get_league",
    "get_teams",
    "get_draft",
    "newest_matchup",
    "powerscore",
    "transform_matchups",
    "write_table",
    "read_table",
    "upsert_by_date",
    "collect_h2h_matchups",
    "build_h2h_record_matrix",
    "build_h2h_category_matrix",
    "write_h2h_matchups",
    "read_h2h_matchups",
]