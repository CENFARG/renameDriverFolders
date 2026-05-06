"""
Test: Worker Job Processor extraction (T2.6).

Verifies:
1. process_job() handles manual and scheduled modes
2. process_job() returns success/error dicts
3. process_folder_files() processes files in a folder

:task: T2.6 - Extract Worker Job Processor
:phase: RED (test written first)
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestProcessJob:
    """process_job() orchestrates file processing for a single job."""

    def test_job_processor_module_exists(self):
        from job_processor import process_job, process_folder_files
        assert process_job is not None
        assert process_folder_files is not None

    def test_manual_mode_processes_all_files(self):
        """Manual mode: process all files in the given folder."""
        from job_processor import process_job

        job_config = {
            "id": "job1",
            "name": "Test Job",
            "source_folder_id": "folder_root",
            "agent_config": {"prompt_template": "test"},
        }

        with patch("job_processor.agent_factory") as mock_af, \
             patch("job_processor.build") as mock_build, \
             patch("job_processor.storage") as mock_storage, \
             patch("job_processor.process_folder_files") as mock_pff:

            mock_af.create_agent_from_job_config.return_value = MagicMock()
            mock_pff.return_value = {"files_processed": 3, "files_renamed": 2, "errors": 0}

            result = process_job(job_config, folder_id="manual_folder", credentials=MagicMock())

            assert result["status"] == "success"
            assert result["stats"]["files_processed"] == 3
            assert result["stats"]["files_renamed"] == 2

    def test_scheduled_mode_uses_target_names(self):
        """Scheduled mode: find subfolders by name."""
        from job_processor import process_job

        job_config = {
            "id": "job2",
            "name": "Scheduled Job",
            "source_folder_id": "root_folder",
            "target_folder_names": ["Recibos", "Facturas"],
            "agent_config": {"prompt_template": "test"},
        }

        with patch("job_processor.agent_factory") as mock_af, \
             patch("job_processor.build") as mock_build, \
             patch("job_processor.storage") as mock_storage, \
             patch("job_processor.find_target_folders") as mock_find, \
             patch("job_processor.process_folder_files") as mock_pff:

            mock_af.create_agent_from_job_config.return_value = MagicMock()
            mock_find.return_value = ["folder_a", "folder_b"]
            mock_pff.return_value = {"files_processed": 1, "files_renamed": 1, "errors": 0}

            result = process_job(job_config, credentials=MagicMock())

            assert result["status"] == "success"
            assert mock_find.called

    def test_scheduled_mode_wildcard_processes_all(self):
        """Scheduled mode with ['*']: process all files in root folder."""
        from job_processor import process_job

        job_config = {
            "id": "job3",
            "name": "Wildcard Job",
            "source_folder_id": "root",
            "target_folder_names": ["*"],
            "agent_config": {"prompt_template": "test"},
        }

        with patch("job_processor.agent_factory") as mock_af, \
             patch("job_processor.build") as mock_build, \
             patch("job_processor.storage") as mock_storage, \
             patch("job_processor.process_folder_files") as mock_pff:

            mock_af.create_agent_from_job_config.return_value = MagicMock()
            mock_pff.return_value = {"files_processed": 5, "files_renamed": 4, "errors": 1}

            result = process_job(job_config, credentials=MagicMock())

            assert result["status"] == "success"
            assert result["stats"]["files_processed"] == 5

    def test_error_returns_error_dict(self):
        """Should return error dict on exception."""
        from job_processor import process_job

        job_config = {"id": "job4", "name": "Bad Job", "source_folder_id": "folder1"}

        with patch("job_processor.agent_factory") as mock_af, \
             patch("job_processor.build"), \
             patch("job_processor.storage"):
            mock_af.create_agent_from_job_config.side_effect = Exception("Agent failed")

            result = process_job(job_config, credentials=MagicMock())

            assert result["status"] == "error"
            assert "Agent failed" in result["error"]

    def test_no_folder_raises_in_result(self):
        """No folder_id and no source_folder_id → error result."""
        from job_processor import process_job

        job_config = {"id": "job5", "name": "No Folder"}

        with patch("job_processor.agent_factory") as mock_af, \
             patch("job_processor.build"), \
             patch("job_processor.storage"):

            mock_af.create_agent_from_job_config.return_value = MagicMock()
            result = process_job(job_config, credentials=MagicMock())
            assert result["status"] == "error"


class TestProcessFolderFiles:
    """process_folder_files() processes all files in a folder."""

    def test_processes_files_and_returns_stats(self):
        """Should process files and return stats dict."""
        from job_processor import process_folder_files

        mock_drive = MagicMock()
        mock_drive.files().list.return_value.execute.return_value = {
            "files": [
                {"id": "f1", "name": "doc1.pdf", "mimeType": "application/pdf"},
                {"id": "f2", "name": "DOCPROCESADO_doc.pdf", "mimeType": "application/pdf"},
            ]
        }

        mock_agent = MagicMock()
        mock_agent.run.return_value = MagicMock()

        job_config = {
            "agent_config": {
                "prompt_template": "Analyze {original_filename}: {file_content}",
            }
        }

        with patch("job_processor.download_file", return_value=b"content"), \
             patch("job_processor.content_extractor") as mock_ce, \
             patch("job_processor.parse_agent_response") as mock_parse, \
             patch("job_processor.build_filename") as mock_bf, \
             patch("job_processor.rename_file") as mock_rf:

            mock_ce.get_content.return_value = "extracted text"
            mock_parse.return_value = {"algorithm_id": "factura", "date": "2025-01-01"}
            mock_bf.return_value = "factura_2025-01-01.pdf"

            stats = process_folder_files(mock_drive, "folder1", mock_agent, job_config)

            assert stats["files_processed"] == 2  # counts all files
            assert stats["files_renamed"] == 1  # skips DOCPROCESADO

    def test_empty_folder_returns_zero_stats(self):
        """Should return zero stats for empty folder."""
        from job_processor import process_folder_files

        mock_drive = MagicMock()
        mock_drive.files().list.return_value.execute.return_value = {"files": []}

        stats = process_folder_files(mock_drive, "empty_folder", MagicMock(), {})
        assert stats["files_processed"] == 0
        assert stats["files_renamed"] == 0
        assert stats["errors"] == 0
