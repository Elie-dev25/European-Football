import pandas as pd 



PLAYER_POSITION_COLUMNS = (
    [f"home_player_X{i}" for i in range(1, 12)] +
    [f"away_player_X{i}" for i in range(1, 12)] +
    [f"home_player_Y{i}" for i in range(1, 12)] +
    [f"away_player_Y{i}" for i in range(1, 12)]
)

PLAYER_ID_COLUMNS = (
    [f"home_player_{i}" for i in range(1, 12)] +
    [f"away_player_{i}" for i in range(1, 12)]
)

ODDS_COLUMNS = [
    f"{bookmaker}{outcome}"
    for bookmaker in ["B365", "BW", "IW", "LB", "PS", "WH", "SJ", "VC", "GB", "BS"]
    for outcome in ["H", "D", "A"]
]

XML_COLUMNS = ["goal", "shoton", "shotoff", "foulcommit", "card", "cross", "corner", "possession"]


def flatten_league(raw_json: list[dict]) -> pd.DataFrame:
    """
    Transforme le JSON brut Kaggle League.json en DataFrame aligné sur RAW.LEAGUE.
    Ce cas ne contient aucune structure imbriquée — seul un renommage de colonnes est nécessaire.
    """
    df = pd.DataFrame(raw_json)
    df = df.rename(columns={
        "id": "league_id",
        "name": "league_name",
        # country_id ne change pas de nom
    })
    return df[["league_id", "country_id", "league_name"]] 


def flatten_team(raw_json: list[dict]) -> pd.DataFrame:
    """
    Aplatit le JSON Kaggle team.json vers le schéma RAW.TEAM.

    Le JSON source est déjà plat et ses clés correspondent déjà aux colonnes
    cibles, donc pas de renommage nécessaire.

    team_fifa_api_id arrive en float dans le JSON (ex. 673.0) alors que la
    colonne cible est un entier nullable (peut être NULL pour certaines
    équipes) — conversion vers Int64 (nullable pandas) pour éviter d'écrire
    "673.0" au lieu de "673" en base.

    Bronze strict : aucune ligne filtrée, les 299 équipes sont conservées.
    """
    df = pd.DataFrame(raw_json)
    df["team_fifa_api_id"] = df["team_fifa_api_id"].astype("Int64")
    return df[["id", "team_api_id", "team_fifa_api_id", "team_long_name", "team_short_name"]] 


def flatten_team_attributes(raw_json: list[dict]) -> pd.DataFrame:
    """
    Aplatit le JSON Kaggle Team_Attributes.json vers le schéma RAW.TEAM_ATTRIBUTES.

    Renommage camelCase -> snake_case (le JSON source utilise buildUpPlaySpeed,
    la table cible build_up_play_speed, etc.) — contrairement à LEAGUE/TEAM,
    les clés ne correspondent pas directement ici.

    build_up_play_dribbling contient de vrais NaN dans les données (confirmé,
    pas une précaution abstraite) -> converti en Int64 nullable comme
    team_fifa_api_id dans flatten_team.

    date arrive en string ("2010-02-22 00:00:00") -> revalidée via pd.to_datetime
    puis reformatée en texte propre (.dt.strftime) plutôt que laissée en
    datetime64. Raison : write_pandas corrompt silencieusement les colonnes
    datetime64 lors de l'écriture (bug du chemin Arrow -> Parquet -> Snowflake,
    confirmé empiriquement, indépendant de la magnitude ns/us). Contournement
    validé : transporter la date en STRING jusqu'en STAGING, conversion en
    TIMESTAMP_NTZ déléguée au MERGE (SQL pur, aucune perte de précision).

    2 lignes strictement dupliquées détectées dans la source (team_api_id=9996,
    date=2015-09-10, id 860 et 861 — contenu identique en tout point sauf id) ->
    dédupliquées sur (team_api_id, date), la clé métier de la table.
    """
    df = pd.DataFrame(raw_json)

    df = df.rename(columns={
        "buildUpPlaySpeed": "build_up_play_speed",
        "buildUpPlaySpeedClass": "build_up_play_speed_class",
        "buildUpPlayDribbling": "build_up_play_dribbling",
        "buildUpPlayDribblingClass": "build_up_play_dribbling_class",
        "buildUpPlayPassing": "build_up_play_passing",
        "buildUpPlayPassingClass": "build_up_play_passing_class",
        "buildUpPlayPositioningClass": "build_up_play_positioning_class",
        "chanceCreationPassing": "chance_creation_passing",
        "chanceCreationPassingClass": "chance_creation_passing_class",
        "chanceCreationCrossing": "chance_creation_crossing",
        "chanceCreationCrossingClass": "chance_creation_crossing_class",
        "chanceCreationShooting": "chance_creation_shooting",
        "chanceCreationShootingClass": "chance_creation_shooting_class",
        "chanceCreationPositioningClass": "chance_creation_positioning_class",
        "defencePressure": "defence_pressure",
        "defencePressureClass": "defence_pressure_class",
        "defenceAggression": "defence_aggression",
        "defenceAggressionClass": "defence_aggression_class",
        "defenceTeamWidth": "defence_team_width",
        "defenceTeamWidthClass": "defence_team_width_class",
        "defenceDefenderLineClass": "defence_defender_line_class",
    })

    df["build_up_play_dribbling"] = df["build_up_play_dribbling"].astype("Int64")
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df = df.drop_duplicates(subset=["team_api_id", "date"], keep="first")

    return df[[
        "id", "team_fifa_api_id", "team_api_id", "date",
        "build_up_play_speed", "build_up_play_speed_class",
        "build_up_play_dribbling", "build_up_play_dribbling_class",
        "build_up_play_passing", "build_up_play_passing_class",
        "build_up_play_positioning_class",
        "chance_creation_passing", "chance_creation_passing_class",
        "chance_creation_crossing", "chance_creation_crossing_class",
        "chance_creation_shooting", "chance_creation_shooting_class",
        "chance_creation_positioning_class",
        "defence_pressure", "defence_pressure_class",
        "defence_aggression", "defence_aggression_class",
        "defence_team_width", "defence_team_width_class",
        "defence_defender_line_class",
    ]]



def flatten_match(raw_json: list[dict]) -> pd.DataFrame:
    """
    Aplatit le JSON Kaggle Match.json vers le schéma RAW.MATCH.

    Les clés du JSON correspondent déjà exactement aux colonnes cibles
    (contrairement à TEAM_ATTRIBUTES) : aucun renommage nécessaire.

    Colonnes joueurs/positions (66 colonnes) : converties en Int64 nullable.
    14 colonnes ont des NaN confirmés (home_player_9/10/11, away_player_1-11),
    et le JSON source mélange par endroits int/float pour une même colonne
    (ex. away_player_X10: 5 vs away_player_X11: 5.0) même sans NaN présent —
    Int64 absorbe les deux cas de façon uniforme.

    Colonnes XML (goal, shoton, etc.) : conservées brutes en string, aucun
    parsing (repoussé vers Silver, cohérent avec le commentaire du SQL RAW).

    Colonnes de cotes (30, 10 bookmakers x H/D/A) : laissées en float natif,
    NUMBER(10,2) côté Snowflake accepte les NaN nativement.

    Bronze strict : aucune ligne filtrée (14 585 matchs, déjà filtrés aux
    5 ligues au niveau de l'extraction, pas ici).
    """
    df = pd.DataFrame(raw_json)

    for col in PLAYER_POSITION_COLUMNS + PLAYER_ID_COLUMNS:
        df[col] = df[col].astype("Int64")

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    target_columns = (
        ["id", "country_id", "league_id", "season", "stage", "date", "match_api_id",
         "home_team_api_id", "away_team_api_id", "home_team_goal", "away_team_goal"]
        + PLAYER_POSITION_COLUMNS
        + PLAYER_ID_COLUMNS
        + XML_COLUMNS
        + ODDS_COLUMNS
    )

    return df[target_columns] 


def flatten_fixtures(raw_json: list[dict]) -> pd.DataFrame:
    """
    Aplatit les réponses API-Football (fixtures) vers le schéma RAW.FIXTURES,
    via json_normalize plutôt qu'une extraction manuelle champ par champ.
    """
    df = pd.json_normalize(raw_json, sep="_")

    df = df.rename(columns={
        "fixture_id": "fixture_id",
        "fixture_referee": "referee",
        "fixture_date": "match_date",
        "fixture_timestamp": "match_timestamp",
        "fixture_venue_id": "venue_id",
        "fixture_venue_name": "venue_name",
        "fixture_venue_city": "venue_city",
        "fixture_status_long": "status_long",
        "fixture_status_short": "status_short",
        "fixture_status_elapsed": "status_elapsed",
        "league_id": "league_id",
        "league_name": "league_name",
        "league_country": "league_country",
        "league_season": "season",
        "league_round": "round",
        "teams_home_id": "home_team_id",
        "teams_home_name": "home_team_name",
        "teams_home_winner": "home_winner",
        "teams_away_id": "away_team_id",
        "teams_away_name": "away_team_name",
        "teams_away_winner": "away_winner",
        "goals_home": "goals_home",
        "goals_away": "goals_away",
        "score_halftime_home": "halftime_home",
        "score_halftime_away": "halftime_away",
        "score_fulltime_home": "fulltime_home",
        "score_fulltime_away": "fulltime_away",
        "score_extratime_home": "extratime_home",
        "score_extratime_away": "extratime_away",
        "score_penalty_home": "penalty_home",
        "score_penalty_away": "penalty_away",
    })

    target_columns = [
        "fixture_id", "referee", "match_date", "match_timestamp",
        "venue_id", "venue_name", "venue_city",
        "status_long", "status_short", "status_elapsed",
        "league_id", "league_name", "league_country", "season", "round",
        "home_team_id", "home_team_name", "home_winner",
        "away_team_id", "away_team_name", "away_winner",
        "goals_home", "goals_away",
        "halftime_home", "halftime_away",
        "fulltime_home", "fulltime_away",
        "extratime_home", "extratime_away",
        "penalty_home", "penalty_away",
    ]

    return df[target_columns] 


def flatten_standings(raw_json: list[dict]) -> pd.DataFrame:
    """
    Aplatit les réponses API-Football (standings) vers le schéma RAW.STANDINGS.

    Structure à double imbrication : chaque élément de raw_json est une ligue,
    dont league["standings"] est une liste de groupes (list de list), chaque
    groupe contenant les équipes classées. Pour ces 5 championnats nationaux,
    un seul groupe est attendu, mais la structure API le permet et est
    parcourue sans supposer qu'il n'y en a qu'un.

    json_normalize appliqué après le déroulement manuel des deux niveaux de
    liste, pour aplatir chaque dict d'équipe (team.id, all.played, etc.).
    """
    all_team_rows = []

    for item in raw_json:
        league = item["league"]
        league_id = league["id"]
        league_name = league["name"]
        league_country = league["country"]
        season = league["season"]

        for group in league["standings"]:
            for team_entry in group:
                team_entry["_league_id"] = league_id
                team_entry["_league_name"] = league_name
                team_entry["_league_country"] = league_country
                team_entry["_season"] = season
                all_team_rows.append(team_entry)

    df = pd.json_normalize(all_team_rows, sep="_")

    df = df.rename(columns={
        "_league_id": "league_id",
        "_league_name": "league_name",
        "_league_country": "league_country",
        "_season": "season",
        "team_id": "team_id",
        "team_name": "team_name",
        "rank": "rank",
        "points": "points",
        "goalsDiff": "goals_diff",
        "group": "group_name",
        "form": "form",
        "status": "status",
        "description": "description",
        "all_played": "played_total",
        "all_win": "win_total",
        "all_draw": "draw_total",
        "all_lose": "lose_total",
        "all_goals_for": "goals_for_total",
        "all_goals_against": "goals_against_total",
        "home_played": "played_home",
        "home_win": "win_home",
        "home_draw": "draw_home",
        "home_lose": "lose_home",
        "home_goals_for": "goals_for_home",
        "home_goals_against": "goals_against_home",
        "away_played": "played_away",
        "away_win": "win_away",
        "away_draw": "draw_away",
        "away_lose": "lose_away",
        "away_goals_for": "goals_for_away",
        "away_goals_against": "goals_against_away",
        "update": "last_update",
    })

    target_columns = [
        "league_id", "league_name", "league_country", "season",
        "team_id", "team_name", "rank", "points", "goals_diff",
        "group_name", "form", "status", "description",
        "played_total", "win_total", "draw_total", "lose_total",
        "goals_for_total", "goals_against_total",
        "played_home", "win_home", "draw_home", "lose_home",
        "goals_for_home", "goals_against_home",
        "played_away", "win_away", "draw_away", "lose_away",
        "goals_for_away", "goals_against_away",
        "last_update",
    ]

    return df[target_columns] 


def flatten_player_statistics(raw_json: list[dict]) -> pd.DataFrame:
    """
    Aplatit les réponses API-Football "players statistics" (top scorers ET
    top assists partagent cet endroit/cette structure — confirmé via
    03_raw_top_scorers.sql et 04_raw_top_assists.sql, colonnes identiques).

    Chaque joueur a un dict "player" (infos statiques) et une liste
    "statistics" (1 entrée par équipe où il a joué cette saison — confirmé :
    certains joueurs transférés en cours de saison ont 2 entrées). Une ligne
    est générée par (joueur, équipe), cohérent avec la clé composite
    (league_id, season, team_id, player_id) des deux tables cibles.

    height/weight restent en STRING sans conversion (déjà des strings sans
    unité dans le JSON source, ex. "178", pas "178 cm").
    """
    rows = []

    for item in raw_json:
        player = item["player"]

        for stat in item["statistics"]:
            rows.append({
                "player_id": player["id"],
                "player_name": player["name"],
                "firstname": player["firstname"],
                "lastname": player["lastname"],
                "age": player["age"],
                "birth_date": player["birth"]["date"],
                "birth_place": player["birth"]["place"],
                "birth_country": player["birth"]["country"],
                "nationality": player["nationality"],
                "height": player["height"],
                "weight": player["weight"],
                "injured": player["injured"],
                "team_id": stat["team"]["id"],
                "team_name": stat["team"]["name"],
                "league_id": stat["league"]["id"],
                "league_name": stat["league"]["name"],
                "league_country": stat["league"]["country"],
                "season": stat["league"]["season"],
                "appearences": stat["games"]["appearences"],
                "lineups": stat["games"]["lineups"],
                "minutes": stat["games"]["minutes"],
                "position": stat["games"]["position"],
                "rating": stat["games"]["rating"],
                "captain": stat["games"]["captain"],
                "subs_in": stat["substitutes"]["in"],
                "subs_out": stat["substitutes"]["out"],
                "subs_bench": stat["substitutes"]["bench"],
                "shots_total": stat["shots"]["total"],
                "shots_on": stat["shots"]["on"],
                "goals_total": stat["goals"]["total"],
                "goals_conceded": stat["goals"]["conceded"],
                "goals_assists": stat["goals"]["assists"],
                "goals_saves": stat["goals"]["saves"],
                "passes_total": stat["passes"]["total"],
                "passes_key": stat["passes"]["key"],
                "passes_accuracy": stat["passes"]["accuracy"],
                "tackles_total": stat["tackles"]["total"],
                "tackles_blocks": stat["tackles"]["blocks"],
                "tackles_interceptions": stat["tackles"]["interceptions"],
                "duels_total": stat["duels"]["total"],
                "duels_won": stat["duels"]["won"],
                "dribbles_attempts": stat["dribbles"]["attempts"],
                "dribbles_success": stat["dribbles"]["success"],
                "dribbles_past": stat["dribbles"]["past"],
                "fouls_drawn": stat["fouls"]["drawn"],
                "fouls_committed": stat["fouls"]["committed"],
                "cards_yellow": stat["cards"]["yellow"],
                "cards_yellowred": stat["cards"]["yellowred"],
                "cards_red": stat["cards"]["red"],
                "penalty_won": stat["penalty"]["won"],
                "penalty_committed": stat["penalty"]["commited"],
                "penalty_scored": stat["penalty"]["scored"],
                "penalty_missed": stat["penalty"]["missed"],
                "penalty_saved": stat["penalty"]["saved"],
            })

    return pd.DataFrame(rows)


# Alias : les deux tables (TOP_SCORERS, TOP_ASSISTS) partagent le même endpoint
# API-Football et donc la même structure de flatten — confirmé sur les deux
# schémas SQL (03_raw_top_scorers.sql, 04_raw_top_assists.sql, colonnes identiques).
flatten_top_scorers = flatten_player_statistics
flatten_top_assists = flatten_player_statistics 



def flatten_weather(raw_json: list[dict]) -> pd.DataFrame:
    """
    Aplatit les données Open-Meteo (weather) vers le schéma RAW.WEATHER.

    Chaque élément de raw_json est un match, avec des champs statiques
    (fixture_id, kickoff, team_home) et une liste hourly_weather (48 heures
    de mesures, une par heure autour du kickoff). Les dicts de hourly_weather
    sont déjà plats (weather_time, temperature_2m, etc.) — json_normalize
    avec record_path déroule une ligne par heure, meta rattache les champs
    statiques du match à chaque ligne générée.

    Bronze strict : aucune ligne filtrée, aucune agrégation (moyenne/somme
    repoussée vers Silver, cohérent avec le commentaire du SQL RAW).
    """
    df = pd.json_normalize(
        raw_json,
        record_path="hourly_weather",
        meta=["fixture_id", "kickoff", "team_home"],
        sep="_",
    )

    return df[[
        "fixture_id", "kickoff", "team_home",
        "weather_time", "temperature_2m", "precipitation",
        "windspeed_10m", "weathercode",
    ]]