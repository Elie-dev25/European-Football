USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS TEAM (
    id                  NUMBER COMMENT 'Identifiant interne au dataset Kaggle',
    team_api_id         NUMBER COMMENT 'Identifiant utilisé pour les jointures avec Match',
    team_fifa_api_id    NUMBER COMMENT 'Identifiant FIFA de l''équipe (peut être NULL)',
    team_long_name      STRING COMMENT 'Nom complet de l''équipe',
    team_short_name     STRING COMMENT 'Abréviation de l''équipe (ex. GEN)'
)
COMMENT = 'Table de transit pour le chargement de RAW.TEAM — vidée à chaque run, sans contrainte de clé';