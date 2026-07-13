from pipelines.utils import get_snowflake_connection
from pipelines.quality import get_null_counts, get_row_count, get_duplicate_count, evaluate_quality

DATABASE = "FOOTBALL_DB"
SCHEMA = "SILVER"
TABLE = "TEAM_ATTRIBUTES"

CRITICAL_COLUMNS = {"TEAM_API_ID", "DATE"}


def check_team_attributes_quality():
    with get_snowflake_connection() as conn:
        raw_count = get_row_count(
            conn, DATABASE, "RAW", "TEAM_ATTRIBUTES",
            where="""team_api_id IN (
                SELECT home_team_api_id FROM FOOTBALL_DB.RAW.MATCH
                UNION
                SELECT away_team_api_id FROM FOOTBALL_DB.RAW.MATCH
            )"""
        )
        silver_count = get_row_count(conn, DATABASE, SCHEMA, TABLE)
        null_counts = get_null_counts(conn, DATABASE, SCHEMA, TABLE)

    print(f"RAW.TEAM_ATTRIBUTES (filtré aux équipes de RAW.MATCH) : {raw_count} lignes")
    print(f"{SCHEMA}.{TABLE} : {silver_count} lignes")
    print(f"Complétude OK : {raw_count == silver_count}")
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
    success = check_team_attributes_quality()
    sys.exit(0 if success else 1)