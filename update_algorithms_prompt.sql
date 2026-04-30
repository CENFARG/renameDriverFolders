-- Script para actualizar el prompt_template del job job-manual-auto-classify
-- con algorithms_prompt ya formateado

-- NOTA: Este es un workaround hasta que deploemos el API Server con el fix

-- 1. Primero, ver el estado actual
SELECT id, name,
       jsonb_extract_path_text(agent_config, '$.prompt_template') as prompt_template_preview
FROM jobs
WHERE id = 'job-manual-auto-classify';

-- 2. Actualizar el prompt_template para incluir los algorithms
-- NOTA: Necesitarás actualizar esto manualmente en la UI de Supabase
-- o esperar a que deploymos el API Server con el fix

-- El fix que necesitamos es formatear el prompt_template ANTES de guardarlo
-- para que algorithms_prompt ya esté incluido y no sea un placeholder
