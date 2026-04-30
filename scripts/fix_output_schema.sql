-- Fix output_schema for job-manual-auto-classify
-- El output_schema estaba NULL, causando que Agno devuelva string plano en lugar de Pydantic model

UPDATE jobs
SET agent_config = jsonb_set(
    agent_config,
    '{output_schema}',
    to_jsonb($prompt${
  "algorithm_id": "string - ID del algoritmo seleccionado (estado_contable, recibo_sueldo, resumen_bancario, factura, prestamo, impuesto, seguro, legal, doc_interna, constancia)",
  "date": "string - fecha del documento (YYYY-MM-DD, opcional para algunos algoritmos)",
  "period": "string - período fiscal o de referencia (YYYY-MM o YYYY, opcional)",
  "type": "string - tipo de documento (opcional, varia por algoritmo)",
  "company": "string - nombre de la empresa (opcional)",
  "fiscal_year": "string - año fiscal (opcional)",
  "employee": "string - nombre del empleado (opcional)",
  "employer": "string - nombre del empleador (opcional)",
  "net_amount": "number - monto neto (opcional)",
  "bank": "string - nombre del banco (opcional)",
  "account_type": "string - tipo de cuenta bancaria (opcional)",
  "account_last4": "string - últimos 4 dígitos de cuenta (opcional)",
  "issuer": "string - nombre del emisor (opcional)",
  "number": "string - número de comprobante (opcional)",
  "amount": "number - importe total (opcional)",
  "detail": "string - descripción breve o detalle adicional (opcional)",
  "loan_type": "string - tipo de préstamo (opcional)",
  "installment": "string - número de cuota (opcional)",
  "organism": "string - nombre del organismo (opcional)",
  "tax_type": "string - tipo de impuesto (opcional)",
  "insurer": "string - nombre de la aseguradora (opcional)",
  "insurance_type": "string - tipo de seguro (opcional)",
  "insured": "string - nombre del asegurado (opcional)",
  "policy_number": "string - número de póliza (opcional)",
  "doc_type": "string - tipo de documento legal (opcional)",
  "parties": "string - partes intervinientes (opcional)",
  "concept": "string - objeto o concepto del acuerdo (opcional)",
  "client": "string - nombre del cliente (opcional)",
  "work_type": "string - tipo de trabajo (opcional)",
  "entity": "string - nombre de la entidad o persona (opcional)"
}$prompt$::text)
)
WHERE id = 'job-manual-auto-classify';

-- Verificar que se actualizó correctamente
SELECT
    id,
    agent_config->'output_schema'->'algorithm_id' as has_algorithm_id,
    agent_config->'output_schema'->'date' as has_date_field,
    jsonb_typeof(agent_config->'output_schema') as schema_type
FROM jobs
WHERE id = 'job-manual-auto-classify';
