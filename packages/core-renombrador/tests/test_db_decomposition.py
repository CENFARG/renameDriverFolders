"""
Test: database_manager decomposition into db_connection + db_queries.

Verifies that:
1. db_connection.py handles connection initialization (supabase, gcs, json)
2. db_queries.py handles CRUD operations
3. DatabaseManager facade preserves backward-compatible API

:task: T1.6 - Decompose database_manager.py
:phase: RED (test written first)
"""

import pytest
from unittest.mock import MagicMock, patch


class TestDbConnection:
    """DbConnection handles connection lifecycle and data I/O."""

    def test_db_connection_module_exists(self):
        from core_renombrador.db_connection import DbConnection
        assert DbConnection is not None

    def test_init_json_mode(self):
        from core_renombrador.db_connection import DbConnection

        mock_fm = MagicMock()
        mock_fm.get_path.return_value = "/tmp/test_db.json"

        with patch("builtins.open"), patch("core_renombrador.db_connection.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            conn = DbConnection(
                file_manager=mock_fm,
                db_path="/tmp/test_db.json",
            )
        assert conn is not None

    def test_init_supabase_mode(self):
        from core_renombrador.db_connection import DbConnection

        mock_supabase = MagicMock()
        mock_supabase.create_client.return_value = MagicMock()
        with patch.dict("sys.modules", {"supabase": mock_supabase}):
            conn = DbConnection(
                use_supabase=True,
                supabase_url="https://test.supabase.co",
                supabase_key="test-key",
            )
        assert conn is not None

    def test_load_data_returns_list(self):
        from core_renombrador.db_connection import DbConnection

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = [{"id": "1", "name": "test"}]

        with patch("core_renombrador.db_connection.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            conn = DbConnection(file_manager=mock_fm, db_path="/tmp/test.json")

        result = conn.load_data()
        assert isinstance(result, list)
        assert len(result) == 1


class TestDbQueries:
    """DbQueries handles CRUD operations using a DbConnection."""

    def test_db_queries_module_exists(self):
        from core_renombrador.db_queries import DbQueries
        assert DbQueries is not None

    def test_insert_json_mode(self):
        from core_renombrador.db_queries import DbQueries
        from core_renombrador.db_connection import DbConnection

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = []
        mock_fm.write_json_file = MagicMock()

        with patch("core_renombrador.db_connection.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            conn = DbConnection(file_manager=mock_fm, db_path="/tmp/test.json")

        queries = DbQueries(connection=conn)
        queries.insert({"id": "1", "name": "test"})

        mock_fm.write_json_file.assert_called_once()

    def test_find_all_json_mode(self):
        from core_renombrador.db_queries import DbQueries
        from core_renombrador.db_connection import DbConnection

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = [{"id": "1"}, {"id": "2"}]

        with patch("core_renombrador.db_connection.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            conn = DbConnection(file_manager=mock_fm, db_path="/tmp/test.json")

        queries = DbQueries(connection=conn)
        result = queries.find_all()
        assert len(result) == 2

    def test_find_by_key(self):
        from core_renombrador.db_queries import DbQueries
        from core_renombrador.db_connection import DbConnection

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = [
            {"id": "1", "name": "alpha"},
            {"id": "2", "name": "beta"},
        ]

        with patch("core_renombrador.db_connection.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            conn = DbConnection(file_manager=mock_fm, db_path="/tmp/test.json")

        queries = DbQueries(connection=conn)
        result = queries.find("id", "1")
        assert len(result) == 1
        assert result[0]["name"] == "alpha"

    def test_update_record(self):
        from core_renombrador.db_queries import DbQueries
        from core_renombrador.db_connection import DbConnection

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = [{"id": "1", "name": "old"}]
        mock_fm.write_json_file = MagicMock()

        with patch("core_renombrador.db_connection.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            conn = DbConnection(file_manager=mock_fm, db_path="/tmp/test.json")

        queries = DbQueries(connection=conn)
        count = queries.update("id", "1", {"name": "new"})
        assert count == 1

    def test_delete_record(self):
        from core_renombrador.db_queries import DbQueries
        from core_renombrador.db_connection import DbConnection

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = [{"id": "1"}, {"id": "2"}]
        mock_fm.write_json_file = MagicMock()

        with patch("core_renombrador.db_connection.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            conn = DbConnection(file_manager=mock_fm, db_path="/tmp/test.json")

        queries = DbQueries(connection=conn)
        count = queries.delete("id", "1")
        assert count == 1


class TestDatabaseManagerFacade:
    """DatabaseManager facade preserves backward-compatible API."""

    def test_database_manager_imports(self):
        from core_renombrador.database_manager import DatabaseManager
        assert DatabaseManager is not None

    def test_insert_delegates(self):
        from core_renombrador.database_manager import DatabaseManager

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = []
        mock_fm.write_json_file = MagicMock()

        with patch("core_renombrador.database_manager.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            dm = DatabaseManager(file_manager=mock_fm, db_path="/tmp/test.json")

        dm.insert({"id": "x"})
        mock_fm.write_json_file.assert_called()

    def test_find_all_delegates(self):
        from core_renombrador.database_manager import DatabaseManager

        mock_fm = MagicMock()
        mock_fm.read_json_file.return_value = [{"id": "1"}]

        with patch("core_renombrador.database_manager.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            dm = DatabaseManager(file_manager=mock_fm, db_path="/tmp/test.json")

        result = dm.find_all()
        assert len(result) == 1
