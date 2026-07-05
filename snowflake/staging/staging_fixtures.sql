USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS FIXTURES (
    fixture_id       NUMBER,
    referee          STRING,
    match_date       TIMESTAMP_TZ,
    match_timestamp  NUMBER,
    venue_id         NUMBER,
    venue_name       STRING,
    venue_city       STRING,
    status_long      STRING,
    status_short     STRING,
    status_elapsed   NUMBER,
    league_id        NUMBER,
    league_name      STRING,
    league_country   STRING,
    season           NUMBER,
    round            STRING,
    home_team_id     NUMBER,
    home_team_name   STRING,
    home_winner      BOOLEAN,
    away_team_id     NUMBER,
    away_team_name   STRING,
    away_winner      BOOLEAN,
    goals_home       NUMBER,
    goals_away       NUMBER,
    halftime_home    NUMBER,
    halftime_away    NUMBER,
    fulltime_home    NUMBER,
    fulltime_away    NUMBER,
    extratime_home   NUMBER,
    extratime_away   NUMBER,
    penalty_home     NUMBER,
    penalty_away     NUMBER
)
COMMENT = 'Table de transit pour le chargement de RAW.FIXTURES — vidée à chaque run, sans contrainte de clé';