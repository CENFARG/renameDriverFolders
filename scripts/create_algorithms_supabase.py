#!/usr/bin/env python3
"""
Crear tabla e insertar algoritmos en Supabase usando REST API
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuración
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://uenywfvtuulcjelouork.supabase.co")
# Usar service_role key para operaciones admin (sin ROW LEVEL SECURITY)
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

def create_table_via_rpc():
    """Crear tabla usando RPC call (permite SQL arbitrario)"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    sql = """
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

CREATE INDEX IF NOT EXISTS idx_document_algorithms_active
ON document_algorithms(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_document_algorithms_id
ON document_algorithms(id);
"""

    payload = {"sql": sql}

    print("Creando tabla document_algorithms...")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print("OK: Tabla creada exitosamente")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print(f"ERROR: {response.status_code}")
        print(response.text)
        return False

def insert_algorithm_via_rpc(algorithm_data):
    """Insertar algoritmo usando RPC"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    sql = """
INSERT INTO document_algorithms (
    id, name, description, classification_criteria,
    extraction_prompt, output_schema, filename_format, is_active
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, true
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    classification_criteria = EXCLUDED.classification_criteria,
    extraction_prompt = EXCLUDED.extraction_prompt,
    output_schema = EXCLUDED.output_schema,
    filename_format = EXCLUDED.filename_format,
    updated_at = NOW();
"""

    payload = {
        "sql": sql,
        "params": [
            algorithm_data["id"],
            algorithm_data["name"],
            algorithm_data["description"],
            algorithm_data["classification_criteria"],
            algorithm_data["extraction_prompt"],
            algorithm_data["output_schema"],
            algorithm_data["filename_format"]
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print(f"OK: Algoritmo '{algorithm_data['id']}' insertado")
        return True
    else:
        print(f"ERROR insertando '{algorithm_data['id']}': {response.status_code}")
        if response.text:
            print(f"  {response.text[:200]}")
        return False

if __name__ == "__main__":
    print("=== Crear tabla de algoritmos ===")
    if create_table_via_rpc():
        print("\n=== Insertar algoritmos ===")

        # Definir algoritmos
        algorithms = [
            {
                "id": "factura_rg830",
                "name": "Facturas RG 830",
                "description": "Para facturas de servicios publicos con resolucion general 830",
                "classification_criteria": "Eres un clasificador experto en documentos contables argentinos. Tu tarea es analizar si el documento ES una factura de servicios publicos con resolucion general 830.",
                "extraction_prompt": "Eres un clasificador experto en documentos contables argentinos. Tu tarea es analizar si el documento ES una factura de servicios publicos con resolucion general 830.",
                "output_schema": '{"servicio": "string", "tipo_factura": "string", "periodo": "string", "cuit_emisor": "string", "numero_factura": "string", "fecha_emision": "string", "importe": "string"}',
                "filename_format": "{fecha_emision}_{servicio}_{tipo_factura}_{numero_factura}.{ext}"
            },
            {
                "id": "recibo_sueldo",
                "name": "Recibos de Sueldo",
                "description": "Para recibos de haberes, liquidaciones y pagos de nomina",
                "classification_criteria": "Eres un clasificador experto en documentos de recursos humanos argentinos. Tu tarea es analizar si el documento ES un recibo de sueldo, liquidacion de haberes o comprobante de pago de nomina.",
                "extraction_prompt": "Eres un clasificador experto en documentos de recursos humanos argentinos. Tu tarea es analizar si el documento ES un recibo de sueldo, liquidacion de haberes o comprobante de pago de nomina.",
                "output_schema": '{"tipo_documento": "string", "periodo_pago": "string", "empleado": "string", "cuil": "string", "empleador": "string", "cuit_empleador": "string", "monto_neto": "string"}',
                "filename_format": "{periodo_pago}_{tipo_documento}_{empleado}.{ext}"
            },
            {
                "id": "resumen_bancario",
                "name": "Resumenes Bancarios",
                "description": "Para resumenes de cuenta, extractos y movimientos bancarios",
                "classification_criteria": "Eres un clasificador experto en documentos bancarios argentinos. Tu tarea es analizar si el documento ES un resumen de cuenta, extracto, estado de cuenta o movimiento bancario.",
                "extraction_prompt": "Eres un clasificador experto en documentos bancarios argentinos. Tu tarea es analizar si el documento ES un resumen de cuenta, extracto, estado de cuenta o movimiento bancario.",
                "output_schema": '{"banco": "string", "tipo_documento": "string", "periodo_corte": "string", "tipo_cuenta": "string", "saldo_final": "string"}',
                "filename_format": "{periodo_corte}_{banco}_{tipo_documento}.{ext}"
            },
            {
                "id": "estado_contable",
                "name": "Estados Contables",
                "description": "Para balances generales, estados de resultados y estados patrimoniales",
                "classification_criteria": "Eres un clasificador experto en informes contables. Tu tarea es analizar si el documento ES un estado contable formal (balance general, estado de resultados, estado patrimonial).",
                "extraction_prompt": "Eres un clasificador experto en informes contables. Tu tarea es analizar si el documento ES un estado contable formal (balance general, estado de resultados, estado patrimonial).",
                "output_schema": '{"tipo_informe": "string", "empresa": "string", "ejercicio": "string", "fecha_cierre": "string", "resultado": "string"}',
                "filename_format": "{fecha_cierre}_{tipo_informe}_{empresa}.{ext}"
            },
            {
                "id": "contrato",
                "name": "Contratos y Acuerdos",
                "description": "Para contratos de alquiler, servicios, venta, compra y acuerdos comerciales",
                "classification_criteria": "Eres un clasificador experto en documentos legales y contractuales. Tu tarea es analizar si el documento ES un contrato, acuerdo o documento legal vinculante.",
                "extraction_prompt": "Eres un clasificador experto en documentos legales y contractuales. Tu tarea es analizar si el documento ES un contrato, acuerdo o documento legal vinculante.",
                "output_schema": '{"tipo_contrato": "string", "fecha_inicio": "string", "monto": "string", "empresa": "string"}',
                "filename_format": "{fecha_inicio}_{tipo_contrato}_{empresa}.{ext}"
            },
            {
                "id": "generic",
                "name": "Generico - Deteccion Automatica",
                "description": "Algoritmo por defecto para documentos que no coinciden con ninguna categoria especifica",
                "classification_criteria": "Eres un clasificador experto en documentos generales. Tu tarea es analizar el documento y extraer informacion basica para renombrado automatico.",
                "extraction_prompt": "Eres un clasificador experto en documentos generales. Tu tarea es analizar el documento y extraer informacion basica para renombrado automatico.",
                "output_schema": '{"date": "string", "type": "string", "keywords": ["string"], "entity": "string", "concept": "string"}',
                "filename_format": "{date}_{type}_{entity}_{concept}.{ext}"
            }
        ]

        for algo in algorithms:
            insert_algorithm_via_rpc(algo)

        print("\n=== Verificacion ===")
        verify_url = f"{SUPABASE_URL}/rest/v1/document_algorithms?select=id,name,is_active&order=created_at"
        verify_response = requests.get(verify_url, headers=headers)
        if verify_response.status_code == 200:
            data = verify_response.json()
            print(f"\nAlgoritmos en base de datos: {len(data)}")
            for algo in data:
                print(f"  - {algo['id']}: {algo['name']} (activo: {algo['is_active']})")
