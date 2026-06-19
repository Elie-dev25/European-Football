import os
import json
import time
import logging
import requests
import pandas as pd
from pathlib import Path

# Configuration du logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# === Configuration ===

# Dossier contenant les fixtures JSON téléchargées en Phase 1
FIXTURES_DIR = Path("data/raw/api_football")

# Fichier de sortie — directement dans dbt/seeds/ pour être versionné
OUTPUT_CSV = Path("dbt/seeds/stadiums.csv")

# Nominatim — API OpenStreetMap, gratuite, pas de clé requise
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Header obligatoire — Nominatim exige un User-Agent identifiant ton application
# Sans ça, les requêtes sont bloquées
NOMINATIM_HEADERS = {
    "User-Agent": "EuropeanFootballAnalytics/1.0 (elienjinedev@gmail.com)"
}

# Délai entre chaque appel Nominatim — leur politique impose 1 req/seconde maximum
NOMINATIM_DELAY = 1.1  # un peu plus que 1 seconde pour être sûr de ne pas dépasser la limite 

def extract_teams_from_fixtures(fixtures_dir: Path) -> pd.DataFrame:
    """
    Parcourt tous les fichiers *_fixtures.json dans fixtures_dir,
    toutes saisons confondues, et extrait pour chaque match :
    - le nom de l'équipe à domicile (home team)
    - le nom du stade
    - la ville

    On ne prend que l'équipe à DOMICILE parce que c'est elle qui joue
    dans son stade — l'équipe visiteuse joue dans le stade de l'adversaire.

    Retourne un DataFrame dédupliqué — une ligne par équipe.
    """
    records = []

    # Trouver tous les fichiers fixtures, toutes saisons confondues
    fixture_files = list(fixtures_dir.glob("*_fixtures.json"))

    if not fixture_files:
        logger.error(f"Aucun fichier fixtures trouvé dans {fixtures_dir}")
        return pd.DataFrame()

    logger.info(f"{len(fixture_files)} fichier(s) fixtures trouvé(s)")

    for filepath in fixture_files:
        logger.info(f"Lecture de {filepath.name}...")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        matches = data.get("response", [])

        for match in matches:
            try:
                home_team = match["teams"]["home"]["name"]
                venue_name = match["fixture"]["venue"]["name"]
                venue_city = match["fixture"]["venue"]["city"]

                # On ignore les matchs sans infos de stade
                # (peut arriver sur terrain neutre ou données manquantes)
                if not venue_name or not venue_city:
                    continue

                records.append({
                    "team_name": home_team,
                    "stadium_name": venue_name,
                    "city": venue_city
                })

            except (KeyError, TypeError):
                # Si la structure JSON est inattendue sur un match, on skip
                # et on log pour pouvoir investiguer si nécessaire
                logger.warning(f"Structure inattendue sur un match dans {filepath.name} — ignoré")
                continue

    if not records:
        logger.error("Aucune donnée extraite des fixtures")
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Dédupliquer — une équipe peut apparaître dans plusieurs saisons
    # et plusieurs fichiers. On garde la première occurrence.
    # drop_duplicates sur team_name suffit car un club joue toujours
    # dans le même stade (on ignore les rares cas de déménagement)
    df = df.drop_duplicates(subset=["team_name"], keep="first")
    df = df.sort_values("team_name").reset_index(drop=True)

    logger.info(f"{len(df)} équipes uniques extraites")
    return df 

def get_coordinates(stadium_name: str, city: str) -> tuple:
    """
    Appelle l'API Nominatim (OpenStreetMap) pour récupérer les coordonnées
    GPS d'un stade à partir de son nom et de sa ville.

    Retourne un tuple (latitude, longitude) ou (None, None) si non trouvé.
    """
    # On cherche d'abord avec le nom du stade + la ville
    # Si Nominatim ne trouve rien, on retente avec juste la ville
    # pour ne pas bloquer sur un stade au nom inhabituel
    queries = [
        f"{stadium_name} {city}",  # tentative précise
        city                        # tentative de repli
    ]

    for query in queries:
        params = {
            "q": query,
            "format": "json",
            "limit": 1
        }

        try:
            response = requests.get(
                NOMINATIM_URL,
                headers=NOMINATIM_HEADERS,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                results = response.json()

                if results:
                    lat = float(results[0]["lat"])
                    lon = float(results[0]["lon"])
                    logger.info(f"Coordonnées trouvées pour '{query}' → ({lat}, {lon})")
                    return lat, lon
                else:
                    logger.warning(f"Aucun résultat Nominatim pour '{query}', tentative suivante...")

            else:
                logger.error(f"Erreur HTTP {response.status_code} pour '{query}'")

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout pour '{query}'")

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau pour '{query}' : {e}")

        except Exception as e:
            logger.error(f"Erreur inattendue pour '{query}' : {e}")

        finally:
            # Respecter la limite de 1 req/seconde de Nominatim
            # Le finally garantit qu'on attend même si une exception est levée
            time.sleep(NOMINATIM_DELAY)

    # Aucune des deux tentatives n'a fonctionné
    logger.warning(f"Coordonnées introuvables pour {stadium_name} ({city}) — à compléter manuellement")
    return None, None 

def generate_stadiums_seed(fixtures_dir: Path, stadiums_csv: Path) -> None:    
    """
    Orchestre l'ensemble du processus :
    1. Extrait les équipes/stades/villes depuis les fixtures JSON
    2. Récupère les coordonnées GPS via Nominatim pour chaque stade
    3. Sauvegarde le résultat dans stadiums_csv

    Ce script est conçu pour être relancé à chaque nouvelle saison —
    il lit tous les fichiers fixtures disponibles et produit un CSV
    cumulatif de toutes les équipes vues sur toutes les saisons.
    """
    logger.info("=== Démarrage de la génération du seed stadiums ===")

    # Étape 1 — Extraire les équipes depuis les fixtures
    df = extract_teams_from_fixtures(fixtures_dir)

    if df.empty:
        logger.error("Aucune donnée extraite — arrêt du script")
        return

    # Étape 2 — Charger le CSV existant si présent
    # Permet de ne pas recalculer les coordonnées déjà connues
    # quand on relance le script pour une nouvelle saison
    existing_teams = set()

    if stadiums_csv.exists():
        df_existing = pd.read_csv(stadiums_csv)
        existing_teams = set(df_existing["team_name"].tolist())
        logger.info(f"{len(existing_teams)} équipes déjà présentes dans le CSV existant")

        # On fusionne — les nouvelles équipes s'ajoutent aux anciennes
        df = pd.concat([df_existing, df], ignore_index=True)
        df = df.drop_duplicates(subset=["team_name"], keep="first")
        df = df.sort_values("team_name").reset_index(drop=True)

    # Étape 3 — Récupérer les coordonnées uniquement pour les nouvelles équipes
    new_teams = df[~df["team_name"].isin(existing_teams)]
    logger.info(f"{len(new_teams)} nouvelle(s) équipe(s) à géocoder")

    for idx, row in new_teams.iterrows():
        lat, lon = get_coordinates(row["stadium_name"], row["city"])
        df.at[idx, "latitude"] = lat
        df.at[idx, "longitude"] = lon

    # Étape 4 — Sauvegarder le CSV
    stadiums_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(stadiums_csv, index=False, encoding="utf-8")

    # Résumé final
    total = len(df)
    geocoded = df["latitude"].notna().sum()
    missing = df["latitude"].isna().sum()

    logger.info(f"=== Seed généré : {total} équipes total, {geocoded} géocodées, {missing} manquantes ===")
    logger.info(f"Fichier sauvegardé : {stadiums_csv}")

    if missing > 0:
        missing_teams = df[df["latitude"].isna()]["team_name"].tolist()
        logger.warning(f"Équipes sans coordonnées à compléter manuellement : {missing_teams}")

if __name__ == "__main__":
    generate_stadiums_seed(
        fixtures_dir=FIXTURES_DIR,
        stadiums_csv=OUTPUT_CSV
    )