# Active Context

Esta sesión se centró en la estabilización total de la v2.0.0, corrigiendo errores críticos de despliegue, validación de esquemas y robustez en el procesado de archivos.

## Estado Actual
- **Producción Estable**: El sistema se encuentra en la revisión **v2-00024** en Cloud Run (`us-central1`).
- **Funcionalidad Validada**: Se confirmó el procesado exitoso de archivos con nombres generados correctamente (sin "unknown") y mapeo de categorías.
- **Frontend Corregido**: Se resolvieron los bugs de redirección, visibilidad de botones y autenticación (re-renderizado de Google Login).

## Cambios Recientes (Sesión Actual)
- ✅ **Fix de Despliegue**: Se identificó que `gcloud builds submit` debía lanzarse desde el root del proyecto para capturar el paquete `core-renombrador`.
- ✅ **Fix de Esquema**: Se eliminaron los metadatos Pydantic (`json_schema_extra`) que causaban errores en la API de Vertex/Gemini.
- ✅ **Robustez en Nombres**: Se implementó `CaseInsensitiveDict` y mapeo de alias (`issuer`, `type`, `entity`) en `build_filename`.
- ✅ **Frontend Refined**: Solucionado el re-renderizado del botón Login tras logout y el estado del botón "Procesar".
- ✅ **Security Patch**: Añadido tag `COOP` en `index.html` para resolver advertencias del navegador.

## Próximos Pasos (Próxima Sesión)
1. **Mantenimiento**: Monitorear el crecimiento del bucket de GCS y realizar una rotación de secretos (Gemini API Key) si es necesario.
2. **Nuevos Jobs**: El sistema está listo para recibir nuevas configuraciones de jobs en `jobs.json` (o Supabase).

*2026-01-05 - Contexto sincronizado tras estabilización exitosa de la v2.0.0.*
