"""
Tests des fonctions d'aplatissement, sur données réelles (pas synthétiques),
conformément à la règle "vérifier avant de deviner".
"""

import json
import math 
import pandas as pd
import pytest
import logging
import os
from pathlib import Path

import pytest

from pipelines.loaders.snowflake_flatteners import (
    flatten_fixtures, flatten_league, flatten_standings, flatten_team, flatten_team_attributes, 
    flatten_match, flatten_top_scorers, flatten_top_assists, flatten_weather,
    PLAYER_POSITION_COLUMNS, PLAYER_ID_COLUMNS, XML_COLUMNS,
)
LEAGUE_JSON_PATH = Path("data/raw/kaggle/League.json") 

TEAM_JSON_PATH = Path("data/raw/kaggle/team.json")  

TEAM_ATTRIBUTES_JSON_PATH = Path("data/raw/kaggle/team_attributes.json") 

MATCH_JSON_PATH = Path("data/raw/kaggle/match_2008_2016.json") 

FIXTURES_JSON_PATH = Path("data/raw/api_football/bundesliga_2022_fixtures.json") 

STANDINGS_JSON_PATH = Path("data/raw/api_football/bundesliga_2022_standings.json") 

TOP_SCORERS_JSON_PATH = Path("data/raw/api_football/bundesliga_2022_top_scorers.json")

TOP_ASSISTS_JSON_PATH = Path("data/raw/api_football/bundesliga_2022_top_assists.json")

WEATHER_JSON_PATH = Path("data/raw/api_weather/bundesliga_2022_weather.json")







@pytest.fixture
def real_league_json():
    with open(LEAGUE_JSON_PATH, encoding="utf-8") as f:
        return json.load(f) 
    
@pytest.fixture
def real_team_json():
    with open(TEAM_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)
    
@pytest.fixture
def real_team_attributes_json():
    with open(TEAM_ATTRIBUTES_JSON_PATH, encoding="utf-8") as f:
        return json.load(f) 
    
@pytest.fixture
def real_match_json():
    with open(MATCH_JSON_PATH, encoding="utf-8") as f:
        return json.load(f) 

@pytest.fixture
def real_fixtures_json():
    with open(FIXTURES_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["response"] 

@pytest.fixture
def real_standings_json():
    with open(STANDINGS_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["response"] 

@pytest.fixture
def real_top_scorers_json():
    with open(TOP_SCORERS_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["response"] 

@pytest.fixture
def real_top_assists_json():
    with open(TOP_ASSISTS_JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["response"] 


@pytest.fixture
def real_weather_json():
    with open(WEATHER_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)



class TestFlattenLeague:

    def test_renommage_et_structure_colonnes(self, real_league_json):
        """Les colonnes id/name doivent être renommées en league_id/league_name,
        et country_id conservé tel quel."""
        df = flatten_league(real_league_json)
        assert list(df.columns) == ["league_id", "country_id", "league_name"]

    def test_preservation_des_11_lignes_bronze_strict(self, real_league_json):
        """Bronze strict : aucune ligne ne doit être filtrée."""
        df = flatten_league(real_league_json)
        assert len(df) == 11

    def test_coherence_ligne_bundesliga(self, real_league_json):
        """Vérifie une ligne spécifique (Bundesliga, id 7809) contre la source."""
        df = flatten_league(real_league_json)
        bundesliga = df[df["league_id"] == 7809].iloc[0]
        assert bundesliga["league_name"] == "Germany 1. Bundesliga" 



class TestFlattenTeam:

    def test_structure_colonnes(self, real_team_json):
        """Les colonnes doivent correspondre exactement au schéma RAW.TEAM."""
        df = flatten_team(real_team_json)
        assert list(df.columns) == [
            "id", "team_api_id", "team_fifa_api_id", "team_long_name", "team_short_name"
        ]

    def test_preservation_des_299_lignes_bronze_strict(self, real_team_json):
        """Bronze strict : aucune ligne ne doit être filtrée."""
        df = flatten_team(real_team_json)
        assert len(df) == 299

    def test_conversion_team_fifa_api_id_en_entier(self, real_team_json):
        """team_fifa_api_id arrive en float dans le JSON (ex. 673.0),
        doit être converti en entier nullable dans le DataFrame."""
        df = flatten_team(real_team_json)
        assert df["team_fifa_api_id"].dtype == "Int64"

    def test_coherence_ligne_krc_genk(self, real_team_json):
        """Vérifie une ligne spécifique (KRC Genk, team_api_id 9987) contre la source."""
        df = flatten_team(real_team_json)
        genk = df[df["team_api_id"] == 9987].iloc[0]
        assert genk["team_fifa_api_id"] == 673
        assert genk["team_long_name"] == "KRC Genk"
        assert genk["team_short_name"] == "GEN" 



class TestFlattenTeamAttributes:

    def test_renommage_camelcase_vers_snake_case(self, real_team_attributes_json):
        """Toutes les colonnes camelCase du JSON doivent être renommées en snake_case."""
        df = flatten_team_attributes(real_team_attributes_json)
        assert "build_up_play_speed" in df.columns
        assert "buildUpPlaySpeed" not in df.columns

    def test_preservation_des_1458_lignes_bronze_strict(self, real_team_attributes_json):
        """Bronze strict : aucune ligne ne doit être filtrée."""
        df = flatten_team_attributes(real_team_attributes_json)
        assert len(df) == 1458

    def test_nan_convertis_en_null_pandas(self, real_team_attributes_json):
        """969 lignes ont buildUpPlayDribbling = NaN dans le JSON source :
        doivent devenir pd.NA (Int64 nullable), pas rester des float NaN."""
        df = flatten_team_attributes(real_team_attributes_json)
        assert df["build_up_play_dribbling"].dtype == "Int64"
        assert df["build_up_play_dribbling"].isna().sum() == 969

    def test_date_convertie_en_datetime(self, real_team_attributes_json):
        """La colonne date doit être un vrai datetime, pas une string."""
        df = flatten_team_attributes(real_team_attributes_json)
        assert pd.api.types.is_datetime64_any_dtype(df["date"])

    def test_coherence_premiere_ligne(self, real_team_attributes_json):
        """Vérifie la ligne d'exemple (id=1, team_api_id=9930, date 2010-02-22) contre la source."""
        df = flatten_team_attributes(real_team_attributes_json)
        row = df[df["id"] == 1].iloc[0]
        assert row["team_api_id"] == 9930
        assert row["build_up_play_speed"] == 60
        assert pd.isna(row["build_up_play_dribbling"])
        assert row["build_up_play_dribbling_class"] == "Little" 


class TestFlattenMatch:

    def test_nombre_de_colonnes(self, real_match_json):
        """115 colonnes attendues : identifiants/scores (11) + positions (44)
        + IDs joueurs (22) + XML (8) + cotes (30)."""
        df = flatten_match(real_match_json)
        assert len(df.columns) == 115

    def test_preservation_des_14585_lignes_bronze_strict(self, real_match_json):
        """Bronze strict : aucune ligne ne doit être filtrée."""
        df = flatten_match(real_match_json)
        assert len(df) == 14585

    def test_colonnes_joueurs_converties_en_int64(self, real_match_json):
        """Les 66 colonnes positions/IDs joueurs doivent être Int64 nullable,
        y compris celles sans NaN (le JSON mélange int/float pour une même
        colonne par endroits, ex. away_player_X10 vs away_player_X11)."""
        df = flatten_match(real_match_json)
        for col in PLAYER_POSITION_COLUMNS + PLAYER_ID_COLUMNS:
            assert df[col].dtype == "Int64"

    def test_nan_joueurs_preserves(self, real_match_json):
        """away_player_11 a 72 NaN confirmés dans le JSON source :
        doivent devenir pd.NA, pas être filtrés ou remplacés."""
        df = flatten_match(real_match_json)
        assert df["away_player_11"].isna().sum() == 72

    def test_colonnes_xml_non_parsees(self, real_match_json):
        """Les colonnes XML doivent rester des strings brutes, aucun parsing."""
        df = flatten_match(real_match_json)
        for col in XML_COLUMNS:
            assert df[col].dtype == object
            assert df[col].iloc[0].startswith(f"<{col}>")

    def test_cotes_nan_preserves(self, real_match_json):
        """PSH a 7293 NaN confirmés : doivent rester NaN, pas être filtrés."""
        df = flatten_match(real_match_json)
        assert df["PSH"].isna().sum() == 7293

    def test_date_convertie_en_string_iso(self, real_match_json):
        """date est convertie en string ISO ('YYYY-MM-DD HH:MM:SS'), pas laissée
        en datetime64[ns] pandas : évite un bug de précision nanoseconde qui
        fait planter la lecture via le client SnowSQL (Python int too large)."""
        df = flatten_match(real_match_json)
        assert df["date"].dtype == object
        assert df["date"].iloc[0] == "2008-08-17 00:00:00"

    def test_coherence_premiere_ligne(self, real_match_json):
        """Vérifie la ligne d'exemple (match_api_id 489042) contre la source."""
        df = flatten_match(real_match_json)
        row = df[df["match_api_id"] == 489042].iloc[0]
        assert row["home_team_api_id"] == 10260
        assert row["away_team_api_id"] == 10261
        assert row["home_team_goal"] == 1
        assert row["away_team_goal"] == 1
        assert row["B365H"] == 1.29
        assert pd.isna(row["PSH"]) 

class TestFlattenFixtures:

    def test_structure_colonnes(self, real_fixtures_json):
        df = flatten_fixtures(real_fixtures_json)
        expected = [
            "fixture_id", "referee", "match_date", "match_timestamp",
            "venue_id", "venue_name", "venue_city",
            "status_long", "status_short", "status_elapsed",
            "league_id", "league_name", "league_country", "season", "round",
            "home_team_id", "home_team_name", "home_winner",
            "away_team_id", "away_team_name", "away_winner",
            "goals_home", "goals_away",
            "halftime_home", "halftime_away",
            "fulltime_home", "fulltime_away",
            "extratime_home", "extratime_away",
            "penalty_home", "penalty_away",
        ]
        assert list(df.columns) == expected

    def test_preservation_des_308_lignes_bronze_strict(self, real_fixtures_json):
        """Bronze strict : aucune ligne ne doit être filtrée (1 ligue, 1 saison)."""
        df = flatten_fixtures(real_fixtures_json)
        assert len(df) == 308

    def test_matchs_nuls_winner_null_preserves(self, real_fixtures_json):
        """75 matchs sur 308 ont home_winner null (égalité) : doivent le rester,
        pas être filtrés ni convertis en False."""
        df = flatten_fixtures(real_fixtures_json)
        assert df["home_winner"].isna().sum() == 75

    def test_coherence_premier_match(self, real_fixtures_json):
        """Vérifie le match d'exemple (fixture_id 871164) contre la source."""
        df = flatten_fixtures(real_fixtures_json)
        row = df[df["fixture_id"] == 871164].iloc[0]
        assert row["venue_name"] == "Deutsche Bank Park"
        assert row["home_team_name"] == "Eintracht Frankfurt"
        assert row["away_team_name"] == "Bayern Munich"
        assert row["goals_home"] == 1
        assert row["goals_away"] == 6
        assert row["home_winner"] == False
        assert row["away_winner"] == True 



class TestFlattenStandings:

    def test_structure_colonnes(self, real_standings_json):
        df = flatten_standings(real_standings_json)
        expected = [
            "league_id", "league_name", "league_country", "season",
            "team_id", "team_name", "rank", "points", "goals_diff",
            "group_name", "form", "status", "description",
            "played_total", "win_total", "draw_total", "lose_total",
            "goals_for_total", "goals_against_total",
            "played_home", "win_home", "draw_home", "lose_home",
            "goals_for_home", "goals_against_home",
            "played_away", "win_away", "draw_away", "lose_away",
            "goals_for_away", "goals_against_away",
            "last_update",
        ]
        assert list(df.columns) == expected

    def test_preservation_des_18_equipes(self, real_standings_json):
        """Bundesliga a 18 équipes, 1 seul groupe de classement."""
        df = flatten_standings(real_standings_json)
        assert len(df) == 18

    def test_coherence_bayern_munich_premier(self, real_standings_json):
        """Vérifie la ligne du champion (Bayern Munich, rank 1) contre la source."""
        df = flatten_standings(real_standings_json)
        row = df[df["team_id"] == 157].iloc[0]
        assert row["rank"] == 1
        assert row["points"] == 71
        assert row["goals_diff"] == 54
        assert row["played_total"] == 34
        assert row["goals_for_home"] == 53 


class TestFlattenTopScorers:

    def test_structure_colonnes(self, real_top_scorers_json):
        df = flatten_top_scorers(real_top_scorers_json)
        assert "player_id" in df.columns
        assert "penalty_committed" in df.columns
        assert len(df.columns) == 54

    def test_20_lignes_pour_18_joueurs_dont_2_transferts(self, real_top_scorers_json):
        """18 joueurs, mais Guirassy et Bülter ont chacun 2 entrées statistics
        (transfert en cours de saison) : 20 lignes attendues, pas 18."""
        df = flatten_top_scorers(real_top_scorers_json)
        assert len(df) == 20

    def test_joueur_transfere_a_bien_deux_lignes(self, real_top_scorers_json):
        """Guirassy (id 21393) doit apparaître 2 fois, une par équipe."""
        df = flatten_top_scorers(real_top_scorers_json)
        guirassy_rows = df[df["player_id"] == 21393]
        assert len(guirassy_rows) == 2
        assert set(guirassy_rows["team_id"]) == set(guirassy_rows["team_id"])  # équipes différentes
        assert guirassy_rows["team_id"].nunique() == 2

    def test_coherence_meilleur_buteur(self, real_top_scorers_json):
        """Vérifie la ligne de C. Nkunku (id 269, meilleur buteur) contre la source."""
        df = flatten_top_scorers(real_top_scorers_json)
        row = df[df["player_id"] == 269].iloc[0]
        assert row["goals_total"] == 16
        assert row["team_name"] == "RB Leipzig"
        assert row["height"] == "178"
        assert row["penalty_committed"] is None or pd.isna(row["penalty_committed"]) 

class TestFlattenTopAssists:

    def test_coherence_meilleur_passeur(self, real_top_assists_json):
        """Vérifie la ligne de R. Guerreiro (id 8, vu dans l'extrait JSON collé
        plus tôt) contre la source."""
        df = flatten_top_assists(real_top_assists_json)
        row = df[df["player_id"] == 8].iloc[0]
        assert row["goals_assists"] == 12
        assert row["team_name"] == "Bayern München"


class TestFlattenWeather:

    def test_structure_colonnes(self, real_weather_json):
        df = flatten_weather(real_weather_json)
        assert list(df.columns) == [
            "fixture_id", "kickoff", "team_home",
            "weather_time", "temperature_2m", "precipitation",
            "windspeed_10m", "weathercode",
        ]

    def test_48_lignes_par_match_bronze_strict(self, real_weather_json):
        """308 matchs x 48h confirmés : 14784 lignes attendues, aucun filtrage."""
        df = flatten_weather(real_weather_json)
        assert len(df) == 308 * 48
        assert len(df) == 14784

    def test_coherence_premiere_heure_premier_match(self, real_weather_json):
        """Vérifie la première heure du match d'exemple (fixture_id 871164)."""
        df = flatten_weather(real_weather_json)
        row = df[
            (df["fixture_id"] == 871164) & (df["weather_time"] == "2022-08-05T00:00")
        ].iloc[0]
        assert row["team_home"] == "Eintracht Frankfurt"
        assert row["temperature_2m"] == 25.6
        assert row["weathercode"] == 3

    def test_toutes_les_heures_presentes_pour_un_match(self, real_weather_json):
        """Le match 871164 doit avoir exactement 48 lignes."""
        df = flatten_weather(real_weather_json)
        assert len(df[df["fixture_id"] == 871164]) == 48