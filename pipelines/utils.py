import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Nommage des fichiers
# =============================================================================

def normalize_league_name(league_name: str) -> str:
    """
    Normalise un nom de ligue en nom de fichier sûr.
    Exemple : "Premier League" → "premier_league"

    Utilisé partout où un nom de fichier est construit depuis un nom de ligue,
    pour garantir une convention unique entre les pipelines qui écrivent
    (api_football) et ceux qui lisent (api_weather).
    """
    return league_name.lower().replace(" ", "_")


def build_filepath(base_dir: Path, league_name: str, season: int, data_type: str) -> Path:
    """
    Construit le chemin complet d'un fichier JSON pour une (ligue, saison, type).
    Exemple : build_filepath(Path("data/raw/api_football"), "Premier League", 2022, "fixtures")
              → data/raw/api_football/premier_league_2022_fixtures.json

    Centralise la convention de nommage — un seul endroit à modifier si elle change.
    Les deux pipelines (api_football et api_weather) utilisent cette fonction
    pour écrire et lire les fichiers, ce qui garantit qu'ils parlent des mêmes fichiers.
    """
    safe_name = normalize_league_name(league_name)
    return base_dir / f"{safe_name}_{season}_{data_type}.json"


# =============================================================================
# Chargement des référentiels
# =============================================================================

def load_leagues(leagues_csv: Path, id_column: str = "league_id") -> dict:
    """
    Charge les ligues cibles depuis dbt/seeds/leagues.csv.
    Retourne un dict {league_name: id} où id est la colonne spécifiée par id_column.

    Exemples :
    - load_leagues(csv) → {league_name: league_id}  (API-Football)
    - load_leagues(csv, id_column="kaggle_league_id") → {league_name: kaggle_league_id}

    Lève FileNotFoundError si le CSV est absent — erreur bloquante intentionnelle :
    sans ce référentiel, aucun pipeline ne peut démarrer.
    """
    if not leagues_csv.exists():
        raise FileNotFoundError(
            f"{leagues_csv} introuvable — vérifie que dbt/seeds/leagues.csv existe"
        )

    df = pd.read_csv(leagues_csv)
    leagues = dict(zip(df["league_name"], df[id_column]))
    logger.info(f"{len(leagues)} ligue(s) chargée(s) depuis {leagues_csv} : {list(leagues.keys())}")
    return leagues

def load_stadiums(stadiums_csv: Path) -> pd.DataFrame:
    """
    Charge le référentiel des stades depuis dbt/seeds/stadiums.csv.
    Retourne un DataFrame avec les colonnes :
    team_name, stadium_name, city, latitude, longitude.

    Lève FileNotFoundError si le CSV est absent — erreur bloquante intentionnelle :
    sans coordonnées GPS, aucun appel Open-Meteo ne peut être fait.
    """
    if not stadiums_csv.exists():
        raise FileNotFoundError(
            f"{stadiums_csv} introuvable — vérifie que dbt/seeds/stadiums.csv existe "
            f"(généré par scripts/generate_stadiums_seed.py)"
        )

    df = pd.read_csv(stadiums_csv)
    logger.info(f"{len(df)} stade(s) chargé(s) depuis {stadiums_csv}")
    return df