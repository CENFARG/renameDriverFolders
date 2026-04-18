# src/core/config_manager.py
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Gestiona la carga y acceso a la configuración de la aplicación.
    La configuración se carga desde un archivo JSON.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializa el ConfigManager cargando la configuración desde el archivo especificado.
        Si no se proporciona una ruta, intenta cargar desde 'config/config.template.json'
        relativo a la raíz del proyecto.
        """
        self._config: Dict[str, Any] = {}
        self.config_path = config_path if config_path else self._get_default_config_path()
        self._load_config()

    def _get_default_config_path(self) -> Path:
        """
        Intenta determinar la ruta por defecto del archivo de configuración.
        Asume que el script se ejecuta desde la raíz del proyecto o desde src/.
        """
        current_file_path = Path(__file__).resolve()
        # Si estamos en src/core/config_manager.py, la raíz es current_file_path.parent.parent.parent
        project_root = current_file_path.parent.parent.parent
        return project_root / "config" / "config.template.json"

    def _load_config(self) -> None:
        """
        Carga la configuración desde el archivo JSON especificado.
        """
        if not self.config_path.exists():
            logger.error(f"Archivo de configuración no encontrado: {self.config_path}")
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"Configuración cargada exitosamente desde {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar el archivo JSON de configuración {self.config_path}: {e}")
            raise ValueError(f"Formato JSON inválido en el archivo de configuración: {e}")
        except Exception as e:
            logger.error(f"Error inesperado al cargar la configuración desde {self.config_path}: {e}")
            raise

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando una clave con notación de punto (ej. "app_info.name").
        """
        parts = key.split('.')
        current_setting = self._config
        for part in parts:
            if isinstance(current_setting, dict) and part in current_setting:
                current_setting = current_setting[part]
            else:
                logger.warning(f"Configuración '{key}' no encontrada. Usando valor por defecto: {default}")
                return default
        return current_setting

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Retorna todas las configuraciones cargadas.
        """
        return self._config

# Example usage (for testing purposes, not part of the class itself)
if __name__ == "__main__":
    # Configurar un logger básico para la prueba
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Crear un archivo de configuración temporal para la prueba
    temp_config_dir = Path(__file__).parent.parent.parent / "config"
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    temp_config_path = temp_config_dir / "test_config.json"
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump({"app_info": {"name": "TestApp", "version": "1.0.0"}, "logging": {"level": "DEBUG"}}, f)

    try:
        # Probar con la ruta por defecto (asumiendo que test_config.json está en config/)
        # Para que funcione el _get_default_config_path, el config.template.json debe existir
        # o se debe pasar la ruta explícitamente.
        # Para esta prueba, pasamos la ruta explícitamente.
        config_manager = ConfigManager(config_path=temp_config_path)
        
        app_name = config_manager.get_setting("app_info.name")
        app_version = config_manager.get_setting("app_info.version")
        log_level = config_manager.get_setting("logging.level")
        non_existent = config_manager.get_setting("non.existent.key", "default_value")

        print(f"App Name: {app_name}")
        print(f"App Version: {app_version}")
        print(f"Log Level: {log_level}")
        print(f"Non-existent key: {non_existent}")

        # Probar con un archivo que no existe
        try:
            ConfigManager(config_path=Path("non_existent.json"))
        except FileNotFoundError:
            print("Manejo correcto de archivo no encontrado.")

        # Probar con JSON inválido
        invalid_json_path = temp_config_dir / "invalid.json"
        with open(invalid_json_path, 'w', encoding='utf-8') as f:
            f.write("{invalid json}")
        try:
            ConfigManager(config_path=invalid_json_path)
        except ValueError:
            print("Manejo correcto de JSON inválido.")

    finally:
        # Limpiar archivos temporales
        temp_config_path.unlink(missing_ok=True)
        invalid_json_path.unlink(missing_ok=True)