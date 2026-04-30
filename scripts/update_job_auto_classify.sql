-- ACTUALIZAR job-manual-auto-classify con prompt completo y schemas
-- Usa to_jsonb() con cast explícito a text

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
    substr(agent_config->>'prompt_template', 1, 100) as prompt_preview
FROM jobs
WHERE id = 'job-manual-auto-classify';
