-- snowflake/silver/06_silver_team_attributes.sql
-- Table SILVER : profils tactiques FIFA filtrés aux équipes présentes dans RAW.MATCH
-- Grain préservé : une ligne par équipe x date (historique complet, non réduit)
-- La sélection/agrégation d'un snapshot représentatif par équipe est reportée à Gold

USE DATABASE FOOTBALL_DB;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS TEAM_ATTRIBUTES (
    TEAM_FIFA_API_ID                   NUMBER,
    TEAM_API_ID                        NUMBER COMMENT 'Pivot vers TEAM_CROSSWALK.kaggle_team_api_id',
    DATE                                TIMESTAMP_NTZ,

    BUILD_UP_PLAY_SPEED                NUMBER,
    BUILD_UP_PLAY_SPEED_CLASS          STRING,
    BUILD_UP_PLAY_DRIBBLING            NUMBER,
    BUILD_UP_PLAY_DRIBBLING_CLASS      STRING,
    BUILD_UP_PLAY_PASSING              NUMBER,
    BUILD_UP_PLAY_PASSING_CLASS        STRING,
    BUILD_UP_PLAY_POSITIONING_CLASS    STRING,

    CHANCE_CREATION_PASSING            NUMBER,
    CHANCE_CREATION_PASSING_CLASS      STRING,
    CHANCE_CREATION_CROSSING           NUMBER,
    CHANCE_CREATION_CROSSING_CLASS     STRING,
    CHANCE_CREATION_SHOOTING           NUMBER,
    CHANCE_CREATION_SHOOTING_CLASS     STRING,
    CHANCE_CREATION_POSITIONING_CLASS  STRING,

    DEFENCE_PRESSURE                   NUMBER,
    DEFENCE_PRESSURE_CLASS             STRING,
    DEFENCE_AGGRESSION                 NUMBER,
    DEFENCE_AGGRESSION_CLASS           STRING,
    DEFENCE_TEAM_WIDTH                 NUMBER,
    DEFENCE_TEAM_WIDTH_CLASS           STRING,
    DEFENCE_DEFENDER_LINE_CLASS        STRING,

    CONSTRAINT pk_silver_team_attributes PRIMARY KEY (TEAM_API_ID, DATE)
)
COMMENT = 'Profils tactiques FIFA (Kaggle), filtrés aux 164 équipes présentes dans RAW.MATCH. Historique complet préservé (grain équipe x date) — sélection du snapshot représentatif reportée à Gold. Rechargée en TRUNCATE + INSERT.';