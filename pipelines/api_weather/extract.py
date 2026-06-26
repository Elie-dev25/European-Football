import json
import time
import logging
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

from pipelines.utils import normalize_league_name, build_filepath, load_leagues, load_stadiums

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

# Ligues cibles — mêmes données de référence que api_football/extract.py
LEAGUES_CSV = Path("dbt/seeds/leagues.csv")

# Référentiel des stades — données de référence versionnées dans Git
# (généré par scripts/generate_stadiums_seed.py à partir des fixtures déjà extraites)
STADIUMS_CSV = Path("dbt/seeds/stadiums.csv")

# Dossier des fixtures déjà extraites par api_football/extract.py — source de vérité
# pour savoir quels matchs existent et à quelle date/heure ils ont eu lieu
FIXTURES_DIR = Path("data/raw/api_football")

# Dossier de sauvegarde des données météo brutes
OUTPUT_DIR = Path("data/raw/api_weather")

# Phase 1 — synchronisé avec api_football/extract.py
SEASONS = [2022]

# Phase 2 — Extension une fois l'architecture validée
# SEASONS = [2022, 2023, 2024]


# =============================================================================
# Lookup GPS
# =============================================================================

def get_stadium_coords(team_name: str, stadiums_df: pd.DataFrame) -> tuple:
    """
    Retourne (latitude, longitude) pour l'équipe à domicile d'un match,
    à partir du référentiel des stades (team_name -> latitude, longitude).

    On part du nom de l'équipe et non du stade : stadiums.csv a été généré
    par team_name, et un nom de stade n'est pas une clé fiable
    (sponsoring, renommage possible d'une saison à l'autre).

    Retourne (None, None) si l'équipe est introuvable — non bloquant,
    le match sera simplement ignoré dans extract_weather_for_league().
    """
    match = stadiums_df.loc[stadiums_df["team_name"] == team_name]

    if match.empty:
        logger.warning(f"Aucune coordonnée trouvée pour l'équipe '{team_name}' dans stadiums.csv")
        return None, None

    row = match.iloc[0]
    return row["latitude"], row["longitude"]


# =============================================================================
# Appel API Open-Meteo
# =============================================================================

def _call_api(params: dict, retries: int = 8) -> dict:
    """
    Fonction interne qui gère l'appel HTTP brut vers Open-Meteo Archive API.
    Toutes les fonctions get_xxx() passent par ici pour bénéficier d'une
    gestion centralisée des erreurs et des retries.

    Pas de retry sur 429 : Open-Meteo n'a pas de rate limiting.
    Pas de HEADERS : pas de clé API requise.
    Retry sur Timeout et ConnectionError avec backoff exponentiel —
    adapté aux connexions instables.
    """
    for attempt in range(retries):
        try:
            response = requests.get(BASE_URL, params=params, timeout=30)

            if response.status_code == 200:
                logger.info(f"OK — Open-Meteo avec params={params}")
                return response.json()

            else:
                # Erreur HTTP non récupérable (400, 500...) — inutile de retenter
                logger.error(f"Erreur HTTP {response.status_code} pour params={params}")
                return {}

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            # Erreur réseau temporaire — on retente avec backoff exponentiel
            # 2^attempt : 1s, 2s, 4s, 8s, 16s entre les tentatives
            wait = 2 ** attempt
            logger.warning(f"Erreur réseau (tentative {attempt + 1}/{retries}) : {e} — nouvelle tentative dans {wait}s...")
            time.sleep(wait)

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau inattendue : {e}")
            return {}

        except Exception as e:
            logger.error(f"Erreur inattendue : {e}")
            return {}

    logger.error(f"Échec définitif après {retries} tentatives")
    return {}

def get_weather_for_day(latitude: float, longitude: float, date: str) -> dict:
    """
    Récupère les données météo horaires pour un lieu donné, en couvrant
    le jour du match ET le lendemain (end_date = date + 1 jour).

    La fenêtre +1 jour est nécessaire pour les matchs tardifs (ex: coup
    d'envoi à 22h + ~135 min déborde sur minuit). Le filtrage exact sur
    la durée du match sera fait en dbt/Silver — pas ici.

    date doit être au format "YYYY-MM-DD" (date du coup d'envoi).
    """
    start = datetime.strptime(date, "%Y-%m-%d")
    end = start + timedelta(days=1)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "hourly": HOURLY_VARS,
        "timezone": "UTC"
    }
    return _call_api(params)


# =============================================================================
# Restructuration de la réponse
# =============================================================================

def reshape_hourly_data(weather_response: dict) -> list:
    """
    Restructure la réponse brute d'Open-Meteo (format "colonnes parallèles")
    en une liste de dicts, un par heure.

    Open-Meteo renvoie des tableaux parallèles : {"time": [...], "temperature_2m": [...], ...}
    On pivote en : [{"weather_time": "...", "temperature_2m": ..., ...}, ...]

    Aucun filtre, aucune agrégation — Bronze strict.
    Retourne [] si la réponse est vide ou invalide.
    """
    hourly = weather_response.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        logger.warning("Aucune donnée horaire disponible dans la réponse Open-Meteo")
        return []

    reshaped = []

    for i, time_str in enumerate(times):
        reshaped.append({
            "weather_time": time_str,
            "temperature_2m": hourly.get("temperature_2m", [None] * len(times))[i],
            "precipitation": hourly.get("precipitation", [None] * len(times))[i],
            "windspeed_10m": hourly.get("windspeed_10m", [None] * len(times))[i],
            "weathercode": hourly.get("weathercode", [None] * len(times))[i],
        })

    return reshaped


# =============================================================================
# Chargement des fixtures
# =============================================================================

def load_fixtures(league_name: str, season: int, fixtures_dir: Path) -> list:
    """
    Charge les fixtures d'une ligue/saison déjà extraites par api_football/extract.py.
    Utilise build_filepath() depuis utils.py — même convention de nommage que
    le pipeline qui a créé ces fichiers.

    Retourne la liste des matchs (data["response"]), ou [] si le fichier
    est introuvable. Non bloquant : un fichier manquant signifie que le pipeline
    api_football n'a pas encore tourné pour cette ligue/saison.
    """
    filepath = build_filepath(fixtures_dir, league_name, season, "fixtures")

    if not filepath.exists():
        logger.error(f"Fichier de fixtures introuvable : {filepath}")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixtures = data.get("response", [])
    logger.info(f"{len(fixtures)} match(s) chargé(s) depuis {filepath}")
    return fixtures


def _file_exists(league_name: str, season: int, output_dir: Path) -> bool:
    """
    Vérifie si le fichier météo JSON pour cette (ligue, saison) existe déjà sur disque.
    Utilisé par extract_and_save_season() pour éviter de retraiter une ligue/saison
    déjà complète.
    """
    filepath = build_filepath(output_dir, league_name, season, "weather")
    return filepath.exists()


# =============================================================================
# Extraction météo par ligue
# =============================================================================

def extract_weather_for_league(
    league_name: str,
    season: int,
    stadiums_df: pd.DataFrame,
    fixtures_dir: Path
) -> list:
    """
    Orchestre la récupération météo pour tous les matchs d'une ligue/saison.

    Pour chaque match :
    1. Récupère l'équipe à domicile et le coup d'envoi (kickoff)
    2. Cherche les coordonnées GPS du stade via le référentiel des stades
    3. Appelle Open-Meteo pour cette date/lieu (48h de données brutes)
    4. Restructure la réponse (reshape_hourly_data) et l'associe au match

    Un match sans coordonnées GPS ou sans données météo est ignoré (log WARNING)
    sans bloquer le reste du pipeline.

    Retourne une liste de dicts, un par match :
    {"fixture_id": ..., "kickoff": ..., "team_home": ..., "hourly_weather": [...]}
    """
    fixtures = load_fixtures(league_name, season, fixtures_dir)

    if not fixtures:
        logger.warning(f"Aucun match à traiter pour {league_name} {season}")
        return []

    logger.info(f"Extraction météo pour {league_name} {season} — {len(fixtures)} matchs")

    results = []

    for match in fixtures:
        fixture_id = match["fixture"]["id"]
        team_home = match["teams"]["home"]["name"]
        kickoff_iso = match["fixture"]["date"]

        latitude, longitude = get_stadium_coords(team_home, stadiums_df)

        if latitude is None or longitude is None:
            # Équipe absente de stadiums.csv — on skip ce match uniquement
            logger.warning(f"Match {fixture_id} ignoré — pas de coordonnées pour '{team_home}'")
            continue

        # On extrait uniquement la date (YYYY-MM-DD) depuis l'ISO complet
        match_date = kickoff_iso[:10]
        weather_response = get_weather_for_day(latitude, longitude, match_date)
        hourly_weather = reshape_hourly_data(weather_response)

        if not hourly_weather:
            logger.warning(f"Match {fixture_id} ignoré — aucune donnée météo récupérée")
            continue

        results.append({
            "fixture_id": fixture_id,
            "kickoff": kickoff_iso,
            "team_home": team_home,
            "hourly_weather": hourly_weather
        })

    logger.info(f"{len(results)}/{len(fixtures)} match(s) avec météo récupérée pour {league_name} {season}")
    return results


# =============================================================================
# Orchestration et sauvegarde
# =============================================================================

def extract_all_leagues(
    season: int,
    leagues: list,
    stadiums_df: pd.DataFrame,
    fixtures_dir: Path
) -> dict:
    """
    Boucle sur toutes les ligues et retourne un dict {league_name: [résultats]}.
    Responsabilité unique : extraire seulement, pas de sauvegarde ici.

    Une exception sur une ligue n'arrête pas les autres — on log l'erreur
    et on retourne [] pour cette ligue.
    """
    all_data = {}

    for league_name in leagues:
        logger.info(f"=== Début extraction météo : {league_name} {season} ===")
        try:
            results = extract_weather_for_league(league_name, season, stadiums_df, fixtures_dir)
            all_data[league_name] = results
        except Exception as e:
            logger.error(f"Échec extraction {league_name} {season} : {e}")
            all_data[league_name] = []

    return all_data


def save_raw_data(all_data: dict, season: int, output_dir: Path) -> None:
    """
    Sauvegarde les données météo brutes en JSON, une ligue par fichier.
    Exemple de fichier produit : data/raw/api_weather/premier_league_2022_weather.json

    Skip les fichiers déjà existants (idempotence).
    Une erreur d'écriture sur une ligue n'arrête pas les autres.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for league_name, results in all_data.items():
        if _file_exists(league_name, season, output_dir):
            logger.info(f"[SKIP] {league_name} {season} — fichier déjà existant")
            continue

        filepath = build_filepath(output_dir, league_name, season, "weather")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"[SAVE] {len(results)} match(s) sauvegardé(s) → {filepath}")
        except OSError as e:
            logger.error(f"Impossible d'écrire {filepath} : {e}")


def extract_and_save_season(
    season: int,
    leagues: list,
    stadiums_df: pd.DataFrame,
    fixtures_dir: Path
) -> None:
    """
    Point d'entrée par saison : vérifie l'idempotence AVANT d'extraire,
    extrait, puis sauvegarde immédiatement ligue par ligue.

    Le check _file_exists() est ici — pas dans extract_weather_for_league() —
    parce que c'est une décision d'orchestration : "ai-je déjà traité
    cette ligue/saison entière ?". extract_weather_for_league() reste pure.

    Une défaillance sur une ligue est isolée — les autres continuent.
    """
    for league_name in leagues:
        # Idempotence : si le fichier existe déjà, on ne retélécharge rien
        if _file_exists(league_name, season, OUTPUT_DIR):
            logger.info(f"[SKIP] {league_name} {season} — déjà traité")
            continue

        logger.info(f"=== Traitement : {league_name} {season} ===")
        try:
            results = extract_weather_for_league(league_name, season, stadiums_df, fixtures_dir)
            save_raw_data({league_name: results}, season, OUTPUT_DIR)
        except Exception as e:
            logger.error(f"Échec traitement {league_name} {season} : {e} — on continue avec les autres ligues")


def run_pipeline(seasons: list = SEASONS) -> None:
    """
    Point d'entrée principal du pipeline météo.
    Charge les référentiels, boucle sur les saisons, délègue à extract_and_save_season().

    load_stadiums() et load_leagues() lèvent FileNotFoundError si leurs CSV
    sont absents — erreur bloquante intentionnelle : sans référentiels,
    aucun appel API ne peut être fait.

    Une défaillance sur une saison n'arrête pas les autres.
    """
    logger.info("=== Démarrage pipeline météo Open-Meteo ===")

    # Chargement des référentiels — bloquant si absents
    stadiums_df = load_stadiums(STADIUMS_CSV)
    leagues = list(load_leagues(LEAGUES_CSV, id_column="league_id").keys())

    for season in seasons:
        logger.info(f"--- Saison {season} ---")
        try:
            extract_and_save_season(season, leagues, stadiums_df, FIXTURES_DIR)
        except Exception as e:
            logger.error(f"Échec saison {season} : {e} — on continue avec les autres saisons")

    logger.info("=== Pipeline météo terminé ===")


if __name__ == "__main__":
    run_pipeline()