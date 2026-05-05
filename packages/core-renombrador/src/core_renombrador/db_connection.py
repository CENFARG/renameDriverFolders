"""
Database Connection — Connection lifecycle and data I/O.
==========================================================

Manages connections to Supabase, Google Cloud Storage, or local JSON.
Handles data loading and saving across all backends.

:created:   2026-05-05
:filename:  db_connection.py
:path:      packages/core-renombrador/src/core_renombrador/db_connection.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class DbConnection:
    """Manages database connections and raw data I/O."""

    def __init__(
        self,
        file_manager=None,
        db_path: Optional[Union[str, Path]] = None,
        use_supabase: bool = False,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        use_gcs: bool = False,
        gcs_bucket_name: Optional[str] = None,
        table_name: str = "app_config",
    ):
        self.use_supabase = use_supabase
        self.use_gcs = use_gcs
        self.table_name = table_name
        self.supabase_client = None
        self.gcs_client = None
        self.bucket = None
        self.file_manager = file_manager

        if self.use_supabase:
            self._init_supabase(supabase_url, supabase_key)
        elif self.use_gcs:
            self._init_gcs(gcs_bucket_name)
        else:
            if not file_manager:
                raise ValueError("FileManager required for JSON database mode")
            self.file_manager = file_manager
            if db_path:
                self.db_path = Path(db_path)
            else:
                self.db_path = self.file_manager.get_path(
                    config_key="database.path", relative_path="data/database.json"
                )
            self._ensure_json_db()

    def _init_supabase(self, url: Optional[str], key: Optional[str]) -> None:
        from supabase import create_client, Client

        supabase_url = url or os.environ.get("SUPABASE_URL")
        supabase_key = key or os.environ.get("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not provided.")
        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        logger.info(f"Supabase client initialized for table '{self.table_name}'")

    def _init_gcs(self, bucket_name: Optional[str]) -> None:
        from google.cloud import storage

        self.bucket_name = bucket_name or os.environ.get("GCS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME not provided.")
        try:
            self.gcs_client = storage.Client()
            self.bucket = self.gcs_client.bucket(self.bucket_name)
            self.blob_name = f"data/{self.table_name}.json"
            logger.info(f"GCS persistence initialized: gs://{self.bucket_name}/{self.blob_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise

    def _ensure_json_db(self) -> None:
        if not self.db_path.exists():
            try:
                self.file_manager.write_json_file(self.db_path, [])
                logger.info(f"Created new JSON database at {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to create JSON database at {self.db_path}: {e}")
                raise

    def load_data(self) -> List[Dict[str, Any]]:
        """Unified data loader for GCS/Local JSON."""
        if self.use_gcs:
            return self._load_gcs_data()
        return self._load_json_data()

    def save_data(self, data: List[Dict[str, Any]]) -> None:
        """Unified data saver for GCS/Local JSON."""
        if self.use_gcs:
            self._save_gcs_data(data)
        else:
            self._save_json_data(data)

    def _load_gcs_data(self) -> List[Dict[str, Any]]:
        try:
            blob = self.bucket.blob(self.blob_name)
            if not blob.exists():
                self._save_gcs_data([])
                return []
            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load data from GCS: {e}")
            return []

    def _save_gcs_data(self, data: List[Dict[str, Any]]) -> None:
        try:
            blob = self.bucket.blob(self.blob_name)
            blob.upload_from_string(json.dumps(data, indent=2), content_type="application/json")
            logger.debug(f"Saved {len(data)} records to gs://{self.bucket_name}/{self.blob_name}")
        except Exception as e:
            logger.error(f"Failed to save data to GCS: {e}")
            raise

    def _load_json_data(self) -> List[Dict[str, Any]]:
        try:
            data = self.file_manager.read_json_file(self.db_path)
            if not isinstance(data, list):
                return []
            return data
        except Exception as e:
            logger.error(f"Failed to load local JSON data: {e}")
            return []

    def _save_json_data(self, data: List[Dict[str, Any]]) -> None:
        try:
            self.file_manager.write_json_file(self.db_path, data)
        except Exception as e:
            logger.error(f"Failed to save local JSON data: {e}")
            raise
