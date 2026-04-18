# Estándar de Codificación y Mejores Prácticas para Scripts (v2)

Este documento define el estándar de codificación, la estructura y las mejores prácticas para la creación y mantenimiento de scripts reutilizables dentro del ecosistema de `amBotHs-OS`.

## Filosofía

- **Modularidad y Reutilización**: Cada script es un "driver" o una herramienta independiente, pero debe ser diseñado para ser reutilizable y combinable con otros.
- **Configurabilidad**: Los scripts deben ser altamente configurables sin necesidad de modificar el código fuente.
- **Robustez**: El manejo de errores, el logging y la validación de entradas son obligatorios.
- **Seguridad**: Las credenciales y datos sensibles deben ser manejados de forma segura y centralizada.

---

## 1. Estructura de Directorios de un Script

Cada script debe residir en su propia carpeta dentro de `scripts/apps/` y seguir la siguiente estructura:

```
/nombre_del_script/
├── config.toml         # Archivo de configuración específico del script (si es necesario).
├── run.bat             # Batch para ejecución simple desde la CLI de Gemini.
├── run.py              # El punto de entrada principal del script.
└── README.md           # Documentación específica del script.
```

## 2. Estándar de Codificación (run.py)

### 2.1. Cabecera del Archivo

Todo archivo `.py` debe comenzar con una cabecera que incluya la ruta del archivo y el versionado semántico (MAJOR.MINOR.PATCH).

```python
# /scripts/apps/nombre_del_script/run.py
# Version: 1.0.0
#
# (Breve descripción del propósito del script)
```

### 2.2. Doble Modo de Ejecución: CLI y API

Los scripts deben ser diseñados para funcionar de dos maneras:

1.  **Como herramienta de línea de comandos (CLI)**: Utilizando `argparse`.
2.  **Como una librería/API**: Con funciones que pueden ser importadas y utilizadas por otros scripts.

```python
import argparse
from pathlib import Path
from typing import List, Dict, Any

def funcion_principal(parametro1: str, parametro2: int) -> Dict[str, Any]:
    """
    Lógica principal del script. Documentada con type hints.
    """
    # ... lógica del script ...
    return {"status": "success", "resultado": "valor"}

def main():
    """
    Punto de entrada para la ejecución desde la línea de comandos.
    """
    parser = argparse.ArgumentParser(description="Descripción del script.")
    parser.add_argument('--param1', required=True, help="Descripción del parámetro 1.")
    parser.add_argument('--param2', type=int, default=10, help="Descripción del parámetro 2.")
    args = parser.parse_args()

    resultado = funcion_principal(args.param1, args.param2)
    import json
    print(json.dumps(resultado, indent=2))

if __name__ == "__main__":
    main()
```

### 2.3. Configuración y Credenciales

- **Parámetros por `argparse`**: Todos los scripts deben ser configurables a través de parámetros de línea de comandos.
- **Archivos de Configuración**: Para configuraciones complejas, cada script puede tener su propio archivo `config.toml`.
- **Credenciales Centralizadas**: **TODA** la información sensible (API keys, tokens, `.env`) debe ser almacenada en `C:\Users\gonza\Dropbox\DOC. RECA\06-Software\ambot-os-distro\scripts\config`. Los scripts deben leer de esta ubicación. Está prohibido hardcodear credenciales.

### 2.4. Logging y Manejo de Errores

- **Logging Centralizado**: Es **obligatorio** utilizar el `LoggerManager` de la librería `core`.
- **Excepciones Específicas**: Captura excepciones específicas de las librerías que uses (ej. `HttpError` de Google, `FileNotFoundError`) en lugar de un `except Exception:` genérico.
- **Validación de Entradas**: Valida siempre los datos de entrada (ej. con `argparse` o manualmente) antes de procesarlos.

### 2.5. Prácticas de Código Obligatorias

- **Type Hinting**: Usa `typing` para anotar los tipos de los argumentos de las funciones y los valores de retorno.
- **`pathlib`**: Usa la librería `pathlib` para toda la manipulación de rutas de archivos. Es más segura y legible.
- **Timestamps**: Para scripts que modifican datos, añade campos de timestamp (`created_at`, `updated_at`) automáticamente.
- **Salida Estructurada**: Si un script debe ser consumido por otro, su salida por `stdout` debe ser en formato **JSON**.
- **Despacho Dinámico**: Para scripts que manejan múltiples formatos o tipos (ej. `docx`, `xlsx`), usa un patrón de despacho para seleccionar la función correcta basado en un identificador (ej. la extensión del archivo).

## 3. Gestión de Dependencias

- **`requirements.txt` Centralizado**: Existirá un único archivo `C:\Users\gonza\Dropbox\DOC. RECA\06-Software\ambot-os-distro\scripts\requirements.txt`, organizado y comentado por script.

```
# -- Core & General Dependencies --
python-dotenv
requests

# -- Google API (manage_gmail, manage_google_files) --
google-api-python-client
google-auth-oauthlib

# -- Office Files (manage_office_files) --
python-docx
pandas
openpyxl
python-pptx
```

- **Entorno Virtual**: Se debe crear un único entorno virtual en `scripts/.venv` donde se instalarán todas las dependencias.

## 4. Documentación

- **`README.md` por Script**: Cada script debe tener su propio `README.md`.
- **Diagramas con Mermaid**: Para flujos complejos, es **obligatorio** incluir un diagrama Mermaid en el `README.md` o en los docstrings del código.

## 5. Ejecución y Reutilización

- **`run.bat`**: Cada script debe incluir un `run.bat` para su ejecución simple.
- **Agente Orquestador**: El agente de IA que utilice estos scripts debe ser diseñado para **reutilizar y combinar** las funciones principales de estos módulos, no solo para ejecutarlos como procesos externos. Debe poder importar `funcion_principal` de cada script y usarla directamente.

---

## Nota sobre Agentes de IA

El `agentePerfilador` es un prototipo de **Agente de IA**, no un script estándar. Se utilizará como base para un `TEMPLATE_AGENTE.md` futuro que definirá la arquitectura para agentes con memoria, ciclos de pensamiento y capacidades autónomas.

```
