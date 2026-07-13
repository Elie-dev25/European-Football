-- snowflake/05_raw_weather.sql
-- Table RAW : miroir SQL aplati du Bronze S3 (api_weather)
-- Une ligne par heure de mesure météo (48h par match)
-- Aucune transformation métier — l'agrégation (moyenne, somme) est un travail de Silver

USE DATABASE FOOTBALL_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS WEATHER (
    fixture_id       NUMBER COMMENT 'Référence au match (jointure possible vers FIXTURES)',
    kickoff          TIMESTAMP_TZ COMMENT 'Date et heure du coup d''envoi',
    team_home        STRING COMMENT 'Équipe à domicile (lieu du match)',
    weather_time     TIMESTAMP_NTZ COMMENT 'Heure de la mesure météo (sans fuseau, tel que renvoyé par la source)',
    temperature_2m   FLOAT COMMENT 'Température à 2m (°C)',
    precipitation    FLOAT COMMENT 'Précipitations (mm)',
    windspeed_10m    FLOAT COMMENT 'Vitesse du vent à 10m',
    weathercode      NUMBER COMMENT 'Code météo Open-Meteo (WMO)',
    CONSTRAINT pk_weather PRIMARY KEY (fixture_id, weather_time)
)
COMMENT = 'Miroir aplati du Bronze S3 api_weather/{league}_{season}_weather.json — une ligne par heure de mesure';