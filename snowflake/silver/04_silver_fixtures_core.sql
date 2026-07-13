-- snowflake/silver/04_silver_fixtures_core.sql
-- Table SILVER : fixtures API-Football allégées, matchs terminés uniquement
-- Grain : une ligne par fixture_id
-- Pas de jointure : RAW.FIXTURES fournit déjà les noms d'équipes nativement

USE DATABASE FOOTBALL_DB;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS FIXTURES_CORE (
    FIXTURE_ID       NUMBER PRIMARY KEY,
    MATCH_DATE       TIMESTAMP_TZ,
    LEAGUE_ID        NUMBER,
    LEAGUE_NAME      STRING,
    LEAGUE_COUNTRY   STRING,
    SEASON           NUMBER,

    HOME_TEAM_ID     NUMBER COMMENT 'ID API-Football, pivot vers TEAM_CROSSWALK.api_football_team_id',
    HOME_TEAM_NAME   STRING,
    AWAY_TEAM_ID     NUMBER COMMENT 'ID API-Football, pivot vers TEAM_CROSSWALK.api_football_team_id',
    AWAY_TEAM_NAME   STRING,

    GOALS_HOME       NUMBER,
    GOALS_AWAY       NUMBER,
    STATUS_SHORT     STRING COMMENT 'Filtré à FT (Match Finished) uniquement'
)
COMMENT = 'Fixtures API-Football (2022-2024), matchs terminés uniquement. Rechargée en TRUNCATE + INSERT.';