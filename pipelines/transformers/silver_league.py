import pandas as pd
from pipelines.utils import get_snowflake_connection


def fetch_raw_league(conn) -> pd.DataFrame:
    """Récupère les ligues de RAW.LEAGUE, filtrées à celles présentes dans RAW.MATCH.

    Filtre dynamique (sous-requête) plutôt qu'une liste d'IDs en dur : reste
    correct automatiquement si RAW.MATCH évolue, et documente la règle
    plutôt que son résultat figé.
    """
    query = """
        SELECT league_id, country_id, league_name
        FROM FOOTBALL_DB.RAW.LEAGUE
        WHERE league_id IN (
            SELECT DISTINCT league_id FROM FOOTBALL_DB.RAW.MATCH
        );
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def load_league():
    """Point d'entrée : reconstruit entièrement SILVER.LEAGUE."""
    with get_snowflake_connection() as conn:
        result_df = fetch_raw_league(conn)
        result_df.columns = result_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.LEAGUE;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            result_df,
            table_name="LEAGUE",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"SILVER.LEAGUE rechargée : {len(result_df)} lignes")


if __name__ == "__main__":
    load_league()