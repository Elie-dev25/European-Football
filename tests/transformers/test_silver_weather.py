import pandas as pd
import pytest
from pipelines.transformers.silver_weather import aggregate_weather_by_match, filter_weather_window 


def test_filter_weather_window_keeps_only_match_duration():
    kickoff = pd.Timestamp("2022-08-05 18:30:00", tz="UTC")

    weather_df = pd.DataFrame({
        "fixture_id": [1, 1, 1, 1, 1],
        "kickoff": [kickoff] * 5,
        "weather_time": [
            pd.Timestamp("2022-08-05 17:00:00"),  # avant kickoff — hors fenêtre
            pd.Timestamp("2022-08-05 18:00:00"),  # avant kickoff — hors fenêtre
            pd.Timestamp("2022-08-05 19:00:00"),  # dans la fenêtre (kickoff+30min)
            pd.Timestamp("2022-08-05 20:00:00"),  # dans la fenêtre (kickoff+90min, limite 135min)
            pd.Timestamp("2022-08-05 21:00:00"),  # après kickoff+135min — hors fenêtre
        ],
        "temperature_2m": [10.0, 11.0, 12.0, 13.0, 14.0],
    })

    result = filter_weather_window(weather_df)

    assert len(result) == 2
    assert result["weather_time"].tolist() == [
        pd.Timestamp("2022-08-05 19:00:00"),
        pd.Timestamp("2022-08-05 20:00:00"),
    ] 


def test_aggregate_weather_by_match_computes_correct_stats_and_flags():
    weather_df = pd.DataFrame({
        "fixture_id": [1, 1, 1, 2, 2],
        "weathercode": [61, 71, 0, 95, 0],
        "temperature_2m": [10.0, 8.0, 9.0, 20.0, 22.0],
        "precipitation": [2.0, 1.5, 0.0, 5.0, 0.0],
        "windspeed_10m": [15.0, 20.0, 10.0, 30.0, 25.0],
    })

    result = aggregate_weather_by_match(weather_df).set_index("fixture_id")

    assert result.loc[1, "has_rain"] == True
    assert result.loc[1, "has_snow"] == True
    assert result.loc[1, "has_fog"] == False
    assert result.loc[1, "has_storm"] == False
    assert result.loc[1, "temperature_avg"] == pytest.approx((10.0 + 8.0 + 9.0) / 3)
    assert result.loc[1, "precipitation_total"] == pytest.approx(3.5)

    assert result.loc[2, "has_rain"] == False
    assert result.loc[2, "has_snow"] == False
    assert result.loc[2, "has_storm"] == True