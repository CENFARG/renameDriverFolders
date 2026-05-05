-- Rollback Migration 001: Remove Foreign Keys
-- Reverts FK constraint from job_executions.job_config_id

BEGIN;

-- Drop index
DROP INDEX IF EXISTS idx_job_executions_job_config_id;

-- Drop FK constraint and revert column to plain VARCHAR
ALTER TABLE job_executions
  DROP COLUMN IF EXISTS job_config_id,
  ADD COLUMN job_config_id VARCHAR(255);

COMMIT;
