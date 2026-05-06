-- Rollback Migration 003: Remove added indexes

BEGIN;

DROP INDEX IF EXISTS idx_jobs_active_scheduled;
DROP INDEX IF EXISTS idx_jobs_name;
DROP INDEX IF EXISTS idx_job_executions_status_timestamp;
DROP INDEX IF EXISTS idx_job_executions_user_time;

COMMIT;
