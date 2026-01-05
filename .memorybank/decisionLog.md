# Decision Log

This file records architectural and implementation decisions using a list format.

## Decision: Refactor to Microservices Architecture (V3)
*   **Date:** 2025-11-28
*   **Rationale:** The existing monolithic application, while functional for a single automated task, cannot support the client's full vision, which requires both automated processing and a manual, user-driven UI. A decoupled architecture is needed to support these dual workflows, improve scalability, and align with #ambotOS standards.
*   **Implementation Details:** The project will be refactored into a monorepo containing:
    1.  A shared `core-renombrador` Python package with all business logic.
    2.  An `api-server` microservice to handle incoming HTTP requests (from the UI and Scheduler) and create tasks.
    3.  A `worker-renombrador` microservice (an `AgentOS` app) that processes tasks asynchronously from a Google Cloud Tasks queue.
*   **Consequences:** This significantly improves modularity, reusability, and scalability. It allows the "brain" (`core-renombrador`) to be used by multiple triggers and paves the way for dynamic, database-driven agent configuration. It requires a more complex multi-service deployment setup.

## Decision: Use Service Account with Impersonation
*   **Rationale:** To allow a backend application to securely access a user's Google Drive data without requiring manual OAuth 2.0 user consent flows. This is ideal for automated, non-interactive processes.
*   **Implementation Details:** The application uses a Service Account key (provided as a Base64 environment variable) and impersonates user specified in `DRIVE_IMPERSONATED_USER` environment variable.

## Decision: Store State (`pageToken`) in GCS
*   **Rationale:** To make the application stateless and suitable for serverless environments like Google Cloud Run, where instances are ephemeral. Storing token externally ensures continuity between runs.
*   **Implementation Details:** The `pageToken` from Google Drive API is saved as a JSON file in a designated GCS bucket after each successful run.

## Decision: Run as Non-Root User in Docker
*   **Rationale:** To follow security best practices and reduce the container's attack surface. Running as a non-privileged user limits potential damage if the application is compromised.
*   **Implementation Details:** The `Dockerfile` includes steps to create a system user (`appuser`) and switches to this user before executing the application.

## Decision: Implement a Centralized Logger
*   **Rationale:** Simple `print()` statements are insufficient for debugging in a serverless or containerized environment. A proper logger allows for structured, leveled output that can be directed to files or other monitoring services.
*   **Implementation Details:** The standard Python `logging` module was configured to output DEBUG level messages and higher to both console (`sys.stdout`) and a file (`app_debug.log`).

## Decision: Create a Specific VS Code Debug Configuration
*   **Rationale:** The default debugger behavior was insufficient as it didn't automatically load crucial `.env` file. A custom configuration was needed to streamline the local debugging experience.
*   **Implementation Details:** A `launch.json` file was created with a "Python Debugger: Flask App" configuration that specifies the module to run (`flask`), sets environment variables, and explicitly loads the project's `.env` file.

## Decision: Change ROOT_FOLDER_ID Strategy
*   **Rationale:** The original root folder "Temporal" (0AJbBisiIAtpmUk9PVA) was not accessible by the service account, causing empty folder search results.
*   **Implementation Details:** Changed ROOT_FOLDER_ID to "test_integrado" (1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn) which contains the target "doc de respaldo" folder and has proper service account permissions.

## Decision: Update Gemini Model
*   **Rationale:** The "gemini-2.5-flash" model was returning 404 errors, indicating it's not available in the API version being used.
*   **Implementation Details:** Updated to "gemini-2.0-flash-exp" model which is available and working correctly.

## Decision: Fix Environment Variable Mapping
*   **Rationale:** Cloud Run deployment was incorrectly mapping GOOGLE_APPLICATION_CREDENTIALS to DRIVE_IMPERSONATED_USER secret, causing authentication failures.
*   **Implementation Details:** Corrected environment variable names to match code expectations: DRIVE_IMPERSONATED_USER, GEMINI_API_KEY, ROOT_FOLDER_ID, GCS_BUCKET_NAME.

## Decision: Use Manual Deployment Strategy
*   **Rationale:** Automated deployment scripts were experiencing caching issues with Cloud Build, causing old code to be deployed despite changes.
*   **Implementation Details:** Implemented manual two-step deployment: `gcloud builds submit` followed by `gcloud run deploy` to ensure fresh builds and avoid cache problems.

## Decision: Implement Comprehensive Monitoring
*   **Rationale:** Production applications require proactive monitoring to detect issues before they impact users and to track performance metrics.
*   **Implementation Details:** Created custom logging metrics (rename-driver-errors, rename-driver-success) and documented complete alerting infrastructure with JSON templates for error rate and response time monitoring.

## Decision: Create Programming Standards Template
*   **Rationale:** Multiple similar errors occurred during development (environment variable parsing, import structure, error handling) that could be prevented with established patterns.
*   **Implementation Details:** Created TemplateProgramacionCENF.md with rules of thumb, architectural patterns, and checklists to prevent common mistakes and ensure code consistency.

## Decision: Use Hybrid Documentation Approach
*   **Rationale:** Different stakeholders need different levels of detail - developers need comprehensive guides, operators need quick references, and future maintainers need context.
*   **Implementation Details:** Created tiered documentation: DEPLOYMENT_DOCUMENTATION.md (comprehensive), QUICK_DEPLOYMENT.md (essential commands), MONITORING_SETUP.md (operational focus), and updated README.md with production status.

## Decision: Leverage Existing Google Cloud Scheduler
*   **Rationale:** The client already had Google Cloud Scheduler configured (rename-driver-folders-v1-07112025-schedul), eliminating the need to create new automation infrastructure.
*   **Implementation Details:** Verified existing scheduler configuration and focused monitoring setup on complementing the existing automation rather than rebuilding it.

*2025-11-25 23:45:00 - Log updated with monitoring, documentation, and final production decisions.*
