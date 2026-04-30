-- ============================================================
-- LIMPIEZA TOTAL: Borrar todos los jobs manuales viejos
-- ============================================================

-- Mostrar todos los jobs manuales antes de borrar
SELECT id, name, target_folder_names, trigger_type 
FROM jobs 
WHERE id LIKE 'job-manual-%'
ORDER BY id;

-- Borrar TODOS los jobs manuales
DELETE FROM jobs WHERE id LIKE 'job-manual-%';

-- Verificar que se borraron
SELECT id, name, target_folder_names, trigger_type 
FROM jobs 
WHERE id LIKE 'job-manual-%';
