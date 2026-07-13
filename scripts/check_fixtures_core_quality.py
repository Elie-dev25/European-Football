from pipelines.utils import get_snowflake_connection
from pipelines.quality import get_null_counts, get_row_count, get_duplicate_count, evaluate_quality

DATABASE = "FOOTBALL_DB"
SCHEMA = "SILVER"
TABLE = "FIXTURES_CORE"

CRITICAL_COLUMNS = {"HOME_TEAM_NAME", "AWAY_TEAM_NAME", "GOALS_HOME", "GOALS_AWAY"}


def check_fixtures_core_quality():
    with get_snowflake_connection() as conn:
        raw_count = get_row_count(conn, DATABASE, "RAW", "FIXTURES", where="status_short = 'FT'")
        silver_count = get_row_count(conn, DATABASE, SCHEMA, TABLE)
        duplicates = get_duplicate_count(conn, DATABASE, SCHEMA, TABLE, "FIXTURE_ID")
        null_counts = get_null_counts(conn, DATABASE, SCHEMA, TABLE)

    print(f"RAW.FIXTURES (status_short = FT) : {raw_count} lignes")
    print(f"{SCHEMA}.{TABLE} : {silver_count} lignes")
    print(f"Complétude OK : {raw_count == silver_count}")
    print(f"Doublons sur FIXTURE_ID : {duplicates}")
    print()

    success, errors = evaluate_quality(null_counts, CRITICAL_COLUMNS)
    for column, count in null_counts.items():
        flag = "CRITIQUE" if column in CRITICAL_COLUMNS else "toléré"
        print(f"NULL {column} : {count} ({flag})")

    print()
    print(f"Résultat global : {'PASS' if success else 'FAIL'}")
    if not success:
        print("Erreurs :", *errors, sep="\n  - ")

    return success


if __name__ == "__main__":
    import sys
    success = check_fixtures_core_quality()
    sys.exit(0 if success else 1)