USE DATABASE FOOTBALL_DB;
USE SCHEMA STAGING;

CREATE TABLE IF NOT EXISTS TOP_SCORERS (
    player_id NUMBER, player_name STRING, firstname STRING, lastname STRING,
    age NUMBER, birth_date DATE, birth_place STRING, birth_country STRING,
    nationality STRING, height STRING, weight STRING, injured BOOLEAN,
    team_id NUMBER, team_name STRING, league_id NUMBER, league_name STRING,
    league_country STRING, season NUMBER, appearences NUMBER, lineups NUMBER,
    minutes NUMBER, position STRING, rating STRING, captain BOOLEAN,
    subs_in NUMBER, subs_out NUMBER, subs_bench NUMBER,
    shots_total NUMBER, shots_on NUMBER,
    goals_total NUMBER, goals_conceded NUMBER, goals_assists NUMBER, goals_saves NUMBER,
    passes_total NUMBER, passes_key NUMBER, passes_accuracy NUMBER,
    tackles_total NUMBER, tackles_blocks NUMBER, tackles_interceptions NUMBER,
    duels_total NUMBER, duels_won NUMBER,
    dribbles_attempts NUMBER, dribbles_success NUMBER, dribbles_past NUMBER,
    fouls_drawn NUMBER, fouls_committed NUMBER,
    cards_yellow NUMBER, cards_yellowred NUMBER, cards_red NUMBER,
    penalty_won NUMBER, penalty_committed NUMBER, penalty_scored NUMBER,
    penalty_missed NUMBER, penalty_saved NUMBER
)
COMMENT = 'Table de transit pour le chargement de RAW.TOP_SCORERS — vidée à chaque run, sans contrainte de clé';