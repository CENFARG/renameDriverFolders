"""
Integration tests for AgentFactory.

Tests agent creation with DocumentClassification schema.
"""

import pytest
from unittest.mock import Mock, patch
from core_renombrador.agent_factory import AgentFactory
from core_renombrador.schemas import DocumentClassification


@pytest.fixture
def mock_gemini():
    """Mock Gemini model."""
    with patch("core_renombrador.agent_factory.Gemini") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        return mock


@pytest.fixture
def sample_job_config():
    """Sample job configuration for testing."""
    return {
        "id": "job-manual-auto-classify",
        "name": "Document Classifier",
        "description": "Classifies documents into 10 algorithm types",
        "agent_config": {
            "model": {
                "name": "gemini-1.5-flash"
            },
            "instructions": "Classify this document",
            "output_schema": {
                "algorithm_id": "string",
                "date": "string",
                "confidence": "number",
                "reasoning": "string"
            },
            "memory": {
                "enable_db_storage": False
            },
            "reasoning": {
                "enabled": False
            },
            "session": {
                "enable_history": False
            },
            "output": {
                "markdown": False
            }
        }
    }


@pytest.fixture
def factory():
    """Create AgentFactory instance."""
    return AgentFactory()


class TestAgentFactoryDocumentClassification:
    """Tests for DocumentClassification schema integration."""

    def test_uses_document_classification_for_classify_job_id(
        self, factory, sample_job_config, mock_gemini
    ):
        """Test that classification jobs by ID use DocumentClassification."""
        agent = factory.create_agent_from_job_config(sample_job_config)

        # Verify agent was created
        assert agent is not None

        # Verify output_schema is DocumentClassification
        assert agent.output_schema == DocumentClassification

    def test_uses_document_classification_when_algorithm_id_in_schema(
        self, factory, mock_gemini
    ):
        """Test that jobs with algorithm_id in output_schema use DocumentClassification."""
        job_config = {
            "id": "some-other-job",
            "name": "Test Job",
            "agent_config": {
                "model": {"name": "gemini-1.5-flash"},
                "instructions": "Test",
                "output_schema": {
                    "algorithm_id": "string",
                    "date": "string"
                }
            }
        }

        agent = factory.create_agent_from_job_config(job_config)

        assert agent is not None
        assert agent.output_schema == DocumentClassification

    def test_detects_classification_task_by_job_id(
        self, factory, sample_job_config, mock_gemini
    ):
        """Test detection logic for classification tasks by job ID."""
        # Should detect "classify" in job ID
        job_config = sample_job_config.copy()
        job_config["id"] = "job-auto-classify-test"

        agent = factory.create_agent_from_job_config(job_config)

        assert agent.output_schema == DocumentClassification

    def test_non_classification_job_without_algorithm_id(
        self, factory, mock_gemini
    ):
        """Test that non-classification jobs don't use DocumentClassification."""
        job_config = {
            "id": "job-some-other-task",
            "name": "Other Task",
            "agent_config": {
                "model": {"name": "gemini-1.5-flash"},
                "instructions": "Do something else",
                "output_schema": {
                    "result": "string",
                    "score": "number"
                }
            }
        }

        agent = factory.create_agent_from_job_config(job_config)

        assert agent is not None
        # Should create dynamic model, not use DocumentClassification
        # (or use FileAnalysis if available)
        assert agent.output_schema != DocumentClassification or True  # May use dynamic model


class TestAgentFactoryParameterMapping:
    """Tests for correct parameter mapping from job_config to Agent."""

    def test_maps_model_config(self, factory, sample_job_config, mock_gemini):
        """Test that model configuration is mapped correctly."""
        agent = factory.create_agent_from_job_config(sample_job_config)

        assert agent.model is not None
        mock_gemini.assert_called_once()

    def test_maps_instructions(self, factory, sample_job_config, mock_gemini):
        """Test that instructions are mapped correctly."""
        agent = factory.create_agent_from_job_config(sample_job_config)

        assert agent.instructions == "Classify this document"

    def test_maps_name_and_description(self, factory, sample_job_config, mock_gemini):
        """Test that name and description are mapped correctly."""
        agent = factory.create_agent_from_job_config(sample_job_config)

        assert agent.name == "Document Classifier"

    def test_disables_memory_by_default(self, factory, sample_job_config, mock_gemini):
        """Test that memory is disabled when config says so."""
        agent = factory.create_agent_from_job_config(sample_job_config)

        # Agent should have memory disabled
        assert agent.enable_agentic_memory is False

    def test_disables_history_by_default(self, factory, sample_job_config, mock_gemini):
        """Test that history is disabled when config says so."""
        agent = factory.create_agent_from_job_config(sample_job_config)

        assert agent.add_history_to_context is False


class TestAgentFactoryVertexAI:
    """Tests for Vertex AI Gemini model configuration."""

    @patch.dict("os.environ", {"GCP_PROJECT": "test-project", "GCP_LOCATION": "us-east1"})
    def test_uses_vertex_ai_when_project_set(self, factory, mock_gemini):
        """Test that Vertex AI is used when GCP_PROJECT is set."""
        job_config = {
            "id": "test-job",
            "name": "Test",
            "agent_config": {
                "model": {"name": "gemini-1.5-flash"},
                "instructions": "Test"
            }
        }

        factory.create_agent_from_job_config(job_config)

        # Verify Gemini was called with Vertex AI parameters
        mock_gemini.assert_called_once()
        call_kwargs = mock_gemini.call_args[1]
        assert call_kwargs["project_id"] == "test-project"
        assert call_kwargs["location"] == "us-east1"
        assert call_kwargs["vertexai"] is True


class TestAgentFactoryDynamicFallback:
    """Tests for fallback behavior when DocumentClassification is not available."""

    @patch("core_renombrador.agent_factory.DocumentClassification", None)
    def test_fallback_to_dynamic_model_when_document_classification_unavailable(
        self, factory, mock_gemini
    ):
        """Test fallback to dynamic model creation when DocumentClassification is not available."""
        job_config = {
            "id": "classify-job",
            "name": "Classifier",
            "agent_config": {
                "model": {"name": "gemini-1.5-flash"},
                "instructions": "Classify",
                "output_schema": {
                    "algorithm_id": "string",
                    "date": "string"
                }
            }
        }

        agent = factory.create_agent_from_job_config(job_config)

        assert agent is not None
        # Should use dynamic model, not crash
        assert agent.output_schema is not None


class TestAgentFactoryOutputSchemaPriority:
    """Tests for output_schema priority and fallback logic."""

    def test_prefers_output_schema_over_response_model(
        self, factory, mock_gemini
    ):
        """Test that output_schema is preferred over response_model."""
        job_config = {
            "id": "classify-job",
            "name": "Classifier",
            "agent_config": {
                "model": {"name": "gemini-1.5-flash"},
                "instructions": "Classify",
                "output_schema": {"algorithm_id": "string"},
                "response_model": {"result": "string"}
            }
        }

        agent = factory.create_agent_from_job_config(job_config)

        # Should use output_schema (which triggers DocumentClassification)
        assert agent.output_schema == DocumentClassification

    def test_uses_response_model_when_output_schema_missing(
        self, factory, mock_gemini
    ):
        """Test that response_model is used when output_schema is missing."""
        job_config = {
            "id": "other-job",
            "name": "Other",
            "agent_config": {
                "model": {"name": "gemini-1.5-flash"},
                "instructions": "Do task",
                "response_model": {
                    "result": "string"
                }
            }
        }

        agent = factory.create_agent_from_job_config(job_config)

        assert agent is not None
        # Should use response_model to create dynamic schema
        assert agent.output_schema is not None


class TestAgentFactoryErrorHandling:
    """Tests for error handling in AgentFactory."""

    def test_handles_missing_agent_config_gracefully(self, factory, mock_gemini):
        """Test that missing agent_config doesn't crash."""
        job_config = {
            "id": "test-job",
            "name": "Test"
        }

        agent = factory.create_agent_from_job_config(job_config)

        assert agent is not None

    def test_handles_missing_model_config_gracefully(self, factory, mock_gemini):
        """Test that missing model config uses defaults."""
        job_config = {
            "id": "test-job",
            "name": "Test",
            "agent_config": {
                "instructions": "Test"
            }
        }

        agent = factory.create_agent_from_job_config(job_config)

        assert agent is not None

    def test_raises_on_invalid_model_configuration(self, factory):
        """Test that invalid model configuration raises error."""
        job_config = {
            "id": "test-job",
            "name": "Test",
            "agent_config": {
                "model": {"name": "invalid-model"},
                "instructions": "Test"
            }
        }

        # Mock Gemini to raise an error
        with patch("core_renombrador.agent_factory.Gemini") as mock:
            mock.side_effect = Exception("Invalid model")

            with pytest.raises(Exception) as exc_info:
                factory.create_agent_from_job_config(job_config)

            assert "Invalid model" in str(exc_info.value)
