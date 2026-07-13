import inspect
from pipelines.transformers.silver_top_assists import fetch_raw_top_assists


def test_fetch_raw_top_assists_filters_on_raw_fixtures():
    """La requête doit filtrer dynamiquement sur les équipes présentes dans
    RAW.FIXTURES (home et away), sans réduire le grain joueur x équipe x ligue x saison."""
    source = inspect.getsource(fetch_raw_top_assists)
    assert "home_team_id FROM FOOTBALL_DB.RAW.FIXTURES" in source
    assert "away_team_id FROM FOOTBALL_DB.RAW.FIXTURES" in source
    assert "GROUP BY" not in source.upper()
    assert "DISTINCT player_id" not in source