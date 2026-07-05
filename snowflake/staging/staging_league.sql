-- snowflake/staging/staging_league.sql
-- Table STAGING : zone de transit pour le chargement de RAW.LEAGUE
-- Structure strictement identique à RAW.LEAGUE, sans PRIMARY KEY
-- (vidée par TRUNCATE avant chaque run du loader, puis MERGE vers RAW.LEAGUE)

USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS LEAGUE (
    league_id     NUMBER COMMENT 'Identifiant Kaggle de la ligue',
    country_id    NUMBER COMMENT 'Identifiant du pays (identique à league_id dans ce jeu de données)',
    league_name   STRING COMMENT 'Nom complet de la ligue (ex. England Premier League)'
)
COMMENT = 'Table de transit pour le chargement de RAW.LEAGUE — vidée à chaque run, sans contrainte de clé';