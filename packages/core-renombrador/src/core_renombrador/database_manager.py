"""
Database Manager — Facade for database operations.
====================================================

Delegates to DbConnection (connection lifecycle) and DbQueries (CRUD).
Backward-compatible API.

:created:   2025-12-05
:updated:   2026-05-05
:filename:  database_manager.py
:path:      packages/core-renombrador/src/core_renombrador/database_manager.py
:author:    amBotHs + CENF
:version:   3.0.0
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .db_connection import DbConnection
from .db_queries import DbQueries

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Facade for database operations.

    Delegates to DbConnection for connection management and
    DbQueries for CRUD operations.
    """

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
        self._conn = DbConnection(
            file_manager=file_manager,
            db_path=db_path,
            use_supabase=use_supabase,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            use_gcs=use_gcs,
            gcs_bucket_name=gcs_bucket_name,
            table_name=table_name,
        )
        self._queries = DbQueries(connection=self._conn)

        # Preserve public attributes for backward compat
        self.use_supabase = self._conn.use_supabase
        self.use_gcs = self._conn.use_gcs
        self.table_name = self._conn.table_name
        self.supabase_client = self._conn.supabase_client

    def insert(self, record: Dict[str, Any]) -> None:
        return self._queries.insert(record)

    def find_all(self) -> List[Dict[str, Any]]:
        return self._queries.find_all()

    def find(self, key: str, value: Any) -> List[Dict[str, Any]]:
        return self._queries.find(key, value)

    def update(self, filter_key: str, filter_value: Any, updates: Dict[str, Any]) -> int:
        return self._queries.update(filter_key, filter_value, updates)

    def delete(self, key: str, value: Any) -> int:
        return self._queries.delete(key, value)
