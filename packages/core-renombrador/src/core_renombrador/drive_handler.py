"""
Drive Handler — Facade for Google Drive operations.
====================================================

Delegates to DriveReader (read ops) and DriveWriter (write ops).
Maintains backward compatibility with existing callers.

:created:   2025-12-05
:updated:   2026-05-05
:filename:  drive_handler.py
:path:      packages/core-renombrador/src/core_renombrador/drive_handler.py
:author:    amBotHs + CENF
:version:   2.0.0
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from google.cloud import storage
from googleapiclient.discovery import build

import google.generativeai as genai

from .config_manager import ConfigManager
from .logger_manager import LoggerManager
from .drive_reader import DriveReader
from .drive_writer import DriveWriter

logger = logging.getLogger(__name__)


class DriveHandler:
    """
    Facade for Google Drive operations.

    Delegates to DriveReader for read operations and DriveWriter for
    write operations. Provides backward-compatible API.
    """

    def __init__(self, credentials, storage_client: storage.Client, config_manager: ConfigManager):
        self.drive_service = build("drive", "v3", credentials=credentials)
        self.storage_client = storage_client
        self.config_manager = config_manager
        self.target_folder_names = config_manager.get_setting(
            "google_cloud.target_folder_names", ["doc de respaldo"]
        )

        # Gemini setup (legacy — kept for backward compat)
        gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip().strip("'\"")
        if not gemini_api_key:
            logger.error("GEMINI_API_KEY not configured. Gemini analysis will fail.")
            self.gemini_model = None
        else:
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel(
                config_manager.get_setting("gemini.model_name", "gemini-2.5-flash-exp")
            )

        # Delegate instances
        self._reader = DriveReader(self.drive_service, storage_client, config_manager)
        self._writer = DriveWriter(self.drive_service, config_manager)

    # --- Read operations (delegate to DriveReader) ---

    def find_target_folders_recursively(self, start_folder_id: str) -> list:
        return self._reader.find_target_folders_recursively(start_folder_id)

    def get_file_content_and_metadata(self, file_id: str) -> tuple[Optional[str], Optional[dict]]:
        return self._reader.get_file_content_and_metadata(file_id)

    def list_files_in_folder(self, folder_id: str) -> list:
        return self._reader.list_files_in_folder(folder_id)

    def find_folders_by_name(self, root_folder_id: str, target_names: list) -> list:
        return self._reader.find_folders_by_name(root_folder_id, target_names)

    # --- Write operations (delegate to DriveWriter) ---

    def rename_drive_file(self, file_id: str, original_name: str, analysis: dict) -> Optional[str]:
        return self._writer.rename_drive_file(file_id, original_name, analysis)

    def rename_file(self, file_id: str, new_name: str) -> Optional[str]:
        return self._writer.rename_file(file_id, new_name)

    def move_file(self, file_id: str, dest_folder_id: str) -> bool:
        return self._writer.move_file(file_id, dest_folder_id)

    def update_html_index(self, folder_id: str, original_name: str, new_name: str,
                          summary: str, is_deleted: bool = False):
        return self._writer.update_html_index(
            folder_id, original_name, new_name, summary, is_deleted,
            drive_reader=self._reader
        )

    # --- AI operations (legacy — kept for backward compat) ---

    def build_dynamic_prompt(self, original_filename: str, file_content: str) -> str:
        prompt_config = self.config_manager.get_setting("prompt_config")
        prompt_template = prompt_config.get("prompt_template", "")
        json_structure = json.dumps(prompt_config.get("json_structure", {}), indent=4)
        prompt = prompt_template.format(original_filename=original_filename, file_content=file_content[:8000])
        prompt += f"\n\nLa estructura del JSON de salida debe ser:\n{json_structure}"
        return prompt

    def analyze_content_with_gemini(self, original_filename: str, content: str) -> Optional[dict]:
        if not content:
            return None
        if not self.gemini_model:
            logger.error("Gemini model not available.")
            return {"keywords": ["generico"], "date": datetime.now().strftime("%Y-%m-%d")}
        prompt = self.build_dynamic_prompt(original_filename, content)
        try:
            response = self.gemini_model.generate_content(prompt)
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            return json.loads(json_text)
        except Exception as e:
            logger.error(f"Error analyzing content with Gemini: {e}")
            return {"keywords": ["generico"], "date": datetime.now().strftime("%Y-%m-%d")}

    # --- Change processing (delegate to DriveReader) ---

    def process_folder_for_changes(self, root_folder_id: str, credentials,
                                   storage_client: storage.Client, config_manager: ConfigManager):
        if not LoggerManager._initialized:
            LoggerManager.initialize(config_manager)

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
                logger.warning(f"Could not retrieve token: {e}")
            return None

        def save_new_token(token):
            try:
                bucket = storage_client.bucket(gcs_bucket_name)
                blob = bucket.blob(token_file_name)
                blob.upload_from_string(json.dumps({"pageToken": token}), content_type="application/json")
            except Exception as e:
                logger.error(f"Error saving token: {e}")

        target_folder_ids = self._reader.find_target_folders_recursively(root_folder_id)
        if not target_folder_ids:
            return "No target folders found.", 200

        for folder_id in target_folder_ids:
            self.process_folder(folder_id)

        page_token = get_last_token()
        if not page_token:
            page_token = self._reader.get_start_page_token()
            if page_token:
                save_new_token(page_token)
            return "Initial processing complete.", 200

        while page_token:
            changes, new_token = self._reader.get_changes(page_token, target_folder_ids)
            for change in changes:
                logger.info(f"Change detected: '{change['name']}'")
                self.process_file_item(change['file_id'], change['name'], change['parent_folder'])
            if new_token:
                save_new_token(new_token)
            page_token = new_token if new_token != page_token else None

        return "Change review completed.", 200

    # These are referenced but not defined in this file — implemented by callers
    def process_folder(self, folder_id):
        raise NotImplementedError("process_folder must be implemented by subclass or caller")

    def process_file_item(self, file_id, name, parent_folder):
        raise NotImplementedError("process_file_item must be implemented by subclass or caller")
