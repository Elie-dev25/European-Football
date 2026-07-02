-- snowflake/02_raw_standings.sql
-- Table RAW : miroir SQL aplati du Bronze S3 (api_football/standings)
-- Aucune transformation métier — extraction 1:1 des champs pertinents

USE DATABASE FOOTBALL_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS STANDINGS (
    league_id            NUMBER COMMENT 'Identifiant de la ligue côté API-Football',
    league_name          STRING COMMENT 'Nom de la ligue',
    league_country       STRING COMMENT 'Pays de la ligue',
    season               NUMBER COMMENT 'Saison concernée',
    team_id              NUMBER COMMENT 'Identifiant de l''équipe',
    team_name            STRING COMMENT 'Nom de l''équipe',
    rank                 NUMBER COMMENT 'Position au classement',
    points               NUMBER COMMENT 'Nombre de points',
    goals_diff           NUMBER COMMENT 'Différence de buts',
    group_name           STRING COMMENT 'Groupe/poule (redondant avec league_name pour ces 5 ligues)',
    form                 STRING COMMENT '5 derniers résultats (ex. LDWWW)',
    status               STRING COMMENT 'Évolution du classement (ex. same)',
    description          STRING COMMENT 'Texte de qualification (ex. Promotion - Champions League)',
    played_total         NUMBER COMMENT 'Matchs joués (total)',
    win_total            NUMBER COMMENT 'Victoires (total)',
    draw_total            NUMBER COMMENT 'Nuls (total)',
    lose_total           NUMBER COMMENT 'Défaites (total)',
    goals_for_total       NUMBER COMMENT 'Buts marqués (total)',
    goals_against_total   NUMBER COMMENT 'Buts encaissés (total)',
    played_home           NUMBER COMMENT 'Matchs joués à domicile',
    win_home              NUMBER COMMENT 'Victoires à domicile',
    draw_home             NUMBER COMMENT 'Nuls à domicile',
    lose_home             NUMBER COMMENT 'Défaites à domicile',
    goals_for_home        NUMBER COMMENT 'Buts marqués à domicile',
    goals_against_home    NUMBER COMMENT 'Buts encaissés à domicile',
    played_away           NUMBER COMMENT 'Matchs joués à l''extérieur',
    win_away              NUMBER COMMENT 'Victoires à l''extérieur',
    draw_away             NUMBER COMMENT 'Nuls à l''extérieur',
    lose_away             NUMBER COMMENT 'Défaites à l''extérieur',
    goals_for_away        NUMBER COMMENT 'Buts marqués à l''extérieur',
    goals_against_away    NUMBER COMMENT 'Buts encaissés à l''extérieur',
    last_update            TIMESTAMP_TZ COMMENT 'Date de dernière mise à jour du classement',
    CONSTRAINT pk_standings PRIMARY KEY (league_id, season, team_id)
)
COMMENT = 'Miroir aplati du Bronze S3 api_football/{league}_{season}_standings.json';