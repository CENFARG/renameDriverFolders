"""
Pydantic models for structured outputs from Gemini via Agno.
Based on Estudio Cutignola business requirements (Diego Cutignola, Nov 2025).
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class FileAnalysis(BaseModel):
    """
    Structured output from Gemini for file analysis.
    
    Business Format: [FECHA]_[CATEGORÍA]_[EMISOR]_[DETALLE_BREVE]
    
    Client: Estudio Cutignola
    Spec Date: Nov 2025

    IMPORTANT: Return ONLY the data. DO NOT include an 'examples' field in the output.
    """
    date: str = Field(
        description=(
            "Date in format: YYYY-MM-DD (punctual docs like invoices), "
            "YYYY-MM (monthly docs like bank statements), or "
            "YYYY (annual docs like balance sheets). "
            "Extract from document content."
        )
    )
    category: Literal[
        "CONTABLE", "FACTURA", "SUELDO", "RESUMEN", 
        "IMPUESTO", "LEGAL", "DOC-INTERNA", "CONSTANCIA"
    ] = Field(
        description=(
            "Document category (exclusive): "
            "CONTABLE (Balances, Libro Diario, Sumas y Saldos), "
            "FACTURA (Facturas A/B/C, Tickets, Notas de Crédito), "
            "SUELDO (Recibos de Haberes, F931, Liquidaciones), "
            "RESUMEN (Resúmenes Bancarios, Tarjetas, Brokers), "
            "IMPUESTO (VEPs, DDJJ IIBB/Ganancias, Tasas), "
            "LEGAL (Contratos, Estatutos, Actas), "
            "DOC-INTERNA (Excel auxiliares, borradores), "
            "CONSTANCIA (Inscripciones, CUIT)"
        )
    )
    issuer: str = Field(
        max_length=30,
        description=(
            "Entity or company that issued the document. "
            "Examples: 'AFIP', 'Banco Galicia', 'Cliente XYZ'. "
            "Max 30 characters, no spaces, use hyphens."
        )
    )
    brief_detail: str = Field(
        max_length=50,
        description=(
            "Brief description of document content or specific type. "
            "Examples: 'balance-general', 'resumen-tarjeta-visa', 'contrato-locacion'. "
            "Max 50 characters, lowercase, use hyphens, no spaces."
        )
    )
    
    model_config = ConfigDict(extra='ignore')
