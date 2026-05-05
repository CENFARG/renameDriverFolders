"""
Test: Worker AI Classifier extraction (T2.5).

Verifies:
1. parse_agent_response() handles Pydantic models (v2 + v1)
2. parse_agent_response() handles dict responses
3. parse_agent_response() handles string/JSON responses
4. parse_agent_response() provides fallback on failure

:task: T2.5 - Extract Worker AI Classifier
:phase: RED (test written first)
"""

import pytest
from unittest.mock import MagicMock


class TestParseAgentResponse:
    """parse_agent_response() extracts structured data from AI agent responses."""

    def test_ai_classifier_module_exists(self):
        from ai_classifier import parse_agent_response
        assert parse_agent_response is not None

    def test_pydantic_v2_model(self):
        """Should handle RunResponse with Pydantic v2 .model_dump()."""
        from ai_classifier import parse_agent_response

        mock_content = MagicMock()
        mock_content.model_dump.return_value = {
            "algorithm_id": "factura",
            "date": "2025-03-15",
            "confidence": 0.95,
            "reasoning": "Invoice detected",
        }

        mock_response = MagicMock()
        mock_response.content = mock_content

        result = parse_agent_response(mock_response)
        assert result["algorithm_id"] == "factura"
        assert result["date"] == "2025-03-15"

    def test_pydantic_v1_model(self):
        """Should handle Pydantic v1 .dict() models."""
        from ai_classifier import parse_agent_response

        mock_content = MagicMock(spec=["dict"])
        mock_content.dict.return_value = {
            "algorithm_id": "recibo_sueldo",
            "date": "2025-02-01",
            "confidence": 0.88,
            "reasoning": "Pay stub",
        }
        # Remove model_dump to simulate v1
        del mock_content.model_dump

        mock_response = MagicMock()
        mock_response.content = mock_content

        result = parse_agent_response(mock_response)
        assert result["algorithm_id"] == "recibo_sueldo"

    def test_dict_content(self):
        """Should handle dict content directly."""
        from ai_classifier import parse_agent_response

        mock_response = MagicMock()
        mock_response.content = {
            "algorithm_id": "estado_contable",
            "date": "2025-01-01",
            "confidence": 0.9,
            "reasoning": "Balance sheet",
        }

        result = parse_agent_response(mock_response)
        assert result["algorithm_id"] == "estado_contable"

    def test_string_json_content(self):
        """Should parse JSON from string content."""
        from ai_classifier import parse_agent_response

        mock_response = MagicMock()
        mock_response.content = '{"algorithm_id": "impuesto", "date": "2025-04-01", "confidence": 0.7, "reasoning": "Tax form"}'

        result = parse_agent_response(mock_response)
        assert result["algorithm_id"] == "impuesto"

    def test_string_json_with_code_block(self):
        """Should extract JSON from markdown code blocks."""
        from ai_classifier import parse_agent_response

        mock_response = MagicMock()
        mock_response.content = '```json\n{"algorithm_id": "seguro", "date": "2025-05-01", "confidence": 0.8, "reasoning": "Insurance"}\n```'

        result = parse_agent_response(mock_response)
        assert result["algorithm_id"] == "seguro"

    def test_fallback_on_unparseable_response(self):
        """Should return fallback dict when response cannot be parsed."""
        from ai_classifier import parse_agent_response

        mock_response = MagicMock(spec=[])
        del mock_response.content

        result = parse_agent_response(mock_response)
        assert result["algorithm_id"] == "unknown"
        assert result["confidence"] == 0.0
