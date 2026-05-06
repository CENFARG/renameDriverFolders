"""
Agent Factory — Facade for agent creation.
===========================================

Delegates to AgentConfig (config loading, model resolution) and
AgentBuilder (agent construction). Backward-compatible API.

:created:   2025-12-03
:updated:   2026-05-05
:filename:  agent_factory.py
:path:      packages/core-renombrador/src/core_renombrador/agent_factory.py
:author:    amBotHs + CENF
:version:   3.0.0
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import logging
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.tools import Toolkit

from .agent_config import AgentConfig
from .agent_builder import AgentBuilder

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Facade for creating Agno agents with dynamic configuration.

    Delegates to:
    - AgentConfig: job loading, model resolution
    - AgentBuilder: agent construction, schema handling
    """

    def __init__(
        self,
        database_manager: Optional[Any] = None,
        config_manager: Optional[Any] = None,
    ):
        self._config = AgentConfig(
            database_manager=database_manager,
            config_manager=config_manager,
        )
        self._builder = AgentBuilder(config=self._config)
        self.database_manager = database_manager
        self.config_manager = config_manager

    def create_agent_from_job_config(
        self,
        job_config: Dict[str, Any],
        db: Optional[Any] = None,
        tools: Optional[List[Union[Toolkit, callable]]] = None,
    ) -> Agent:
        """Create an Agno Agent from a job configuration."""
        return self._builder.build_agent(job_config, db=db, tools=tools)

    def create_agent_with_defaults(
        self, instructions: str, model_id: str = "gemini-2.5-flash", **kwargs
    ) -> Agent:
        """Create an agent with sensible defaults."""
        return self._builder.build_with_defaults(instructions, model_id=model_id, **kwargs)

    def load_job_config(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load a job configuration from database."""
        return self._config.load_job_config(job_id)


def create_document_agent(
    job_config: Dict[str, Any],
    database_manager: Optional[Any] = None,
    tools: Optional[List] = None,
) -> Agent:
    """Shortcut to create a document processing agent."""
    factory = AgentFactory(database_manager=database_manager)
    return factory.create_agent_from_job_config(job_config, tools=tools)
