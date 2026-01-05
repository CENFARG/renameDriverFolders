"""
AgentFactory - Configuración dinámica de agentes Agno
====================================================

Factory pattern para instanciar agentes Agno con configuración
cargada desde base de datos. Usa todas las capacidades de Agno
versión 2.3.9 con las APIs correctas documentadas.

NOTA: Este factory no hardcodea ninguna configuración.
Todo se lee del job config desde database.

:created:   2025-12-03
:filename:  agent_factory.py
:author:    amBotHs + CENF
:version:   2.1.0
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import os
import logging
from typing import Dict, Any, List, Callable, Union, Optional

# Agno 2.3.9 imports - using correct module paths from documentation
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import Toolkit
from agno.guardrails import PIIDetectionGuardrail, PromptInjectionGuardrail

# Import Pydantic model for structured outputs
try:
    from .models import FileAnalysis
except ImportError:
    FileAnalysis = None

logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory para crear agentes Agno con configuración dinámica.
    Factory to create Agno agents with dynamic configuration.
    
    No hardcodea ninguna configuración. Todo se carga desde:
    - Base de datos (jobs table)
    - ConfigManager
    - Argumentos en runtime
    """

    def __init__(
        self,
        database_manager: Optional[Any] = None,
        config_manager: Optional[Any] = None
    ):
        """
        Initialize AgentFactory.

        Args:
            database_manager: DatabaseManager instance for loading agent configs.
            config_manager: ConfigManager instance for default settings.
        """
        self.database_manager = database_manager
        self.config_manager = config_manager

    def create_agent_from_job_config(
        self,
        job_config: Dict[str, Any],
        db: Optional[Any] = None,  # Agno db instance (e.g., SqliteDb)
        tools: Optional[List[Union[Toolkit, callable]]] = None
    ) -> Agent:
        """
        Creates an Agno Agent from a job configuration.
        Crea un Agente Agno desde una configuración de job.

        Args:
            job_config: Job configuration dictionary from database.
                       Diccionario de configuración del job desde BD.
            db: Optional Agno database for session persistence (e.g., SqliteDb).
               Base de datos opcional para persistir sesiones.
            tools: Optional list of tools/toolkits to add to the agent.
                  Lista opcional de herramientas para el agente.

        Returns:
            Configured Agno Agent instance.
            Instancia de Agente Agno configurada.
        """
        agent_config = job_config.get("agent_config", {})
        
        # Extract model configuration
        model_config = agent_config.get("model", {})
        model_id = model_config.get("name", "gemini-1.5-flash")
        
        # Create Gemini model instance
        # Create Gemini model instance
        # According to Agno docs, use Gemini class for Google models
        # Fix: Provide Vertex AI context if available
        project_id = os.environ.get("GCP_PROJECT")
        location = os.environ.get("GCP_LOCATION", "us-central1")

        if project_id:
            logger.info(f"Initializing Vertex AI Gemini model with project={project_id}, location={location}")
            model = Gemini(
                id=model_id,
                project_id=project_id,
                location=location,
                vertexai=True
            )
        else:
            logger.warning("GCP_PROJECT not set. Initializing Gemini in standard mode (API Key might be required).")
            model = Gemini(id=model_id)
        
        # Build Agent parameters dynamically from config
        agent_params = {
            "model": model,
            "name": job_config.get("name", "DocumentProcessorAgent"),
            "description": job_config.get("description"),
            
            # Instructions (system message)
            "instructions": agent_config.get("instructions"),
            
            # Security Guardrails (pre_hooks)
            # Disabled by request to prevent false positives on document PII (2026-01-02)
            "pre_hooks": [
                # PIIDetectionGuardrail(),  # Detect PII in inputs
                # PromptInjectionGuardrail()  # Prevent prompt injection attacks
            ],
            
            # Tools
            "tools": tools or [],
            
            # Session management
            "db": db,
            "session_id": None,  # Lo generará Agno automáticamente
            
            # Memory & Knowledge
            "enable_agentic_memory": agent_config.get("memory", {}).get("enable_db_storage", False),
            "enable_user_memories": agent_config.get("memory", {}).get("enable_user_memories", False),
            
            # Reasoning (si está habilitado)
            "reasoning": agent_config.get("reasoning", {}).get("enabled", False),
            
            # Session history
            "add_history_to_context": agent_config.get("session", {}).get("enable_history", False),
            "num_history_messages": agent_config.get("session", {}).get("num_history_messages", 10),
            
            # Output handling
            "markdown": agent_config.get("output", {}).get("markdown", False),
            "structured_outputs": True,  # Para structured output con Pydantic
        }
        
        # Add optional output schema if defined
        output_schema = agent_config.get("output_schema") or agent_config.get("response_model")
        
        # CENF 2026-01-04: Force FileAnalysis model if it's a file analysis task
        if FileAnalysis is not None:
             logger.info("Forcing FileAnalysis Pydantic model for structured outputs")
             agent_params["output_schema"] = FileAnalysis
        elif output_schema:
            # Convert dict to Pydantic model if necessary
            if isinstance(output_schema, dict):
                agent_params["output_schema"] = self._create_pydantic_model(output_schema)
            else:
                agent_params["output_schema"] = output_schema
        
        # Remove None values to let Agno use defaults
        agent_params = {k: v for k, v in agent_params.items() if v is not None}
        
        try:
            agent = Agent(**agent_params)
            logger.info(f"Created agent '{agent.name}' with model '{model_id}'")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    def _create_pydantic_model(self, schema: Dict[str, Any]) -> type:
        """
        Creates a Pydantic model from a JSON schema dict.
        Crea un modelo Pydantic desde un dict de schema JSON.
        
        Agno requiere output_schema como Type[BaseModel] para structured outputs.
        
        UPDATED: Usa FileAnalysis model si está disponible para mejor validación.
        """
        # If FileAnalysis is imported, use it for file analysis tasks
        if FileAnalysis is not None:
            logger.info("Using FileAnalysis Pydantic model for structured outputs")
            return FileAnalysis
        
        # Fallback: create dynamic model (old behavior)
        logger.warning("FileAnalysis model not available, creating dynamic Pydantic model")
        from pydantic import BaseModel, create_model
        
        fields = {}
        for field_name, field_info in schema.items():
            if isinstance(field_info, str):
                python_type = {
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                }.get(field_info, str)
                fields[field_name] = (python_type, ...)
            else:
                fields[field_name] = (str, ...)
        
        OutputModel = create_model("DynamicOutputModel", **fields)
        
        # Allow extra fields in dynamic model
        from pydantic import ConfigDict
        OutputModel.model_config = ConfigDict(extra='ignore')

        return OutputModel

    def create_agent_with_defaults(
        self,
        instructions: str,
        model_id: str = "gemini-1.5-flash",
        **kwargs
    ) -> Agent:
        """
        Creates an agent with sensible defaults for quick experimentation.
        Crea un agente con defaults razonables para experimentación rápida.
        
        Útil para testing o cuando no hay un job config disponible.
        """
        return Agent(
            model=Gemini(id=model_id),
            instructions=instructions,
            **kwargs
        )

    def load_job_config(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Loads a job configuration from database.
        Carga una configuración de job desde la base de datos.
        """
        if not self.database_manager:
            logger.warning("No DatabaseManager configured")
            return None
        
        try:
            jobs = self.database_manager.find("id", job_id)
            if jobs:
                return jobs[0]
            else:
                logger.warning(f"Job '{job_id}' not found in database")
                return None
        except Exception as e:
            logger.error(f"Error loading job config: {e}")
            return None


# Función helper para uso simple
def create_document_agent(
    job_config: Dict[str, Any],
    database_manager: Optional[Any] = None,
    tools: Optional[List] = None
) -> Agent:
    """
    Shortcut function to create a document processing agent.
    Función de atajo para crear un agente de procesamiento de documentos.
    
    Usage:
        agent = create_document_agent(job_config, db_manager)
        response = agent.run("Analyze this document...")
    """
    factory = AgentFactory(database_manager=database_manager)
    return factory.create_agent_from_job_config(job_config, tools=tools)
