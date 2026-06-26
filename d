[33mcommit 0eb572a9221fd474ec9e968728d163fec808281f[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mdevelop[m[33m, [m[1;31morigin/develop[m[33m)[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Fri Jun 26 15:49:44 2026 +0100

    fix: supprime les doublons de tests dans test_api_football.py

[33mcommit 1604bdb9c0ea20fe2e4b22a77eac3242481c99e7[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Thu Jun 25 23:56:15 2026 +0100

    Add unit tests for utils, api_football and api_weather (mocked, no real API calls)

[33mcommit cb622d48b6b5a02bffaa1da57d5787dac4cead3e[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Thu Jun 25 22:28:51 2026 +0100

    refactor(api-football): use shared utils for normalize, build_filepath, load_leagues

[33mcommit 74f7057cf9ab7cdbd34d375dc536f8a50e99cb96[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Thu Jun 25 22:12:00 2026 +0100

    fix(weather): retry on ConnectionError, add missing PL teams to stadiums seed

[33mcommit 9593f2f5d00e971fe770f30bc6b5c04e858cf8cc[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Thu Jun 25 17:43:54 2026 +0100

    chore: ignore VS Code venv auto-activation file

[33mcommit 4c6ccc8619938bc134cae20eeb327130b0c37111[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Thu Jun 25 17:35:11 2026 +0100

    feat(weather): add Open-Meteo ingestion pipeline and shared utils
    
    - pipelines/api_weather/extract.py : pipeline complet (chargement fixtures,
      appel Open-Meteo, reshape horaire, idempotence, orchestration, gestion d'erreurs)
    - pipelines/utils.py : utilitaires partagés entre pipelines
      (normalize_league_name, build_filepath, load_leagues, load_stadiums)

[33mcommit feacbbbb20631c8e719309f45f2a1463f652fca8[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Sat Jun 20 21:19:29 2026 +0100

    couche d'accès aux données pour Open-Meteo: Les premières fonctions

[33mcommit f8b562a8565b25c307a069c10bc63458b06ddd9b[m
Merge: cafc5d3 d84441c
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Sat Jun 20 04:42:23 2026 +0100

    merge: resolve conflict — keep improved api_football extract.py from develop

[33mcommit d84441c0139f1413224432994a096444e2f1a43f[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Sat Jun 20 04:27:50 2026 +0100

    improve(api-football): lecture leagues.csv + idempotence + logging + gestion erreurs réseau

[33mcommit 408e5fb06c940fb94160296ef34f71d7388d50c6[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Sat Jun 20 04:04:35 2026 +0100

    ajouter le fichier stadiums.csv

[33mcommit cafc5d31b6666d32c63cc4bac1a8621eb1547c45[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Fri Jun 19 23:27:05 2026 +0100

    feat: ajouter pipeline météo et géocodage des stades
    
    - Implémenter module d'extraction API météo avec Open-Meteo
    - Ajouter générateur de seed stades avec géocodage Nominatim
    - Mettre à jour README avec documentation architecture complète

[33mcommit c8486b95d69487461faf6eba97df020342c51403[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Fri Jun 19 03:40:10 2026 +0100

    refactor: remplace print() par logging structuré + gestion erreurs réseau

[33mcommit 10c6494ff99d1d592eedb283a1529b5060478a24[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Fri Jun 19 02:37:42 2026 +0100

    refactor: Refactoriser les 4 fonctions API + ajouter orchestration
    
    - Refactoriser get_standings, get_fixtures, get_top_scorers, get_top_assists
      via fonction interne _call_api() (DRY + retry automatique 429)
    - Ajouter orchestration : extract_league_data, extract_all_leagues
    - Ajouter sauvegarde : save_raw_data, extract_and_save_season, run_pipeline

[33mcommit 08dcbbfbd6c9e19e6ac14ac87e84850f723c201f[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Fri Jun 19 01:02:16 2026 +0100

    Implémenter les 4 fonctions principales d'extraction (separer)
    
    - get_standings: classements par ligue/saison
    - get_fixtures: matchs par ligue/saison
    - get_top_scorers: meilleurs buteurs
    - get_top_assists: meilleurs passeurs

[33mcommit 758fc2c6f938f5a24a18ba3039abe34c88706bb5[m[33m ([m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m, [m[1;32mmain[m[33m)[m
Author: Elie-dev25 <elienjinedev@gmail.com>
Date:   Tue Jun 16 23:25:48 2026 +0100

    chore: initial project structure and documentation

[33mcommit 4f0bb2349cd07cac024f8116c47a9c6d3ce7a2d4[m
Author: NJINE TIENCHEU Elie <elienjinedev@gmail.com>
Date:   Tue Jun 16 22:51:08 2026 +0100

    Initial commit
