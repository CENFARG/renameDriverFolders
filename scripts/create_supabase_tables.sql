-- Script SQL para crear tablas en Supabase
-- =============================================
--
-- Uso:
--   1. Ir a Supabase Dashboard: https://supabase.com/dashboard
--   2. Seleccionar proyecto: uenywfvtuulcjelouork
--   3. Ir a SQL Editor
--   4. Copiar y pegar este script
--   5. Ejecutar (Run)
--
-- Tablas a crear:
--   - jobs: Configuraciones de algoritmos
--   - job_executions: Historial de ejecuciones (caja negra)

-- =============================================
-- TABLA: jobs
-- =============================================

CREATE TABLE IF NOT EXISTS jobs (
  -- Primary Key
  id VARCHAR(255) PRIMARY KEY,

  -- Job Configuration
  name VARCHAR(500) NOT NULL,
  description TEXT,

  -- Trigger Configuration
  trigger_type VARCHAR(50) NOT NULL,  -- 'manual', 'scheduled'
  schedule VARCHAR(100),  -- Cron expression: '0 8 * * *'

  -- Folder Configuration
  source_folder_id VARCHAR(500) NOT NULL,

  -- Agent Configuration
  agent_config JSONB NOT NULL,

  -- Status
  active BOOLEAN DEFAULT true,

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE jobs IS 'Configuraciones de algoritmos de renombrado';
COMMENT ON COLUMN jobs.trigger_type IS 'Tipo de trigger: manual o scheduled';
COMMENT ON COLUMN jobs.schedule IS 'Expresión cron para scheduled jobs';
COMMENT ON COLUMN jobs.source_folder_id IS 'ID de carpeta de Google Drive';
COMMENT ON COLUMN jobs.agent_config IS 'Configuración del agente IA (model, prompt, etc.)';

-- Indexes para performance
CREATE INDEX IF NOT EXISTS idx_jobs_active ON jobs(active);
CREATE INDEX IF NOT EXISTS idx_jobs_trigger_type ON jobs(trigger_type);

-- =============================================
-- TABLA: job_executions (Caja Negra)
-- =============================================

CREATE TABLE IF NOT EXISTS job_executions (
  -- Primary Key
  id VARCHAR(255) PRIMARY KEY,  -- Formato: exec-{timestamp}

  -- User Info
  user_email VARCHAR(255) NOT NULL,
  user_name VARCHAR(500),

  -- Job Info
  folder_id VARCHAR(500),
  job_type VARCHAR(100),
  job_config_id VARCHAR(255),

  -- Execution Info
  timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
  status VARCHAR(50) NOT NULL,  -- 'submitted', 'processing', 'completed', 'failed'

  -- Task Info
  task_id VARCHAR(255),

  -- Results
  details TEXT,  -- Detalles de la ejecución, errores, etc.

  -- Metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comments
COMMENT ON TABLE job_executions IS 'Historial de ejecuciones (caja negra) - Auditoría completa';
COMMENT ON COLUMN job_executions.status IS 'Estados: submitted → processing → completed/failed';
COMMENT ON COLUMN job_executions.details IS 'Detalles: cantidad de archivos, errores, etc.';

-- Indexes para performance (CRITICAL para dashboard)
CREATE INDEX IF NOT EXISTS idx_job_executions_timestamp ON job_executions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_job_executions_user_email ON job_executions(user_email);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status);
CREATE INDEX IF NOT EXISTS idx_job_executions_folder_id ON job_executions(folder_id);

-- =============================================
-- ENABLE ROW LEVEL SECURITY (Opcional)
-- =============================================

ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_executions ENABLE ROW LEVEL SECURITY;

-- Políticas (ajustar según necesidad)
-- DROP POLICY IF EXISTS "Users can view all jobs" ON jobs;
-- CREATE POLICY "Users can view all jobs" ON jobs FOR SELECT USING (true);
--
-- DROP POLICY IF EXISTS "Users can view all executions" ON job_executions;
-- CREATE POLICY "Users can view all executions" ON job_executions FOR SELECT USING (true);

-- =============================================
-- VERIFICACIÓN
-- =============================================

-- Verificar que las tablas fueron creadas
SELECT
  'jobs' as table_name,
  COUNT(*) as record_count
FROM jobs
UNION ALL
SELECT
  'job_executions' as table_name,
  COUNT(*) as record_count
FROM job_executions;
