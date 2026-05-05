"""
AI Classifier — Agent response parsing for worker-v3.
=====================================================

Parses structured data from Agno agent responses.
Handles Pydantic v2, v1, dicts, JSON strings, and code blocks.

:created:   2026-05-05
:filename:  ai_classifier.py
:path:      services/worker-v3/src/ai_classifier.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

FALLBACK_RESPONSE = {
    "algorithm_id": "unknown",
    "date": "2025-01-01",
    "confidence": 0.0,
    "reasoning": "Unable to parse response - no .content attribute",
}


def parse_agent_response(response) -> Dict[str, Any]:
    """
    Parse Agno agent response to extract structured data.

    Agno returns a RunResponse with .content attribute.
    Content may be a Pydantic model, dict, or JSON string.

    Args:
        response: Agno RunResponse object.

    Returns:
        Dict with analysis fields (algorithm_id, date, confidence, reasoning).
    """
    logger.debug(f"Parsing agent response. Type: {type(response)}")

    if not hasattr(response, "content"):
        logger.error(f"No .content attribute. Type: {type(response)}")
        return FALLBACK_RESPONSE.copy()

    content = response.content
    logger.debug(f"Response has .content. Type: {type(content)}")

    # Pydantic v2: has model_dump()
    if hasattr(content, "model_dump") and callable(content.model_dump):
        result = content.model_dump()
        logger.debug(f"Converted Pydantic v2 model to dict")
        return result

    # Pydantic v1: has dict()
    if hasattr(content, "dict") and callable(content.dict):
        result = content.dict()
        logger.debug(f"Converted Pydantic v1 model to dict")
        return result

    # Already a dict
    if isinstance(content, dict):
        logger.debug("Content is already a dict")
        return content

    # String: try JSON parse
    if isinstance(content, str):
        return _parse_json_string(content)

    logger.error(f"Unable to parse response content. Type: {type(content)}")
    return FALLBACK_RESPONSE.copy()


def _parse_json_string(content: str) -> Dict[str, Any]:
    """Parse JSON from a string, handling markdown code blocks."""
    logger.warning(f"Content is string, attempting JSON parse: {content[:200]}...")

    text = content
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    try:
        result = json.loads(text.strip())
        logger.info(f"Successfully parsed JSON from string")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}. Content: {content[:500]}")
        return {
            "algorithm_id": "unknown",
            "date": "2025-01-01",
            "confidence": 0.0,
            "reasoning": f"JSON parse error: {str(e)[:100]}",
        }
