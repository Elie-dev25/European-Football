-- snowflake/silver/02_silver_weather_match.sql
-- Table SILVER : météo agrégée par match, filtrée sur la fenêtre
-- kickoff → kickoff+135min. Grain : une ligne par fixture_id.

USE DATABASE FOOTBALL_DB;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS WEATHER_MATCH (
    fixture_id             NUMBER COMMENT 'Référence au match (clé, jointure vers FIXTURES)',
    temperature_avg        FLOAT COMMENT 'Température moyenne (°C) sur la fenêtre du match',
    windspeed_avg          FLOAT COMMENT 'Vitesse du vent moyenne (10m) sur la fenêtre du match',
    precipitation_total    FLOAT COMMENT 'Précipitations cumulées (mm) sur la fenêtre du match',
    has_rain               BOOLEAN COMMENT 'Au moins une mesure de pluie/bruine dans la fenêtre',
    has_snow                BOOLEAN COMMENT 'Au moins une mesure de neige dans la fenêtre',
    has_fog                BOOLEAN COMMENT 'Au moins une mesure de brouillard dans la fenêtre',
    has_storm               BOOLEAN COMMENT 'Au moins une mesure d''orage dans la fenêtre',
    loaded_at              TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_weather_match PRIMARY KEY (fixture_id)
)
COMMENT = 'Météo agrégée par match — grain 1 ligne/fixture_id, dérivée de RAW.WEATHER filtrée sur la fenêtre du match';