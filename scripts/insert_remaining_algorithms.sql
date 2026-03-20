-- =====================================================
-- PASO 3: Insertar los algoritmos restantes
-- =====================================================

-- Algoritmo 2: Recibos de Sueldo
INSERT INTO document_algorithms (
    id, name, description, classification_criteria, extraction_prompt,
    output_schema, filename_format, is_active
) VALUES (
    'recibo_sueldo',
    'Recibos de Sueldo',
    'Para recibos de haberes, liquidaciones y pagos de nomina. Identifica automaticamente comprobantes de pago de sueldos.',
    'Eres un clasificador experto en documentos de recursos humanos argentinos. Tu tarea es analizar si el documento ES un recibo de sueldo, liquidacion de haberes o comprobante de pago de nomina.

Caracteristicas de Recibos de Sueldo:
- Contiene datos del empleado: nombre, CUIL/CUIT
- Contiene datos del empleador: empresa, razon social
- Periodo de pago: Generalmente mensual (ej: "Marzo 2025")
- Montos: Bruto, neto, descuentos
- Tipo: "Liquidacion de haberes", "Recibo de sueldo", "Comprobante de pago"
- Palabras clave: "recibo", "liquidacion", "haberes", "sueldo", "remuneracion", "pago", "nomina", "empleado", "empleador"

CRITERIOS DE CLASIFICACION:
1. Identificar si es un documento de pago/liquidacion
2. Buscar palabras clave relacionadas con nomina
3. Verificar datos de empleado y empleador
4. Identificar tipo de documento
5. Determinar periodo de pago

Si NO es un recibo de sueldo, responde que no lo es.

Output JSON:
{
  "is_recibo_sueldo": boolean,
  "confidence": float (0.0 a 1.0, que tan seguro estas de la clasificacion),
  "tipo_documento": string ("Recibo de sueldo", "Liquidacion de haberes", "Comprobante de pago"),
  "periodo_pago": string (ej: "Marzo 2025"),
  "empleado": string,
  "cuil": string,
  "empleador": string,
  "cuit_empleador": string,
  "monto_bruto": string,
  "monto_neto": string,
  "fecha_pago": string (YYYY-MM-DD)
}',
    '{"tipo_documento": "string", "periodo_pago": "string", "empleado": "string", "cuil": "string", "empleador": "string", "cuit_empleador": "string", "monto_neto": "string", "fecha_pago": "string"}',
    '{periodo_pago}_{tipo_documento}_{empleado}.{ext}',
    true
);

-- Algoritmo 3: Resumenes Bancarios
INSERT INTO document_algorithms (
    id, name, description, classification_criteria, extraction_prompt,
    output_schema, filename_format, is_active
) VALUES (
    'resumen_bancario',
    'Resumenes Bancarios',
    'Para resumenes de cuenta, extractos y movimientos bancarios. Identifica automaticamente documentos de bancos.',
    'Eres un clasificador experto en documentos bancarios argentinos. Tu tarea es analizar si el documento ES un resumen de cuenta, extracto, estado de cuenta o movimiento bancario.

Caracteristicas de Resumenes Bancarios:
- Contiene: nombre del banco, periodo de corte, tipo de cuenta
- Datos de cuenta: CBU/CVU, numero de cuenta
- Saldo: inicial, final, disponible
- Movimientos: lista de operaciones (ingresos, egresos)
- Tipo de documento: "Resumen de cuenta", "Estado de cuenta", "Extracto", "Movimientos"
- Palabras clave: "banco", "cuenta", "resumen", "estado", "extracto", "saldo", "movimiento", "cbu", "cvu", "debito", "credito"

CRITERIOS DE CLASIFICACION:
1. Identificar si es un documento de un banco
2. Buscar nombre del banco (Galicia, Santander, Macro, Nacion, etc.)
3. Verificar si muestra saldos y movimientos
4. Identificar tipo de documento bancario
5. Determinar periodo de corte

Si NO es un resumen bancario, responde que no lo es.

Output JSON:
{
  "is_resumen_bancario": boolean,
  "confidence": float (0.0 a 1.0, que tan seguro estas de la clasificacion),
  "banco": string (ej: "Galicia", "Santander", "Macro", "Nacion"),
  "tipo_documento": string ("Resumen de cuenta", "Estado de cuenta", "Extracto", "Movimientos"),
  "periodo_corte": string (ej: "Marzo 2025"),
  "tipo_cuenta": string (ej: "Cuenta corriente", "Caja de ahorro", "Cuenta sueldo"),
  "cbu_cvu": string,
  "saldo_final": string,
  "fecha_corte": string (YYYY-MM-DD)
}',
    '{"banco": "string", "tipo_documento": "string", "periodo_corte": "string", "tipo_cuenta": "string", "saldo_final": "string", "fecha_corte": "string"}',
    '{periodo_corte}_{banco}_{tipo_documento}.{ext}',
    true
);

-- Algoritmo 4: Estados Contables
INSERT INTO document_algorithms (
    id, name, description, classification_criteria, extraction_prompt,
    output_schema, filename_format, is_active
) VALUES (
    'estado_contable',
    'Estados Contables',
    'Para balances generales, estados de resultados y estados patrimoniales. Identifica automaticamente informes contables formales.',
    'Eres un clasificador experto en informes contables. Tu tarea es analizar si el documento ES un estado contable formal (balance general, estado de resultados, estado patrimonial, etc.).

Caracteristicas de Estados Contables:
- Documento contable formal con estructura profesional
- Contiene: fecha de cierre, periodo de ejercicio, empresa/entidad
- Datos contables: Activo, Pasivo, Patrimonio Neto
- Resultado del ejercicio: Ganancia o Perdida
- Tipo de documento: "Balance General", "Estado de Resultados", "Estado Patrimonial", "Informes de gestion"
- Palabras clave: "balance", "activo", "pasivo", "patrimonio", "resultado", "ganancia", "perdida", "ejercicio", "cierre", "contable", "informe"

CRITERIOS DE CLASIFICACION:
1. Identificar si es un documento contable formal
2. Buscar terminos contables especificos
3. Verificar estructura de balance/estado
4. Identificar tipo de informe contable
5. Determinar periodo de ejercicio

Si NO es un estado contable, responde que no lo es.

Output JSON:
{
  "is_estado_contable": boolean,
  "confidence": float (0.0 a 1.0, que tan seguro estas de la clasificacion),
  "tipo_informe": string ("Balance General", "Estado de Resultados", "Estado Patrimonial", "Otros"),
  "empresa": string,
  "ejercicio": string (ej: "2025" o "Cierre 31/12/2024"),
  "fecha_cierre": string (YYYY-MM-DD),
  "resultado": string ("Ganancia", "Perdida", "Equilibrio"),
  "moneda": string
}',
    '{"tipo_informe": "string", "empresa": "string", "ejercicio": "string", "fecha_cierre": "string", "resultado": "string"}',
    '{fecha_cierre}_{tipo_informe}_{empresa}.{ext}',
    true
);

-- Algoritmo 5: Contratos y Acuerdos
INSERT INTO document_algorithms (
    id, name, description, classification_criteria, extraction_prompt,
    output_schema, filename_format, is_active
) VALUES (
    'contrato',
    'Contratos y Acuerdos',
    'Para contratos de alquiler, servicios, venta, compra y acuerdos comerciales. Identifica automaticamente documentos contractuales.',
    'Eres un clasificador experto en documentos legales y contractuales. Tu tarea es analizar si el documento ES un contrato, acuerdo o documento legal vinculante.

Caracteristicas de Contratos:
- Documento legal formal con clausulas
- Contiene: partes contratantes, objeto del contrato, plazo, condiciones
- Tipo de contrato: "Alquiler", "Servicios", "Venta", "Compra", "Confidencialidad", etc.
- Datos: fechas, montos, firmas, identificaciones
- Palabras clave: "contrato", "acuerdo", "convenio", "clausulas", "obligaciones", "partes", "vencimiento", "plazo", "renovacion"

CRITERIOS DE CLASIFICACION:
1. Identificar si es un documento legal/contractual
2. Buscar terminos contractuales
3. Identificar tipo de contrato
4. Extraer partes involucradas
5. Determinar fechas importantes

Si NO es un contrato, responde que no lo es.

Output JSON:
{
  "is_contrato": boolean,
  "confidence": float (0.0 a 1.0, que tan seguro estas de la clasificacion),
  "tipo_contrato": string ("Alquiler", "Servicios", "Venta", "Compra", "Confidencialidad", "Otro"),
  "partes": [string, string],
  "fecha_inicio": string (YYYY-MM-DD),
  "fecha_fin": string (YYYY-MM-DD o null),
  "monto": string o null,
  "empresa": string o null
}',
    '{"tipo_contrato": "string", "fecha_inicio": "string", "monto": "string", "empresa": "string"}',
    '{fecha_inicio}_{tipo_contrato}_{empresa}.{ext}',
    true
);

-- Algoritmo 6: Generico (Fallback)
INSERT INTO document_algorithms (
    id, name, description, classification_criteria, extraction_prompt,
    output_schema, filename_format, is_active
) VALUES (
    'generic',
    'Generico - Deteccion Automatica',
    'Algoritmo por defecto para documentos que no coinciden con ninguna categoria especifica. Detecta automaticamente fecha, tipo y palabras clave del documento.',
    'Eres un clasificador experto en documentos generales. Tu tarea es analizar el documento y extraer informacion basica para renombrado automatico.

Caracteristicas de Documentos Genericos:
- Cualquier tipo de documento
- Contiene: fecha (de creacion, emision, fecha del documento), tipo de contenido
- Objetivo: Extraer datos minimos para generar un nombre descriptivo
- Palabras clave: Terminos principales que describen el contenido

CRITERIOS DE EXTRACCION:
1. Identificar fecha del documento (creacion, emision, fecha de archivo)
2. Determinar tipo de documento (que describe el archivo)
3. Extraer 3-5 palabras clave principales
4. Si hay entidad/empresa, incluirla

Formato de fecha: YYYY-MM-DD (si no se encuentra, usar fecha actual)

Output JSON:
{
  "date": string (YYYY-MM-DD),
  "type": string (tipo de documento),
  "keywords": [string, string, string], (3-5 palabras clave),
  "entity": string o null (empresa/emisor si se identifica),
  "concept": string o null (concepto breve descriptivo),
  "ext": string (extension del archivo)
}',
    '{"date": "string", "type": "string", "keywords": ["string", "string", "string"], "entity": "string", "concept": "string", "ext": "string"}',
    '{date}_{type}_{entity}_{concept}.{ext}',
    true
);

-- Verificar todos los algoritmos insertados
SELECT id, name, is_active, created_at FROM document_algorithms ORDER BY created_at;
