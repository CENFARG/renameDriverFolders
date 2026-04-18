# Metodología y Arquitectura para la Creación de Agentes (amBotHs-OS)

**Versión:** 1.1
**Audiencia Principal:** Agente de IA (Gemini-CLI) Constructor
**Propósito:** Servir como manual de arquitectura para entender, replicar y construir nuevos agentes reutilizando la estructura existente.

---

## 1. Filosofía: El Chasis y el Espíritu

La arquitectura de agentes de `amBotHs-OS` se basa en la separación de dos conceptos fundamentales:

1.  **El Chasis del Agente**: Es el código Python, genérico y reutilizable. Proporciona la estructura, el ciclo de vida y los sistemas de soporte vital (`core`). El chasis es robusto, estandarizado y **no debe ser modificado** para crear un nuevo agente con una funcionalidad estándar.
2.  **El Espíritu del Agente**: Son los archivos de configuración y prompts en lenguaje natural. Definen la personalidad, el propósito, el conocimiento y el método de razonamiento de un agente específico. **La creación de un nuevo agente se logra principalmente modificando su espíritu.**

El objetivo de esta arquitectura es permitir que un agente constructor (como esta instancia de Gemini-CLI) pueda generar nuevos agentes funcionales y seguros modificando únicamente archivos de configuración, sin necesidad de escribir o alterar la lógica de programación subyacente.

## 2. Arquitectura del "Chasis" (El Código)

El chasis está compuesto por el orquestador, el motor de razonamiento y los pilares del core.

### 2.1. El Orquestador (`main.py`)

- **Responsabilidad**: Es el punto de entrada. Su única función es arrancar los sistemas de soporte vital y poner en marcha al agente.
- **Proceso**:
    1.  **Integración con amBotHs-OS**: Ejecuta el boilerplate de código para localizar el `core` y las `apps`.
    2.  Inicializa `ConfigManager` para cargar la configuración del agente.
    3.  Inicializa `LoggerManager` usando la configuración cargada.
    4.  Instancia la clase `Agent` del motor de razonamiento, inyectándole la configuración y el prompt de sistema.
    5.  Ejecuta el método `run()` del agente.
- **Reutilización**: Este archivo es 100% genérico. Para un nuevo agente, se copia sin modificaciones.

### 2.2. Boilerplate de Integración (Código Obligatorio)

Para que un agente pueda funcionar desde su propio directorio (`/agentes/`) y aun así utilizar el `core` y las `apps` compartidas de la carpeta `/scripts/`, **es mandatorio** que su archivo `main.py` comience con el siguiente bloque de código:

```python
# /agentes/nombre_del_agente/src/main.py

import sys
import os

# --- INICIO: Boilerplate de Integración con #amBotHsOS ---
# 1. Encontrar la ruta raíz del proyecto (ambot-os-distro)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 2. Construir la ruta a la carpeta de scripts
scripts_path = os.path.join(project_root, 'scripts')

# 3. Añadir la carpeta de scripts al sys.path para poder importar 'core' y 'apps'
if scripts_path not in sys.path:
    sys.path.append(scripts_path)
# --- FIN: Boilerplate de Integración con #amBotHsOS ---

# Ahora se pueden importar los módulos del core
from core.logger_manager import LoggerManager
# ... resto del código
```

### 2.3. El Motor de Razonamiento (`agent.py`)

- **Responsabilidad**: Implementa el ciclo de vida y pensamiento abstracto del agente a través de la clase `Agent`.
- **Ciclo `Sense-Think-Act`**:
    1.  **`_sense()`**: Recibe la entrada del mundo exterior y carga el estado actual de la **memoria** del agente (ej. lee un archivo JSON).
    2.  **`_think()`**: Es el núcleo cognitivo. Combina el **espíritu** (el `system_prompt.md`) con la entrada y la memoria para formular una consulta a un modelo de IA externo. La elección del modelo (Gemini, OpenAI, etc.) se define en `agent_config.json`, haciendo a esta capa agnóstica.
    3.  **`_act()`**: Recibe la respuesta del modelo de IA y la traduce en acciones concretas: actualizar la memoria, escribir logs de justificación o invocar herramientas externas (otros scripts).
- **Reutilización**: La clase `Agent` es una plantilla. Para un nuevo agente, se reutiliza directamente. Solo se modificaría para añadir capacidades fundamentales nuevas, como un nuevo tipo de herramienta.

### 2.4. Los Pilares del Core (`/scripts/core`)

Estos módulos son **guardrails no negociables** que garantizan la estabilidad y seguridad de cualquier agente construido sobre este chasis.

- **`ConfigManager`**: El ADN del agente. Centraliza toda la configuración, asegurando que el comportamiento sea predecible y fácilmente modificable desde un único punto.
- **`LoggerManager`**: La caja negra. Obliga a todo agente a registrar sus acciones y decisiones de forma estandarizada, crucial para la depuración y la trazabilidad.
- **`ErrorHandler`**: El sistema inmune. Captura excepciones no controladas para evitar que el agente falle de forma catastrófica.

## 3. El "Espíritu" del Agente (La Configuración)

Aquí es donde reside la verdadera identidad de cada agente. Crear un nuevo agente es, en esencia, definir un nuevo espíritu.

- **`config/agent_config.json`**: El panel de control técnico. Define los parámetros *operativos*: qué modelo de IA usar (`model_name`), la ruta a su memoria (`memory_path`), los límites de tokens, etc.
- **`config/system_prompt.md`**: El alma del agente. Es un documento en lenguaje natural que define:
    - **Rol**: "Eres un..."
    - **Objetivo**: "Tu meta es..."
    - **Método**: "Sigue estos pasos: 1, 2, 3..."
    - **Formato de Salida**: "Tu respuesta final debe ser un JSON con las claves 'A' y 'B'."

## 4. Guía de Construcción para el Agente Constructor

Para crear un nuevo agente (ej. `agenteAnalistaDeLicitaciones`) a partir de la plantilla `agentePerfilador`:

1.  **Clonar Estructura**: Copia el directorio completo de `/agentes/agentePerfilador/` a `/agentes/nuevoAgente/`.
2.  **Implementar Boilerplate**: Asegúrate de que el `main.py` del nuevo agente incluye el boilerplate de integración del punto 2.2.
3.  **Definir el Espíritu**: 
    *   Crea un nuevo `system_prompt.md` en `nuevoAgente/config/` que describa en detalle el rol, objetivo y método del nuevo agente.
    *   Ajusta `agent_config.json` para definir el modelo de IA que usará y, crucialmente, la ruta a su propia base de memoria (ej. `memory/licitaciones_activas.json`).
4.  **Definir la Memoria**: Crea la estructura inicial del archivo de memoria (ej. un archivo JSON vacío con las claves esperadas) en la carpeta `nuevoAgente/memory/`.
5.  **No Tocar el Chasis**: No modifiques la lógica genérica del `main.py` o los archivos del `core`.

Siguiendo estos pasos, se puede generar un agente completamente nuevo, funcional y seguro, reutilizando el 95% del código existente y enfocando el esfuerzo en definir su comportamiento a través de la configuración y el lenguaje natural.