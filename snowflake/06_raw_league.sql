-- snowflake/06_raw_league.sql
-- Table RAW : miroir SQL de la table Kaggle League
-- Bronze strict — les 11 ligues sont conservées telles quelles, filtrage repoussé vers Silver

USE DATABASE FOOTBALL_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS LEAGUE (
    league_id     NUMBER PRIMARY KEY COMMENT 'Identifiant Kaggle de la ligue',
    country_id    NUMBER COMMENT 'Identifiant du pays (identique à league_id dans ce jeu de données)',
    league_name   STRING COMMENT 'Nom complet de la ligue (ex. England Premier League)'
)
COMMENT = 'Miroir de la table Kaggle League.json — 11 ligues, non filtré';