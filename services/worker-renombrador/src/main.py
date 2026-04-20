"""
Worker Renombrador - Multi-Job Processing
==========================================

Worker service que procesa jobs de renombrado de archivos.
Soporta múltiples jobs con diferentes configuraciones y schedules.

:created:   2025-12-05
:filename:  main.py
:author:    amBotHs + CENF
:version:   2.0.0
:status:    Development
:license:   MIT
:copyright: Copyright (c) 2025 CENF
"""

import os
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
import google.auth
from google.oauth2 import service_account
from google.oauth2 import credentials as oauth2_credentials  # OAuth user credentials
from google.cloud import storage
import google_auth_httplib2
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
# from google.cloud import secretmanager  # Imported below optionally
from googleapiclient.discovery import build

# Core modules
from core_renombrador.config_manager import ConfigManager
from core_renombrador.logger_manager import LoggerManager
from core_renombrador.database_manager import DatabaseManager
from core_renombrador.file_manager import FileManager
from core_renombrador.agent_factory import AgentFactory, create_document_agent
from core_renombrador.drive_handler import DriveHandler
from core_renombrador.content_extractor import ContentExtractor

def get_secret(secret_id: str) -> str:
    """
    Get secret from Secret Manager (production) or .env (local)

    Priority:
    1. Environment variable (for local dev)
    2. Secret Manager (for production)
    """
    # Check if running locally (has .env file)
    env_var = secret_id.upper().replace("-", "_")
    local_value = os.environ.get(env_var)

    if local_value:
        logger.info(f"Using local config for {secret_id}")
        return local_value.strip()

    # Production: use Secret Manager
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT_ID", "cloud-functions-474716")
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        logger.info(f"Using Secret Manager for {secret_id}")
        return response.payload.data.decode("UTF-8").strip()
    except ImportError as e:
        logger.warning(f"Secret Manager not available: {e}")
        logger.warning(f"Please set {env_var} environment variable")
        return ""
    except Exception as e:
        logger.warning(f"Failed to get secret {secret_id}: {e}")
        return ""


# --- Initialization ---
config_manager = ConfigManager(config_path="config.json")
LoggerManager.initialize(config_manager)

# Enable DEBUG logging for troubleshooting (TODO: Remove in production)
logging.basicConfig(level=logging.DEBUG)
logger = LoggerManager.get_logger(__name__)
logger.setLevel(logging.DEBUG)
logger.debug("Worker initialized with DEBUG logging enabled")

# Database Manager
file_manager = FileManager(base_path="./data", config_manager=config_manager)
use_supabase = os.environ.get("USE_SUPABASE", "false").lower() == "true"

use_gcs = os.environ.get("USE_GCS", "false").lower() == "true" or "GCS_BUCKET_NAME" in os.environ

# Load Supabase credentials from Secret Manager if using Supabase
if use_supabase:
    supabase_url = get_secret("supabase-url")
    supabase_key = get_secret("supabase-key")

    if supabase_url and supabase_key:
        os.environ["SUPABASE_URL"] = supabase_url
        os.environ["SUPABASE_KEY"] = supabase_key
        logger.info("Supabase credentials loaded from Secret Manager")
    else:
        logger.warning("Supabase credentials not found in Secret Manager, falling back to JSON mode")
        use_supabase = False

if use_supabase:
    db_manager = DatabaseManager(
        use_supabase=True,
        table_name="jobs"
    )
    logger.info("DatabaseManager initialized in Supabase mode")
elif use_gcs:
    db_manager = DatabaseManager(
        use_gcs=True,
        table_name="jobs"
    )
    logger.info("DatabaseManager initialized in GCS mode")
else:
    db_manager = DatabaseManager(
        file_manager=file_manager,
        db_path="data/jobs.json"
    )
    logger.info("DatabaseManager initialized in JSON mode")

# Job Executions Manager (for audit logs)
if use_supabase:
    executions_manager = DatabaseManager(use_supabase=True, table_name="job_executions")
    logger.info("Executions DatabaseManager initialized in Supabase mode")
elif use_gcs:
    executions_manager = DatabaseManager(
        use_gcs=True,
        table_name="job_executions"
    )
    logger.info("Executions DatabaseManager initialized in GCS mode")
else:
    executions_manager = DatabaseManager(
        file_manager=file_manager,
        db_path="data/job_executions.json"
    )
    logger.info("Executions DatabaseManager initialized in JSON mode")

# Agent Factory
agent_factory = AgentFactory(
    database_manager=db_manager,
    config_manager=config_manager
)

# Content Extractor with OCR
enable_ocr = os.environ.get("ENABLE_OCR", "true").lower() == "true"
content_extractor = ContentExtractor(enable_ocr=enable_ocr)
logger.info(f"ContentExtractor initialized (OCR: {enable_ocr})")

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Life span of the application.
    """
    logger.info("Worker Version: v2-00016 (Fix Extra Fields - ConfigDict)")
    logger.info(f"Starting Worker... Config loaded.")
    
    # Initialize things here if needed
    yield
    
    logger.info("Shutting down Worker...")

# FastAPI app
app = FastAPI(
    title="Worker Renombrador",
    description="Multi-job document processing worker",
    version="2.0.0",
    lifespan=lifespan
)


# --- Request Models ---

class UserCredentials(BaseModel):
    """
    User OAuth credentials passed from API Server.

    Security:
    - access_token is validated by API Server before being sent
    - Token is short-lived (~60 min)
    - Scope is limited to drive API
    """
    access_token: str
    email: str
    name: Optional[str] = None
    scope: str = "https://www.googleapis.com/auth/drive"

    class Config:
        # Extra fields for future compatibility
        extra = "ignore"


class TaskPayload(BaseModel):
    """
    Payload for Cloud Tasks.

    Contains job configuration and optionally user credentials.
    """
    job_id: Optional[str] = None
    folder_id: Optional[str] = None
    user_token: Optional[str] = None  # Deprecated: kept for backward compatibility
    trigger_type: str = "scheduled"  # "scheduled" or "manual"
    execution_id: Optional[str] = None

    # NEW: User OAuth credentials (optional, for manual jobs)
    user_credentials: Optional[UserCredentials] = None


class JobRunRequest(BaseModel):
    """
    Request to run a specific job.
    """
    job_id: str
    folder_id: Optional[str] = None  # For manual jobs


# --- Helper Functions ---

def get_credentials():
    """
    Get Google Cloud credentials (Service Account or ADC).
    Obtiene credenciales de Google Cloud (Service Account o ADC).
    """
    SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    try:
        # Try Application Default Credentials first (Cloud Run)
        credentials, project_id = google.auth.default(scopes=SCOPES)
        logger.info("Using Application Default Credentials")
        return credentials
    except Exception as e:
        logger.error(f"Failed to get credentials: {e}")
        raise


def get_user_credentials(access_token: str, scope: str):
    """
    Create OAuth credentials from user access token.

    This creates credentials that the Worker can use to access Google Drive
    on behalf of the user, instead of using service account credentials.

    Args:
        access_token: User's OAuth access token (validated by API Server)
        scope: OAuth scope (e.g., https://www.googleapis.com/auth/drive)

    Returns:
        OAuth credentials object for Google API calls

    Security:
    - Access token is short-lived (~60 min)
    - No refresh token is stored
    - Credentials are only used in memory
    """
    # Use google.oauth2.credentials.Credentials instead of OAuthCredentials
    # to prevent automatic token refresh attempts
    return oauth2_credentials.Credentials(
        token=access_token,
        scopes=[scope],
        # Disable token refresh - we don't have refresh_token
        expiry=None,
        token_uri=None,
        client_id=None,
        client_secret=None
    )


def build_drive_service_with_credentials(credentials):
    """
    Build Drive service with custom HTTP object that injects Bearer token manually.

    CRITICAL: google_auth_httplib2.AuthorizedHttp ALWAYS attempts to refresh
    credentials on 401/403, regardless of how credentials are configured.

    Solution: Create custom Http object that adds Authorization header to every request.
    """
    import httplib2

    # Store the access token
    access_token = credentials.token

    logger.info(f"🔧 Building Drive service with manual Bearer token injection")
    logger.info(f"🔧 Access token: {mask_access_token(access_token)}")

    # Create custom HTTP object that injects Bearer token
    class TokenInjectorHttp(httplib2.Http):
        def request(self, uri, method="GET", body=None, headers=None,
                   redirections=1, connection_type=None):
            # Inject Authorization header into every request
            if headers is None:
                headers = {}
            headers['Authorization'] = f'Bearer {access_token}'

            logger.debug(f"🔑 Injected Bearer token into {method} request to {uri}")

            # Call parent request with updated headers
            return super().request(uri, method, body, headers,
                                  redirections, connection_type)

    # Build Drive service with custom HTTP object
    http = TokenInjectorHttp()
    drive_service = build("drive", "v3", http=http)

    logger.info("✅ Drive service built successfully (manual token injection)")
    return drive_service


def mask_access_token(token: str) -> str:
    """
    Mask access token for safe logging.

    Shows only first 4 and last 4 characters.

    Args:
        token: Access token to mask

    Returns:
        Masked token string
    """
    if len(token) > 8:
        return f"{token[:4]}...{token[-4:]}"
    return "****"


def load_job_config(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Load job configuration from database.
    Carga configuración de job desde base de datos.
    """
    try:
        jobs = db_manager.find("id", job_id)
        if jobs:
            job = jobs[0]
            if not job.get("active", True):
                logger.warning(f"Job '{job_id}' is not active")
                return None
            return job
        else:
            logger.warning(f"Job '{job_id}' not found in database")
            return None
    except Exception as e:
        logger.error(f"Error loading job config: {e}")
        return None


def get_all_active_jobs() -> list:
    """
    Get all active jobs from database.
    Obtiene todos los jobs activos desde base de datos.
    """
    try:
        all_jobs = db_manager.find_all()
        active_jobs = [job for job in all_jobs if job.get("active", True)]
        logger.info(f"Found {len(active_jobs)} active jobs")
        return active_jobs
    except Exception as e:
        logger.error(f"Error getting active jobs: {e}")
        return []


def process_job(
    job_config: Dict[str, Any],
    folder_id: Optional[str] = None,
    credentials = None
) -> Dict[str, Any]:
    """
    Process a single job.
    Procesa un solo job.
    
    Args:
        job_config: Job configuration from database.
        folder_id: Override folder ID (for manual jobs).
        credentials: Google Cloud credentials.
    
    Returns:
        Result dictionary with status and stats.
    """
    job_id = job_config.get("id")
    job_name = job_config.get("name")
    
    logger.info(f"Starting job '{job_name}' (ID: {job_id})")
    
    try:
        # Use provided folder_id or get from config
        target_folder_id = folder_id or job_config.get("source_folder_id")
        
        if not target_folder_id or target_folder_id == "DYNAMIC":
            raise ValueError(f"No folder_id provided for job '{job_id}'")
        
        # Create agent for this job using AgentFactory
        agent = agent_factory.create_agent_from_job_config(job_config)
        logger.info(f"Agent created for job '{job_name}'")

        # ============================================================
        # DEBUG: Verificar credenciales antes de crear Drive service
        # ============================================================
        logger.info(f"🔍 Credentials type: {type(credentials).__name__}")
        logger.info(f"🔍 Credentials module: {type(credentials).__module__}")
        logger.info(f"🔍 Credentials token: {mask_access_token(credentials.token) if hasattr(credentials, 'token') else 'NO TOKEN'}")
        logger.info(f"🔍 Credentials scopes: {credentials.scopes if hasattr(credentials, 'scopes') else 'NO SCOPES'}")
        logger.info(f"🔍 Credentials expiry: {credentials.expiry if hasattr(credentials, 'expiry') else 'NO EXPIRY'}")
        logger.info(f"🔍 Credentials token_uri: {credentials.token_uri if hasattr(credentials, 'token_uri') else 'NO TOKEN_URI'}")
        logger.info(f"🔍 Credentials client_id: {credentials.client_id if hasattr(credentials, 'client_id') else 'NO CLIENT_ID'}")
        # ============================================================

        # Initialize Drive service with custom HTTP transport (no auto-refresh)
        drive_service = build_drive_service_with_credentials(credentials)
        storage_client = storage.Client(credentials=credentials)
        
        # Get target folder names
        target_folder_names = job_config.get("target_folder_names", ["*"])
        
        # Process files
        stats = {
            "files_processed": 0,
            "files_renamed": 0,
            "errors": 0
        }
        
        # If target_folder_names is ["*"], process all files in folder
        if target_folder_names == ["*"]:
            folders_to_process = [target_folder_id]
        else:
            # Find specific subfolders
            folders_to_process = find_target_folders(
                drive_service,
                target_folder_id,
                target_folder_names
            )
        
        for folder in folders_to_process:
            folder_stats = process_folder_files(
                drive_service=drive_service,
                folder_id=folder,
                agent=agent,
                job_config=job_config
            )
            stats["files_processed"] += folder_stats["files_processed"]
            stats["files_renamed"] += folder_stats["files_renamed"]
            stats["errors"] += folder_stats["errors"]
        
        logger.info(
            f"Job '{job_name}' completed. "
            f"Processed: {stats['files_processed']}, "
            f"Renamed: {stats['files_renamed']}, "
            f"Errors: {stats['errors']}"
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "job_name": job_name,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error processing job '{job_name}': {e}", exc_info=True)
        return {
            "status": "error",
            "job_id": job_id,
            "job_name": job_name,
            "error": str(e)
        }


def find_target_folders(
    drive_service,
    root_folder_id: str,
    target_names: list
) -> list:
    """
    Find specific folders by name within a root folder.
    Encuentra carpetas específicas por nombre dentro de una carpeta raíz.
    """
    found_folders = []
    
    try:
        query = f"'{root_folder_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"
        response = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        folders = response.get("files", [])
        
        for folder in folders:
            if folder["name"] in target_names:
                found_folders.append(folder["id"])
                logger.info(f"Found target folder: {folder['name']} (ID: {folder['id']})")
    
    except Exception as e:
        logger.error(f"Error finding folders: {e}")
    
    return found_folders


def process_folder_files(
    drive_service,
    folder_id: str,
    agent,
    job_config: Dict[str, Any]
) -> Dict[str, int]:
    """
    Process all files in a folder.
    Procesa todos los archivos en una carpeta.
    """
    stats = {"files_processed": 0, "files_renamed": 0, "errors": 0}
    
    try:
        # List files in folder
        query = f"'{folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
        response = drive_service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        files = response.get("files", [])
        logger.info(f"Found {len(files)} files in folder {folder_id}")
        
        for file in files:
            stats["files_processed"] += 1
            
            # Skip already processed files
            if "DOCPROCESADO" in file["name"] or file["name"] == "index.html":
                continue
            
            try:
                # Download file content
                file_bytes = download_file(drive_service, file["id"])
                
                # Extract content (with OCR if needed)
                content = content_extractor.get_content(file["name"], file_bytes)
                logger.info(f"Extracted content length: {len(content)} chars for {file['name']}")
                
                # Analyze with agent
                prompt = job_config["agent_config"]["prompt_template"].format(
                    original_filename=file["name"],
                    file_content=content[:8000]  # Limit content
                )
                
                # LOG COMPLETO DEL PROMPT
                print("\n" + "="*80)
                print("PROMPT SENT TO GEMINI:")
                print("="*80)
                print(prompt[:2000])  # Primeros 2000 chars
                print("..." if len(prompt) > 2000 else "")
                print("="*80 + "\n")
                
                logger.info(f"Sending prompt to Gemini for {file['name']} (prompt length: {len(prompt)} chars)")
                
                response = agent.run(prompt)
                
                # LOG COMPLETO DE LA RESPUESTA
                print("\n" + "="*80)
                print("RAW RESPONSE FROM GEMINI:")
                print("="*80)
                print(f"Type: {type(response)}")
                print(f"Has .content: {hasattr(response, 'content')}")
                if hasattr(response, 'content'):
                    print(f"Content type: {type(response.content)}")
                    print(f"Content: {response.content}")
                print(f"Response repr: {repr(response)[:500]}")
                print("="*80 + "\n")
                
                logger.info(f"Gemini response received for {file['name']}")
                
                # Parse response (should match output_schema)
                # For now, assume response.content has the structured data
                analysis = parse_agent_response(response)
                logger.info(f"Parsed analysis for {file['name']}: {analysis}")
                
                # Rename file
                new_name = build_filename(file["name"], analysis, job_config)
                logger.info(f"Generated filename: {new_name}")
                
                rename_file(drive_service, file["id"], new_name)
                stats["files_renamed"] += 1
                logger.info(f"Renamed: {file['name']} -> {new_name}")
                
            except Exception as e:
                logger.error(f"Error processing file {file['name']}: {e}")
                stats["errors"] += 1
    
    except Exception as e:
        logger.error(f"Error listing files in folder {folder_id}: {e}")
        stats["errors"] += 1
    
    return stats


def download_file(drive_service, file_id: str) -> bytes:
    """Download file from Drive."""
    from googleapiclient.http import MediaIoBaseDownload
    from io import BytesIO
    
    request = drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
    file_bytes = BytesIO()
    downloader = MediaIoBaseDownload(file_bytes, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    return file_bytes.getvalue()


def parse_agent_response(response) -> Dict[str, Any]:
    """
    Parse agent response to extract structured data.
    
    With Agno's output_schema (Pydantic), the response should already be a Pydantic model.
    This function now simply converts it to dict.
    
    UPDATED: Simplified since Agno guarantees structured Pydantic output.
    """
    logger.debug(f"Parsing agent response. Type: {type(response)}")
    
    # Check if response has Pydantic model_dump() method (Pydantic v2)
    if hasattr(response, 'model_dump'):
        result = response.model_dump()
        logger.debug(f"Successfully converted Pydantic model to dict: {result}")
        return result
    
    # Check if response has dict() method (Pydantic v1)
    if hasattr(response, 'dict'):
        result = response.dict()
        logger.debug(f"Successfully converted Pydantic model to dict (v1): {result}")
        return result
    
    # If response has .content attribute
    if hasattr(response, "content"):
        content = response.content
        logger.debug(f"Response has .content attribute. Type: {type(content)}")
        
        # If content is already a Pydantic model
        if hasattr(content, 'model_dump'):
            result = content.model_dump()
            logger.debug(f"Converted content Pydantic model to dict: {result}")
            return result
        
        # If content is a dict
        if isinstance(content, dict):
            logger.debug(f"Content is already a dict: {content}")
            return content
        
        # If content is a string, try to parse as JSON (fallback)
        if isinstance(content, str):
            logger.warning(f"Content is string, attempting JSON parse: {content[:200]}...")
            import json
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                result = json.loads(content.strip())
                logger.info(f"Successfully parsed JSON from string: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}. Content: {content[:500]}")
                return {"date": "2025-01-01", "keywords": ["documento"]}
    
    # Last resort fallback
    logger.error(f"Unable to parse response. Type: {type(response)}. Using fallback values.")
    return {"date": "2025-01-01", "keywords": ["documento"]}


def build_filename(
    original_name: str,
    analysis: Dict[str, Any],
    job_config: Dict[str, Any]
) -> str:
    """
    Build new filename from analysis with alias support and case-insensitivity.
    Construye el nuevo nombre de archivo con soporte para alias e insensibilidad a mayúsculas.
    """
    import os
    from collections import defaultdict
    
    template = job_config["agent_config"]["filename_format"]
    ext = os.path.splitext(original_name)[1]
    
    # 1. Prepare raw variables from analysis (lowercase keys for matching)
    raw_vars = {k.lower(): v for k, v in analysis.items()}
    
    # 2. Build keywords string
    keywords_list = analysis.get("keywords", [])
    if not isinstance(keywords_list, list):
        keywords_list = [str(keywords_list)]
    
    keywords_str = "_".join(keywords_list) if keywords_list else "doc"
    
    # 3. Define Standard Variables (The "Big 4")
    template_vars = {
        "date": analysis.get("date") or raw_vars.get("fecha") or "2025-01-01",
        "keywords": keywords_str,
        "ext": ext,
        "original_filename": os.path.splitext(original_name)[0]
    }
    
    # 4. Add Aliases / Mapping for common template placeholders
    # If keywords has 3 elements: [type, entity, concept]
    if len(keywords_list) >= 1:
        template_vars["type"] = keywords_list[0]
    if len(keywords_list) >= 2:
        template_vars["issuer"] = keywords_list[1]
        template_vars["entity"] = keywords_list[1]
    if len(keywords_list) >= 3:
        template_vars["brief_detail"] = keywords_list[2]
        template_vars["concept"] = keywords_list[2]

    # 5. Merge all analysis fields (prefer existing title-case if matching)
    for key, value in analysis.items():
        low_key = key.lower()
        if low_key not in template_vars:
            if isinstance(value, list):
                template_vars[low_key] = "_".join(map(str, value))
            else:
                template_vars[low_key] = value

    # 6. Create Case-Insensitive safe_vars mapper
    # This allows {CATEGORY} or {category} or {Category} to work
    class CaseInsensitiveDict(defaultdict):
        def __missing__(self, key):
            return self.get(key.lower(), "unknown")

    safe_vars = CaseInsensitiveDict(lambda: "unknown")
    for k, v in template_vars.items():
        safe_vars[k.lower()] = v
        safe_vars[k] = v # Keep original just in case

    try:
        # Use format_map for safe replacement
        new_name = template.format_map(safe_vars)
        logger.info(f"Filename generated: {new_name} using template: {template}")
    except Exception as e:
        logger.error(f"Error formatting filename with template '{template}': {e}")
        new_name = f"{template_vars['date']}_{template_vars['keywords']}{ext}"
    
    return new_name


def rename_file(drive_service, file_id: str, new_name: str):
    """Rename file in Drive."""
    drive_service.files().update(
        fileId=file_id,
        body={"name": new_name},
        fields="id, name",
        supportsAllDrives=True
    ).execute()


# --- API Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "worker-renombrador",
        "version": "2.0.0"
    }


@app.get("/debug/code")
async def debug_code():
    """
    DEBUG: Return source code of critical functions to verify deployed code.
    This endpoint allows us to check what code is actually running in production.
    """
    import inspect

    return {
        "function": "get_user_credentials",
        "source": inspect.getsource(get_user_credentials),
        "module": get_user_credentials.__module__,
        "file": inspect.getfile(get_user_credentials)
    }


@app.post("/run-task")
async def run_task(request: Request):
    """
    Main endpoint triggered by Cloud Tasks.
    Punto de entrada principal disparado por Cloud Tasks.

    Processes jobs with user OAuth credentials (manual jobs) or
    service account credentials (scheduled jobs).

    Security:
    - OIDC token verification for Cloud Tasks authentication
    - Only Cloud Tasks service account can invoke this endpoint
    - User credentials are used when available (manual jobs)
    - Service account fallback for scheduled jobs
    - Access tokens are masked in logs
    """
    # ============================================================
    # SECURITY: Verify OIDC token from Cloud Tasks
    # ============================================================
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        logger.warning("🚨 SECURITY: Missing Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. This endpoint requires OIDC authentication from Cloud Tasks."
        )

    if not auth_header.startswith("Bearer "):
        logger.warning(f"🚨 SECURITY: Invalid Authorization header format: {auth_header[:20]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>"
        )

    token = auth_header.split(" ")[1]

    try:
        # Verify OIDC token
        expected_audience = os.environ.get("WORKER_URL")
        if not expected_audience:
            logger.error("🚨 SECURITY: WORKER_URL environment variable not set")
            raise HTTPException(
                status_code=500,
                detail="Server configuration error: WORKER_URL not set"
            )

        logger.info(f"🔐 Verifying OIDC token with audience: {expected_audience}")

        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            expected_audience
        )

        # Verify that the token is from the correct Cloud Tasks service account
        expected_sa = "scheduler-trigger@cloud-functions-474716.iam.gserviceaccount.com"
        token_email = id_info.get("email")

        if token_email != expected_sa:
            logger.warning(f"🚨 SECURITY: Unauthorized service account: {token_email} (expected: {expected_sa})")
            raise HTTPException(
                status_code=403,
                detail=f"Unauthorized service account: {token_email}. Only Cloud Tasks service account can invoke this endpoint."
            )

        logger.info(f"✅ OIDC token verified successfully from: {token_email}")

    except ValueError as e:
        logger.error(f"🚨 SECURITY: Invalid OIDC token: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid OIDC token: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"🚨 SECURITY: Token verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail=f"Token verification failed: {str(e)}"
        )

    logger.info("=" * 60)
    logger.info("Task received from Cloud Tasks")

    # ============================================================
    # DEBUG: Capturar request body crudo ANTES de procesar
    # ============================================================
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")

        logger.info(f"📦 Raw request body length: {len(body_str)} bytes")
        logger.info(f"📦 Raw request body (first 500 chars): {body_str[:500]}")

        import json
        task_data = json.loads(body_str)

        logger.info(f"📋 Parsed JSON keys: {list(task_data.keys())}")
        logger.info(f"📋 Total fields in payload: {len(task_data)}")

        if "user_credentials" in task_data:
            logger.info(f"✅ user_credentials FOUND in payload")
            creds = task_data["user_credentials"]
            logger.info(f"   - Keys in user_credentials: {list(creds.keys()) if isinstance(creds, dict) else 'NOT A DICT'}")
            if isinstance(creds, dict) and "access_token" in creds:
                token = creds["access_token"]
                logger.info(f"   - access_token length: {len(token)}")
                logger.info(f"   - access_token prefix: {token[:20]}...")
        else:
            logger.info("❌ user_credentials NOT FOUND in payload")

        if "access_token" in task_data:
            logger.info(f"⚠️  DEPRECATED access_token field found (should be in user_credentials)")

    except Exception as debug_e:
        logger.error(f"DEBUG logging failed: {debug_e}")
    # ============================================================

    try:
        payload = await request.json()
        task = TaskPayload(**payload)

        logger.info(f"🔧 TaskPayload deserialized successfully")
        logger.info(f"   - task.user_credentials: {task.user_credentials is not None}")
        if task.user_credentials:
            logger.info(f"   - task.user_credentials.email: {task.user_credentials.email}")
    except Exception as e:
        logger.error(f"Invalid task payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")

    # ============================================================
    # NUEVO: Determinar qué credenciales usar
    # ============================================================

    if task.user_credentials and task.user_credentials.access_token:
        # Manual job with user credentials
        user_email = task.user_credentials.email
        access_token = task.user_credentials.access_token
        scope = task.user_credentials.scope

        logger.info(f"🔐 Using USER OAuth credentials")
        logger.info(f"   User: {user_email}")

        # Mask token for logging (don't log full token)
        masked_token = mask_access_token(access_token)
        logger.info(f"   Access token: {masked_token}")
        logger.info(f"   Scope: {scope}")

        # Create OAuth credentials from user's access token
        credentials = get_user_credentials(access_token, scope)

        logger.info(f"   ✅ User OAuth credentials created")

    else:
        # Scheduled job with service account credentials
        logger.info("🔧 Using SERVICE ACCOUNT credentials (scheduled job)")
        logger.info("   ⚠️  No user credentials provided")

        credentials = get_credentials()

    # ============================================================
    # FIN NUEVO
    # ============================================================
    
    # Process specific job or all active jobs
    if task.job_id:
        job_config = load_job_config(task.job_id)
        if not job_config:
            raise HTTPException(status_code=404, detail=f"Job '{task.job_id}' not found or inactive")
        
        if task.execution_id:
            try:
                logger.info(f"🔄 ATTEMPTING status update to 'processing' for {task.execution_id}")
                logger.info(f"🔍 Executions manager type: {type(executions_manager)}, Table: {executions_manager.table_name if hasattr(executions_manager, 'table_name') else 'unknown'}")
                logger.info(f"🔍 Filter: id={task.execution_id}, Updates: {{'status': 'processing'}}")

                # DEBUG: Verify if execution exists in Supabase before update
                if executions_manager.use_supabase:
                    try:
                        existing = executions_manager.supabase_client.table("job_executions").select("*").eq("id", task.execution_id).execute()
                        logger.info(f"🔍 EXECUTION RECORD QUERY: Found {len(existing.data) if existing.data else 0} records with id={task.execution_id}")
                        if existing.data:
                            logger.info(f"🔍 EXECUTION RECORD DATA: {existing.data[0]}")
                        else:
                            logger.error(f"❌ EXECUTION RECORD NOT FOUND in Supabase for id={task.execution_id}")
                    except Exception as query_error:
                        logger.error(f"❌ QUERY ERROR: {query_error}")

                update_result = executions_manager.update("id", task.execution_id, {"status": "processing"})
                logger.info(f"✅ Status updated to 'processing' for {task.execution_id}. Result: {update_result}")

                # DEBUG: Verify the update worked
                if executions_manager.use_supabase and update_result > 0:
                    try:
                        updated = executions_manager.supabase_client.table("job_executions").select("*").eq("id", task.execution_id).execute()
                        if updated.data:
                            logger.info(f"🔍 VERIFIED UPDATE: New status is '{updated.data[0].get('status', 'unknown')}'")
                    except Exception as verify_error:
                        logger.error(f"❌ VERIFY ERROR: {verify_error}")

            except Exception as e:
                logger.error(f"❌ FAILED to update status to 'processing' for {task.execution_id}: {e}", exc_info=True)
                logger.error(f"executions_manager type: {type(executions_manager)}")
                logger.error(f"executions_manager table: {executions_manager.table_name if hasattr(executions_manager, 'table_name') else 'unknown'}")

        try:
            result = process_job(job_config, task.folder_id, credentials)
            
            if task.execution_id:
                final_status = "completed" if result.get("status") == "success" else "failed"
                final_details = f"Processed {result.get('stats', {}).get('files_processed', 0)} files, Renamed {result.get('stats', {}).get('files_renamed', 0)} files. Folder: {task.folder_id}"

                logger.info(f"🔄 ATTEMPTING status update to '{final_status}' for {task.execution_id}")
                logger.info(f"📊 Stats: {result.get('stats', {})}")

                try:
                    update_result = executions_manager.update("id", task.execution_id, {
                        "status": final_status,
                        "details": final_details,
                        "stats": result.get('stats', {})
                    })
                    logger.info(f"✅ Status updated to '{final_status}' for {task.execution_id}. Result: {update_result}")
                except Exception as e:
                    logger.error(f"❌ FAILED to update status to '{final_status}' for {task.execution_id}: {e}", exc_info=True)

            return result
        except Exception as e:
            logger.error(f"Error in process_job: {e}")
            if task.execution_id:
                executions_manager.update("id", task.execution_id, {"status": "failed", "details": str(e)})
            raise HTTPException(status_code=500, detail=str(e))
    
    else:
        # Run all active scheduled jobs
        active_jobs = get_all_active_jobs()
        scheduled_jobs = [j for j in active_jobs if j.get("trigger_type") == "scheduled"]
        
        results = []
        for job in scheduled_jobs:
            result = process_job(job, credentials=credentials)
            results.append(result)
        
        return {
            "status": "success",
            "jobs_processed": len(results),
            "results": results
        }




@app.post("/run-job")
async def run_job(request: JobRunRequest):
    """
    Run a specific job by ID.
    Ejecuta un job específico por ID.
    
    Useful for testing or manual triggers.
    """
    logger.info(f"Manual job run requested: {request.job_id}")
    
    job_config = load_job_config(request.job_id)
    if not job_config:
        raise HTTPException(status_code=404, detail=f"Job '{request.job_id}' not found or inactive")
    
    credentials = get_credentials()
    result = process_job(job_config, request.folder_id, credentials)
    
    return result


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting worker in development mode")
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)