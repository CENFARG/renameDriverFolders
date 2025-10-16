# main.py

import base64
import json
import os
from datetime import datetime
from io import BytesIO

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

# Cargar variables de entorno desde .env
load_dotenv()

# --- Configuración ---
# Estas variables deben ser configuradas como variables de entorno en tu servicio de Cloud Run/Function.

# ID de la carpeta raíz en Google Drive para iniciar el monitoreo.
ROOT_FOLDER_ID = os.environ.get("ROOT_FOLDER_ID")

# Nombres de las carpetas a monitorear (formato JSON como string, ej: '["Doc de Respaldo", "Otra Carpeta"]')
TARGET_FOLDER_NAMES = json.loads(os.environ.get("TARGET_FOLDER_NAMES", '["Doc de Respaldo"]'))

# Nombre del bucket de Google Cloud Storage para guardar el estado del token.
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
# Nombre del archivo en el bucket para guardar el token.
TOKEN_FILE_NAME = "drive_changes_token.json"

# ID de tu proyecto de Google Cloud.
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
# Región donde se desplegará el modelo de Gemini.
GCP_REGION = os.environ.get("GCP_REGION")

# Credenciales de la cuenta de servicio codificadas en Base64.
ENCODED_SERVICE_ACCOUNT_KEY = os.environ.get("SERVICE_ACCOUNT_KEY_B64")

# --- Decodificación de credenciales y configuración de clientes ---

# Decodificar las credenciales desde la variable de entorno.
SERVICE_ACCOUNT_KEY = base64.b64decode(ENCODED_SERVICE_ACCOUNT_KEY)
SERVICE_ACCOUNT_INFO = json.loads(SERVICE_ACCOUNT_KEY)

# Configurar credenciales para las APIs de Google.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/cloud-platform",
]

credentials = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO, scopes=SCOPES
)

# Inicializar clientes de las APIs.
try:
    drive_service = build("drive", "v3", credentials=credentials)
    storage_client = storage.Client(credentials=credentials)
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY")) # O configurar autenticación de GCP
    gemini_model = genai.GenerativeModel("gemini-pro")
except Exception as e:
    print(f"Error al inicializar los clientes de las APIs: {e}")
    # Manejar el error apropiadamente.
    
app = Flask(__name__)

# --- Funciones de Soporte ---

def get_last_token():
    """Recupera el último pageToken guardado desde Google Cloud Storage."""
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(TOKEN_FILE_NAME)
        if blob.exists():
            token_data = json.loads(blob.download_as_string())
            return token_data.get("pageToken")
    except Exception as e:
        print(f"No se pudo recuperar el token, se iniciará una nueva sincronización. Error: {e}")
    return None

def save_new_token(token):
    """Guarda el nuevo pageToken en Google Cloud Storage."""
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(TOKEN_FILE_NAME)
        token_data = {"pageToken": token}
        blob.upload_from_string(json.dumps(token_data), content_type="application/json")
        print(f"Nuevo token guardado exitosamente: {token}")
    except Exception as e:
        print(f"Error al guardar el nuevo token: {e}")

def find_target_folders_recursively(start_folder_id):
    """Encuentra todos los IDs de las carpetas con los nombres objetivo, de forma recursiva."""
    target_folders = set()
    query = f"trashed=false and mimeType='application/vnd.google-apps.folder'"
    page_token = None
    
    # Función interna para la recursión
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
                # Llamada recursiva para buscar en subcarpetas
                search(folder.get('id'))
            page_token = response.get('nextPageToken', None)
        except HttpError as error:
            print(f"Ocurrió un error al buscar carpetas: {error}")

    search(start_folder_id)
    print(f"Carpetas objetivo encontradas: {target_folders}")
    return list(target_folders)

def get_file_content(file_id):
    """Descarga y devuelve el contenido de un archivo desde Google Drive."""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_content = BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return file_content.getvalue().decode("utf-8", errors='ignore')
    except HttpError as error:
        print(f"Ocurrió un error al descargar el archivo {file_id}: {error}")
        return None

def analyze_content_with_gemini(content):
    """Usa la API de Gemini para extraer palabras clave y fecha del contenido."""
    if not content:
        return None
        
    prompt = f"""
    Analiza el siguiente texto y extrae la siguiente información en formato JSON:
    1.  "keywords": Una lista de 3 a 5 palabras clave muy relevantes que resuman el documento.
    2.  "date": La fecha principal del documento en formato AAAA-MM-DD. Si no encuentras una fecha clara, usa la fecha actual.

    Texto:
    ---
    {content[:4000]}
    ---

    Responde únicamente con el objeto JSON.
    """
    try:
        response = gemini_model.generate_content(prompt)
        # Limpiar y parsear la respuesta JSON
        json_response = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(json_response)
    except Exception as e:
        print(f"Error al analizar el contenido con Gemini: {e}")
        return {"keywords": ["generico"], "date": datetime.now().strftime("%Y-%m-%d")}

def rename_drive_file(file_id, new_name):
    """Renombra un archivo en Google Drive."""
    try:
        file_metadata = {'name': new_name}
        updated_file = drive_service.files().update(fileId=file_id, body=file_metadata, fields='id, name').execute()
        print(f"Archivo renombrado a: {updated_file.get('name')}")
        return updated_file.get('name')
    except HttpError as error:
        print(f"Ocurrió un error al renombrar el archivo: {error}")
        return None

def update_html_index(folder_id, original_name, new_name, summary, is_deleted=False):
    """Crea o actualiza el archivo index.html en una carpeta de Google Drive."""
    index_name = "index.html"
    index_file_id = None
    
    # Buscar si el índice ya existe
    try:
        query = f"'{folder_id}' in parents and name='{index_name}' and trashed=false"
        response = drive_service.files().list(q=query, fields='files(id)').execute()
        files = response.get('files', [])
        if files:
            index_file_id = files[0]['id']
    except HttpError as error:
        print(f"Error buscando el index.html: {error}")

    soup = None
    if index_file_id:
        # Descargar y parsear el índice existente
        html_content = get_file_content(index_file_id)
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
    
    if not soup:
        # Crear un nuevo HTML si no existe
        soup = BeautifulSoup("""
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
        """, "html.parser")

    tbody = soup.find('tbody')
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Buscar si ya existe una fila para este archivo
    row_id = f"file-{''.join(filter(str.isalnum, original_name))}"
    existing_row = soup.find('tr', id=row_id)

    if is_deleted:
        if existing_row:
            # Actualizar la fila para marcar como eliminado
            status_cell = existing_row.find_all('td')[3]
            status_cell.string = f"Eliminado"
            date_cell = existing_row.find_all('td')[4]
            date_cell.string = now_str
        else:
            # Añadir una nueva fila para el archivo eliminado si no existía
            new_row = soup.new_tag('tr', id=row_id)
            new_row.append(soup.new_tag('td', string=original_name))
            new_row.append(soup.new_tag('td', string="N/A"))
            new_row.append(soup.new_tag('td', string="Archivo eliminado del registro."))
            new_row.append(soup.new_tag('td', string=f"Eliminado"))
            new_row.append(soup.new_tag('td', string=now_str))
            tbody.append(new_row)
    else:
         if existing_row:
             # Si por alguna razón se vuelve a crear, se actualiza la fila
             existing_row.find_all('td')[1].string = new_name
             existing_row.find_all('td')[2].string = summary
             existing_row.find_all('td')[3].string = "Activo"
             existing_row.find_all('td')[4].string = now_str
         else:
            # Crear nueva fila para el nuevo archivo
            new_row = soup.new_tag('tr', id=row_id)
            new_row.append(soup.new_tag('td', string=original_name))
            new_row.append(soup.new_tag('td', string=new_name))
            new_row.append(soup.new_tag('td', string=summary))
            new_row.append(soup.new_tag('td', string="Activo"))
            new_row.append(soup.new_tag('td', string=now_str))
            tbody.append(new_row)

    # Subir el archivo HTML actualizado
    html_bytes = BytesIO(soup.prettify("utf-8"))
    media = MediaIoBaseUpload(html_bytes, mimetype='text/html', resumable=True)
    
    file_metadata = {'name': index_name, 'mimeType': 'text/html'}
    if index_file_id:
        drive_service.files().update(fileId=index_file_id, media_body=media).execute()
        print(f"Índice HTML actualizado en la carpeta {folder_id}.")
    else:
        file_metadata['parents'] = [folder_id]
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Índice HTML creado en la carpeta {folder_id}.")


# --- Función Principal (Endpoint) ---

@app.route("/", methods=["GET"])
def index():
    """Página principal que muestra información sobre la aplicación."""
    return """
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
    """

@app.route("/", methods=["POST"])
def process_drive_changes():
    """Punto de entrada principal para procesar los cambios en Google Drive."""
    
    print("Iniciando la revisión de cambios en Google Drive...")
    
    # 1. Encontrar las carpetas objetivo
    target_folder_ids = find_target_folders_recursively(ROOT_FOLDER_ID)
    if not target_folder_ids:
        return "No se encontraron carpetas objetivo para monitorear.", 200

    # 2. Obtener el token de la última ejecución
    page_token = get_last_token()
    if not page_token:
        # Si no hay token, obtener el token de inicio y guardarlo para la próxima vez
        response = drive_service.changes().getStartPageToken().execute()
        page_token = response.get('startPageToken')
        save_new_token(page_token)
        print("No se encontró token. Se obtuvo uno nuevo. La próxima ejecución procesará los cambios.")
        return "Token inicial obtenido. La próxima ejecución procesará los cambios.", 200

    # 3. Consultar los cambios desde el último token
    while page_token is not None:
        response = drive_service.changes().list(pageToken=page_token,
                                                spaces='drive',
                                                fields='nextPageToken, newStartPageToken, changes(fileId, removed, file(name, parents, mimeType))').execute()
        
        for change in response.get('changes', []):
            file_id = change.get('fileId')
            if change.get('removed'):
                # Archivo eliminado
                # NOTA: La API de cambios a veces no provee metadatos del archivo eliminado.
                # Se requiere una lógica más compleja (ej. base de datos) para asociar el ID con el nombre anterior.
                # Por simplicidad, aquí se omite la actualización del índice en borrado.
                print(f"Archivo con ID {file_id} fue eliminado.")
                # Aquí iría la lógica para actualizar el índice marcando el archivo como eliminado.
                
            else:
                # Archivo añadido o modificado
                file_info = change.get('file')
                if not file_info or file_info.get('mimeType') == 'application/vnd.google-apps.folder':
                    continue # Ignorar carpetas

                file_parents = file_info.get('parents')
                if not file_parents or file_parents[0] not in target_folder_ids:
                    continue # El archivo no está en una de nuestras carpetas objetivo

                original_name = file_info.get('name')
                
                # Evitar procesar el propio índice o archivos ya procesados
                if original_name == "index.html" or "DOCPROCESADO" in original_name:
                    continue
                    
                print(f"Nuevo archivo detectado: '{original_name}' (ID: {file_id})")

                # 4. Procesar el nuevo archivo
                content = get_file_content(file_id)
                if content:
                    analysis = analyze_content_with_gemini(content)
                    if analysis:
                        # 5. Renombrar el archivo
                        keywords_str = "_".join(analysis.get("keywords", ["doc"])).replace(" ", "")
                        date_str = analysis.get("date", datetime.now().strftime("%Y-%m-%d"))
                        
                        file_extension = os.path.splitext(original_name)[1]
                        new_name = f"{date_str}_{keywords_str}_DOCPROCESADO{file_extension}"
                        
                        renamed_file = rename_drive_file(file_id, new_name)

                        # 6. Actualizar el índice HTML
                        if renamed_file:
                             summary = " ".join(analysis.get("keywords", []))
                             update_html_index(file_parents[0], original_name, renamed_file, summary)

        # 7. Guardar el token para la próxima ejecución
        if 'newStartPageToken' in response:
            save_new_token(response['newStartPageToken'])
        page_token = response.get('nextPageToken')

    return "Proceso de revisión de cambios completado.", 200

if __name__ == "__main__":
    # Para pruebas locales. En Cloud Run se usa un servidor WSGI como Gunicorn.
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))