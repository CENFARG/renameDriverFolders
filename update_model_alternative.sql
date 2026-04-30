-- Si jsonb_set no funciona, intentar con esta alternativa:

-- Opción 2: Actualizar usando concatenación de JSONB
UPDATE jobs
SET agent_config = agent_config || '{"model": {"name": "gemini-2.5-flash"}}'
WHERE id LIKE 'job-manual-%';

-- Verificar
SELECT id,
       jsonb_extract_path_text(agent_config, '$.model.name') as model_name
FROM jobs
WHERE id LIKE 'job-manual-%';
