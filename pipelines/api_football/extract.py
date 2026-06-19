import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

# Nos 5 ligues cibles avec leurs IDs
LEAGUE_IDS = {
    "Premier League": 39,
    "Ligue 1": 61,
    "Bundesliga": 78,
    "Serie A": 135,
    "La Liga": 140
}

# Phase 1 - Validation architecture
SEASONS = [2022]

# Phase 2 - Extension (après validation)
# SEASONS = [2022, 2023, 2024] 

def get_standings(league_id: int, season: int) -> dict:
    """
    Récupère le classement d'une ligue pour une saison donnée.
    """
    url = f"{BASE_URL}/standings"
    
    params = {
        "league": league_id,
        "season": season
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur {response.status_code} pour la ligue {league_id}")
        return {} 
    

def get_fixtures(league_id: int, season: int) -> dict:
    """
    Récupère tous les matchs (fixtures) d'une ligue pour une saison donnée.
    """
    url = f"{BASE_URL}/fixtures"

    params = {
        "league": league_id,
        "season": season
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur {response.status_code} pour la ligue {league_id}")
        return {}    
    

def get_top_scorers(league_id: int, season: int) -> dict:
    """
    Récupère les meilleurs buteurs d'une ligue pour une saison donnée.
    """
    url = f"{BASE_URL}/players/topscorers"

    params = {
        "league": league_id,
        "season": season
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur {response.status_code} pour la ligue {league_id}")
        return {}  
    
def get_top_assists(league_id: int, season: int) -> dict:
    """
    Récupère les meilleurs passeurs d'une ligue pour une saison donnée.
    """
    url = f"{BASE_URL}/players/topassists"

    params = {
        "league": league_id,
        "season": season
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur {response.status_code} pour la ligue {league_id}")
        return {} 
    
def extract_league_data(league_id: int, season: int) -> dict:
    """
    Orchestre les 4 appels API pour une ligue et une saison données.
    Retourne un dictionnaire regroupant standings, fixtures, top scorers et top assists.
    """
    print(f"Extraction league={league_id}, season={season}...")

    data = {
        "standings": get_standings(league_id, season),
        "fixtures": get_fixtures(league_id, season),
        "top_scorers": get_top_scorers(league_id, season),
        "top_assists": get_top_assists(league_id, season)
    }

    print(f"Terminé pour league={league_id}, season={season}")
    return data



# if __name__ == "__main__":
#     data = get_top_scorers(LEAGUE_IDS["Premier League"], 2022)
    
#     print(f"Statut: {data.get('results')} résultats")
#     print(f"Premier buteur: {data['response'][0]['player']['name']}")
#     print(f"Ses buts: {data['response'][0]['statistics'][0]['goals']['total']}")

# if __name__ == "__main__":
#     data = get_fixtures(LEAGUE_IDS["Premier League"], 2022)
#     with open("data/fixtures_pl_2022.json", "w") as f:
#         json.dump(data, f, indent=2)
#     print(f"{len(data.get('response', []))} matchs récupérés") 

if __name__ == "__main__":
    data = get_top_assists(LEAGUE_IDS["Premier League"], 2022)
    
    print(f"Statut: {data.get('results')} résultats")
    print(f"Premier passeur: {data['response'][0]['player']['name']}")
    print(f"Ses passes: {data['response'][0]['statistics'][0]['goals']['assists']}")

