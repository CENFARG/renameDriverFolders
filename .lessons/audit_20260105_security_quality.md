# Auditoría de Seguridad y Calidad de Código - Proyecto Renombrador

## Resumen Ejecutivo de Seguridad
El sistema utiliza una arquitectura de microservicios autenticada mediante OAuth2 y OIDC. Se han identificado puntos de mejora en la gestión de headers y validación de inputs.

## Hallazgos de Seguridad

### 1. Cabeceras de Seguridad (API Server)
- **Estado**: Parcialmente implementado.
- **Hallazgo**: El middleware `SecurityHeadersMiddleware` es básico. La `Content-Security-Policy` actual es muy restrictiva (`default-src 'self'`), lo cual es bueno, pero podría romper integraciones si no se ajusta.
- **Recomendación**: Asegurar que las políticas COOP y COEP estén alineadas entre el frontend y el backend para evitar bloqueos de Google Auth.

### 2. Gestión de Secretos
- **Estado**: Muy bien (Google Secret Manager).
- **Hallazgo**: Los scripts locales de despliegue (`deploy_runner.py`) limpian comillas, lo cual previene errores comunes de parsing.
- **Recomendación**: Implementar rotación de secretos para la `GEMINI_API_KEY` cada 90 días.

### 3. Validación de Entradas
- **Estado**: Implementado vía Pydantic Validators.
- **Regla Aplicada**: `ManualJobRequest` valida que el `folder_id` siga un patrón de GDrive.
- **Mejora**: Añadir sanitización profunda en `job_type` para evitar inyecciones de templates en el worker.

## Hallazgos de Calidad (Python Pro)

### 1. Gestión de Dependencias
- **Hallazgo**: Se detectan múltiples `requirements.txt` y carpetas `.venv` dispersas.
- **Recomendación**: Unificar la gestión del entorno de desarrollo local o usar un `pyproject.toml` raíz si se decide migrar a una estructura de monorepo más formal (ej: con `poetry` o `uv`).

### 2. Estructura de Paquetes
- **Hallazgo**: `core-renombrador` está bien desacoplado.
- **Acción**: Seguir usando `pip install -e` para desarrollo local para mantener la vinculación viva sin redundancias.

### 3. Manejo de Errores y Logging
- **Hallazgo**: El uso de `defaultdict` en `build_filename` es excelente para la robustez (resiliencia).
- **Mejora**: Centralizar los mensajes de error del worker para que el API Server pueda reportar estados más granulares a la UI (ej: "Error en IA", "Error en I/O").

## Lista de Tareas para Limpieza
- [ ] Eliminar archivos temporales de `data/` si no se usa persistencia local.
- [ ] Borrar carpetas `.venv` innecesarias si se va a recrear el entorno.
- [ ] Actualizar `README.md` con las nuevas instrucciones de build (desde root).
- [ ] Sincronizar Memory Bank con el estado v2.0.0 estable.

## Conclusión
El código actual cumple con estándares de producción básicos-intermedios. Es resiliente y modular. Los cambios pendientes son principalmente de pulido y unificación de infraestructura.
