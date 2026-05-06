"""
Audit Routes — Audit logs and execution export.
================================================

Provides audit log listing and execution log export
as downloadable text files.

:created:   2026-05-06
:filename:  audit.py
:path:      services/api-server-v3/src/routes/audit.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["audit"])

# Injected by main.py
executions_manager = None


@router.get("/audit-logs")
async def get_audit_logs(limit: int = 100, user: dict = None):
    """Get audit logs for system activity."""
    if limit > 1000:
        limit = 1000

    try:
        all_executions = executions_manager.find_all()
        all_executions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        limited = all_executions[:limit]

        audit_logs = []
        for exe in limited:
            audit_logs.append({
                "id": exe.get("id"),
                "timestamp": exe.get("timestamp"),
                "user_email": exe.get("user_email"),
                "user_name": exe.get("user_name"),
                "action": "job_submitted",
                "status": exe.get("status", "submitted"),
                "details": f"Folder: {exe.get('folder_id')} | Type: {exe.get('job_type')}",
            })

        logger.info(f"Audit logs requested, limit={limit}, returned {len(audit_logs)}")
        return {"status": "success", "logs": audit_logs, "total": len(audit_logs)}
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit logs: {str(e)}")


@router.get("/executions/{execution_id}/logs")
async def export_execution_logs(execution_id: str, user: dict = None):
    """Export execution logs as a downloadable TXT file."""
    logger.info(f"Requesting logs for execution {execution_id}")

    try:
        executions = executions_manager.find("id", execution_id)
        if not executions:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        execution = executions[0]

        if user and execution.get("user_email") != user.get("email"):
            logger.warning(f"User {user.get('email')} attempted to access logs of execution owned by {execution.get('user_email')}")
            raise HTTPException(status_code=403, detail="You can only export your own executions")

        log_content = _build_log_content(execution)

        return Response(
            content=log_content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=logs_{execution_id}.txt"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting logs for {execution_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export logs: {str(e)}")


def _build_log_content(execution: dict) -> str:
    """Build formatted TXT log content from execution record."""
    lines = []
    lines.append("=" * 80)
    lines.append("LOG DE EJECUCION - RENAME DRIVER FOLDERS")
    lines.append("=" * 80)
    lines.append(f"ID de Ejecucion: {execution['id']}")
    lines.append(f"Fecha: {execution.get('timestamp', 'N/A')}")
    lines.append(f"Usuario: {execution.get('user_email', 'N/A')}")
    lines.append(f"Folder ID: {execution.get('folder_id', 'N/A')}")
    lines.append(f"Status: {execution.get('status', 'N/A')}")
    lines.append("")

    lines.append("-" * 80)
    lines.append("DETALLES")
    lines.append("-" * 80)
    lines.append(execution.get("details", "Sin detalles disponibles"))
    lines.append("")

    stats = execution.get("stats", {})
    if stats:
        lines.append("-" * 80)
        lines.append("ESTADISTICAS")
        lines.append("-" * 80)
        lines.append(f"Archivos Procesados: {stats.get('files_processed', 0)}")
        lines.append(f"Archivos Renombrados: {stats.get('files_renamed', 0)}")
        lines.append(f"Errores: {stats.get('errors', 0)}")
        lines.append("")

    lines.append("-" * 80)
    lines.append("TIMESTAMPS")
    lines.append("-" * 80)
    lines.append(f"Created: {execution.get('timestamp', 'N/A')}")
    lines.append(f"Submitted: {execution.get('submitted_at', 'N/A')}")
    lines.append("")

    lines.append("=" * 80)
    lines.append("FIN DEL LOG")
    lines.append("=" * 80)

    return "\n".join(lines)
