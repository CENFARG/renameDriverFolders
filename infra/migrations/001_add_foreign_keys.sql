-- Migration 001: Add Foreign Keys
-- Adds FK constraint from job_executions.job_config_id → jobs.id
-- Includes cascade delete for cleanup when a job is removed

BEGIN;

-- Step 1: Remove orphaned executions (job_config_id references non-existent jobs)
DELETE FROM job_executions
WHERE job_config_id IS NOT NULL
  AND job_config_id NOT IN (SELECT id FROM jobs);

-- Step 2: Add FK constraint with CASCADE DELETE
ALTER TABLE job_executions
  DROP COLUMN IF EXISTS job_config_id,
  ADD COLUMN job_config_id VARCHAR(255)
    REFERENCES jobs(id) ON DELETE CASCADE;

-- Step 3: Add index for FK lookups
CREATE INDEX IF NOT EXISTS idx_job_executions_job_config_id
  ON job_executions(job_config_id);

COMMIT;
