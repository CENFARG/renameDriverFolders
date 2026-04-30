-- Insertar los 7 algoritmos faltantes definidos por Diego
-- Basado en el archivo "Prompt para renombrar.txt"

-- 1. FACTURA
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'factura',
    'Factura',
    'Procesa facturas, comprobantes A/B/C y tickets. Extrae fecha, emisor, tipo y detalles.',
    'Comprobantes de compra/venta incluyendo facturas A, B, C, tickets, facturas de bienes de uso. Contienen términos como "factura", "comprobante", "gravado", "no gravado", "IVA", "CAE", "CUIT".',
    'Extrae de la factura:
1. Fecha de emisión (formato AAAA-MM-DD para facturas puntuales)
2. Tipo de comprobante (A, B, C, ticket)
3. Nombre del emisor (empresa que emite la factura)
4. Número de factura
5. Importe total si está disponible
6. Detalle breve de qué se compra (ej: "Compra_Fiat_Cronos")

Devuelve en formato JSON.',
    '{
        "date": "string - fecha de emisión (YYYY-MM-DD)",
        "type": "string - tipo de comprobante (A/B/C/ticket)",
        "issuer": "string - nombre del emisor",
        "number": "string - número de factura",
        "amount": "number - importe total (opcional)",
        "detail": "string - descripción breve del concepto"
    }',
    '{date}_FACTURA_{issuer}_{detail}',
    true
);

-- 2. PRESTAMO
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'prestamo',
    'Préstamo',
    'Procesa liquidaciones de cuotas y estados de deuda. Extrae fecha, entidad, tipo y cuota.',
    'Documentos de préstamos incluyendo liquidaciones de cuotas, estados de deuda financiera, mutuos bancarios. Contienen términos como "cuota", "préstamo", "deuda", "amortización", "interés", "prendario", "hipotecario".',
    'Extrae del préstamo:
1. Fecha del comprobante (formato AAAA-MM-DD)
2. Nombre de la entidad bancaria
3. Tipo de préstamo (prendario, hipotecario, personal)
4. Número de cuota
5. Detalle adicional (ej: "Cuota_Prendario")

Devuelve en formato JSON.',
    '{
        "date": "string - fecha del comprobante (YYYY-MM-DD)",
        "bank": "string - nombre del banco",
        "loan_type": "string - tipo de préstamo",
        "installment": "string - número de cuota",
        "detail": "string - detalle adicional"
    }',
    '{date}_PRESTAMO_{bank}_{detail}',
    true
);

-- 3. IMPUESTO
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'impuesto',
    'Impuesto',
    'Procesa DDJJ, formularios AFIP/ARCA y pagos de impuestos. Extrae período, impuesto y organismo.',
    'Documentos impositivos incluyendo VEP, declaraciones juradas, formularios AFIP/ARCA, IIBB, tasas. Contienen términos como "DDJJ", "F931", "VEP", "impuesto", "ARCA", "período fiscal".',
    'Extrae del impuesto:
1. Período fiscal (formato AAAA-MM para mensuales, AAAA para anuales)
2. Nombre del organismo (AFIP, ARCA, IIBB, municipalidad)
3. Tipo de impuesto o formulario (ej: "F931", "IVA", "Ganancias")
4. Detalle específico (ej: "Cargas_Sociales")

Devuelve en formato JSON.',
    '{
        "period": "string - período fiscal (YYYY-MM o YYYY)",
        "organism": "string - nombre del organismo (AFIP/ARCA/IIBB)",
        "tax_type": "string - tipo de impuesto o formulario",
        "detail": "string - detalle específico"
    }',
    '{period}_IMPUESTO_{organism}_{tax_type}_{detail}',
    true
);

-- 4. SEGURO
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'seguro',
    'Seguro',
    'Procesa pólizas y certificados de cobertura. Extrae fecha, aseguradora, tipo y asegurado.',
    'Documentos de seguros incluyendo pólizas, certificados de cobertura, recibos de pago de primas. Contienen términos como "póliza", "seguro", "cobertura", "aseguradora", "prima", "siniestro".',
    'Extrae del seguro:
1. Fecha de emisión o vigencia (formato AAAA-MM-DD)
2. Nombre de la aseguradora
3. Tipo de seguro (automotor, incendio, vida, responsabilidad civil)
4. Nombre del asegurado (empresa o persona)
5. Número de póliza si está disponible

Devuelve en formato JSON.',
    '{
        "date": "string - fecha de emisión o vigencia (YYYY-MM-DD)",
        "insurer": "string - nombre de la aseguradora",
        "insurance_type": "string - tipo de seguro",
        "insured": "string - nombre del asegurado",
        "policy_number": "string - número de póliza (opcional)"
    }',
    '{date}_SEGURO_{insurer}_{insurance_type}',
    true
);

-- 5. LEGAL
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'legal',
    'Legal',
    'Procesa contratos, escrituras y documentos legales. Extrae fecha, tipo, partes y concepto.',
    'Documentos legales incluyendo contratos comerciales, escrituras, mutuos entre partes, estatutos. Contienen términos como "contrato", "escritura", "mutuo", "estatutos", "comparecen", "certifico".',
    'Extrae del documento legal:
1. Fecha del documento (formato AAAA-MM-DD)
2. Tipo de documento (contrato, escritura, mutuo, estatutos)
3. Partes intervinientes (empresas o personas)
4. Objeto o concepto breve del acuerdo

Devuelve en formato JSON.',
    '{
        "date": "string - fecha del documento (YYYY-MM-DD)",
        "doc_type": "string - tipo de documento legal",
        "parties": "string - partes intervinientes",
        "concept": "string - objeto o concepto del acuerdo"
    }',
    '{date}_LEGAL_{doc_type}_{parties}_{concept}',
    true
);

-- 6. DOC_INTERNA
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'doc_interna',
    'Documento Interno',
    'Procesa documentos internos del estudio. Extrae fecha, cliente y tipo de trabajo.',
    'Documentos internos de trabajo incluyendo papeles de trabajo, planillas Excel de cálculos auxiliares, borradores. Contienen términos como "ajuste", "cálculo", "borrador", "hoja de trabajo", "auxiliar".',
    'Extrae del documento interno:
1. Fecha o período (formato AAAA-MM para documentos periódicos)
2. Nombre del cliente/empresa
3. Tipo de trabajo (ajuste por inflación, cálculo de impuestos, planificación)
4. Detalle específico del trabajo

Devuelve en formato JSON.',
    '{
        "period": "string - período o fecha (YYYY-MM)",
        "client": "string - nombre del cliente",
        "work_type": "string - tipo de trabajo",
        "detail": "string - detalle específico"
    }',
    '{period}_DOC-INTERNA_{client}_{work_type}_{detail}',
    true
);

-- 7. CONSTANCIA
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'constancia',
    'Constancia',
    'Procesa constancias, certificados y documentos de inscripción. Extrae fecha, tipo y organismo.',
    'Documentos de constancia incluyendo inscripciones, CUIT, domicilio, certificados. Contienen términos como "constancia", "certificado", "inscripción", "CUIT", "domicilio", "tramité".',
    'Extrae de la constancia:
1. Fecha de emisión (formato AAAA-MM-DD)
2. Tipo de constancia (inscripción, CUIT, domicilio)
3. Organismo que emite (AFIP, municipalidad, otro)
4. Nombre de la empresa o persona si está disponible

Devuelve en formato JSON.',
    '{
        "date": "string - fecha de emisión (YYYY-MM-DD)",
        "type": "string - tipo de constancia",
        "organism": "string - organismo emisor",
        "entity": "string - nombre de la empresa o persona (opcional)"
    }',
    '{date}_CONSTANCIA_{type}_{organism}',
    true
);

-- Verificar que se insertaron correctamente
SELECT id, name, is_active FROM document_algorithms ORDER BY name;
