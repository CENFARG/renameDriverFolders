# src/core/logger_manager.py
import logging
from pathlib import Path
from src.core.config_manager import ConfigManager # Assuming ConfigManager is in the same core module

class LoggerManager:
    """
    Gestiona la configuración centralizada del sistema de logging de la aplicación.
    """
    _initialized = False

    @classmethod
    def initialize(cls, config_manager: ConfigManager):
        """
        Inicializa el sistema de logging de la aplicación.
        Debe llamarse una única vez al inicio de la aplicación.
        """
        if cls._initialized:
            return

        log_level_str = config_manager.get_setting("logging.level", "INFO").upper()
        log_file_path_str = config_manager.get_setting("logging.file", "logs/app.log")

        numeric_level = getattr(logging, log_level_str, None)
        if not isinstance(numeric_level, int):
            raise ValueError(f"Nivel de log inválido: {log_level_str}")

        # Crear el directorio de logs si no existe
        log_file_path = Path(log_file_path_str)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Configuración básica del logger raíz
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler() # Para que también se muestre en consola
            ]
        )
        cls._initialized = True
        logging.getLogger(__name__).info(f"Sistema de logging inicializado con nivel {log_level_str} y archivo {log_file_path}")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Obtiene una instancia de logger con el nombre especificado.
        """
        if not LoggerManager._initialized:
            # Esto es un fallback, idealmente initialize() debería llamarse primero.
            # Si no se ha inicializado, se usará la configuración por defecto de logging.
            logging.warning("LoggerManager no ha sido inicializado. Usando configuración de logging por defecto.")
        return logging.getLogger(name)

# Example usage (for testing purposes, not part of the class itself)
if __name__ == "__main__":
    # Crear una instancia de ConfigManager para la prueba
    # Asegúrate de que config/config.template.json exista para esta prueba
    # o crea un archivo temporal como en el ejemplo de ConfigManager
    
    # Para esta prueba, asumimos que config.template.json ya existe en la ruta esperada
    # o creamos uno temporal para la prueba.
    
    # Crear un archivo de configuración temporal para la prueba
    temp_config_dir = Path(__file__).parent.parent.parent / "config"
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    temp_config_path = temp_config_dir / "test_config_logger.json"
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump({"logging": {"level": "DEBUG", "file": "logs/test_app.log"}}, f)

    try:
        test_config_manager = ConfigManager(config_path=temp_config_path)
        LoggerManager.initialize(test_config_manager)

        app_logger = LoggerManager.get_logger("MyApp")
        app_logger.debug("Este es un mensaje de depuración.")
        app_logger.info("Este es un mensaje informativo.")
        app_logger.warning("Este es un mensaje de advertencia.")
        app_logger.error("Este es un mensaje de error.")
        app_logger.critical("Este es un mensaje crítico.")

        another_logger = LoggerManager.get_logger("AnotherModule")
        another_logger.info("Mensaje desde otro módulo.")

    finally:
        # Limpiar archivos temporales y de log
        temp_config_path.unlink(missing_ok=True)
        log_file_to_clean = Path(__file__).parent.parent.parent / "logs" / "test_app.log"
        log_file_to_clean.unlink(missing_ok=True)
