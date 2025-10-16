# Guía de Despliegue en Google Cloud Run

Esta guía te ayudará a desplegar la aplicación `renameDriverFolders` en Google Cloud Run. Se cubren dos métodos: el despliegue recomendado a través de **VS Code con la extensión Cloud Code** (más sencillo para usuarios no expertos) y un método manual usando scripts.

## 1. Despliegue con VS Code y Cloud Code (Recomendado)

Este es el método más sencillo y recomendado para desplegar la aplicación en Google Cloud Run, especialmente si no estás familiarizado con la línea de comandos de `gcloud`.

### Requisitos Previos

1.  **VS Code**: Asegúrate de tener Visual Studio Code instalado.
2.  **Extensión Cloud Code**: Instala la extensión "Cloud Code" para VS Code. Puedes encontrarla en el Marketplace de VS Code.
3.  **Google Cloud SDK**: Asegúrate de tener `gcloud CLI` instalado y configurado en tu máquina. Cloud Code lo utilizará internamente.
4.  **Autenticación**: Debes estar autenticado en `gcloud` con una cuenta que tenga los permisos necesarios para:
    *   Construir imágenes de Docker (Cloud Build).
    *   Subir imágenes a Google Container Registry (o Artifact Registry).
    *   Desplegar servicios en Google Cloud Run.
    *   Acceder a Google Cloud Storage y Vertex AI (para Gemini).
    *   Acceder a Google Drive.
    Puedes autenticarte ejecutando `gcloud auth login` y `gcloud config set project [TU_PROYECTO_ID]` en tu terminal.

### Configuración de Variables de Entorno con Secret Manager

Para las variables sensibles (`SERVICE_ACCOUNT_KEY_B64` y `GEMINI_API_KEY`), utilizaremos **Google Secret Manager**. Esto es una buena práctica de seguridad y facilita la gestión de credenciales.

1.  **Crea los Secretos en Google Secret Manager**:
    *   Ve a la consola de Google Cloud y busca "Secret Manager".
    *   Crea un nuevo secreto para `SERVICE_ACCOUNT_KEY_B64`. El valor del secreto debe ser el contenido Base64 de tu clave JSON de la cuenta de servicio.
    *   Crea otro secreto para `GEMINI_API_KEY`. El valor del secreto debe ser tu clave de API de Gemini.
    *   Asegúrate de que la cuenta de servicio que usará Cloud Run tenga permisos para acceder a estos secretos.

2.  **Configura las Variables de Entorno en Cloud Code**:
    *   En VS Code, abre la paleta de comandos (Ctrl+Shift+P o Cmd+Shift+P) y busca "Cloud Code: Deploy to Cloud Run".
    *   Sigue los pasos del asistente. Cuando llegues a la sección de "Environment Variables", deberás configurar:
        *   **Variables normales**: `ROOT_FOLDER_ID`, `TARGET_FOLDER_NAMES`, `GCS_BUCKET_NAME`, `GCP_PROJECT_ID`, `GCP_REGION`. Introduce sus valores directamente.
        *   **Variables de Secret Manager**: Para `SERVICE_ACCOUNT_KEY_B64` y `GEMINI_API_KEY`, selecciona la opción para referenciar un secreto de Secret Manager. Deberás especificar el nombre del secreto que creaste y la versión (normalmente `latest`).

### Pasos para el Despliegue con Cloud Code

1.  **Abre el proyecto** `renameDriverFolders` en VS Code.
2.  **Abre la paleta de comandos** (Ctrl+Shift+P o Cmd+Shift+P).
3.  **Busca y selecciona "Cloud Code: Deploy to Cloud Run"**.
4.  **Sigue el asistente**:
    *   Selecciona tu proyecto de Google Cloud.
    *   Elige la región de Cloud Run.
    *   Configura las variables de entorno (como se explicó anteriormente, usando Secret Manager para las sensibles).
    *   Asegúrate de que el `Dockerfile` sea detectado correctamente.
    *   Confirma el despliegue.

Cloud Code se encargará de construir la imagen de Docker, subirla a Google Container Registry (o Artifact Registry) y desplegarla en Cloud Run, inyectando las variables de entorno y los secretos configurados.

## 2. Despliegue Manual (Usando `deploy_manual.bat`)

Este método es para usuarios más avanzados que prefieren usar la línea de comandos.

### Requisitos Previos

1.  **Google Cloud SDK**: Asegúrate de tener `gcloud CLI` instalado y configurado en tu máquina.
2.  **Autenticación**: Debes estar autenticado en `gcloud` con una cuenta que tenga los permisos necesarios (ver sección anterior).
3.  **Variables de Entorno**: Tu archivo `.env` local contiene las configuraciones necesarias. **Antes de ejecutar el script `deploy_manual.bat`, debes asegurarte de que estas variables de entorno estén configuradas en tu sesión de terminal.** El script `deploy_manual.bat` las leerá de tu entorno de shell para pasarlas a Cloud Run.

    **Ejemplo de cómo configurar una variable de entorno en Windows CMD:**
    ```cmd
    set ROOT_FOLDER_ID="tu_id_de_carpeta"
    set TARGET_FOLDER_NAMES="[\"Doc de Respaldo\"]" REM Nota: las comillas internas deben escaparse
    set GCS_BUCKET_NAME="tu_bucket"
    set GCP_PROJECT_ID="tu_proyecto"
    set GCP_REGION="tu_region"
    set SERVICE_ACCOUNT_KEY_B64="tu_clave_base64"
    set GEMINI_API_KEY="tu_api_key"
    ```
    **¡Importante!** Para `TARGET_FOLDER_NAMES`, si contiene comillas dobles internas, estas deben ser escapadas con una barra invertida (`\"`) cuando se define como variable de entorno en la línea de comandos de Windows.

### Pasos para el Despliegue Manual

1.  **Navega al directorio `deployment`** en tu terminal.

    ```cmd
    cd deployment
    ```

2.  **Configura las variables de entorno** necesarias en tu sesión de terminal (como se explica en la sección de Requisitos Previos).

3.  **Ejecuta el script de despliegue manual**:

    ```cmd
    deploy_manual.bat
    ```

El script realizará los siguientes pasos:

*   Construirá la imagen de Docker de tu aplicación y la subirá a Google Container Registry.
*   Desplegará esta imagen como un nuevo servicio en Google Cloud Run en la región especificada.
*   Configurará las variables de entorno en el servicio de Cloud Run utilizando las que hayas definido en tu sesión de terminal.
*   El servicio se configurará para permitir invocaciones no autenticadas (`--allow-unauthenticated`), lo cual es útil para pruebas, pero considera cambiarlo en producción.

## Después del Despliegue

Una vez que el despliegue sea exitoso, `gcloud` te proporcionará la URL del servicio de Cloud Run. Podrás acceder a tu aplicación a través de esa URL.

Para activar el procesamiento de archivos, deberás enviar una petición `POST` a esa URL (similar a cómo lo harías localmente con `curl`).