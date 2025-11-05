# Product Context

  This file provides a high-level overview of the project and the expected product that will be created. Initially it is based upon projectBrief.md (if provided) and all other available project-related information in the working directory. This file is intended to be updated as the project evolves, and should be used to inform all other modes of the project's goals and context.
  
  ## Project Goal
  *   To create a serverless application that automates the processing and organization of files in Google Drive. The application monitors designated folders, analyzes new files using the Gemini AI, renames them based on the analysis, and maintains an HTML index of all processed files.

  ## Key Features
  *   **Automated File Monitoring:** The application checks for new or modified files in user-defined subfolders within a specific Google Drive root folder.
  *   **AI-Powered Content Analysis:** Uses the Gemini AI model (`gemini-2.5-flash`) to analyze the content of new files and extract relevant keywords and a primary date.
  *   **Standardized Renaming:** Renames files to a consistent format: `YYYY-MM-DD_keywords_DOCPROCESADO.extension`.
  *   **HTML Indexing:** Automatically creates and updates an `index.html` file in each monitored folder, providing a clear log of original filenames, new filenames, and a summary.
  *   **State Persistence:** Uses a Google Cloud Storage (GCS) bucket to store a `pageToken`, ensuring that it only processes changes since the last run, making it efficient and scalable.
  *   **Environment-Based Configuration:** All settings (folder IDs, API keys, etc.) are managed via environment variables, allowing for easy configuration between local, testing, and production environments.

  ## Overall Architecture
  *   The application is a Python-based Flask web server.
  *   It is designed to be stateless and run in a serverless environment like Google Cloud Run.
  *   The core logic is triggered by an incoming HTTP POST request. In production, this trigger is intended to be automated by a service like Google Cloud Scheduler.
  *   It integrates with three core Google services: Drive API, Cloud Storage API, and the Gemini API.
  *   Authentication is handled securely via a single Service Account with impersonation, allowing it to act on behalf of a specified user without exposing user credentials.

*2025-11-05 18:30:00 - Updated with final architecture and feature set after successful testing and debugging.*
