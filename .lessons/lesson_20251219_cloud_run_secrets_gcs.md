# Lección Aprendida: Gestión de Secretos y Crashes de Inicio en Cloud Run

**Project:** renameDriverFolders  
**Date:** 2025-12-19  
**Context_Tags:** #CloudRun, #SecretManager, #Python, #GCS, #Debugging  
**User_Working_Style_Update:** No new style directives.

## Executive Summary
Se resolvió un crash crítico de inicio en los servicios Cloud Run (`api-server` y `worker`) causado por caracteres ocultos (saltos de línea) en un secreto de Google Cloud Secret Manager utilizado para el nombre del bucket de GCS. La solución implicó cambiar de Secret Manager a una variable de entorno literal para valores de configuración no sensibles, simplificando la arquitectura y eliminando puntos de fallo por codificación.

## Algorithmic Directives

### 1. Secretos vs. Variables de Entorno Literales
*   **Condition (IF):** Configurando variables de entorno en Cloud Run que no son credenciales (ej. nombres de buckets, URLs, IDs de proyecto).
*   **Trigger (WHEN):** Decidiendo entre usar Secret Manager o texto plano.
*   **Rule (THEN):** MUST usar variables de entorno literales (`--set-env-vars`) para datos de configuración no sensibles.
*   **Reasoning:** Secret Manager introduce complejidad de montaje, latencia y riesgos de codificación (newlines/BOM) innecesarios para datos públicos o de configuración estructural. Reservar Secret Manager estrictamente para passwords, keys y tokens.

### 2. Sanitización de Inputs en Secret Manager
*   **Condition (IF):** Creando una nueva versión de un secreto desde la línea de comandos.
*   **Trigger (WHEN):** Usando `echo` o tuberías (`|`) para pasar el valor.
*   **Rule (THEN):** MUST usar `echo -n` (Linux) o crear un archivo temporal validado sin saltos de línea y usar `--data-file`. En Windows PowerShell, `echo "val" | ...` a menudo añade CR/LF.
*   **Reasoning:** Librerías como `google-cloud-storage` validan estrictamente los nombres de buckets (regex) y fallan fatalmente si el string contiene `\n` o `\r`, causando crashes de inicio difíciles de depurar.

### 3. Diagnóstico de Crashes de Inicio Silenciosos
*   **Condition (IF):** Un servicio Cloud Run falla al iniciar (Container failed to start) y los logs de aplicación estándar no aparecen.
*   **Trigger (WHEN):** Buscando la causa raíz en Log Explorer.
*   **Rule (THEN):** MUST filtrar por `resource.type="cloud_run_revision"` Y `logName:"/stderr"`. NO confiar solo en filtros de severidad global.
*   **Reasoning:** Los errores de inicialización de Python (antes de que arranque Uvicorn/FastAPI y el logger de la app) se escriben en `stderr` del sistema. A veces no aparecen como "ERROR" estructurado, sino como texto plano en el stream de error estándar.

## Legacy Categories

### Programming Lessons
*   **Validación Defensiva:** Al leer variables de entorno críticas en Python, aplicar `.strip()` inmediatamente para eliminar whitespace accidental: `os.environ.get("BUCKET").strip()`.

### Strategic Lessons
*   **Simplicidad Arquitectural:** No sobre-ingenierizar la seguridad. Proteger el nombre de un bucket privado con Secret Manager no aporta seguridad real (la seguridad está en IAM) y añade fragilidad operativa.

### Methodology Lessons
*   **Verificación de Secretos:** Antes de desplegar, verificar el valor exacto del secreto con `gcloud secrets versions access latest` para confirmar que no hay caracteres basura.

## The "Anti-Gravity" Perspective
**"Configuration Gravity":** Tendemos a tratar toda configuración en la nube como "secreto" por defecto para ser "seguros". Esto añade peso innecesario. La verdadera seguridad es IAM; la configuración debe ser transparente y robusta. La "Anti-Gravedad" aquí es liberar la configuración estructural (nombres, rutas) de la bóveda de secretos para hacer el sistema más ligero y fácil de depurar.

## Future Checklist
*   [ ] Verificar que `database_manager.py` aplique `.strip()` a las variables de entorno.
*   [ ] Revisar si hay otros "falsos secretos" en la configuración que puedan pasarse a env vars normales.
