# pipelines/kaggle/extract.py
import json
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pipelines.extractors.kaggle.extract import (
    _connect_sqlite,
    _read_table,
    _file_exists,
    save_raw_data,
    extract_table,
    run_pipeline,
    TABLES_CONFIG,
)


# =============================================================================
# Tests _connect_sqlite
# =============================================================================

class TestConnectSqlite:

    def test_returns_connection_when_file_exists(self, tmp_path):
        db_path = tmp_path / "test.sqlite"
        conn = sqlite3.connect(db_path)
        conn.close()
        result = _connect_sqlite(db_path)
        assert isinstance(result, sqlite3.Connection)
        result.close()

    def test_raises_filenotfounderror_when_missing(self, tmp_path):
        missing = tmp_path / "missing.sqlite"
        with pytest.raises(FileNotFoundError):
            _connect_sqlite(missing)

    def test_error_message_mentions_path(self, tmp_path):
        missing = tmp_path / "missing.sqlite"
        with pytest.raises(FileNotFoundError, match="missing.sqlite"):
            _connect_sqlite(missing)


# =============================================================================
# Tests _read_table
# =============================================================================

class TestReadTable:

    def test_returns_list_of_dicts(self, tmp_path):
        db_path = tmp_path / "test.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE Team (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO Team VALUES (1, 'Arsenal')")
        conn.commit()
        result = _read_table(conn, "SELECT * FROM Team")
        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        conn.close()

    def test_returns_correct_data(self, tmp_path):
        db_path = tmp_path / "test.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE Team (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO Team VALUES (1, 'Arsenal')")
        conn.commit()
        result = _read_table(conn, "SELECT * FROM Team")
        assert result == [{"id": 1, "name": "Arsenal"}]
        conn.close()

    def test_returns_empty_list_when_no_data(self, tmp_path):
        db_path = tmp_path / "test.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE Team (id INTEGER, name TEXT)")
        conn.commit()
        result = _read_table(conn, "SELECT * FROM Team")
        assert result == []
        conn.close()

    def test_returns_multiple_rows(self, tmp_path):
        db_path = tmp_path / "test.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE Team (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO Team VALUES (1, 'Arsenal')")
        conn.execute("INSERT INTO Team VALUES (2, 'Chelsea')")
        conn.commit()
        result = _read_table(conn, "SELECT * FROM Team")
        assert len(result) == 2
        conn.close()

    def test_column_names_preserved(self, tmp_path):
        db_path = tmp_path / "test.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE Team (team_id INTEGER, team_name TEXT)")
        conn.execute("INSERT INTO Team VALUES (1, 'Arsenal')")
        conn.commit()
        result = _read_table(conn, "SELECT * FROM Team")
        assert "team_id" in result[0]
        assert "team_name" in result[0]
        conn.close()


# =============================================================================
# Tests _file_exists
# =============================================================================

class TestFileExists:

    def test_returns_true_when_file_exists(self, tmp_path):
        f = tmp_path / "team.json"
        f.write_text("[]")
        assert _file_exists(tmp_path, "team.json") is True

    def test_returns_false_when_file_missing(self, tmp_path):
        assert _file_exists(tmp_path, "team.json") is False


# =============================================================================
# Tests save_raw_data
# =============================================================================

class TestSaveRawData:

    def test_creates_file(self, tmp_path):
        data = [{"id": 1, "name": "Arsenal"}]
        save_raw_data(data, tmp_path, "team.json")
        assert (tmp_path / "team.json").exists()

    def test_file_content_is_valid_json(self, tmp_path):
        data = [{"id": 1, "name": "Arsenal"}]
        save_raw_data(data, tmp_path, "team.json")
        with open(tmp_path / "team.json", "r") as f:
            result = json.load(f)
        assert result == data

    def test_does_not_create_file_when_empty(self, tmp_path):
        save_raw_data([], tmp_path, "team.json")
        assert not (tmp_path / "team.json").exists()

    def test_creates_output_dir_if_missing(self, tmp_path):
        output_dir = tmp_path / "kaggle"
        save_raw_data([{"id": 1}], output_dir, "team.json")
        assert output_dir.exists()

    def test_handles_multiple_records(self, tmp_path):
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        save_raw_data(data, tmp_path, "team.json")
        with open(tmp_path / "team.json", "r") as f:
            result = json.load(f)
        assert len(result) == 3


# =============================================================================
# Tests extract_table
# =============================================================================

class TestExtractTable:

    def test_skips_if_file_exists(self, tmp_path):
        existing = tmp_path / "team.json"
        existing.write_text("[]")
        with patch("pipelines.extractors.kaggle.extract._connect_sqlite") as mock_conn:
            extract_table("team", "SELECT * FROM Team", "team.json", tmp_path / "db.sqlite", tmp_path)
            mock_conn.assert_not_called()

    def test_extracts_and_saves_when_file_missing(self, tmp_path):
        db_path = tmp_path / "test.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE Team (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO Team VALUES (1, 'Arsenal')")
        conn.commit()
        conn.close()
        extract_table("team", "SELECT * FROM Team", "team.json", db_path, tmp_path)
        assert (tmp_path / "team.json").exists()

    def test_raises_filenotfounderror_when_db_missing(self, tmp_path):
        missing_db = tmp_path / "missing.sqlite"
        with pytest.raises(FileNotFoundError):
            extract_table("team", "SELECT * FROM Team", "team.json", missing_db, tmp_path)

    def test_idempotence_does_not_overwrite(self, tmp_path):
        existing = tmp_path / "team.json"
        existing.write_text('[{"id": 99}]')
        with patch("pipelines.extractors.kaggle.extract._connect_sqlite"):
            extract_table("team", "SELECT * FROM Team", "team.json", tmp_path / "db.sqlite", tmp_path)
        with open(existing) as f:
            result = json.load(f)
        assert result == [{"id": 99}]


# =============================================================================
# Tests run_pipeline
# =============================================================================

class TestRunPipeline:

    def test_calls_extract_table_for_each_table(self, tmp_path):
        leagues_csv = tmp_path / "leagues.csv"
        leagues_csv.write_text(
            "league_name,league_id,country,kaggle_league_id\n"
            "Premier League,39,England,1729\n"
        )
        with patch("pipelines.extractors.kaggle.extract.extract_table") as mock_extract, \
             patch("pipelines.extractors.kaggle.extract.LEAGUES_CSV", leagues_csv):
            run_pipeline(db_path=tmp_path / "db.sqlite", output_dir=tmp_path)
            # TABLES_CONFIG + match = 4 tables
            assert mock_extract.call_count == len(TABLES_CONFIG) + 1

    def test_continues_on_table_failure(self, tmp_path):
        leagues_csv = tmp_path / "leagues.csv"
        leagues_csv.write_text(
            "league_name,league_id,country,kaggle_league_id\n"
            "Premier League,39,England,1729\n"
        )
        with patch("pipelines.extractors.kaggle.extract.extract_table", side_effect=Exception("erreur")), \
             patch("pipelines.extractors.kaggle.extract.LEAGUES_CSV", leagues_csv):
            # Ne doit pas lever d'exception
            run_pipeline(db_path=tmp_path / "db.sqlite", output_dir=tmp_path)

    def test_match_query_contains_league_ids(self, tmp_path):
        leagues_csv = tmp_path / "leagues.csv"
        leagues_csv.write_text(
            "league_name,league_id,country,kaggle_league_id\n"
            "Premier League,39,England,1729\n"
            "Ligue 1,61,France,4769\n"
        )
        calls = []
        with patch("pipelines.extractors.kaggle.extract.extract_table", side_effect=lambda **kw: calls.append(kw)), \
             patch("pipelines.extractors.kaggle.extract.LEAGUES_CSV", leagues_csv):
            run_pipeline(db_path=tmp_path / "db.sqlite", output_dir=tmp_path)
        match_call = next(c for c in calls if c["filename"] == "match_2008_2016.json")
        assert "1729" in match_call["query"]
        assert "4769" in match_call["query"]
