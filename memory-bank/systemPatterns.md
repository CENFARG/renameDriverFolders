# System Patterns

  This file documents recurring patterns and standards used in the project.

  ## Coding Patterns
  *   **Configuration via Environment:** All configuration is managed through environment variables, loaded from a `.env` file locally. This follows the 12-factor app methodology and avoids hardcoding settings.
  *   **Centralized Logging:** A standard Python `logging` module is configured to output messages to both the console and a file (`app_debug.log`). This provides structured, leveled logging (DEBUG, INFO, ERROR) crucial for diagnostics.
  *   **Robust API Error Handling:** All external API calls (Google Drive, GCS, Gemini) are wrapped in `try...except` blocks to handle potential `HttpError` exceptions and other failures gracefully.
  *   **Bilingual Commenting:** Code is commented in both English and Spanish to improve clarity and maintainability for a wider audience.

  ## Architectural Patterns
  *   **Serverless Webhook/Trigger:** The application is designed as a stateless service that executes a task in response to an HTTP POST request. This is a common pattern for serverless functions and event-driven automation.
  *   **Externalized State:** To remain stateless, the application's state (the Google Drive `pageToken`) is stored externally in a Google Cloud Storage bucket. This allows any instance of the application to resume work from where the last one left off.

  ## Testing Patterns
  *   **End-to-End Integration Testing:** The project relies on a comprehensive integration test (`test_integration.py`) that simulates the entire workflow, from creating test files in a live Google Drive environment to verifying the final output.
  *   **Dynamic Test Environment:** The `setUpClass` and `tearDownClass` methods are used to dynamically create and destroy the necessary test resources (folders, files) in Google Drive for each test run.
  *   **Configuration Mocking for Tests:** During tests, environment variables like `TARGET_FOLDER_NAMES` are temporarily modified in-memory to point to test-specific folders, isolating the test from the main configuration.
  *   **Graceful Test Cleanup:** The `tearDownClass` method specifically catches and ignores `HttpError 404` to prevent the entire test suite from failing if a resource was already deleted during the test itself.

*2025-11-05 18:30:00 - Updated with testing, architectural, and coding patterns established during development.*
