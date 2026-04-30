-- SQL simplificado para actualizar el modelo en todos los jobs manuales
-- Funciona en Supabase/PostgreSQL

-- Opción 1: Usar jsonb_set con sintaxis correcta de PostgreSQL
UPDATE jobs
SET agent_config = jsonb_set(
    agent_config,
    '{model,name}',
    'gemini-2.5-flash'
)
WHERE id LIKE 'job-manual-%';

-- Verificar el cambio
SELECT id,
       jsonb_extract_path_text(agent_config, '$.model.name') as model_name
FROM jobs
WHERE id LIKE 'job-manual-%';
