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
from google.cloud import storage
from googleapiclient.discovery import build

# Core modules
from core_renombrador.config_manager import ConfigManager
from core_renombrador.logger_manager import LoggerManager
from core_renombrador.database_manager import DatabaseManager
from core_renombrador.file_manager import FileManager
from core_renombrador.agent_factory import AgentFactory, create_document_agent
from core_renombrador.drive_handler import DriveHandler
from core_renombrador.content_extractor import ContentExtractor

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

class TaskPayload(BaseModel):
    """
    Payload for Cloud Tasks.
    """
    job_id: Optional[str] = None
    folder_id: Optional[str] = None
    user_token: Optional[str] = None
    trigger_type: str = "scheduled"  # "scheduled" or "manual"


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
        
        # Initialize Drive service
        drive_service = build("drive", "v3", credentials=credentials)
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


@app.post("/run-task")
async def run_task(request: Request):
    """
    Main endpoint triggered by Cloud Tasks.
    Punto de entrada principal disparado por Cloud Tasks.
    
    Processes jobs based on payload:
    - If job_id provided: runs that specific job
    - If no job_id: runs all active scheduled jobs
    """
    logger.info("Task received from Cloud Tasks")
    
    try:
        payload = await request.json()
        task = TaskPayload(**payload)
    except Exception as e:
        logger.error(f"Invalid task payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    
    credentials = get_credentials()
    
    # Process specific job or all active jobs
    if task.job_id:
        job_config = load_job_config(task.job_id)
        if not job_config:
            raise HTTPException(status_code=404, detail=f"Job '{task.job_id}' not found or inactive")
        
        result = process_job(job_config, task.folder_id, credentials)
        return result
    
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