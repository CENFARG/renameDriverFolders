"""
DocumentationManager
========================

Manages documentation generation.
Gestiona la generación de documentación.

Generates Mintlify-compatible Markdown files from structured data.
Genera archivos Markdown compatibles con Mintlify a partir de datos estructurados.

:created:   2025-11-28
:filename:  documentation_manager.py
:author:    amBotHs
:version:   1.0.0
:status:    Production
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional
from .file_manager import FileManager

logger = logging.getLogger(__name__)

class DocumentationManager:
    """
    Manages documentation generation.
    Gestiona la generación de documentación.
    """

    def __init__(self, file_manager: FileManager, docs_base_path: Optional[str] = None):
        """
        Initialize DocumentationManager.
        Inicializa DocumentationManager.
        
        Args:
            file_manager: FileManager instance.
                          Instancia de FileManager.
            docs_base_path: Output directory. Defaults to 'docs_generated'.
                            Directorio de salida. Por defecto 'docs_generated'.
        """
        self.file_manager = file_manager
        self.docs_base_path = Path(docs_base_path) if docs_base_path else Path("docs_generated")
        
        if not self.docs_base_path.exists():
            self.docs_base_path.mkdir(parents=True, exist_ok=True)

    def _generate_markdown_content(self, data: Dict[str, Any]) -> str:
        """
        Generates Markdown content with YAML frontmatter.
        Genera contenido Markdown con frontmatter YAML.
        """
        # Frontmatter for Mintlify
        content = "---"
        content += f"title: \"{data.get('title', 'Untitled')}\"\n"
        content += f"description: \"{data.get('description', 'No description')}\"\n"
        content += "---"
        content += "\n"
        
        # Body
        content += f"# {data.get('title', 'Untitled')}"
        content += "\n\n"
        
        if "sections" in data and isinstance(data["sections"], list):
            for section in data["sections"]:
                content += f"## {section.get('heading', '')}"
                content += "\n\n"
                content += f"{section.get('body', '')}"
                content += "\n\n"
                
                if "items" in section and isinstance(section["items"], list):
                    for item in section["items"]:
                        content += f"- {item}"
                        content += "\n"
                    content += "\n"
                    
        return content

    def generate_mintlify_doc(self, doc_name: str, data: Dict[str, Any], subdirectory: Optional[str] = None) -> Optional[Path]:
        """
        Generates a Mintlify-compatible Markdown file.
        Genera un archivo Markdown compatible con Mintlify.
        
        Args:
            doc_name: Filename without extension.
                      Nombre del archivo sin extensión.
            data: Content dictionary.
                  Diccionario de contenido.
            subdirectory: Optional subfolder.
                          Subcarpeta opcional.
            
        Returns:
            Optional[Path]: Path to the generated file, or None on failure.
                            Ruta al archivo generado, o None si falla.
        """
        try:
            target_dir = self.docs_base_path
            if subdirectory:
                target_dir = target_dir / subdirectory
            
            file_path = target_dir / f"{doc_name}.md"
            content = self._generate_markdown_content(data)
            
            self.file_manager.write_text_file(file_path, content)
            logger.info(f"Generated Mintlify doc: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to generate doc: {e}")
            return None
