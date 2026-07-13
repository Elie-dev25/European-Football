import inspect
from pipelines.transformers.silver_team_attributes import fetch_raw_team_attributes


def test_fetch_raw_team_attributes_filters_on_raw_match():
    """La requête doit filtrer dynamiquement sur les équipes présentes dans
    RAW.MATCH (home et away), sans réduire le grain équipe x date."""
    source = inspect.getsource(fetch_raw_team_attributes)
    assert "home_team_api_id FROM FOOTBALL_DB.RAW.MATCH" in source
    assert "away_team_api_id FROM FOOTBALL_DB.RAW.MATCH" in source
    assert "GROUP BY" not in source.upper()
    assert "DISTINCT team_api_id" not in source