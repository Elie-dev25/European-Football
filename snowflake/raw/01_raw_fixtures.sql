-- snowflake/01_raw_fixtures.sql
-- Table RAW : miroir SQL aplati du Bronze S3 (api_football/fixtures)
-- Aucune transformation métier — extraction 1:1 des champs pertinents

USE DATABASE FOOTBALL_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS FIXTURES (
    fixture_id       NUMBER PRIMARY KEY COMMENT 'Identifiant unique du match côté API-Football',
    referee          STRING COMMENT 'Nom de l''arbitre',
    match_date       TIMESTAMP_TZ COMMENT 'Date et heure du coup d''envoi, avec fuseau',
    match_timestamp  NUMBER COMMENT 'Timestamp Unix du coup d''envoi',
    venue_id         NUMBER COMMENT 'Identifiant du stade côté API-Football',
    venue_name       STRING COMMENT 'Nom du stade',
    venue_city       STRING COMMENT 'Ville du stade',
    status_long      STRING COMMENT 'Statut du match en toutes lettres',
    status_short     STRING COMMENT 'Code court du statut (ex. FT)',
    status_elapsed   NUMBER COMMENT 'Minutes jouées au moment du statut',
    league_id        NUMBER COMMENT 'Identifiant de la ligue côté API-Football',
    league_name      STRING COMMENT 'Nom de la ligue',
    league_country   STRING COMMENT 'Pays de la ligue',
    season           NUMBER COMMENT 'Saison du match',
    round            STRING COMMENT 'Journée / round de championnat',
    home_team_id     NUMBER COMMENT 'Identifiant de l''équipe à domicile',
    home_team_name   STRING COMMENT 'Nom de l''équipe à domicile',
    home_winner      BOOLEAN COMMENT 'Vrai si l''équipe à domicile a gagné',
    away_team_id     NUMBER COMMENT 'Identifiant de l''équipe à l''extérieur',
    away_team_name   STRING COMMENT 'Nom de l''équipe à l''extérieur',
    away_winner      BOOLEAN COMMENT 'Vrai si l''équipe à l''extérieur a gagné',
    goals_home       NUMBER COMMENT 'Buts marqués par l''équipe à domicile (score final)',
    goals_away       NUMBER COMMENT 'Buts marqués par l''équipe à l''extérieur (score final)',
    halftime_home    NUMBER COMMENT 'Score à la mi-temps, domicile',
    halftime_away    NUMBER COMMENT 'Score à la mi-temps, extérieur',
    fulltime_home    NUMBER COMMENT 'Score à la fin du temps réglementaire, domicile',
    fulltime_away    NUMBER COMMENT 'Score à la fin du temps réglementaire, extérieur',
    extratime_home   NUMBER COMMENT 'Score en prolongation, domicile',
    extratime_away   NUMBER COMMENT 'Score en prolongation, extérieur',
    penalty_home     NUMBER COMMENT 'Score aux tirs au but, domicile',
    penalty_away     NUMBER COMMENT 'Score aux tirs au but, extérieur'
)
COMMENT = 'Miroir aplati du Bronze S3 api_football/{league}_{season}_fixtures.json';