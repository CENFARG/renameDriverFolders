# renameDriverFolders - Procesador Automatizado de Archivos de Google Drive

## Descripción General del Proyecto

Este proyecto es un procesador de archivos automatizado basado en Python para Google Drive, diseñado para monitorear subcarpetas específicas, analizar nuevos archivos usando el modelo de IA Gemini Pro, renombrarlos con un formato estandarizado y mantener un archivo `index.html` para un fácil seguimiento.

Está construido para ser desplegado como una función sin servidor (por ejemplo, en Google Cloud Run), pero también puede ejecutarse localmente para desarrollo y pruebas.

## Guía de Inicio (Para el Cliente)

Esta sección te guiará a través de la configuración y ejecución de la aplicación localmente.

### 1. Prerrequisitos

*   **Python 3.9+:** Asegúrate de que Python esté instalado en tu sistema.
*   **Proyecto de Google Cloud:** Necesitas un proyecto de Google Cloud activo con la facturación habilitada.
*   **Cuenta de Servicio (Service Account):** Una cuenta de servicio de Google Cloud con los siguientes roles:
    *   `API de Google Drive` (acceso completo)
    *   `Administrador de objetos de Storage` (para Google Cloud Storage)
    *   `Usuario de Vertex AI` (para acceso al modelo Gemini Pro)
*   **Clave de API de Gemini:** Una clave de API para el modelo Gemini.

### 2. Clonar el Repositorio

Primero, clona este repositorio en tu máquina local:

```bash
git clone https://github.com/CENFARG/renameDriverFolders.git
cd renameDriverFolders
```

### 3. Configurar el Entorno Virtual de Python

Es muy recomendable utilizar un entorno virtual para gestionar las dependencias:

```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate
```

### 4. Instalar Dependencias

Con tu entorno virtual activado, instala los paquetes de Python requeridos:

```bash
pip install -r requirements.txt
```

### 5. Configuración (archivo `.env`)

Esta aplicación utiliza variables de entorno para la configuración. Debes crear un archivo `.env` en el directorio raíz del proyecto.

**Pasos para crear tu archivo `.env`:**

1.  **Crear `SERVICE_ACCOUNT_KEY_B64`:**
    *   Descarga la clave JSON de tu cuenta de servicio desde la Consola de Google Cloud.
    *   Abre el archivo JSON y copia todo su contenido.
    *   Codifica el contenido JSON a Base64. En PowerShell de Windows, puedes usar:
        ```powershell
        [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Raw "ruta\a\tu\clave-de-servicio.json")))
        ```
    *   En macOS/Linux, puedes usar:
        ```bash
        base64 -w 0 ruta/a/tu/clave-de-servicio.json
        ```
    *   Copia la cadena Base64 resultante.

2.  **Poblar el archivo `.env`:** Crea un archivo llamado `.env` en la raíz del proyecto y llénalo con tus valores específicos:

    ```
    ROOT_FOLDER_ID="<ID_de_tu_Carpeta_Raíz_en_Google_Drive>"
    TARGET_FOLDER_NAMES='["Doc de Respaldo", "Facturas"]' # Ejemplo: Ajústalo según sea necesario
    GCS_BUCKET_NAME="<Nombre_de_tu_Bucket_en_Google_Cloud_Storage>"
GCP_PROJECT_ID="<ID_de_tu_Proyecto_de_Google_Cloud>"
GCP_REGION="us-central1" # O tu región de preferencia
SERVICE_ACCOUNT_KEY_B64="<Tu_Clave_de_Servicio_JSON_Codificada_en_Base64>"
GEMINI_API_KEY="<Tu_Clave_de_API_de_Gemini>"
    ```
    *   **`ROOT_FOLDER_ID`**: El ID de Google Drive de la carpeta principal que deseas monitorear.
    *   **`TARGET_FOLDER_NAMES`**: Una cadena JSON con los nombres de las subcarpetas dentro de `ROOT_FOLDER_ID` que se monitorearán específicamente.
    *   **`GCS_BUCKET_NAME`**: Un bucket de Google Cloud Storage donde la aplicación almacenará su estado (por ejemplo, el `pageToken` para los cambios de Drive).
    *   **`GCP_PROJECT_ID`**: El ID de tu proyecto de Google Cloud.
    *   **`GCP_REGION`**: La región donde está desplegado tu modelo de Gemini (ej., `us-central1`).
    *   **`SERVICE_ACCOUNT_KEY_B64`**: El contenido codificado en Base64 de tu clave JSON de la cuenta de servicio de Google.
    *   **`GEMINI_API_KEY`**: Tu clave de API para el modelo Gemini.

### 6. Ejecutar la Aplicación Localmente

Una vez configurada, puedes ejecutar el servidor de desarrollo de Flask:

```bash
# Asegúrate de que tu entorno virtual esté activado
python main.py
```

La aplicación se iniciará en `http://localhost:8080`. Puedes activar el procesamiento de archivos enviando una solicitud HTTP POST a este endpoint. Por ejemplo, usando `curl`:

```bash
curl -X POST http://localhost:8080/
```

### 7. Ejecutar Pruebas

El proyecto incluye pruebas básicas para verificar la configuración y la funcionalidad.

```bash
# Asegúrate de que tu entorno virtual esté activado
# Ejecuta la prueba de importación de Gemini
python tests/test_gemini_import.py

# Ejecuta la prueba de integración (requiere una configuración correcta del .env y acceso a Google Cloud)
python tests/test_integration.py
```
*Nota: La prueba de integración (`test_integration.py`) solo pasará si tu archivo `.env` está configurado correctamente con credenciales válidas de Google Cloud y la cuenta de servicio tiene los permisos necesarios.*

## Despliegue en Google Cloud Run

La aplicación está diseñada para un despliegue sin servidor. Consulta la documentación de Google Cloud Run para ver los pasos detallados de despliegue. Consideraciones clave:

*   **Contenerización:** Utiliza el `Dockerfile` proporcionado (o crea uno si no está presente) para construir tu imagen de contenedor.
*   **Variables de Entorno:** Configura todas las variables de entorno requeridas en la configuración del servicio de Cloud Run.
*   **Punto de Entrada (Entrypoint):** Usa `gunicorn` como punto de entrada para producción: `gunicorn --bind :$PORT --workers 1 --threads 8 main:app`.
*   **Activación (Triggering):** El servicio puede ser activado mediante solicitudes HTTP, típicamente desde un programador (por ejemplo, Google Cloud Scheduler) u otros servicios en la nube.

## Convenciones de Desarrollo

*   **Configuración:** Toda la configuración se gestiona a través de variables de entorno, siguiendo los principios de la aplicación de 12 factores.
*   **Modularidad:** El código está organizado en funciones distintas para facilitar la lectura y el mantenimiento.
*   **Gestión de Estado:** La aplicación en sí misma no tiene estado; el `pageToken` para los cambios de Google Drive se persiste en un bucket de Google Cloud Storage.
*   **Manejo de Errores:** Se utilizan bloques `try...except` para una gestión robusta de errores.