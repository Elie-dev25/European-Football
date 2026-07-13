import pandas as pd
from pipelines.utils import get_snowflake_connection


def fetch_raw_team_attributes(conn) -> pd.DataFrame:
    """Récupère les profils tactiques filtrés aux équipes présentes dans RAW.MATCH.

    Filtre dynamique (sous-requête sur home/away de RAW.MATCH), même logique
    que pour SILVER.LEAGUE : documente la règle plutôt qu'une liste d'IDs figée.
    Le grain équipe x date de RAW.TEAM_ATTRIBUTES est préservé, aucune réduction
    à une ligne par équipe (décision reportée à Gold).
    """
    query = """
        SELECT
            team_fifa_api_id, team_api_id, date,
            build_up_play_speed, build_up_play_speed_class,
            build_up_play_dribbling, build_up_play_dribbling_class,
            build_up_play_passing, build_up_play_passing_class,
            build_up_play_positioning_class,
            chance_creation_passing, chance_creation_passing_class,
            chance_creation_crossing, chance_creation_crossing_class,
            chance_creation_shooting, chance_creation_shooting_class,
            chance_creation_positioning_class,
            defence_pressure, defence_pressure_class,
            defence_aggression, defence_aggression_class,
            defence_team_width, defence_team_width_class,
            defence_defender_line_class
        FROM FOOTBALL_DB.RAW.TEAM_ATTRIBUTES
        WHERE team_api_id IN (
            SELECT home_team_api_id FROM FOOTBALL_DB.RAW.MATCH
            UNION
            SELECT away_team_api_id FROM FOOTBALL_DB.RAW.MATCH
        );
    """
    cursor = conn.cursor()
    cursor.execute(query)
    df = cursor.fetch_pandas_all()
    df.columns = df.columns.str.lower()
    return df


def load_team_attributes():
    """Point d'entrée : reconstruit entièrement SILVER.TEAM_ATTRIBUTES."""
    with get_snowflake_connection() as conn:
        result_df = fetch_raw_team_attributes(conn)
        result_df.columns = result_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.TEAM_ATTRIBUTES;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            result_df,
            table_name="TEAM_ATTRIBUTES",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"SILVER.TEAM_ATTRIBUTES rechargée : {len(result_df)} lignes")


if __name__ == "__main__":
    load_team_attributes()

