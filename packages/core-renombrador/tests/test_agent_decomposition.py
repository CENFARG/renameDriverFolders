"""
Test: agent_factory decomposition into agent_config + agent_builder.

Verifies that:
1. agent_config.py handles model config, job loading, schema resolution
2. agent_builder.py handles agent construction and Pydantic model creation
3. AgentFactory facade preserves backward-compatible API

:task: T1.5 - Decompose agent_factory.py
:phase: RED (test written first)
"""

import os
import pytest
from unittest.mock import MagicMock, patch


class TestAgentConfig:
    """AgentConfig handles configuration loading and model setup."""

    def test_agent_config_module_exists(self):
        from core_renombrador.agent_config import AgentConfig
        assert AgentConfig is not None

    def test_load_job_config_from_database(self):
        from core_renombrador.agent_config import AgentConfig

        mock_db = MagicMock()
        mock_db.find.return_value = [{"id": "test-job", "name": "Test"}]

        config = AgentConfig(database_manager=mock_db)
        result = config.load_job_config("test-job")

        assert result is not None
        assert result["id"] == "test-job"
        mock_db.find.assert_called_with("id", "test-job")

    def test_load_job_config_not_found(self):
        from core_renombrador.agent_config import AgentConfig

        mock_db = MagicMock()
        mock_db.find.return_value = []

        config = AgentConfig(database_manager=mock_db)
        result = config.load_job_config("nonexistent")

        assert result is None

    def test_load_job_config_no_db(self):
        from core_renombrador.agent_config import AgentConfig

        config = AgentConfig(database_manager=None)
        result = config.load_job_config("any-job")

        assert result is None

    def test_resolve_model_vertex_ai(self):
        from core_renombrador.agent_config import AgentConfig

        config = AgentConfig()
        with patch.dict(os.environ, {"GCP_PROJECT": "test-project", "GCP_LOCATION": "us-central1"}):
            model = config.resolve_model("gemini-2.5-flash")
            assert model is not None

    def test_resolve_model_standard(self):
        from core_renombrador.agent_config import AgentConfig

        config = AgentConfig()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GCP_PROJECT", None)
            model = config.resolve_model("gemini-2.5-flash")
            assert model is not None


class TestAgentBuilder:
    """AgentBuilder constructs Agno agents from config."""

    def test_agent_builder_module_exists(self):
        from core_renombrador.agent_builder import AgentBuilder
        assert AgentBuilder is not None

    def test_build_agent_from_job_config(self):
        from core_renombrador.agent_builder import AgentBuilder

        builder = AgentBuilder()
        job_config = {
            "id": "test-classify",
            "name": "Test Agent",
            "description": "Test",
            "agent_config": {
                "model": {"name": "gemini-2.5-flash"},
                "instructions": "Analyze documents",
            }
        }

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GCP_PROJECT", None)
            agent = builder.build_agent(job_config)

        assert agent is not None

    def test_create_pydantic_model_uses_document_classification(self):
        from core_renombrador.agent_builder import AgentBuilder

        builder = AgentBuilder()
        schema = {"algorithm_id": "str", "date": "str"}
        model_class = builder._create_pydantic_model(schema)
        assert model_class is not None


class TestAgentFactoryFacade:
    """AgentFactory facade preserves backward-compatible API."""

    def test_agent_factory_imports(self):
        from core_renombrador.agent_factory import AgentFactory
        assert AgentFactory is not None

    def test_create_agent_from_job_config_works(self):
        from core_renombrador.agent_factory import AgentFactory

        factory = AgentFactory()
        job_config = {
            "id": "test-job",
            "name": "Test",
            "agent_config": {
                "model": {"name": "gemini-2.5-flash"},
                "instructions": "Test",
            }
        }

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GCP_PROJECT", None)
            agent = factory.create_agent_from_job_config(job_config)

        assert agent is not None

    def test_create_document_agent_helper_works(self):
        from core_renombrador.agent_factory import create_document_agent

        job_config = {
            "id": "classify-test",
            "name": "Test",
            "agent_config": {
                "model": {"name": "gemini-2.5-flash"},
                "instructions": "Classify",
            }
        }

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GCP_PROJECT", None)
            agent = create_document_agent(job_config)

        assert agent is not None

    def test_load_job_config_delegates(self):
        from core_renombrador.agent_factory import AgentFactory

        mock_db = MagicMock()
        mock_db.find.return_value = [{"id": "x", "name": "Y"}]
        factory = AgentFactory(database_manager=mock_db)
        result = factory.load_job_config("x")
        assert result is not None
