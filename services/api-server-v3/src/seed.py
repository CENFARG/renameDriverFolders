"""
Seed — Default algorithm seeding.
=================================

Seeds professional study algorithms on first run
if they don't exist in the database.

:created:   2026-05-06
:filename:  seed.py
:path:      services/api-server-v3/src/seed.py
:author:    CENF
:version:   1.0.0
:license:   MIT
:copyright: Copyright (c) 2026 CENF
"""

import logging

logger = logging.getLogger(__name__)

DEFAULT_ALGORITHMS = [
    {
        "id": "facturas-rg830",
        "name": "Facturas RG 830 (Deteccion Auto)",
        "description": "Estilo Diego Cutignola: [FECHA]_[TIPO]_[EMISOR]_[DETALLE]",
        "active": True,
        "trigger_type": "manual",
        "source_folder_id": "DYNAMIC",
        "target_folder_names": ["Procesados"],
        "agent_config": {
            "model": {"name": "gemini-2.5-flash", "temperature": 0.1, "max_tokens": 4096},
            "instructions": "Analiza el documento. Si es factura, usa TIPO=FACTURA. Emisor: Empresa externa. Detalle: Concepto breve.",
            "prompt_template": "Analiza: {content}. Formato: YYYY-MM-DD_FACTURA_EMISOR_DETALLE. Devuelve solo el nombre.",
            "filename_format": "{date}_FACTURA_{issuer}_{detail}",
        },
    },
    {
        "id": "sueldos-digitales",
        "name": "Sueldos y Liquidaciones RRHH",
        "description": "Estilo Diego Cutignola: AAAA-MM_SUELDO_EMPRESA_DETALLE",
        "active": True,
        "trigger_type": "manual",
        "source_folder_id": "DYNAMIC",
        "target_folder_names": ["Recibos_Procesados"],
        "agent_config": {
            "model": {"name": "gemini-2.5-pro", "temperature": 0.1, "max_tokens": 4096},
            "instructions": "Analiza recibos de sueldo. Usa TIPO=SUELDO. Emisor: Nombre de la empresa. Detalle: Apellido empleado o concepto.",
            "prompt_template": "Analiza: {content}. Formato: YYYY-MM_SUELDO_EMPRESA_DETALLE.",
            "filename_format": "{date}_SUELDO_{issuer}_{detail}",
        },
    },
    {
        "id": "resumenes-bancarios",
        "name": "Resumenes y Tenencias",
        "description": "Estilo Diego Cutignola: AAAA-MM_RESUMEN_BANCO_DETALLE",
        "active": True,
        "trigger_type": "manual",
        "source_folder_id": "DYNAMIC",
        "target_folder_names": ["Extractos"],
        "agent_config": {
            "model": {"name": "gemini-2.5-flash", "temperature": 0.1, "max_tokens": 4096},
            "instructions": "Analiza resumenes. Usa TIPO=RESUMEN. Emisor: Banco o Broker. Detalle: Tipo de cuenta.",
            "prompt_template": "Analiza: {content}. Formato: YYYY-MM_RESUMEN_BANCO_DETALLE.",
            "filename_format": "{date}_RESUMEN_{issuer}_{detail}",
        },
    },
    {
        "id": "estados-contables",
        "name": "Estados Contables y Balances",
        "description": "Estilo Diego Cutignola: AAAA_CONTABLE_CLIENTE_DETALLE",
        "active": True,
        "trigger_type": "manual",
        "source_folder_id": "DYNAMIC",
        "target_folder_names": ["Balances_Oficiales"],
        "agent_config": {
            "model": {"name": "gemini-3-pro-preview", "temperature": 0.1, "max_tokens": 4096},
            "instructions": "Analiza Balances. Usa TIPO=CONTABLE. Emisor: Nombre del Cliente. Detalle: Estados Contables.",
            "prompt_template": "Analiza: {content}. Formato: YYYY_CONTABLE_CLIENTE_Estados_Contables.",
            "filename_format": "{date}_CONTABLE_{issuer}_Estados_Contables",
        },
    },
]


def seed_default_algorithms(db_manager):
    """
    Seed professional study algorithms if they don't exist.

    Args:
        db_manager: DatabaseManager for the jobs table.
    """
    for algo in DEFAULT_ALGORITHMS:
        try:
            if not db_manager.find("id", algo["id"]):
                db_manager.insert(algo)
                logger.info(f"Seeded algorithm: {algo['id']}")
        except Exception as e:
            logger.error(f"Failed to seed {algo['id']}: {e}")
