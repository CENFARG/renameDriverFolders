# Crear Tabla de Algoritmos en Supabase

## Paso 1: Abrir el Editor SQL de Supabase

1. Ir a: https://supabase.com/dashboard/project/uenywfvtuulcjelouork
2. En el menú lateral, hacer clic en **"SQL Editor"**
3. Crear una nueva query

## Paso 2: Ejecutar el SQL para crear la tabla

Copiar y pegar este SQL:

```sql
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
CREATE INDEX IF NOT EXISTS idx_document_algorithms_active
ON document_algorithms(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_document_algorithms_id
ON document_algorithms(id);

-- Verificar que la tabla se creó
SELECT * FROM document_algorithms;
```

## Paso 3: Verificar que la tabla existe

Ejecutar:
```sql
SELECT COUNT(*) as table_exists
FROM information_schema.tables
WHERE table_name = 'document_algorithms';
```

Debería mostrar `1` si la tabla existe.

## Paso 4: Insertar un algoritmo de prueba

```sql
INSERT INTO document_algorithms (
    id, name, description, classification_criteria,
    extraction_prompt, output_schema, filename_format, is_active
) VALUES (
    'factura_rg830',
    'Facturas RG 830',
    'Para facturas de servicios publicos con resolucion general 830',
    'Eres un clasificador experto en documentos contables argentinos.',
    'Eres un clasificador experto en documentos contables argentinos.',
    '{"servicio": "string", "tipo_factura": "string"}',
    '{fecha_emision}_{servicio}_{tipo_factura}.{ext}',
    true
);
```

## Paso 5: Verificar la inserción

```sql
SELECT id, name, is_active, created_at
FROM document_algorithms;
```

---

**NOTA IMPORTANTE**: Los 6 algoritmos restantes se insertarán con el script Python corregido.
