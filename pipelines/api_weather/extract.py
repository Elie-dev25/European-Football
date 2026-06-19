import os
import json
import time
import logging
import requests
from dotenv import load_dotenv

# Configuration du logging — niveaux INFO/WARNING/ERROR avec horodatage
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()

# === Configuration ===

# Pas de clé API — Open-Meteo est gratuit et public, aucune authentification requise
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Phase 1 - Validation de l'architecture sur une seule saison avant d'étendre
SEASONS = [2022]

# Phase 2 — extension une fois l'architecture validée
# SEASONS = [2022, 2023, 2024]