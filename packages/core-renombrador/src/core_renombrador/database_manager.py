"""
DatabaseManager con soporte para JSON local, GCS y Supabase
===========================================================

Provides unified interface for data persistence using:
- JSON files (local development)
- Google Cloud Storage (shared persistence in Cloud Run)
- Supabase (production SQL)

:created:   2025-12-05
:updated:   2025-12-19
:filename:  database_manager.py
:author:    amBotHs + CENF
:version:   2.1.0
:status:    Production
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .file_manager import FileManager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Unified database interface supporting JSON, GCS, and Supabase.
    Interfaz unificada de base de datos soportando JSON, GCS y Supabase.
    """

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        db_path: Optional[Union[str, Path]] = None,
        use_supabase: bool = False,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        use_gcs: bool = False,
        gcs_bucket_name: Optional[str] = None,
        table_name: str = "app_config"
    ):
        """
        Initialize DatabaseManager.

        Args:
            file_manager: FileManager instance (for JSON/GCS mode).
            db_path: Path to JSON database file (local).
            use_supabase: Whether to use Supabase.
            supabase_url: Supabase project URL.
            supabase_key: Supabase API key.
            use_gcs: Whether to use Google Cloud Storage.
            gcs_bucket_name: Name of the GCS bucket.
            table_name: Name of the table/collection to use.
        """
        self.use_supabase = use_supabase
        self.use_gcs = use_gcs
        self.table_name = table_name
        self.supabase_client = None
        self.gcs_client = None
        self.bucket = None
        self.file_manager = file_manager

        # Priority: Supabase > GCS > Local JSON
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
                    config_key="database.path",
                    relative_path="data/database.json"
                )
            self._ensure_json_db()

    def _init_supabase(self, url: Optional[str], key: Optional[str]) -> None:
        """Initializes Supabase client."""
        try:
            from supabase import create_client, Client
        except ImportError:
            raise ImportError("Supabase library not installed.")

        supabase_url = url or os.environ.get("SUPABASE_URL")
        supabase_key = key or os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Supabase credentials not provided.")

        self.supabase_client: Client = create_client(supabase_url, supabase_key)
        logger.info(f"Supabase client initialized for table '{self.table_name}'")

    def _init_gcs(self, bucket_name: Optional[str]) -> None:
        """Initializes Google Cloud Storage client."""
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError("google-cloud-storage library not installed.")
            
        self.bucket_name = bucket_name or os.environ.get("GCS_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME not provided for GCS persistence.")
            
        try:
            self.gcs_client = storage.Client()
            self.bucket = self.gcs_client.bucket(self.bucket_name)
            self.blob_name = f"data/{self.table_name}.json"
            logger.info(f"GCS persistence initialized: gs://{self.bucket_name}/{self.blob_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise

    def _ensure_json_db(self) -> None:
        """Ensures the JSON database file exists (Local only)."""
        if not self.db_path.exists():
            try:
                self.file_manager.write_json_file(self.db_path, [])
                logger.info(f"Created new JSON database at {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to create JSON database at {self.db_path}: {e}")
                raise

    # --- Data Loading/Saving Abstractions ---

    def _load_data(self) -> List[Dict[str, Any]]:
        """Unified data loader for GCS/Local."""
        if self.use_gcs:
            return self._load_gcs_data()
        return self._load_json_data()

    def _save_data(self, data: List[Dict[str, Any]]) -> None:
        """Unified data saver for GCS/Local."""
        if self.use_gcs:
            self._save_gcs_data(data)
        else:
            self._save_json_data(data)

    def _load_gcs_data(self) -> List[Dict[str, Any]]:
        """Loads JSON from GCS blob."""
        try:
            blob = self.bucket.blob(self.blob_name)
            if not blob.exists():
                logger.info(f"GCS blob {self.blob_name} does not exist. Creating empty.")
                self._save_gcs_data([])
                return []
            
            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to load data from GCS: {e}")
            return []

    def _save_gcs_data(self, data: List[Dict[str, Any]]) -> None:
        """Saves JSON to GCS blob."""
        try:
            blob = self.bucket.blob(self.blob_name)
            blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
            logger.debug(f"Saved {len(data)} records to gs://{self.bucket_name}/{self.blob_name}")
        except Exception as e:
            logger.error(f"Failed to save data to GCS: {e}")
            raise

    def _load_json_data(self) -> List[Dict[str, Any]]:
        """Loads data from local JSON file."""
        try:
            data = self.file_manager.read_json_file(self.db_path)
            if not isinstance(data, list):
                return []
            return data
        except Exception as e:
            logger.error(f"Failed to load local JSON data: {e}")
            return []

    def _save_json_data(self, data: List[Dict[str, Any]]) -> None:
        """Saves data to local JSON file."""
        try:
            self.file_manager.write_json_file(self.db_path, data)
        except Exception as e:
            logger.error(f"Failed to save local JSON data: {e}")
            raise

    # --- CRUD Operations ---

    def insert(self, record: Dict[str, Any]) -> None:
        if self.use_supabase:
            try:
                self.supabase_client.table(self.table_name).insert(record).execute()
                logger.debug(f"Inserted into Supabase table '{self.table_name}'")
            except Exception as e:
                logger.error(f"Supabase insert failed: {e}")
                raise
        else:
            data = self._load_data()
            data.append(record)
            self._save_data(data)
            logger.debug(f"Inserted record into {'GCS' if self.use_gcs else 'Local JSON'}")

    def find_all(self) -> List[Dict[str, Any]]:
        if self.use_supabase:
            try:
                result = self.supabase_client.table(self.table_name).select("*").execute()
                return result.data or []
            except Exception as e:
                logger.error(f"Supabase select failed: {e}")
                return []
        else:
            return self._load_data()

    def find(self, key: str, value: Any) -> List[Dict[str, Any]]:
        if self.use_supabase:
            try:
                result = self.supabase_client.table(self.table_name).select("*").eq(key, value).execute()
                return result.data or []
            except Exception as e:
                logger.error(f"Supabase find failed: {e}")
                return []
        else:
            data = self._load_data()
            return [item for item in data if item.get(key) == value]

    def update(self, filter_key: str, filter_value: Any, updates: Dict[str, Any]) -> int:
        if self.use_supabase:
            try:
                result = self.supabase_client.table(self.table_name).update(updates).eq(filter_key, filter_value).execute()
                return len(result.data) if result.data else 0
            except Exception as e:
                logger.error(f"Supabase update failed: {e}")
                return 0
        else:
            data = self._load_data()
            count = 0
            for item in data:
                if item.get(filter_key) == filter_value:
                    item.update(updates)
                    count += 1
            if count > 0:
                self._save_data(data)
            return count

    def delete(self, key: str, value: Any) -> int:
        if self.use_supabase:
            try:
                result = self.supabase_client.table(self.table_name).delete().eq(key, value).execute()
                return len(result.data) if result.data else 0
            except Exception as e:
                logger.error(f"Supabase delete failed: {e}")
                return 0
        else:
            data = self._load_data()
            original_count = len(data)
            data = [item for item in data if item.get(key) != value]
            deleted_count = original_count - len(data)
            if deleted_count > 0:
                self._save_data(data)
            return deleted_count
