-- Migration 003: Add performance indexes
-- Covers common query patterns for dashboard and job listing

BEGIN;

-- Jobs table: compound index for active scheduled jobs
CREATE INDEX IF NOT EXISTS idx_jobs_active_scheduled
  ON jobs(is_active, trigger_type) WHERE is_active = true;

-- Jobs table: name search
CREATE INDEX IF NOT EXISTS idx_jobs_name ON jobs(name);

-- Job executions: compound index for dashboard (status + time)
CREATE INDEX IF NOT EXISTS idx_job_executions_status_timestamp
  ON job_executions(status, timestamp DESC);

-- Job executions: user + time for user-specific views
CREATE INDEX IF NOT EXISTS idx_job_executions_user_time
  ON job_executions(user_email, timestamp DESC);

COMMIT;
