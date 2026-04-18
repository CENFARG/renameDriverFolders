# src/core/file_manager.py
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class FileManager:
    """
    Gestiona operaciones de archivo de forma genérica para la aplicación.
    Permite definir rutas base configurables para diferentes tipos de archivos.
    """

    def __init__(self, base_path: Union[str, Path], config_manager=None):
        """
        Inicializa el FileManager.
        Args:
            base_path: La ruta base principal para todas las operaciones de archivo.
            config_manager: Opcional. Una instancia de ConfigManager para obtener rutas configurables.
        """
        self.base_path = Path(base_path).resolve()
        self.config_manager = config_manager
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Asegura que el directorio base exista."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directorio base asegurado: {self.base_path}")
        except Exception as e:
            logger.error(f"Error al asegurar el directorio base {self.base_path}: {e}")
            raise

    def get_path(self, config_key: Optional[str] = None, relative_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Obtiene una ruta completa, ya sea desde la configuración o relativa a la ruta base.
        Args:
            config_key: Clave de configuración para obtener una ruta predefinida (ej. "paths.data_dir").
            relative_path: Ruta relativa a la ruta base del FileManager.
        Returns:
            Un objeto Path con la ruta completa y resuelta.
        """
        if config_key and self.config_manager:
            configured_path_str = self.config_manager.get_setting(config_key)
            if configured_path_str:
                path = Path(configured_path_str)
                if not path.is_absolute():
                    return (self.base_path / path).resolve()
                return path.resolve()
            else:
                logger.warning(f"Clave de configuración '{config_key}' no encontrada o vacía. Usando ruta base.")
        
        if relative_path:
            return (self.base_path / relative_path).resolve()
        
        return self.base_path

    def ensure_directory(self, path: Union[str, Path]):
        """Asegura que un directorio específico exista."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directorio asegurado: {path}")
        except Exception as e:
            logger.error(f"Error al asegurar el directorio {path}: {e}")
            raise

    def read_text_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Lee el contenido de un archivo de texto."""
        try:
            content = Path(file_path).read_text(encoding=encoding)
            logger.debug(f"Archivo leído: {file_path}")
            return content
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error al leer el archivo {file_path}: {e}")
            raise

    def write_text_file(self, file_path: Union[str, Path], content: str, encoding: str = 'utf-8'):
        """Escribe contenido en un archivo de texto."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True) # Asegurar que el directorio padre exista
            Path(file_path).write_text(content, encoding=encoding)
            logger.debug(f"Archivo escrito: {file_path}")
        except Exception as e:
            logger.error(f"Error al escribir en el archivo {file_path}: {e}")
            raise

    def read_json_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> Dict[str, Any]:
        """Lee y parsea un archivo JSON."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)
            logger.debug(f"Archivo JSON leído: {file_path}")
            return data
        except FileNotFoundError:
            logger.error(f"Archivo JSON no encontrado: {file_path}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Error de formato JSON en el archivo: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error al leer el archivo JSON {file_path}: {e}")
            raise

    def write_json_file(self, file_path: Union[str, Path], data: Dict[str, Any], encoding: str = 'utf-8', indent: int = 2):
        """Escribe un diccionario en un archivo JSON."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True) # Asegurar que el directorio padre exista
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.debug(f"Archivo JSON escrito: {file_path}")
        except Exception as e:
            logger.error(f"Error al escribir el archivo JSON {file_path}: {e}")
            raise

    def list_files(self, directory_path: Union[str, Path], pattern: str = "*") -> List[Path]:
        """Lista archivos en un directorio que coinciden con un patrón."""
        try:
            return list(Path(directory_path).glob(pattern))
        except Exception as e:
            logger.error(f"Error al listar archivos en {directory_path} con patrón {pattern}: {e}")
            raise

    def copy_file(self, source_path: Union[str, Path], destination_path: Union[str, Path]):
        """Copia un archivo de una ubicación a otra."""
        try:
            Path(destination_path).parent.mkdir(parents=True, exist_ok=True) # Asegurar que el directorio padre exista
            shutil.copy2(source_path, destination_path)
            logger.debug(f"Archivo copiado de {source_path} a {destination_path}")
        except Exception as e:
            logger.error(f"Error al copiar archivo de {source_path} a {destination_path}: {e}")
            raise

    def delete_file(self, file_path: Union[str, Path]):
        """Elimina un archivo."""
        try:
            Path(file_path).unlink(missing_ok=True)
            logger.debug(f"Archivo eliminado: {file_path}")
        except Exception as e:
            logger.error(f"Error al eliminar archivo {file_path}: {e}")
            raise

    def delete_directory(self, directory_path: Union[str, Path]):
        """Elimina un directorio y todo su contenido."""
        try:
            shutil.rmtree(directory_path)
            logger.debug(f"Directorio eliminado: {directory_path}")
        except Exception as e:
            logger.error(f"Error al eliminar directorio {directory_path}: {e}")
            raise

# Example usage (for testing purposes, not part of the class itself)
if __name__ == "__main__":
    import os
    import tempfile
    import shutil
    from src.core.config_manager import ConfigManager # Assuming ConfigManager is available

    # Configurar un logger básico para la prueba
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Crear un directorio temporal para las pruebas
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Directorio temporal para pruebas: {temp_dir}")

    # Crear un config.template.json temporal para la prueba de ConfigManager
    temp_config_dir = Path(__file__).parent.parent.parent / "config"
    temp_config_dir.mkdir(parents=True, exist_ok=True)
    temp_config_path = temp_config_dir / "config.template.json"
    with open(temp_config_path, 'w', encoding='utf-8') as f:
        json.dump({
            "app_info": {"name": "TestApp", "version": "1.0.0"},
            "logging": {"level": "DEBUG", "file": "logs/test_app.log"},
            "paths": {
                "data_dir": "data",
                "output_dir": "output"
            }
        }, f)

    try:
        # Inicializar ConfigManager
        config_manager = ConfigManager(config_path=temp_config_path)

        # Inicializar FileManager con el directorio temporal como base
        file_manager = FileManager(base_path=temp_dir, config_manager=config_manager)

        # --- Probar get_path ---
        data_path = file_manager.get_path(config_key="paths.data_dir")
        output_path = file_manager.get_path(config_key="paths.output_dir")
        relative_file_path = file_manager.get_path(relative_path="my_file.txt")
        print(f"Ruta de datos (desde config): {data_path}")
        print(f"Ruta de salida (desde config): {output_path}")
        print(f"Ruta de archivo relativo: {relative_file_path}")

        # --- Probar ensure_directory ---
        file_manager.ensure_directory(data_path)
        file_manager.ensure_directory(output_path)
        print(f"Directorios {data_path} y {output_path} asegurados.")

        # --- Probar write_text_file y read_text_file ---
        test_text_file = data_path / "test.txt"
        file_manager.write_text_file(test_text_file, "Hola, esto es una prueba de texto.")
        read_content = file_manager.read_text_file(test_text_file)
        print(f"Contenido leído de {test_text_file}: '{read_content}'")

        # --- Probar write_json_file y read_json_file ---
        test_json_file = output_path / "test.json"
        test_data = {"key": "value", "number": 123}
        file_manager.write_json_file(test_json_file, test_data)
        read_json = file_manager.read_json_file(test_json_file)
        print(f"Contenido JSON leído de {test_json_file}: {read_json}")

        # --- Probar list_files ---
        listed_files = file_manager.list_files(data_path, "*.txt")
        print(f"Archivos .txt en {data_path}: {listed_files}")

        # --- Probar copy_file ---
        copied_file = output_path / "copied_test.txt"
        file_manager.copy_file(test_text_file, copied_file)
        print(f"Archivo copiado a {copied_file}")

        # --- Probar delete_file ---
        file_manager.delete_file(test_text_file)
        print(f"Archivo {test_text_file} eliminado.")

    finally:
        # Limpiar el directorio temporal
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"Directorio temporal {temp_dir} eliminado.")
        # Limpiar el config.template.json temporal
        temp_config_path.unlink(missing_ok=True)
