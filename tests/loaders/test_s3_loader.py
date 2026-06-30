"""
tests/loaders/test_s3_loader.py

Tests unitaires pour pipelines/loaders/s3_loader.py
Aucun appel reseau reel - s3_client entierement mocke.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from pipelines.loaders import s3_loader


def make_client_error(code: str) -> ClientError:
    return ClientError(
        error_response={"Error": {"Code": code, "Message": "mocked"}},
        operation_name="mocked_operation",
    )


# ---------------------------------------------------------------------------
# _file_exists_in_s3
# ---------------------------------------------------------------------------

class TestFileExistsInS3:

    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_returns_true_when_object_exists(self, mock_client):
        mock_client.head_object.return_value = {}
        assert s3_loader._file_exists_in_s3("bucket", "key.json") is True

    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_returns_false_on_404(self, mock_client):
        mock_client.head_object.side_effect = make_client_error("404")
        assert s3_loader._file_exists_in_s3("bucket", "key.json") is False

    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_reraises_other_client_errors(self, mock_client):
        mock_client.head_object.side_effect = make_client_error("403")
        with pytest.raises(ClientError):
            s3_loader._file_exists_in_s3("bucket", "key.json")


# ---------------------------------------------------------------------------
# upload_file_to_s3
# ---------------------------------------------------------------------------

class TestUploadFileToS3:

    def test_raises_if_local_file_missing(self, tmp_path):
        missing = tmp_path / "ghost.json"
        with pytest.raises(FileNotFoundError):
            s3_loader.upload_file_to_s3(missing, "key.json")

    @patch("pipelines.loaders.s3_loader._file_exists_in_s3", return_value=True)
    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_skips_if_exists_and_not_forced(self, mock_client, mock_exists, tmp_path):
        local_file = tmp_path / "data.json"
        local_file.write_text("{}")

        result = s3_loader.upload_file_to_s3(local_file, "key.json", force_upload=False)

        assert result is False
        mock_client.upload_file.assert_not_called()

    @patch("pipelines.loaders.s3_loader._file_exists_in_s3", return_value=True)
    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_uploads_if_exists_but_forced(self, mock_client, mock_exists, tmp_path):
        local_file = tmp_path / "data.json"
        local_file.write_text("{}")

        result = s3_loader.upload_file_to_s3(local_file, "key.json", force_upload=True)

        assert result is True
        mock_client.upload_file.assert_called_once()

    @patch("pipelines.loaders.s3_loader._file_exists_in_s3", return_value=False)
    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_uploads_if_not_present(self, mock_client, mock_exists, tmp_path):
        local_file = tmp_path / "data.json"
        local_file.write_text("{}")

        result = s3_loader.upload_file_to_s3(local_file, "key.json")

        assert result is True
        mock_client.upload_file.assert_called_once_with(str(local_file), s3_loader.BUCKET_NAME, "key.json")

    @patch("pipelines.loaders.s3_loader._file_exists_in_s3", return_value=False)
    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_access_denied_fails_immediately_no_retry(self, mock_client, mock_exists, tmp_path):
        local_file = tmp_path / "data.json"
        local_file.write_text("{}")
        mock_client.upload_file.side_effect = make_client_error("AccessDenied")

        with pytest.raises(ClientError):
            s3_loader.upload_file_to_s3(local_file, "key.json", retries=5)

        # Un seul essai, pas de retry sur AccessDenied
        assert mock_client.upload_file.call_count == 1

    @patch("pipelines.loaders.s3_loader.time.sleep", return_value=None)
    @patch("pipelines.loaders.s3_loader._file_exists_in_s3", return_value=False)
    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_retries_on_other_client_error_then_succeeds(self, mock_client, mock_exists, mock_sleep, tmp_path):
        local_file = tmp_path / "data.json"
        local_file.write_text("{}")
        mock_client.upload_file.side_effect = [
            make_client_error("ThrottlingException"),
            make_client_error("ThrottlingException"),
            None,  # succes au 3e essai
        ]

        result = s3_loader.upload_file_to_s3(local_file, "key.json", retries=5)

        assert result is True
        assert mock_client.upload_file.call_count == 3

    @patch("pipelines.loaders.s3_loader.time.sleep", return_value=None)
    @patch("pipelines.loaders.s3_loader._file_exists_in_s3", return_value=False)
    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_retries_on_generic_exception_then_succeeds(self, mock_client, mock_exists, mock_sleep, tmp_path):
        local_file = tmp_path / "data.json"
        local_file.write_text("{}")
        mock_client.upload_file.side_effect = [
            ConnectionError("reseau coupe"),
            None,
        ]

        result = s3_loader.upload_file_to_s3(local_file, "key.json", retries=5)

        assert result is True
        assert mock_client.upload_file.call_count == 2

    @patch("pipelines.loaders.s3_loader.time.sleep", return_value=None)
    @patch("pipelines.loaders.s3_loader._file_exists_in_s3", return_value=False)
    @patch("pipelines.loaders.s3_loader.s3_client")
    def test_returns_false_after_exhausting_all_retries(self, mock_client, mock_exists, mock_sleep, tmp_path):
        local_file = tmp_path / "data.json"
        local_file.write_text("{}")
        mock_client.upload_file.side_effect = make_client_error("ThrottlingException")

        result = s3_loader.upload_file_to_s3(local_file, "key.json", retries=3)

        assert result is False
        assert mock_client.upload_file.call_count == 3


# ---------------------------------------------------------------------------
# upload_directory_to_s3
# ---------------------------------------------------------------------------

class TestUploadDirectoryToS3:

    def test_raises_if_local_dir_missing(self, tmp_path):
        missing_dir = tmp_path / "ghost"
        with pytest.raises(FileNotFoundError):
            s3_loader.upload_directory_to_s3(missing_dir, "bronze/prefix")

    def test_returns_empty_results_if_no_json_files(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = s3_loader.upload_directory_to_s3(empty_dir, "bronze/prefix")

        assert result == {"uploaded": [], "skipped": [], "failed": []}

    @patch("pipelines.loaders.s3_loader.upload_file_to_s3")
    def test_dispatches_uploaded_and_skipped_correctly(self, mock_upload, tmp_path):
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        mock_upload.side_effect = [True, False]  # a uploade, b skip

        result = s3_loader.upload_directory_to_s3(tmp_path, "bronze/prefix")

        assert result["uploaded"] == ["bronze/prefix/a.json"]
        assert result["skipped"] == ["bronze/prefix/b.json"]
        assert result["failed"] == []

    @patch("pipelines.loaders.s3_loader.upload_file_to_s3")
    def test_isolates_failure_one_file_does_not_block_others(self, mock_upload, tmp_path):
        (tmp_path / "a.json").write_text("{}")
        (tmp_path / "b.json").write_text("{}")
        (tmp_path / "c.json").write_text("{}")
        mock_upload.side_effect = [True, Exception("panne reseau"), True]

        result = s3_loader.upload_directory_to_s3(tmp_path, "bronze/prefix")

        assert result["uploaded"] == ["bronze/prefix/a.json", "bronze/prefix/c.json"]
        assert result["failed"] == ["b.json"]
        assert mock_upload.call_count == 3  # le 3e fichier a quand meme ete tente


# ---------------------------------------------------------------------------
# run_pipeline
# ---------------------------------------------------------------------------

class TestRunPipeline:

    @patch("pipelines.loaders.s3_loader.upload_directory_to_s3")
    def test_processes_all_sources_by_default(self, mock_upload_dir):
        mock_upload_dir.return_value = {"uploaded": [], "skipped": [], "failed": []}

        results = s3_loader.run_pipeline()

        assert set(results.keys()) == set(s3_loader.SOURCES_CONFIG.keys())
        assert mock_upload_dir.call_count == len(s3_loader.SOURCES_CONFIG)

    @patch("pipelines.loaders.s3_loader.upload_directory_to_s3")
    def test_processes_only_requested_sources(self, mock_upload_dir):
        mock_upload_dir.return_value = {"uploaded": [], "skipped": [], "failed": []}

        results = s3_loader.run_pipeline(sources=["api_football"])

        assert list(results.keys()) == ["api_football"]
        mock_upload_dir.assert_called_once()

    @patch("pipelines.loaders.s3_loader.upload_directory_to_s3")
    def test_ignores_unknown_source(self, mock_upload_dir):
        mock_upload_dir.return_value = {"uploaded": [], "skipped": [], "failed": []}

        results = s3_loader.run_pipeline(sources=["api_football", "source_inexistante"])

        assert list(results.keys()) == ["api_football"]

    @patch("pipelines.loaders.s3_loader.upload_directory_to_s3")
    def test_isolates_failure_one_source_does_not_block_others(self, mock_upload_dir):
        def side_effect(local_dir, s3_prefix, force_upload=False):
            if "api_football" in s3_prefix:
                raise Exception("panne totale source api_football")
            return {"uploaded": ["ok.json"], "skipped": [], "failed": []}

        mock_upload_dir.side_effect = side_effect

        results = s3_loader.run_pipeline()

        assert results["api_football"]["failed"] == ["DOSSIER_ENTIER"]
        assert results["api_weather"]["uploaded"] == ["ok.json"]
        assert results["kaggle"]["uploaded"] == ["ok.json"]

    @patch("pipelines.loaders.s3_loader.upload_directory_to_s3")
    def test_force_upload_propagated_to_directory_upload(self, mock_upload_dir):
        mock_upload_dir.return_value = {"uploaded": [], "skipped": [], "failed": []}

        s3_loader.run_pipeline(sources=["api_football"], force_upload=True)

        _, kwargs = mock_upload_dir.call_args
        assert kwargs["force_upload"] is True