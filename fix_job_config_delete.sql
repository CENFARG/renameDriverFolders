-- SOLUCIÓN TEMPORAL: Eliminar y recrear el job config
-- Esto hará que el API Server lo recree con el código fixed

-- Paso 1: Eliminar el job config actual
DELETE FROM jobs WHERE id = 'job-manual-auto-classify';

-- Paso 2: Verificar que se eliminó
SELECT * FROM jobs WHERE id = 'job-manual-auto-classify';

-- Paso 3: El job se recreará automáticamente la próxima vez que alguien ejecute /rename
-- porque el código del API Server tiene la lógica de auto-creación
