-- ==========================================
-- CREAR TABLA Y INSERTAR ALGORITMOS
-- Ejecutar en Supabase SQL Editor
-- https://supabase.com/dashboard/project/uenywfvtuulcjelouork/sql
-- ==========================================

-- 1. Crear tabla
CREATE TABLE IF NOT EXISTS document_algorithms (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    classification_criteria TEXT NOT NULL,
    extraction_prompt TEXT NOT NULL,
    output_schema TEXT NOT NULL,
    filename_format VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Crear índices
CREATE INDEX IF NOT EXISTS idx_document_algorithms_active
ON document_algorithms(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_document_algorithms_id
ON document_algorithms(id);

-- 3. Insertar algoritmos
INSERT INTO document_algorithms (
    id, name, description, classification_criteria,
    extraction_prompt, output_schema, filename_format, is_active
) VALUES
(
    'factura_rg830',
    'Facturas RG 830',
    'Para facturas de servicios publicos con resolucion general 830',
    'Eres un clasificador experto en documentos contables argentinos. Tu tarea es analizar si el documento ES una factura de servicios publicos con resolucion general 830.',
    'Eres un clasificador experto en documentos contables argentinos. Tu tarea es analizar si el documento ES una factura de servicios publicos con resolucion general 830.',
    '{"servicio": "string", "tipo_factura": "string", "periodo": "string", "cuit_emisor": "string", "numero_factura": "string", "fecha_emision": "string", "importe": "string"}',
    '{fecha_emision}_{servicio}_{tipo_factura}_{numero_factura}.{ext}',
    true
),
(
    'recibo_sueldo',
    'Recibos de Sueldo',
    'Para recibos de haberes, liquidaciones y pagos de nomina',
    'Eres un clasificador experto en documentos de recursos humanos argentinos. Tu tarea es analizar si el documento ES un recibo de sueldo, liquidacion de haberes o comprobante de pago de nomina.',
    'Eres un clasificador experto en documentos de recursos humanos argentinos. Tu tarea es analizar si el documento ES un recibo de sueldo, liquidacion de haberes o comprobante de pago de nomina.',
    '{"tipo_documento": "string", "periodo_pago": "string", "empleado": "string", "cuil": "string", "empleador": "string", "cuit_empleador": "string", "monto_neto": "string"}',
    '{periodo_pago}_{tipo_documento}_{empleado}.{ext}',
    true
),
(
    'resumen_bancario',
    'Resumenes Bancarios',
    'Para resumenes de cuenta, extractos y movimientos bancarios',
    'Eres un clasificador experto en documentos bancarios argentinos. Tu tarea es analizar si el documento ES un resumen de cuenta, extracto, estado de cuenta o movimiento bancario.',
    'Eres un clasificador experto en documentos bancarios argentinos. Tu tarea es analizar si el documento ES un resumen de cuenta, extracto, estado de cuenta o movimiento bancario.',
    '{"banco": "string", "tipo_documento": "string", "periodo_corte": "string", "tipo_cuenta": "string", "saldo_final": "string"}',
    '{periodo_corte}_{banco}_{tipo_documento}.{ext}',
    true
),
(
    'estado_contable',
    'Estados Contables',
    'Para balances generales, estados de resultados y estados patrimoniales',
    'Eres un clasificador experto en informes contables. Tu tarea es analizar si el documento ES un estado contable formal (balance general, estado de resultados, estado patrimonial).',
    'Eres un clasificador experto en informes contables. Tu tarea es analizar si el documento ES un estado contable formal (balance general, estado de resultados, estado patrimonial).',
    '{"tipo_informe": "string", "empresa": "string", "ejercicio": "string", "fecha_cierre": "string", "resultado": "string"}',
    '{fecha_cierre}_{tipo_informe}_{empresa}.{ext}',
    true
),
(
    'contrato',
    'Contratos y Acuerdos',
    'Para contratos de alquiler, servicios, venta, compra y acuerdos comerciales',
    'Eres un clasificador experto en documentos legales y contractuales. Tu tarea es analizar si el documento ES un contrato, acuerdo o documento legal vinculante.',
    'Eres un clasificador experto en documentos legales y contractuales. Tu tarea es analizar si el documento ES un contrato, acuerdo o documento legal vinculante.',
    '{"tipo_contrato": "string", "fecha_inicio": "string", "monto": "string", "empresa": "string"}',
    '{fecha_inicio}_{tipo_contrato}_{empresa}.{ext}',
    true
),
(
    'generic',
    'Generico - Deteccion Automatica',
    'Algoritmo por defecto para documentos que no coinciden con ninguna categoria especifica',
    'Eres un clasificador experto en documentos generales. Tu tarea es analizar el documento y extraer informacion basica para renombrado automatico.',
    'Eres un clasificador experto en documentos generales. Tu tarea es analizar el documento y extraer informacion basica para renombrado automatico.',
    '{"date": "string", "type": "string", "keywords": ["string"], "entity": "string", "concept": "string"}',
    '{date}_{type}_{entity}_{concept}.{ext}',
    true
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    classification_criteria = EXCLUDED.classification_criteria,
    extraction_prompt = EXCLUDED.extraction_prompt,
    output_schema = EXCLUDED.output_schema,
    filename_format = EXCLUDED.filename_format,
    updated_at = NOW();

-- 4. Verificar inserción
SELECT id, name, is_active, created_at
FROM document_algorithms
ORDER BY created_at;
