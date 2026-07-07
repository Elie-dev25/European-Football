-- snowflake/09_raw_match.sql
-- Table RAW : miroir SQL de la table Kaggle Match
-- Bronze strict — 14 585 lignes, déjà filtrées aux 5 ligues à l'extraction
-- Colonnes XML (goal, shoton, etc.) conservées brutes — parsing repoussé vers Silver

USE DATABASE FOOTBALL_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS MATCH (
    -- Identifiants et métadonnées
    id                  NUMBER COMMENT 'Identifiant interne au dataset Kaggle',
    country_id          NUMBER COMMENT 'Identifiant du pays',
    league_id           NUMBER COMMENT 'Identifiant de la ligue (jointure vers LEAGUE)',
    season              STRING COMMENT 'Saison (ex. 2008/2009)',
    stage               NUMBER COMMENT 'Journée de championnat',
    date                TIMESTAMP_NTZ COMMENT 'Date du match',
    match_api_id        NUMBER PRIMARY KEY COMMENT 'Identifiant API-Football du match, clé de jointure',
    home_team_api_id    NUMBER COMMENT 'Identifiant de l''équipe à domicile (jointure vers TEAM)',
    away_team_api_id    NUMBER COMMENT 'Identifiant de l''équipe à l''extérieur (jointure vers TEAM)',
    home_team_goal      NUMBER COMMENT 'Buts de l''équipe à domicile',
    away_team_goal      NUMBER COMMENT 'Buts de l''équipe à l''extérieur',

    -- Positions tactiques (formation sur le terrain)
    home_player_X1 NUMBER, home_player_X2 NUMBER, home_player_X3 NUMBER, home_player_X4 NUMBER,
    home_player_X5 NUMBER, home_player_X6 NUMBER, home_player_X7 NUMBER, home_player_X8 NUMBER,
    home_player_X9 NUMBER, home_player_X10 NUMBER, home_player_X11 NUMBER,
    away_player_X1 NUMBER, away_player_X2 NUMBER, away_player_X3 NUMBER, away_player_X4 NUMBER,
    away_player_X5 NUMBER, away_player_X6 NUMBER, away_player_X7 NUMBER, away_player_X8 NUMBER,
    away_player_X9 NUMBER, away_player_X10 NUMBER, away_player_X11 NUMBER,
    home_player_Y1 NUMBER, home_player_Y2 NUMBER, home_player_Y3 NUMBER, home_player_Y4 NUMBER,
    home_player_Y5 NUMBER, home_player_Y6 NUMBER, home_player_Y7 NUMBER, home_player_Y8 NUMBER,
    home_player_Y9 NUMBER, home_player_Y10 NUMBER, home_player_Y11 NUMBER,
    away_player_Y1 NUMBER, away_player_Y2 NUMBER, away_player_Y3 NUMBER, away_player_Y4 NUMBER,
    away_player_Y5 NUMBER, away_player_Y6 NUMBER, away_player_Y7 NUMBER, away_player_Y8 NUMBER,
    away_player_Y9 NUMBER, away_player_Y10 NUMBER, away_player_Y11 NUMBER,

    -- Identifiants des joueurs titulaires (pas de table Player en RAW actuellement)
    home_player_1 NUMBER, home_player_2 NUMBER, home_player_3 NUMBER, home_player_4 NUMBER,
    home_player_5 NUMBER, home_player_6 NUMBER, home_player_7 NUMBER, home_player_8 NUMBER,
    home_player_9 NUMBER, home_player_10 NUMBER, home_player_11 NUMBER,
    away_player_1 NUMBER, away_player_2 NUMBER, away_player_3 NUMBER, away_player_4 NUMBER,
    away_player_5 NUMBER, away_player_6 NUMBER, away_player_7 NUMBER, away_player_8 NUMBER,
    away_player_9 NUMBER, away_player_10 NUMBER, away_player_11 NUMBER,

    -- Événements de match en XML brut (parsing repoussé vers Silver)
    goal          STRING COMMENT 'Détail des buts, XML brut',
    shoton        STRING COMMENT 'Tirs cadrés, XML brut',
    shotoff       STRING COMMENT 'Tirs non cadrés, XML brut',
    foulcommit    STRING COMMENT 'Fautes commises, XML brut',
    card          STRING COMMENT 'Cartons, XML brut',
    cross         STRING COMMENT 'Centres, XML brut',
    corner        STRING COMMENT 'Corners, XML brut',
    possession    STRING COMMENT 'Possession, XML brut',

    -- Cotes de paris (8 bookmakers x Home/Draw/Away)
    B365H NUMBER(10,2), B365D NUMBER(10,2), B365A NUMBER(10,2),
    BWH NUMBER(10,2), BWD NUMBER(10,2), BWA NUMBER(10,2),
    IWH NUMBER(10,2), IWD NUMBER(10,2), IWA NUMBER(10,2),
    LBH NUMBER(10,2), LBD NUMBER(10,2), LBA NUMBER(10,2),
    PSH NUMBER(10,2), PSD NUMBER(10,2), PSA NUMBER(10,2),
    WHH NUMBER(10,2), WHD NUMBER(10,2), WHA NUMBER(10,2),
    SJH NUMBER(10,2), SJD NUMBER(10,2), SJA NUMBER(10,2),
    VCH NUMBER(10,2), VCD NUMBER(10,2), VCA NUMBER(10,2),
    GBH NUMBER(10,2), GBD NUMBER(10,2), GBA NUMBER(10,2),
    BSH NUMBER(10,2), BSD NUMBER(10,2), BSA NUMBER(10,2)
)
COMMENT = 'Miroir de la table Kaggle Match.json — 14 585 matchs, 5 ligues, 2008-2016';