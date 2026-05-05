-- Migration 002: Rename active → is_active in jobs table
-- Standardizes naming with document_algorithms.is_active

BEGIN;

-- Rename column for consistency
ALTER TABLE jobs RENAME COLUMN active TO is_active;

-- Update index (drop old, create new)
DROP INDEX IF EXISTS idx_jobs_active;
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active) WHERE is_active = true;

COMMIT;
