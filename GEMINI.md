# GEMINI.md - Contexto del Proyecto `renameDriverFolders`

Este documento proporciona un resumen del proyecto `renameDriverFolders` para el contexto de futuras interacciones con Gemini CLI.

## 1. Resumen del Proyecto

`renameDriverFolders` es una aplicación Python basada en Flask diseñada para automatizar el procesamiento y renombrado de archivos en Google Drive. Monitorea subcarpetas específicas, utiliza el modelo de IA Gemini Pro para analizar el contenido de nuevos archivos, los renombra según un formato estandarizado y mantiene un `index.html` actualizado para facilitar el seguimiento. Está optimizado para despliegue sin servidor en Google Cloud Run.

**Tecnologías Clave:**
*   **Python 3.9+**
*   **Flask**: Microframework web para la aplicación.
*   **Google Drive API**: Para interactuar con Google Drive (monitoreo de cambios, lectura y renombrado de archivos).
*   **Google Cloud Storage (GCS)**: Para persistir el `pageToken` y mantener el estado entre ejecuciones.
*   **Gemini API**: Para el análisis de contenido de archivos mediante IA.
*   **Gunicorn**: Servidor WSGI para producción.
*   **Docker**: Para contenerización y despliegue en Cloud Run.

**Arquitectura:**
La aplicación sigue un modelo sin servidor, diseñada para ser ejecutada en Google Cloud Run. Utiliza variables de entorno para la configuración y Secret Manager para credenciales sensibles.

## 2. Archivos Clave del Proyecto

*   **`main.py`**: El archivo principal de la aplicación Flask. Contiene la lógica para monitorear cambios en Google Drive, analizar archivos con Gemini, renombrarlos y actualizar el índice HTML.
*   **`requirements.txt`**: Lista las dependencias de Python necesarias para el proyecto.
*   **`Dockerfile`**: Define cómo construir la imagen de Docker de la aplicación para su despliegue.
*   **`.env.example`**: Un archivo de ejemplo que describe las variables de entorno requeridas para la configuración de la aplicación, con explicaciones detalladas.

*   **`.gitignore`**: Especifica los archivos y directorios que Git debe ignorar (ej. `.env`, `.venv`, `__pycache__`).
*   **`README.md`**: Documentación completa del proyecto, incluyendo instrucciones de configuración, ejecución local y despliegue.
*   **`deployment/`**: Carpeta que contiene scripts y documentación relacionada con el despliegue.
    *   **`deployment/README.md`**: Guía detallada para el despliegue en Google Cloud Run, incluyendo el uso de VS Code con Cloud Code y Secret Manager.
    *   **`deployment/deploy.bat`**: Script para construir y subir la imagen de Docker a Google Container Registry.
    *   **`deployment/deploy_manual.bat`**: Script para el despliegue manual en Cloud Run.
*   **`tests/`**: Contiene las pruebas unitarias y de integración del proyecto.
    *   **`tests/test_gemini_import.py`**: Prueba la importación y accesibilidad de la biblioteca Gemini.
    *   **`tests/test_integration.py`**: Prueba el flujo completo de la aplicación (requiere credenciales válidas).

## 3. Construcción y Ejecución

### Entorno Local:
1.  **Clonar el Repositorio:** `git clone https://github.com/CENFARG/renameDriverFolders.git`
2.  **Configurar Entorno Virtual:** `python -m venv .venv` y activarlo.
3.  **Instalar Dependencias:** `pip install -r requirements.txt`
4.  **Configurar `.env`**: Crear un archivo `.env` basado en `.env.example` con tus credenciales y configuraciones de Google Cloud y Gemini.
5.  **Ejecutar Localmente:** `python main.py`
6.  **Ejecutar Pruebas:** `python tests/test_gemini_import.py` y `python tests/test_integration.py` (esta última requiere credenciales válidas).

### Despliegue en Google Cloud Run:
El método recomendado es usar la extensión **Cloud Code para VS Code**, que automatiza la construcción de la imagen de Docker, la subida a GCR y el despliegue en Cloud Run, integrándose con Google Secret Manager para las variables sensibles. También existe un script `deployment/deploy_manual.bat` para despliegue manual.

## 4. Convenciones de Desarrollo

*   **Configuración:** Basada en variables de entorno (principios de aplicación de 12 factores).
*   **Modularidad:** Código organizado en funciones distintas.
*   **Gestión de Estado:** La aplicación es sin estado; el `pageToken` de Google Drive se persiste en GCS.
*   **Manejo de Errores:** Uso de bloques `try...except` para una gestión robusta.
*   **Comentarios:** Código comentado en inglés y español.
*   **Encabezados de Archivo:** Cada archivo Python incluye un encabezado con su ruta relativa.
