---
Project: renameDriverFolders
Date: 2026-01-01
Context_Tags: #Agno2.0 #Gemini #PydanticV2 #Python #Validation
User_Working_Style_Update: "PREFERENCIA: Los tests deben residir siempre en un directorio `tests/` dedicado, no en la raíz."

Executive Summary:
Se resolvió un `ValidationError` persistente en la integración Agno-Gemini causado por campos adicionales en la respuesta JSON del LLM ('examples'). La solución implicó configurar la permisividad en los modelos Pydantic (`extra='ignore'`) tanto en los archivos estáticos (`models.py`) como en la creación dinámica de modelos dentro del `AgentFactory`. También se corrigió un error de inicialización (`strict_output`) en la clase Gemini.

Algorithmic Directives:
- Condition: IF Defining Pydantic models for LLM Structured Output in Agno/Pydantic V2
  Trigger: WHEN creating `BaseModel` subclasses for `output_schema`
  Rule: MUS INCLUDE `model_config = ConfigDict(extra='ignore')`. DO NOT rely on default strict validation.
  Reasoning: LLMs often inject metadata or hallucinated fields (e.g., 'examples', 'context') that break strict schema validation.

- Condition: IF implementing a Dynamic Model Factory (e.g., `create_model`)
  Trigger: WHEN instantiating a Pydantic model dynamically
  Rule: MUST explicitly inject `__config__` or assign `model_config` to the created class to match the permissiveness of static models.
  Reasoning: Dynamic models default to strict validation unless configured otherwise, bypassing static file fixes.

- Condition: IF using Agno 2.3.x with Gemini
  Trigger: WHEN initializing `Gemini(Model)`
  Rule: DO NOT pass `strict_output`/`structured_outputs` arguments to the constructor if they are not supported by the specific version's API. USE `output_schema` on the Agent instead.
  Reasoning: Passing unsupported arguments causes immediate `TypeError` during agent creation.

Legacy Categories:
- Programming Lessons:
  - En Pydantic v2, no mezclar `class Config` con `model_config = ConfigDict(...)`. Fusionar todo dentro de `model_config`.
  - Python `create_model` retorna una clase a la que se le pueden asignar atributos de clase como `model_config` post-creación.

- Strategic Lessons:
  - Verificar siempre la paridad entre el código del "Worker" (servicio) y el código "Core" (paquete compartido). La divergencia en `models.py` fue la causa raíz del despiste inicial.

- Methodology Lessons:
  - Cuando la validación falla "misteriosamente", verificar si el factory está usando un archivo distinto al que se está editando (Core vs Service).

The "Anti-Gravity" Perspective:
La "Single Source of Truth" es frágil en arquitecturas de microservicios/paquetes locales. Si editas un modelo y el error persiste, asume INMEDIATAMENTE que hay una copia oculta o una generación dinámica que no está leyendo tu cambio. No confíes en que "ya lo edité".

Future Checklist:
[ ] Verificar que todos los `models.py` en `packages/` tengan `extra='ignore'`.
[ ] Confirmar que el despliegue a GCR use la versión actualizada del paquete `core-renombrador`.
---
