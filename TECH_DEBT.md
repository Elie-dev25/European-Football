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

| Emplacement | Probleme | Contournement actuel | A faire |
|---|---|---|---|
| `scripts/generate_stadiums_seed.py` | Nominatim retourne Southampton, Massachusetts au lieu de UK | Correction manuelle des coordonnees apres chaque re-run | Liste blanche de coordonnees manuelles |

## Fonctions non utilisees dans le flux principal

| Emplacement | Element | Note |
|---|---|---|
| `pipelines/extractors/api_weather/extract.py` | `extract_all_leagues` | Existe mais plus appelee par `extract_and_save_season()` - utile tests/debug uniquement | 
| `pipelines/loaders/s3_loader.py` | `upload_kaggle_source` | Existe mais non appelee par `run_pipeline()` - upload one-shot manuel du fichier source Kaggle (gros fichier, cas particulier) |

## Limitations de testabilite

| Emplacement | Probleme | Impact | A faire |
|---|---|---|---|
| `pipelines/extractors/api_weather/extract.py` | `extract_and_save_season` lit `OUTPUT_DIR` global plutot qu'un parametre injecte | Fonctionne bien, mais moins testable sans patcher le module global | Pas urgent |

## Scalabilite (non bloquant en Phase 1)

| Sujet | Note |
|---|---|
| Parallelisme absent | Contre-productif avec 100 req/jour API-Football en plan gratuit |
| Cache distribue absent | Pertinent seulement en multi-machines |
| Batching Open-Meteo | Optimisation possible Phase 6+ | 



---
*Derniere mise a jour : 30/06/2026*