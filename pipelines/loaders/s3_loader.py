"""
pipelines/loaders/s3_loader.py

Charge les fichiers Bronze deja extraits localement (data/raw/...)
vers le bucket S3, sans jamais retoucher l'API source.

Philosophie : separation stricte extraction / chargement.
Ce module lit uniquement depuis le disque local, jamais depuis une API.
"""

import os 
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

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

SOURCES_CONFIG = {
    "api_football": {
        "local_dir": Path("data/raw/api_football"),
        "s3_prefix": "bronze/api_football",
    },
    "api_weather": {
        "local_dir": Path("data/raw/api_weather"),
        "s3_prefix": "bronze/api_weather",
    },
    "kaggle": {
        "local_dir": Path("data/raw/kaggle"),
        "s3_prefix": "bronze/kaggle/extracted",
    },
}


def _file_exists_in_s3(bucket: str, key: str) -> bool:
    """
    Verifie si un objet existe deja sur S3 a la cle donnee.
    Utilise head_object - une seule requete, pas de listing complet.
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise 



def upload_file_to_s3(
    local_path: Path,
    s3_key: str,
    force_upload: bool = False,
    retries: int = 5,
) -> bool:
    """
    Upload un fichier local vers S3.

    Idempotence : si le fichier existe deja sur S3 et force_upload=False,
    l'upload est ignore.

    Resilience : retry avec backoff exponentiel sur les erreurs reseau,
    (reseau instable).

    Retourne True si l'upload a eu lieu, False s'il a ete skip.
    """
    if not local_path.exists():
        logger.error(f"Fichier local introuvable, upload annule : {local_path}")
        raise FileNotFoundError(f"Fichier local introuvable : {local_path}")

    if not force_upload and _file_exists_in_s3(BUCKET_NAME, s3_key):
        logger.info(f"Deja present sur S3, ignore : {s3_key}")
        return False

    for attempt in range(retries):
        try:
            s3_client.upload_file(str(local_path), BUCKET_NAME, s3_key)
            logger.info(f"Uploade vers S3 : {s3_key}")
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            # AccessDenied : pas la peine de retry, le probleme est permanent (permissions)
            if error_code == "AccessDenied":
                logger.error(f"Acces refuse sur S3 pour {s3_key} - verifier les permissions IAM")
                raise
            wait = 2 ** attempt
            logger.warning(f"Erreur S3 ({error_code}) sur {s3_key}, retry dans {wait}s ({attempt + 1}/{retries})")
            time.sleep(wait)

        except Exception as e:
            # Filet de securite final : capture tout ce qui n'est pas anticipe
            # (coupure reseau brute, EndpointConnectionError, etc.)
            wait = 2 ** attempt
            logger.warning(f"Erreur inattendue sur {s3_key} : {e}, retry dans {wait}s ({attempt + 1}/{retries})")
            time.sleep(wait)

    logger.error(f"Echec definitif de l'upload apres {retries} tentatives : {s3_key}")
    return False 



def upload_directory_to_s3(
    local_dir: Path,
    s3_prefix: str,
    force_upload: bool = False,
) -> dict:
    """
    Upload tous les fichiers d'un dossier local vers un prefixe S3.

    Isolation des pannes : un fichier qui echoue n'empeche pas
    les autres d'etre uploades (meme pattern que extract_all_leagues).

    Retourne un resume : {"uploaded": [...], "skipped": [...], "failed": [...]}
    """
    if not local_dir.exists():
        logger.error(f"Dossier local introuvable : {local_dir}")
        raise FileNotFoundError(f"Dossier local introuvable : {local_dir}")

    results = {"uploaded": [], "skipped": [], "failed": []}

    files = sorted(local_dir.glob("*.json"))
    if not files:
        logger.warning(f"Aucun fichier JSON trouve dans {local_dir}")
        return results

    for file_path in files:
        s3_key = f"{s3_prefix}/{file_path.name}"
        try:
            was_uploaded = upload_file_to_s3(file_path, s3_key, force_upload=force_upload)
            if was_uploaded:
                results["uploaded"].append(s3_key)
            else:
                results["skipped"].append(s3_key)
        except Exception as e:
            logger.error(f"Echec de l'upload pour {file_path.name} : {e}")
            results["failed"].append(str(file_path.name))
            continue

    logger.info(
        f"{local_dir} -> {s3_prefix} : "
        f"{len(results['uploaded'])} uploades, "
        f"{len(results['skipped'])} ignores, "
        f"{len(results['failed'])} echecs"
    )
    return results 


def run_pipeline(sources: list[str] = None, force_upload: bool = False) -> dict:
    """
    Orchestre l'upload Bronze vers S3 pour les sources demandees.
    Si sources=None, traite toutes les sources connues dans SOURCES_CONFIG.

    Isolation des pannes : une source qui echoue completement
    n'empeche pas les autres d'etre traitees.
    """
    sources_to_process = sources if sources else list(SOURCES_CONFIG.keys())
    all_results = {}

    for source_name in sources_to_process:
        if source_name not in SOURCES_CONFIG:
            logger.warning(f"Source inconnue, ignoree : {source_name}")
            continue

        config = SOURCES_CONFIG[source_name]
        logger.info(f"--- Traitement de la source : {source_name} ---")

        try:
            all_results[source_name] = upload_directory_to_s3(
                config["local_dir"],
                config["s3_prefix"],
                force_upload=force_upload,
            )
        except Exception as e:
            logger.error(f"Echec complet pour la source {source_name} : {e}")
            all_results[source_name] = {"uploaded": [], "skipped": [], "failed": ["DOSSIER_ENTIER"]}
            continue

    return all_results 


def upload_kaggle_source(force_upload: bool = False) -> bool:
    """
    Upload one-shot du fichier source Kaggle (database.sqlite) vers S3.

    Cas particulier : un seul gros fichier, pas un dossier a boucler,
    donc separe de SOURCES_CONFIG / upload_directory_to_s3.
    Non appelee par run_pipeline() - a lancer manuellement au besoin
    (premier upload, migration, corruption du fichier sur S3).
    """
    return upload_file_to_s3(
        local_path=Path("data/database.sqlite"),
        s3_key="bronze/kaggle/source/database.sqlite",
        force_upload=force_upload,
    )


# pour execution directe du script, utile pour tests manuels
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    results = run_pipeline()
    for source, summary in results.items():
        print(f"\n--- {source} ---")
        print(f"  Uploadés : {len(summary['uploaded'])}")
        print(f"  Ignorés  : {len(summary['skipped'])}")
        print(f"  Échecs   : {len(summary['failed'])}")
