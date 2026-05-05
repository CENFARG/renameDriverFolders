"""
Pydantic schemas for document classification and extraction.

This module defines structured output schemas for Agno agents following
best practices:
- Clear field descriptions for AI guidance
- Proper type hints and validation
- Comprehensive docstrings
- Optional fields for uncertain data

According to Agno documentation (docs.agno.com), output_schema should be a
Pydantic BaseModel class, not a dict. The agent converts this to JSON schema
and passes it to the model's structured output API.

Example:
    agent = Agent(
        model=OpenAIResponses(id="gpt-5.2"),
        output_schema=DocumentClassification,
    )
    response = agent.run("Analyze this document...")
    # response.content is a DocumentClassification object
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class DocumentClassification(BaseModel):
    """
    Schema for document classification and metadata extraction.

    This is the MAIN schema used by job-manual-auto-classify. It includes
    all possible fields from the 10 supported algorithms. The AI will:
    1. Classify which algorithm matches the document
    2. Extract relevant fields based on the algorithm's requirements
    3. Return a DocumentClassification object with all applicable fields

    The Worker then uses algorithm_id to determine which filename format
    to apply, and the extracted fields to populate the template.

    Attributes:
        algorithm_id: Which of the 10 algorithms matched this document
        date: Document date (YYYY-MM-DD format)
        confidence: AI confidence score (0.0 to 1.0)
        reasoning: AI explanation of the classification

    Algorithm-specific fields (only populated when algorithm_id matches):
        - estado_contable: company, fiscal_year, type
        - recibo_sueldo: employee, employer, period, net_amount
        - resumen_bancario: bank, account_type, period
        - factura: issuer, type, number, amount
        - prestamo: bank, loan_type, installment
        - impuesto: organism, tax_type, period
        - seguro: insurer, insurance_type, policy_number
        - legal: doc_type, parties, concept
        - doc_interna: client, work_type, detail
        - constancia: type, organism, entity
    """

    # === CORE FIELDS (required by all algorithms) ===
    algorithm_id: Literal[
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
    ] = Field(
        description="ID of the algorithm that matched this document. Must be one of the 10 supported algorithms."
    )

    date: str = Field(
        description="Document date in YYYY-MM-DD format. If uncertain, AI should extract the most likely date from the document content."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=0.8,
        description="AI confidence score from 0.0 to 1.0. Higher means more certain about the classification."
    )

    reasoning: str = Field(
        description="Brief explanation of why this algorithm was chosen and what was found in the document."
    )

    # === ESTADO CONTABLE FIELDS ===
    company: Optional[str] = Field(
        default=None,
        description="Company name (for estado_contable)"
    )
    fiscal_year: Optional[str] = Field(
        default=None,
        description="Fiscal year (for estado_contable)"
    )
    type: Optional[str] = Field(
        default=None,
        description="Document type (for estado_contable, factura, constancia)"
    )

    # === RECIBO SUELDO FIELDS ===
    employee: Optional[str] = Field(
        default=None,
        description="Employee name (for recibo_sueldo)"
    )
    employer: Optional[str] = Field(
        default=None,
        description="Employer name (for recibo_sueldo)"
    )
    period: Optional[str] = Field(
        default=None,
        description="Pay period (for recibo_sueldo, resumen_bancario, impuesto)"
    )
    net_amount: Optional[float] = Field(
        default=None,
        description="Net amount paid (for recibo_sueldo)"
    )

    # === RESUMEN BANCARIO FIELDS ===
    bank: Optional[str] = Field(
        default=None,
        description="Bank name (for resumen_bancario, prestamo)"
    )
    account_type: Optional[str] = Field(
        default=None,
        description="Account type (for resumen_bancario)"
    )
    account_last4: Optional[str] = Field(
        default=None,
        description="Last 4 digits of account (for resumen_bancario)"
    )

    # === FACTURA FIELDS ===
    issuer: Optional[str] = Field(
        default=None,
        description="Issuer name (for factura, constancia)"
    )
    number: Optional[str] = Field(
        default=None,
        description="Invoice/document number (for factura)"
    )
    amount: Optional[float] = Field(
        default=None,
        description="Amount (for factura)"
    )
    detail: Optional[str] = Field(
        default=None,
        description="Brief description or concept (for factura, prestamo, legal, doc_interna)"
    )

    # === PRÉSTAMO FIELDS ===
    loan_type: Optional[str] = Field(
        default=None,
        description="Type of loan (for prestamo)"
    )
    installment: Optional[str] = Field(
        default=None,
        description="Installment number (for prestamo)"
    )

    # === IMPUESTO FIELDS ===
    organism: Optional[str] = Field(
        default=None,
        description="Tax authority (AFIP/ARCA/IIBB) (for impuesto, constancia)"
    )
    tax_type: Optional[str] = Field(
        default=None,
        description="Tax or form type (for impuesto)"
    )

    # === SEGURO FIELDS ===
    insurer: Optional[str] = Field(
        default=None,
        description="Insurance company name (for seguro)"
    )
    insurance_type: Optional[str] = Field(
        default=None,
        description="Type of insurance (for seguro)"
    )
    policy_number: Optional[str] = Field(
        default=None,
        description="Policy number (for seguro)"
    )

    # === LEGAL FIELDS ===
    doc_type: Optional[str] = Field(
        default=None,
        description="Type of legal document (for legal)"
    )
    parties: Optional[str] = Field(
        default=None,
        description="Parties involved (for legal)"
    )
    concept: Optional[str] = Field(
        default=None,
        description="Purpose or object of agreement (for legal)"
    )

    # === DOCUMENTO INTERNO FIELDS ===
    client: Optional[str] = Field(
        default=None,
        description="Client name (for doc_interna)"
    )
    work_type: Optional[str] = Field(
        default=None,
        description="Type of work performed (for doc_interna)"
    )

    # === CONSTANCIA FIELDS ===
    entity: Optional[str] = Field(
        default=None,
        description="Entity or person name (for constancia)"
    )


class DocumentList(BaseModel):
    """
    Schema for processing multiple documents.

    Used when the agent needs to analyze multiple documents at once.
    Not currently used but provided for future batch processing.
    """
    documents: list[DocumentClassification] = Field(
        description="List of classified documents"
    )
