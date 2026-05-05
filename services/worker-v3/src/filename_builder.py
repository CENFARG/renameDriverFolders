"""
Filename Builder — Generates filenames from AI analysis.
========================================================

Builds new filenames using templates with variable substitution.
Supports case-insensitive variables and keyword aliases.

:created:   2026-05-05
:filename:  filename_builder.py
:path:      services/worker-v3/src/filename_builder.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging
import os
from collections import defaultdict
from typing import Any, Dict

logger = logging.getLogger(__name__)


def build_filename(
    original_name: str,
    analysis: Dict[str, Any],
    job_config: Dict[str, Any],
) -> str:
    """
    Build new filename from analysis with alias support and case-insensitivity.

    Template variables: {date}, {type}, {issuer}, {entity}, {concept},
    {keywords}, {ext}, {original_filename}, plus all analysis fields.

    Args:
        original_name: Original filename with extension.
        analysis: Parsed AI analysis (algorithm_id, date, keywords, etc.).
        job_config: Job configuration with agent_config.filename_format.

    Returns:
        New filename string.
    """
    ext = os.path.splitext(original_name)[1]
    template = job_config.get("agent_config", {}).get("filename_format")

    if not template:
        algorithm_id = analysis.get("algorithm_id", "unknown")
        date = analysis.get("date", "unknown")
        return f"{algorithm_id}_{date}{ext}"

    # Raw variables with lowercase keys
    raw_vars = {k.lower(): v for k, v in analysis.items()}

    # Build keywords string
    keywords_list = analysis.get("keywords", [])
    if not isinstance(keywords_list, list):
        keywords_list = [str(keywords_list)]
    keywords_str = "_".join(keywords_list) if keywords_list else "doc"

    # Standard variables
    template_vars = {
        "date": analysis.get("date") or raw_vars.get("fecha") or "2025-01-01",
        "keywords": keywords_str,
        "ext": ext,
        "original_filename": os.path.splitext(original_name)[0],
    }

    # Keyword aliases: [type, issuer/entity, concept/detail]
    if len(keywords_list) >= 1:
        template_vars["type"] = keywords_list[0]
    if len(keywords_list) >= 2:
        template_vars["issuer"] = keywords_list[1]
        template_vars["entity"] = keywords_list[1]
    if len(keywords_list) >= 3:
        template_vars["brief_detail"] = keywords_list[2]
        template_vars["concept"] = keywords_list[2]

    # Merge all analysis fields
    for key, value in analysis.items():
        low_key = key.lower()
        if low_key not in template_vars:
            if isinstance(value, list):
                template_vars[low_key] = "_".join(map(str, value))
            else:
                template_vars[low_key] = value

    # Case-insensitive mapper
    class CaseInsensitiveDict(defaultdict):
        def __missing__(self, key):
            return self.get(key.lower(), "unknown")

    safe_vars = CaseInsensitiveDict(lambda: "unknown")
    for k, v in template_vars.items():
        safe_vars[k.lower()] = v
        safe_vars[k] = v

    try:
        new_name = template.format_map(safe_vars)
        logger.info(f"Filename generated: {new_name} using template: {template}")
    except Exception as e:
        logger.error(f"Error formatting filename with template '{template}': {e}")
        new_name = f"{template_vars['date']}_{template_vars['keywords']}{ext}"

    return new_name
