# Decision Log

  This file records architectural and implementation decisions using a list format.

  ## Decision: Use Service Account with Impersonation
  *   **Rationale:** To allow a backend application to securely access a user's Google Drive data without requiring manual OAuth 2.0 user consent flows. This is ideal for automated, non-interactive processes.
  *   **Implementation Details:** The application uses a Service Account key (provided as a Base64 environment variable) and impersonates the user specified in the `DRIVE_IMPERSONATED_USER` environment variable.

  ## Decision: Store State (`pageToken`) in GCS
  *   **Rationale:** To make the application stateless and suitable for serverless environments like Google Cloud Run, where instances are ephemeral. Storing the token externally ensures continuity between runs.
  *   **Implementation Details:** The `pageToken` from the Google Drive API is saved as a JSON file in a designated GCS bucket after each successful run.

  ## Decision: Run as Non-Root User in Docker
  *   **Rationale:** To follow security best practices and reduce the container's attack surface. Running as a non-privileged user limits the potential damage if the application is compromised.
  *   **Implementation Details:** The `Dockerfile` includes steps to create a system user (`appuser`) and switches to this user before executing the application.

  ## Decision: Implement a Centralized Logger
  *   **Rationale:** Simple `print()` statements are insufficient for debugging in a serverless or containerized environment. A proper logger allows for structured, leveled output that can be directed to files or other monitoring services.
  *   **Implementation Details:** The standard Python `logging` module was configured to output DEBUG level messages and higher to both the console (`sys.stdout`) and a file (`app_debug.log`).

  ## Decision: Create a Specific VS Code Debug Configuration
  *   **Rationale:** The default debugger behavior was insufficient as it didn't automatically load the crucial `.env` file. A custom configuration was needed to streamline the local debugging experience.
  *   **Implementation Details:** A `launch.json` file was created with a "Python Debugger: Flask App" configuration that specifies the module to run (`flask`), sets environment variables, and explicitly loads the project's `.env` file.

*2025-11-05 18:30:00 - Log updated with all key decisions made during the debugging and refinement process.*
