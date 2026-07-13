import pandas as pd
from pipelines.utils import get_snowflake_connection


def fetch_match_team_ids(conn) -> pd.DataFrame:
    """Récupère les IDs équipe (domicile/extérieur) depuis RAW.MATCH."""
    query = """
        SELECT home_team_api_id, away_team_api_id
        FROM FOOTBALL_DB.RAW.MATCH;
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def fetch_team_ids(conn) -> pd.DataFrame:
    """Récupère les IDs équipe référencés dans RAW.TEAM."""
    query = """
        SELECT team_api_id
        FROM FOOTBALL_DB.RAW.TEAM;
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def check_team_id_orphans():
    """
    Vérifie empiriquement si home_team_api_id / away_team_api_id dans
    RAW.MATCH partagent bien le même espace d'ID que team_api_id dans
    RAW.TEAM (hypothèse : même source Kaggle, donc même système d'ID).
    """
    with get_snowflake_connection() as conn:
        matches = fetch_match_team_ids(conn)
        teams = fetch_team_ids(conn)

    team_ids = set(teams["team_api_id"])

    home_ids = set(matches["home_team_api_id"])
    away_ids = set(matches["away_team_api_id"])

    home_orphans = home_ids - team_ids
    away_orphans = away_ids - team_ids

    print(f"Total lignes RAW.MATCH : {len(matches)}")
    print(f"Total équipes distinctes RAW.TEAM : {len(team_ids)}")
    print()
    print(f"IDs distincts home_team_api_id : {len(home_ids)}")
    print(f"  -> orphelins (absents de TEAM) : {len(home_orphans)}")
    if home_orphans:
        print(f"  -> exemples : {list(home_orphans)[:10]}")
    print()
    print(f"IDs distincts away_team_api_id : {len(away_ids)}")
    print(f"  -> orphelins (absents de TEAM) : {len(away_orphans)}")
    if away_orphans:
        print(f"  -> exemples : {list(away_orphans)[:10]}")

    # Impact en nombre de lignes (matchs), pas juste en IDs distincts
    home_orphan_rows = matches["home_team_api_id"].isin(home_orphans).sum()
    away_orphan_rows = matches["away_team_api_id"].isin(away_orphans).sum()
    print()
    print(f"Lignes MATCH avec home_team_api_id orphelin : {home_orphan_rows} / {len(matches)}")
    print(f"Lignes MATCH avec away_team_api_id orphelin : {away_orphan_rows} / {len(matches)}")


if __name__ == "__main__":
    check_team_id_orphans()