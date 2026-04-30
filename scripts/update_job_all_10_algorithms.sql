-- ACTUALIZAR job-manual-auto-classify con LOS 10 ALGORITMOS COMPLETOS
-- Incluye los 7 nuevos algorithms que acabamos de crear

UPDATE jobs
SET agent_config = jsonb_set(
    agent_config,
    '{prompt_template}',
    to_jsonb($prompt$Analyze the following document and determine which algorithm applies:

ORIGINAL FILE: {original_filename}

DOCUMENT CONTENT:
{file_content}

AVAILABLE ALGORITHMS:

<ALGORITHM id="estado_contable" name="Estado Contable">
Documentos contables que incluyen estados contables, balances generales, cuadros de resultados y estados de situación patrimonial. Incluyen términos como "activo", "pasivo", "patrimonio neto", "resultado del ejercicio".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha de cierre del estado contable (YYYY-MM-DD)",
        "type": "string - tipo de estado contable",
        "company": "string - nombre de la empresa",
        "fiscal_year": "string - año fiscal"
    }

FILENAME_FORMAT:
estado_contable_{company}_{fiscal_year}_{date}.{ext}
</ALGORITHM>

<ALGORITHM id="recibo_sueldo" name="Recibo de Sueldo">
Documentos de nómina que incluyen recibos de sueldo, liquidaciones de haberes, boletas de pago. Contienen términos como "sueldo", "jornal", "remuneración", "deducciones", "neto a cobrar", "período", "empleador".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha de pago (YYYY-MM-DD)",
        "period": "string - período liquidado",
        "employee": "string - nombre del empleado",
        "net_amount": "number - monto neto a cobrar",
        "employer": "string - nombre del empleador"
    }

FILENAME_FORMAT:
recibo_{employee}_{period}_{date}.{ext}
</ALGORITHM>

<ALGORITHM id="resumen_bancario" name="Resumen Bancario">
Documentos bancarios que incluyen resúmenes de cuenta, estados de cuenta, movimientos bancarios. Contienen términos como "saldo", "débito", "crédito", "resumen", "cuenta corriente", "caja de ahorro", "CBU", "CVU".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha de corte (YYYY-MM-DD)",
        "period": "string - período resumido",
        "bank": "string - nombre del banco",
        "account_type": "string - tipo de cuenta",
        "account_last4": "string - últimos 4 dígitos de la cuenta"
    }

FILENAME_FORMAT:
resumen_{bank}_{account_type}_{period}_{date}.{ext}
</ALGORITHM>

<ALGORITHM id="factura" name="Factura">
Comprobantes de compra/venta incluyendo facturas A, B, C, tickets, facturas de bienes de uso. Contienen términos como "factura", "comprobante", "gravado", "no gravado", "IVA", "CAE", "CUIT".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha de emisión (YYYY-MM-DD)",
        "type": "string - tipo de comprobante (A/B/C/ticket)",
        "issuer": "string - nombre del emisor",
        "number": "string - número de factura",
        "amount": "number - importe total (opcional)",
        "detail": "string - descripción breve del concepto"
    }

FILENAME_FORMAT:
{date}_FACTURA_{issuer}_{detail}.{ext}
</ALGORITHM>

<ALGORITHM id="prestamo" name="Préstamo">
Documentos de préstamos incluyendo liquidaciones de cuotas, estados de deuda financiera, mutuos bancarios. Contienen términos como "cuota", "préstamo", "deuda", "amortización", "interés", "prendario", "hipotecario".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha del comprobante (YYYY-MM-DD)",
        "bank": "string - nombre del banco",
        "loan_type": "string - tipo de préstamo",
        "installment": "string - número de cuota",
        "detail": "string - detalle adicional"
    }

FILENAME_FORMAT:
{date}_PRESTAMO_{bank}_{detail}.{ext}
</ALGORITHM>

<ALGORITHM id="impuesto" name="Impuesto">
Documentos impositivos incluyendo VEP, declaraciones juradas, formularios AFIP/ARCA, IIBB, tasas. Contienen términos como "DDJJ", "F931", "VEP", "impuesto", "ARCA", "período fiscal".

EXTRACTION_SCHEMA:
{
        "period": "string - período fiscal (YYYY-MM o YYYY)",
        "organism": "string - nombre del organismo (AFIP/ARCA/IIBB)",
        "tax_type": "string - tipo de impuesto o formulario",
        "detail": "string - detalle específico"
    }

FILENAME_FORMAT:
{period}_IMPUESTO_{organism}_{tax_type}_{detail}.{ext}
</ALGORITHM>

<ALGORITHM id="seguro" name="Seguro">
Documentos de seguros incluyendo pólizas, certificados de cobertura, recibos de pago de primas. Contienen términos como "póliza", "seguro", "cobertura", "aseguradora", "prima", "siniestro".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha de emisión o vigencia (YYYY-MM-DD)",
        "insurer": "string - nombre de la aseguradora",
        "insurance_type": "string - tipo de seguro",
        "insured": "string - nombre del asegurado",
        "policy_number": "string - número de póliza (opcional)"
    }

FILENAME_FORMAT:
{date}_SEGURO_{insurer}_{insurance_type}.{ext}
</ALGORITHM>

<ALGORITHM id="legal" name="Legal">
Documentos legales incluyendo contratos comerciales, escrituras, mutuos entre partes, estatutos. Contienen términos como "contrato", "escritura", "mutuo", "estatutos", "comparecen", "certifico".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha del documento (YYYY-MM-DD)",
        "doc_type": "string - tipo de documento legal",
        "parties": "string - partes intervinientes",
        "concept": "string - objeto o concepto del acuerdo"
    }

FILENAME_FORMAT:
{date}_LEGAL_{doc_type}_{parties}_{concept}.{ext}
</ALGORITHM>

<ALGORITHM id="doc_interna" name="Documento Interno">
Documentos internos de trabajo incluyendo papeles de trabajo, planillas Excel de cálculos auxiliares, borradores. Contienen términos como "ajuste", "cálculo", "borrador", "hoja de trabajo", "auxiliar".

EXTRACTION_SCHEMA:
{
        "period": "string - período o fecha (YYYY-MM)",
        "client": "string - nombre del cliente",
        "work_type": "string - tipo de trabajo",
        "detail": "string - detalle específico"
    }

FILENAME_FORMAT:
{period}_DOC-INTERNA_{client}_{work_type}_{detail}.{ext}
</ALGORITHM>

<ALGORITHM id="constancia" name="Constancia">
Documentos de constancia incluyendo inscripciones, CUIT, domicilio, certificados. Contienen términos como "constancia", "certificado", "inscripción", "CUIT", "domicilio", "tramité".

EXTRACTION_SCHEMA:
{
        "date": "string - fecha de emisión (YYYY-MM-DD)",
        "type": "string - tipo de constancia",
        "organism": "string - organismo emisor",
        "entity": "string - nombre de la empresa o persona (opcional)"
    }

FILENAME_FORMAT:
{date}_CONSTANCIA_{type}_{organism}.{ext}
</ALGORITHM>


TASK:
1. Identify which algorithm best matches this document
2. Extract information according to that algorithm's schema
3. Return the data in the exact format specified by the chosen algorithm

Output the result as JSON following the chosen algorithm's output_schema.
$prompt$::text)
)
WHERE id = 'job-manual-auto-classify';

-- Verificar que se actualizó correctamente
SELECT id, name,
    length(agent_config->>'prompt_template') as prompt_length,
    substr(agent_config->>'prompt_template', 1, 100) as prompt_preview
FROM jobs
WHERE id = 'job-manual-auto-classify';
