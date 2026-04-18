# System Patterns

This file documents recurring patterns and standards used in project.

## Coding Patterns
*   **Configuration via Environment:** All configuration is managed through environment variables, loaded from a `.env` file locally. This follows 12-factor app methodology and avoids hardcoding settings.
*   **Robust Variable Parsing:** Environment variables are cleaned with `.strip().strip("'\"")` to prevent parsing errors from spaces and quotes.
*   **Centralized Logging:** A standard Python `logging` module is configured to output messages to both console and a file (`app_debug.log`). This provides structured, leveled logging (DEBUG, INFO, ERROR) crucial for diagnostics.
*   **Robust API Error Handling:** All external API calls (Google Drive, GCS, Gemini) are wrapped in `try...except` blocks to handle potential `HttpError` exceptions and other failures gracefully.
*   **Bilingual Commenting:** Code is commented in both English and Spanish to improve clarity and maintainability for a wider audience.
*   **Core Module Usage:** Standardized use of `core` modules (config_manager, logger_manager, error_handler) instead of reinventing functionality.

## Architectural Patterns
*   **Serverless Webhook/Trigger:** The application is designed as a stateless service that executes a task in response to an HTTP POST request. This is a common pattern for serverless functions and event-driven automation.
*   **Externalized State:** To remain stateless, application's state (the Google Drive `pageToken`) is stored externally in a Google Cloud Storage bucket. This allows any instance of the application to resume work from where the last one left off.
*   **Sense-Think-Act Pattern:** Core processing follows a structured approach: Sense (detect changes), Think (analyze with AI), Act (rename and index).
*   **Microservices Integration:** Each Google service (Drive, Storage, Gemini) is integrated as a separate concern with proper error boundaries.

## Testing Patterns
*   **End-to-End Integration Testing:** The project relies on a comprehensive integration test (`test_integration.py`) that simulates the entire workflow, from creating test files in a live Google Drive environment to verifying the final output.
*   **Dynamic Test Environment:** The `setUpClass` and `tearDownClass` methods are used to dynamically create and destroy necessary test resources (folders, files) in Google Drive for each test run.
*   **Configuration Mocking for Tests:** During tests, environment variables like `TARGET_FOLDER_NAMES` are temporarily modified in-memory to point to test-specific folders, isolating the test from the main configuration.
*   **Graceful Test Cleanup:** The `tearDownClass` method specifically catches and ignores `HttpError 404` to prevent the entire test suite from failing if a resource was already deleted during the test itself.

## Deployment Patterns
*   **Container-based Deployment:** Application is packaged in Docker container with non-root user for security.
*   **Environment-specific Configuration:** Different configurations for local development vs production (Cloud Run).
*   **Secret Management:** Sensitive data (API keys, credentials) stored in Google Secret Manager and accessed via environment variables.
*   **Manual Deployment Strategy:** Two-step deployment (`gcloud builds submit` + `gcloud run deploy`) to avoid caching issues and ensure fresh builds.
*   **Progressive Rollout:** Deployments use revision-based updates allowing for rollback if needed.

## Monitoring Patterns
*   **Custom Logging Metrics:** Application-specific metrics created for errors and success tracking.
*   **Structured Logging:** Consistent log format with JSON payloads for machine parsing.
*   **Alert-driven Operations:** JSON templates for alert configuration ready for import.
*   **Dashboard Standardization:** 6-widget dashboard pattern for consistent monitoring across services.

## Documentation Patterns
*   **Tiered Documentation Approach:** Comprehensive guides for developers, quick references for operators, and context for maintainers.
*   **Memory Bank Pattern:** All decisions, progress, and context tracked in structured markdown files.
*   **Template-driven Development:** Programming standards template to prevent common errors and ensure consistency.
*   **Living Documentation:** Documentation updated in real-time with project changes.

## Error Handling Patterns
*   **Specific Exception Handling:** Different exception types handled with appropriate recovery strategies.
*   **Graceful Degradation:** Application continues operating even when non-critical components fail.
*   **Comprehensive Logging:** All errors logged with context for debugging.
*   **User-friendly Messages:** Error responses provide actionable information.

## Security Patterns
*   **Principle of Least Privilege:** Service accounts have minimal required permissions.
*   **Non-root Execution:** Containers run as non-privileged users.
*   **Secret Isolation:** Sensitive data never hardcoded or committed to version control.
*   **Input Validation:** All external inputs validated and sanitized.

## Performance Patterns
*   **Lazy Loading:** Resources loaded only when needed to reduce startup time.
*   **Connection Reuse:** API clients reused across requests when possible.
*   **Efficient State Management:** Only processing changes since last run using page tokens.
*   **Resource Optimization:** Memory and CPU limits configured based on actual usage patterns.

*2025-11-25 23:45:00 - Updated with monitoring, documentation, security, and performance patterns.*
