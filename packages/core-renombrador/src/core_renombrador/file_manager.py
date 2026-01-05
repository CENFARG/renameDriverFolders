# packages/core-renombrador/src/core_renombrador/file_manager.py

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_path: Union[str, Path], config_manager=None):
        self.base_path = Path(base_path).resolve()
        self.config_manager = config_manager
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error al asegurar directorio base {self.base_path}: {e}")
            raise

    def get_path(self, config_key: Optional[str] = None, relative_path: Optional[str] = None) -> Path:
        if config_key and self.config_manager:
            path_str = self.config_manager.get_setting(config_key)
            if path_str:
                return Path(path_str)
        if relative_path:
            return self.base_path / relative_path
        raise ValueError("Se debe proporcionar config_key o relative_path.")

    def read_text_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        try:
            return Path(file_path).read_text(encoding=encoding)
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise

    def write_text_file(self, file_path: Union[str, Path], content: str, encoding: str = 'utf-8'):
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_text(content, encoding=encoding)
        except Exception as e:
            logger.error(f"Error al escribir archivo {file_path}: {e}")
            raise
    
    def read_json_file(self, file_path: Union[str, Path]) -> Any:
        content = self.read_text_file(file_path)
        return json.loads(content)

    def write_json_file(self, file_path: Union[str, Path], data: Any):
        content = json.dumps(data, indent=4)
        self.write_text_file(file_path, content)

    def copy_file(self, src: Union[str, Path], dest: Union[str, Path]):
        try:
            Path(dest).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dest)
        except Exception as e:
            logger.error(f"Error al copiar archivo de {src} a {dest}: {e}")
            raise
