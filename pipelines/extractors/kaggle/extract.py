# pipelines/kaggle/extract.py
import json
import logging
import sqlite3
from pathlib import Path
from pipelines.utils import load_leagues

import pandas as pd 

logger = logging.getLogger(__name__)

DB_PATH = Path("data/database.sqlite")
OUTPUT_DIR = Path("data/raw/kaggle")
LEAGUES_CSV = Path("dbt/seeds/leagues.csv") 

TABLES_CONFIG = {
    "team": {
        "query": "SELECT * FROM Team",
        "filename": "team.json",
    },
    "league": {
        "query": "SELECT * FROM League",
        "filename": "league.json",
    },
    "team_attributes": {
        "query": "SELECT * FROM Team_Attributes",
        "filename": "team_attributes.json",
    },
}



def _connect_sqlite(db_path: Path) -> sqlite3.Connection:
    """
    Ouvre une connexion vers la base SQLite locale.
    Lève FileNotFoundError si le fichier n'existe pas.
    """
    if not db_path.exists():
        raise FileNotFoundError(
            f"{db_path} introuvable — vérifie que database.sqlite est présent localement"
        )
    return sqlite3.connect(db_path) 


def _read_table(conn: sqlite3.Connection, query: str) -> list[dict]:
    """
    Exécute une requête SQL sur la connexion ouverte et retourne les résultats
    sous forme de liste de dicts — format cohérent avec les autres pipelines.

    pd.read_sql_query() gère automatiquement la correspondance colonnes/valeurs,
    évitant la conversion manuelle depuis cursor.fetchall(). ce qui justifie l'utilisation de pandas ici, 
    même si c'est un peu plus lourd que sqlite3 seul.
    """
    df = pd.read_sql_query(query, conn)
    return df.to_dict(orient="records") 

def _file_exists(output_dir: Path, filename: str) -> bool:
    """
    Vérifie si le fichier JSON existe déjà sur disque.
    Mécanisme d'idempotence — si le fichier existe, on ne re-extrait pas.
    Cohérent avec les pipelines api_football et api_weather.
    """
    return (output_dir / filename).exists() 


def save_raw_data(data: list[dict], output_dir: Path, filename: str) -> None:
    """
    Sauvegarde les données extraites en JSON sur disque.
    Crée le dossier output_dir si absent.
    Ne sauvegarde pas si les données sont vides 
    """
    if not data:
        logger.warning("Données vides pour %s — fichier non créé.", filename)
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, default=str)

    logger.info("Sauvegardé : %s (%d enregistrements)", filepath, len(data)) 


def extract_table(table_name: str, query: str, filename: str, db_path: Path = DB_PATH, output_dir: Path = OUTPUT_DIR) -> None:
    """
    Orchestre l'extraction d'une table SQLite vers un fichier JSON Bronze.
    Vérifie l'idempotence avant d'ouvrir la connexion — si le fichier existe
    déjà sur disque, on ne touche pas à la base.
    """
    if _file_exists(output_dir, filename):
        logger.info("Idempotence — fichier déjà présent : %s", filename)
        return

    try:
        conn = _connect_sqlite(db_path)
        data = _read_table(conn, query)
        conn.close()
        save_raw_data(data, output_dir, filename)
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error("Erreur lors de l'extraction de '%s' : %s", table_name, e)
        raise    


def run_pipeline(db_path: Path = DB_PATH, output_dir: Path = OUTPUT_DIR) -> None:
    """
    Point d'entrée principal du pipeline Kaggle.
    Charge les IDs Kaggle depuis leagues.csv, construit la requête Match
    dynamiquement, puis extrait toutes les tables définies dans TABLES_CONFIG.
    """
    logger.info("Démarrage pipeline Kaggle SQLite")

    # Chargement des IDs Kaggle depuis le seed dbt
    leagues = load_leagues(LEAGUES_CSV, id_column="kaggle_league_id")
    league_ids = list(leagues.values())
    placeholders = ",".join(str(i) for i in league_ids)

    # Requête Match construite dynamiquement — filtre sur nos 5 ligues uniquement
    match_config = {
        "query": f"SELECT * FROM Match WHERE league_id IN ({placeholders})",
        "filename": "match_2008_2016.json",
    }

    # Fusion avec les autres tables
    all_tables = {**TABLES_CONFIG, "match": match_config}

    for table_name, config in all_tables.items():
        try:
            extract_table(
                table_name=table_name,
                query=config["query"],
                filename=config["filename"],
                db_path=db_path,
                output_dir=output_dir,
            )
        except Exception as e:
            logger.error("Échec table '%s' : %s — pipeline continue.", table_name, e)

    logger.info("Pipeline Kaggle terminé.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()