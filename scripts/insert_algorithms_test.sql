-- =====================================================
-- PASO 2: Insertar algoritmos UNO POR UNO
-- =====================================================

-- Algoritmo 1: Facturas RG 830
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
    'factura_rg830',
    'Facturas RG 830',
    'Para facturas de servicios publicos con resolucion general 830. Identifica automaticamente facturas de servicios (luz, gas, internet, agua, etc.)',
    'Eres un clasificador experto en documentos contables argentinos. Tu tarea es analizar si el documento ES una factura de servicios publicos con resolucion general 830.

Caracteristicas de Facturas RG 830:
- Resolucion de imagen: 830 (aprox 2480x3508 px)
- Contiene: CUIT del emisor, numero de factura, fecha de emision, vencimiento, importe
- Tipo: A (bimestral), B (anual), C (otro)
- Servicio: Luz (Edenor), Gas (CamuzziGas), Agua (AySA), Internet, etc.
- Periodo: Generalmente bimestral (ej: Enero-Febrero)

CRITERIOS DE CLASIFICACION:
1. Identificar si es una factura comercial de servicios
2. Buscar palabras clave: "factura", "servicios", "publicos", "resolucion", "cuit", "importe", "vencimiento"
3. Verificar resolucion aproximada (mencionada en headers o metadatos)
4. Identificar tipo de servicio (luz, gas, agua, internet, etc.)
5. Determinar tipo de factura (A, B, C)

Si NO es una factura RG 830, responde que no lo es.

Output JSON:
{
  "is_factura_rg830": boolean,
  "confidence": float (0.0 a 1.0, que tan seguro estas de la clasificacion),
  "servicio": string (ej: "luz", "gas", "agua", "internet"),
  "tipo_factura": string ("A", "B", "C" o null),
  "periodo": string (ej: "Enero-Febrero" o null),
  "cuit_emisor": string,
  "numero_factura": string,
  "fecha_emision": string (YYYY-MM-DD),
  "vencimiento": string (YYYY-MM-DD o null),
  "observaciones": string
}',
    '{"servicio": "string", "tipo_factura": "string", "periodo": "string", "cuit_emisor": "string", "numero_factura": "string", "fecha_emision": "string", "importe": "string", "vencimiento": "string"}',
    '{fecha_emision}_{servicio}_{tipo_factura}_{numero_factura}.{ext}',
    true
);

-- Verificar que se insertó
SELECT id, name, is_active FROM document_algorithms WHERE id = 'factura_rg830';
