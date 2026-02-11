# Database Architecture Documentation

## Current Setup (Job Configurations)

### DatabaseManager Instance: `db_manager`
- **Storage**: Google Cloud Storage (GCS)
- **Table/Blob Name**: `jobs`
- **Full Path**: `gs://{GCS_BUCKET_NAME}/data/jobs.json`
- **Purpose**: Stores job **configurations** (templates/algorithms)
- **Examples**: `job-manual-generic`, `job-manual-invoice`

### Data Structure
```json
[
  {
    "id": "job-manual-generic",
    "name": "Manual Job Generic",
    "description": "Auto-generated job configuration",
    "active": true,
    "trigger_type": "manual",
    "source_folder_id": "DYNAMIC",
    "target_folder_names": ["*"],
    "agent_config": {...}
  }
]
```

---

## New Setup (Job Executions) - TO BE IMPLEMENTED

### DatabaseManager Instance: `executions_manager`
- **Storage**: Google Cloud Storage (GCS)
- **Table/Blob Name**: `job_executions`
- **Full Path**: `gs://{GCS_BUCKET_NAME}/data/job_executions.json`
- **Purpose**: Stores job **execution history** (submission logs)

### Data Structure
```json
[
  {
    "id": "exec-1707686400000",
    "user_email": "gonzalo.f.recalde@gmail.com",
    "user_name": "Gonzalo Recalde",
    "folder_id": "1AbCdEf...",
    "job_type": "generic",
    "job_config_id": "job-manual-generic",
    "timestamp": "2026-02-11T20:00:00Z",
    "status": "submitted",
    "task_id": "projects/.../tasks/..."
  }
]
```

---

## Implementation Plan

### Phase 1: Add Executions Manager
```python
# After db_manager initialization (line 99)
executions_manager = DatabaseManager(
    use_gcs=use_gcs,
    table_name="job_executions"
)
logger.info("Executions DatabaseManager initialized")
```

### Phase 2: Log on Submission
Modify `/api/v1/jobs/manual` to log each execution before sending to Cloud Tasks.

### Phase 3: Update Audit Endpoint
Modify `/api/v1/audit-logs` to read from `executions_manager` instead of `db_manager`.

---

## Benefits

1. **Separation of Concerns**: Configurations vs Executions
2. **Audit Trail**: Complete history of all job submissions
3. **User Tracking**: Know who submitted what and when
4. **Debugging**: Trace issues to specific executions
5. **Analytics**: Usage patterns, popular job types, etc.
