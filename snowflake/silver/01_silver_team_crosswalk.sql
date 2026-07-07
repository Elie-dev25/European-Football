CREATE TABLE IF NOT EXISTS FOOTBALL_DB.SILVER.TEAM_CROSSWALK (
    kaggle_team_api_id      NUMBER,
    kaggle_team_name        VARCHAR,
    api_football_team_id    NUMBER,
    api_football_team_name  VARCHAR,
    match_confidence        VARCHAR,   -- 'exact' | 'manual_verified' | 'unmatched'
    loaded_at                TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);