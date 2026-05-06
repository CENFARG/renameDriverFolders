"""
Test: Worker Integration Tests (T2.10).

End-to-end tests for the full job processing flow:
1. Manual job with user credentials
2. Scheduled job with ADC credentials
3. Full flow: config → job → files → rename

:task: T2.10 - Worker Test Infrastructure + Integration Tests
:phase: RED (test written first)
"""

import pytest
from unittest.mock import MagicMock, patch
import os


class TestIntegrationJobFlow:
    """Integration tests for full job processing pipeline."""

    def test_manual_job_full_flow(self):
        """Manual job: user provides folder_id and access_token."""
        from config import WorkerConfig
        from job_processor import process_job

        with patch.dict(os.environ, {
            "USE_SUPABASE": "false",
            "USE_GCS": "false",
            "ENVIRONMENT": "development",
        }):
            cfg = WorkerConfig()
            assert cfg.use_supabase is False

        job_config = {
            "id": "manual-job-1",
            "name": "Manual Classification",
            "source_folder_id": "root_folder",
            "agent_config": {
                "prompt_template": "Classify {original_filename}: {file_content}",
                "filename_format": "{date}_{algorithm_id}{ext}",
            },
        }

        with patch("job_processor.agent_factory") as mock_af, \
             patch("job_processor.build") as mock_build, \
             patch("job_processor.storage"), \
             patch("job_processor.process_folder_files") as mock_pff:

            mock_af.create_agent_from_job_config.return_value = MagicMock()
            mock_pff.return_value = {
                "files_processed": 5,
                "files_renamed": 4,
                "errors": 1,
            }

            result = process_job(
                job_config,
                folder_id="user_selected_folder",
                credentials=MagicMock(),
            )

            assert result["status"] == "success"
            assert result["job_id"] == "manual-job-1"
            assert result["stats"]["files_processed"] == 5
            assert result["stats"]["files_renamed"] == 4
            assert result["stats"]["errors"] == 1
            # Manual mode: should NOT call find_target_folders
            mock_pff.assert_called_once()

    def test_scheduled_job_with_subfolders(self):
        """Scheduled job: finds subfolders and processes each."""
        from job_processor import process_job

        job_config = {
            "id": "scheduled-1",
            "name": "Nightly Run",
            "source_folder_id": "root_folder",
            "target_folder_names": ["Recibos", "Facturas"],
            "agent_config": {
                "prompt_template": "Analyze {original_filename}",
                "filename_format": "{date}_{type}{ext}",
            },
        }

        with patch("job_processor.agent_factory") as mock_af, \
             patch("job_processor.build"), \
             patch("job_processor.storage"), \
             patch("job_processor.find_target_folders") as mock_find, \
             patch("job_processor.process_folder_files") as mock_pff:

            mock_af.create_agent_from_job_config.return_value = MagicMock()
            mock_find.return_value = ["folder_recibos", "folder_facturas"]
            mock_pff.return_value = {"files_processed": 2, "files_renamed": 2, "errors": 0}

            result = process_job(job_config, credentials=MagicMock())

            assert result["status"] == "success"
            assert mock_find.called
            assert mock_pff.call_count == 2  # Two subfolders
            assert result["stats"]["files_processed"] == 4  # 2 per folder

    def test_folder_processing_with_ai_pipeline(self):
        """Full pipeline: download → extract → classify → build filename → rename."""
        from job_processor import process_folder_files

        mock_drive = MagicMock()
        mock_drive.files().list.return_value.execute.return_value = {
            "files": [
                {"id": "f1", "name": "invoice_001.pdf", "mimeType": "application/pdf"},
            ]
        }

        mock_agent = MagicMock()
        mock_agent.run.return_value = MagicMock()

        job_config = {
            "agent_config": {
                "prompt_template": "Classify {original_filename}: {file_content}",
                "filename_format": "{date}_{algorithm_id}{ext}",
            },
        }

        with patch("job_processor.download_file", return_value=b"PDF content"), \
             patch("job_processor.content_extractor") as mock_ce, \
             patch("job_processor.parse_agent_response") as mock_parse, \
             patch("job_processor.build_filename") as mock_bf, \
             patch("job_processor.rename_file") as mock_rf:

            mock_ce.get_content.return_value = "Invoice from Mercedes Benz 2025-03"
            mock_parse.return_value = {
                "algorithm_id": "factura",
                "date": "2025-03-15",
                "confidence": 0.95,
                "reasoning": "Invoice detected",
            }
            mock_bf.return_value = "factura_2025-03-15.pdf"

            stats = process_folder_files(mock_drive, "folder1", mock_agent, job_config)

            assert stats["files_processed"] == 1
            assert stats["files_renamed"] == 1
            assert stats["errors"] == 0
            mock_rf.assert_called_once_with(mock_drive, "f1", "factura_2025-03-15.pdf")

    def test_config_and_credentials_flow(self):
        """Config loads correctly and creates appropriate credentials."""
        from config import WorkerConfig, get_credentials, create_credentials_from_token

        with patch.dict(os.environ, {"USE_SUPABASE": "false", "USE_GCS": "false"}):
            cfg = WorkerConfig()
            assert cfg.enable_ocr is True  # default

        # ADC credentials
        with patch("config.google.auth.default") as mock_default:
            mock_creds = MagicMock()
            mock_default.return_value = (mock_creds, "project-123")
            creds = get_credentials()
            assert creds == mock_creds

        # Token credentials
        with patch("config.OAuthCredentials") as mock_oauth:
            mock_oauth.return_value = MagicMock(token="ya29.test")
            token_creds = create_credentials_from_token("ya29.test")
            assert token_creds.token == "ya29.test"

    def test_ai_classifier_with_pydantic_model(self):
        """AI classifier extracts data from Pydantic model in agent response."""
        from ai_classifier import parse_agent_response

        mock_content = MagicMock()
        mock_content.model_dump.return_value = {
            "algorithm_id": "estado_contable",
            "date": "2025-12-31",
            "confidence": 0.92,
            "reasoning": "Annual balance sheet",
            "company": "Acme Corp",
        }

        response = MagicMock()
        response.content = mock_content

        result = parse_agent_response(response)
        assert result["algorithm_id"] == "estado_contable"
        assert result["company"] == "Acme Corp"

    def test_filename_builder_integration(self):
        """Filename builder works with real analysis data."""
        from filename_builder import build_filename

        analysis = {
            "algorithm_id": "factura",
            "date": "2025-03-15",
            "confidence": 0.95,
            "keywords": ["factura", "mercedes", "servicio"],
        }
        job_config = {
            "agent_config": {
                "filename_format": "{date}_{type}_{issuer}{ext}",
            }
        }

        result = build_filename("original.pdf", analysis, job_config)
        assert result == "2025-03-15_factura_mercedes.pdf"
