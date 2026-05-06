"""
Test: Worker job_loader module.
================================

Verifies job_loader.py loads configs and lists active jobs.

:created:   2026-05-06
:task:      Decompose Worker main.py
"""

import pytest
from unittest.mock import MagicMock

from job_loader import load_job_config, get_all_active_jobs
import job_loader


class TestLoadJobConfig:
    """Load job configuration from database."""

    def test_load_existing_active_job(self):
        mock_db = MagicMock()
        mock_db.find.return_value = [{"id": "job1", "name": "Test", "active": True}]
        original = job_loader.db_manager
        try:
            job_loader.db_manager = mock_db
            result = load_job_config("job1")
            assert result is not None
            assert result["id"] == "job1"
        finally:
            job_loader.db_manager = original

    def test_load_inactive_job_returns_none(self):
        mock_db = MagicMock()
        mock_db.find.return_value = [{"id": "job1", "active": False}]
        original = job_loader.db_manager
        try:
            job_loader.db_manager = mock_db
            result = load_job_config("job1")
            assert result is None
        finally:
            job_loader.db_manager = original

    def test_load_missing_job_returns_none(self):
        mock_db = MagicMock()
        mock_db.find.return_value = []
        original = job_loader.db_manager
        try:
            job_loader.db_manager = mock_db
            result = load_job_config("nonexistent")
            assert result is None
        finally:
            job_loader.db_manager = original

    def test_load_job_handles_db_error(self):
        mock_db = MagicMock()
        mock_db.find.side_effect = Exception("DB error")
        original = job_loader.db_manager
        try:
            job_loader.db_manager = mock_db
            result = load_job_config("job1")
            assert result is None
        finally:
            job_loader.db_manager = original


class TestGetAllActiveJobs:
    """Get all active jobs from database."""

    def test_returns_only_active_jobs(self):
        mock_db = MagicMock()
        mock_db.find_all.return_value = [
            {"id": "j1", "active": True},
            {"id": "j2", "active": False},
            {"id": "j3", "active": True},
        ]
        original = job_loader.db_manager
        try:
            job_loader.db_manager = mock_db
            result = get_all_active_jobs()
            assert len(result) == 2
        finally:
            job_loader.db_manager = original

    def test_returns_empty_on_error(self):
        mock_db = MagicMock()
        mock_db.find_all.side_effect = Exception("DB error")
        original = job_loader.db_manager
        try:
            job_loader.db_manager = mock_db
            result = get_all_active_jobs()
            assert result == []
        finally:
            job_loader.db_manager = original
