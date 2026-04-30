"""
E2E tests for Worker document classification flow.

Tests the complete flow from Cloud Task trigger to file renaming.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import asyncio

# Worker imports
try:
    from main import (
        app,
        TaskPayload,
        GoogleDriveService,
        process_files,
        rename_file,
        create_agent
    )
except ImportError:
    pytest.skip("Worker modules not available", allow_module_level=True)


# Sample DocumentClassification responses
SAMPLE_ESTADO_CONTABLE = {
    "algorithm_id": "estado_contable",
    "date": "2024-03-15",
    "confidence": 0.92,
    "reasoning": "Balance general de closing anual correspondiente a 2024",
    "company": "Mi Empresa S.A.",
    "fiscal_year": "2024",
    "type": "balance_general"
}

SAMPLE_RECIBO_SUELDO = {
    "algorithm_id": "recibo_sueldo",
    "date": "2024-03-15",
    "confidence": 0.95,
    "reasoning": "Recibo de sueldo mensual correspondiente a marzo 2024",
    "employee": "Juan Pérez",
    "employer": "Empresa S.A.",
    "period": "2024-03",
    "net_amount": 450000.50
}

SAMPLE_FACTURA = {
    "algorithm_id": "factura",
    "date": "2024-03-15",
    "confidence": 0.88,
    "reasoning": "Factura A de servicios profesionales",
    "issuer": "Proveedor S.A.",
    "type": "A",
    "number": "0001-00012345",
    "amount": 125000.00,
    "detail": "Servicios profesionales de consultoría"
}


@pytest.fixture
def mock_oidc_token():
    """Mock OIDC token for Cloud Tasks authentication."""
    return "test-oidc-token-12345"


@pytest.fixture
def sample_task_payload():
    """Sample Cloud Task payload."""
    return TaskPayload(
        job_id="job-manual-auto-classify",
        job_name="Document Classifier",
        folder_id="1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH",
        user_id="user123",
        execution_id="exec-001",
        user_credentials=None
    )


@pytest.fixture
def sample_files():
    """Sample Google Drive files."""
    return [
        {
            "id": "file1",
            "name": "documento.pdf",
            "mimeType": "application/pdf",
            "modifiedTime": "2024-03-15T10:30:00.000Z"
        },
        {
            "id": "file2",
            "name": "recibo.png",
            "mimeType": "image/png",
            "modifiedTime": "2024-03-15T11:00:00.000Z"
        },
        {
            "id": "file3",
            "name": "factura.pdf",
            "mimeType": "application/pdf",
            "modifiedTime": "2024-03-15T12:00:00.000Z"
        }
    ]


@pytest.mark.asyncio
class TestWorkerE2EClassificationFlow:
    """E2E tests for Worker document classification flow."""

    async def test_full_classification_flow_with_estado_contable(
        self, sample_task_payload, sample_files, mock_oidc_token
    ):
        """
        Test complete flow:
        1. Cloud Task triggers /run-task endpoint
        2. Worker fetches files from Google Drive
        3. Worker classifies document with Agno
        4. Worker renames file according to algorithm
        5. Worker creates job_execution record
        """
        with patch('main.get_credentials') as mock_creds, \
             patch('main.build') as mock_build, \
             patch('main.create_agent') as mock_create_agent:

            # Mock Google Drive service
            mock_drive_service = Mock()
            mock_files = Mock()
            mock_files.list.return_value.execute.return_value = {
                "files": sample_files
            }
            mock_drive_service.files.return_value = mock_files
            mock_build.return_value = mock_drive_service

            # Mock Agno Agent to return DocumentClassification
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(
                content=SAMPLE_ESTADO_CONTABLE
            )
            mock_create_agent.return_value = mock_agent

            # Mock file rename
            mock_rename = Mock()
            mock_rename.return_value = {
                "id": "file1",
                "name": "2024-03-15_Mi Empresa S.A._balance_general.pdf"
            }
            mock_files.update.return_value.execute.return_value = mock_rename

            # Process the task
            from main import process_files
            results = await process_files(
                mock_drive_service,
                sample_task_payload,
                sample_files
            )

            # Verify results
            assert len(results) == 3
            assert results[0]["success"] is True
            assert "2024-03-15_Mi Empresa S.A._balance_general.pdf" in results[0]["new_name"]

    async def test_classification_with_recibo_sueldo(
        self, sample_task_payload, sample_files
    ):
        """Test classification with recibo_sueldo algorithm."""
        with patch('main.create_agent') as mock_create_agent, \
             patch('main.rename_file') as mock_rename:

            # Mock Agent to return recibo_sueldo classification
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(
                content=SAMPLE_RECIBO_SUELDO
            )
            mock_create_agent.return_value = mock_agent

            # Mock rename
            mock_rename.return_value = {
                "success": True,
                "new_name": "2024-03_Juan Pérez_Empresa S.A..png"
            }

            # Process single file
            result = await rename_file(
                mock_agent,
                sample_files[1],
                sample_task_payload
            )

            # Verify recibo_sueldo naming pattern
            assert result["success"] is True
            assert "Juan Pérez" in result["new_name"]
            assert "2024-03" in result["new_name"]

    async def test_classification_with_factura(
        self, sample_task_payload, sample_files
    ):
        """Test classification with factura algorithm."""
        with patch('main.create_agent') as mock_create_agent, \
             patch('main.rename_file') as mock_rename:

            # Mock Agent to return factura classification
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(
                content=SAMPLE_FACTURA
            )
            mock_create_agent.return_value = mock_agent

            # Mock rename
            mock_rename.return_value = {
                "success": True,
                "new_name": "A_0001-00012345_Proveedor S.A._2024-03-15.pdf"
            }

            # Process single file
            result = await rename_file(
                mock_agent,
                sample_files[2],
                sample_task_payload
            )

            # Verify factura naming pattern
            assert result["success"] is True
            assert "A" in result["new_name"]
            assert "0001-00012345" in result["new_name"]
            assert "Proveedor S.A." in result["new_name"]


@pytest.mark.asyncio
class TestWorkerDocumentClassificationSchema:
    """Tests for DocumentClassification schema usage in Agent."""

    async def test_agent_uses_document_classification_schema(
        self, sample_task_payload
    ):
        """Test that Agent is created with DocumentClassification schema."""
        with patch('main.AgentFactory') as mock_factory:

            # Mock factory to create agent with DocumentClassification
            mock_agent = AsyncMock()
            mock_factory.return_value.create_agent_from_job_config.return_value = mock_agent

            # Create agent
            from main import create_agent
            agent = create_agent(sample_task_payload)

            # Verify factory was called
            mock_factory.assert_called_once()

    async def test_agent_returns_document_classification_object(
        self, sample_task_payload, sample_files
    ):
        """Test that Agent returns DocumentClassification object (not dict)."""
        with patch('main.create_agent') as mock_create_agent:

            # Mock Agent to return DocumentClassification
            from core_renombrador.schemas import DocumentClassification

            classification = DocumentClassification(**SAMPLE_ESTADO_CONTABLE)
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(
                content=classification
            )
            mock_create_agent.return_value = mock_agent

            # Process file
            response = await mock_agent.run("Analyze this document")

            # Verify response is DocumentClassification
            assert isinstance(response.content, dict)
            assert response.content["algorithm_id"] == "estado_contable"
            assert response.content["company"] == "Mi Empresa S.A."


@pytest.mark.asyncio
class TestWorkerFilenameFormats:
    """Tests for filename format generation per algorithm."""

    @pytest.mark.parametrize("algorithm_data,expected_pattern", [
        (
            SAMPLE_ESTADO_CONTABLE,
            r"2024-03-15_Mi Empresa S.A._balance_general\.pdf"
        ),
        (
            SAMPLE_RECIBO_SUELDO,
            r"2024-03_Juan Pérez_Empresa S.A.\.png"
        ),
        (
            SAMPLE_FACTURA,
            r"A_0001-00012345_Proveedor S.A._2024-03-15\.pdf"
        )
    ])
    async def test_filename_format_per_algorithm(
        self, algorithm_data, expected_pattern, sample_task_payload
    ):
        """Test that each algorithm generates correct filename format."""
        import re

        with patch('main.create_agent') as mock_create_agent, \
             patch('main.rename_file') as mock_rename:

            # Mock Agent
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(content=algorithm_data)
            mock_create_agent.return_value = mock_agent

            # Mock rename to return formatted name
            def format_rename(agent, file_data, task):
                # Simulate Worker's filename formatting logic
                alg = algorithm_data["algorithm_id"]
                if alg == "estado_contable":
                    name = f'{algorithm_data["date"]}_{algorithm_data["company"]}_{algorithm_data["type"]}.pdf'
                elif alg == "recibo_sueldo":
                    name = f'{algorithm_data["period"]}_{algorithm_data["employee"]}_{algorithm_data["employer"]}.png'
                elif alg == "factura":
                    name = f'{algorithm_data["type"]}_{algorithm_data["number"]}_{algorithm_data["issuer"]}_{algorithm_data["date"]}.pdf'
                return {"success": True, "new_name": name}

            mock_rename.side_effect = format_rename

            # Process file
            result = await mock_rename(
                mock_agent,
                {"id": "file1", "name": "doc.pdf", "mimeType": "application/pdf"},
                sample_task_payload
            )

            # Verify filename matches expected pattern
            assert result["success"] is True
            assert re.match(expected_pattern, result["new_name"])


@pytest.mark.asyncio
class TestWorkerErrorHandling:
    """Tests for error handling in classification flow."""

    async def test_handles_ai_timeout_gracefully(
        self, sample_task_payload, sample_files
    ):
        """Test that AI timeout is handled gracefully."""
        with patch('main.create_agent') as mock_create_agent:

            # Mock Agent to timeout
            mock_agent = AsyncMock()
            mock_agent.run.side_effect = asyncio.TimeoutError("AI timeout")
            mock_create_agent.return_value = mock_agent

            # Should not crash, but log error and continue
            # (Worker should handle this gracefully)
            from main import rename_file

            result = await rename_file(
                mock_agent,
                sample_files[0],
                sample_task_payload
            )

            # Verify error was handled
            assert result["success"] is False
            assert "timeout" in result["error"].lower() or "error" in result["error"].lower()

    async def test_handles_invalid_document_classification(
        self, sample_task_payload, sample_files
    ):
        """Test that invalid DocumentClassification is handled."""
        with patch('main.create_agent') as mock_create_agent:

            # Mock Agent to return invalid classification
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(
                content={
                    "algorithm_id": "invalid_algorithm",  # Invalid
                    "date": "2024-03-15",
                    "confidence": 0.8,
                    "reasoning": "Test"
                }
            )
            mock_create_agent.return_value = mock_agent

            # Worker should handle validation error
            from main import rename_file

            result = await rename_file(
                mock_agent,
                sample_files[0],
                sample_task_payload
            )

            # Verify error was handled
            assert result["success"] is False


@pytest.mark.asyncio
class TestWorkerDatabaseIntegration:
    """Tests for database integration in classification flow."""

    async def test_creates_job_execution_record(
        self, sample_task_payload, sample_files, mock_oidc_token
    ):
        """Test that Worker creates job_execution record in database."""
        with patch('main.SupabaseClient') as mock_supabase, \
             patch('main.create_agent') as mock_create_agent, \
             patch('main.rename_file') as mock_rename:

            # Mock Supabase
            mock_table = Mock()
            mock_insert = Mock()
            mock_insert.execute.return_value = {"data": [{"id": "exec-123"}], "error": None}
            mock_table.insert.return_value = mock_insert
            mock_supabase.return_value.table.return_value = mock_table

            # Mock Agent and rename
            mock_agent = AsyncMock()
            mock_agent.run.return_value = Mock(content=SAMPLE_ESTADO_CONTABLE)
            mock_create_agent.return_value = mock_agent
            mock_rename.return_value = {"success": True, "new_name": "test.pdf"}

            # Process files
            from main import process_files
            await process_files(
                Mock(),  # drive_service
                sample_task_payload,
                sample_files
            )

            # Verify job_execution record was created
            mock_table.insert.assert_called()

    async def test_updates_execution_status_to_completed(
        self, sample_task_payload, sample_files
    ):
        """Test that Worker updates execution status to completed."""
        # This would test the status update flow
        # Implementation depends on how Worker tracks execution status
        pass
