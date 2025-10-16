# renameDriverFolders - Automated Google Drive File Processor

## Project Overview

This project is a Python-based automated file processor for Google Drive, designed to monitor specified subfolders, analyze new files using the Gemini Pro AI model, rename them with a standardized format, and maintain an `index.html` for easy tracking.

It's built to be deployable as a serverless function (e.g., on Google Cloud Run), but can also be run locally for development and testing.

## Getting Started (For Client)

This section guides you through setting up and running the application locally.

### 1. Prerequisites

*   **Python 3.9+:** Ensure Python is installed on your system.
*   **Google Cloud Project:** You need an active Google Cloud Project with billing enabled.
*   **Service Account:** A Google Cloud Service Account with the following roles:
    *   `Google Drive API` (full access)
    *   `Storage Object Admin` (for Google Cloud Storage)
    *   `Vertex AI User` (for Gemini Pro model access)
*   **Gemini API Key:** An API key for the Gemini model.

### 2. Clone the Repository

First, clone this repository to your local machine:

```bash
git clone <repository_url>
cd renameDriverFolders
```
*(Note: `<repository_url>` will be provided once the GitHub repo is created.)*

### 3. Set up the Python Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies:

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 4. Install Dependencies

With your virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Configuration (`.env` file)

This application uses environment variables for configuration. You need to create a `.env` file in the root directory of the project.

**Steps to create your `.env` file:**

1.  **Create `SERVICE_ACCOUNT_KEY_B64`:**
    *   Download your Service Account JSON key from Google Cloud Console.
    *   Open the JSON file and copy its entire content.
    *   Encode the JSON content to Base64. On Windows PowerShell, you can use:
        ```powershell
        [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Raw "path\to\your\service-account-key.json")))
        ```
    *   On macOS/Linux, you can use:
        ```bash
        base64 -w 0 path/to/your/service-account-key.json
        ```
    *   Copy the resulting Base64 string.

2.  **Populate `.env`:** Create a file named `.env` in the project root and fill it with your specific values:

    ```
    ROOT_FOLDER_ID="<Your_Google_Drive_Root_Folder_ID>"
    TARGET_FOLDER_NAMES='["Doc de Respaldo", "Facturas"]' # Example: Adjust as needed
    GCS_BUCKET_NAME="<Your_Google_Cloud_Storage_Bucket_Name>"
GCP_PROJECT_ID="<Your_Google_Cloud_Project_ID>"
GCP_REGION="us-central1" # Or your preferred region
SERVICE_ACCOUNT_KEY_B64="<Your_Base64_Encoded_Service_Account_JSON>"
GEMINI_API_KEY="<Your_Gemini_API_Key>"
    ```
    *   **`ROOT_FOLDER_ID`**: The Google Drive ID of the main folder you want to monitor.
    *   **`TARGET_FOLDER_NAMES`**: A JSON string of subfolder names within `ROOT_FOLDER_ID` to specifically monitor.
    *   **`GCS_BUCKET_NAME`**: A Google Cloud Storage bucket where the application will store its state (e.g., `pageToken` for Drive changes).
    *   **`GCP_PROJECT_ID`**: Your Google Cloud Project ID.
    *   **`GCP_REGION`**: The region where your Gemini model is deployed (e.g., `us-central1`).
    *   **`SERVICE_ACCOUNT_KEY_B64`**: The Base64 encoded content of your Google Service Account JSON key.
    *   **`GEMINI_API_KEY`**: Your API key for the Gemini model.

### 6. Running the Application Locally

Once configured, you can run the Flask development server:

```bash
# Ensure your virtual environment is activated
python main.py
```

The application will start on `http://localhost:8080`. You can trigger the file processing by sending an HTTP POST request to this endpoint. For example, using `curl`:

```bash
curl -X POST http://localhost:8080/
```

### 7. Running Tests

The project includes basic tests to verify setup and functionality.

```bash
# Ensure your virtual environment is activated
# Run the Gemini import test
python tests/test_gemini_import.py

# Run the integration test (requires proper .env configuration and Google Cloud access)
python tests/test_integration.py
```
*Note: The integration test (`test_integration.py`) will only pass if your `.env` file is correctly configured with valid Google Cloud credentials and the service account has the necessary permissions.*

## Deployment to Google Cloud Run

The application is designed for serverless deployment. Refer to Google Cloud Run documentation for detailed deployment steps. Key considerations:

*   **Containerization:** Use the provided `Dockerfile` (or create one if not present) to build your container image.
*   **Environment Variables:** Configure all required environment variables in the Cloud Run service settings.
*   **Entrypoint:** Use `gunicorn` as the entrypoint for production: `gunicorn --bind :$PORT --workers 1 --threads 8 main:app`.
*   **Triggering:** The service can be triggered via HTTP requests, typically from a scheduler (e.g., Google Cloud Scheduler) or other Cloud services.

## Development Conventions

*   **Configuration:** All configuration is managed through environment variables, following 12-factor app principles.
*   **Modularity:** Code is organized into distinct functions for readability and maintainability.
*   **State Management:** The application is stateless; `pageToken` for Google Drive changes is persisted in a Google Cloud Storage bucket.
*   **Error Handling:** `try...except` blocks are used for robust error management.
