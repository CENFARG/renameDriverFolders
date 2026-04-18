# Estándar de Codificación y Arquitectura para Agentes de IA (v1)

Este documento define la arquitectura, estructura y mejores prácticas para la creación de Agentes de IA dentro del ecosistema `amBotHs-OS`, utilizando el `agentePerfilador` como caso de estudio y plantilla base.

## Filosofía del Agente

A diferencia de un *script* (que es un driver reactivo), un **Agente de IA** es una entidad semi-autónoma con las siguientes características:

- **Rol y Propósito**: Tiene una identidad y un objetivo definidos (ej. "Soy un agente perfilador de usuarios").
- **Memoria Persistente**: Puede leer y escribir en una base de conocimiento externa para aprender y mantener un estado a lo largo del tiempo.
- **Ciclo de Pensamiento (Sense-Think-Act)**: Opera en un ciclo donde percibe información, razona sobre ella y ejecuta acciones.
- **Uso de Herramientas (Tools)**: Puede utilizar otros scripts o APIs para interactuar con su entorno.

---

## 1. Arquitectura y Estructura de Directorios

Todo agente debe residir en su propia carpeta dentro de `agentes/` y seguir esta estructura:

```
/nombre_del_agente/
├── config/
│   ├── agent_config.json     # Configuración principal del agente (parámetros, rutas).
│   └── system_prompt.md      # El prompt de sistema que define la identidad y el rol del agente.
├── memory/
│   └── user_profile.json     # Ejemplo de la estructura de memoria que utiliza el agente.
├── src/
│   ├── agent.py            # La lógica central y el ciclo de pensamiento del agente.
│   └── main.py             # Punto de entrada para la ejecución (CLI y/o API).
├── logs/
│   ├── justifications.log  # Log de justificaciones (salida legible para humanos).
│   └── backlog.log         # Log técnico de cambios (salida para máquinas).
├── README.md               # Documentación específica del agente.
└── requirements.txt        # Dependencias de Python del agente.
```

## 2. Componentes Clave del Agente

### 2.1. Configuración (`config/`)

- **`agent_config.json`**: Define todos los parámetros operativos del agente: el modelo de IA a utilizar, los `max_tokens`, las rutas a los archivos de memoria y logs, etc. Permite cambiar el comportamiento del agente sin tocar el código.
- **`system_prompt.md`**: El corazón de la identidad del agente. Es un archivo de texto o Markdown que contiene el prompt de sistema detallado. Debe definir claramente:
    - El **Rol** del agente.
    - El **Objetivo** que debe cumplir.
    - Las **Instrucciones** paso a paso de su ciclo de pensamiento.
    - El **Formato de Salida** esperado.

### 2.2. Lógica Central (`src/agent.py`)

Esta es la implementación del ciclo **Sense-Think-Act**:

1.  **`_sense(self, input_data)`**: Método privado que recibe la entrada (texto, archivo, etc.) y carga el estado actual de la memoria (ej. lee `user_profile.json`).
2.  **`_think(self)`**: El núcleo del razonamiento. Aquí, el agente:
    *   Construye el prompt final combinando el `system_prompt`, la información de la memoria y la nueva entrada.
    *   Llama al modelo de IA (ej. Gemini) para obtener una respuesta.
    *   Procesa la respuesta del modelo para extraer las acciones a realizar.
3.  **`_act(self, response_data)`**: Método que ejecuta las acciones. Esto incluye:
    *   Actualizar la memoria persistente (ej. sobrescribir `user_profile.json`).
    *   Escribir en los logs de justificación y backlog.
    *   Devolver el resultado final.

La clase principal del agente debe tener un método público como `run(self, input_data)` que orqueste la llamada a estos tres métodos en orden.

### 2.3. Memoria (`memory/`)

- La memoria del agente debe ser explícita y estar externalizada, típicamente en archivos JSON o en una base de datos.
- El agente debe ser capaz de leer su estado actual al inicio de una tarea y escribir el nuevo estado al finalizarla.
- El `agentePerfilador` usa un archivo JSON (`user_profile.json`) como memoria, lo que representa un patrón simple y efectivo para empezar.

## 3. Salidas y Trazabilidad (`logs/`)

Un agente no solo debe actuar, sino también explicar por qué. Es mandatorio que un agente genere dos tipos de logs:

- **Log de Justificación (`justifications.log`)**: Una explicación en lenguaje natural de las decisiones tomadas. Responde al "porqué" del cambio y está destinado a la supervisión humana.
- **Log de Backlog/Técnico (`backlog.log`)**: Un registro estructurado (ej. JSON, diff) de los cambios realizados. Está destinado al control de versiones y a la interoperabilidad con otras máquinas.

## 4. Integración con Herramientas (Scripts/Drivers)

- Un agente avanzado debe ser capaz de utilizar los `scripts` de la carpeta `apps/` como herramientas.
- El `system_prompt` del agente debe incluir una descripción de las herramientas que tiene disponibles y en qué formato debe "solicitar" su uso.
- La lógica del agente (`agent.py`) debe ser capaz de parsear esta solicitud y ejecutar el script correspondiente (importando su `funcion_principal` o llamándolo como un subproceso de forma segura).

---

Este estándar provee una base sólida y escalable para construir un ecosistema de agentes de IA consistentes, mantenibles y robustos. El `agentePerfilador` es la implementación de referencia de esta arquitectura.
