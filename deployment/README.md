# Guía de Despliegue en Google Cloud Run con Cloud Code

Esta guía detalla el proceso para desplegar la aplicación `renameDriverFolders` en Google Cloud Run, utilizando la extensión [Cloud Code para VS Code](https://cloud.google.com/code/docs/vscode/install) y gestionando los secretos con [Google Secret Manager](https://cloud.google.com/secret-manager).

## 1. Prerrequisitos

Antes de comenzar, asegúrate de tener instalado y configurado lo siguiente:

1. **Google Cloud SDK:** [Instrucciones de instalación](https://cloud.google.com/sdk/docs/install).
2. **Docker:** Debe estar instalado y corriendo en tu máquina. [Instrucciones de instalación](https://docs.docker.com/get-docker/).
3. **Visual Studio Code:** [Descargar aquí](https://code.visualstudio.com/).
4. **Extensión Cloud Code para VS Code:** [Instalar desde el Marketplace](https://marketplace.visualstudio.com/items?itemName=GoogleCloudTools.cloudcode).

## 2. Configuración de Secret Manager

Para mantener la seguridad, todas las variables sensibles se gestionarán a través de Secret Manager. Debes crear un secreto por cada variable de entorno requerida.

**Pasos:**

1. Ve a la [página de Secret Manager](https://console.cloud.google.com/security/secret-manager) en tu Google Cloud Console.
2. Asegúrate de estar en el proyecto correcto.
3. Haz clic en **"Crear Secreto"** y crea los siguientes secretos. El valor de cada secreto debe ser el mismo que tienes en tu archivo `.env` local.

| Nombre del Secreto          | Valor del Secreto                                        |
| --------------------------- | -------------------------------------------------------- |
| `ROOT_FOLDER_ID`          | El ID de la carpeta raíz de Google Drive a monitorear.  |
| `GCS_BUCKET_NAME`         | El nombre de tu bucket de Google Cloud Storage.          |
| `SERVICE_ACCOUNT_KEY_B64` | La clave de tu cuenta de servicio, codificada en Base64. |
| `DRIVE_IMPERSONATED_USER` | El email del usuario a suplantar en Google Drive.        |
| `GEMINI_API_KEY`          | Tu clave de API para el modelo Gemini.                   |

**Importante:** Al crear cada secreto, asígnale el nombre exacto como se muestra en la tabla.

## 3. Despliegue con la Extensión Cloud Code

Cloud Code simplifica enormemente el proceso de construcción del contenedor y despliegue.

**Pasos:**

1. Abre este proyecto en VS Code.
2. Abre la paleta de comandos: `Ctrl+Shift+P` (o `Cmd+Shift+P` en Mac).
3. Escribe y selecciona **`Cloud Code: Deploy to Cloud Run`**.
4. Aparecerá un panel de configuración. Rellénalo de la siguiente manera:

   * **Service name:** Elige un nombre para tu servicio (ej. `renamedriverfolders`).
   * **Region:** Selecciona la región donde quieres desplegar (ej. `us-central1`).
   * **Authentication:** Selecciona **`Allow unauthenticated invocations`**. La seguridad la manejaremos con Cloud Scheduler.
5. **Vincular los Secretos:** Esta es la parte más importante.

   * Expande la sección **`Environment variables`**.
   * Haz clic en **`Add Environment Variable`** cinco veces para crear cinco entradas.
   * Para cada entrada, configúrala de la siguiente manera:

| Name                        | Type       | Key                                  |
| --------------------------- | ---------- | ------------------------------------ |
| `ROOT_FOLDER_ID`          | `Secret` | `ROOT_FOLDER_ID` (latest)          |
| `GCS_BUCKET_NAME`         | `Secret` | `GCS_BUCKET_NAME` (latest)         |
| `SERVICE_ACCOUNT_KEY_B64` | `Secret` | `SERVICE_ACCOUNT_KEY_B64` (latest) |
| `DRIVE_IMPERSONATED_USER` | `Secret` | `DRIVE_IMPERSONATED_USER` (latest) |
| `GEMINI_API_KEY`          | `Secret` | `GEMINI_API_KEY` (latest)          |

    *   Para cada una, en`Type`, selecciona `Secret`. En `Key`, busca y selecciona el secreto correspondiente que creaste en el paso anterior, asegurándote de elegir la versión `latest`.

6. Haz clic en el botón **`Deploy`**.

Cloud Code ahora construirá la imagen de Docker, la subirá a Google Container Registry y desplegará tu servicio en Cloud Run con la configuración y los secretos especificados. Al finalizar, te proporcionará la URL del servicio desplegado.

## 4. Configuración de Cloud Scheduler (Ejecución Periódica)

Finalmente, crearemos una tarea programada para que llame a nuestra aplicación automáticamente.

**Pasos:**

1. Ve a la [página de Cloud Scheduler](https://console.cloud.google.com/cloudscheduler) en tu Google Cloud Console.
2. Haz clic en **"Crear un trabajo"**.
3. **Define la frecuencia:** Usa un formato cron. Por ejemplo, para ejecutarlo cada hora, escribe `0 * * * *`.
4. **Configura el destino:**
   * **Tipo de destino:** `HTTP`
   * **URL:** Pega la URL de tu servicio de Cloud Run que obtuviste en el paso anterior.
   * **Método HTTP:** `POST`
5. **Configura la autenticación:**
   * **Añadir encabezado de autenticación:** `OIDC token`.
   * **Cuenta de servicio:** Selecciona una cuenta de servicio que tenga permisos para invocar servicios de Cloud Run (puedes usar la cuenta de servicio de cómputo por defecto o crear una específica para mayor seguridad).
6. Haz clic en **"Crear"**.

¡Listo! Ahora tienes un sistema completamente automatizado que se ejecutará en la frecuencia que definiste, procesando tus archivos de Google Drive de forma segura y eficiente.
