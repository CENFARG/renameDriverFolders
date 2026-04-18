# Lesson: Cloud Run Vertex AI Initialization & Worker Config

**Project:** renameDriverFolders
**Date:** 2025-12-12
**Context_Tags:** #CloudRun #Python #VertexAI #GoogleGenAI_V1 #FastAPI
**User_Working_Style_Update:** Prioritize capturing "Lessons Learned" in structured, algorithmic formats (Context->Trigger->Rule) within a `.lessons` folder over simply fixing bugs. The goal is to build a reusable knowledge base for future agents.

## Executive Summary
Failed to initialize `google-genai` (Gemini) client on Cloud Run Worker due to missing project/location context, which the V1 SDK does not auto-discover in all environments. Resolved by injecting `GCP_PROJECT` and `GCP_LOCATION` environment variables and forcing `vertexai=True` in the constructor. Also standardized explicit environment variable definition in deployment commands.

## Algorithmic Directives

### 1. Vertex AI Client Initialization
*   **Condition (IF):** Initializing `google-genai` (V1 SDK) or `Agno` Gemini models (`agno.models.google.Gemini`) in a serverless environment (Cloud Run/Functions).
*   **Trigger (WHEN):** Instantiating the model class (e.g., `Gemini(id=...)`).
*   **Rule (THEN):** MUST explicitly provide `project_id`, `location`, and `vertexai=True` arguments. DO NOT refrain from passing them assuming ADC will handle discovery.
*   **Reasoning:** The V1 SDK is strict about "Cloud" (Vertex) vs "AI Studio" (API Key) modes. Without explicit Cloud params, it may default to API Key mode or fail validation.

### 2. Environment Variable Propagation
*   **Condition (IF):** Deploying a Service (Cloud Run) that depends on Project ID/Location.
*   **Trigger (WHEN):** Running `gcloud run deploy`.
*   **Rule (THEN):** MUST verify that `GCP_PROJECT` and `GCP_LOCATION` are set via `--set-env-vars` or `cloudbuild.yaml`. Do not assume the runtime env contains them with those specific keys.
*   **Reasoning:** Cloud Run provides `PORT` and `K_SERVICE` but strict GCP identity vars often need explicit mapping.

### 3. Static Config in DockerImages
*   **Condition (IF):** Logic depends on static JSON files (e.g., `jobs.json`) packaged in the image.
*   **Trigger (WHEN):** Deploying a new revision after changing local config.
*   **Rule (THEN):** MUST consistency check that the file is `COPY`'d correctly in Dockerfile and that the build context includes the updated file.
*   **Reasoning:** "Ghost Jobs" (404s) occur when code is updated but data files in the image remain stale.

### 4. Deploy Command Syntax (PowerShell)
*   **Condition (IF):** running `gcloud run deploy ... --set-env-vars` from PowerShell.
*   **Trigger (WHEN):** Passing multiple comma-separated variables `KEY=VAL,KEY2=VAL2`.
*   **Rule (THEN):** MUST wrap the entire argument in quotes: `--set-env-vars "KEY=VAL,KEY2=VAL2"`.
*   **Reasoning:** PowerShell parsing can merge arguments or mishandle the comma, causing `KEY1` to contain the value of `KEY1,KEY2=...` which leads to invalid configuration values (e.g., Project ID becomes "id KEY2=val2").

## Future Checklist
*   [ ] Verify `agent_factory.py` reads `os.environ["GCP_PROJECT"]`.
*   [ ] Verify `gcloud run deploy` command includes `GCP_PROJECT` and `GCP_LOCATION`.
*   [ ] Check `jobs.json` content inside the container if "Job not found" errors persist.
