-- =====================================================
-- PASO 1: Crear tabla document_algorithms
-- =====================================================

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

-- Crear indices
CREATE INDEX IF NOT EXISTS idx_document_algorithms_active ON document_algorithms(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_document_algorithms_id ON document_algorithms(id);

-- Verificar que la tabla se creó
SELECT COUNT(*) as table_exists FROM information_schema.tables WHERE table_name = 'document_algorithms';
