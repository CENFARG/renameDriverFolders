-- Rollback Migration 002: Revert is_active → active

BEGIN;

ALTER TABLE jobs RENAME COLUMN is_active TO active;

DROP INDEX IF EXISTS idx_jobs_is_active;
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active);

COMMIT;
