# Dette technique — European Football Analytics Platform

Document de suivi centralisé. Chaque entrée doit etre resolue ou
explicitement reconduite lors du refactoring global prevu en Phase 5 (Airflow).

## Configuration hardcodee dans le code Python

| Emplacement | Element | Raison du report | A faire |
|---|---|---|---|
| `pipelines/extractors/api_football/extract.py` | `data_types` (liste des endpoints) | Coherence avec le reste du projet en Phase 1-4 | Externaliser en YAML/config |
| `pipelines/extractors/kaggle/extract.py` | `TABLES_CONFIG` | Idem | Externaliser en YAML/config |
| `pipelines/loaders/s3_loader.py` | `SOURCES_CONFIG` | Idem - ajoute le 30/06/2026 | Externaliser en YAML/config |
| `pipelines/extractors/api_football/extract.py`, `api_weather/extract.py` | `SEASONS`, paths | Valider l'architecture sur 2022 d'abord | Externaliser, Phase 5 |

## Bugs connus / contournements manuels

*Aucune entree active — voir section Resolu.*

## Fonctions non utilisees dans le flux principal

| Emplacement | Element | Note |
|---|---|---|
| `pipelines/extractors/api_weather/extract.py` | `extract_all_leagues` | Existe mais plus appelee par `extract_and_save_season()` - utile tests/debug uniquement | 
| `pipelines/loaders/s3_loader.py` | `upload_kaggle_source` | Existe mais non appelee par `run_pipeline()` - upload one-shot manuel du fichier source Kaggle (gros fichier, cas particulier) |

## Limitations de testabilite

*Aucune entree active — voir section Resolu.*

## Scalabilite (non bloquant en Phase 1)

| Sujet | Note |
|---|---|
| Parallelisme absent | Contre-productif avec 100 req/jour API-Football en plan gratuit |
| Cache distribue absent | Pertinent seulement en multi-machines |
| Batching Open-Meteo | Optimisation possible Phase 6+ |

## Résolu

| Date | Emplacement | Probleme | Resolution |
|---|---|---|---|
| 03/07/2026 | `scripts/generate_stadiums_seed.py` | Nominatim retournait Southampton, Massachusetts au lieu de Southampton, UK (homonymie) | Ajout de `MANUAL_COORDINATES_OVERRIDES`, dict de coordonnees connues verifie avant tout appel Nominatim. Valide en conditions reelles (re-geocodage force de Southampton) |
| 03/07/2026 | `dbt/seeds/stadiums.csv` | 7 lignes corrompues (Bournemouth, Brentford, Brighton, Leeds, Leicester, Nottingham Forest, Wolves) issues d'un bug de quoting CSV lors du commit `74f7057` — doublons de chaque ligne encapsules entierement entre guillemets | Lignes supprimees apres verification qu'aucun code ne les referencait (`load_stadiums()` fait un lookup exact par `team_name`, jamais atteint par ces lignes malformees) |
| 03/07/2026 | `dbt/seeds/stadiums.csv` | Ligne orpheline `Southampton FC` (jamais ce nom dans les fixtures API-Football, qui utilisent `Southampton`) — vestige d'une correction manuelle anterieure sous un nom incorrect | Ligne supprimee |
| 03/07/2026 | `scripts/generate_stadiums_seed.py` | Bug d'indentation dans la boucle de geocodage : `df.at[idx, "latitude"/"longitude"]` places hors de la boucle `for`, donc executes une seule fois apres la boucle au lieu d'une fois par equipe | Corrige — les deux lignes reindentees a l'interieur de la boucle |
| 03/07/2026 | `pipelines/extractors/api_football/extract.py` | Fichiers `bundesliga_2022_top_assists.json` et `bundesliga_2022_top_scorers.json` vides (298 octets) — rate limit API-Football (10 req/min) depasse lors de l'extraction initiale | Nouvelle fonction `_is_valid_content()` : detecte une reponse vide et re-telecharge automatiquement, appliquee a la fois a la lecture (`extract_league_data`) et a l'ecriture (`save_raw_data`) — protection generalisee contre toute future ligue touchee par un rate limit, pas seulement Bundesliga. Fichiers re-extraits et valides (48 Ko chacun, conforme aux autres ligues) |
| 03/07/2026 | `pipelines/extractors/api_weather/extract.py` | `extract_and_save_season` lisait `OUTPUT_DIR` global plutot qu'un parametre injecte — tests obliges de patcher le module global | `output_dir` devient un parametre explicite avec `OUTPUT_DIR` en valeur par defaut — comportement production inchange, tests simplifies (appel normal avec `output_dir=tmp_path`) |

---
*Derniere mise a jour : 03/07/2026*