-- snowflake/00_setup_database.sql
-- Création de la base de données et des schémas Bronze→Silver
-- Exécution : one-shot via SnowSQL, script versionné pour traçabilité

CREATE DATABASE IF NOT EXISTS FOOTBALL_DB
    COMMENT = 'European Football Analytics Platform - portfolio project';

CREATE SCHEMA IF NOT EXISTS FOOTBALL_DB.RAW
    COMMENT = 'Miroir SQL exact du Bronze S3 - aucune transformation';

CREATE SCHEMA IF NOT EXISTS FOOTBALL_DB.SILVER
    COMMENT = 'Données nettoyées et jointes - transformations métier';