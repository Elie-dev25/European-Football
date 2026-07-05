USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS TEAM_ATTRIBUTES (
    id                                 NUMBER,
    team_fifa_api_id                   NUMBER,
    team_api_id                        NUMBER,
    date                               TIMESTAMP_NTZ,
    build_up_play_speed                NUMBER,
    build_up_play_speed_class          STRING,
    build_up_play_dribbling            NUMBER,
    build_up_play_dribbling_class      STRING,
    build_up_play_passing              NUMBER,
    build_up_play_passing_class        STRING,
    build_up_play_positioning_class    STRING,
    chance_creation_passing            NUMBER,
    chance_creation_passing_class      STRING,
    chance_creation_crossing           NUMBER,
    chance_creation_crossing_class     STRING,
    chance_creation_shooting           NUMBER,
    chance_creation_shooting_class     STRING,
    chance_creation_positioning_class  STRING,
    defence_pressure                   NUMBER,
    defence_pressure_class             STRING,
    defence_aggression                 NUMBER,
    defence_aggression_class           STRING,
    defence_team_width                 NUMBER,
    defence_team_width_class           STRING,
    defence_defender_line_class        STRING
)
COMMENT = 'Table de transit pour le chargement de RAW.TEAM_ATTRIBUTES — vidée à chaque run, sans contrainte de clé';