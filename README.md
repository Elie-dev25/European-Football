# 🏆 European Football Analytics Platform 

> **🚧 UNDER ACTIVE DEVELOPMENT ON BRANCH `develop` 🚧** 

An end-to-end data engineering pipeline that collects, transforms, and analyzes
football data from the 5 major European leagues using a modern data stack.

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Airflow](https://img.shields.io/badge/Airflow-2.0+-green)
![dbt](https://img.shields.io/badge/dbt-1.0+-orange)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
![Snowflake](https://img.shields.io/badge/Snowflake-❄️-lightblue)

---

## 📋 Description

This project builds a production-grade data pipeline covering the 5 major
European football leagues:

- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League** (England)
- 🇪🇸 **La Liga** (Spain)
- 🇮🇹 **Serie A** (Italy)
- 🇩🇪 **Bundesliga** (Germany)
- 🇫🇷 **Ligue 1** (France)

---

## 🏗️ Global Architecture

```mermaid
flowchart TD
    subgraph Sources["📦 Data Sources"]
        A[🔌 API-Football\nMatch results · Standings · Stats]
        B[🌤️ OpenWeather API\nWeather conditions]
        C[📂 Kaggle CSV\nHistorical data]
    end

    subgraph Ingestion["⚙️ Ingestion Layer"]
        D[Python · Pandas · requests]
    end

    subgraph Storage["🗄️ Storage Layer"]
        E[(🪣 AWS S3\nBronze - Raw Data)]
        F[(❄️ Snowflake\nSilver - Cleaned Data)]
    end

    subgraph Transformation["🔄 Transformation Layer"]
        G[dbt\nGold - Analytics Tables]
    end

    subgraph Orchestration["🎯 Orchestration"]
        H[Apache Airflow\nScheduling · Monitoring]
    end

    subgraph Insights["📈 Insights"]
        I[Home vs Away rates]
        J[Goals per league]
        K[Weather impact]
        L[Top scorers]
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
    subgraph Bronze["🥉 Bronze Layer - AWS S3"]
        B1[raw_matches.json]
        B2[raw_standings.json]
        B3[raw_players.json]
        B4[raw_weather.json]
        B5[raw_history.csv]
    end

    subgraph Silver["🥈 Silver Layer - Snowflake"]
        S1[matches_cleaned]
        S2[standings_cleaned]
        S3[players_cleaned]
        S4[weather_cleaned]
    end

    subgraph Gold["🥇 Gold Layer - dbt"]
        G1[mart_league_performance]
        G2[mart_team_stats]
        G3[mart_player_rankings]
        G4[mart_weather_impact]
    end

    B1 --> S1
    B2 --> S2
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

---

## 🔄 Pipeline Flow

```mermaid
sequenceDiagram
    participant AF as Airflow
    participant PY as Python
    participant S3 as AWS S3
    participant SF as Snowflake
    participant DBT as dbt

    AF->>PY: Trigger ingestion
    PY->>PY: Extract from APIs & CSV
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

```mermaid
graph TD
    Root[🏆 European-Football/]

    Root --> P[📁 pipelines/]
    Root --> D[📁 dags/]
    Root --> DBT[📁 dbt/]
    Root --> DOC[📁 docker/]
    Root --> T[📁 tests/]
    Root --> C[📁 configs/]
    Root --> L[📁 logs/]

    P --> P1[📁 api_football/]
    P --> P2[📁 api_weather/]
    P --> P3[📁 kaggle/]

    P1 --> P1A[extract.py]
    P2 --> P2A[extract.py]
    P3 --> P3A[extract.py]

    DBT --> M[📁 models/]
    M --> M1[📁 staging/]
    M --> M2[📁 intermediate/]
    M --> M3[📁 marts/]

    D --> D1[football_pipeline.py]
    DOC --> DOC1[Dockerfile]
    DOC --> DOC2[docker-compose.yml]

    style Root fill:#1a1a2e,color:#fff
    style P fill:#16213e,color:#fff
    style DBT fill:#533483,color:#fff
    style D fill:#e94560,color:#fff
    style T fill:#2d6a4f,color:#fff
```

---

## 🛠️ Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| ![Python](https://img.shields.io/badge/Python-3.8+-blue) | 3.8+ | Data ingestion & transformation |
| ![Airflow](https://img.shields.io/badge/Airflow-2.0+-green) | 2.0+ | Pipeline orchestration |
| ![AWS S3](https://img.shields.io/badge/AWS-S3-orange) | - | Raw data storage (Bronze) |
| ![Snowflake](https://img.shields.io/badge/Snowflake-❄️-lightblue) | - | Data Warehouse (Silver) |
| ![dbt](https://img.shields.io/badge/dbt-1.0+-orange) | 1.0+ | Data transformation (Gold) |
| ![Docker](https://img.shields.io/badge/Docker-ready-blue) | - | Containerization |
| ![pytest](https://img.shields.io/badge/pytest-✅-green) | - | Unit testing |

---

## 📊 Data Sources

| Source | Type | Data |
|--------|------|------|
| [API-Football](https://api-football.com) | REST API | Match results, standings, player stats |
| [OpenWeather](https://openweathermap.org) | REST API | Weather conditions at match locations |
| [Kaggle](https://kaggle.com) | CSV | Historical football data |

---

## 📈 Analytics Insights

```mermaid
mindmap
  root((⚽ Insights))
    🏠 Team Performance
      Home vs Away win rates
      Goals scored per league
      Performance trends
    👟 Player Rankings
      Top scorers per league
      Top assisters per league
      Player consistency
    🌧️ Weather Impact
      Rain vs Clear conditions
      Temperature effect
      Match outcomes by weather
    📊 League Analysis
      Most competitive league
      Average goals per match
      Season comparisons
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker Desktop
- AWS Account (Free Tier)
- Snowflake Account

### Installation

```bash
# Clone the repository
git clone https://github.com/ton-username/European-Football.git
cd European-Football

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and credentials

# Start with Docker
docker-compose up -d
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

*🚧 Project currently in progress — Star ⭐ this repo to follow the progress!*
