import inspect
from pipelines.transformers.silver_league import fetch_raw_league


def test_fetch_raw_league_filters_on_raw_match():
    """La requête doit filtrer dynamiquement sur les league_id présents dans RAW.MATCH,
    et non sur une liste d'IDs codée en dur."""
    source = inspect.getsource(fetch_raw_league)
    assert "SELECT DISTINCT league_id FROM FOOTBALL_DB.RAW.MATCH" in source
    assert "FOOTBALL_DB.RAW.LEAGUE" in source