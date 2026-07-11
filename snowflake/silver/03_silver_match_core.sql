-- snowflake/silver/03_silver_match_core.sql
-- Table SILVER : matchs enrichis avec noms d'équipes lisibles
-- Grain : une ligne par match_api_id (identique à RAW.MATCH, pas d'agrégation)
-- Jointure directe RAW.MATCH <- RAW.TEAM (même source Kaggle, même espace d'ID,
-- 0 orphelin vérifié empiriquement sur les 14 585 lignes de MATCH)

USE DATABASE FOOTBALL_DB;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS MATCH_CORE (
    MATCH_API_ID                    NUMBER PRIMARY KEY COMMENT 'Identifiant du match, clé de jointure vers WEATHER_MATCH',
    COUNTRY_ID                      NUMBER,
    LEAGUE_ID                       NUMBER,
    SEASON                          STRING,
    STAGE                           NUMBER,
    DATE                            TIMESTAMP_NTZ,

    HOME_TEAM_API_ID                NUMBER COMMENT 'Identifiant équipe domicile (source RAW.MATCH)',
    AWAY_TEAM_API_ID                NUMBER COMMENT 'Identifiant équipe extérieur (source RAW.MATCH)',

    HOME_TEAM_NAME                  STRING COMMENT 'Résolu via RAW.TEAM.team_long_name',
    AWAY_TEAM_NAME                  STRING COMMENT 'Résolu via RAW.TEAM.team_long_name',
    HOME_TEAM_SHORT_NAME            STRING COMMENT 'Résolu via RAW.TEAM.team_short_name',
    AWAY_TEAM_SHORT_NAME            STRING COMMENT 'Résolu via RAW.TEAM.team_short_name',
    HOME_TEAM_FIFA_ID               NUMBER COMMENT 'Résolu via RAW.TEAM.team_fifa_api_id, peut être NULL',
    AWAY_TEAM_FIFA_ID               NUMBER COMMENT 'Résolu via RAW.TEAM.team_fifa_api_id, peut être NULL',

    HOME_TEAM_GOAL                  NUMBER,
    AWAY_TEAM_GOAL                  NUMBER
)
COMMENT = 'Matchs Kaggle (2008-2016, 5 ligues) enrichis des noms d''équipes. Rechargée en TRUNCATE + INSERT.';