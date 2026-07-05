USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS WEATHER (
    fixture_id       NUMBER,
    kickoff          TIMESTAMP_TZ,
    team_home        STRING,
    weather_time     TIMESTAMP_NTZ,
    temperature_2m   FLOAT,
    precipitation    FLOAT,
    windspeed_10m    FLOAT,
    weathercode      NUMBER
)
COMMENT = 'Table de transit pour le chargement de RAW.WEATHER — vidée à chaque run, sans contrainte de clé';