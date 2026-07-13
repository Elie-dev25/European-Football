-- Table SILVER : classements API-Football, grain équipe x ligue x saison
-- Filtre dynamique sur les équipes présentes dans RAW.FIXTURES (même espace d'ID
-- que STANDINGS, contrairement à TEAM_ATTRIBUTES qui vient de Kaggle) : voir
-- pipelines/transformers/silver_standings.py
-- Scalabilité : une seule saison (2022) extraite à ce stade, les suivantes
-- viendront s'ajouter sans modification de ce DDL ni du transformer.

USE DATABASE FOOTBALL_DB;
USE SCHEMA SILVER;

CREATE TABLE IF NOT EXISTS STANDINGS (
    LEAGUE_ID             NUMBER,
    LEAGUE_NAME           STRING,
    LEAGUE_COUNTRY        STRING,
    SEASON                NUMBER,
    TEAM_ID               NUMBER,
    TEAM_NAME             STRING,
    RANK                  NUMBER,
    POINTS                NUMBER,
    GOALS_DIFF            NUMBER,
    GROUP_NAME            STRING,
    FORM                  STRING,
    STATUS                STRING,
    DESCRIPTION           STRING,
    PLAYED_TOTAL          NUMBER,
    WIN_TOTAL             NUMBER,
    DRAW_TOTAL            NUMBER,
    LOSE_TOTAL            NUMBER,
    GOALS_FOR_TOTAL       NUMBER,
    GOALS_AGAINST_TOTAL   NUMBER,
    PLAYED_HOME           NUMBER,
    WIN_HOME              NUMBER,
    DRAW_HOME             NUMBER,
    LOSE_HOME             NUMBER,
    GOALS_FOR_HOME        NUMBER,
    GOALS_AGAINST_HOME    NUMBER,
    PLAYED_AWAY           NUMBER,
    WIN_AWAY              NUMBER,
    DRAW_AWAY             NUMBER,
    LOSE_AWAY             NUMBER,
    GOALS_FOR_AWAY        NUMBER,
    GOALS_AGAINST_AWAY    NUMBER,
    LAST_UPDATE           STRING COMMENT 'Format ISO 8601 — conversion TIMESTAMP_TZ déléguée à Gold (dbt). Transport en STRING pour contourner le bug write_pandas sur les colonnes datetime64 tz-aware.',
    PRIMARY KEY (LEAGUE_ID, SEASON, TEAM_ID)
)
COMMENT = 'Classements API-Football filtrés aux équipes présentes dans RAW.FIXTURES. Grain équipe x ligue x saison préservé. Rechargée en TRUNCATE + INSERT.';