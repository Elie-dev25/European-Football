import pandas as pd
from pipelines.utils import get_snowflake_connection

# Familles de codes météo WMO (Open-Meteo), utilisées pour dériver
# des indicateurs booléens simples par match. Référence : documentation
# Open-Meteo (variable weathercode, standard WMO 4677).
WEATHER_CODES_RAIN = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}
WEATHER_CODES_SNOW = {71, 73, 75, 77, 85, 86}
WEATHER_CODES_FOG = {45, 48}
WEATHER_CODES_STORM = {95, 96, 99}


def filter_weather_window(weather_df: pd.DataFrame, duration_minutes: int = 135) -> pd.DataFrame:
    """
    Filtre les mesures météo horaires pour ne garder que celles comprises
    entre le coup d'envoi (kickoff) et kickoff + duration_minutes.

    kickoff est en TIMESTAMP_TZ (avec fuseau) ; weather_time est en UTC naïf
    (confirmé : l'appel Open-Meteo utilise timezone="UTC"). On convertit donc
    kickoff en UTC puis on le rend naïf pour pouvoir comparer les deux
    colonnes directement.
    """
    df = weather_df.copy()

    kickoff_utc_naive = (
        df["kickoff"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .astype("datetime64[ns]")
    )
    window_end = kickoff_utc_naive + pd.to_timedelta(duration_minutes, unit="m")

    mask = (df["weather_time"] >= kickoff_utc_naive) & (df["weather_time"] <= window_end)

    return df.loc[mask].reset_index(drop=True)


def aggregate_weather_by_match(filtered_df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrège les mesures météo horaires filtrées en une ligne par match.

    Grain en entrée : une ligne par (fixture_id, weather_time).
    Grain en sortie : une ligne par fixture_id.

    Version vectorisée (pas de .apply() par groupe) pour rester performant
    sur un volume de ~88k lignes.
    """
    df = filtered_df.copy()

    # Colonnes booléennes précalculées ligne par ligne (vectorisé)
    df["_is_rain"] = df["weathercode"].isin(WEATHER_CODES_RAIN)
    df["_is_snow"] = df["weathercode"].isin(WEATHER_CODES_SNOW)
    df["_is_fog"] = df["weathercode"].isin(WEATHER_CODES_FOG)
    df["_is_storm"] = df["weathercode"].isin(WEATHER_CODES_STORM)

    result = df.groupby("fixture_id").agg(
        temperature_avg=("temperature_2m", "mean"),
        windspeed_avg=("windspeed_10m", "mean"),
        precipitation_total=("precipitation", "sum"),
        has_rain=("_is_rain", "any"),
        has_snow=("_is_snow", "any"),
        has_fog=("_is_fog", "any"),
        has_storm=("_is_storm", "any"),
    ).reset_index()

    return result


def fetch_raw_weather(conn) -> pd.DataFrame:
    """Récupère toutes les lignes météo horaires depuis RAW.WEATHER."""
    query = """
        SELECT fixture_id, kickoff, team_home, weather_time,
               temperature_2m, precipitation, windspeed_10m, weathercode
        FROM FOOTBALL_DB.RAW.WEATHER;
    """
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def load_weather_match():
    """Point d'entrée : reconstruit entièrement SILVER.WEATHER_MATCH."""
    with get_snowflake_connection() as conn:
        raw_df = fetch_raw_weather(conn)
        filtered_df = filter_weather_window(raw_df)
        match_df = aggregate_weather_by_match(filtered_df)
        match_df.columns = match_df.columns.str.upper()

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE FOOTBALL_DB.SILVER.WEATHER_MATCH;")

        from snowflake.connector.pandas_tools import write_pandas
        write_pandas(
            conn,
            match_df,
            table_name="WEATHER_MATCH",
            database="FOOTBALL_DB",
            schema="SILVER",
        )

    print(f"WEATHER_MATCH rechargée : {len(match_df)} lignes")


if __name__ == "__main__":
    load_weather_match()