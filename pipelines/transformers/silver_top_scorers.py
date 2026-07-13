import pandas as pd
from pipelines.utils import get_snowflake_connection


def fetch_raw_top_scorers(conn) -> pd.DataFrame:
    """Récupère les top buteurs filtrés aux équipes présentes dans RAW.FIXTURES.

    Filtre dynamique (sous-requête sur home/away de RAW.FIXTURES), même logique
    que STANDINGS. Le grain joueur x équipe x ligue x saison est préservé.
    Colonnes démographiques exclues (sans valeur analytique pour l'objectif du projet).
    Colonnes numériques NULL=0 métier remplacées par 0 explicitement.
    """
    query = """
        SELECT
            player_id, player_name, firstname, lastname, age,
            team_id, team_name, league_id, league_name, league_country, season,
            appearences, lineups, minutes, position, rating,
            subs_in, subs_out, subs_bench,
            shots_total, shots_on,
            goals_total, goals_assists, goals_saves,
            passes_total, passes_key,
            tackles_total, tackles_blocks, tackles_interceptions,
            duels_total, duels_won,
            dribbles_attempts, dribbles_success, dribbles_past,
            fouls_drawn, fouls_committed,
            cards_yellow, cards_yellowred, cards_red,
            penalty_won, penalty_committed, penalty_scored, penalty_missed, penalty_saved
        FROM FOOTBALL_DB.RAW.TOP_SCORERS
        WHERE team_id IN (
            SELECT home_team_id FROM FOOTBALL_DB.RAW.FIXTURES
            UNION
            SELECT away_team_id FROM FOOTBALL_DB.RAW.FIXTURES
        );
    """
    cursor = conn.cursor()
    cursor.execute(query)
    df = cursor.fetch_pandas_all()
    df.columns = df.columns.str.lower()

    zero_fill_columns = [
        "goals_saves", "goals_assists",
        "dribbles_past", "dribbles_success",
        "penalty_won", "penalty_committed", "penalty_saved",
        "subs_out", "subs_bench",
        "cards_yellowred", "tackles_blocks", "tackles_interceptions",
    ]
    df[zero_fill_columns] = df[zero_fill_columns].fillna(0)

    return df


def load_top_scorers():
    """Point d'entrée : reconstruit entièrement SILVER.TOP_SCORERS."""
    with get_snowflake_connection() as conn:
        result_df = fetch_raw_top_scorers(conn)
        result_df.columns = result_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.TOP_SCORERS;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            result_df,
            table_name="TOP_SCORERS",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"SILVER.TOP_SCORERS rechargée : {len(result_df)} lignes")


if __name__ == "__main__":
    load_top_scorers()