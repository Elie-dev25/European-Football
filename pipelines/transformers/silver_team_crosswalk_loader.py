"""
Charge la table SILVER.TEAM_CROSSWALK à partir du mapping manuel
défini dans team_crosswalk.py, en résolvant les noms d'équipes
vers leurs vrais IDs Snowflake (RAW.TEAM et RAW.FIXTURES).

Stratégie de chargement : TRUNCATE + INSERT (pas de staging/merge).
Raison : table de référence statique dérivée d'un dict Python versionné
dans git, pas un flux incrémental externe. La reconstruire entièrement
à chaque run garantit la fraîcheur sans complexité inutile.
"""

import pandas as pd
from pipelines.utils import get_snowflake_connection
from pipelines.transformers.team_crosswalk import (
    EXACT_MATCHES,
    TEAM_CROSSWALK,
    KNOWN_UNMATCHED,
    build_full_crosswalk,
)


def fetch_kaggle_teams(conn) -> pd.DataFrame:
    """Récupère team_api_id + team_long_name depuis RAW.TEAM."""
    query = "SELECT team_api_id, team_long_name FROM FOOTBALL_DB.RAW.TEAM;"
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def fetch_api_football_teams(conn) -> pd.DataFrame:
    """
    Récupère team_id + team_name uniques depuis RAW.FIXTURES
    (home + away combinés, dédupliqués).
    """
    query = """
        SELECT DISTINCT home_team_id AS team_id, home_team_name AS team_name
        FROM FOOTBALL_DB.RAW.FIXTURES
        UNION
        SELECT DISTINCT away_team_id, away_team_name
        FROM FOOTBALL_DB.RAW.FIXTURES;
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def build_crosswalk_rows(
    kaggle_df: pd.DataFrame,
    api_df: pd.DataFrame,
    full_mapping: dict[str, str] | None = None,
    unmatched: list[str] | None = None,
) -> pd.DataFrame:
    """
    Assemble les lignes finales de TEAM_CROSSWALK en résolvant
    chaque nom (API-Football + Kaggle) vers son ID réel.
    """
    if full_mapping is None:
        full_mapping = build_full_crosswalk()
    if unmatched is None:
        unmatched = KNOWN_UNMATCHED

    kaggle_lookup = dict(zip(kaggle_df["team_long_name"], kaggle_df["team_api_id"]))
    api_lookup = dict(zip(api_df["team_name"], api_df["team_id"]))

    rows = []

    for api_name, kaggle_name in full_mapping.items():
        api_id = api_lookup.get(api_name)
        kaggle_id = kaggle_lookup.get(kaggle_name)

        if api_id is None:
            raise ValueError(f"Nom API-Football introuvable dans RAW.FIXTURES : {api_name!r}")
        if kaggle_id is None:
            raise ValueError(f"Nom Kaggle introuvable dans RAW.TEAM : {kaggle_name!r}")

        confidence = "exact" if api_name in EXACT_MATCHES else "manual_verified"
        rows.append({
            "kaggle_team_api_id": kaggle_id,
            "kaggle_team_name": kaggle_name,
            "api_football_team_id": api_id,
            "api_football_team_name": api_name,
            "match_confidence": confidence,
        })

    for api_name in unmatched:
        api_id = api_lookup.get(api_name)
        if api_id is None:
            raise ValueError(f"Nom API-Football introuvable dans RAW.FIXTURES : {api_name!r}")

        rows.append({
            "kaggle_team_api_id": None,
            "kaggle_team_name": None,
            "api_football_team_id": api_id,
            "api_football_team_name": api_name,
            "match_confidence": "unmatched",
        })

    return pd.DataFrame(rows)


def load_team_crosswalk():
    """Point d'entrée : reconstruit entièrement SILVER.TEAM_CROSSWALK."""
    with get_snowflake_connection() as conn:
        kaggle_df = fetch_kaggle_teams(conn)
        api_df = fetch_api_football_teams(conn)

        crosswalk_df = build_crosswalk_rows(kaggle_df, api_df)
        crosswalk_df.columns = crosswalk_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.TEAM_CROSSWALK;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            crosswalk_df,
            table_name="TEAM_CROSSWALK",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"TEAM_CROSSWALK rechargée : {len(crosswalk_df)} lignes "
          f"({crosswalk_df['MATCH_CONFIDENCE'].value_counts().to_dict()})")


if __name__ == "__main__":
    load_team_crosswalk()