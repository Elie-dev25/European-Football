"""
Table de correspondance (crosswalk) entre les noms d'équipes Kaggle (2008-2016)
et API-Football (2022-2024).

Pourquoi un dict manuel plutôt qu'un fuzzy matching :
Le foot européen contient trop de noms proches entre eux (Real Madrid / Real Betis /
Real Sociedad / Real Valladolid / Real Zaragoza), un algorithme de similarité de
chaînes risquerait de faux positifs silencieux. Un mapping explicite est plus long
à construire mais déterministe et auditable.

Clé   = nom API-Football (home_team_name / away_team_name dans RAW.FIXTURES)
Valeur = nom Kaggle (team_long_name dans RAW.TEAM)
"""

# Correspondances exactes (aucune transformation nécessaire, incluses ici
# uniquement pour que ce dict soit la SEULE source de vérité du mapping)
EXACT_MATCHES = [
    "Arsenal", "Aston Villa", "Atalanta", "Bologna", "Borussia Dortmund",
    "Bournemouth", "Chelsea", "Crystal Palace", "Eintracht Frankfurt", "Empoli",
    "FC Augsburg", "FC Schalke 04", "Fiorentina", "Fulham", "Hamburger SV",
    "Hellas Verona", "Inter", "Juventus", "Lazio", "Lecce", "Liverpool",
    "Manchester City", "Manchester United", "Napoli", "Rayo Vallecano",
    "Real Sociedad", "SC Freiburg", "Sampdoria", "Sassuolo", "Southampton",
    "Stade Brestois 29", "Torino", "Udinese", "VfB Stuttgart", "VfL Wolfsburg",
    "1. FC Köln","Everton",
]

# Correspondances divergentes, validées manuellement une par une
TEAM_CROSSWALK = {
    "1899 Hoffenheim"                              :"TSG 1899 Hoffenheim",
    "AC Milan"                                     :"Milan",
    "AS Roma"                                      :"Roma",
    "Ajaccio"                                      :"AC Ajaccio",  # pas GFC Ajaccio, club distinct
    "Almeria"                                      :"UD Almería",
    "Angers"                                       :"Angers SCO",
    "Athletic Club"                                :"Athletic Club de Bilbao",
    "Atletico Madrid"                              :"Atlético Madrid",
    "Auxerre"                                      :"AJ Auxerre",
    "Barcelona"                                    :"FC Barcelona",
    "Bayer Leverkusen"                             :"Bayer 04 Leverkusen",
    "Bayern Munich"                                :"FC Bayern Munich",
    "Borussia Monchengladbach"                     :"Borussia Mönchengladbach",
    "Celta Vigo"                                   :"RC Celta de Vigo",
    "Elche"                                        :"Elche CF",
    "Espanyol"                                     :"RCD Espanyol",
    "Estac Troyes"                                 :"ES Troyes AC",
    "Getafe"                                       :"Getafe CF",
    "Hertha Berlin"                                :"Hertha BSC Berlin",
    "Leicester"                                    :"Leicester City",
    "Lens"                                         :"RC Lens",
    "Lille"                                        :"LOSC Lille",
    "Lorient"                                      :"FC Lorient",
    "Lyon"                                         :"Olympique Lyonnais",
    "Mallorca"                                     :"RCD Mallorca",
    "Marseille"                                    :"Olympique de Marseille",
    "Monaco"                                       :"AS Monaco",
    "Montpellier"                                  :"Montpellier Hérault SC",
    "Nantes"                                       :"FC Nantes",
    "Newcastle"                                    :"Newcastle United",
    "Nice"                                         :"OGC Nice",
    "Osasuna"                                      :"CA Osasuna",
    "Paris Saint Germain"                          :"Paris Saint-Germain",
    "Real Betis"                                   :"Real Betis Balompié",
    "Real Madrid"                                  :"Real Madrid CF",
    "Reims"                                        :"Stade de Reims",
    "Rennes"                                       :"Stade Rennais FC",
    "Sevilla"                                      :"Sevilla FC",
    "Tottenham"                                    :"Tottenham Hotspur",
    "Toulouse"                                     :"Toulouse FC",
    "Valencia"                                     :"Valencia CF",
    "Valladolid"                                   :"Real Valladolid",
    "Vfl Bochum"                                   :"VfL Bochum",
    "Villarreal"                                   :"Villarreal CF",
    "Werder Bremen"                                :"SV Werder Bremen",
    "West Ham"                                     :"West Ham United",
    "Wolves"                                       :"Wolverhampton Wanderers",
    "FSV Mainz 05"                                 :"1. FSV Mainz 05",

}

# Clubs API-Football sans correspondance Kaggle : montés en D1 après 2016,
# donc absents du dataset historique 2008-2016. Non-match légitime, pas un bug.
KNOWN_UNMATCHED = [
    "Brentford", "Brighton", "Cadiz", "Clermont Foot", "Cremonese", "Girona",
    "Leeds", "Monza", "Nottingham Forest", "RB Leipzig", "Salernitana",
    "Spezia", "Strasbourg", "Union Berlin",
]


def build_full_crosswalk() -> dict[str, str]:
    """Fusionne exact matches + divergents en un seul dict api_name -> kaggle_name."""
    full = {name: name for name in EXACT_MATCHES}
    full.update(TEAM_CROSSWALK)
    return full