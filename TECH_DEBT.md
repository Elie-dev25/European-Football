# Dette technique — European Football Analytics Platform

Document de suivi centralisé. Chaque entrée doit être résolue ou
explicitement reconduite lors du refactoring global prévu en Phase 5 (Airflow).

## Configuration hardcodée dans le code Python

| Emplacement | Element | Raison du report | A faire |
|---|---|---|---|
| `pipelines/extractors/api_football/extract.py` | `data_types` (liste des endpoints) | Cohérence avec le reste du projet en Phase 1-4 | Externaliser en YAML/config |
| `pipelines/extractors/kaggle/extract.py` | `TABLES_CONFIG` | Idem | Externaliser en YAML/config |
| `pipelines/loaders/s3_loader.py` | `SOURCES_CONFIG` | Idem — ajouté le 30/06/2026 | Externaliser en YAML/config |
| `pipelines/extractors/api_football/extract.py`, `api_weather/extract.py` | `SEASONS`, paths | Valider l'architecture sur 2022 d'abord | Externaliser, Phase 5 |
| `pipelines/loaders/snowflake_loader.py` | `TABLES_CONFIG` (9 entrées), `SEASONS` | Valider la mécanique staging/merge sur un cas simple (LEAGUE) avant de figer un schéma de config — anticiper le format sur un seul exemple aurait probablement produit un schéma faux ou incomplet | Externaliser en YAML/config, Phase 5, en même temps que `data_types` et `SOURCES_CONFIG` |
| `pipelines/extractors/kaggle/extract.py`, `pipelines/loaders/snowflake_loader.py` | `TABLES_CONFIG` existe en double sous le même nom | Deux modules distincts, deux périmètres distincts (extraction Kaggle vs chargement Snowflake) — piège identifié pour Phase 5 | Consolider ou renommer lors de l'externalisation YAML en Phase 5 |

## Logging

| Emplacement | Element | Raison du report | A faire |
|---|---|---|---|
| Tous les modules `pipelines/transformers/` et `scripts/` | `print()` utilisé partout | Priorité donnée à la livraison de la couche Silver | Migrer vers `logging` Python standard dans une branche dédiée `refactor/logging` avant Phase 5 — Airflow capture `logging` nativement, les `print()` seront invisibles une fois orchestré |

## Bugs connus / contournements manuels

| Emplacement | Element | Note |
|---|---|---|
| `pipelines/loaders/snowflake_flatteners.py` | 2 commentaires obsolètes (lignes ~310, ~389) | Vestige d'une version antérieure — à nettoyer dans `refactor/logging` ou une branche dédiée |

## Fonctions non utilisées dans le flux principal

| Emplacement | Element | Note |
|---|---|---|
| `pipelines/extractors/api_weather/extract.py` | `extract_all_leagues` | Existe mais plus appelée par `extract_and_save_season()` — utile tests/debug uniquement |
| `pipelines/loaders/s3_loader.py` | `upload_kaggle_source` | Existe mais non appelée par `run_pipeline()` — upload one-shot manuel du fichier source Kaggle (gros fichier, cas particulier) |

## Mutation d'argument (non bloquant)

| Emplacement | Element | Note |
|---|---|---|
| `pipelines/loaders/snowflake_flatteners.py` | `flatten_standings()` | Modifie les dicts `team_entry` du JSON source en place (ajout de clés `_league_id`, etc.) plutôt que de travailler sur une copie. Sans conséquence pratique actuellement (`raw_json` rechargé frais depuis S3 à chaque appel de `load_table()`), mais fragile si `raw_json` était réutilisé après l'appel. À corriger si besoin (créer un nouveau dict plutôt que muter `team_entry`) |

## Scalabilité (non bloquant en Phase 1)

| Sujet | Note |
|---|---|
| Parallélisme absent | Contre-productif avec 100 req/jour API-Football en plan gratuit |
| Cache distribué absent | Pertinent seulement en multi-machines |
| Batching Open-Meteo | Optimisation possible Phase 6+ |
| Flatten de MATCH lent (~15-20 min) | Vectorisation potentielle non traitée — sans impact sur la correction des données, à optimiser si les volumes augmentent |

## Résolu

| Date | Emplacement | Problème | Résolution |
|---|---|---|---|
| 03/07/2026 | `scripts/generate_stadiums_seed.py` | Nominatim retournait Southampton, Massachusetts au lieu de Southampton, UK (homonymie) | Ajout de `MANUAL_COORDINATES_OVERRIDES`, dict de coordonnées connues vérifié avant tout appel Nominatim. Validé en conditions réelles (re-géocodage forcé de Southampton) |
| 03/07/2026 | `dbt/seeds/stadiums.csv` | 7 lignes corrompues (Bournemouth, Brentford, Brighton, Leeds, Leicester, Nottingham Forest, Wolves) issues d'un bug de quoting CSV lors du commit `74f7057` — doublons de chaque ligne encapsulés entièrement entre guillemets | Lignes supprimées après vérification qu'aucun code ne les référençait |
| 03/07/2026 | `dbt/seeds/stadiums.csv` | Ligne orpheline `Southampton FC` — vestige d'une correction manuelle antérieure sous un nom incorrect | Ligne supprimée |
| 03/07/2026 | `scripts/generate_stadiums_seed.py` | Bug d'indentation dans la boucle de géocodage : `df.at[idx, "latitude"/"longitude"]` placés hors de la boucle `for`, donc exécutés une seule fois après la boucle | Corrigé — les deux lignes réindentées à l'intérieur de la boucle |
| 03/07/2026 | `pipelines/extractors/api_football/extract.py` | Fichiers `bundesliga_2022_top_assists.json` et `bundesliga_2022_top_scorers.json` vides (298 octets) — rate limit API-Football (10 req/min) dépassé lors de l'extraction initiale | Nouvelle fonction `_is_valid_content()` : détecte une réponse vide et re-télécharge automatiquement. Fichiers re-extraits et valides (48 Ko chacun) |
| 03/07/2026 | `pipelines/extractors/api_weather/extract.py` | `extract_and_save_season` lisait `OUTPUT_DIR` global plutôt qu'un paramètre injecté — tests obligés de patcher le module global | `output_dir` devient un paramètre explicite avec `OUTPUT_DIR` en valeur par défaut — comportement production inchangé, tests simplifiés |
| 04-06/07/2026 | `pipelines/loaders/snowflake_loader.py` | `RAW.MATCH` : cotes de paris déclarées `NUMBER` sans précision (`NUMBER(38,0)`, zéro décimale) — perte de précision silencieuse sur des cotes décimales (ex. 1.29 → 1) | `09_raw_match.sql` corrigé en `NUMBER(10,2)` pour les 30 colonnes de cotes, table `DROP` + recréée, rechargement complet validé |
| 04-06/07/2026 | `pipelines/loaders/snowflake_flatteners.py` | `flatten_match()` : colonne `date` en `datetime64[ns]` pandas fait planter la lecture via SnowSQL (`Python int too large to convert to C int`) | `date` convertie en string ISO (`strftime("%Y-%m-%d %H:%M:%S")`) avant écriture — Snowflake caste proprement en `TIMESTAMP_NTZ` au MERGE |
| 04-06/07/2026 | `pipelines/loaders/snowflake_loader.py` | `read_multi_json_from_s3()` supposait que tous les fichiers multi-sources étaient des wrappers API-Football (`{"response": [...]}`) — cassait sur `api_weather` (liste JSON directe sans wrapper) | Détection du format à la lecture de chaque fichier (`isinstance(file_content, dict)`) |
| 12/07/2026 | `pipelines/loaders/snowflake_flatteners.py` | `RAW.TEAM_ATTRIBUTES.date` corrompue depuis le premier chargement — `write_pandas` corrompt silencieusement les colonnes `datetime64` via Arrow → Parquet → Snowflake (bug documenté du connecteur). Corruption invisible jusqu'à la première lecture de cette colonne | `date` transportée en STRING via `strftime("%Y-%m-%d %H:%M:%S")` dans `flatten_team_attributes`, conversion `TIMESTAMP_NTZ` déléguée au MERGE SQL. `STAGING.TEAM_ATTRIBUTES.date` passée en STRING. `RAW.TEAM_ATTRIBUTES` vidée (`TRUNCATE`) puis rechargée — nécessaire car le MERGE ne peut pas réconcilier d'anciennes clés corrompues avec de nouvelles clés propres. **Règle généralisée : ne jamais laisser `write_pandas` gérer une colonne `datetime64` — toujours transporter en STRING, conversion déléguée au MERGE SQL ou à Gold (dbt)** |
| 12/07/2026 | `pipelines/loaders/snowflake_flatteners.py` | Doublon réel masqué dans `RAW.TEAM_ATTRIBUTES` (team_api_id=9996, date=2015-09-10, lignes id=860 et 861 identiques en tout point) — rendu invisible par le bug de précision des timestamps qui leur donnait des résidus légèrement différents | Dédoublonnage ajouté dans `flatten_team_attributes` via `.drop_duplicates(subset=["team_api_id", "date"], keep="first")` avant écriture |
| 13/07/2026 | `pipelines/quality.py` | `get_duplicate_count` avec clé composite utilisait `COUNT(DISTINCT (col1, col2, col3))` — syntaxe ROW multi-colonnes non supportée par Snowflake (`Invalid argument types for function COUNT`) | Remplacé par sous-requête `SELECT COUNT(*) - COUNT(*) FROM (SELECT DISTINCT ...)` — fonctionne en clé simple et composite, un seul chemin de code |
| 13/07/2026 | `pipelines/transformers/silver_standings.py` | `SILVER.STANDINGS.LAST_UPDATE` (TIMESTAMP_TZ, tz-aware) corrompue par `write_pandas` — même cause que `TEAM_ATTRIBUTES.date`, confirmée par le warning `use_logical_type=None` et l'erreur `Python int too large` à la lecture | `LAST_UPDATE` passée en STRING dans Silver (`dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%SZ")`), conversion `TIMESTAMP_TZ` déléguée à Gold (dbt). Règle étendue : s'applique aussi aux colonnes TIMESTAMP_TZ (tz-aware), pas seulement TIMESTAMP_NTZ |

---
*Dernière mise à jour : 13/07/2026*