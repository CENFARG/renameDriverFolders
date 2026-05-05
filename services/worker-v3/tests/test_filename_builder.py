"""
Test: Worker Filename Builder extraction (T2.7).

Verifies:
1. build_filename() with template and analysis fields
2. Case-insensitive variable substitution
3. Fallback when template is missing
4. Alias support (keywords → type, issuer, etc.)

:task: T2.7 - Extract Worker Filename Builder
:phase: RED (test written first)
"""

import pytest


class TestFilenameBuilder:
    """build_filename() generates filenames from analysis + template."""

    def test_filename_builder_module_exists(self):
        from filename_builder import build_filename
        assert build_filename is not None

    def test_build_filename_with_template(self):
        """Should substitute variables from analysis into template."""
        from filename_builder import build_filename

        analysis = {
            "algorithm_id": "factura",
            "date": "2025-03-15",
            "keywords": ["factura", "mercedes", "servicio"],
        }
        job_config = {
            "agent_config": {
                "filename_format": "{date}_{type}_{issuer}{ext}",
            }
        }

        result = build_filename("original.pdf", analysis, job_config)
        assert "2025-03-15" in result
        assert "factura" in result
        assert "mercedes" in result
        assert result.endswith(".pdf")

    def test_build_filename_case_insensitive(self):
        """Should handle {DATE}, {date}, {Date} equally."""
        from filename_builder import build_filename

        analysis = {"algorithm_id": "test", "date": "2025-06-01", "keywords": []}
        job_config = {
            "agent_config": {
                "filename_format": "{DATE}_{ALGORITHM_ID}{ext}",
            }
        }

        result = build_filename("doc.pdf", analysis, job_config)
        assert "2025-06-01" in result

    def test_build_filename_fallback_when_no_template(self):
        """Should use algorithm_id_date format when no template."""
        from filename_builder import build_filename

        analysis = {"algorithm_id": "recibo", "date": "2025-02-01"}
        job_config = {"agent_config": {}}

        result = build_filename("file.pdf", analysis, job_config)
        assert "recibo" in result
        assert "2025-02-01" in result
        assert result.endswith(".pdf")

    def test_build_filename_preserves_extension(self):
        """Should preserve original file extension."""
        from filename_builder import build_filename

        analysis = {"algorithm_id": "test", "date": "2025-01-01"}
        job_config = {"agent_config": {}}

        result = build_filename("document.xlsx", analysis, job_config)
        assert result.endswith(".xlsx")

    def test_build_filename_keywords_alias(self):
        """Should map keywords to type, issuer, concept aliases."""
        from filename_builder import build_filename

        analysis = {
            "algorithm_id": "factura",
            "date": "2025-03-15",
            "keywords": ["factura", "mercedes", "servicio"],
        }
        job_config = {
            "agent_config": {
                "filename_format": "{date}_{type}_{issuer}_{concept}{ext}",
            }
        }

        result = build_filename("file.pdf", analysis, job_config)
        assert "mercedes" in result
        assert "servicio" in result
