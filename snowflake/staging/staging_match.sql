USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS MATCH (
    id                  NUMBER,
    country_id          NUMBER,
    league_id           NUMBER,
    season              STRING,
    stage               NUMBER,
    date                TIMESTAMP_NTZ,
    match_api_id        NUMBER,
    home_team_api_id    NUMBER,
    away_team_api_id    NUMBER,
    home_team_goal      NUMBER,
    away_team_goal      NUMBER,

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

    home_player_1 NUMBER, home_player_2 NUMBER, home_player_3 NUMBER, home_player_4 NUMBER,
    home_player_5 NUMBER, home_player_6 NUMBER, home_player_7 NUMBER, home_player_8 NUMBER,
    home_player_9 NUMBER, home_player_10 NUMBER, home_player_11 NUMBER,
    away_player_1 NUMBER, away_player_2 NUMBER, away_player_3 NUMBER, away_player_4 NUMBER,
    away_player_5 NUMBER, away_player_6 NUMBER, away_player_7 NUMBER, away_player_8 NUMBER,
    away_player_9 NUMBER, away_player_10 NUMBER, away_player_11 NUMBER,

    goal          STRING,
    shoton        STRING,
    shotoff       STRING,
    foulcommit    STRING,
    card          STRING,
    cross         STRING,
    corner        STRING,
    possession    STRING,

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
COMMENT = 'Table de transit pour le chargement de RAW.MATCH — vidée à chaque run, sans contrainte de clé';