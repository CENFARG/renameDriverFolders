# packages/core-renombrador/src/core_renombrador/logger_manager.py
import logging
from pathlib import Path
from .config_manager import ConfigManager

class LoggerManager:
    _initialized = False

    @classmethod
    def initialize(cls, config_manager: ConfigManager):
        if cls._initialized:
            return
            
        log_level_str = config_manager.get_setting("logging.level", "INFO").upper()
        log_file_path_str = config_manager.get_setting("logging.file", "logs/app.log")
        
        numeric_level = getattr(logging, log_level_str, None)
        if not isinstance(numeric_level, int):
            logging.basicConfig(level=logging.INFO)
            logging.warning(f"Nivel de log inválido: {log_level_str}. Usando INFO por defecto.")
        else:
            log_file_path = Path(log_file_path_str)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            logging.basicConfig(
                level=numeric_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file_path, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            
        cls._initialized = True
        logging.getLogger(__name__).info(f"Logging inicializado (nivel {log_level_str}, archivo {log_file_path_str})")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        if not LoggerManager._initialized:
            logging.basicConfig(level=logging.INFO)
            logging.getLogger(__name__).warning("LoggerManager no inicializado. Usando config básica.")
        return logging.getLogger(name)
