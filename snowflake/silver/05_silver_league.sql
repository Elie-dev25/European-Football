-- snowflake/silver/05_silver_league.sql
-- Table SILVER : ligues filtrées aux 5 championnats effectivement représentés dans RAW.MATCH
-- Grain : une ligne par league_id
-- Filtre dynamique (pas de liste d'IDs en dur) : voir pipelines/transformers/silver_league.py

USE DATABASE FOOTBALL_DB;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS LEAGUE (
    LEAGUE_ID     NUMBER PRIMARY KEY,
    COUNTRY_ID    NUMBER,
    LEAGUE_NAME   STRING
)
COMMENT = 'Ligues Kaggle filtrées aux 5 grands championnats présents dans RAW.MATCH (sur 11 au total en RAW). Rechargée en TRUNCATE + INSERT.';