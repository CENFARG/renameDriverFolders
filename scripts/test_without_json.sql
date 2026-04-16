-- Script de prueba sin formato JSON
-- Prueba si el problema es con el ::jsonb

-- Crear tabla
CREATE TABLE IF NOT EXISTS document_algorithms (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    classification_criteria TEXT NOT NULL,
    extraction_prompt TEXT NOT NULL,
    output_schema TEXT NOT NULL,
    filename_format VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Insert sin ::jsonb (como TEXT simple)
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES (
    'factura_rg830',
    'Facturas RG 830',
    'Para facturas de servicios publicos',
    'Prompt de clasificacion...',
    '{"servicio": "string"}',
    '{fecha}_{servicio}.{ext}',
    true
);

-- Verificar
SELECT id, name, is_active FROM document_algorithms;
