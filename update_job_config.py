#!/usr/bin/env python3
"""
Script para actualizar el job_config en Supabase y formatear el prompt_template con algorithms_prompt
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Conectar a Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
client = create_client(url, key)

print("=" * 60)
print("ACTUALIZAR job_config CON algorithms_prompt FORMATEADO")
print("=" * 60)
print()

# 1. Obtener el job_config actual
result = client.table('jobs').select("*").eq('id', 'job-manual-auto-classify').execute()

if not result.data:
    print("❌ ERROR: No se encontró job 'job-manual-auto-classify'")
    exit(1)

job_config = result.data[0]
print(f"✅ Job config encontrado: {job_config['name']}")
print()

# 2. Obtener todos los algorithms activos
algorithms_result = client.table('document_algorithms').select("*").eq('is_active', True).execute()
algorithms = algorithms_result.data

print(f"✅ Found {len(algorithms)} active algorithms")
for algo in algorithms:
    print(f"  - {algo['id']}: {algo['name']}")
print()

# 3. Construir algorithms_prompt
algorithm_blocks = []
for algo in algorithms:
    algorithm_blocks.append(f"""
<ALGORITHM id="{algo['id']}" name="{algo['name']}">
{algo['classification_criteria']}

EXTRACTION_SCHEMA:
{algo['output_schema']}

FILENAME_FORMAT:
{algo['filename_format']}
</ALGORITHM>
""")

algorithms_prompt = "\n".join(algorithm_blocks)

# 4. Construir prompt_template CON algorithms_prompt ya incluido
new_prompt_template = f"""Analyze the following document and determine which algorithm applies:

ORIGINAL FILE: {{original_filename}}

DOCUMENT CONTENT:
{{file_content}}

AVAILABLE ALGORITHMS:
{algorithms_prompt}

TASK:
1. Identify which algorithm best matches this document
2. Extract information according to that algorithm's schema
3. Return the data in the exact format specified by the chosen algorithm

Output the result as JSON following the chosen algorithm's output_schema.
"""

print("✅ Nuevo prompt_template creado (con algorithms_prompt formateado)")
print(f"   Length: {len(new_prompt_template)} chars")
print()

# 5. Actualizar el job_config
update_data = {
    "agent_config": job_config["agent_config"]
}
update_data["agent_config"]["prompt_template"] = new_prompt_template

print("📝 Actualizando job_config en Supabase...")
result = client.table('jobs').update(update_data).eq('id', 'job-manual-auto-classify').execute()

if result.data:
    print("✅ SUCCESS: Job config actualizado!")
    print(f"   Nuevo prompt_template length: {len(result.data[0]['agent_config']['prompt_template'])} chars")
else:
    print("❌ ERROR: No se pudo actualizar el job_config")
    exit(1)

print()
print("=" * 60)
print("NEXT STEP:")
print("=" * 60)
print("El job_config ahora tiene el prompt_template formateado con algorithms_prompt.")
print("El Worker ya debería poder procesar archivos sin el KeyError.")
print()
