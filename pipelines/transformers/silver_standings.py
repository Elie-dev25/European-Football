import pandas as pd
from pipelines.utils import get_snowflake_connection


def fetch_raw_standings(conn) -> pd.DataFrame:
    """Récupère les classements filtrés aux équipes présentes dans RAW.FIXTURES.

    Filtre dynamique (sous-requête sur home/away de RAW.FIXTURES), même logique
    que pour SILVER.TEAM_ATTRIBUTES : documente la règle plutôt qu'une liste
    d'IDs figée. STANDINGS et FIXTURES partagent le même espace d'ID (tous deux
    API-Football), contrairement à TEAM_ATTRIBUTES (Kaggle) qui nécessite le
    crosswalk. Le grain équipe x ligue x saison est préservé, aucune réduction.
    """
    query = """
        SELECT
            league_id, league_name, league_country, season,
            team_id, team_name, rank, points, goals_diff,
            group_name, form, status, description,
            played_total, win_total, draw_total, lose_total,
            goals_for_total, goals_against_total,
            played_home, win_home, draw_home, lose_home,
            goals_for_home, goals_against_home,
            played_away, win_away, draw_away, lose_away,
            goals_for_away, goals_against_away,
            last_update
        FROM FOOTBALL_DB.RAW.STANDINGS
        WHERE team_id IN (
            SELECT home_team_id FROM FOOTBALL_DB.RAW.FIXTURES
            UNION
            SELECT away_team_id FROM FOOTBALL_DB.RAW.FIXTURES
        );
    """
    cursor = conn.cursor()
    cursor.execute(query)
    df = cursor.fetch_pandas_all()
    df["LAST_UPDATE"] = df["LAST_UPDATE"].dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df.columns = df.columns.str.lower()
    return df


def load_standings():
    """Point d'entrée : reconstruit entièrement SILVER.STANDINGS."""
    with get_snowflake_connection() as conn:
        result_df = fetch_raw_standings(conn)
        result_df.columns = result_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.STANDINGS;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            result_df,
            table_name="STANDINGS",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"SILVER.STANDINGS rechargée : {len(result_df)} lignes")


if __name__ == "__main__":
    load_standings()