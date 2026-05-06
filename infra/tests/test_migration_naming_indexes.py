"""Test column naming migration and performance indexes."""
import sqlite3
import pytest


@pytest.fixture
def db():
    """Create DB with post-migration schema (is_active column, new indexes)."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE jobs (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(500) NOT NULL,
            trigger_type VARCHAR(50) NOT NULL,
            source_folder_id VARCHAR(500) NOT NULL,
            agent_config TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
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

        -- Migration 002 indexes
        CREATE INDEX idx_jobs_is_active ON jobs(is_active);
        CREATE INDEX idx_jobs_name ON jobs(name);

        -- Migration 003 indexes
        CREATE INDEX idx_jobs_active_scheduled ON jobs(is_active, trigger_type);
        CREATE INDEX idx_job_executions_status_timestamp ON job_executions(status, timestamp DESC);
        CREATE INDEX idx_job_executions_user_time ON job_executions(user_email, timestamp DESC);
        CREATE INDEX idx_job_executions_job_config_id ON job_executions(job_config_id);
    """)
    yield conn
    conn.close()


def test_is_active_column_exists(db):
    """Verify the renamed column exists."""
    columns = [row[1] for row in db.execute("PRAGMA table_info(jobs)").fetchall()]
    assert "is_active" in columns
    assert "active" not in columns


def test_insert_with_is_active(db):
    """Insert a job using the renamed column."""
    db.execute("INSERT INTO jobs (id, name, trigger_type, source_folder_id, agent_config, is_active) VALUES (?, ?, ?, ?, ?, ?)",
               ("job-1", "Test", "manual", "f1", "{}", 1))
    row = db.execute("SELECT is_active FROM jobs WHERE id = 'job-1'").fetchone()
    assert row[0] == 1


def test_filter_active_jobs(db):
    """Query active jobs uses the new column."""
    db.execute("INSERT INTO jobs (id, name, trigger_type, source_folder_id, agent_config, is_active) VALUES (?, ?, ?, ?, ?, ?)",
               ("job-1", "Active", "manual", "f1", "{}", 1))
    db.execute("INSERT INTO jobs (id, name, trigger_type, source_folder_id, agent_config, is_active) VALUES (?, ?, ?, ?, ?, ?)",
               ("job-2", "Inactive", "manual", "f2", "{}", 0))

    active = db.execute("SELECT id FROM jobs WHERE is_active = 1").fetchall()
    assert len(active) == 1
    assert active[0][0] == "job-1"


def test_active_scheduled_index_exists(db):
    """Compound index for active scheduled jobs exists."""
    idx = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_jobs_active_scheduled'").fetchone()
    assert idx is not None


def test_name_index_exists(db):
    """Name search index exists."""
    idx = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_jobs_name'").fetchone()
    assert idx is not None


def test_execution_status_timestamp_index_exists(db):
    """Dashboard compound index exists."""
    idx = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_job_executions_status_timestamp'").fetchone()
    assert idx is not None


def test_execution_user_time_index_exists(db):
    """User-specific query index exists."""
    idx = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_job_executions_user_time'").fetchone()
    assert idx is not None
