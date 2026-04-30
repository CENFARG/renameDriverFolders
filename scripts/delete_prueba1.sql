-- Eliminar el job de prueba obsoleto
DELETE FROM jobs WHERE id = 'prueba1';

-- Verificar que solo quedaron los jobs correctos
SELECT id, name, trigger_type, active FROM jobs ORDER BY id;
