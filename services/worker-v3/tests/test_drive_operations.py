"""
Test: Worker Drive Operations extraction (T2.4).

Verifies:
1. download_file() downloads from Drive API
2. find_target_folders() finds folders by name
3. rename_file() renames files in Drive

:task: T2.4 - Extract Worker Drive Operations
:phase: RED (test written first)
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestDownloadFile:
    """download_file() downloads file bytes from Drive."""

    def test_drive_operations_module_exists(self):
        from drive_operations import download_file, find_target_folders, rename_file
        assert download_file is not None
        assert find_target_folders is not None
        assert rename_file is not None

    def test_download_file_returns_bytes(self):
        """Should return file content as bytes."""
        from drive_operations import download_file

        mock_service = MagicMock()
        mock_request = MagicMock()
        mock_service.files().get_media.return_value = mock_request

        with patch("drive_operations.MediaIoBaseDownload") as mock_downloader:
            mock_instance = mock_downloader.return_value
            mock_instance.next_chunk.side_effect = [(MagicMock(progress=1.0), True)]
            mock_instance.next_chunk.return_value = (MagicMock(), True)

            # The BytesIO written by downloader
            with patch("drive_operations.BytesIO") as mock_bio:
                mock_bio_instance = MagicMock()
                mock_bio_instance.getvalue.return_value = b"file content here"
                mock_bio.return_value = mock_bio_instance

                result = download_file(mock_service, "file123")
                assert result == b"file content here"


class TestFindTargetFolders:
    """find_target_folders() finds folders by name within a root folder."""

    def test_finds_matching_folders(self):
        """Should return IDs of folders matching target names."""
        from drive_operations import find_target_folders

        mock_service = MagicMock()
        mock_service.files().list.return_value.execute.return_value = {
            "files": [
                {"id": "folder1", "name": "Recibos"},
                {"id": "folder2", "name": "Facturas"},
                {"id": "folder3", "name": "Otros"},
            ]
        }

        result = find_target_folders(mock_service, "root123", ["Recibos", "Facturas"])
        assert "folder1" in result
        assert "folder2" in result
        assert "folder3" not in result

    def test_returns_empty_when_no_match(self):
        """Should return empty list when no folders match."""
        from drive_operations import find_target_folders

        mock_service = MagicMock()
        mock_service.files().list.return_value.execute.return_value = {
            "files": [{"id": "f1", "name": "Other"}]
        }

        result = find_target_folders(mock_service, "root", ["NonExistent"])
        assert result == []

    def test_handles_api_error_gracefully(self):
        """Should return empty list on API error."""
        from drive_operations import find_target_folders

        mock_service = MagicMock()
        mock_service.files().list.return_value.execute.side_effect = Exception("API error")

        result = find_target_folders(mock_service, "root", ["anything"])
        assert result == []


class TestRenameFile:
    """rename_file() renames a file in Drive."""

    def test_rename_file_calls_update(self):
        """Should call drive_service.files().update() with new name."""
        from drive_operations import rename_file

        mock_service = MagicMock()
        rename_file(mock_service, "file123", "new_name.pdf")

        mock_service.files().update.assert_called_once()
        call_kwargs = mock_service.files().update.call_args
        assert call_kwargs.kwargs["fileId"] == "file123"
        assert call_kwargs.kwargs["body"] == {"name": "new_name.pdf"}

    def test_rename_file_uses_drive_support(self):
        """Should pass supportsAllDrives=True for shared drives."""
        from drive_operations import rename_file

        mock_service = MagicMock()
        rename_file(mock_service, "file123", "renamed.pdf")

        call_kwargs = mock_service.files().update.call_args
        assert call_kwargs.kwargs["supportsAllDrives"] is True
