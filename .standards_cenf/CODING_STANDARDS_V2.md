# Metodología y Estándares de Programación para el Ecosistema de Scripts y Agentes (amBotHs-OS)

**Versión:** 2.0
**Audiencia Principal:** Agente de IA Constructor (Gemini-CLI)
**Propósito:** Servir como manual de operaciones y metodología para entender, utilizar, reutilizar y crear nuevos componentes (Scripts y Agentes) dentro del ecosistema `amBotHs-OS`.

---

## 1. Manifiesto del Ecosistema amBotHs-OS

Este ecosistema se compone de tres tipos de entidades de software. Tu misión como agente constructor es entender su rol y saber cómo y cuándo crearlas y utilizarlas.

1.  **Core (`/core`)**: **La Librería del Sistema Operativo.** Es la base fundamental y no negociable. Contiene los servicios esenciales (Logging, Configuración, Errores). **Regla: No se modifica. Se utiliza siempre.**

2.  **Drivers/Scripts (`/apps`)**: **Las Herramientas Atómicas.** Son programas reactivos que ejecutan una tarea específica y bien definida (ej. `manage_gmail`, `update_json_file`). Son las "manos" del sistema. **Regla: Se crean para tareas reutilizables y deben seguir una estructura estricta.**

3.  **Agentes (`/agentes`)**: **Las Entidades Cognitivas.** Son unidades semi-autónomas que tienen un propósito, memoria y un ciclo de razonamiento (`Sense-Think-Act`). Utilizan los *Drivers* como herramientas para cumplir sus objetivos. **Regla: Se crean para tareas complejas que requieren estado y contexto. Se construyen a partir de una plantilla (arquetipo).**

La filosofía principal es **configuración sobre código**. El comportamiento de Scripts y Agentes se modifica a través de archivos de configuración y prompts en lenguaje natural, no reescribiendo la lógica de programación subyacente.

## 2. El Core: Servicios Fundamentales del Sistema

Como agente constructor, **debes** integrar estos componentes en cada nuevo script o agente que crees para garantizar la estabilidad y consistencia del ecosistema.

- **`ConfigManager`**: Es el servicio de configuración central. Se utiliza para leer parámetros de archivos `.json` o `.toml`, permitiendo que el comportamiento del componente sea dinámico.
- **`LoggerManager`**: Es el servicio de registro de actividad. **Todo** componente debe usarlo en lugar de `print()` para emitir información, advertencias o errores. Esto crea una "caja negra" auditable para todo el sistema.
- **`ErrorHandler`**: Es el servicio de seguridad que captura excepciones no controladas, previniendo fallos catastróficos.

## 3. Metodología para la Creación de "Drivers" (Scripts)

Cuando necesites crear una nueva herramienta reutilizable, sigue esta metodología:

1.  **Estructura**: Crea un nuevo directorio en `/apps/` con la estructura definida en `CODING_STANDARDS.md` (v1), incluyendo `run.py`, `run.bat`, y `README.md`.

2.  **Doble Modo de Ejecución (CLI/API)**: La lógica principal debe estar en una función (`funcion_principal`) que pueda ser importada y llamada por un Agente. El bloque `if __name__ == "__main__":` se usará para la ejecución vía línea de comandos (`argparse`).

3.  **Configuración**: Expón todos los parámetros posibles a través de `argparse`. Las credenciales y datos sensibles **deben** leerse de la carpeta centralizada `scripts/config/`.

4.  **Salida Estándar**: Si el script devuelve datos que otro programa pueda necesitar, la salida por `stdout` **debe** ser en formato **JSON**.

## 4. Metodología para la Creación de "Agentes"

Los agentes son el cerebro del sistema. Para crear uno nuevo, **debes** seguir el patrón del arquetipo `agentePerfilador`.

### 4.1. Arquitectura del Arquetipo (Basada en `agentePerfilador`)

- **El Chasis (Código Genérico)**: El código Python (`main.py`) es un lanzador que no cambia. Su única función es:
    1. Cargar el `core` (Config, Logger).
    2. Leer el "Espíritu" del agente (el `system_prompt.md` y el `agent_config.json`).
    3. Instanciar y ejecutar el ciclo de razonamiento del agente.

- **El Espíritu (Configuración Específica)**:
    - `agent_config.json`: Define los parámetros *técnicos*: el modelo de IA a usar (ej. `gemini-1.5-pro-latest`), la ruta a su archivo de memoria, etc.
    - `system_prompt.md`: Define la *personalidad y el método*. Es un manual de instrucciones en lenguaje natural para el modelo de IA, que le dice quién es, qué debe hacer y cómo debe formatear su respuesta (ej. "Devuelve siempre un JSON con las claves `perfilDeUsuarioActualizado` y `justificacionDeCambios`").

- **El Ciclo de Razonamiento (Implementado en `main.py` del arquetipo)**:
    1.  **Sense**: Lee la entrada del usuario y carga el estado actual de su **Memoria** (el archivo JSON de perfil).
    2.  **Think**: Construye un prompt combinando el `system_prompt`, la Memoria y la nueva entrada. Envía este prompt al modelo de IA definido en la configuración.
    3.  **Act**: Recibe la respuesta estructurada (JSON) del modelo. Parsea esta respuesta y ejecuta las acciones: actualiza el archivo de Memoria y escribe en los logs de justificación.

### 4.2. Guía de Construcción para el Agente Constructor

Para crear un nuevo agente (ej. `agenteAnalistaDeLicitaciones`):

1.  **Clonar Arquetipo**: Copia la estructura completa de `/agentes/agentePerfilador/` a `/agentes/nuevoAgente/`.
2.  **Definir Espíritu**: Modifica los archivos en `nuevoAgente/config/`:
    *   **`system_prompt.md`**: Reescribe el prompt para definir el nuevo rol, objetivo y formato de salida del `agenteAnalistaDeLicitaciones`.
    *   **`agent_config.json`**: Ajusta la ruta al nuevo archivo de memoria (ej. `memory/licitacion_activa.json`).
3.  **Inicializar Memoria**: Crea el archivo JSON de memoria inicial en `nuevoAgente/memory/`.
4.  **No Modificar el Chasis**: El código `main.py` del arquetipo no debe ser modificado. Su lógica es genérica y se adapta al nuevo comportamiento definido en el Espíritu.

## 5. Reglas de Oro del Ecosistema

- **Dependencias**: Todas las dependencias de Python se gestionan en el archivo central `scripts/requirements.txt`, que debe estar comentado por componente.
- **Documentación**: Todo nuevo componente (Script o Agente) debe tener un `README.md` que explique su propósito y uso, y el código debe incluir comentarios y diagramas Mermaid para lógicas complejas.
- **Seguridad**: El acceso a la carpeta `scripts/config/` es un punto crítico. Cualquier código que la utilice debe ser validado para evitar la exposición de credenciales.
