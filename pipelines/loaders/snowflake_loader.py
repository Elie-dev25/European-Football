"""
pipelines/loaders/snowflake_loader.py

Charge les fichiers Bronze (S3, imbriqués) vers RAW Snowflake (aplati).
Architecture générique pilotée par config : une entrée TABLES_CONFIG par table,
seule la fonction flatten_fn est spécifique à chaque source.

Mécanique : S3 (JSON imbriqué) -> flatten -> STAGING.xxx (Python pur, write_pandas)
            -> MERGE INTO RAW.xxx (upsert par clé métier)

Bronze/RAW strict : write_pandas ne fait pas d'upsert nativement, d'où le passage
obligé par une table de staging intermédiaire avant le MERGE.
"""

import os
import json
import logging

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

from pipelines.utils import get_snowflake_connection
from pipelines.loaders.snowflake_flatteners import (
    flatten_league, flatten_team, flatten_team_attributes, flatten_match,
    flatten_fixtures, flatten_standings, flatten_top_scorers, flatten_top_assists,
    flatten_weather,
)
logger = logging.getLogger(__name__)

load_dotenv()

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


TABLES_CONFIG = {
    "league": {
        "s3_key": "bronze/kaggle/extracted/league.json",
        "flatten_fn": flatten_league,
        "primary_keys": ["league_id"],
        "staging_table": "LEAGUE",
        "raw_table": "LEAGUE",
    },

    "team": {
        "s3_key": "bronze/kaggle/extracted/team.json",
        "flatten_fn": flatten_team,
        "primary_keys": ["team_api_id"],
        "staging_table": "TEAM",
        "raw_table": "TEAM",
    },

    "team_attributes": {
        "s3_key": "bronze/kaggle/extracted/team_attributes.json",
        "flatten_fn": flatten_team_attributes,
        "primary_keys": ["team_api_id", "date"],
        "staging_table": "TEAM_ATTRIBUTES",
        "raw_table": "TEAM_ATTRIBUTES",
    },

    "match": {
        "s3_key": "bronze/kaggle/extracted/match_2008_2016.json",
        "flatten_fn": flatten_match,
        "primary_keys": ["match_api_id"],
        "staging_table": "MATCH",
        "raw_table": "MATCH",
    }, 

    "fixtures": {
        "s3_prefix": "bronze/api_football/",
        "s3_suffix_template": "_{season}_fixtures.json",
        "flatten_fn": flatten_fixtures,
        "primary_keys": ["fixture_id"],
        "staging_table": "FIXTURES",
        "raw_table": "FIXTURES",
    },

    "standings": {
        "s3_prefix": "bronze/api_football/",
        "s3_suffix_template": "_{season}_standings.json",
        "flatten_fn": flatten_standings,
        "primary_keys": ["league_id", "season", "team_id"],
        "staging_table": "STANDINGS",
        "raw_table": "STANDINGS",
    },
        "top_scorers": {
        "s3_prefix": "bronze/api_football/",
        "s3_suffix_template": "_{season}_top_scorers.json",
        "flatten_fn": flatten_top_scorers,
        "primary_keys": ["league_id", "season", "team_id", "player_id"],
        "staging_table": "TOP_SCORERS",
        "raw_table": "TOP_SCORERS",
    },

    "top_assists": {
        "s3_prefix": "bronze/api_football/",
        "s3_suffix_template": "_{season}_top_assists.json",
        "flatten_fn": flatten_top_assists,
        "primary_keys": ["league_id", "season", "team_id", "player_id"],
        "staging_table": "TOP_ASSISTS",
        "raw_table": "TOP_ASSISTS",
    },

    "weather": {
        "s3_prefix": "bronze/api_weather/",
        "s3_suffix_template": "_{season}_weather.json",
        "flatten_fn": flatten_weather,
        "primary_keys": ["fixture_id", "weather_time"],
        "staging_table": "WEATHER",
        "raw_table": "WEATHER",
    },
}



SEASONS = [2022]  # centralisé une seule fois, réutilisé pour toutes les tables multi-fichiers



def read_json_from_s3(s3_key: str) -> list[dict]:
    """
    Lit un fichier JSON depuis S3 et le retourne parsé (liste de dicts).

    Meme pattern que upload_file_to_s3 dans s3_loader.py : client boto3
    au niveau module, erreurs S3 loguees explicitement.

    Leve FileNotFoundError si la cle n'existe pas sur S3 (coherent avec
    le comportement de s3_loader.py pour les fichiers locaux manquants).
    """
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            logger.error(f"Fichier introuvable sur S3 : {s3_key}")
            raise FileNotFoundError(f"Fichier introuvable sur S3 : {s3_key}")
        logger.error(f"Erreur S3 ({error_code}) en lisant {s3_key}")
        raise 


def read_multi_json_from_s3(prefix: str, suffix_template: str, seasons: list[int]) -> list[dict]:
    """
    Liste et lit tous les fichiers JSON sous un préfixe S3 correspondant
    aux saisons demandées (une ligue par fichier, toutes concaténées).

    suffix_template contient {season}, ex. "_{season}_fixtures.json" ->
    généré pour chaque saison de SEASONS, puis chaque fichier du bucket
    dont la clé se termine par un de ces suffixes est lu et concatené.

    Gère deux formats de fichiers : les wrappers API-Football (dict avec
    une clé "response" contenant la liste réelle) et les listes JSON
    directes (ex. api_weather, qui n'a pas de wrapper) — détecté au moment
    de la lecture de chaque fichier, pas supposé fixe pour toute la fonction.

    Scalabilité : ajouter une saison à SEASONS suffit à charger plus de
    fichiers, sans changement de code.
    """ 
     
    expected_suffixes = [suffix_template.format(season=s) for s in seasons]

    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)
    matching_keys = [
        obj["Key"] for obj in response.get("Contents", [])
        if any(obj["Key"].endswith(suffix) for suffix in expected_suffixes)
    ]

    if not matching_keys:
        raise FileNotFoundError(f"Aucun fichier trouvé pour {prefix}* avec suffixes {expected_suffixes}")

    all_rows = []
    for key in matching_keys:
        file_content = read_json_from_s3(key)
        rows = file_content["response"] if isinstance(file_content, dict) else file_content
        all_rows.extend(rows)

    logger.info(f"{len(matching_keys)} fichier(s) lus, {len(all_rows)} ligne(s) au total pour {prefix}")
    return all_rows


def merge_into_raw(conn, staging_table: str, raw_table: str, primary_keys: list[str]) -> None:
    """
    MERGE INTO RAW.<raw_table> USING STAGING.<staging_table>, par clé(s) métier.

    Upsert : les lignes existantes (même clé) sont mises à jour, les nouvelles
    sont insérées. Aucune ligne n'est supprimée (Bronze/RAW ne filtre jamais).
    """
    match_condition = " AND ".join(
        f"target.{key} = source.{key}" for key in primary_keys
    )

    # Colonnes = toutes celles de la table staging, récupérées dynamiquement
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM STAGING.{staging_table} LIMIT 0")
    columns = [desc[0] for desc in cursor.description]

    update_clause = ", ".join(
        f"target.{col} = source.{col}" for col in columns if col not in primary_keys
    )
    insert_columns = ", ".join(columns)
    insert_values = ", ".join(f"source.{col}" for col in columns)

    merge_sql = f"""
        MERGE INTO RAW.{raw_table} AS target
        USING STAGING.{staging_table} AS source
        ON {match_condition}
        WHEN MATCHED THEN UPDATE SET {update_clause}
        WHEN NOT MATCHED THEN INSERT ({insert_columns}) VALUES ({insert_values})
    """

    cursor.execute(merge_sql)
    logger.info(f"MERGE STAGING.{staging_table} -> RAW.{raw_table} : {cursor.rowcount} ligne(s) affectée(s)")
    cursor.close()


def load_table(table_name: str) -> None:
    """
    Charge une table RAW de bout en bout : S3 -> flatten -> STAGING -> MERGE -> RAW.

    table_name doit être une clé de TABLES_CONFIG (ex. "league").
    Une seule connexion Snowflake, partagée entre le TRUNCATE staging,
    le write_pandas et le MERGE (même session logique).
    """
    if table_name not in TABLES_CONFIG:
        raise ValueError(f"Table inconnue dans TABLES_CONFIG : {table_name}")

    config = TABLES_CONFIG[table_name]
    logger.info(f"--- Chargement de {table_name} ---")

    if "s3_key" in config:
        raw_json = read_json_from_s3(config["s3_key"])
    elif "s3_prefix" in config:
        raw_json = read_multi_json_from_s3(
            config["s3_prefix"], config["s3_suffix_template"], SEASONS
        )
    else:
        raise ValueError(f"Config invalide pour {table_name} : ni s3_key ni s3_prefix")

    df = config["flatten_fn"](raw_json)
    logger.info(f"{len(df)} ligne(s) aplatie(s) pour {table_name}")

    with get_snowflake_connection() as conn:
        cursor = conn.cursor()

        # Vide le staging avant d'écrire : évite d'accumuler des runs précédents
        cursor.execute(f"TRUNCATE TABLE STAGING.{config['staging_table']}")

        write_pandas(
            conn,
            df,
            table_name=config["staging_table"],
            schema="STAGING",
            quote_identifiers=False,
        )
        logger.info(f"{len(df)} ligne(s) écrite(s) dans STAGING.{config['staging_table']}")

        merge_into_raw(
            conn,
            staging_table=config["staging_table"],
            raw_table=config["raw_table"],
            primary_keys=config["primary_keys"],
        )

        cursor.close()

    logger.info(f"--- {table_name} chargée avec succès ---")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_table("table_name")  # exemple d'exécution directe pour tests manuels





