import pandas as pd
from pipelines.utils import get_snowflake_connection


def fetch_raw_match(conn) -> pd.DataFrame:
    """Récupère les colonnes pertinentes de RAW.MATCH (hors XML, cotes, positions tactiques)."""
    query = """
        SELECT match_api_id, country_id, league_id, season, stage, date,
               home_team_api_id, away_team_api_id,
               home_team_goal, away_team_goal
        FROM FOOTBALL_DB.RAW.MATCH;
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def fetch_raw_team(conn) -> pd.DataFrame:
    """Récupère les infos équipe depuis RAW.TEAM."""
    query = """
        SELECT team_api_id, team_long_name, team_short_name, team_fifa_api_id
        FROM FOOTBALL_DB.RAW.TEAM;
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def join_match_team(match_df: pd.DataFrame, team_df: pd.DataFrame) -> pd.DataFrame:
    """
    Résout les IDs équipe (home/away) en noms lisibles via RAW.TEAM.
    Jointure directe : même espace d'ID (source Kaggle commune),
    0 orphelin vérifié empiriquement sur les 14 585 lignes de MATCH.
    """
    home_team = team_df.rename(columns={
        "team_api_id": "home_team_api_id",
        "team_long_name": "home_team_name",
        "team_short_name": "home_team_short_name",
        "team_fifa_api_id": "home_team_fifa_id",
    })
    away_team = team_df.rename(columns={
        "team_api_id": "away_team_api_id",
        "team_long_name": "away_team_name",
        "team_short_name": "away_team_short_name",
        "team_fifa_api_id": "away_team_fifa_id",
    })

    result = match_df.merge(home_team, on="home_team_api_id", how="left")
    result = result.merge(away_team, on="away_team_api_id", how="left")

    return result


def load_match_core():
    """Point d'entrée : reconstruit entièrement SILVER.MATCH_CORE."""
    with get_snowflake_connection() as conn:
        match_df = fetch_raw_match(conn)
        team_df = fetch_raw_team(conn)
        result_df = join_match_team(match_df, team_df)
        result_df.columns = result_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.MATCH_CORE;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            result_df,
            table_name="MATCH_CORE",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"MATCH_CORE rechargée : {len(result_df)} lignes")


if __name__ == "__main__":
    load_match_core()