# Technical Context

  This file documents the technical stack, dependencies, and architecture decisions.

   ## Technology Stack
   *   **Backend:** Python 3.11
   *   **Web Framework:** Flask
   *   **WSGI Server:** Gunicorn (for production deployment)
   *   **Cloud Platform:** Google Cloud
   *   **Deployment Target:** Google Cloud Run (Serverless)
   *   **Containerization:** Docker
   *   **Core APIs:**
       *   Google Drive API v3
       *   Google Cloud Storage API
       *   Google Generative AI (Gemini) API

  ## Key Dependencies
  *   `google-api-python-client`: To interact with the Google Drive API.
  *   `google-cloud-storage`: To interact with the GCS bucket for state management.
  *   `google-generativeai`: To interact with the Gemini model.
  *   `google-auth` & `google-oauth2`: For handling Service Account authentication and impersonation.
  *   `Flask`: To create the web endpoint that triggers the process.
  *   `gunicorn`: To run the Flask application in a production-ready manner inside the Docker container.
  *   `python-dotenv`: For loading local configuration from the `.env` file during development and testing.
  *   `beautifulsoup4`: For creating and manipulating the `index.html` file.

  ## System Architecture
  *   The application is a stateless Flask service triggered by an HTTP POST request.
  *   State persistence is achieved by storing the Google Drive `pageToken` in a JSON file within a GCS bucket. This is critical for the serverless design, as each execution is ephemeral.
  *   Authentication relies on a Google Service Account. The credentials (as a Base64 encoded JSON) and the user email to impersonate (`DRIVE_IMPERSONATED_USER`) are passed as environment variables, ensuring no sensitive keys are hardcoded.
  *   The `Dockerfile` is configured to build a production-ready image, running the application as a non-root user (`appuser`) for improved security.
  *   Local debugging is supported via a `.vscode/launch.json` configuration that correctly loads the `.env` file and starts the Flask development server.

   *   **AI Model:** Gemini 2.0 Flash Experimental (gemini-2.0-flash-exp)

*2025-11-25 22:30:00 - Updated with production deployment details and current AI model.*
