from pipelines.utils import get_snowflake_connection


def get_null_counts(conn, database: str, schema: str, table: str) -> dict:
    """
    Calcule le nombre de NULL par colonne pour une table donnée.
    Générique : s'appuie sur INFORMATION_SCHEMA pour lister les colonnes,
    donc réutilisable sans modification pour toute nouvelle table Silver.
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM {database}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
        ORDER BY ORDINAL_POSITION;
    """)
    columns = [row[0] for row in cursor.fetchall()]

    case_clauses = ", ".join(
        f'SUM(CASE WHEN "{col}" IS NULL THEN 1 ELSE 0 END) AS "{col}"'
        for col in columns
    )
    cursor.execute(f"SELECT {case_clauses} FROM {database}.{schema}.{table};")
    row = cursor.fetchone()

    return dict(zip(columns, row))


def get_row_count(conn, database: str, schema: str, table: str, where: str = "") -> int:
    """Compte les lignes d'une table, avec clause WHERE optionnelle."""
    cursor = conn.cursor()
    clause = f"WHERE {where}" if where else ""
    cursor.execute(f"SELECT COUNT(*) FROM {database}.{schema}.{table} {clause};")
    return cursor.fetchone()[0]


def get_duplicate_count(conn, database: str, schema: str, table: str, key_column: str) -> int:
    """Compte les doublons sur une colonne clé."""
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT COUNT(*) - COUNT(DISTINCT "{key_column}")
        FROM {database}.{schema}.{table};
    """)
    return cursor.fetchone()[0]


def evaluate_quality(null_counts: dict, critical_columns: set) -> tuple[bool, list[str]]:
    """
    Évalue si les NULL détectés sont acceptables.
    Une colonne absente de critical_columns est tolérée sans déclencher d'échec.
    Retourne (succès, liste des erreurs) — succès=False si au moins une colonne
    critique a des NULL. C'est cette fonction qu'Airflow appellera directement
    en Phase 5 pour décider de faire échouer la tâche (raise) ou non.
    """
    errors = []
    for column, count in null_counts.items():
        if column in critical_columns and count > 0:
            errors.append(f"{column} : {count} NULL (colonne critique)")

    return len(errors) == 0, errors