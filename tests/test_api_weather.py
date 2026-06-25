"""
Tests pour pipelines/api_weather/extract.py

Philosophie : aucun vrai appel HTTP. requests.get est systematiquement mocke.
time.sleep est mocke pour ne jamais ralentir la suite de tests.
"""

import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, Mock

from pipelines.api_weather.extract import (
    get_stadium_coords,
    _call_api,
    get_weather_for_day,
    reshape_hourly_data,
    load_fixtures,
    _file_exists,
    extract_weather_for_league,
    extract_all_leagues,
    save_raw_data,
    extract_and_save_season,
    run_pipeline,
)


def make_stadiums_df():
    return pd.DataFrame([
        {"team_name": "Arsenal", "stadium_name": "Emirates", "city": "London", "latitude": 51.5549, "longitude": -0.1084},
        {"team_name": "Real Madrid", "stadium_name": "Bernabeu", "city": "Madrid", "latitude": 40.4531, "longitude": -3.6883},
    ])


def make_fixture(fixture_id=1, team_home="Arsenal", kickoff="2022-08-06T15:00:00+00:00"):
    return {
        "fixture": {"id": fixture_id, "date": kickoff},
        "teams": {"home": {"name": team_home}, "away": {"name": "Chelsea"}},
    }


def make_weather_response(times=None):
    if times is None:
        times = ["2022-08-06T14:00", "2022-08-06T15:00"]
    n = len(times)
    return {
        "hourly": {
            "time": times,
            "temperature_2m": [18.2] * n,
            "precipitation": [0.0] * n,
            "windspeed_10m": [11.0] * n,
            "weathercode": [2] * n,
        }
    }


class TestGetStadiumCoords:

    def test_returns_coords_for_known_team(self):
        df = make_stadiums_df()
        lat, lon = get_stadium_coords("Arsenal", df)
        assert lat == 51.5549
        assert lon == -0.1084

    def test_returns_none_none_for_unknown_team(self):
        df = make_stadiums_df()
        lat, lon = get_stadium_coords("Unknown FC", df)
        assert lat is None
        assert lon is None


class TestCallApi:

    @patch("pipelines.api_weather.extract.requests.get")
    def test_success_200_returns_json(self, mock_get):
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"hourly": {"time": ["2022-08-06T14:00"]}}
        mock_get.return_value = mock_response

        result = _call_api({"latitude": 51.5, "longitude": -0.1})

        assert result == {"hourly": {"time": ["2022-08-06T14:00"]}}
        mock_get.assert_called_once()

    @patch("pipelines.api_weather.extract.requests.get")
    def test_http_error_returns_empty_dict_no_retry(self, mock_get):
        mock_response = Mock(status_code=400)
        mock_get.return_value = mock_response

        result = _call_api({"latitude": 51.5, "longitude": -0.1}, retries=8)

        assert result == {}
        mock_get.assert_called_once()

    @patch("pipelines.api_weather.extract.time.sleep")
    @patch("pipelines.api_weather.extract.requests.get")
    def test_timeout_then_success_uses_exponential_backoff(self, mock_get, mock_sleep):
        import requests
        success = Mock(status_code=200)
        success.json.return_value = {"hourly": {"time": []}}
        mock_get.side_effect = [requests.exceptions.Timeout(), success]

        result = _call_api({"latitude": 51.5, "longitude": -0.1}, retries=8)

        assert result == {"hourly": {"time": []}}
        # attempt=0 -> wait = 2**0 = 1
        mock_sleep.assert_called_once_with(1)
        assert mock_get.call_count == 2

    @patch("pipelines.api_weather.extract.time.sleep")
    @patch("pipelines.api_weather.extract.requests.get")
    def test_connection_error_retries_with_backoff(self, mock_get, mock_sleep):
        import requests
        success = Mock(status_code=200)
        success.json.return_value = {"hourly": {"time": []}}
        mock_get.side_effect = [requests.exceptions.ConnectionError(), requests.exceptions.ConnectionError(), success]

        result = _call_api({"latitude": 51.5, "longitude": -0.1}, retries=8)

        assert result == {"hourly": {"time": []}}
        assert mock_sleep.call_args_list[0].args == (1,)   # 2**0
        assert mock_sleep.call_args_list[1].args == (2,)   # 2**1
        assert mock_get.call_count == 3

    @patch("pipelines.api_weather.extract.time.sleep")
    @patch("pipelines.api_weather.extract.requests.get")
    def test_exhausts_all_retries_with_growing_backoff(self, mock_get, mock_sleep):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        result = _call_api({"latitude": 51.5, "longitude": -0.1}, retries=4)

        assert result == {}
        assert mock_get.call_count == 4
        waits = [c.args[0] for c in mock_sleep.call_args_list]
        assert waits == [1, 2, 4, 8]

    @patch("pipelines.api_weather.extract.requests.get")
    def test_generic_request_exception_returns_empty_dict(self, mock_get):
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("erreur reseau")

        result = _call_api({"latitude": 51.5, "longitude": -0.1})

        assert result == {}

    @patch("pipelines.api_weather.extract.requests.get")
    def test_no_api_key_header_sent(self, mock_get):
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        _call_api({"latitude": 51.5, "longitude": -0.1})

        called_kwargs = mock_get.call_args.kwargs
        assert "headers" not in called_kwargs


class TestGetWeatherForDay:

    @patch("pipelines.api_weather.extract._call_api")
    def test_builds_correct_params_with_one_day_window(self, mock_call_api):
        mock_call_api.return_value = {"hourly": {"time": []}}

        get_weather_for_day(51.5549, -0.1084, "2022-08-06")

        called_params = mock_call_api.call_args.args[0]
        assert called_params["latitude"] == 51.5549
        assert called_params["longitude"] == -0.1084
        assert called_params["start_date"] == "2022-08-06"
        assert called_params["end_date"] == "2022-08-07"
        assert called_params["timezone"] == "UTC"
        assert "temperature_2m" in called_params["hourly"]

    @patch("pipelines.api_weather.extract._call_api")
    def test_month_boundary_rollover(self, mock_call_api):
        mock_call_api.return_value = {"hourly": {"time": []}}

        get_weather_for_day(51.5, -0.1, "2022-08-31")

        called_params = mock_call_api.call_args.args[0]
        assert called_params["end_date"] == "2022-09-01"


class TestReshapeHourlyData:

    def test_reshapes_parallel_arrays_into_list_of_dicts(self):
        response = make_weather_response(["2022-08-06T14:00", "2022-08-06T15:00"])

        result = reshape_hourly_data(response)

        assert len(result) == 2
        assert result[0]["weather_time"] == "2022-08-06T14:00"
        assert result[0]["temperature_2m"] == 18.2
        assert result[0]["precipitation"] == 0.0
        assert result[0]["windspeed_10m"] == 11.0
        assert result[0]["weathercode"] == 2

    def test_empty_times_returns_empty_list(self):
        result = reshape_hourly_data({"hourly": {"time": []}})
        assert result == []

    def test_missing_hourly_key_returns_empty_list(self):
        result = reshape_hourly_data({})
        assert result == []

    def test_missing_variable_defaults_to_none(self):
        response = {"hourly": {"time": ["2022-08-06T14:00"]}}  # pas de temperature_2m etc.

        result = reshape_hourly_data(response)

        assert result[0]["temperature_2m"] is None
        assert result[0]["precipitation"] is None


class TestLoadFixtures:

    def test_loads_fixtures_from_existing_file(self, tmp_path):
        filepath = tmp_path / "premier_league_2022_fixtures.json"
        filepath.write_text(json.dumps({"response": [make_fixture()]}))

        result = load_fixtures("Premier League", 2022, tmp_path)

        assert len(result) == 1
        assert result[0]["fixture"]["id"] == 1

    def test_missing_file_returns_empty_list_non_blocking(self, tmp_path):
        result = load_fixtures("Premier League", 2022, tmp_path)
        assert result == []


class TestFileExists:

    def test_returns_true_when_weather_file_exists(self, tmp_path):
        filepath = tmp_path / "premier_league_2022_weather.json"
        filepath.write_text("[]")
        assert _file_exists("Premier League", 2022, tmp_path) is True

    def test_returns_false_when_missing(self, tmp_path):
        assert _file_exists("Premier League", 2022, tmp_path) is False


class TestExtractWeatherForLeague:

    @patch("pipelines.api_weather.extract.reshape_hourly_data")
    @patch("pipelines.api_weather.extract.get_weather_for_day")
    def test_happy_path_single_match(self, mock_get_weather, mock_reshape, tmp_path):
        fixtures_file = tmp_path / "premier_league_2022_fixtures.json"
        fixtures_file.write_text(json.dumps({"response": [make_fixture(team_home="Arsenal")]}))

        mock_get_weather.return_value = {"hourly": {"time": ["x"]}}
        mock_reshape.return_value = [{"weather_time": "x", "temperature_2m": 18.0}]

        df = make_stadiums_df()
        result = extract_weather_for_league("Premier League", 2022, df, tmp_path)

        assert len(result) == 1
        assert result[0]["fixture_id"] == 1
        assert result[0]["team_home"] == "Arsenal"
        assert result[0]["hourly_weather"] == [{"weather_time": "x", "temperature_2m": 18.0}]

    def test_no_fixtures_returns_empty_list(self, tmp_path):
        df = make_stadiums_df()
        result = extract_weather_for_league("Premier League", 2022, df, tmp_path)
        assert result == []

    def test_match_skipped_when_team_not_in_stadiums(self, tmp_path):
        fixtures_file = tmp_path / "premier_league_2022_fixtures.json"
        fixtures_file.write_text(json.dumps({"response": [make_fixture(team_home="Unknown FC")]}))

        df = make_stadiums_df()
        result = extract_weather_for_league("Premier League", 2022, df, tmp_path)

        assert result == []

    @patch("pipelines.api_weather.extract.get_weather_for_day")
    def test_match_skipped_when_no_weather_data(self, mock_get_weather, tmp_path):
        fixtures_file = tmp_path / "premier_league_2022_fixtures.json"
        fixtures_file.write_text(json.dumps({"response": [make_fixture(team_home="Arsenal")]}))

        mock_get_weather.return_value = {"hourly": {"time": []}}  # vide -> reshape donnera []

        df = make_stadiums_df()
        result = extract_weather_for_league("Premier League", 2022, df, tmp_path)

        assert result == []

    @patch("pipelines.api_weather.extract.reshape_hourly_data")
    @patch("pipelines.api_weather.extract.get_weather_for_day")
    def test_mixed_matches_some_skipped_some_kept(self, mock_get_weather, mock_reshape, tmp_path):
        fixtures_file = tmp_path / "premier_league_2022_fixtures.json"
        fixtures_file.write_text(json.dumps({"response": [
            make_fixture(fixture_id=1, team_home="Arsenal"),
            make_fixture(fixture_id=2, team_home="Unknown FC"),
        ]}))

        mock_get_weather.return_value = {"hourly": {"time": ["x"]}}
        mock_reshape.return_value = [{"weather_time": "x"}]

        df = make_stadiums_df()
        result = extract_weather_for_league("Premier League", 2022, df, tmp_path)

        assert len(result) == 1
        assert result[0]["fixture_id"] == 1


class TestExtractAllLeagues:

    @patch("pipelines.api_weather.extract.extract_weather_for_league")
    def test_loops_over_all_leagues(self, mock_extract, tmp_path):
        mock_extract.side_effect = lambda league_name, season, stadiums_df, fixtures_dir: [
            {"fixture_id": 1, "team_home": league_name}
        ]
        df = make_stadiums_df()

        result = extract_all_leagues(2022, ["Premier League", "Ligue 1"], df, tmp_path)

        assert set(result.keys()) == {"Premier League", "Ligue 1"}
        assert result["Premier League"][0]["team_home"] == "Premier League"

    @patch("pipelines.api_weather.extract.extract_weather_for_league")
    def test_exception_on_one_league_does_not_block_others(self, mock_extract, tmp_path):
        def side_effect(league_name, season, stadiums_df, fixtures_dir):
            if league_name == "Premier League":
                raise ValueError("boom")
            return [{"fixture_id": 1}]

        mock_extract.side_effect = side_effect
        df = make_stadiums_df()

        result = extract_all_leagues(2022, ["Premier League", "Ligue 1"], df, tmp_path)

        assert result["Premier League"] == []
        assert result["Ligue 1"] == [{"fixture_id": 1}]


class TestSaveRawData:

    def test_writes_new_file(self, tmp_path):
        all_data = {"Premier League": [{"fixture_id": 1}]}

        save_raw_data(all_data, season=2022, output_dir=tmp_path)

        filepath = tmp_path / "premier_league_2022_weather.json"
        assert filepath.exists()
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert content == [{"fixture_id": 1}]

    def test_does_not_overwrite_existing_file(self, tmp_path):
        filepath = tmp_path / "premier_league_2022_weather.json"
        filepath.write_text(json.dumps([{"fixture_id": "original"}]))

        all_data = {"Premier League": [{"fixture_id": "new_ignored"}]}
        save_raw_data(all_data, season=2022, output_dir=tmp_path)

        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert content == [{"fixture_id": "original"}]

    def test_creates_output_dir_if_missing(self, tmp_path):
        output_dir = tmp_path / "nested" / "weather"
        all_data = {"Serie A": []}

        save_raw_data(all_data, season=2022, output_dir=output_dir)

        assert output_dir.exists()
        assert (output_dir / "serie_a_2022_weather.json").exists()

    @patch("builtins.open")
    def test_oserror_on_write_does_not_raise(self, mock_open_builtin, tmp_path):
        mock_open_builtin.side_effect = OSError("disk full")
        all_data = {"Premier League": [{"fixture_id": 1}]}

        # Ne doit pas lever d'exception malgre l'OSError -> capturee et loggee
        save_raw_data(all_data, season=2022, output_dir=tmp_path)


class TestExtractAndSaveSeason:

    @patch("pipelines.api_weather.extract.save_raw_data")
    @patch("pipelines.api_weather.extract.extract_weather_for_league")
    def test_extracts_and_saves_each_league(self, mock_extract, mock_save, tmp_path):
        # _file_exists utilise build_filepath(OUTPUT_DIR, ...) -> on pointe OUTPUT_DIR vers tmp_path
        with patch("pipelines.api_weather.extract.OUTPUT_DIR", tmp_path):
            mock_extract.return_value = [{"fixture_id": 1}]
            df = make_stadiums_df()

            extract_and_save_season(2022, ["Premier League"], df, tmp_path)

            mock_extract.assert_called_once_with("Premier League", 2022, df, tmp_path)
            mock_save.assert_called_once_with({"Premier League": [{"fixture_id": 1}]}, 2022, tmp_path)

    def test_skips_league_already_processed(self, tmp_path):
        # Fichier deja present pour Premier League dans OUTPUT_DIR (mocke = tmp_path)
        existing = tmp_path / "premier_league_2022_weather.json"
        existing.write_text("[]")

        with patch("pipelines.api_weather.extract.OUTPUT_DIR", tmp_path), \
             patch("pipelines.api_weather.extract.extract_weather_for_league") as mock_extract:

            df = make_stadiums_df()
            extract_and_save_season(2022, ["Premier League"], df, tmp_path)

            mock_extract.assert_not_called()

    def test_exception_on_one_league_does_not_block_others(self, tmp_path):
        with patch("pipelines.api_weather.extract.OUTPUT_DIR", tmp_path), \
             patch("pipelines.api_weather.extract.extract_weather_for_league") as mock_extract, \
             patch("pipelines.api_weather.extract.save_raw_data") as mock_save:

            def side_effect(league_name, season, stadiums_df, fixtures_dir):
                if league_name == "Premier League":
                    raise ValueError("boom")
                return [{"fixture_id": 1}]

            mock_extract.side_effect = side_effect
            df = make_stadiums_df()

            # Ne doit pas lever -> exception capturee, "Ligue 1" doit etre traitee
            extract_and_save_season(2022, ["Premier League", "Ligue 1"], df, tmp_path)

            assert mock_extract.call_count == 2
            mock_save.assert_called_once_with({"Ligue 1": [{"fixture_id": 1}]}, 2022, tmp_path)


class TestRunPipeline:

    @patch("pipelines.api_weather.extract.extract_and_save_season")
    @patch("pipelines.api_weather.extract.load_leagues")
    @patch("pipelines.api_weather.extract.load_stadiums")
    def test_runs_once_per_season(self, mock_load_stadiums, mock_load_leagues, mock_extract_and_save):
        mock_load_stadiums.return_value = make_stadiums_df()
        mock_load_leagues.return_value = {"Premier League": 39, "Ligue 1": 61}

        run_pipeline([2022, 2023])

        assert mock_extract_and_save.call_count == 2

    @patch("pipelines.api_weather.extract.extract_and_save_season")
    @patch("pipelines.api_weather.extract.load_leagues")
    @patch("pipelines.api_weather.extract.load_stadiums")
    def test_loads_referentials_only_once(self, mock_load_stadiums, mock_load_leagues, mock_extract_and_save):
        mock_load_stadiums.return_value = make_stadiums_df()
        mock_load_leagues.return_value = {"Premier League": 39}

        run_pipeline([2022, 2023, 2024])

        mock_load_stadiums.assert_called_once()
        mock_load_leagues.assert_called_once()

    @patch("pipelines.api_weather.extract.extract_and_save_season")
    @patch("pipelines.api_weather.extract.load_leagues")
    @patch("pipelines.api_weather.extract.load_stadiums")
    def test_passes_league_names_not_ids(self, mock_load_stadiums, mock_load_leagues, mock_extract_and_save):
        mock_load_stadiums.return_value = make_stadiums_df()
        mock_load_leagues.return_value = {"Premier League": 39, "Ligue 1": 61}

        run_pipeline([2022])

        called_leagues = mock_extract_and_save.call_args.args[1]
        assert called_leagues == ["Premier League", "Ligue 1"]

    @patch("pipelines.api_weather.extract.extract_and_save_season")
    @patch("pipelines.api_weather.extract.load_leagues")
    @patch("pipelines.api_weather.extract.load_stadiums")
    def test_exception_on_one_season_does_not_block_others(self, mock_load_stadiums, mock_load_leagues, mock_extract_and_save):
        mock_load_stadiums.return_value = make_stadiums_df()
        mock_load_leagues.return_value = {"Premier League": 39}
        mock_extract_and_save.side_effect = [ValueError("boom"), None]

        # Ne doit pas lever malgre l'exception sur la premiere saison
        run_pipeline([2022, 2023])

        assert mock_extract_and_save.call_count == 2

    @patch("pipelines.api_weather.extract.load_stadiums")
    def test_missing_stadiums_csv_raises_filenotfounderror(self, mock_load_stadiums):
        mock_load_stadiums.side_effect = FileNotFoundError("stadiums.csv introuvable")

        with pytest.raises(FileNotFoundError):
            run_pipeline([2022])