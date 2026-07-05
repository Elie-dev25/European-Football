USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS STANDINGS (
    league_id            NUMBER,
    league_name          STRING,
    league_country       STRING,
    season               NUMBER,
    team_id              NUMBER,
    team_name            STRING,
    rank                 NUMBER,
    points               NUMBER,
    goals_diff           NUMBER,
    group_name           STRING,
    form                 STRING,
    status               STRING,
    description          STRING,
    played_total         NUMBER,
    win_total            NUMBER,
    draw_total           NUMBER,
    lose_total            NUMBER,
    goals_for_total       NUMBER,
    goals_against_total   NUMBER,
    played_home           NUMBER,
    win_home              NUMBER,
    draw_home             NUMBER,
    lose_home             NUMBER,
    goals_for_home        NUMBER,
    goals_against_home    NUMBER,
    played_away           NUMBER,
    win_away              NUMBER,
    draw_away             NUMBER,
    lose_away             NUMBER,
    goals_for_away        NUMBER,
    goals_against_away    NUMBER,
    last_update            TIMESTAMP_TZ
)
COMMENT = 'Table de transit pour le chargement de RAW.STANDINGS — vidée à chaque run, sans contrainte de clé';