"""
Drive Writer — Write operations for Google Drive.
==================================================

Handles renaming, moving, uploading, and HTML index updates
in Google Drive. All operations that modify files.

:created:   2026-05-05
:filename:  drive_writer.py
:path:      packages/core-renombrador/src/core_renombrador/drive_writer.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import os
from io import BytesIO
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)


class DriveWriter:
    """Write operations for Google Drive API."""

    def __init__(self, drive_service, config_manager=None):
        self.drive_service = drive_service
        self.config_manager = config_manager

    def rename_file(self, file_id: str, new_name: str) -> Optional[str]:
        """Rename a file in Google Drive. Returns new name on success."""
        try:
            updated_file = self.drive_service.files().update(
                fileId=file_id,
                body={"name": new_name},
                fields="id, name",
                supportsAllDrives=True
            ).execute()
            logger.info(f"File renamed to: {updated_file.get('name')}")
            return updated_file.get('name')
        except HttpError as error:
            logger.error(f"Error renaming file {file_id}: {error.content}")
            return None

    def rename_drive_file(self, file_id: str, original_name: str, analysis: dict) -> Optional[str]:
        """Rename file based on Gemini analysis (legacy compat)."""
        try:
            new_filename_format = self.config_manager.get_setting("prompt_config.new_filename_format")
            keywords_str = "_".join(analysis.get("keywords", ["doc"])).replace(" ", "")
            date_str = analysis.get("date", datetime.now().strftime("%Y-%m-%d"))
            file_extension = os.path.splitext(original_name)[1]
            new_name = new_filename_format.format(date=date_str, keywords=keywords_str).replace('.ext', file_extension)
            return self.rename_file(file_id, new_name)
        except HttpError as error:
            logger.error(f"Error renaming file: {error.content}")
            return None

    def move_file(self, file_id: str, dest_folder_id: str) -> bool:
        """Move a file to a different folder."""
        try:
            file = self.drive_service.files().get(
                fileId=file_id, fields='parents', supportsAllDrives=True
            ).execute()
            previous_parents = ",".join(file.get('parents', []))
            self.drive_service.files().update(
                fileId=file_id,
                addParents=dest_folder_id,
                removeParents=previous_parents,
                fields='id, parents',
                supportsAllDrives=True
            ).execute()
            logger.info(f"File {file_id} moved to folder {dest_folder_id}")
            return True
        except HttpError as error:
            logger.error(f"Error moving file {file_id}: {error.content}")
            return False

    def update_html_index(
        self,
        folder_id: str,
        original_name: str,
        new_name: str,
        summary: str,
        is_deleted: bool = False,
        drive_reader=None,
    ):
        """Create or update an index.html in a Drive folder with rename history."""
        index_name = "index.html"
        index_file_id = None

        try:
            query = f"'{folder_id}' in parents and name='{index_name}' and trashed=false"
            response = self.drive_service.files().list(
                q=query, fields='files(id)',
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            files = response.get('files', [])
            if files:
                index_file_id = files[0]['id']
        except HttpError as error:
            logger.error(f"Error searching for index.html: {error.content}")

        soup = None
        if index_file_id and drive_reader:
            html_content, _ = drive_reader.get_file_content_and_metadata(index_file_id)
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")

        if not soup:
            soup = BeautifulSoup(
                '''<html><head><title>Indice de Documentos</title></head>
                <body><h1>Indice de Documentos</h1>
                <table border="1"><thead><tr>
                <th>Nombre Original</th><th>Nuevo Nombre</th>
                <th>Resumen</th><th>Estado</th><th>Fecha</th>
                </tr></thead><tbody></tbody></table></body></html>''',
                "html.parser"
            )

        tbody = soup.find('tbody')
        if not tbody:
            tbody = soup.new_tag('tbody')
            soup.find('table').append(tbody)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_id = f"file-{''.join(filter(str.isalnum, original_name))}"

        existing_row = soup.find('tr', id=row_id)
        if is_deleted:
            if existing_row:
                existing_row.find_all('td')[3].string = "Eliminado"
                existing_row.find_all('td')[4].string = now_str
            else:
                new_row = soup.new_tag('tr', id=row_id)
                new_row.append(soup.new_tag('td', string=original_name))
                new_row.append(soup.new_tag('td', string="N/A"))
                new_row.append(soup.new_tag('td', string="Archivo eliminado."))
                new_row.append(soup.new_tag('td', string="Eliminado"))
                new_row.append(soup.new_tag('td', string=now_str))
                tbody.append(new_row)
        else:
            if existing_row:
                cells = existing_row.find_all('td')
                if len(cells) >= 5:
                    cells[1].string = new_name
                    cells[2].string = summary
                    cells[3].string = "Activo"
                    cells[4].string = now_str
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
            self.drive_service.files().update(
                fileId=index_file_id, body=file_metadata, media_body=media,
                supportsAllDrives=True
            ).execute()
            logger.info(f"HTML index updated in folder {folder_id}.")
        else:
            file_metadata['parents'] = [folder_id]
            self.drive_service.files().create(
                body=file_metadata, media_body=media, fields='id',
                supportsAllDrives=True
            ).execute()
            logger.info(f"HTML index created in folder {folder_id}.")
