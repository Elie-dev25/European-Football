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


def get_duplicate_count(conn, database: str, schema: str, table: str, key_columns) -> int:
    """
    Compte les doublons sur une clé, simple ou composite.
    key_columns accepte soit une chaîne (clé simple, ex. "MATCH_API_ID"),
    soit une liste (clé composite, ex. ["TEAM_API_ID", "DATE"]).
    Implémentation via sous-requête SELECT DISTINCT plutôt que COUNT(DISTINCT (tuple)),
    car Snowflake ne supporte pas COUNT(DISTINCT ...) sur un ROW multi-colonnes.
    """
    if isinstance(key_columns, str):
        key_columns = [key_columns]

    cursor = conn.cursor()
    cols = ", ".join(f'"{col}"' for col in key_columns)
    cursor.execute(f"""
        SELECT
            (SELECT COUNT(*) FROM {database}.{schema}.{table})
            -
            (SELECT COUNT(*) FROM (SELECT DISTINCT {cols} FROM {database}.{schema}.{table}));
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

def get_max_timestamp_drift_seconds(conn, database: str,
                                     raw_schema: str, raw_table: str,
                                     silver_schema: str, silver_table: str,
                                     key_columns, timestamp_column: str) -> float:
    """
    Compare l'instant d'une colonne timestamp entre RAW et SILVER, ligne à ligne
    (jointure sur key_columns), et retourne l'écart maximal en secondes.
    Sert à détecter une corruption write_pandas (cf. bug TEAM_ATTRIBUTES) sur
    toute table qui transporte un datetime64 nativement plutôt qu'en STRING.
    Une perte de précision (ns -> us) donne un écart proche de 0, pas un vrai décalage.
    """
    if isinstance(key_columns, str):
        key_columns = [key_columns]

    join_clause = " AND ".join(f'r."{col}" = s."{col}"' for col in key_columns)

    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT MAX(ABS(DATEDIFF('second', r."{timestamp_column}", s."{timestamp_column}")))
        FROM {database}.{raw_schema}.{raw_table} r
        JOIN {database}.{silver_schema}.{silver_table} s
            ON {join_clause};
    """)
    result = cursor.fetchone()[0]
    return float(result) if result is not None else 0.0