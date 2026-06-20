import os
import json
import time
import logging
import requests
import pandas as pd
from pathlib import Path
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

# Chemin vers le seed dbt des ligues — données de référence versionnées dans Git
# Les IDs des ligues ne changent jamais — ils sont maintenus dans ce CSV,
# pas hardcodés dans le code, pour ne pas avoir à modifier le code si on ajoute une ligue
LEAGUES_CSV = Path("dbt/seeds/leagues.csv")

# Dossier de sauvegarde des données brutes
OUTPUT_DIR = Path("data/raw/api_football")

# Phase 1 - Validation de l'architecture sur une seule saison avant d'étendre
SEASONS = [2022]

# Phase 2 - Extension une fois l'architecture validée
# SEASONS = [2022, 2023, 2024]


# === Chargement des ligues depuis le seed dbt ===

def load_leagues(leagues_csv: Path) -> dict:
    """
    Charge les ligues cibles depuis dbt/seeds/leagues.csv.
    Retourne un dict {league_name: league_id} — même structure
    que l'ancien LEAGUE_IDS hardcodé, mais lu depuis le CSV.

    Ajouter une nouvelle ligue = ajouter une ligne dans leagues.csv,
    sans toucher au code.
    """
    if not leagues_csv.exists():
        logger.error(f"Fichier leagues.csv introuvable : {leagues_csv}")
        raise FileNotFoundError(f"{leagues_csv} introuvable — vérifie que dbt/seeds/leagues.csv existe")

    df = pd.read_csv(leagues_csv)
    leagues = dict(zip(df["league_name"], df["league_id"]))
    logger.info(f"{len(leagues)} ligue(s) chargée(s) depuis {leagues_csv} : {list(leagues.keys())}")
    return leagues


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

        except Exception as e:
            logger.error(f"Erreur inattendue pour {endpoint} : {e}")
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


# === Idempotence ===

def _file_exists(league_name: str, season: int, data_type: str, output_dir: Path) -> bool:
    """
    Vérifie si le fichier JSON pour cette (ligue, saison, type) existe déjà sur disque.

    C'est le mécanisme d'idempotence du pipeline — si le fichier existe,
    on ne re-télécharge pas depuis l'API. Cela permet de :
    - Ne pas consommer de quota API inutilement (100 req/jour sur le plan gratuit)
    - Reprendre un run interrompu sans repartir de zéro
    - Ajouter une nouvelle saison sans re-télécharger les saisons existantes
    """
    safe_name = league_name.lower().replace(" ", "_")
    filepath = output_dir / f"{safe_name}_{season}_{data_type}.json"
    return filepath.exists()


# === Orchestration ===

def extract_league_data(league_name: str, league_id: int, season: int, output_dir: Path) -> dict:
    """
    Orchestre les 4 appels API pour UNE ligue et UNE saison données.
    Pour chaque type de donnée, vérifie d'abord si le fichier existe déjà
    avant d'appeler l'API — principe d'idempotence.
    """
    logger.info(f"Extraction {league_name} (id={league_id}), saison {season}...")

    data_types = ["standings", "fixtures", "top_scorers", "top_assists"]
    getters = {
        "standings": lambda: get_standings(league_id, season),
        "fixtures": lambda: get_fixtures(league_id, season),
        "top_scorers": lambda: get_top_scorers(league_id, season),
        "top_assists": lambda: get_top_assists(league_id, season),
    }

    data = {}
    for data_type in data_types:
        if _file_exists(league_name, season, data_type, output_dir):
            # Fichier déjà présent — on charge depuis le disque, pas depuis l'API
            logger.info(f"Déjà téléchargé — {league_name} {season} {data_type} ignoré (0 requête consommée)")
            safe_name = league_name.lower().replace(" ", "_")
            filepath = output_dir / f"{safe_name}_{season}_{data_type}.json"
            with open(filepath, "r", encoding="utf-8") as f:
                data[data_type] = json.load(f)
        else:
            # Fichier absent — on appelle l'API
            data[data_type] = getters[data_type]()

    logger.info(f"Terminé pour {league_name}, saison {season}")
    return data


def extract_all_leagues(season: int, leagues: dict, output_dir: Path) -> dict:
    """
    Boucle sur toutes les ligues définies dans leagues (chargées depuis leagues.csv)
    et extrait leurs données complètes pour la saison donnée.

    Résultat : {"Premier League": {...}, "Ligue 1": {...}, ...}
    où chaque valeur a la même structure que extract_league_data().
    """
    all_data = {}

    for league_name, league_id in leagues.items():
        all_data[league_name] = extract_league_data(league_name, league_id, season, output_dir)

    return all_data


# === Sauvegarde locale ===

def save_raw_data(all_data: dict, season: int, output_dir: Path) -> None:
    """
    Sauvegarde les données extraites en fichiers JSON locaux sur disque,
    un fichier par (ligue, type de donnée).

    Exemple de fichier généré : data/raw/api_football/premier_league_2022_fixtures.json

    Ne sauvegarde pas les fichiers déjà existants — cohérent avec la logique
    d'idempotence dans extract_league_data().
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for league_name, league_data in all_data.items():
        safe_name = league_name.lower().replace(" ", "_")

        for data_type, content in league_data.items():
            filepath = output_dir / f"{safe_name}_{season}_{data_type}.json"

            if filepath.exists():
                # Déjà présent — on ne réécrit pas, cohérence avec l'idempotence
                logger.info(f"Fichier existant conservé — {filepath.name}")
                continue

            with open(filepath, "w", encoding="utf-8") as f:
                # ensure_ascii=False pour garder les accents/caractères spéciaux
                # lisibles dans le fichier (noms de joueurs, villes, etc.)
                json.dump(content, f, indent=2, ensure_ascii=False)
            logger.info(f"Sauvegardé — {filepath.name}")

    logger.info(f"Sauvegarde terminée dans {output_dir}/")


# === Orchestration multi-saisons ===

def extract_and_save_season(season: int, leagues: dict, output_dir: Path) -> dict:
    """
    Extrait ET sauvegarde immédiatement les données de toutes les ligues pour UNE saison.

    Combiner les deux ici garantit que si une erreur survient à la saison 2024,
    les saisons 2022 et 2023 sont déjà sur disque — rien n'est perdu.
    """
    all_data = extract_all_leagues(season, leagues, output_dir)
    save_raw_data(all_data, season=season, output_dir=output_dir)
    return all_data


def run_pipeline(seasons: list) -> None:
    """
    Point d'entrée principal du pipeline d'ingestion.
    Extrait et sauvegarde les données pour CHAQUE saison de la liste, une par une.

    C'est ce qui permet de passer de SEASONS = [2022] à SEASONS = [2022, 2023, 2024]
    en changeant UNE seule ligne de configuration — aucune fonction ici n'a besoin d'être modifiée.
    """
    # Chargement des ligues depuis le seed dbt — une seule fois pour tout le pipeline
    leagues = load_leagues(LEAGUES_CSV)

    logger.info(f"Démarrage du pipeline pour les saisons : {seasons}")

    for season in seasons:
        logger.info(f"=== Saison {season} ===")
        all_data = extract_and_save_season(season, leagues, OUTPUT_DIR)

        # Résumé par saison pour vérifier visuellement la cohérence des données récupérées
        for league_name, data in all_data.items():
            nb_fixtures = len(data["fixtures"].get("response", []))
            logger.info(f"{league_name}: {nb_fixtures} matchs")

    logger.info("Pipeline terminé.")


# === Point d'entrée pour tester ce fichier directement ===
# Ce bloc ne s'exécute QUE si on lance "python extract.py" directement,
# pas si ce fichier est importé ailleurs (ex: dans un DAG Airflow plus tard)
if __name__ == "__main__":
    run_pipeline(SEASONS)