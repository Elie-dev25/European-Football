from pipelines.utils import get_snowflake_connection
from pipelines.quality import get_null_counts, get_row_count, get_duplicate_count, evaluate_quality
DATABASE = "FOOTBALL_DB"
SCHEMA = "SILVER"
TABLE = "STANDINGS"

CRITICAL_COLUMNS = {"LEAGUE_ID", "SEASON", "TEAM_ID", "RANK", "POINTS"}


def check_standings_quality():
    with get_snowflake_connection() as conn:
        raw_count = get_row_count(
            conn, DATABASE, "RAW", "STANDINGS",
            where="""team_id IN (
                SELECT home_team_id FROM FOOTBALL_DB.RAW.FIXTURES
                UNION
                SELECT away_team_id FROM FOOTBALL_DB.RAW.FIXTURES
            )"""
        )
        silver_count = get_row_count(conn, DATABASE, SCHEMA, TABLE)
        null_counts = get_null_counts(conn, DATABASE, SCHEMA, TABLE)
        duplicate_count = get_duplicate_count(
            conn, DATABASE, SCHEMA, TABLE, ["LEAGUE_ID", "SEASON", "TEAM_ID"]
        )

    print(f"RAW.STANDINGS (filtré aux équipes de RAW.FIXTURES) : {raw_count} lignes")
    print(f"{SCHEMA}.{TABLE} : {silver_count} lignes")
    print(f"Complétude OK : {raw_count == silver_count}")
    print(f"Doublons sur (LEAGUE_ID, SEASON, TEAM_ID) : {duplicate_count}")
    print()

    success, errors = evaluate_quality(null_counts, CRITICAL_COLUMNS)
    for column, count in null_counts.items():
        flag = "CRITIQUE" if column in CRITICAL_COLUMNS else "toléré"
        print(f"NULL {column} : {count} ({flag})")

    if duplicate_count > 0:
        success = False
        errors.append(f"{duplicate_count} doublon(s) sur la clé composite")

    print()
    print(f"Résultat global : {'PASS' if success else 'FAIL'}")
    if not success:
        print("Erreurs :", *errors, sep="\n  - ")

    return success


if __name__ == "__main__":
    import sys
    success = check_standings_quality()
    sys.exit(0 if success else 1)