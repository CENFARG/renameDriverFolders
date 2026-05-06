"""
Job Processor — Core job orchestration for worker-v3.
=====================================================

Orchestrates file processing: loads job config, finds folders,
processes files with AI analysis, and renames them.

:created:   2026-05-05
:filename:  job_processor.py
:path:      services/worker-v3/src/job_processor.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
from typing import Any, Dict, Optional

from google.cloud import storage
from googleapiclient.discovery import build

from ai_classifier import parse_agent_response
from drive_operations import download_file, find_target_folders, rename_file
from filename_builder import build_filename

logger = logging.getLogger(__name__)

# These are injected by main.py during initialization
agent_factory = None
content_extractor = None


def process_job(
    job_config: Dict[str, Any],
    folder_id: Optional[str] = None,
    credentials=None,
) -> Dict[str, Any]:
    """
    Process a single job.

    Args:
        job_config: Job configuration from database.
        folder_id: Override folder ID (manual mode).
        credentials: Google Cloud credentials.

    Returns:
        Dict with status, job_id, job_name, stats or error.
    """
    job_id = job_config.get("id")
    job_name = job_config.get("name")

    logger.info(f"Starting job '{job_name}' (ID: {job_id})")

    try:
        target_folder_id = folder_id or job_config.get("source_folder_id")

        logger.info(f"Target folder ID: {target_folder_id}")

        if not target_folder_id or target_folder_id == "DYNAMIC":
            raise ValueError(f"No folder_id provided for job '{job_id}'")

        agent = agent_factory.create_agent_from_job_config(job_config)
        logger.info(f"Agent created for job '{job_name}'")

        drive_service = build("drive", "v3", credentials=credentials)
        storage.Client(credentials=credentials)

        stats = {"files_processed": 0, "files_renamed": 0, "errors": 0}

        if folder_id:
            # Manual mode: process all files in given folder
            logger.info(f"MANUAL MODE: Processing all files in: {target_folder_id}")
            folders_to_process = [target_folder_id]
        else:
            # Scheduled mode: use target_folder_names from config
            target_folder_names = job_config.get("target_folder_names", ["*"])
            logger.info(f"SCHEDULED MODE: target_folder_names: {target_folder_names}")

            if target_folder_names == ["*"]:
                folders_to_process = [target_folder_id]
            else:
                folders_to_process = find_target_folders(
                    drive_service, target_folder_id, target_folder_names
                )
                logger.info(f"Found {len(folders_to_process)} folders")

        for folder in folders_to_process:
            folder_stats = process_folder_files(
                drive_service=drive_service,
                folder_id=folder,
                agent=agent,
                job_config=job_config,
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

        return {"status": "success", "job_id": job_id, "job_name": job_name, "stats": stats}

    except Exception as e:
        logger.error(f"Error processing job '{job_name}': {e}", exc_info=True)
        return {"status": "error", "job_id": job_id, "job_name": job_name, "error": str(e)}


def process_folder_files(
    drive_service,
    folder_id: str,
    agent,
    job_config: Dict[str, Any],
) -> Dict[str, int]:
    """
    Process all files in a folder.

    Lists files, skips already processed ones (DOCPROCESADO, index.html),
    downloads content, runs AI analysis, and renames files.

    Args:
        drive_service: Authenticated Drive API service.
        folder_id: Folder to process.
        agent: AI agent for classification.
        job_config: Job configuration with prompt template.

    Returns:
        Stats dict: files_processed, files_renamed, errors.
    """
    stats = {"files_processed": 0, "files_renamed": 0, "errors": 0}

    try:
        query = (
            f"'{folder_id}' in parents and trashed=false "
            f"and mimeType != 'application/vnd.google-apps.folder'"
        )
        response = drive_service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        files = response.get("files", [])
        logger.info(f"Found {len(files)} files in folder {folder_id}")

        if not files:
            return stats

        for file in files:
            stats["files_processed"] += 1

            if "DOCPROCESADO" in file["name"] or file["name"] == "index.html":
                continue

            try:
                file_bytes = download_file(drive_service, file["id"])
                content = content_extractor.get_content(file["name"], file_bytes)
                logger.info(f"Extracted {len(content)} chars for {file['name']}")

                prompt_template = job_config["agent_config"]["prompt_template"]
                prompt = prompt_template.replace("{original_filename}", file["name"])
                prompt = prompt.replace("{file_content}", content[:8000])

                logger.info(f"Sending prompt for {file['name']} ({len(prompt)} chars)")
                response = agent.run(prompt)

                analysis = parse_agent_response(response)
                logger.info(f"Analysis for {file['name']}: {analysis}")

                new_name = build_filename(file["name"], analysis, job_config)
                rename_file(drive_service, file["id"], new_name)
                stats["files_renamed"] += 1
                logger.info(f"Renamed: {file['name']} -> {new_name}")

            except Exception as e:
                logger.error(f"Error processing {file['name']}: {e}", exc_info=True)
                stats["errors"] += 1

    except Exception as e:
        logger.error(f"Error listing files in folder {folder_id}: {e}")
        stats["errors"] += 1

    return stats
