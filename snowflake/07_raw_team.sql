-- snowflake/07_raw_team.sql
-- Table RAW : miroir SQL de la table Kaggle Team
-- Bronze strict — 299 équipes, non filtré

USE DATABASE FOOTBALL_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS TEAM (
    id                  NUMBER COMMENT 'Identifiant interne au dataset Kaggle',
    team_api_id         NUMBER PRIMARY KEY COMMENT 'Identifiant utilisé pour les jointures avec Match',
    team_fifa_api_id    NUMBER COMMENT 'Identifiant FIFA de l''équipe (peut être NULL)',
    team_long_name      STRING COMMENT 'Nom complet de l''équipe',
    team_short_name     STRING COMMENT 'Abréviation de l''équipe (ex. GEN)'
)
COMMENT = 'Miroir de la table Kaggle Team.json — 299 équipes, non filtré';