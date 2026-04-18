# Lecciones Aprendidas - Proyecto Renombrador (#amBotHsOS)

## Metadata
- **Project**: Renombrador Archivos GDrive
- **Date**: 2026-01-05
- **Context_Tags**: #CloudRun #Docker #GeminiAPI #FastAPI #PydanticV2
- **User_Working_Style_Update**: El usuario prefiere despliegues directos y rápidos ("quick wins") pero requiere auditoría de seguridad y limpieza de código al finalizar. Valora la persistencia de lecciones en formato algorítmico y la sincronización estricta del Memory Bank.

## Resumen Ejecutivo
Se logró estabilizar un sistema de renombrado automático basado en IA tras superar bloqueos críticos de despliegue, validación de esquemas y lógica de formateo. La complejidad radicó en la interacción entre Pydantic V2, la API de Gemini (Vertex AI compatible) y el contexto de compilación de Docker en despliegues monorepo.

## Directivas Algorítmicas (Core Knowledge)

### 1. Contexto de Compilación Docker en Monorepos
- **Condición (IF):** Desplegando un microservicio que depende de paquetes locales (ej: `packages/core-renombrador`) usando Cloud Build.
- **Trigger (WHEN):** Ejecutando `gcloud builds submit` dentro de la carpeta del servicio.
- **Regla (THEN):** **SIEMPRE** ejecutar el comando de build desde la **raíz (root)** del repositorio y pasar el archivo de configuración con la ruta completa.
- **Reasoning:** Si se ejecuta dentro de la subcarpeta, Docker no puede "ver" carpetas hermanas o superiores, resultando en errores de `COPY` o archivos no encontrados.

### 2. Validación de Esquemas Gemini/Vertex AI
- **Condición (IF):** Usando el SDK de Google Generative AI con modelos Pydantic para `response_mime_type: "application/json"`.
- **Trigger (WHEN):** Definiendo el modelo en `output_schema` o `response_model`.
- **Regla (THEN):** **PROHIBIDO** incluir `json_schema_extra` o `examples` dentro del `ConfigDict` del modelo Pydantic. **DEBE** ser un esquema puro (campos y tipos).
- **Reasoning:** La API de Vertex/Gemini rechaza esquemas que contengan metadatos adicionales no estándar, lanzando errores de validación de argumentos.

### 3. Robustez en Generación de Nombres (Template Safety)
- **Condición (IF):** Generando strings dinámicos usando `.format()` o `.format_map()` basados en salida de IA.
- **Trigger (WHEN):** Aplicando una plantilla definida por el usuario que puede contener placeholders no devueltos por la IA.
- **Regla (THEN):** **SIEMPRE** usar un `defaultdict` o un mapeador **case-insensitive** con valores por defecto (ej: "unknown"). **NUNCA** permitir que un `KeyError` detenga el flujo.
- **Reasoning:** Las IAs pueden omitir campos o cambiar el casing. El sistema debe ser resiliente ante variaciones en la respuesta.

## Categorías de Lecciones

### Programación (Python/FastAPI)
- **PII Guardrails:** Los guardrails de Pydantic/Agno pueden dar falsos positivos en documentos internos legales/financieros. Se optó por desactivarlos para este caso de uso específico.
- **API Key Mapping:** La librería `google-generative-ai` a veces requiere `GOOGLE_API_KEY` incluso si se configura `GEMINI_API_KEY`. Realizar el mapeo explícito en el entorno de ejecución.

### Estrategia (Arquitectura)
- **Monorepo vs Microservicios:** La centralización de lógica en `packages/core-renombrador` es excelente para consistencia, pero requiere que el CI/CD (Cloud Build) tenga visibilidad total del repo.

## Anti-Gravity Insight
"La robustez de un sistema de IA no está en la precisión del prompt, sino en la elasticidad del código que recibe su salida." – Fallar con elegancia (mapeo de alias, casing-insensitivity) ahorró más tiempo que re-intentar prompts.

## Future Checklist
- [ ] ¿El build se lanza desde el root?
- [ ] ¿El modelo Pydantic es 'limpio' (sin extras)?
- [ ] ¿El formatter tiene safe-fallbacks?
- [ ] ¿Las API Keys están mapeadas correctamente?
