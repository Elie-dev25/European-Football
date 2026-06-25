"""
Tests pour pipelines/utils.py

Philosophie : aucune dépendance aux vrais fichiers dbt/seeds/.
Tous les CSV sont créés dans des répertoires temporaires (fixture tmp_path),
détruits automatiquement après chaque test.
"""

import pytest
from pathlib import Path

from pipelines.utils import (
    normalize_league_name,
    build_filepath,
    load_leagues,
    load_stadiums,
)


# =============================================================================
# normalize_league_name
# =============================================================================

class TestNormalizeLeagueName:

    def test_simple_name(self):
        assert normalize_league_name("Premier League") == "premier_league"

    def test_name_with_number(self):
        # "Ligue 1" doit garder le chiffre, seul l'espace devient underscore
        assert normalize_league_name("Ligue 1") == "ligue_1"

    def test_single_word(self):
        assert normalize_league_name("Bundesliga") == "bundesliga"

    def test_already_lowercase(self):
        assert normalize_league_name("serie a") == "serie_a"

    def test_multiple_spaces_collapsed_individually(self):
        # Chaque espace devient un underscore : pas de collapse, comportement attendu
        # de .replace(" ", "_") — un double espace donne un double underscore.
        assert normalize_league_name("La  Liga") == "la__liga"

    def test_mixed_case(self):
        assert normalize_league_name("PREMIER LEAGUE") == "premier_league"


# =============================================================================
# build_filepath
# =============================================================================

class TestBuildFilepath:

    def test_standard_path(self):
        result = build_filepath(
            Path("data/raw/api_football"), "Premier League", 2022, "fixtures"
        )
        assert result == Path("data/raw/api_football/premier_league_2022_fixtures.json")

    def test_different_data_type(self):
        result = build_filepath(
            Path("data/raw/api_football"), "Ligue 1", 2022, "standings"
        )
        assert result == Path("data/raw/api_football/ligue_1_2022_standings.json")

    def test_weather_data_type(self):
        result = build_filepath(
            Path("data/raw/api_weather"), "Serie A", 2023, "weather"
        )
        assert result == Path("data/raw/api_weather/serie_a_2023_weather.json")

    def test_returns_path_object(self):
        result = build_filepath(Path("base"), "Bundesliga", 2022, "fixtures")
        assert isinstance(result, Path)

    def test_season_as_int_in_filename(self):
        # season est un int dans la signature ; vérifie qu'il s'intègre
        # correctement dans le nom de fichier (pas de "2022.0" ou autre).
        result = build_filepath(Path("base"), "La Liga", 2022, "top_scorers")
        assert result.name == "la_liga_2022_top_scorers.json"


# =============================================================================
# load_leagues
# =============================================================================

class TestLoadLeagues:

    def test_loads_valid_csv(self, tmp_path):
        csv_path = tmp_path / "leagues.csv"
        csv_path.write_text(
            "league_name,league_id,country\n"
            "Premier League,39,England\n"
            "Ligue 1,61,France\n"
        )
        result = load_leagues(csv_path)
        assert result == {"Premier League": 39, "Ligue 1": 61}

    def test_returns_dict_type(self, tmp_path):
        csv_path = tmp_path / "leagues.csv"
        csv_path.write_text("league_name,league_id,country\nSerie A,135,Italy\n")
        result = load_leagues(csv_path)
        assert isinstance(result, dict)

    def test_missing_file_raises_filenotfounderror(self, tmp_path):
        missing_path = tmp_path / "does_not_exist.csv"
        with pytest.raises(FileNotFoundError):
            load_leagues(missing_path)

    def test_missing_file_error_message_mentions_path(self, tmp_path):
        missing_path = tmp_path / "leagues.csv"
        with pytest.raises(FileNotFoundError, match="leagues.csv"):
            load_leagues(missing_path)

    def test_single_league(self, tmp_path):
        csv_path = tmp_path / "leagues.csv"
        csv_path.write_text("league_name,league_id,country\nBundesliga,78,Germany\n")
        result = load_leagues(csv_path)
        assert result == {"Bundesliga": 78}

    def test_all_five_leagues(self, tmp_path):
        csv_path = tmp_path / "leagues.csv"
        csv_path.write_text(
            "league_name,league_id,country\n"
            "Premier League,39,England\n"
            "Ligue 1,61,France\n"
            "Bundesliga,78,Germany\n"
            "Serie A,135,Italy\n"
            "La Liga,140,Spain\n"
        )
        result = load_leagues(csv_path)
        assert len(result) == 5
        assert result["La Liga"] == 140

    def test_duplicate_league_name_last_wins(self, tmp_path):
        # Verrouille le comportement actuel de dict(zip(...)) :
        # en cas de doublon, la dernière valeur l'emporte silencieusement.
        csv_path = tmp_path / "leagues.csv"
        csv_path.write_text(
            "league_name,league_id,country\n"
            "Premier League,39,England\n"
            "Premier League,999,England\n"
        )
        result = load_leagues(csv_path)
        assert result["Premier League"] == 999


# =============================================================================
# load_stadiums
# =============================================================================

class TestLoadStadiums:

    def test_loads_valid_csv(self, tmp_path):
        csv_path = tmp_path / "stadiums.csv"
        csv_path.write_text(
            "team_name,stadium_name,city,latitude,longitude\n"
            "Arsenal,Emirates Stadium,London,51.5549,-0.1084\n"
            "Real Madrid,Santiago Bernabeu,Madrid,40.4531,-3.6883\n"
        )
        result = load_stadiums(csv_path)
        assert len(result) == 2
        assert list(result.columns) == [
            "team_name", "stadium_name", "city", "latitude", "longitude"
        ]

    def test_returns_dataframe_type(self, tmp_path):
        import pandas as pd
        csv_path = tmp_path / "stadiums.csv"
        csv_path.write_text(
            "team_name,stadium_name,city,latitude,longitude\n"
            "Arsenal,Emirates Stadium,London,51.5549,-0.1084\n"
        )
        result = load_stadiums(csv_path)
        assert isinstance(result, pd.DataFrame)

    def test_missing_file_raises_filenotfounderror(self, tmp_path):
        missing_path = tmp_path / "does_not_exist.csv"
        with pytest.raises(FileNotFoundError):
            load_stadiums(missing_path)

    def test_missing_file_error_message_mentions_generator_script(self, tmp_path):
        missing_path = tmp_path / "stadiums.csv"
        with pytest.raises(FileNotFoundError, match="generate_stadiums_seed.py"):
            load_stadiums(missing_path)

    def test_correct_values_loaded(self, tmp_path):
        csv_path = tmp_path / "stadiums.csv"
        csv_path.write_text(
            "team_name,stadium_name,city,latitude,longitude\n"
            "Southampton,St Mary's Stadium,Southampton,50.9085,-1.4042\n"
        )
        result = load_stadiums(csv_path)
        row = result.iloc[0]
        assert row["team_name"] == "Southampton"
        assert row["latitude"] == 50.9085
        assert row["longitude"] == -1.4042

    def test_empty_csv_with_headers_only(self, tmp_path):
        # Cas limite : fichier valide mais sans aucune ligne de données.
        csv_path = tmp_path / "stadiums.csv"
        csv_path.write_text("team_name,stadium_name,city,latitude,longitude\n")
        result = load_stadiums(csv_path)
        assert len(result) == 0