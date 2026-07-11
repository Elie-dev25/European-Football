import pandas as pd
from pipelines.transformers.silver_match_core import join_match_team


def test_join_match_team_resolves_home_and_away_names():
    """Vérifie que les noms d'équipes home/away sont correctement résolus,
    sans mélange entre les deux côtés."""
    match_df = pd.DataFrame({
        "match_api_id": [1],
        "home_team_api_id": [100],
        "away_team_api_id": [200],
        "home_team_goal": [2],
        "away_team_goal": [1],
    })
    team_df = pd.DataFrame({
        "team_api_id": [100, 200],
        "team_long_name": ["FC Domicile", "FC Extérieur"],
        "team_short_name": ["DOM", "EXT"],
        "team_fifa_api_id": [1001, 1002],
    })

    result = join_match_team(match_df, team_df)

    assert result.loc[0, "home_team_name"] == "FC Domicile"
    assert result.loc[0, "away_team_name"] == "FC Extérieur"
    assert result.loc[0, "home_team_short_name"] == "DOM"
    assert result.loc[0, "away_team_short_name"] == "EXT"
    assert result.loc[0, "home_team_fifa_id"] == 1001
    assert result.loc[0, "away_team_fifa_id"] == 1002


def test_join_match_team_handles_missing_team_id():
    """Vérifie qu'un ID équipe absent de TEAM produit des NaN (pas d'erreur),
    cas théorique jamais rencontré en pratique (0 orphelin vérifié)."""
    match_df = pd.DataFrame({
        "match_api_id": [1],
        "home_team_api_id": [999],  # absent de team_df
        "away_team_api_id": [200],
        "home_team_goal": [0],
        "away_team_goal": [0],
    })
    team_df = pd.DataFrame({
        "team_api_id": [200],
        "team_long_name": ["FC Extérieur"],
        "team_short_name": ["EXT"],
        "team_fifa_api_id": [1002],
    })

    result = join_match_team(match_df, team_df)

    assert pd.isna(result.loc[0, "home_team_name"])
    assert result.loc[0, "away_team_name"] == "FC Extérieur"


def test_join_match_team_preserves_row_count():
    """La jointure ne doit ni dupliquer ni perdre de lignes (grain inchangé,
    1 ligne match_api_id en entrée = 1 ligne en sortie)."""
    match_df = pd.DataFrame({
        "match_api_id": [1, 2, 3],
        "home_team_api_id": [100, 100, 200],
        "away_team_api_id": [200, 300, 100],
        "home_team_goal": [1, 0, 2],
        "away_team_goal": [1, 3, 0],
    })
    team_df = pd.DataFrame({
        "team_api_id": [100, 200, 300],
        "team_long_name": ["A", "B", "C"],
        "team_short_name": ["A", "B", "C"],
        "team_fifa_api_id": [1, 2, 3],
    })

    result = join_match_team(match_df, team_df)

    assert len(result) == len(match_df)
    assert result["match_api_id"].is_unique