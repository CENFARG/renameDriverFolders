# main.py

# English: Import necessary libraries.
# Español: Importación de las bibliotecas necesarias.
import base64
import json
import os
from datetime import datetime
from io import BytesIO

# English: Import third-party libraries for Google APIs, web framework, and environment management.
# Español: Importación de bibliotecas de terceros para las APIs de Google, el framework web y la gestión del entorno.
import google.auth
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# English: Load environment variables from a .env file for local development.
# Español: Carga las variables de entorno desde un archivo .env para el desarrollo local.
load_dotenv()

# --- Configuration / Configuración ---
# English: These variables are loaded from environment variables. In a production environment like Cloud Run, they must be set in the service's configuration.
# Español: Estas variables se cargan desde las variables de entorno. En un entorno de producción como Cloud Run, deben configurarse en la configuración del servicio.

# English: The root folder ID in Google Drive where monitoring will start.
# Español: ID de la carpeta raíz en Google Drive donde comenzará el monitoreo.
ROOT_FOLDER_ID = os.environ.get("ROOT_FOLDER_ID")

# English: A JSON string of folder names to monitor, e.g., '["Backup Docs", "Invoices"]'.
# Español: Una cadena JSON con los nombres de las carpetas a monitorear, ej: '["Doc de Respaldo", "Facturas"]'.
TARGET_FOLDER_NAMES = json.loads(os.environ.get("TARGET_FOLDER_NAMES", '["Doc de Respaldo"]'))

# English: The name of the Google Cloud Storage bucket used to store the state token.
# Español: Nombre del bucket de Google Cloud Storage utilizado para guardar el token de estado.
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
# English: The name of the file within the bucket to store the token.
# Español: Nombre del archivo en el bucket para guardar el token.
TOKEN_FILE_NAME = "drive_changes_token.json"

# English: Your Google Cloud Project ID.
# Español: ID de tu proyecto de Google Cloud.
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
# English: The region where the Gemini model is deployed.
# Español: Región donde se despliega el modelo de Gemini.
GCP_REGION = os.environ.get("GCP_REGION")

# English: The service account key, Base64 encoded.
# Español: La clave de la cuenta de servicio, codificada en Base64.
ENCODED_SERVICE_ACCOUNT_KEY = os.environ.get("SERVICE_ACCOUNT_KEY_B64")

# --- Credential Decoding and API Client Setup / Decodificación de Credenciales y Configuración de Clientes ---

# English: Decode the service account credentials from the environment variable.
# Español: Decodifica las credenciales de la cuenta de servicio desde la variable de entorno.
SERVICE_ACCOUNT_KEY = base64.b64decode(ENCODED_SERVICE_ACCOUNT_KEY)
SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_KEY)

# English: Define the scopes required for the Google APIs.
# Español: Define los alcances (scopes) necesarios para las APIs de Google.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/cloud-platform",
]

# English: Create credentials from the service account info.
# Español: Crea las credenciales a partir de la información de la cuenta de servicio.
credentials = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO, scopes=SCOPES
)

# English: Initialize the API clients for Drive, Storage, and Gemini.
# Español: Inicializa los clientes de las APIs para Drive, Storage y Gemini.
try:
    drive_service = build("drive", "v3", credentials=credentials)
    storage_client = storage.Client(credentials=credentials)
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    gemini_model = genai.GenerativeModel("gemini-pro")
except Exception as e:
    print(f"Error initializing API clients: {e}")
    # English: Handle the error appropriately in a production environment.
    # Español: Manejar el error apropiadamente en un entorno de producción.
    
# English: Initialize the Flask application.
# Español: Inicializa la aplicación Flask.
app = Flask(__name__)

# --- Helper Functions / Funciones de Soporte ---

def get_last_token():
    """
    English: Retrieves the last saved pageToken from Google Cloud Storage.
    Español: Recupera el último pageToken guardado desde Google Cloud Storage.
    """
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(TOKEN_FILE_NAME)
        if blob.exists():
            token_data = json.loads(blob.download_as_string())
            return token_data.get("pageToken")
    except Exception as e:
        print(f"Could not retrieve token, a new sync will be started. Error: {e}")
    return None

def save_new_token(token):
    """
    English: Saves the new pageToken to Google Cloud Storage.
    Español: Guarda el nuevo pageToken en Google Cloud Storage.
    """
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(TOKEN_FILE_NAME)
        token_data = {"pageToken": token}
        blob.upload_from_string(json.dumps(token_data), content_type="application/json")
        print(f"New token saved successfully: {token}")
    except Exception as e:
        print(f"Error saving new token: {e}")

def find_target_folders_recursively(start_folder_id):
    """
    English: Recursively finds all folder IDs with the target names.
    Español: Encuentra de forma recursiva todos los IDs de las carpetas con los nombres objetivo.
    """
    target_folders = set()
    query = f"trashed=false and mimeType='application/vnd.google-apps.folder'"
    page_token = None
    
    # English: Inner function for recursion.
    # Español: Función interna para la recursión.
    def search(folder_id):
        nonlocal page_token
        q = f"'{folder_id}' in parents and {query}"
        try:
            response = drive_service.files().list(q=q,
                                                  spaces='drive',
                                                  fields='nextPageToken, files(id, name)',
                                                  pageToken=page_token).execute()
            for folder in response.get('files', []):
                if folder.get('name') in TARGET_FOLDER_NAMES:
                    target_folders.add(folder.get('id'))
                # English: Recursive call to search in subfolders.
                # Español: Llamada recursiva para buscar en subcarpetas.
                search(folder.get('id'))
            page_token = response.get('nextPageToken', None)
        except HttpError as error:
            print(f"An error occurred while searching for folders: {error}")

    search(start_folder_id)
    print(f"Target folders found: {target_folders}")
    return list(target_folders)

def get_file_content(file_id):
    """
    English: Downloads and returns the content of a file from Google Drive.
    Español: Descarga y devuelve el contenido de un archivo desde Google Drive.
    """
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_content = BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return file_content.getvalue().decode("utf-8", errors='ignore')
    except HttpError as error:
        print(f"An error occurred while downloading the file {file_id}: {error}")
        return None

def analyze_content_with_gemini(content):
    """
    English: Uses the Gemini API to extract keywords and a date from the content.
    Español: Usa la API de Gemini para extraer palabras clave y una fecha del contenido.
    """
    if not content:
        return None
        
    # English: The prompt instructs the AI to return a JSON object with keywords and a date.
    # Español: El prompt instruye a la IA para que devuelva un objeto JSON con palabras clave y una fecha.
    prompt = f'''
    Analyze the following text and extract the following information in JSON format:
    1.  "keywords": A list of 3 to 5 highly relevant keywords that summarize the document.
    2.  "date": The main date of the document in YYYY-MM-DD format. If you can't find a clear date, use the current date.

    Text:
    ---
    {content[:4000]}
    ---

    Respond only with the JSON object.
    '''
    try:
        response = gemini_model.generate_content(prompt)
        # English: Clean up and parse the JSON response from the model.
        # Español: Limpia y parsea la respuesta JSON del modelo.
        json_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_response)
    except Exception as e:
        print(f"Error analyzing content with Gemini: {e}")
        # English: Fallback in case of an error during analysis.
        # Español: Respuesta de respaldo en caso de error durante el análisis.
        return {"keywords": ["generico"], "date": datetime.now().strftime("%Y-%m-%d")}

def rename_drive_file(file_id, new_name):
    """
    English: Renames a file in Google Drive.
    Español: Renombra un archivo en Google Drive.
    """
    try:
        file_metadata = {'name': new_name}
        updated_file = drive_service.files().update(fileId=file_id, body=file_metadata, fields='id, name').execute()
        print(f"File renamed to: {updated_file.get('name')}")
        return updated_file.get('name')
    except HttpError as error:
        print(f"An error occurred while renaming the file: {error}")
        return None

def update_html_index(folder_id, original_name, new_name, summary, is_deleted=False):
    """
    English: Creates or updates an index.html file in a Google Drive folder.
    Español: Crea o actualiza un archivo index.html en una carpeta de Google Drive.
    """
    index_name = "index.html"
    index_file_id = None
    
    # English: Check if the index file already exists.
    # Español: Comprueba si el archivo de índice ya existe.
    try:
        query = f"'{folder_id}' in parents and name='{index_name}' and trashed=false"
        response = drive_service.files().list(q=query, fields='files(id)').execute()
        files = response.get('files', [])
        if files:
            index_file_id = files[0]['id']
    except HttpError as error:
        print(f"Error searching for index.html: {error}")

    soup = None
    if index_file_id:
        # English: If it exists, download and parse the existing index.
        # Español: Si existe, descarga y parsea el índice existente.
        html_content = get_file_content(index_file_id)
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
    
    if not soup:
        # English: If it doesn't exist, create a new HTML structure.
        # Español: Si no existe, crea una nueva estructura HTML.
        soup = BeautifulSoup('''
        <html>
            <head><title>Índice de Documentos</title></head>
            <body>
                <h1>Índice de Documentos</h1>
                <table border="1">
                    <thead>
                        <tr>
                            <th>Nombre Original</th>
                            <th>Nuevo Nombre (Procesado)</th>
                            <th>Resumen</th>
                            <th>Estado</th>
                            <th>Fecha de Actualización</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </body>
        </html>
        ''', "html.parser")

    tbody = soup.find('tbody')
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # English: Create a unique ID for the row based on the original filename.
    # Español: Crea un ID único para la fila basado en el nombre de archivo original.
    row_id = f"file-{''.join(filter(str.isalnum, original_name))}"
    existing_row = soup.find('tr', id=row_id)

    if is_deleted:
        if existing_row:
            # English: If the file was deleted, update the row to reflect this.
            # Español: Si el archivo fue eliminado, actualiza la fila para reflejarlo.
            existing_row.find_all('td')[3].string = f"Eliminado"
            existing_row.find_all('td')[4].string = now_str
        else:
            # English: If the row doesn't exist, add a new one for the deleted file.
            # Español: Si la fila no existe, añade una nueva para el archivo eliminado.
            new_row = soup.new_tag('tr', id=row_id)
            new_row.append(soup.new_tag('td', string=original_name))
            new_row.append(soup.new_tag('td', string="N/A"))
            new_row.append(soup.new_tag('td', string="Archivo eliminado del registro."))
            new_row.append(soup.new_tag('td', string=f"Eliminado"))
            new_row.append(soup.new_tag('td', string=now_str))
            tbody.append(new_row)
    else:
         if existing_row:
             # English: If the file is re-processed, update the existing row.
             # Español: Si el archivo se vuelve a procesar, actualiza la fila existente.
             existing_row.find_all('td')[1].string = new_name
             existing_row.find_all('td')[2].string = summary
             existing_row.find_all('td')[3].string = "Activo"
             existing_row.find_all('td')[4].string = now_str
         else:
            # English: Create a new row for the new file.
            # Español: Crea una nueva fila para el nuevo archivo.
            new_row = soup.new_tag('tr', id=row_id)
            new_row.append(soup.new_tag('td', string=original_name))
            new_row.append(soup.new_tag('td', string=new_name))
            new_row.append(soup.new_tag('td', string=summary))
            new_row.append(soup.new_tag('td', string="Activo"))
            new_row.append(soup.new_tag('td', string=now_str))
            tbody.append(new_row)

    # English: Upload the updated HTML file back to Google Drive.
    # Español: Sube el archivo HTML actualizado de vuelta a Google Drive.
    html_bytes = BytesIO(soup.prettify("utf-8"))
    media = MediaIoBaseUpload(html_bytes, mimetype='text/html', resumable=True)
    
    file_metadata = {'name': index_name, 'mimeType': 'text/html'}
    if index_file_id:
        # English: If the index existed, update it.
        # Español: Si el índice existía, actualízalo.
        drive_service.files().update(fileId=index_file_id, media_body=media).execute()
        print(f"HTML index updated in folder {folder_id}.")
    else:
        # English: If not, create a new index file.
        # Español: Si no, crea un nuevo archivo de índice.
        file_metadata['parents'] = [folder_id]
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"HTML index created in folder {folder_id}.")


# --- Main Functions (Endpoints) / Funciones Principales (Endpoints) ---

@app.route("/", methods=["GET"])
def index():
    """
    English: Main page that displays information about the application.
    Español: Página principal que muestra información sobre la aplicación.
    """
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>renameDriverFolders - API</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .info { background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .endpoint { background: #e8f4fd; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; }
            code { background: #f8f8f8; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 renameDriverFolders API</h1>
            <div class="info">
                <h2>Información de la Aplicación</h2>
                <p><strong>Estado:</strong> <span style="color: green;">✅ Funcionando</span></p>
                <p><strong>Puerto:</strong> 8080</p>
                <p><strong>Framework:</strong> Flask</p>
                <p><strong>Función:</strong> Procesamiento automático de archivos en Google Drive</p>
            </div>

            <div class="endpoint">
                <h3>📡 Endpoints Disponibles</h3>
                <p><strong>GET /</strong> - Esta página de información</p>
                <p><strong>POST /</strong> - Procesar cambios en Google Drive</p>
            </div>

            <div class="info">
                <h3>📋 Uso</h3>
                <p>Para procesar cambios en Google Drive, envía una petición POST a esta URL.</p>
                <p>Ejemplo con curl:</p>
                <code>curl -X POST http://127.0.0.1:8080/</code>
            </div>

            <div class="info">
                <h3>⚙️ Configuración</h3>
                <p>Asegúrate de tener configuradas las siguientes variables de entorno:</p>
                <ul>
                    <li><code>ROOT_FOLDER_ID</code> - ID de la carpeta raíz en Google Drive</li>
                    <li><code>TARGET_FOLDER_NAMES</code> - Nombres de carpetas a monitorear</li>
                    <li><code>GCS_BUCKET_NAME</code> - Bucket de Google Cloud Storage</li>
                    <li><code>GEMINI_API_KEY</code> - Clave API de Google Gemini</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route("/", methods=["POST"])
def process_drive_changes():
    """
    English: Main entry point to process changes in Google Drive. This is triggered by a POST request.
    Español: Punto de entrada principal para procesar los cambios en Google Drive. Se activa mediante una solicitud POST.
    """
    
    print("Starting to check for changes in Google Drive...")
    
    # English: 1. Find the target folders to monitor.
    # Español: 1. Encontrar las carpetas objetivo a monitorear.
    target_folder_ids = find_target_folders_recursively(ROOT_FOLDER_ID)
    if not target_folder_ids:
        return "No target folders found to monitor.", 200

    # English: 2. Get the token from the last execution.
    # Español: 2. Obtener el token de la última ejecución.
    page_token = get_last_token()
    if not page_token:
        # English: If no token is found, get a new start token and save it for the next run.
        # Español: Si no se encuentra un token, obtener un nuevo token de inicio y guardarlo para la próxima ejecución.
        response = drive_service.changes().getStartPageToken().execute()
        page_token = response.get('startPageToken')
        save_new_token(page_token)
        print("No token found. A new one was obtained. The next run will process changes.")
        return "Initial token obtained. The next run will process changes.", 200

    # English: 3. Query for changes since the last token.
    # Español: 3. Consultar los cambios desde el último token.
    while page_token is not None:
        response = drive_service.changes().list(pageToken=page_token,
                                                spaces='drive',
                                                fields='nextPageToken, newStartPageToken, changes(fileId, removed, file(name, parents, mimeType))').execute()
        
        for change in response.get('changes', []):
            file_id = change.get('fileId')
            if change.get('removed'):
                # English: A file was deleted. Complex logic is needed to associate the ID with a past name.
                # Español: Un archivo fue eliminado. Se necesita una lógica compleja para asociar el ID con un nombre anterior.
                print(f"File with ID {file_id} was deleted.")
                # English: Logic to update the index marking the file as deleted would go here.
                # Español: Aquí iría la lógica para actualizar el índice marcando el archivo como eliminado.
                
            else:
                # English: A file was added or modified.
                # Español: Un archivo fue añadido o modificado.
                file_info = change.get('file')
                if not file_info or file_info.get('mimeType') == 'application/vnd.google-apps.folder':
                    continue # English: Ignore folders.

                file_parents = file_info.get('parents')
                if not file_parents or file_parents[0] not in target_folder_ids:
                    continue # English: The file is not in one of our target folders.

                original_name = file_info.get('name')
                
                # English: Avoid processing the index file itself or already processed files.
                # Español: Evita procesar el propio archivo de índice o archivos ya procesados.
                if original_name == "index.html" or "DOCPROCESADO" in original_name:
                    continue
                    
                print(f"New file detected: '{original_name}' (ID: {file_id})")

                # English: 4. Process the new file.
                # Español: 4. Procesar el nuevo archivo.
                content = get_file_content(file_id)
                if content:
                    analysis = analyze_content_with_gemini(content)
                    if analysis:
                        # English: 5. Rename the file based on the analysis.
                        # Español: 5. Renombrar el archivo basándose en el análisis.
                        keywords_str = "_".join(analysis.get("keywords", ["doc"])).replace(" ", "")
                        date_str = analysis.get("date", datetime.now().strftime("%Y-%m-%d"))
                        
                        file_extension = os.path.splitext(original_name)[1]
                        new_name = f"{date_str}_{keywords_str}_DOCPROCESADO{file_extension}"
                        
                        renamed_file = rename_drive_file(file_id, new_name)

                        # English: 6. Update the HTML index.
                        # Español: 6. Actualizar el índice HTML.
                        if renamed_file:
                             summary = " ".join(analysis.get("keywords", []))
                             update_html_index(file_parents[0], original_name, renamed_file, summary)

        # English: 7. Save the new token for the next execution.
        # Español: 7. Guardar el nuevo token para la próxima ejecución.
        if 'newStartPageToken' in response:
            save_new_token(response['newStartPageToken'])
        page_token = response.get('nextPageToken')

    return "Change review process completed.", 200

# English: Main execution block for local testing. In Cloud Run, a WSGI server like Gunicorn is used.
# Español: Bloque de ejecución principal para pruebas locales. En Cloud Run se utiliza un servidor WSGI como Gunicorn.
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))