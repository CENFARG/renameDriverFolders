"""
ConfigManager con estrategia híbrida de configuración
=====================================================

Prioridad de configuración:
1. Variables de entorno (highest priority - for overrides)
2. Database (app_config table)
3. config.json file (fallback/local dev)

:created:   2025-12-05
:filename:  config_manager.py
:author:    amBotHs + CENF
:version:   2.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages application configuration with a hybrid strategy.
    Maneja la configuración de la aplicación con estrategia híbrida.
    
    Priority order:
    1. Environment variables (os.environ)
    2. Database (via DatabaseManager)
    3. Local config.json file
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        database_manager: Optional[Any] = None,
        env_prefix: str = "RENOMBRADOR_"
    ):
        """
        Initialize ConfigManager.

        Args:
            config_path: Path to config.json file.
                        Ruta al archivo config.json.
            database_manager: Optional DatabaseManager instance for config from DB.
                             Instancia opcional de DatabaseManager para config desde BD.
            env_prefix: Prefix for environment variables (e.g., "RENOMBRADOR_DB_HOST").
                       Prefijo para variables de entorno.
        """
        self._file_config: Dict[str, Any] = {}
        self._db_config_cache: Dict[str, Any] = {}
        self.database_manager = database_manager
        self.env_prefix = env_prefix
        
        # Setup config file path
        if isinstance(config_path, str):
            self.config_path = Path(config_path)
        elif config_path is None:
            self.config_path = Path.cwd() / "config.json"
        else:
            self.config_path = config_path
            
        self._load_file_config()
        if self.database_manager:
            self._load_db_config()

    def _load_file_config(self) -> None:
        """
        Loads configuration from JSON file.
        Carga configuración desde archivo JSON.
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            self._file_config = {}
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._file_config = json.load(f)
            logger.info(f"File config loaded from {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON {self.config_path}: {e}")
            self._file_config = {}
        except Exception as e:
            logger.error(f"Error loading config {self.config_path}: {e}")
            self._file_config = {}

    def _load_db_config(self) -> None:
        """
        Loads configuration from database into cache.
        Carga configuración desde base de datos en caché.
        """
        if not self.database_manager:
            return

        try:
            # Assume database has an 'app_config' collection/table
            # with records like: {"key": "gemini.model_name", "value": "gemini-2.0-flash-exp"}
            configs = self.database_manager.find_all()
            
            # Build nested dict from dot-notation keys
            for record in configs:
                if "key" in record and "value" in record:
                    self._set_nested_value(self._db_config_cache, record["key"], record["value"])
            
            logger.info(f"Loaded {len(configs)} config entries from database")
        except Exception as e:
            logger.error(f"Error loading config from database: {e}")
            self._db_config_cache = {}

    def _set_nested_value(self, config_dict: Dict, key_path: str, value: Any) -> None:
        """
        Sets a value in a nested dictionary using dot notation.
        Establece un valor en un diccionario anidado usando notación de punto.
        
        Example: _set_nested_value(d, "a.b.c", 42) -> d["a"]["b"]["c"] = 42
        """
        parts = key_path.split(".")
        current = config_dict
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Gets a configuration value using hybrid strategy.
        Obtiene un valor de configuración usando estrategia híbrida.

        Priority:
        1. Environment variable (e.g., RENOMBRADOR_GEMINI_MODEL_NAME for "gemini.model_name")
        2. Database config
        3. File config
        4. Default value

        Args:
            key: Configuration key in dot notation (e.g., "gemini.model_name").
                Clave de configuración en notación de punto.
            default: Default value if not found.
                    Valor por defecto si no se encuentra.

        Returns:
            Configuration value or default.
            Valor de configuración o valor por defecto.
        """
        # 1. Check environment variable first
        env_key = self._key_to_env_var(key)
        env_value = os.environ.get(env_key)
        if env_value is not None:
            logger.debug(f"Config '{key}' from env var: {env_key}")
            return self._parse_env_value(env_value)

        # 2. Check database config
        db_value = self._get_from_dict(self._db_config_cache, key)
        if db_value is not None:
            logger.debug(f"Config '{key}' from database")
            return db_value

        # 3. Check file config
        file_value = self._get_from_dict(self._file_config, key)
        if file_value is not None:
            logger.debug(f"Config '{key}' from file")
            return file_value

        # 4. Return default
        logger.debug(f"Config '{key}' not found, using default: {default}")
        return default

    def _key_to_env_var(self, key: str) -> str:
        """
        Converts dot notation key to environment variable name.
        Convierte clave en notación de punto a nombre de variable de entorno.
        
        Example: "gemini.model_name" -> "RENOMBRADOR_GEMINI_MODEL_NAME"
        """
        return self.env_prefix + key.replace(".", "_").upper()

    def _parse_env_value(self, value: str) -> Any:
        """
        Parses environment variable string to appropriate type.
        Parsea string de variable de entorno al tipo apropiado.
        
        Tries to parse as JSON first, falls back to string.
        """
        # Remove quotes and whitespace
        value = value.strip().strip("'\"")
        
        # Try to parse as JSON (handles lists, dicts, booleans, numbers)
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            # Return as string
            return value

    def _get_from_dict(self, config_dict: Dict, key: str) -> Any:
        """
        Gets value from nested dict using dot notation.
        Obtiene valor de diccionario anidado usando notación de punto.
        """
        parts = key.split(".")
        current = config_dict
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current

    def reload_db_config(self) -> None:
        """
        Reloads configuration from database.
        Recarga configuración desde base de datos.
        
        Useful for runtime config updates without restarting.
        """
        if self.database_manager:
            self._db_config_cache = {}
            self._load_db_config()
            logger.info("Database configuration reloaded")
        else:
            logger.warning("Cannot reload DB config: DatabaseManager not configured")

    def get_all_config(self) -> Dict[str, Any]:
        """
        Returns merged configuration from all sources.
        Retorna configuración fusionada de todas las fuentes.
        
        Useful for debugging. File config is merged with DB config.
        """
        merged = {}
        merged.update(self._file_config)
        merged.update(self._db_config_cache)
        return merged
