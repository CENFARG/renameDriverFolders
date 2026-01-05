# Arquitectura y Plan de Refactorización v3: Plataforma de Renombrado Documental

Este documento describe la arquitectura final y el plan de ejecución para refactorizar la aplicación `renameDriverFolders` a una plataforma de microservicios robusta y escalable, alineada con los estándares de #ambotOS y #CENF.

## 1. Visión y Objetivos

El objetivo es evolucionar la aplicación desde un único servicio monolítico a una plataforma desacoplada que soporte dos flujos de trabajo distintos pero unificados:

1.  **Modo Automático:** Procesamiento desatendido de carpetas estructurales fijas, invocado por un scheduler.
2.  **Modo Manual:** Una interfaz de usuario donde los colaboradores pueden solicitar el procesamiento de carpetas arbitrarias "a demanda".

Ambos flujos utilizarán la misma lógica de negocio central, garantizando consistencia y mantenibilidad.

## 2. Arquitectura de Microservicios (Monorepo)

La solución se estructurará como un monorepo con los siguientes componentes principales:

```
/rename-driver-folders/
├── services/
│   ├── api-server/             # Microservicio 1: El "Recepcionista" (FastAPI).
│   └── worker-renombrador/       # Microservicio 2: El "Cerebro" (Agno AgentOS).
│
├── frontend/
│   └── prompt_for_aistudio.md  # Prompt técnico detallado para generar la UI.
│
├── packages/
│   └── core-renombrador/         # Paquete Python REUTILIZABLE con toda la lógica de negocio.
│       ├── src/core_renombrador/
│       │   ├── agent_factory.py
│       │   ├── database_manager.py
│       │   ├── documentation_manager.py
│       │   ├── toon_converter.py
│       │   └── drive_handler.py
│       └── pyproject.toml
│
├── .context/
│   └── ARQUITECTURA_Y_PLAN_V3.md # Este mismo documento.
│
└── skaffold.yaml                 # Orquestador de despliegue para AMBOS servicios.
```

## 3. Flujo de Datos y Responsabilidades

**a. `packages/core-renombrador`:**
*   **Propósito:** Contiene toda la lógica de negocio como un paquete de Python instalable y agnóstico al trigger.
*   **Componentes Clave:**
    *   `database_manager.py`: Gestiona la conexión a la base de datos (JSON local para desarrollo, Postgres/Supabase para producción) para obtener configuraciones.
    *   `agent_factory.py`: Utiliza el `database_manager` para obtener la configuración de un agente (prompt, modelo, temperatura) y lo instancia usando el patrón `agno.Agent(**config)`.
    *   `toon_converter.py`: Pre-procesa datos para optimizar el uso de tokens en los prompts.
    *   `drive_handler.py`: Encapsula toda la interacción con la API de Google Drive.

**b. `services/api-server`:**
*   **Propósito:** Es la única puerta de entrada pública al sistema. Será una aplicación FastAPI ligera.
*   **Endpoints:**
    *   `POST /jobs/manual`: Para la UI. Autentica al usuario (OAuth), recibe una URL de carpeta, crea una tarea en Google Cloud Tasks y responde `202 Aceptado`.
    *   `POST /jobs/scheduled`: Para el modo automático. Invocado por Cloud Scheduler. No requiere autenticación de usuario. Crea tareas para una lista predefinida de carpetas.

**c. `services/worker-renombrador`:**
*   **Propósito:** Es un servicio de Cloud Run **privado**. Su única función es procesar tareas de una cola de Google Cloud Tasks.
*   **Lógica:**
    1. Recibe una tarea (con el ID de carpeta y, opcionalmente, un token de usuario).
    2. Usa el paquete `core-renombrador` para instanciar el agente.
    3. Ejecuta el proceso de renombrado.

## 4. Plan de Ejecución del Refactor

1.  **Paso 1: Creación de Estructura.** Crear la nueva estructura de directorios (`services`, `packages`, `frontend`).
2.  **Paso 2: Mover y Crear Archivos Core.** Mover la lógica de `core/` a `packages/core-renombrador/` y crear los nuevos módulos (`database_manager.py`, etc.).
3.  **Paso 3: Generar el Prompt de la UI.** Crear el archivo `frontend/prompt_for_aistudio.md`.
4.  **Paso 4: Implementar Servicios.** Desarrollar el código para el `api-server` y el `worker-renombrador`, asegurando que ambos usen el paquete `core-renombrador`.
5.  **Paso 5: Configurar Despliegue.** Actualizar `skaffold.yaml` y los `Dockerfile` para el despliegue multi-servicio.
6.  **Paso 6: Pruebas y Validación.** Probar cada flujo (manual y automático) de forma independiente y luego en conjunto.
