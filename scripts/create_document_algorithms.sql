-- =====================================================
-- Tabla de Algoritmos de Documentos
-- =====================================================
-- Creado: 2026-03-14
-- Autor: amBotHs + Claude
-- Descripción: Algoritmos de clasificación y renombrado automático
-- =====================================================

-- Crear tabla document_algorithms
CREATE TABLE IF NOT EXISTS document_algorithms (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    classification_criteria TEXT NOT NULL,
    extraction_prompt TEXT NOT NULL,
    output_schema JSONB NOT NULL,
    filename_format VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para búsqueda eficiente
CREATE INDEX IF NOT EXISTS idx_document_algorithms_active ON document_algorithms(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_document_algorithms_name ON document_algorithms(name);

-- =====================================================
-- Algoritmos Preconfigurados
-- =====================================================

-- Algoritmo 1: Facturas RG 830
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active) VALUES
('factura_rg830',
 'Facturas RG 830',
 'Para facturas de servicios públicos con resolución general 830. Identifica automáticamente facturas de servicios (luz, gas, internet, agua, etc.)',
 'Eres un clasificador experto en documentos contables argentinos. Tu tarea es analizar si el documento ES una factura de servicios públicos con resolución general 830.

Características de Facturas RG 830:
- Resolución de imagen: 830 (aprox 2480x3508 px)
- Contiene: CUIT del emisor, número de factura, fecha de emisión, vencimiento, importe
- Tipo: A (bimestral), B (anual), C (otro)
- Servicio: Luz (Edenor), Gas (CamuzziGas), Agua (AySA), Internet, etc.
- Periodo: Generalmente bimestral (ej: Enero-Febrero)

CRITERIOS DE CLASIFICACIÓN:
1. Identificar si es una factura comercial de servicios
2. Buscar palabras clave: "factura", "servicios", "públicos", "resolución", "cuit", "importe", "vencimiento"
3. Verificar resolución aproximada (mencionada en headers o metadatos)
4. Identificar tipo de servicio (luz, gas, agua, internet, etc.)
5. Determinar tipo de factura (A, B, C)

Si NO es una factura RG 830, responde que no lo es.

Output JSON:
{
  "is_factura_rg830": boolean,
  "confidence": float (0-1),
  "servicio": string (ej: "luz", "gas", "agua", "internet"),
  "tipo_factura": string ("A", "B", "C" o null),
  "periodo": string (ej: "Enero-Febrero" o null),
  "cuit_emisor": string,
  "numero_factura": string,
  "fecha_emision": string (YYYY-MM-DD),
  "vencimiento": string (YYYY-MM-DD o null),
  "observaciones": string
}',
 '{
  "servicio": "string - tipo de servicio (luz, gas, agua, internet, etc.)",
  "tipo_factura": "string - tipo de factura (A, B, C)",
  "periodo": "string - período bimestral (ej: Enero-Febrero)",
  "cuit_emisor": "string - CUIT del emisor",
  "numero_factura": "string - número de factura",
  "fecha_emision": "string - fecha de emisión YYYY-MM-DD",
  "importe": "string - importe total",
  "vencimiento": "string - fecha de vencimiento YYYY-MM-DD"
}',
 '{fecha_emision}_{servicio}_{tipo_factura}_{numero_factura}.{ext}',
 true);

-- Algoritmo 2: Recibos de Sueldo
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active) VALUES
('recibo_sueldo',
 'Recibos de Sueldo',
 'Para recibos de haberes, liquidaciones y pagos de nómina. Identifica automáticamente comprobantes de pago de sueldos.',
 'Eres un clasificador experto en documentos de recursos humanos argentinos. Tu tarea es analizar si el documento ES un recibo de sueldo, liquidación de haberes o comprobante de pago de nómina.

Características de Recibos de Sueldo:
- Contiene datos del empleado: nombre, CUIL/CUIT
- Contiene datos del empleador: empresa, razón social
- Periodo de pago: Generalmente mensual (ej: "Marzo 2025")
- Montos: Bruto, neto, descuentos
- Tipo: "Liquidación de haberes", "Recibo de sueldo", "Comprobante de pago"
- Palabras clave: "recibo", "liquidación", "haberes", "sueldo", "remuneración", "pago", "nómina", "empleado", "empleador"

CRITERIOS DE CLASIFICACIÓN:
1. Identificar si es un documento de pago/liquidación
2. Buscar palabras clave relacionadas con nómina
3. Verificar datos de empleado y empleador
4. Identificar tipo de documento
5. Determinar período de pago

Si NO es un recibo de sueldo, responde que no lo es.

Output JSON:
{
  "is_recibo_sueldo": boolean,
  "confidence": float (0-1),
  "tipo_documento": string ("Recibo de sueldo", "Liquidación de haberes", "Comprobante de pago"),
  "periodo_pago": string (ej: "Marzo 2025"),
  "empleado": string,
  "cuil": string,
  "empleador": string,
  "cuit_empleador": string,
  "monto_bruto": string,
  "monto_neto": string,
  "fecha_pago": string (YYYY-MM-DD)
}',
 '{
  "tipo_documento": "string - tipo de comprobante",
  "periodo_pago": "string - período de pago",
  "empleado": "string - nombre del empleado",
  "cuil": "string - CUIL del empleado",
  "empleador": "string - nombre de la empresa",
  "cuit_empleador": "string - CUIT del empleador",
  "monto_neto": "string - monto neto recibido",
  "fecha_pago": "string - fecha de pago YYYY-MM-DD"
}',
 '{periodo_pago}_{tipo_documento}_{empleado}.{ext}',
 true);

-- Algoritmo 3: Resúmenes Bancarios
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active) VALUES
('resumen_bancario',
 'Resúmenes Bancarios',
 'Para resúmenes de cuenta, extractos y movimientos bancarios. Identifica automáticamente documentos de bancos.',
 'Eres un clasificador experto en documentos bancarios argentinos. Tu tarea es analizar si el documento ES un resumen de cuenta, extracto, estado de cuenta o movimiento bancario.

Características de Resúmenes Bancarios:
- Contiene: nombre del banco, período de corte, tipo de cuenta
- Datos de cuenta: CBU/CVU, número de cuenta
- Saldo: inicial, final, disponible
- Movimientos: lista de operaciones (ingresos, egresos)
- Tipo de documento: "Resumen de cuenta", "Estado de cuenta", "Extracto", "Movimientos"
- Palabras clave: "banco", "cuenta", "resumen", "estado", "extracto", "saldo", "movimiento", "cbu", "cvu", "débito", "crédito"

CRITERIOS DE CLASIFICACIÓN:
1. Identificar si es un documento de un banco
2. Buscar nombre del banco (Galicia, Santander, Macro, Nación, etc.)
3. Verificar si muestra saldos y movimientos
4. Identificar tipo de documento bancario
5. Determinar período de corte

Si NO es un resumen bancario, responde que no lo es.

Output JSON:
{
  "is_resumen_bancario": boolean,
  "confidence": float (0-1),
  "banco": string (ej: "Galicia", "Santander", "Macro", "Nación"),
  "tipo_documento": string ("Resumen de cuenta", "Estado de cuenta", "Extracto", "Movimientos"),
  "periodo_corte": string (ej: "Marzo 2025"),
  "tipo_cuenta": string (ej: "Cuenta corriente", "Caja de ahorro", "Cuenta sueldo"),
  "cbu_cvu": string,
  "saldo_final": string,
  "fecha_corte": string (YYYY-MM-DD)
}',
 '{
  "banco": "string - nombre del banco",
  "tipo_documento": "string - tipo de documento bancario",
  "periodo_corte": "string - período de corte",
  "tipo_cuenta": "string - tipo de cuenta",
  "saldo_final": "string - saldo al cierre",
  "fecha_corte": "string - fecha de corte YYYY-MM-DD"
}',
 '{periodo_corte}_{banco}_{tipo_documento}.{ext}',
 true);

-- Algoritmo 4: Estados Contables
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active) VALUES
('estado_contable',
 'Estados Contables',
 'Para balances generales, estados de resultados y estados patrimoniales. Identifica automáticamente informes contables formales.',
 'Eres un clasificador experto en informes contables. Tu tarea es analizar si el documento ES un estado contable formal (balance general, estado de resultados, estado patrimonial, etc.).

Características de Estados Contables:
- Documento contable formal con estructura profesional
- Contiene: fecha de cierre, período de ejercicio, empresa/entidad
- Datos contables: Activo, Pasivo, Patrimonio Neto
- Resultado del ejercicio: Ganancia o Pérdida
- Tipo de documento: "Balance General", "Estado de Resultados", "Estado Patrimonial", "Informes de gestión"
- Palabras clave: "balance", "activo", "pasivo", "patrimonio", "resultado", "ganancia", "pérdida", "ejercicio", "cierre", "contable", "informe"

CRITERIOS DE CLASIFICACIÓN:
1. Identificar si es un documento contable formal
2. Buscar términos contables específicos
3. Verificar estructura de balance/estado
4. Identificar tipo de informe contable
5. Determinar período de ejercicio

Si NO es un estado contable, responde que no lo es.

Output JSON:
{
  "is_estado_contable": boolean,
  "confidence": float (0-1),
  "tipo_informe": string ("Balance General", "Estado de Resultados", "Estado Patrimonial", "Otros"),
  "empresa": string,
  "ejercicio": string (ej: "2025" o "Cierre 31/12/2024"),
  "fecha_cierre": string (YYYY-MM-DD),
  "resultado": string ("Ganancia", "Pérdida", "Equilibrio"),
  "moneda": string
}',
 '{
  "tipo_informe": "string - tipo de informe contable",
  "empresa": "string - nombre de la empresa",
  "ejercicio": "string - período de ejercicio",
  "fecha_cierre": "string - fecha de cierre YYYY-MM-DD",
  "resultado": "string - resultado del ejercicio (Ganancia/Pérdida)"
}',
 '{fecha_cierre}_{tipo_informe}_{empresa}.{ext}',
 true);

-- Algoritmo 5: Contratos y Acuerdos
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active) VALUES
('contrato',
 'Contratos y Acuerdos',
 'Para contratos de alquiler, servicios, venta, compra y acuerdos comerciales. Identifica automáticamente documentos contractuales.',
 'Eres un clasificador experto en documentos legales y contractuales. Tu tarea es analizar si el documento ES un contrato, acuerdo o documento legal vinculante.

Características de Contratos:
- Documento legal formal con cláusulas
- Contiene: partes contratantes, objeto del contrato, plazo, condiciones
- Tipo de contrato: "Alquiler", "Servicios", "Venta", "Compra", "Confidencialidad", etc.
- Datos: fechas, montos, firmas, identificaciones
- Palabras clave: "contrato", "acuerdo", "convenio", "cláusulas", "obligaciones", "partes", "vencimiento", "plazo", "renovación"

CRITERIOS DE CLASIFICACIÓN:
1. Identificar si es un documento legal/contractual
2. Buscar términos contractuales
3. Identificar tipo de contrato
4. Extraer partes involucradas
5. Determinar fechas importantes

Si NO es un contrato, responde que no lo es.

Output JSON:
{
  "is_contrato": boolean,
  "confidence": float (0-1),
  "tipo_contrato": string ("Alquiler", "Servicios", "Venta", "Compra", "Confidencialidad", "Otro"),
  "partes": [string, string],
  "fecha_inicio": string (YYYY-MM-DD),
  "fecha_fin": string (YYYY-MM-DD o null),
  "monto": string o null,
  "empresa": string o null
}',
 '{
  "tipo_contrato": "string - tipo de contrato",
  "fecha_inicio": "string - fecha de inicio YYYY-MM-DD",
  "monto": "string - monto del contrato o null",
  "empresa": "string - empresa o null"
}',
 '{fecha_inicio}_{tipo_contrato}_{empresa}.{ext}',
 true);

-- =====================================================
-- Algoritmo Genérico (Fallback)
-- =====================================================
-- Este es el algoritmo por defecto cuando no se clasifica como ninguno específico

INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active) VALUES
('generic',
 'Genérico - Detección Automática',
 'Algoritmo por defecto para documentos que no coinciden con ninguna categoría específica. Detecta automáticamente fecha, tipo y palabras clave del documento.',
 'Eres un clasificador experto en documentos generales. Tu tarea es analizar el documento y extraer información básica para renombrado automático.

Características de Documentos Genéricos:
- Cualquier tipo de documento
- Contiene: fecha (de creación, emisión, fecha del documento), tipo de contenido
- Objetivo: Extraer datos mínimos para generar un nombre descriptivo
- Palabras clave: Términos principales que describan el contenido

CRITERIOS DE EXTRACCIÓN:
1. Identificar fecha del documento (creación, emisión, fecha de archivo)
2. Determinar tipo de documento (qué describe el archivo)
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
  "ext": string (extensión del archivo)
}',
 '{
  "date": "string - fecha del documento YYYY-MM-DD",
  "type": "string - tipo de documento",
  "keywords": ["string", "string", "string"] - palabras clave principales (2-3 palabras unidas con _),
  "entity": "string - entidad o null",
  "concept": "string - concepto o null",
  "ext": "string - extensión del archivo"
}',
 '{date}_{type}_{entity}_{concept}.{ext}',
 true);

-- =====================================================
-- Comentario final
-- =====================================================
COMMENT ON TABLE document_algorithms IS 'Algoritmos de clasificación y renombrado automático de documentos. Cada algoritmo tiene criterios de clasificación, instrucciones de extracción y formato de nombre de archivo.';
