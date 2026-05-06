"""
Drive Reader — Read operations for Google Drive.
=================================================

Handles listing, searching, downloading, and change detection
from Google Drive. Read-only operations that don't modify files.

:created:   2026-05-05
:filename:  drive_reader.py
:path:      packages/core-renombrador/src/core_renombrador/drive_reader.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
from io import BytesIO
from typing import List, Optional

from google.cloud import storage
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from .content_extractor import ContentExtractor
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class DriveReader:
    """Read-only operations for Google Drive API."""

    def __init__(self, drive_service, storage_client: storage.Client, config_manager: ConfigManager):
        self.drive_service = drive_service
        self.storage_client = storage_client
        self.config_manager = config_manager
        self.target_folder_names = config_manager.get_setting(
            "google_cloud.target_folder_names", ["doc de respaldo"]
        )

    def find_target_folders_recursively(self, start_folder_id: str) -> list:
        """Search recursively for target folders within a root folder."""
        if not self.drive_service:
            logger.error("Drive service is not available. Cannot search for folders.")
            return []

        target_folders = set()
        query = "trashed=false and mimeType='application/vnd.google-apps.folder'"

        def search(folder_id):
            nonlocal target_folders
            q = f"'{folder_id}' in parents and {query}"
            try:
                response = self.drive_service.files().list(
                    q=q, spaces='drive', fields='nextPageToken, files(id, name)',
                    supportsAllDrives=True, includeItemsFromAllDrives=True
                ).execute()
                for folder in response.get('files', []):
                    if folder.get('name') in self.target_folder_names:
                        target_folders.add(folder.get('id'))
                    if folder.get('name') not in self.target_folder_names:
                        search(folder.get('id'))
            except HttpError as error:
                logger.error(f"Error searching for folders: {error.content}")

        search(start_folder_id)
        logger.info(f"Target folders found: {target_folders}")
        return list(target_folders)

    def get_file_content_and_metadata(self, file_id: str) -> tuple[Optional[str], Optional[dict]]:
        """Download file content and metadata from Drive."""
        try:
            file_metadata = self.drive_service.files().get(
                fileId=file_id, fields="id, name, mimeType", supportsAllDrives=True
            ).execute()

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
            logger.error(f"Error downloading file {file_id}: {error.content}")
            return None, None

    def list_files_in_folder(self, folder_id: str) -> List[dict]:
        """List all non-folder files in a Drive folder."""
        try:
            query = (
                f"'{folder_id}' in parents and trashed=false "
                f"and mimeType != 'application/vnd.google-apps.folder'"
            )
            response = self.drive_service.files().list(
                q=query, fields="files(id, name, mimeType)",
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()
            return response.get("files", [])
        except HttpError as error:
            logger.error(f"Error listing files in folder {folder_id}: {error.content}")
            return []

    def find_folders_by_name(self, root_folder_id: str, target_names: list) -> list:
        """Find specific folders by name within a root folder."""
        found_folders = []
        try:
            query = (
                f"'{root_folder_id}' in parents and trashed=false "
                f"and mimeType='application/vnd.google-apps.folder'"
            )
            response = self.drive_service.files().list(
                q=query, fields="files(id, name)",
                supportsAllDrives=True, includeItemsFromAllDrives=True
            ).execute()

            for folder in response.get("files", []):
                if folder["name"] in target_names:
                    found_folders.append(folder["id"])
                    logger.info(f"Found target folder: {folder['name']} (ID: {folder['id']})")
        except HttpError as error:
            logger.error(f"Error finding folders: {error.content}")
        return found_folders

    def get_changes(self, page_token: str, target_folder_ids: list) -> tuple[list, Optional[str]]:
        """
        Get changes from Drive API since last page token.

        Returns:
            Tuple of (changed_files, new_page_token)
        """
        try:
            response = self.drive_service.changes().list(
                pageToken=page_token,
                spaces='drive',
                fields='nextPageToken, newStartPageToken, changes(fileId, removed, file(name, parents, mimeType))',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            relevant_changes = []
            for change in response.get('changes', []):
                file_info = change.get('file')
                parent_folder = file_info.get('parents', [None])[0] if file_info else None

                if change.get('removed') or not file_info:
                    continue
                if file_info.get('mimeType') == 'application/vnd.google-apps.folder':
                    continue
                if parent_folder not in target_folder_ids:
                    continue

                original_name = file_info.get('name')
                if original_name == "index.html" or "DOCPROCESADO" in original_name:
                    continue

                relevant_changes.append({
                    'file_id': file_info.get('id'),
                    'name': original_name,
                    'parent_folder': parent_folder,
                })

            new_token = response.get('newStartPageToken') or response.get('nextPageToken')
            return relevant_changes, new_token

        except HttpError as e:
            logger.error(f"Error getting Drive changes: {e}")
            return [], None

    def get_start_page_token(self) -> Optional[str]:
        """Get initial page token for Drive changes API."""
        try:
            response = self.drive_service.changes().getStartPageToken().execute()
            return response.get('startPageToken')
        except HttpError as e:
            logger.error(f"Could not get start page token: {e}")
            return None
