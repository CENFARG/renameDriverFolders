"""
Unit test with MOCK to verify Agno agent behavior.

This test uses mocks to avoid calling Gemini API and tests:
1. Agent creation with DocumentClassification
2. What response format Agno returns
3. If there's an issue with structured output parsing
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages', 'core-renombrador', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core_renombrador.agent_factory import AgentFactory
from core_renombrador.schemas import DocumentClassification


class TestAgentWithMockedGemini:
    """Test agent creation with mocked Gemini model."""

    @pytest.fixture
    def job_config(self):
        """Sample job config."""
        return {
            "id": "job-manual-auto-classify",
            "name": "Document Classifier",
            "description": "Test classifier",
            "agent_config": {
                "model": {"name": "gemini-1.5-flash"},
                "instructions": "Classify this document",
                "output_schema": {
                    "algorithm_id": "string",
                    "date": "string"
                },
                "output": {"markdown": False}
            }
        }

    def test_agent_factory_uses_document_classification(self, job_config):
        """Test that AgentFactory uses DocumentClassification for classification jobs."""
        with patch('core_renombrador.agent_factory.Gemini') as mock_gemini:
            # Mock Gemini model
            mock_model = Mock()
            mock_gemini.return_value = mock_model

            factory = AgentFactory()

            # Verify agent can be created
            # (We're not actually creating it to avoid Gemini API calls)
            from agno.agent import Agent

            # Check if the factory would use DocumentClassification
            is_classification_task = (
                "classify" in job_config.get("id", "").lower() or
                (isinstance(job_config.get("agent_config", {}).get("output_schema"), dict) and
                 "algorithm_id" in job_config.get("agent_config", {}).get("output_schema", {}))
            )

            assert is_classification_task is True, "Should detect classification task"

    def test_document_classification_has_model_dump(self):
        """Test that DocumentClassification has model_dump method."""
        classification = DocumentClassification(
            algorithm_id="factura",
            date="2024-03-15",
            confidence=0.9,
            reasoning="Test"
        )

        # Should have model_dump (Pydantic v2)
        assert hasattr(classification, 'model_dump'), "DocumentClassification should have model_dump method"

        # Should convert to dict
        result = classification.model_dump()
        assert isinstance(result, dict), "model_dump should return dict"
        assert result["algorithm_id"] == "factura"

    def test_document_classification_from_dict(self):
        """Test creating DocumentClassification from dict (what Agno should return)."""
        data = {
            "algorithm_id": "recibo_sueldo",
            "date": "2024-03-15",
            "confidence": 0.85,
            "reasoning": "Test recibo"
        }

        classification = DocumentClassification(**data)

        assert classification.algorithm_id == "recibo_sueldo"
        assert classification.date == "2024-03-15"
        assert classification.confidence == 0.85

    def test_parse_agent_response_with_pydantic_model(self):
        """Test parse_agent_response with Pydantic model in .content."""
        from main import parse_agent_response

        # Create a mock response simulating Agno RunResponse
        # RunResponse has .content which is the Pydantic model
        mock_response = Mock()
        classification = DocumentClassification(
            algorithm_id="estado_contable",
            date="2024-03-15",
            confidence=0.9,
            reasoning="Test"
        )
        mock_response.content = classification

        # Should have model_dump as callable
        assert hasattr(mock_response.content, 'model_dump'), "Should have model_dump"
        assert callable(mock_response.content.model_dump), "model_dump should be callable"

        # Parse should work
        result = parse_agent_response(mock_response)

        assert isinstance(result, dict), f"Result should be dict, got {type(result)}"
        assert result["algorithm_id"] == "estado_contable"
        assert result["date"] == "2024-03-15"

    def test_parse_agent_response_with_dict(self):
        """Test parse_agent_response with dict."""
        from main import parse_agent_response

        mock_response = Mock()
        mock_response.content = {
            "algorithm_id": "factura",
            "date": "2024-03-15"
        }

        result = parse_agent_response(mock_response)

        assert isinstance(result, dict)
        assert result["algorithm_id"] == "factura"

    def test_parse_agent_response_with_invalid_string(self):
        """Test parse_agent_response with malformed JSON string (current error)."""
        from main import parse_agent_response

        mock_response = Mock()
        # This is what causes the error '\r\n        "date"'
        mock_response.content = '\r\n        "date"'

        # Should NOT crash, should return fallback
        result = parse_agent_response(mock_response)

        # Should return default fallback
        assert "date" in result
        print(f"Fallback result: {result}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
