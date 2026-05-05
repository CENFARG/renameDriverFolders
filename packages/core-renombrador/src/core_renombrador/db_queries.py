"""
Database Queries — CRUD operations.
====================================

Provides insert, find_all, find, update, and delete operations
using a DbConnection backend (Supabase, GCS, or JSON).

:created:   2026-05-05
:filename:  db_queries.py
:path:      packages/core-renombrador/src/core_renombrador/db_queries.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DbQueries:
    """CRUD operations using a DbConnection backend."""

    def __init__(self, connection):
        self._conn = connection

    def insert(self, record: Dict[str, Any]) -> None:
        if self._conn.use_supabase:
            try:
                self._conn.supabase_client.table(self._conn.table_name).insert(record).execute()
                logger.debug(f"Inserted into Supabase table '{self._conn.table_name}'")
            except Exception as e:
                logger.error(f"Supabase insert failed: {e}")
                raise
        else:
            data = self._conn.load_data()
            data.append(record)
            self._conn.save_data(data)
            logger.debug(f"Inserted record into {'GCS' if self._conn.use_gcs else 'Local JSON'}")

    def find_all(self) -> List[Dict[str, Any]]:
        if self._conn.use_supabase:
            try:
                result = self._conn.supabase_client.table(self._conn.table_name).select("*").execute()
                return result.data or []
            except Exception as e:
                logger.error(f"Supabase select failed: {e}")
                return []
        else:
            return self._conn.load_data()

    def find(self, key: str, value: Any) -> List[Dict[str, Any]]:
        if self._conn.use_supabase:
            try:
                result = self._conn.supabase_client.table(self._conn.table_name).select("*").eq(key, value).execute()
                return result.data or []
            except Exception as e:
                logger.error(f"Supabase find failed: {e}")
                return []
        else:
            data = self._conn.load_data()
            return [item for item in data if item.get(key) == value]

    def update(self, filter_key: str, filter_value: Any, updates: Dict[str, Any]) -> int:
        if self._conn.use_supabase:
            try:
                result = self._conn.supabase_client.table(self._conn.table_name).update(updates).eq(filter_key, filter_value).execute()
                return len(result.data) if result.data else 0
            except Exception as e:
                logger.error(f"Supabase update failed: {e}")
                return 0
        else:
            data = self._conn.load_data()
            count = 0
            for item in data:
                if item.get(filter_key) == filter_value:
                    item.update(updates)
                    count += 1
            if count > 0:
                self._conn.save_data(data)
            return count

    def delete(self, key: str, value: Any) -> int:
        if self._conn.use_supabase:
            try:
                result = self._conn.supabase_client.table(self._conn.table_name).delete().eq(key, value).execute()
                return len(result.data) if result.data else 0
            except Exception as e:
                logger.error(f"Supabase delete failed: {e}")
                return 0
        else:
            data = self._conn.load_data()
            original_count = len(data)
            data = [item for item in data if item.get(key) != value]
            deleted_count = original_count - len(data)
            if deleted_count > 0:
                self._conn.save_data(data)
            return deleted_count
