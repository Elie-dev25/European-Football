"""
Tests pour pipelines/api_football/extract.py

Philosophie : aucun vrai appel HTTP. requests.get est systematiquement mocke.
time.sleep est mocke pour ne jamais ralentir la suite de tests.
"""

import json
import requests
import pytest
from pathlib import Path
from unittest.mock import patch, Mock

from pipelines.extractors.api_football.extract import (
    _call_api,
    get_standings,
    get_fixtures,
    get_top_scorers,
    get_top_assists,
    _file_exists,
    extract_league_data,
    extract_all_leagues,
    save_raw_data,
    extract_and_save_season,
    run_pipeline,
)


class TestCallApi:

    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_success_200_returns_json(self, mock_get):
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"response": ["data"]}
        mock_get.return_value = mock_response

        result = _call_api("standings", {"league": 39, "season": 2022})

        assert result == {"response": ["data"]}
        mock_get.assert_called_once()

    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_404_or_500_returns_empty_dict_no_retry(self, mock_get):
        mock_response = Mock(status_code=500)
        mock_get.return_value = mock_response

        result = _call_api("standings", {"league": 39, "season": 2022})

        assert result == {}
        mock_get.assert_called_once()

    @patch("pipelines.extractors.api_football.extract.time.sleep")
    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_429_retries_with_retry_after_header(self, mock_get, mock_sleep):
        rate_limited = Mock(status_code=429, headers={"Retry-After": "5"})
        success = Mock(status_code=200)
        success.json.return_value = {"response": ["ok"]}
        mock_get.side_effect = [rate_limited, success]

        result = _call_api("fixtures", {"league": 39, "season": 2022}, retries=3)

        assert result == {"response": ["ok"]}
        mock_sleep.assert_called_once_with(5)
        assert mock_get.call_count == 2

    @patch("pipelines.extractors.api_football.extract.time.sleep")
    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_429_without_retry_after_header_defaults_to_60s(self, mock_get, mock_sleep):
        rate_limited = Mock(status_code=429, headers={})
        success = Mock(status_code=200)
        success.json.return_value = {"response": []}
        mock_get.side_effect = [rate_limited, success]

        _call_api("fixtures", {"league": 39, "season": 2022}, retries=3)

        mock_sleep.assert_called_once_with(60)

    @patch("pipelines.extractors.api_football.extract.time.sleep")
    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_timeout_then_success(self, mock_get, mock_sleep):
        success = Mock(status_code=200)
        success.json.return_value = {"response": ["data"]}
        mock_get.side_effect = [requests.exceptions.Timeout(), success]

        result = _call_api("standings", {"league": 39, "season": 2022}, retries=3)

        assert result == {"response": ["data"]}
        mock_sleep.assert_called_once_with(10)
        assert mock_get.call_count == 2

    @patch("pipelines.extractors.api_football.extract.time.sleep")
    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_connection_error_now_retries_like_timeout(self, mock_get, mock_sleep):
        success = Mock(status_code=200)
        success.json.return_value = {"response": ["data"]}
        mock_get.side_effect = [requests.exceptions.ConnectionError(), success]

        result = _call_api("standings", {"league": 39, "season": 2022}, retries=4)

        assert result == {"response": ["data"]}
        mock_sleep.assert_called_once_with(10)
        assert mock_get.call_count == 2

    @patch("pipelines.extractors.api_football.extract.time.sleep")
    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_connection_error_exhausts_retries_if_persistent(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = _call_api("standings", {"league": 39, "season": 2022}, retries=4)

        assert result == {}
        assert mock_get.call_count == 4
        assert mock_sleep.call_count == 4

    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_generic_request_exception_returns_empty_dict(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("erreur reseau")

        result = _call_api("standings", {"league": 39, "season": 2022})

        assert result == {}

    @patch("pipelines.extractors.api_football.extract.time.sleep")
    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_exhausts_all_retries_on_repeated_timeout(self, mock_get, mock_sleep):
        mock_get.side_effect = requests.exceptions.Timeout()

        result = _call_api("standings", {"league": 39, "season": 2022}, retries=3)

        assert result == {}
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 3

    @patch("pipelines.extractors.api_football.extract.requests.get")
    def test_passes_correct_url_and_params(self, mock_get):
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        _call_api("players/topscorers", {"league": 39, "season": 2022})

        called_args = mock_get.call_args.args
        called_kwargs = mock_get.call_args.kwargs
        assert called_args[0] == "https://v3.football.api-sports.io/players/topscorers"
        assert called_kwargs["params"] == {"league": 39, "season": 2022}
        assert called_kwargs["timeout"] == 30


class TestGetters:

    @patch("pipelines.extractors.api_football.extract._call_api")
    def test_get_standings_calls_correct_endpoint(self, mock_call_api):
        mock_call_api.return_value = {"response": ["standings_data"]}

        result = get_standings(39, 2022)

        mock_call_api.assert_called_once_with("standings", {"league": 39, "season": 2022})
        assert result == {"response": ["standings_data"]}

    @patch("pipelines.extractors.api_football.extract._call_api")
    def test_get_fixtures_calls_correct_endpoint(self, mock_call_api):
        mock_call_api.return_value = {"response": ["fixtures_data"]}

        result = get_fixtures(39, 2022)

        mock_call_api.assert_called_once_with("fixtures", {"league": 39, "season": 2022})
        assert result == {"response": ["fixtures_data"]}

    @patch("pipelines.extractors.api_football.extract._call_api")
    def test_get_top_scorers_calls_correct_endpoint(self, mock_call_api):
        get_top_scorers(39, 2022)
        mock_call_api.assert_called_once_with("players/topscorers", {"league": 39, "season": 2022})

    @patch("pipelines.extractors.api_football.extract._call_api")
    def test_get_top_assists_calls_correct_endpoint(self, mock_call_api):
        get_top_assists(39, 2022)
        mock_call_api.assert_called_once_with("players/topassists", {"league": 39, "season": 2022})


class TestFileExists:

    def test_returns_true_when_file_exists(self, tmp_path):
        filepath = tmp_path / "premier_league_2022_fixtures.json"
        filepath.write_text("{}")

        assert _file_exists("Premier League", 2022, "fixtures", tmp_path) is True

    def test_returns_false_when_file_missing(self, tmp_path):
        assert _file_exists("Premier League", 2022, "fixtures", tmp_path) is False


class TestExtractLeagueData:

    @patch("pipelines.extractors.api_football.extract.get_top_assists")
    @patch("pipelines.extractors.api_football.extract.get_top_scorers")
    @patch("pipelines.extractors.api_football.extract.get_fixtures")
    @patch("pipelines.extractors.api_football.extract.get_standings")
    def test_calls_api_when_no_files_exist(
        self, mock_standings, mock_fixtures, mock_scorers, mock_assists, tmp_path
    ):
        mock_standings.return_value = {"response": ["standings"]}
        mock_fixtures.return_value = {"response": ["fixtures"]}
        mock_scorers.return_value = {"response": ["scorers"]}
        mock_assists.return_value = {"response": ["assists"]}

        result = extract_league_data("Premier League", 39, 2022, tmp_path)

        assert result["standings"] == {"response": ["standings"]}
        assert result["fixtures"] == {"response": ["fixtures"]}
        assert result["top_scorers"] == {"response": ["scorers"]}
        assert result["top_assists"] == {"response": ["assists"]}
        mock_standings.assert_called_once_with(39, 2022)
        mock_fixtures.assert_called_once_with(39, 2022)

    @patch("pipelines.extractors.api_football.extract.get_top_assists")
    @patch("pipelines.extractors.api_football.extract.get_top_scorers")
    @patch("pipelines.extractors.api_football.extract.get_fixtures")
    @patch("pipelines.extractors.api_football.extract.get_standings")
    def test_skips_api_call_when_file_already_exists(
        self, mock_standings, mock_fixtures, mock_scorers, mock_assists, tmp_path
    ):
        filepath = tmp_path / "premier_league_2022_standings.json"
        filepath.write_text(json.dumps({"response": ["from_disk"]}))

        mock_fixtures.return_value = {"response": []}
        mock_scorers.return_value = {"response": []}
        mock_assists.return_value = {"response": []}

        result = extract_league_data("Premier League", 39, 2022, tmp_path)

        assert result["standings"] == {"response": ["from_disk"]}
        mock_standings.assert_not_called()

    def test_zero_api_calls_when_all_files_exist(self, tmp_path):
        for data_type in ["standings", "fixtures", "top_scorers", "top_assists"]:
            filepath = tmp_path / f"premier_league_2022_{data_type}.json"
            filepath.write_text(json.dumps({"response": [data_type]}))

        with patch("pipelines.extractors.api_football.extract.get_standings") as mock_s, \
             patch("pipelines.extractors.api_football.extract.get_fixtures") as mock_f, \
             patch("pipelines.extractors.api_football.extract.get_top_scorers") as mock_sc, \
             patch("pipelines.extractors.api_football.extract.get_top_assists") as mock_a:

            result = extract_league_data("Premier League", 39, 2022, tmp_path)

            mock_s.assert_not_called()
            mock_f.assert_not_called()
            mock_sc.assert_not_called()
            mock_a.assert_not_called()

        assert result["standings"] == {"response": ["standings"]}


class TestExtractAllLeagues:

    @patch("pipelines.extractors.api_football.extract.extract_league_data")
    def test_loops_over_all_leagues(self, mock_extract, tmp_path):
        mock_extract.side_effect = lambda league_name, league_id, season, output_dir: {
            "fixtures": {"response": [f"{league_name}_data"]}
        }
        leagues = {"Premier League": 39, "Ligue 1": 61}

        result = extract_all_leagues(2022, leagues, tmp_path)

        assert set(result.keys()) == {"Premier League", "Ligue 1"}
        assert mock_extract.call_count == 2
        mock_extract.assert_any_call("Premier League", 39, 2022, tmp_path)
        mock_extract.assert_any_call("Ligue 1", 61, 2022, tmp_path)

    @patch("pipelines.extractors.api_football.extract.extract_league_data")
    def test_empty_leagues_dict_returns_empty_result(self, mock_extract, tmp_path):
        result = extract_all_leagues(2022, {}, tmp_path)

        assert result == {}
        mock_extract.assert_not_called()


class TestSaveRawData:

    def test_writes_new_file(self, tmp_path):
        all_data = {"Premier League": {"fixtures": {"response": ["match1"]}}}

        save_raw_data(all_data, season=2022, output_dir=tmp_path)

        filepath = tmp_path / "premier_league_2022_fixtures.json"
        assert filepath.exists()
        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert content == {"response": ["match1"]}

    def test_does_not_overwrite_existing_file(self, tmp_path):
        filepath = tmp_path / "premier_league_2022_fixtures.json"
        filepath.write_text(json.dumps({"response": ["original_untouched"]}))

        all_data = {"Premier League": {"fixtures": {"response": ["new_data_should_be_ignored"]}}}
        save_raw_data(all_data, season=2022, output_dir=tmp_path)

        content = json.loads(filepath.read_text(encoding="utf-8"))
        assert content == {"response": ["original_untouched"]}

    def test_creates_output_dir_if_missing(self, tmp_path):
        output_dir = tmp_path / "nested" / "data"
        all_data = {"Serie A": {"standings": {"response": []}}}

        save_raw_data(all_data, season=2022, output_dir=output_dir)

        assert output_dir.exists()
        assert (output_dir / "serie_a_2022_standings.json").exists()

    def test_preserves_special_characters(self, tmp_path):
        all_data = {"Ligue 1": {"top_scorers": {"response": [{"name": "Mbappé", "city": "Genève"}]}}}

        save_raw_data(all_data, season=2022, output_dir=tmp_path)

        filepath = tmp_path / "ligue_1_2022_top_scorers.json"
        raw_text = filepath.read_text(encoding="utf-8")
        assert "Mbappé" in raw_text
        assert "Genève" in raw_text

    def test_multiple_leagues_and_data_types(self, tmp_path):
        all_data = {
            "Premier League": {
                "fixtures": {"response": ["pl_fixtures"]},
                "standings": {"response": ["pl_standings"]},
            },
            "Bundesliga": {
                "fixtures": {"response": ["bl_fixtures"]},
            },
        }

        save_raw_data(all_data, season=2022, output_dir=tmp_path)

        assert (tmp_path / "premier_league_2022_fixtures.json").exists()
        assert (tmp_path / "premier_league_2022_standings.json").exists()
        assert (tmp_path / "bundesliga_2022_fixtures.json").exists()


class TestExtractAndSaveSeason:

    @patch("pipelines.extractors.api_football.extract.save_raw_data")
    @patch("pipelines.extractors.api_football.extract.extract_all_leagues")
    def test_calls_extract_then_save_in_order(self, mock_extract_all, mock_save, tmp_path):
        mock_extract_all.return_value = {"Premier League": {"fixtures": {"response": []}}}
        leagues = {"Premier League": 39}

        result = extract_and_save_season(2022, leagues, tmp_path)

        mock_extract_all.assert_called_once_with(2022, leagues, tmp_path)
        mock_save.assert_called_once_with(
            {"Premier League": {"fixtures": {"response": []}}}, season=2022, output_dir=tmp_path
        )
        assert result == {"Premier League": {"fixtures": {"response": []}}}


class TestRunPipeline:

    @patch("pipelines.extractors.api_football.extract.extract_and_save_season")
    @patch("pipelines.extractors.api_football.extract.load_leagues")
    def test_runs_once_per_season(self, mock_load_leagues, mock_extract_and_save):
        mock_load_leagues.return_value = {"Premier League": 39}
        mock_extract_and_save.return_value = {
            "Premier League": {"fixtures": {"response": ["match1", "match2"]}}
        }

        run_pipeline([2022, 2023])

        assert mock_extract_and_save.call_count == 2
        seasons_called = [c.args[0] for c in mock_extract_and_save.call_args_list]
        assert seasons_called == [2022, 2023]

    @patch("pipelines.extractors.api_football.extract.extract_and_save_season")
    @patch("pipelines.extractors.api_football.extract.load_leagues")
    def test_loads_leagues_only_once(self, mock_load_leagues, mock_extract_and_save):
        mock_load_leagues.return_value = {"Premier League": 39, "Ligue 1": 61}
        mock_extract_and_save.return_value = {}

        run_pipeline([2022, 2023, 2024])

        mock_load_leagues.assert_called_once()

    @patch("pipelines.extractors.api_football.extract.extract_and_save_season")
    @patch("pipelines.extractors.api_football.extract.load_leagues")
    def test_single_season_pipeline(self, mock_load_leagues, mock_extract_and_save):
        mock_load_leagues.return_value = {"Premier League": 39}
        mock_extract_and_save.return_value = {
            "Premier League": {"fixtures": {"response": []}}
        }

        run_pipeline([2022])

        mock_extract_and_save.assert_called_once()
