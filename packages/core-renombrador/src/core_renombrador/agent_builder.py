"""
Agent Builder — Constructs Agno agents from configuration.
============================================================

Builds Agno Agent instances from job configuration dictionaries.
Handles structured output schemas (DocumentClassification) and
dynamic Pydantic model creation.

:created:   2026-05-05
:filename:  agent_builder.py
:path:      packages/core-renombrador/src/core_renombrador/agent_builder.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import Toolkit

try:
    from .schemas import DocumentClassification
except ImportError:
    DocumentClassification = None

try:
    from .models import FileAnalysis
except ImportError:
    FileAnalysis = None

from .agent_config import AgentConfig

logger = logging.getLogger(__name__)


class AgentBuilder:
    """Constructs Agno Agent instances from job configuration."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()

    def build_agent(
        self,
        job_config: Dict[str, Any],
        db: Optional[Any] = None,
        tools: Optional[List[Union[Toolkit, callable]]] = None,
    ) -> Agent:
        """Build an Agno Agent from a job configuration dictionary."""
        agent_config = job_config.get("agent_config", {})
        model_id = self.config.extract_model_id(job_config)
        model = self.config.resolve_model(model_id)

        agent_params = {
            "model": model,
            "name": job_config.get("name", "DocumentProcessorAgent"),
            "description": job_config.get("description"),
            "instructions": agent_config.get("instructions"),
            "pre_hooks": [],
            "tools": tools or [],
            "db": db,
            "session_id": None,
            "enable_agentic_memory": agent_config.get("memory", {}).get("enable_db_storage", False),
            "enable_user_memories": agent_config.get("memory", {}).get("enable_user_memories", False),
            "reasoning": agent_config.get("reasoning", {}).get("enabled", False),
            "add_history_to_context": agent_config.get("session", {}).get("enable_history", False),
            "num_history_messages": agent_config.get("session", {}).get("num_history_messages", 10),
            "markdown": agent_config.get("output", {}).get("markdown", False),
            "structured_outputs": True,
        }

        output_schema = agent_config.get("output_schema") or agent_config.get("response_model")
        is_classification = (
            "classify" in job_config.get("id", "").lower()
            or (isinstance(output_schema, dict) and "algorithm_id" in output_schema)
            or DocumentClassification is not None
        )

        if is_classification and DocumentClassification is not None:
            logger.info("Using DocumentClassification for structured output")
            agent_params["output_schema"] = DocumentClassification
        elif FileAnalysis is not None:
            logger.info("Using FileAnalysis for structured output")
            agent_params["output_schema"] = FileAnalysis
        elif output_schema:
            if isinstance(output_schema, dict):
                agent_params["output_schema"] = self._create_pydantic_model(output_schema)
            else:
                agent_params["output_schema"] = output_schema

        agent_params = {k: v for k, v in agent_params.items() if v is not None}

        try:
            agent = Agent(**agent_params)
            logger.info(f"Created agent '{agent.name}' with model '{model_id}'")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    def _create_pydantic_model(self, schema: Dict[str, Any]) -> type:
        """Create a Pydantic model from a JSON schema dict."""
        if DocumentClassification is not None:
            logger.info("Using DocumentClassification Pydantic model")
            return DocumentClassification

        logger.warning("DocumentClassification not available, creating dynamic model")
        from pydantic import create_model, ConfigDict

        fields = {}
        type_map = {"str": str, "int": int, "float": float, "bool": bool, "list": list, "dict": dict}

        for field_name, field_info in schema.items():
            if isinstance(field_info, str):
                fields[field_name] = (type_map.get(field_info, str), ...)
            else:
                fields[field_name] = (str, ...)

        OutputModel = create_model("DynamicOutputModel", **fields)
        OutputModel.model_config = ConfigDict(extra="ignore")
        return OutputModel

    def build_with_defaults(self, instructions: str, model_id: str = "gemini-2.5-flash", **kwargs) -> Agent:
        """Create an agent with sensible defaults for quick experimentation."""
        return Agent(model=Gemini(id=model_id), instructions=instructions, **kwargs)
