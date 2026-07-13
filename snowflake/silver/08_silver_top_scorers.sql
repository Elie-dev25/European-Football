-- Table SILVER : top buteurs API-Football, grain joueur x équipe x ligue x saison
-- Colonnes démographiques exclues (birth_date, nationality, height, weight, etc.)
-- NULL métier remplacés par 0 dans le transformer (ex. penalty_saved pour un attaquant).

USE DATABASE FOOTBALL_DB;
USE SCHEMA SILVER;

CREATE OR REPLACE TABLE TOP_SCORERS (
    PLAYER_ID              NUMBER,
    PLAYER_NAME            STRING,
    FIRSTNAME              STRING,
    LASTNAME               STRING,
    AGE                    NUMBER,
    TEAM_ID                NUMBER,
    TEAM_NAME              STRING,
    LEAGUE_ID              NUMBER,
    LEAGUE_NAME            STRING,
    LEAGUE_COUNTRY         STRING,
    SEASON                 NUMBER,
    APPEARENCES            NUMBER,
    LINEUPS                NUMBER,
    MINUTES                NUMBER,
    POSITION               STRING,
    RATING                 STRING,
    SUBS_IN                NUMBER,
    SUBS_OUT               NUMBER,
    SUBS_BENCH             NUMBER,
    SHOTS_TOTAL            NUMBER,
    SHOTS_ON               NUMBER,
    GOALS_TOTAL            NUMBER,
    GOALS_ASSISTS          NUMBER,
    GOALS_SAVES            NUMBER,
    PASSES_TOTAL           NUMBER,
    PASSES_KEY             NUMBER,
    TACKLES_TOTAL          NUMBER,
    TACKLES_BLOCKS         NUMBER,
    TACKLES_INTERCEPTIONS  NUMBER,
    DUELS_TOTAL            NUMBER,
    DUELS_WON              NUMBER,
    DRIBBLES_ATTEMPTS      NUMBER,
    DRIBBLES_SUCCESS       NUMBER,
    DRIBBLES_PAST          NUMBER,
    FOULS_DRAWN            NUMBER,
    FOULS_COMMITTED        NUMBER,
    CARDS_YELLOW           NUMBER,
    CARDS_YELLOWRED        NUMBER,
    CARDS_RED              NUMBER,
    PENALTY_WON            NUMBER,
    PENALTY_COMMITTED      NUMBER,
    PENALTY_SCORED         NUMBER,
    PENALTY_MISSED         NUMBER,
    PENALTY_SAVED          NUMBER,
    PRIMARY KEY (LEAGUE_ID, SEASON, TEAM_ID, PLAYER_ID)
)
COMMENT = 'Top buteurs API-Football filtrés aux équipes présentes dans RAW.FIXTURES. Colonnes démographiques exclues. NULL métier remplacés par 0. Rechargée en TRUNCATE + INSERT.';