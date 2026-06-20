import os
import json
import logging
import requests
import pandas as pd
from pathlib import Path

# Configuration du logging — niveaux INFO/WARNING/ERROR avec horodatage
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# === Configuration ===

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Pas de clé API, pas d'en-tête d'authentification — Open-Meteo est entièrement ouvert
HOURLY_VARS = "temperature_2m,precipitation,windspeed_10m,weathercode" 


# Ligues cibles — mêmes données de référence que api_football/extract.py.
LEAGUES_CSV = Path("dbt/seeds/leagues.csv")

# Référentiel des stades — données de référence versionnées dans Git (généré par
# scripts/generate_stadiums_seed.py à partir des fixtures déjà extraites)
STADIUMS_CSV = Path("dbt/seeds/stadiums.csv")

# Dossier des fixtures déjà extraites par api_football/extract.py — source de vérité
# pour savoir quels matchs existent et à quelle date/heure ils ont eu lieu
FIXTURES_DIR = Path("data/raw/api_football")

# Dossier de sauvegarde des données météo brutes
OUTPUT_DIR = Path("data/raw/api_weather")

# Phase 1 - synchronisé avec api_football/extract.py
SEASONS = [2022]

# Phase 2 - Extension une fois l'architecture validée
# SEASONS = [2022, 2023, 2024]

def load_stadiums(stadiums_csv: Path) -> pd.DataFrame:
    """
    Charge le référentiel des stades depuis dbt/seeds/stadiums.csv
    (team_name, stadium_name, city, latitude, longitude).

    Phase 1 : lecture locale du CSV via pandas.
    Phase 4 : cette fonction sera remplacée par une requête Snowflake
    sur dim_stadiums — une seule fonction à changer.
    """
    if not stadiums_csv.exists():
        logger.error(f"Fichier stadiums.csv introuvable : {stadiums_csv}")
        raise FileNotFoundError(f"{stadiums_csv} introuvable — vérifie que dbt/seeds/stadiums.csv existe")

    df = pd.read_csv(stadiums_csv)
    logger.info(f"{len(df)} stade(s) chargé(s) depuis {stadiums_csv}")
    return df