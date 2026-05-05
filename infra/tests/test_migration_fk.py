"""Test database foreign key constraints for migration 001."""
import sqlite3
import pytest


@pytest.fixture
def db():
    """Create an in-memory SQLite DB with the v3 schema + FK constraints."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE jobs (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(500) NOT NULL,
            trigger_type VARCHAR(50) NOT NULL,
            source_folder_id VARCHAR(500) NOT NULL,
            agent_config TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE job_executions (
            id VARCHAR(255) PRIMARY KEY,
            user_email VARCHAR(255) NOT NULL,
            folder_id VARCHAR(500),
            job_type VARCHAR(100),
            job_config_id VARCHAR(255) REFERENCES jobs(id) ON DELETE CASCADE,
            timestamp TIMESTAMP NOT NULL,
            status VARCHAR(50) NOT NULL,
            task_id VARCHAR(255),
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_job_executions_job_config_id
            ON job_executions(job_config_id);
    """)
    yield conn
    conn.close()


def test_insert_execution_with_valid_job(db):
    """Execution references a valid job → succeeds."""
    db.execute("INSERT INTO jobs (id, name, trigger_type, source_folder_id, agent_config) VALUES (?, ?, ?, ?, ?)",
               ("job-1", "Test Job", "manual", "folder-1", "{}"))
    db.execute("INSERT INTO job_executions (id, user_email, job_config_id, timestamp, status) VALUES (?, ?, ?, ?, ?)",
               ("exec-1", "user@test.com", "job-1", "2026-01-01T00:00:00Z", "submitted"))
    row = db.execute("SELECT job_config_id FROM job_executions WHERE id = 'exec-1'").fetchone()
    assert row[0] == "job-1"


def test_insert_execution_with_invalid_job_rejected(db):
    """Execution references non-existent job → FK violation."""
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO job_executions (id, user_email, job_config_id, timestamp, status) VALUES (?, ?, ?, ?, ?)",
                   ("exec-2", "user@test.com", "nonexistent", "2026-01-01T00:00:00Z", "submitted"))


def test_cascade_delete_removes_executions(db):
    """Deleting a job cascades to its executions."""
    db.execute("INSERT INTO jobs (id, name, trigger_type, source_folder_id, agent_config) VALUES (?, ?, ?, ?, ?)",
               ("job-1", "Test Job", "manual", "folder-1", "{}"))
    db.execute("INSERT INTO job_executions (id, user_email, job_config_id, timestamp, status) VALUES (?, ?, ?, ?, ?)",
               ("exec-1", "user@test.com", "job-1", "2026-01-01T00:00:00Z", "submitted"))
    db.execute("INSERT INTO job_executions (id, user_email, job_config_id, timestamp, status) VALUES (?, ?, ?, ?, ?)",
               ("exec-2", "user@test.com", "job-1", "2026-01-01T00:00:00Z", "completed"))

    db.execute("DELETE FROM jobs WHERE id = 'job-1'")

    remaining = db.execute("SELECT COUNT(*) FROM job_executions WHERE job_config_id = 'job-1'").fetchone()[0]
    assert remaining == 0


def test_execution_without_job_config_allowed(db):
    """Execution with NULL job_config_id → allowed (for ad-hoc runs)."""
    db.execute("INSERT INTO job_executions (id, user_email, job_config_id, timestamp, status) VALUES (?, ?, ?, ?, ?)",
               ("exec-3", "user@test.com", None, "2026-01-01T00:00:00Z", "submitted"))
    row = db.execute("SELECT job_config_id FROM job_executions WHERE id = 'exec-3'").fetchone()
    assert row[0] is None


def test_delete_one_job_keeps_other_executions(db):
    """Deleting job-1 does not affect job-2's executions."""
    db.execute("INSERT INTO jobs (id, name, trigger_type, source_folder_id, agent_config) VALUES (?, ?, ?, ?, ?)",
               ("job-1", "Job 1", "manual", "f1", "{}"))
    db.execute("INSERT INTO jobs (id, name, trigger_type, source_folder_id, agent_config) VALUES (?, ?, ?, ?, ?)",
               ("job-2", "Job 2", "manual", "f2", "{}"))
    db.execute("INSERT INTO job_executions (id, user_email, job_config_id, timestamp, status) VALUES (?, ?, ?, ?, ?)",
               ("exec-1", "user@test.com", "job-1", "2026-01-01T00:00:00Z", "submitted"))
    db.execute("INSERT INTO job_executions (id, user_email, job_config_id, timestamp, status) VALUES (?, ?, ?, ?, ?)",
               ("exec-2", "user@test.com", "job-2", "2026-01-01T00:00:00Z", "submitted"))

    db.execute("DELETE FROM jobs WHERE id = 'job-1'")

    remaining = db.execute("SELECT COUNT(*) FROM job_executions WHERE job_config_id = 'job-2'").fetchone()[0]
    assert remaining == 1


def test_index_exists(db):
    """Verify the FK index was created."""
    indexes = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_job_executions_job_config_id'").fetchone()
    assert indexes is not None
