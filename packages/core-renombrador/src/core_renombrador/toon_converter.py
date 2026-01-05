"""
TOON Converter
========================

Generic module to convert Python data structures into TOON format.
Módulo genérico para convertir estructuras de datos Python al formato TOON.

Designed to be granular, reusable, and optimized for LLM token usage.
Diseñado para ser granular, reutilizable y optimizado para el uso de tokens en LLMs.

:created:   2025-11-28
:filename:  toon_converter.py
:author:    amBotHs
:version:   1.0.0
:status:    Production
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import datetime
from typing import Any, Dict, List, Union, Optional

def _escape_string(s: str) -> str:
    """
    Escapes strings containing special TOON characters.
    Escapa strings que contienen caracteres especiales de TOON.
    
    Args:
        s (str): Input string. / String de entrada.
        
    Returns:
        str: Escaped string. / String escapado.
    """
    if not s:
        return ""
    # If it contains newlines, commas (in arrays), or colons, use quotes
    # Si contiene saltos de línea, comas (en arrays), o dos puntos, usar comillas
    if "\n" in s or "," in s or ":" in s or s.strip() == "":
        # Escape existing double quotes
        # Escapar comillas dobles existentes
        return f'"{s.replace("\"", "\\\"")}"'
    return s

def _format_value(value: Any) -> str:
    """
    Formats primitive values for TOON.
    Formatea valores primitivos para TOON.
    
    Args:
        value (Any): The value to format. / El valor a formatear.
        
    Returns:
        str: Formatted string. / String formateado.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return _escape_string(str(value))

def _is_tabular_candidate(data: List[Any]) -> bool:
    """
    Determines if a list of dictionaries can be tabular (same keys).
    Determina si una lista de diccionarios puede ser tabular (mismas keys).
    
    Args:
        data (List[Any]): List to check. / Lista a verificar.
        
    Returns:
        bool: True if tabular candidate. / True si es candidato tabular.
    """
    if not data or not isinstance(data[0], dict):
        return False
    
    keys = set(data[0].keys())
    for item in data[1:]:
        if not isinstance(item, dict) or set(item.keys()) != keys:
            return False
        # Verify values are primitive (not nested)
        # Verificar que los valores sean primitivos (no anidados)
        for v in item.values():
            if isinstance(v, (dict, list)):
                return False
    return True

def _format_tabular(data: List[Dict[str, Any]], key_name: Optional[str], indent: int) -> str:
    """
    Generates the tabular representation of an array.
    Genera la representación tabular de un array.
    
    Args:
        data (List[Dict]): The tabular data. / Los datos tabulares.
        key_name (Optional[str]): The key name. / El nombre de la clave.
        indent (int): Indentation level. / Nivel de indentación.
        
    Returns:
        str: Formatted tabular string. / String tabular formateado.
    """
    indent_str = " " * indent
    if not data:
        return f"{indent_str}{key_name}[0]:" if key_name else f"{indent_str}[0]:"
    
    keys = list(data[0].keys())
    header_keys = ",".join(keys)
    count = len(data)
    
    prefix = f"{key_name}[{count}]" if key_name else f"[{count}]"
    lines = [f"{indent_str}{prefix}{{{header_keys}}}:"]
    
    for item in data:
        values = [_format_value(item[k]) for k in keys]
        row = ",".join(values)
        lines.append(f"{indent_str}  {row}")
        
    return "\n".join(lines)

def to_toon(data: Any, key_name: Optional[str] = None, indent: int = 0) -> str:
    """
    Converts a data structure to TOON string.
    Convierte una estructura de datos a string TOON.
    
    Args:
        data (Any): The data structure. / La estructura de datos.
        key_name (Optional[str]): The key name. / El nombre de la clave.
        indent (int): Current indentation level. / Nivel de indentación actual.
        
    Returns:
        str: Formatted TOON string. / String formateado en TOON.
    """
    indent_str = " " * indent
    
    # Case 1: Dictionary (Object) / Caso 1: Diccionario (Objeto)
    if isinstance(data, dict):
        lines = []
        # If it has key_name (nested), print key first
        # Si tiene key_name (es anidado), imprimir la key primero
        if key_name:
            lines.append(f"{indent_str}{key_name}:")
            child_indent = indent + 2
        else:
            child_indent = indent

        for k, v in data.items():
            # Recursion for each field / Recursión para cada campo
            lines.append(to_toon(v, key_name=k, indent=child_indent))
            
        return "\n".join(lines)

    # Case 2: List (Array) / Caso 2: Lista (Array)
    elif isinstance(data, list):
        if not data:
            return f"{indent_str}{key_name}[0]:" if key_name else f"{indent_str}[0]:"
        
        count = len(data)
        
        # Sub-case 2a: Tabular (List of uniform Dicts) / Sub-caso 2a: Tabular
        if _is_tabular_candidate(data):
            # Cast to List[Dict] for type checker
            return _format_tabular(data, key_name, indent) # type: ignore
        
        # Sub-case 2b: List of Primitives (Inline) / Sub-caso 2b: Lista de Primitivos
        if all(not isinstance(x, (dict, list)) for x in data):
            values = ",".join([_format_value(x) for x in data])
            prefix = f"{key_name}[{count}]" if key_name else f"[{count}]"
            return f"{indent_str}{prefix}: {values}"
            
        # Sub-case 2c: Mixed or Complex List (Block style) / Sub-caso 2c: Lista Mixta
        prefix = f"{key_name}[{count}]" if key_name else f"[{count}]"
        lines = [f"{indent_str}{prefix}:"]
        for item in data:
            if isinstance(item, dict):
                # Render object as list item
                # Renderizar objeto como item de lista
                item_str = to_toon(item, indent=0) 
                item_lines = item_str.split('\n')
                lines.append(f"{indent_str}  - {item_lines[0].strip()}")
                for subline in item_lines[1:]:
                    lines.append(f"{indent_str}    {subline.strip()}")
            else:
                lines.append(f"{indent_str}  - {_format_value(item)}")
        return "\n".join(lines)

    # Case 3: Primitive (Leaf) / Caso 3: Primitivo (Hoja)
    else:
        val_str = _format_value(data)
        if key_name:
            return f"{indent_str}{key_name}: {val_str}"
        return f"{indent_str}{val_str}"

if __name__ == "__main__":
    # Usage Example 1: General / Ejemplo de Uso 1: General
    print("---", "TOON Converter Example 1: General", "---")
    
    sample_data = {
        "id": "TASK-001",
        "title": "Implement TOON",
        "active": True,
        "tags": ["dev", "core", "urgent"],
        "metadata": {
            "created": "2025-11-28",
            "author": "Gemini"
        },
        "subtasks": [
            {"id": 1, "name": "Design", "done": True},
            {"id": 2, "name": "Code", "done": False}
        ],
        "logs": [
            {"ts": "10:00", "msg": "Started"},
            {"ts": "11:00", "msg": "Paused"}
        ]
    }
    
    print("=========== JSON ==========")
    print(sample_data)
    print("=========== TOON ==========")
    print(to_toon(sample_data))
    
    # Usage Example 2: Tabular Data / Ejemplo de Uso 2: Datos Tabulares
    print("\n---", "TOON Converter Example 2: Tabular Data (SQL/CSV Simulation)", "---")
    
    db_results = [
        {"id": 101, "username": "alice", "role": "admin", "last_login": "2025-11-28"},
        {"id": 102, "username": "bob", "role": "user", "last_login": "2025-11-27"},
        {"id": 103, "username": "charlie", "role": "user", "last_login": "2025-11-26"},
        {"id": 104, "username": "dave", "role": "guest", "last_login": "2025-11-25"}
    ]
    
    print("=========== JSON (Verbose) ==========")
    print(db_results)
    print("=========== TOON (Compact) ==========")
    print(to_toon(db_results, key_name="users"))
    print("\n---", "End Examples", "---")
