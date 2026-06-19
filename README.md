# 🏆 European Football Analytics Platform

An end-to-end data engineering pipeline — currently under active development — that will collect,
transform, and analyze football statistics from the 5 major European leagues using a modern,
production-grade data stack.

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)
![Phase](https://img.shields.io/badge/Phase-1%20%E2%80%94%20Ingestion-blue)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Airflow](https://img.shields.io/badge/Airflow-2.0+-green)
![dbt](https://img.shields.io/badge/dbt-1.0+-orange)
![Docker](https://img.shields.io/badge/Docker-planned-lightgrey)
![Snowflake](https://img.shields.io/badge/Snowflake-❄️-lightblue)

> 🚧 **This project is actively being built.** Every phase is documented as it is completed.
> The architecture and decisions below reflect the full target state — not the current state.
> See [Current Status](#-current-status) for exactly where things stand today.

---

## 📋 Description

This project builds a **production-grade data pipeline** covering the 5 major European football leagues:

- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League** (England)
- 🇪🇸 **La Liga** (Spain)
- 🇮🇹 **Serie A** (Italy)
- 🇩🇪 **Bundesliga** (Germany)
- 🇫🇷 **Ligue 1** (France)

**Why this project?**
- **Multi-source ingestion** — demonstrates the ability to handle real-world data complexity
- **Modern stack** — tools used in production at data-driven companies in 2025-2026
- **Concrete domain** — football is universally understood, making it easy for any recruiter to evaluate the analytical output

---

## 🚧 Current Status

> Last updated: June 2026

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Ingestion — API-Football | ✅ Done |
| **Phase 1** | Ingestion — Open-Meteo (weather) | 🔄 In progress |
| **Phase 1** | Ingestion — Kaggle SQLite (historical) | ⬜ Not started |
| **Phase 2** | AWS S3 — Bronze layer upload | ⬜ Not started |
| **Phase 3** | Snowflake — Silver layer | ⬜ Not started |
| **Phase 4** | dbt — Gold layer transformations | ⬜ Not started |
| **Phase 5** | Apache Airflow — Orchestration | ⬜ Not started |
| **Phase 6** | Docker — Containerization | ⬜ Not started |
| **Phase 7** | Tests (pytest) + Final documentation | ⬜ Not started |

**What works today:**
- Full extraction pipeline for API-Football: standings, fixtures, top scorers, top assists
- Covers all 5 leagues for season 2022 (extensible to 2023–2024 with one config change)
- Automatic retry on rate-limit errors (429), structured logging compatible with Airflow
- Raw data saved locally as JSON files under `data/raw/api_football/`

**What does not work yet:**
- Weather ingestion (in progress)
- No S3 upload yet — data stays local
- No Snowflake, dbt, Airflow, or Docker setup yet
- `docker-compose up` in the Getting Started section will not work until Phase 6

---

## 🗄️ Data Sources

| Source | Type | Data | Period | Why |
|--------|------|------|--------|-----|
| [API-Football](https://api-football.com) | REST API | Standings, fixtures, top scorers, top assists | 2022–2024 | Structured, recent football data |
| [Open-Meteo](https://open-meteo.com) | REST API | Weather at stadium cities at match time | 2022–2024 | Free, open-source, historical data back to 1940 — no API key required |
| [Kaggle Soccer DB](https://www.kaggle.com) | SQLite file | Historical match and player data | 2008–2016 | Fills the historical gap not covered by the API-Football free tier |
| [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org) | REST API | GPS coordinates of stadiums | One-shot | Free geocoding API used to generate `dbt/seeds/stadiums.csv` — no API key required |

**Why 4 separate sources?**
In real data engineering environments, data never comes from a single place. Managing multiple heterogeneous sources — APIs, files, databases — is a core skill this project intentionally demonstrates.

**Note on weather source:** OpenWeather was initially planned but its free tier does not include historical data access. Open-Meteo was selected as a replacement — it provides free historical weather data globally since 1940, is fully open-source, and requires no API key for non-commercial use.

---

## 🏗️ Target Architecture

```mermaid
flowchart TD
    subgraph Sources["📦 Data Sources"]
        A[🔌 API-Football\nMatch results · Standings · Stats]
        B[🌤️ Open-Meteo API\nHistorical weather conditions]
        C[📂 Kaggle SQLite\nHistorical data 2008–2016]
    end

    subgraph Ingestion["⚙️ Ingestion Layer"]
        D[Python · Pandas · requests]
    end

    subgraph Storage["🗄️ Storage Layer"]
        E[(🪣 AWS S3\nBronze — Raw Data)]
        F[(❄️ Snowflake\nSilver — Cleaned Data)]
    end

    subgraph Transformation["🔄 Transformation Layer"]
        G[dbt\nGold — Analytics Tables]
    end

    subgraph Orchestration["🎯 Orchestration"]
        H[Apache Airflow\nScheduling · Monitoring]
    end

    subgraph Insights["📈 Insights"]
        I[Home vs Away rates]
        J[Goals per league]
        K[Weather impact on results]
        L[Top scorers & assists]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F --> G
    G --> I
    G --> J
    G --> K
    G --> L
    H -.->|orchestrates| D
    H -.->|orchestrates| G

    style Sources fill:#1a1a2e,color:#fff
    style Ingestion fill:#16213e,color:#fff
    style Storage fill:#0f3460,color:#fff
    style Transformation fill:#533483,color:#fff
    style Orchestration fill:#e94560,color:#fff
    style Insights fill:#2d6a4f,color:#fff
```

---

## 🥉🥈🥇 Medallion Architecture

```mermaid
flowchart LR
    subgraph Bronze["🥉 Bronze Layer — AWS S3"]
        B1[raw_standings.json]
        B2[raw_fixtures.json]
        B3[raw_scorers.json]
        B4[raw_weather.json]
        B5[historical_data.sqlite]
    end

    subgraph Silver["🥈 Silver Layer — Snowflake"]
        S1[matches_cleaned]
        S2[standings_cleaned]
        S3[players_cleaned]
        S4[weather_cleaned]
    end

    subgraph Gold["🥇 Gold Layer — dbt"]
        G1[mart_league_performance]
        G2[mart_team_stats]
        G3[mart_player_rankings]
        G4[mart_weather_impact]
    end

    B1 --> S2
    B2 --> S1
    B3 --> S3
    B4 --> S4
    B5 --> S1

    S1 --> G1
    S1 --> G2
    S2 --> G1
    S3 --> G3
    S4 --> G4
    S1 --> G4

    style Bronze fill:#cd7f32,color:#fff
    style Silver fill:#c0c0c0,color:#000
    style Gold fill:#ffd700,color:#000
```

**Why Medallion?**
- **Bronze** — raw data preserved as-is, always recoverable
- **Silver** — cleaned and structured, ready for analysis
- **Gold** — analytics-ready tables, directly usable for insights and dashboards
- Industry standard: separates concerns, allows reprocessing at any stage without rebuilding everything

---

## 🔄 Target Pipeline Flow

```mermaid
sequenceDiagram
    participant AF as Airflow
    participant PY as Python
    participant S3 as AWS S3
    participant SF as Snowflake
    participant DBT as dbt

    AF->>PY: Trigger ingestion
    PY->>PY: Extract from APIs & SQLite
    PY->>S3: Store raw data (Bronze)
    AF->>SF: Trigger loading
    S3->>SF: Load to Silver tables
    AF->>DBT: Trigger transformations
    DBT->>SF: Build Gold marts
    DBT->>DBT: Run data quality tests
    AF->>AF: Log & monitor pipeline
```

---

## 📁 Project Structure

```
European-Football/
│
├── pipelines/
│   ├── api_football/
│   │   └── extract.py          ✅ Done — standings, fixtures, scorers, assists
│   ├── api_weather/
│   │   └── extract.py          🔄 In progress — Open-Meteo historical weather
│   └── kaggle/
│       └── extract.py          ⬜ Not started — SQLite extraction
│
├── scripts/
│   └── generate_stadiums_seed.py  ✅ Done — geocodes stadiums via Nominatim → stadiums.csv
│
├── dags/
│   └── football_pipeline.py    ⬜ Not started — Airflow DAG
│
├── dbt/
│   ├── seeds/
│   │   └── stadiums.csv        ✅ Done — 99 stadiums with GPS coordinates (dbt seed, Phase 4)
│   └── models/
│       ├── staging/            ⬜ Not started
│       ├── intermediate/       ⬜ Not started
│       └── marts/              ⬜ Not started
│
├── docker/
│   ├── Dockerfile              ⬜ Not started
│   └── docker-compose.yml      ⬜ Not started
│
├── tests/
│   └── ...                     ⬜ Not started — pytest with mocks
│
├── configs/
├── data/
│   └── raw/
│       └── api_football/       ✅ Local JSON files (pre-S3 upload)
│
├── requirements.txt
├── .env
└── README.md
```

---

## 🛠️ Tech Stack

| Tool | Purpose | Status |
|------|---------|--------|
| **Python 3.8+** | Data ingestion & transformation | ✅ In use |
| **requests** | HTTP calls to REST APIs | ✅ In use |
| **Pandas** | Data manipulation | ✅ In use |
| **AWS S3** | Raw data storage — Bronze layer | ⬜ Phase 2 |
| **Snowflake** | Data Warehouse — Silver layer | ⬜ Phase 3 |
| **dbt** | Data transformations — Gold layer | ⬜ Phase 4 |
| **Apache Airflow** | Pipeline orchestration & scheduling | ⬜ Phase 5 |
| **Docker** | Containerization & reproducibility | ⬜ Phase 6 |
| **pytest** | Unit testing with mocks | ⬜ Phase 7 |

---

## 📐 Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| `SEASONS = [2022]` in Phase 1 | Validate the architecture on one season first; extend to `[2022, 2023, 2024]` after — the code already supports it with a single config change |
| One function per API endpoint | Single Responsibility Principle — each function is independently readable and testable |
| Generic `_call_api()` internal function | DRY principle — all HTTP logic (retry, timeout, error handling) centralized in one place |
| Local JSON save before S3 upload | Never lose already-fetched data if a later step fails — save immediately after each extraction |
| `logging` instead of `print()` | Airflow captures Python `logging` natively — using `print()` would make logs invisible once orchestrated |
| Docker in Phase 6, not Phase 1 | Validate the code locally first, containerize once it works — avoids debugging two layers at once |
| Open-Meteo instead of OpenWeather | OpenWeather free tier has no historical data access. Open-Meteo provides free historical weather since 1940, open-source, no API key required |
| Stadium coordinates as a dbt seed | GPS coordinates are reference data, not operational data — they belong in `dbt/seeds/stadiums.csv`, versioned in Git and loaded into Snowflake via `dbt seed`. Generated once via `scripts/generate_stadiums_seed.py` using Nominatim, updated only when new teams appear |

---

## 📊 Planned Analytics Insights

```mermaid
mindmap
  root((⚽ Insights))
    🏠 Team Performance
      Home vs Away win rates
      Goals scored per league
      Performance trends across seasons
    👟 Player Rankings
      Top scorers per league
      Top assisters per league
      Player consistency over seasons
    🌧️ Weather Impact
      Rain vs Clear conditions
      Temperature effect on goals scored
      Match outcomes by weather type
    📊 League Analysis
      Most competitive league
      Average goals per match
      Season-over-season comparisons
```

---

## 🚀 Getting Started

> ⚠️ **The project is in Phase 1.** Only local ingestion is functional at this stage.
> Docker, Airflow, and Snowflake setup are planned for later phases.

### Prerequisites

- Python 3.8+
- API-Football account (free tier — 100 requests/day)
- AWS account (for Phase 2)
- Snowflake account (for Phase 3)

### Installation

```bash
# Clone the repository
git clone https://github.com/Elie-dev25/European-Football.git
cd European-Football

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Run the ingestion (Phase 1 — current)

```bash
# Extract data from API-Football for season 2022
python pipelines/api_football/extract.py
```

Raw data will be saved to `data/raw/api_football/` as JSON files.

```bash
# Generate the stadiums reference seed (one-shot, run once per new season)
# Reads fixtures JSON → geocodes stadiums via Nominatim → saves dbt/seeds/stadiums.csv
python scripts/generate_stadiums_seed.py
```

---

## 👤 Author

**NJINE TIENCHEU Elie**
Software & Data Engineer

[![GitHub](https://img.shields.io/badge/GitHub-Elie--dev25-181717?style=flat&logo=github)](https://github.com/Elie-dev25)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Elie%20NJINE-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/elie-njine-736b04274)
[![Portfolio](https://img.shields.io/badge/Portfolio-elie--njine.online-FF5733?style=flat&logo=google-chrome)](https://elie-njine.online)
[![Email](https://img.shields.io/badge/Email-contact@elie--njine.online-D14836?style=flat&logo=gmail)](mailto:contact@elie-njine.online)

---

*🚧 Project actively in progress — Star ⭐ this repo to follow the build!*