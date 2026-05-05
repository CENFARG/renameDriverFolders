"""
Drive Operations — Worker Drive API interactions.
=================================================

Low-level Drive API operations: download, find folders, rename.

:created:   2026-05-05
:filename:  drive_operations.py
:path:      services/worker-v3/src/drive_operations.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
from io import BytesIO

from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)


def download_file(drive_service, file_id: str) -> bytes:
    """
    Download file content from Google Drive.

    Args:
        drive_service: Authenticated Drive API service.
        file_id: Drive file ID.

    Returns:
        File content as bytes.
    """
    request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
    file_bytes = BytesIO()
    downloader = MediaIoBaseDownload(file_bytes, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    return file_bytes.getvalue()


def find_target_folders(drive_service, root_folder_id: str, target_names: list) -> list:
    """
    Find specific folders by name within a root folder.

    Args:
        drive_service: Authenticated Drive API service.
        root_folder_id: Parent folder to search within.
        target_names: List of folder names to find.

    Returns:
        List of folder IDs that match target names.
    """
    found_folders = []

    try:
        query = (
            f"'{root_folder_id}' in parents and trashed=false "
            f"and mimeType='application/vnd.google-apps.folder'"
        )
        response = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        for folder in response.get("files", []):
            if folder["name"] in target_names:
                found_folders.append(folder["id"])
                logger.info(f"Found target folder: {folder['name']} (ID: {folder['id']})")

    except Exception as e:
        logger.error(f"Error finding folders: {e}")

    return found_folders


def rename_file(drive_service, file_id: str, new_name: str):
    """
    Rename a file in Google Drive.

    Args:
        drive_service: Authenticated Drive API service.
        file_id: Drive file ID.
        new_name: New filename.
    """
    drive_service.files().update(
        fileId=file_id,
        body={"name": new_name},
        fields="id, name",
        supportsAllDrives=True,
    ).execute()
