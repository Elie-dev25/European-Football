import pandas as pd
from pipelines.utils import get_snowflake_connection


def fetch_raw_fixtures(conn) -> pd.DataFrame:
    """Récupère les colonnes pertinentes de RAW.FIXTURES (hors arbitre, stade, prolongations)."""
    query = """
        SELECT fixture_id, match_date, league_id, league_name, league_country, season,
               home_team_id, home_team_name, away_team_id, away_team_name,
               goals_home, goals_away, status_short
        FROM FOOTBALL_DB.RAW.FIXTURES
        WHERE status_short = 'FT';
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def load_fixtures_core():
    """Point d'entrée : reconstruit entièrement SILVER.FIXTURES_CORE."""
    with get_snowflake_connection() as conn:
        result_df = fetch_raw_fixtures(conn)
        result_df.columns = result_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.FIXTURES_CORE;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            result_df,
            table_name="FIXTURES_CORE",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"FIXTURES_CORE rechargée : {len(result_df)} lignes")


if __name__ == "__main__":
    load_fixtures_core()