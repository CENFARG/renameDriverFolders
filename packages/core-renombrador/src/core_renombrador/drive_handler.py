# packages/core-renombrador/src/core_renombrador/drive_handler.py

import os
import json
import logging
from io import BytesIO
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Importaciones de nuestro paquete core-renombrador
from .content_extractor import ContentExtractor
from .config_manager import ConfigManager # Importar ConfigManager
from .logger_manager import LoggerManager # Importar LoggerManager

# Importaciones de terceros
import google.generativeai as genai
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DriveHandler:
    def __init__(self, credentials, storage_client: storage.Client, config_manager: ConfigManager):
        self.drive_service = build("drive", "v3", credentials=credentials)
        self.storage_client = storage_client
        self.config_manager = config_manager
        
        # Cargar variables de entorno necesarias para Gemini
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip().strip("'\"")
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY no configurada. El análisis con Gemini fallará.")
            self.gemini_model = None
        else:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel(config_manager.get_setting("gemini.model_name", "gemini-2.5-flash"))

        self.target_folder_names = config_manager.get_setting("google_cloud.target_folder_names", ["doc de respaldo"])

    def find_target_folders_recursively(self, start_folder_id: str) -> list:
        """
        Busca recursivamente carpetas objetivo dentro de un ID de carpeta inicial.
        """
        if not self.drive_service:
            logger.error("Drive service is not available. Cannot search for folders.")
            return []
            
        target_folders = set()
        query = f"trashed=false and mimeType='application/vnd.google-apps.folder'"
        
        def search(folder_id):
            nonlocal target_folders
            q = f"'{folder_id}' in parents and {query}"
            logger.debug(f"find_target_folders_recursively - Querying with q: {q}")
            try:
                response = self.drive_service.files().list(
                    q=q, spaces='drive', fields='nextPageToken, files(id, name)', 
                    supportsAllDrives=True, includeItemsFromAllDrives=True
                ).execute()
                for folder in response.get('files', []):
                    if folder.get('name') in self.target_folder_names:
                        target_folders.add(folder.get('id'))
                    # Recursivamente buscar en subcarpetas, si no son las carpetas objetivo
                    # Esto evita loops infinitos si una carpeta objetivo contiene una subcarpeta con el mismo nombre
                    if folder.get('name') not in self.target_folder_names:
                        search(folder.get('id'))
            except HttpError as error:
                logger.error(f"An error occurred while searching for folders: {error.content}")
            
        search(start_folder_id)
        logger.info(f"Target folders found: {target_folders}")
        return list(target_folders)

    def get_file_content_and_metadata(self, file_id: str) -> tuple[Optional[str], Optional[dict]]:
        """
        Descarga el contenido de un archivo de Drive y su metadata.
        """
        try:
            file_metadata = self.drive_service.files().get(fileId=file_id, fields="id, name, mimeType", supportsAllDrives=True).execute()
            
            # Solo descargar si no es una carpeta
            if file_metadata.get('mimeType') == 'application/vnd.google-apps.folder':
                return None, file_metadata

            request = self.drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
            file_bytes = BytesIO()
            downloader = MediaIoBaseDownload(file_bytes, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content = ContentExtractor.get_content(file_metadata['name'], file_bytes.getvalue())
            return file_content, file_metadata

        except HttpError as error:
            logger.error(f"An error occurred while downloading the file {file_id}: {error.content}")
            return None, None

    def build_dynamic_prompt(self, original_filename: str, file_content: str) -> str:
        """
        Construye el prompt para Gemini usando la configuración del ConfigManager.
        """
        prompt_config = self.config_manager.get_setting("prompt_config")
        prompt_template = prompt_config.get("prompt_template", "")
        json_structure = json.dumps(prompt_config.get("json_structure", {}), indent=4)
        
        # Limiting content to avoid overly large prompts, especially for binary/encoded content
        prompt = prompt_template.format(original_filename=original_filename, file_content=file_content[:8000])
        prompt += f"\n\nLa estructura del JSON de salida debe ser:\n{json_structure}"
        return prompt

    def analyze_content_with_gemini(self, original_filename: str, content: str) -> Optional[dict]:
        """
        Analiza el contenido de un archivo usando el modelo Gemini.
        """
        if not content:
            return None
        if not self.gemini_model:
            logger.error("Gemini model is not available. Cannot analyze content.")
            return {"keywords": ["generico"], "date": datetime.now().strftime("%Y-%m-%d")}
            
        prompt = self.build_dynamic_prompt(original_filename, content)
        logger.debug(f"Generated prompt for Gemini: {prompt}")
        try:
            response = self.gemini_model.generate_content(prompt)
            # Robust parsing for Gemini's JSON response
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            
            return json.loads(json_text)
        except Exception as e:
            logger.error(f"Error analyzing content with Gemini: {e}")
            return {"keywords": ["generico"], "date": datetime.now().strftime("%Y-%m-%d")}

    def rename_drive_file(self, file_id: str, original_name: str, analysis: dict) -> Optional[str]:
        """
        Renombra un archivo en Google Drive basándose en el análisis de Gemini.
        """
        try:
            new_filename_format = self.config_manager.get_setting("prompt_config.new_filename_format")
            keywords_str = "_".join(analysis.get("keywords", ["doc"])).replace(" ", "")
            date_str = analysis.get("date", datetime.now().strftime("%Y-%m-%d"))
            file_extension = os.path.splitext(original_name)[1]
            new_name = new_filename_format.format(date=date_str, keywords=keywords_str).replace('.ext', file_extension)
            file_metadata = {'name': new_name}
            updated_file = self.drive_service.files().update(fileId=file_id, body=file_metadata, fields='id, name', supportsAllDrives=True).execute()
            logger.info(f"File renamed to: {updated_file.get('name')}")
            return updated_file.get('name')
        except HttpError as error:
            logger.error(f"An error occurred while renaming the file: {error.content}")
            return None

    def update_html_index(self, folder_id: str, original_name: str, new_name: str, summary: str, is_deleted: bool = False):
        """
        Crea o actualiza un archivo index.html en la carpeta de Drive con el historial de renombrado.
        """
        index_name = "index.html"
        index_file_id = None
        try:
            query = f"'{folder_id}' in parents and name='{index_name}' and trashed=false"
            response = self.drive_service.files().list(q=query, fields='files(id)', supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            files = response.get('files', [])
            if files:
                index_file_id = files[0]['id']
        except HttpError as error:
            logger.error(f"Error searching for index.html: {error.content}")

        soup = None
        if index_file_id:
            html_content, _ = self.get_file_content_and_metadata(index_file_id)
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")
        
        if not soup:
            soup = BeautifulSoup(
            '''
            <html><head><title>Índice de Documentos</title></head><body><h1>Índice de Documentos</h1><table border="1"><thead><tr><th>Nombre Original</th><th>Nuevo Nombre (Procesado)</th><th>Resumen</th><th>Estado</th><th>Fecha de Actualización</th></tr></thead><tbody></tbody></table></body></html>
            ''', "html.parser")

        tbody = soup.find('tbody')
        if not tbody: # Asegurarse de que el tbody existe
            body = soup.find('body')
            if body:
                table = soup.new_tag('table', border="1")
                thead = soup.new_tag('thead')
                tr_head = soup.new_tag('tr')
                th_original = soup.new_tag('th')
                th_original.string = "Nombre Original"
                th_new = soup.new_tag('th')
                th_new.string = "Nuevo Nombre (Procesado)"
                th_summary = soup.new_tag('th')
                th_summary.string = "Resumen"
                th_status = soup.new_tag('th')
                th_status.string = "Estado"
                th_date = soup.new_tag('th')
                th_date.string = "Fecha de Actualización"
                tr_head.append(th_original)
                tr_head.append(th_new)
                tr_head.append(th_summary)
                tr_head.append(th_status)
                tr_head.append(th_date)
                thead.append(tr_head)
                tbody = soup.new_tag('tbody')
                table.append(thead)
                table.append(tbody)
                body.append(table)
            else:
                logger.error("No se pudo encontrar o crear el cuerpo del HTML para el índice.")
                return


        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_id = f"file-{''.join(filter(str.isalnum, original_name))}"
        existing_row = soup.find('tr', id=row_id)

        if is_deleted:
            if existing_row:
                existing_row.find_all('td')[3].string = f"Eliminado"
                existing_row.find_all('td')[4].string = now_str
            else:
                new_row = soup.new_tag('tr', id=row_id)
                new_row.append(soup.new_tag('td', string=original_name))
                new_row.append(soup.new_tag('td', string="N/A"))
                new_row.append(soup.new_tag('td', string="Archivo eliminado del registro."))
                new_row.append(soup.new_tag('td', string=f"Eliminado"))
                new_row.append(soup.new_tag('td', string=now_str))
                tbody.append(new_row)
        else:
            if existing_row:
                cells = existing_row.find_all('td')
                if len(cells) >= 5: # Asegurarse de que hay suficientes celdas
                    cells[1].string = new_name
                    cells[2].string = summary
                    cells[3].string = "Activo"
                    cells[4].string = now_str
                else:
                    # Si la fila existente no tiene el formato esperado, loguear y crear una nueva
                    logger.warning(f"Fila existente con ID {row_id} tiene formato inesperado. Creando nueva fila.")
                    new_row = soup.new_tag('tr', id=row_id)
                    new_row.append(soup.new_tag('td', string=original_name))
                    new_row.append(soup.new_tag('td', string=new_name))
                    new_row.append(soup.new_tag('td', string=summary))
                    new_row.append(soup.new_tag('td', string="Activo"))
                    new_row.append(soup.new_tag('td', string=now_str))
                    tbody.append(new_row)
            else:
                new_row = soup.new_tag('tr', id=row_id)
                new_row.append(soup.new_tag('td', string=original_name))
                new_row.append(soup.new_tag('td', string=new_name))
                new_row.append(soup.new_tag('td', string=summary))
                new_row.append(soup.new_tag('td', string="Activo"))
                new_row.append(soup.new_tag('td', string=now_str))
                tbody.append(new_row)

        html_bytes = BytesIO(soup.prettify("utf-8"))
        media = MediaIoBaseUpload(html_bytes, mimetype='text/html', resumable=True)
        
        file_metadata = {'name': index_name, 'mimeType': 'text/html'}
        if index_file_id:
            self.drive_service.files().update(fileId=index_file_id, body=file_metadata, media_body=media, supportsAllDrives=True).execute()
            logger.info(f"HTML index updated in folder {folder_id}.")
        else:
            file_metadata['parents'] = [folder_id]
            self.drive_service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
            logger.info(f"HTML index created in folder {folder_id}.")

    def process_folder_for_changes(self, root_folder_id: str, credentials, storage_client: storage.Client, config_manager: ConfigManager):
        """
        Procesa una carpeta raíz completa para cambios, similar al main.py original.
        Este método será el punto de entrada para el worker o el api-server.
        """
        # Reinicializar logger si no lo está para asegurar configuración
        if not LoggerManager._initialized:
            LoggerManager.initialize(config_manager)
            logger = LoggerManager.get_logger(__name__)

        # Obtener o crear el token de página para Drive Changes
        token_file_name = config_manager.get_setting("google_cloud.token_file_name", "drive_changes_token.json")
        gcs_bucket_name = config_manager.get_setting("GCS_BUCKET_NAME", "").strip().strip("'\"")

        def get_last_token():
            try:
                bucket = storage_client.bucket(gcs_bucket_name)
                blob = bucket.blob(token_file_name)
                if blob.exists():
                    token_data = json.loads(blob.download_as_string())
                    return token_data.get("pageToken")
            except Exception as e:
                logger.warning(f"Could not retrieve token, a new sync will be started. Error: {e}")
            return None

        def save_new_token(token):
            try:
                bucket = storage_client.bucket(gcs_bucket_name)
                blob = bucket.blob(token_file_name)
                token_data = {"pageToken": token}
                blob.upload_from_string(json.dumps(token_data), content_type="application/json")
                logger.info(f"New token saved successfully: {token}")
            except Exception as e:
                logger.error(f"Error saving new token: {e}")

        logger.info("Processing request to check for Drive changes...")
        target_folder_ids = self.find_target_folders_recursively(root_folder_id)
        if not target_folder_ids:
            logger.warning("No target folders found to monitor.")
            return "No target folders found to monitor.", 200 # No se retorna HTTP status aquí

        logger.info("Processing existing files in target folders...")
        for folder_id in target_folder_ids:
            self.process_folder(folder_id)

        logger.info("Checking for new changes since last run...")
        page_token = get_last_token()
        if not page_token:
            try:
                response = self.drive_service.changes().getStartPageToken().execute()
                page_token = response.get('startPageToken')
                save_new_token(page_token)
                logger.info("Initial token obtained. Subsequent runs will process new changes.")
            except HttpError as e:
                logger.error(f"Could not get start page token: {e}")
                return f"Error getting start page token from Drive API: {e}", 500 # No se retorna HTTP status aquí
            return "Initial processing of existing files complete.", 200 # No se retorna HTTP status aquí

        while page_token is not None:
            try:
                response = self.drive_service.changes().list(
                    pageToken=page_token, 
                    spaces='drive', 
                    fields='nextPageToken, newStartPageToken, changes(fileId, removed, file(name, parents, mimeType))',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                for change in response.get('changes', []):
                    file_info = change.get('file')
                    parent_folder = file_info.get('parents', [None])[0] if file_info else None
                    
                    if change.get('removed') or not file_info or \
                       file_info.get('mimeType') == 'application/vnd.google-apps.folder' or \
                       parent_folder not in target_folder_ids:
                        continue

                    original_name = file_info.get('name')
                    if original_name == "index.html" or "DOCPROCESADO" in original_name:
                        continue
                    
                    logger.info(f"New file change detected: '{original_name}' (ID: {file_info.get('id')})")
                    self.process_file_item(file_info.get('id'), original_name, parent_folder)

                if 'newStartPageToken' in response:
                    save_new_token(response['newStartPageToken'])
                
                page_token = response.get('nextPageToken')

            except HttpError as e:
                logger.error(f"Error processing changes from Drive API: {e}")
                if e.resp.status in [401, 403]:
                    logger.warning("Authorization error. Attempting to get a new start page token.")
                    response = self.drive_service.changes().getStartPageToken().execute()
                    save_new_token(response.get('startPageToken'))
                break 

        return "Change review process completed.", 200 # No se retorna HTTP status aquí