import inspect
from pipelines.transformers.silver_standings import fetch_raw_standings


def test_fetch_raw_standings_filters_on_raw_fixtures():
    """La requête doit filtrer dynamiquement sur les équipes présentes dans
    RAW.FIXTURES (home et away), sans réduire le grain équipe x ligue x saison."""
    source = inspect.getsource(fetch_raw_standings)
    assert "home_team_id FROM FOOTBALL_DB.RAW.FIXTURES" in source
    assert "away_team_id FROM FOOTBALL_DB.RAW.FIXTURES" in source
    assert "GROUP BY" not in source.upper()
    assert "DISTINCT team_id" not in source