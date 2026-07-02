-- snowflake/08_raw_team_attributes.sql
-- Table RAW : miroir SQL de la table Kaggle Team_Attributes
-- Bronze strict — 1458 lignes (historique tactique FIFA par équipe et par date)

USE DATABASE FOOTBALL_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS TEAM_ATTRIBUTES (
    id                                 NUMBER COMMENT 'Identifiant interne au dataset Kaggle',
    team_fifa_api_id                   NUMBER COMMENT 'Identifiant FIFA de l''équipe',
    team_api_id                        NUMBER COMMENT 'Identifiant utilisé pour les jointures avec Team',
    date                               TIMESTAMP_NTZ COMMENT 'Date de la mesure des attributs',
    build_up_play_speed                NUMBER COMMENT 'Vitesse de construction du jeu (0-100)',
    build_up_play_speed_class          STRING COMMENT 'Catégorie de vitesse de construction (ex. Balanced)',
    build_up_play_dribbling            NUMBER COMMENT 'Tendance au dribble en construction (0-100, peut être NULL)',
    build_up_play_dribbling_class      STRING COMMENT 'Catégorie de dribble en construction (ex. Little)',
    build_up_play_passing              NUMBER COMMENT 'Style de passe en construction (0-100)',
    build_up_play_passing_class        STRING COMMENT 'Catégorie de passe en construction (ex. Mixed)',
    build_up_play_positioning_class    STRING COMMENT 'Style de positionnement en construction (ex. Organised)',
    chance_creation_passing            NUMBER COMMENT 'Création de chances par la passe (0-100)',
    chance_creation_passing_class      STRING COMMENT 'Catégorie de création par la passe (ex. Normal)',
    chance_creation_crossing           NUMBER COMMENT 'Création de chances par le centre (0-100)',
    chance_creation_crossing_class     STRING COMMENT 'Catégorie de création par le centre',
    chance_creation_shooting           NUMBER COMMENT 'Création de chances par le tir (0-100)',
    chance_creation_shooting_class     STRING COMMENT 'Catégorie de création par le tir',
    chance_creation_positioning_class  STRING COMMENT 'Style de positionnement en création de chances',
    defence_pressure                   NUMBER COMMENT 'Pression défensive (0-100)',
    defence_pressure_class             STRING COMMENT 'Catégorie de pression défensive (ex. Medium)',
    defence_aggression                 NUMBER COMMENT 'Agressivité défensive (0-100)',
    defence_aggression_class           STRING COMMENT 'Catégorie d''agressivité défensive (ex. Press)',
    defence_team_width                 NUMBER COMMENT 'Largeur du bloc défensif (0-100)',
    defence_team_width_class           STRING COMMENT 'Catégorie de largeur défensive (ex. Normal)',
    defence_defender_line_class        STRING COMMENT 'Ligne défensive (ex. Cover)',
    CONSTRAINT pk_team_attributes PRIMARY KEY (team_api_id, date)
)
COMMENT = 'Miroir de la table Kaggle Team_Attributes.json — historique tactique FIFA par équipe';