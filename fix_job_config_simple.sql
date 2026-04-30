-- SQL CORRECTO para actualizar el prompt_template con algorithms_prompt incluido
-- Ejecutar esto en Supabase SQL Editor

-- Primero, veamos qué algorithms activos hay
SELECT id, name FROM document_algorithms WHERE is_active = true;

-- Luego, actualizamos el job config con el prompt_template formateado
-- NOTA: En este SQL uso el placeholder {algorithms_prompt} que se reemplazará dinámicamente

-- Opción 1: Actualización simple con placeholder
UPDATE jobs
SET agent_config = jsonb_set(
    agent_config,
    '{prompt_template}',
    'Analyze the following document and determine which algorithm applies:\n\nORIGINAL FILE: {original_filename}\n\nDOCUMENT CONTENT:\n{file_content}\n\nAVAILABLE ALGORITHMS:\n{algorithms_prompt}\n\nTASK:\n1. Identify which algorithm best matches this document\n2. Extract information according to that algorithm''s schema\n3. Return the data in the exact format specified by the chosen algorithm\n\nOutput the result as JSON following the chosen algorithm''s output_schema.'::text
)
WHERE id = 'job-manual-auto-classify';

-- Verificar el cambio
SELECT id,
       substring(jsonb_extract_path_text(agent_config, '$.prompt_template') from 1 for 100) as prompt_preview
FROM jobs
WHERE id = 'job-manual-auto-classify';
