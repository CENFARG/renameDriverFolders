"""
Pydantic models for structured outputs from Gemini via Agno
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List


class FileAnalysis(BaseModel):
    """
    Structured output from Gemini for file analysis.
    This model is used with Agno's response_model to guarantee
    structured JSON output from Gemini.
    """
    date: str = Field(
        description="Date extracted from document in YYYY-MM-DD format. If no date found, use today's date."
    )
    keywords: List[str] = Field(
        description="Exactly 3 keywords that best categorize the document: (1) document type, (2) main entity/company, (3) main concept",
        min_length=3,
        max_length=3
    )
    category: str = Field(
        description="The main category of the document. Examples: 'Factura', 'Contrato', 'Resumen', 'Informe Estratégico', 'Análisis de Discurso', 'Síntesis Ejecutiva', 'Mapa de Actores', 'Varios'."
    )
    
    model_config = ConfigDict(
        extra='ignore'
    )
