import os
import json
import time
import logging
import requests
import pandas as pd
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

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

# En-tête HTTP requis par API-Football pour authentifier chaque requête
HEADERS = {
    "x-apisports-key": API_KEY
}

# Nos 5 ligues cibles avec leurs IDs internes à l'API
LEAGUE_IDS = {
    "Premier League": 39,
    "Ligue 1": 61,
    "Bundesliga": 78,
    "Serie A": 135,
    "La Liga": 140
}

# Phase 1 - Validation de l'architecture sur une seule saison avant d'étendre
SEASONS = [2022]

# Phase 2 - Extension une fois l'architecture validée
# SEASONS = [2022, 2023, 2024]


# === Couche d'appel API générique ===

def _call_api(endpoint: str, params: dict, retries: int = 3) -> dict:
    """
    Fonction interne qui gère l'appel HTTP brut vers n'importe quel endpoint d'API-Football.
    Toutes les fonctions get_xxx() passent par ici (principe DRY).

    Gère deux types de problèmes :
    - Erreurs réseau (timeout, connexion perdue) via try/except
    - Limite de 10 req/min du plan gratuit via retry automatique avec attente
    """
    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(retries):
        try:
            # timeout=30 : évite que le script reste bloqué indéfiniment si l'API ne répond pas
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)

            if response.status_code == 200:
                logger.info(f"OK — {endpoint} avec params={params}")
                return response.json()

            elif response.status_code == 429:
                # L'API renvoie parfois un header "Retry-After" indiquant combien
                # de secondes attendre ; sinon on attend 60s par défaut par sécurité
                wait_time = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Limite atteinte pour {endpoint}, attente de {wait_time}s (tentative {attempt + 1}/{retries})")
                time.sleep(wait_time)

            else:
                # Autre erreur (401 = clé invalide, 500 = erreur serveur, etc.) — abandon direct
                logger.error(f"Erreur HTTP {response.status_code} pour {endpoint} avec params={params}")
                return {}

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout pour {endpoint} (tentative {attempt + 1}/{retries}), nouvelle tentative...")
            time.sleep(10)

        except requests.exceptions.ConnectionError:
            logger.error(f"Connexion impossible pour {endpoint} — vérifie ta connexion internet")
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau inattendue pour {endpoint} : {e}")
            return {}

    logger.error(f"Échec définitif pour {endpoint} après {retries} tentatives")
    return {}


# === Fonctions par endpoint ===
# Chaque fonction ne fait qu'une chose : préciser l'endpoint et les paramètres,
# puis déléguer l'appel réel à _call_api(). Principe de responsabilité unique.

def get_standings(league_id: int, season: int) -> dict:
    """Récupère le classement d'une ligue pour une saison donnée."""
    return _call_api("standings", {"league": league_id, "season": season})


def get_fixtures(league_id: int, season: int) -> dict:
    """Récupère tous les matchs (fixtures) d'une ligue pour une saison donnée."""
    return _call_api("fixtures", {"league": league_id, "season": season})


def get_top_scorers(league_id: int, season: int) -> dict:
    """Récupère le top 20 des meilleurs buteurs d'une ligue pour une saison donnée."""
    return _call_api("players/topscorers", {"league": league_id, "season": season})


def get_top_assists(league_id: int, season: int) -> dict:
    """Récupère le top des meilleurs passeurs d'une ligue pour une saison donnée."""
    return _call_api("players/topassists", {"league": league_id, "season": season})


# === Orchestration ===

def extract_league_data(league_id: int, season: int) -> dict:
    """
    Orchestre les 4 appels API pour UNE ligue et UNE saison données,
    et regroupe les résultats dans un seul dictionnaire structuré.
    """
    logger.info(f"Extraction league={league_id}, season={season}...")

    data = {
        "standings": get_standings(league_id, season),
        "fixtures": get_fixtures(league_id, season),
        "top_scorers": get_top_scorers(league_id, season),
        "top_assists": get_top_assists(league_id, season)
    }

    logger.info(f"Terminé pour league={league_id}, season={season}")
    return data


def extract_all_leagues(season: int) -> dict:
    """
    Boucle sur les 5 ligues définies dans LEAGUE_IDS et extrait
    leurs données complètes pour la saison donnée.

    Résultat : {"Premier League": {...}, "Ligue 1": {...}, ...}
    où chaque valeur a la même structure que extract_league_data().
    """
    all_data = {}

    for league_name, league_id in LEAGUE_IDS.items():
        all_data[league_name] = extract_league_data(league_id, season)

    return all_data


# === Sauvegarde locale ===

def save_raw_data(all_data: dict, season: int, output_dir: str = "data/raw/api_football") -> None:
    """
    Sauvegarde les données extraites en fichiers JSON locaux sur disque,
    un fichier par (ligue, type de donnée).

    Exemple de fichier généré : data/raw/api_football/premier_league_2022_fixtures.json
    """
    # Crée le dossier de destination s'il n'existe pas encore
    os.makedirs(output_dir, exist_ok=True)

    for league_name, league_data in all_data.items():
        # Normalise le nom de la ligue pour un nom de fichier propre
        # ("Premier League" -> "premier_league")
        safe_name = league_name.lower().replace(" ", "_")

        for data_type, content in league_data.items():
            filename = f"{safe_name}_{season}_{data_type}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                # ensure_ascii=False pour garder les accents/caractères spéciaux
                # lisibles dans le fichier (noms de joueurs, villes, etc.)
                json.dump(content, f, indent=2, ensure_ascii=False)

    logger.info(f"Données sauvegardées dans {output_dir}/")


# === Orchestration multi-saisons ===

def extract_and_save_season(season: int) -> dict:
    """
    Extrait ET sauvegarde immédiatement les données des 5 ligues pour UNE saison.

    Combiner les deux ici garantit que si une erreur survient à la saison 2024,
    les saisons 2022 et 2023 sont déjà sur disque — rien n'est perdu.
    """
    all_data = extract_all_leagues(season)
    save_raw_data(all_data, season=season)
    return all_data


def run_pipeline(seasons: list) -> None:
    """
    Point d'entrée principal du pipeline d'ingestion.
    Extrait et sauvegarde les données pour CHAQUE saison de la liste, une par une.

    C'est ce qui permet de passer de SEASONS = [2022] à SEASONS = [2022, 2023, 2024, ...]
    en changeant UNE seule ligne de configuration — aucune fonction ici n'a besoin d'être modifiée.
    """
    logger.info(f"Démarrage du pipeline pour les saisons : {seasons}")

    for season in seasons:
        logger.info(f"=== Saison {season} ===")
        all_data = extract_and_save_season(season)

        # Résumé par saison pour vérifier visuellement la cohérence des données récupérées
        for league_name, data in all_data.items():
            nb_fixtures = len(data["fixtures"].get("response", []))
            logger.info(f"{league_name}: {nb_fixtures} matchs récupérés")

    logger.info("Pipeline terminé.")


# === Point d'entrée pour tester ce fichier directement ===
# Ce bloc ne s'exécute QUE si on lance "python extract.py" directement,
# pas si ce fichier est importé ailleurs (ex: dans un DAG Airflow plus tard)
if __name__ == "__main__":
    run_pipeline(SEASONS)