"""
Unit tests for DocumentClassification schema.

Tests Pydantic model validation for document classification.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from core_renombrador.schemas import DocumentClassification


class TestDocumentClassificationRequiredFields:
    """Tests for required field validation."""

    def test_all_required_fields_valid(self):
        """Test that a valid DocumentClassification can be created with all required fields."""
        data = {
            "algorithm_id": "estado_contable",
            "date": "2024-03-15",
            "confidence": 0.85,
            "reasoning": "Balance general de closing anual"
        }
        doc = DocumentClassification(**data)

        assert doc.algorithm_id == "estado_contable"
        assert doc.date == "2024-03-15"
        assert doc.confidence == 0.85
        assert doc.reasoning == "Balance general de closing anual"

    def test_missing_algorithm_id_raises_error(self):
        """Test that missing algorithm_id raises ValidationError."""
        data = {
            "date": "2024-03-15",
            "confidence": 0.85,
            "reasoning": "Test"
        }
        with pytest.raises(ValidationError) as exc_info:
            DocumentClassification(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("algorithm_id",) for e in errors)

    def test_missing_date_raises_error(self):
        """Test that missing date raises ValidationError."""
        data = {
            "algorithm_id": "recibo_sueldo",
            "confidence": 0.85,
            "reasoning": "Test"
        }
        with pytest.raises(ValidationError) as exc_info:
            DocumentClassification(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("date",) for e in errors)

    def test_missing_confidence_uses_default(self):
        """Test that missing confidence uses default value of 0.8."""
        data = {
            "algorithm_id": "factura",
            "date": "2024-03-15",
            "reasoning": "Test"
        }
        doc = DocumentClassification(**data)
        assert doc.confidence == 0.8

    def test_missing_reasoning_raises_error(self):
        """Test that missing reasoning raises ValidationError."""
        data = {
            "algorithm_id": "resumen_bancario",
            "date": "2024-03-15",
            "confidence": 0.9
        }
        with pytest.raises(ValidationError) as exc_info:
            DocumentClassification(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("reasoning",) for e in errors)


class TestAlgorithmIdLiteral:
    """Tests for algorithm_id Literal validation."""

    def test_all_valid_algorithm_ids(self):
        """Test that all 10 valid algorithm IDs are accepted."""
        valid_ids = [
            "estado_contable",
            "recibo_sueldo",
            "resumen_bancario",
            "factura",
            "prestamo",
            "impuesto",
            "seguro",
            "legal",
            "doc_interna",
            "constancia"
        ]

        for alg_id in valid_ids:
            data = {
                "algorithm_id": alg_id,
                "date": "2024-03-15",
                "confidence": 0.8,
                "reasoning": "Test"
            }
            doc = DocumentClassification(**data)
            assert doc.algorithm_id == alg_id

    def test_invalid_algorithm_id_raises_error(self):
        """Test that invalid algorithm_id raises ValidationError."""
        data = {
            "algorithm_id": "invalid_algorithm",
            "date": "2024-03-15",
            "confidence": 0.8,
            "reasoning": "Test"
        }
        with pytest.raises(ValidationError) as exc_info:
            DocumentClassification(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("algorithm_id",) for e in errors)


class TestConfidenceValidation:
    """Tests for confidence field validation."""

    def test_confidence_minimum_boundary(self):
        """Test that confidence accepts 0.0 as minimum."""
        data = {
            "algorithm_id": "estado_contable",
            "date": "2024-03-15",
            "confidence": 0.0,
            "reasoning": "Test"
        }
        doc = DocumentClassification(**data)
        assert doc.confidence == 0.0

    def test_confidence_maximum_boundary(self):
        """Test that confidence accepts 1.0 as maximum."""
        data = {
            "algorithm_id": "estado_contable",
            "date": "2024-03-15",
            "confidence": 1.0,
            "reasoning": "Test"
        }
        doc = DocumentClassification(**data)
        assert doc.confidence == 1.0

    def test_confidence_below_minimum_raises_error(self):
        """Test that confidence < 0.0 raises ValidationError."""
        data = {
            "algorithm_id": "estado_contable",
            "date": "2024-03-15",
            "confidence": -0.1,
            "reasoning": "Test"
        }
        with pytest.raises(ValidationError) as exc_info:
            DocumentClassification(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("confidence",) for e in errors)

    def test_confidence_above_maximum_raises_error(self):
        """Test that confidence > 1.0 raises ValidationError."""
        data = {
            "algorithm_id": "estado_contable",
            "date": "2024-03-15",
            "confidence": 1.1,
            "reasoning": "Test"
        }
        with pytest.raises(ValidationError) as exc_info:
            DocumentClassification(**data)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("confidence",) for e in errors)


class TestOptionalFields:
    """Tests for optional algorithm-specific fields."""

    def test_estado_contable_fields(self):
        """Test estado_contable optional fields."""
        data = {
            "algorithm_id": "estado_contable",
            "date": "2024-03-15",
            "confidence": 0.9,
            "reasoning": "Balance general",
            "company": "Mi Empresa S.A.",
            "fiscal_year": "2024",
            "type": "balance_general"
        }
        doc = DocumentClassification(**data)

        assert doc.company == "Mi Empresa S.A."
        assert doc.fiscal_year == "2024"
        assert doc.type == "balance_general"

    def test_recibo_sueldo_fields(self):
        """Test recibo_sueldo optional fields."""
        data = {
            "algorithm_id": "recibo_sueldo",
            "date": "2024-03-15",
            "confidence": 0.95,
            "reasoning": "Recibo de sueldo mensual",
            "employee": "Juan Pérez",
            "employer": "Empresa S.A.",
            "period": "2024-03",
            "net_amount": 450000.50
        }
        doc = DocumentClassification(**data)

        assert doc.employee == "Juan Pérez"
        assert doc.employer == "Empresa S.A."
        assert doc.period == "2024-03"
        assert doc.net_amount == 450000.50

    def test_resumen_bancario_fields(self):
        """Test resumen_bancario optional fields."""
        data = {
            "algorithm_id": "resumen_bancario",
            "date": "2024-03-15",
            "confidence": 0.9,
            "reasoning": "Resumen mensual",
            "bank": "Galicia",
            "account_type": "caja_ahorro",
            "account_last4": "1234"
        }
        doc = DocumentClassification(**data)

        assert doc.bank == "Galicia"
        assert doc.account_type == "caja_ahorro"
        assert doc.account_last4 == "1234"

    def test_factura_fields(self):
        """Test factura optional fields."""
        data = {
            "algorithm_id": "factura",
            "date": "2024-03-15",
            "confidence": 0.88,
            "reasoning": "Factura de servicios",
            "issuer": "Proveedor S.A.",
            "type": "A",
            "number": "0001-00012345",
            "amount": 125000.00,
            "detail": "Servicios profesionales"
        }
        doc = DocumentClassification(**data)

        assert doc.issuer == "Proveedor S.A."
        assert doc.type == "A"
        assert doc.number == "0001-00012345"
        assert doc.amount == 125000.00
        assert doc.detail == "Servicios profesionales"

    def test_prestamo_fields(self):
        """Test prestamo optional fields."""
        data = {
            "algorithm_id": "prestamo",
            "date": "2024-03-15",
            "confidence": 0.9,
            "reasoning": "Cuota de préstamo hipotecario",
            "bank": "Banco Nación",
            "loan_type": "hipotecario",
            "installment": "12/60",
            "detail": "Cuota mensual"
        }
        doc = DocumentClassification(**data)

        assert doc.bank == "Banco Nación"
        assert doc.loan_type == "hipotecario"
        assert doc.installment == "12/60"
        assert doc.detail == "Cuota mensual"

    def test_impuesto_fields(self):
        """Test impuesto optional fields."""
        data = {
            "algorithm_id": "impuesto",
            "date": "2024-03-15",
            "confidence": 0.92,
            "reasoning": "Pago de impuesto",
            "organism": "AFIP",
            "tax_type": "ganancias",
            "period": "2024-03"
        }
        doc = DocumentClassification(**data)

        assert doc.organism == "AFIP"
        assert doc.tax_type == "ganancias"
        assert doc.period == "2024-03"

    def test_seguro_fields(self):
        """Test seguro optional fields."""
        data = {
            "algorithm_id": "seguro",
            "date": "2024-03-15",
            "confidence": 0.89,
            "reasoning": "Póliza de seguro",
            "insurer": "La Caja",
            "insurance_type": "automotor",
            "policy_number": "12345678"
        }
        doc = DocumentClassification(**data)

        assert doc.insurer == "La Caja"
        assert doc.insurance_type == "automotor"
        assert doc.policy_number == "12345678"

    def test_legal_fields(self):
        """Test legal optional fields."""
        data = {
            "algorithm_id": "legal",
            "date": "2024-03-15",
            "confidence": 0.85,
            "reasoning": "Contrato de servicios",
            "doc_type": "contrato",
            "parties": "Empresa S.A. y Cliente S.R.L.",
            "concept": "Prestación de servicios profesionales"
        }
        doc = DocumentClassification(**data)

        assert doc.doc_type == "contrato"
        assert doc.parties == "Empresa S.A. y Cliente S.R.L."
        assert doc.concept == "Prestación de servicios profesionales"

    def test_doc_interna_fields(self):
        """Test doc_interna optional fields."""
        data = {
            "algorithm_id": "doc_interna",
            "date": "2024-03-15",
            "confidence": 0.87,
            "reasoning": "Documento interno de trabajo",
            "client": "Cliente S.A.",
            "work_type": "asesoramiento",
            "detail": "Reunión inicial"
        }
        doc = DocumentClassification(**data)

        assert doc.client == "Cliente S.A."
        assert doc.work_type == "asesoramiento"
        assert doc.detail == "Reunión inicial"

    def test_constancia_fields(self):
        """Test constancia optional fields."""
        data = {
            "algorithm_id": "constancia",
            "date": "2024-03-15",
            "confidence": 0.91,
            "reasoning": "Constancia de inscripción",
            "type": "inscripcion",
            "organism": "AFIP",
            "entity": "Juan Pérez"
        }
        doc = DocumentClassification(**data)

        assert doc.type == "inscripcion"
        assert doc.organism == "AFIP"
        assert doc.entity == "Juan Pérez"

    def test_all_optional_fields_omitted(self):
        """Test that all optional fields can be omitted."""
        data = {
            "algorithm_id": "estado_contable",
            "date": "2024-03-15",
            "confidence": 0.8,
            "reasoning": "Test"
        }
        doc = DocumentClassification(**data)

        assert doc.company is None
        assert doc.fiscal_year is None
        assert doc.type is None
        assert doc.employee is None
        assert doc.employer is None
        assert doc.period is None
        assert doc.net_amount is None
        assert doc.bank is None
        assert doc.account_type is None
        assert doc.account_last4 is None
        assert doc.issuer is None
        assert doc.number is None
        assert doc.amount is None
        assert doc.detail is None
        assert doc.loan_type is None
        assert doc.installment is None
        assert doc.organism is None
        assert doc.tax_type is None
        assert doc.insurer is None
        assert doc.insurance_type is None
        assert doc.policy_number is None
        assert doc.doc_type is None
        assert doc.parties is None
        assert doc.concept is None
        assert doc.client is None
        assert doc.work_type is None
        assert doc.entity is None


class TestDateField:
    """Tests for date field validation."""

    def test_date_format_yyyy_mm_dd(self):
        """Test that dates in YYYY-MM-DD format are accepted."""
        valid_dates = [
            "2024-03-15",
            "2023-12-31",
            "2025-01-01"
        ]

        for date_str in valid_dates:
            data = {
                "algorithm_id": "factura",
                "date": date_str,
                "confidence": 0.8,
                "reasoning": "Test"
            }
            doc = DocumentClassification(**data)
            assert doc.date == date_str

    def test_date_accepts_any_string(self):
        """Test that date field accepts any string (format validation is AI responsibility)."""
        # Pydantic doesn't validate date format - AI must extract in correct format
        data = {
            "algorithm_id": "factura",
            "date": "15/03/2024",  # Wrong format but Pydantic accepts it as str
            "confidence": 0.8,
            "reasoning": "Test"
        }
        doc = DocumentClassification(**data)
        assert doc.date == "15/03/2024"  # Schema accepts any string


class TestSerialization:
    """Tests for JSON serialization."""

    def test_serialize_to_json(self):
        """Test that DocumentClassification can be serialized to JSON."""
        data = {
            "algorithm_id": "factura",
            "date": "2024-03-15",
            "confidence": 0.88,
            "reasoning": "Factura de servicios",
            "issuer": "Proveedor S.A.",
            "type": "A",
            "amount": 125000.00
        }
        doc = DocumentClassification(**data)

        json_dict = doc.model_dump()

        assert json_dict["algorithm_id"] == "factura"
        assert json_dict["date"] == "2024-03-15"
        assert json_dict["confidence"] == 0.88
        assert json_dict["reasoning"] == "Factura de servicios"
        assert json_dict["issuer"] == "Proveedor S.A."
        assert json_dict["type"] == "A"
        assert json_dict["amount"] == 125000.00

    def test_serialize_to_json_exclude_none(self):
        """Test serialization with exclude_none."""
        data = {
            "algorithm_id": "factura",
            "date": "2024-03-15",
            "confidence": 0.8,
            "reasoning": "Test"
        }
        doc = DocumentClassification(**data)

        json_dict = doc.model_dump(exclude_none=True)

        # Should not include optional fields that are None
        assert "company" not in json_dict
        assert "employee" not in json_dict
        assert "bank" not in json_dict
        assert "issuer" not in json_dict
