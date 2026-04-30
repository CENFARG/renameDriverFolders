-- ============================================================
-- RECUPERAR ALGORITMOS BORRADOS
-- ============================================================

-- 1. ESTADO CONTABLE
INSERT INTO document_algorithms (
    id,
    name,
    description,
    classification_criteria,
    extraction_prompt,
    output_schema,
    filename_format,
    is_active
) VALUES (
    'estado_contable',
    'Estado Contable',
    'Procesa estados contables de empresas. Extrae fecha, tipo de estado y nombre de la empresa.',
    'Documentos contables que incluyen estados contables, balances generales, cuadros de resultados y estados de situación patrimonial. Incluyen términos como "activo", "pasivo", "patrimonio neto", "resultado del ejercicio".',
    'Extrae del estado contable:
1. Fecha de cierre del ejercicio (formato AAAA-MM-DD)
2. Tipo de estado (ej: "balance_general", "estado_resultados", "estado_situacion_patrimonial")
3. Nombre de la empresa (como figura en el documento)
4. Año fiscal

Devuelve en formato JSON.',
    '{
        "date": "string - fecha de cierre del estado contable (YYYY-MM-DD)",
        "type": "string - tipo de estado contable",
        "company": "string - nombre de la empresa",
        "fiscal_year": "string - año fiscal"
    }',
    'estado_contable_{company}_{fiscal_year}_{date}.{ext}',
    true
) ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    classification_criteria = EXCLUDED.classification_criteria,
    extraction_prompt = EXCLUDED.extraction_prompt,
    output_schema = EXCLUDED.output_schema,
    filename_format = EXCLUDED.filename_format,
    is_active = EXCLUDED.is_active;

-- 2. RECIBO DE SUELDO
INSERT INTO document_algorithms (
    id,
    name,
    description,
    classification_criteria,
    extraction_prompt,
    output_schema,
    filename_format,
    is_active
) VALUES (
    'recibo_sueldo',
    'Recibo de Sueldo',
    'Procesa recibos de sueldo. Extrae fecha de pago, período, empleado y monto neto.',
    'Documentos de nómina que incluyen recibos de sueldo, liquidaciones de haberes, boletas de pago. Contienen términos como "sueldo", "jornal", "remuneración", "deducciones", "neto a cobrar", "período", "empleador".',
    'Extrae del recibo de sueldo:
1. Fecha de pago (formato AAAA-MM-DD)
2. Período liquidado (ej: "2024-01" o "01/2024")
3. Nombre completo del empleado
4. Monto neto a cobrar (valor numérico)
5. Nombre del empleador

Devuelve en formato JSON.',
    '{
        "date": "string - fecha de pago (YYYY-MM-DD)",
        "period": "string - período liquidado",
        "employee": "string - nombre del empleado",
        "net_amount": "number - monto neto a cobrar",
        "employer": "string - nombre del empleador"
    }',
    'recibo_{employee}_{period}_{date}.{ext}',
    true
) ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    classification_criteria = EXCLUDED.classification_criteria,
    extraction_prompt = EXCLUDED.extraction_prompt,
    output_schema = EXCLUDED.output_schema,
    filename_format = EXCLUDED.filename_format,
    is_active = EXCLUDED.is_active;

-- 3. RESUMEN BANCARIO
INSERT INTO document_algorithms (
    id,
    name,
    description,
    classification_criteria,
    extraction_prompt,
    output_schema,
    filename_format,
    is_active
) VALUES (
    'resumen_bancario',
    'Resumen Bancario',
    'Procesa resúmenes de cuenta bancaria. Extrae fecha de corte, periodo, banco y tipo de cuenta.',
    'Documentos bancarios que incluyen resúmenes de cuenta, estados de cuenta, movimientos bancarios. Contienen términos como "saldo", "débito", "crédito", "resumen", "cuenta corriente", "caja de ahorro", "CBU", "CVU".',
    'Extrae del resumen bancario:
1. Fecha de corte del resumen (formato AAAA-MM-DD)
2. Período resumido (ej: "2024-01" o "enero 2024")
3. Nombre del banco
4. Tipo de cuenta (ej: "cuenta_corriente", "caja_ahorro")
5. Últimos 4 dígitos del número de cuenta

Devuelve en formato JSON.',
    '{
        "date": "string - fecha de corte (YYYY-MM-DD)",
        "period": "string - período resumido",
        "bank": "string - nombre del banco",
        "account_type": "string - tipo de cuenta",
        "account_last4": "string - últimos 4 dígitos de la cuenta"
    }',
    'resumen_{bank}_{account_type}_{period}_{date}.{ext}',
    true
) ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    classification_criteria = EXCLUDED.classification_criteria,
    extraction_prompt = EXCLUDED.extraction_prompt,
    output_schema = EXCLUDED.output_schema,
    filename_format = EXCLUDED.filename_format,
    is_active = EXCLUDED.is_active;

-- Verificar que se crearon correctamente
SELECT id, name, is_active FROM document_algorithms;
