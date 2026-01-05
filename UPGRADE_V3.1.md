# Upgrade V3.1: OCR, Dynamic Config & Multi-Job Support

Este documento detalla las mejoras implementadas en el sistema `renameDriverFolders` para soportar OCR, configuración dinámica y múltiples trabajos.

## 🎯 Características Nuevas

### 1. **OCR para Imágenes y PDFs Escaneados**
- Soporte para extraer texto de imágenes (JPG, PNG, GIF, BMP, TIFF)
- Detección automática de PDFs escaneados (sin texto)
- Conversión de PDFs a imágenes + OCR si es necesario
- Usa Google Cloud Vision API

**Costo**: 
- ⚠️ Google Cloud Vision tiene un **tier gratuito de 1,000 unidades/mes**
- Después del tier gratuito, es **pago por uso**
- Cada imagen procesada = 1 unidad
- [Más información sobre precios](https://cloud.google.com/vision/pricing)

### 2. **Configuración Híbrida**
El nuevo `ConfigManager` soporta múltiples fuentes de configuración con prioridad:

1. **Variables de Entorno** (máxima prioridad) - para overrides
2. **Base de Datos** (Supabase) - para configuración dinámica
3. **Archivo `config.json`** (fallback) - para desarrollo local

**Ejemplo de uso:**
```python
# Configuración desde env var
export RENOMBRADOR_GEMINI_MODEL_NAME="gemini-2.0-flash-exp"

# O desde base de datos (tabla app_config)
# key: "gemini.model_name", value: "gemini-2.0-flash-exp"

# O desde config.json
# {"gemini": {"model_name": "gemini-2.0-flash-exp"}}
```

### 3. **DatabaseManager con Supabase**
Soporte para dos modos de persistencia:

- **Modo JSON** (desarrollo local): simple archivo JSON
- **Modo Supabase** (producción): base de datos PostgreSQL remota

**Configuración:**
```python
# JSON mode (default)
db = DatabaseManager(file_manager=fm, db_path="data/db.json")

# Supabase mode
db = DatabaseManager(
    use_supabase=True,
    supabase_url="https://xxx.supabase.co",
    supabase_key="your-key",
    table_name="app_config"
)
```

**Variables de entorno:**
```bash
SUPABASE_URL="https://xxx.supabase.co"
SUPABASE_KEY="your-anon-key"
```

### 4. **Multi-Job Support**
Permite procesar múltiples carpetas con configuraciones diferentes:

**Estructura de un Job:**
```json
{
  "id": "job-001",
  "name": "Coutinholla - Anual",
  "active": true,
  "trigger_type": "scheduled",
  "schedule": "0 2 * * *",
  "source_folder_id": "FOLDER_ID",
  "target_folder_names": ["doc de respaldo anual"],
  "agent_config": {
    "model": {
      "name": "gemini-2.0-flash-exp",
      "temperature": 0.7,
      "max_tokens": 8192
    },
    "instructions": "...",
    "prompt_template": "...",
    "filename_format": "DOCPROCESADO_{date}_{keywords}.{ext}"
  }
}
```

Ver `config/jobs.example.json` para ejemplos completos.

## 📦 Nuevas Dependencias

Las siguientes dependencias se agregaron a `packages/core-renombrador/pyproject.toml`:

```toml
"google-cloud-vision>=3.4.0"  # OCR
"pdf2image>=1.16.0"           # PDF to image conversion
"Pillow>=10.0.0"              # Image processing
"supabase>=2.0.0"             # Database support
```

**Dependencias del sistema (Docker):**
- `poppler-utils` (para pdf2image)

## 🔧 Configuración Inicial

### 1. Habilitar Google Cloud Vision API

```bash
gcloud services enable vision.googleapis.com --project=YOUR_PROJECT_ID
```

### 2. Configurar Supabase (Opcional)

Si quieres usar Supabase en lugar de JSON local:

1. Crear proyecto en [supabase.com](https://supabase.com)
2. Crear tabla `app_config`:
   ```sql
   CREATE TABLE app_config (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     key TEXT NOT NULL UNIQUE,
     value JSONB NOT NULL,
     description TEXT,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. Crear tabla `jobs`:
   ```sql
   CREATE TABLE jobs (
     id TEXT PRIMARY KEY,
     name TEXT NOT NULL,
     description TEXT,
     active BOOLEAN DEFAULT true,
     trigger_type TEXT NOT NULL,
     schedule TEXT,
     source_folder_id TEXT NOT NULL,
     target_folder_names JSONB NOT NULL,
     agent_config JSONB NOT NULL,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

4. Configurar variables de entorno:
   ```bash
   export SUPABASE_URL="https://xxx.supabase.co"
   export SUPABASE_KEY="your-anon-key"
   ```

### 3. Configurar Jobs

1. Copiar el template:
   ```bash
   cp config/jobs.example.json config/jobs.json
   ```

2. Editar `config/jobs.json` con tus carpetas y configuraciones

3. (Opcional) Cargar jobs en Supabase:
   ```python
   from core_renombrador import DatabaseManager, FileManager
   import json
   
   fm = FileManager(...)
   db = DatabaseManager(use_supabase=True, table_name="jobs")
   
   with open("config/jobs.json") as f:
       jobs_config = json.load(f)
   
   for job in jobs_config["jobs"]:
       db.insert(job)
   ```

## 🎯 Uso

### ContentExtractor con OCR

```python
from core_renombrador import ContentExtractor

# Con OCR habilitado (default)
extractor = ContentExtractor(enable_ocr=True, min_text_threshold=100)

# Procesar PDF (automáticamente usa OCR si es necesario)
text = extractor.get_content("document.pdf", pdf_bytes)

# Procesar imagen
text = extractor.get_content("invoice.jpg", jpg_bytes)

# Con índice de confianza (futuro)
text, confidence = extractor.get_content_with_confidence("scan.pdf", pdf_bytes)
```

### ConfigManager Híbrido

```python
from core_renombrador import ConfigManager, DatabaseManager, FileManager

fm = FileManager(...)
db = DatabaseManager(use_supabase=True)
config = ConfigManager(
    config_path="config.json",
    database_manager=db,
    env_prefix="RENOMBRADOR_"
)

# Obtener configuración (prioridad: env > db > file)
model_name = config.get_setting("gemini.model_name", default="gemini-2.0-flash-exp")

# Recargar config desde DB sin reiniciar
config.reload_db_config()
```

## 🚀 Despliegue

### Actualizar Worker con OCR

El `Dockerfile` del worker ahora incluye `poppler-utils`:

```bash
cd services/worker-renombrador
docker build -t worker-renombrador:latest .
```

### Variables de Entorno Requeridas

```bash
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GCP_PROJECT_ID=your-project-id

# Gemini
GEMINI_API_KEY=your-api-key

# Supabase (opcional)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key

# Config overrides (opcional)
RENOMBRADOR_GEMINI_MODEL_NAME=gemini-2.0-flash-exp
RENOMBRADOR_GEMINI_TEMPERATURE=0.7
```

## 📝 Tareas Pendientes

- [ ] Implementar "verifiability index" (índice de confianza OCR vs IA)
- [ ] Optimizar prompts para reducir uso de tokens
- [ ] Crear scripts de deployment automatizados (.sh)
- [ ] Implementar CI/CD con GitHub Actions
- [ ] Refactorizar logger para Cloud Logging con JSON estructurado
- [ ] Tests unitarios para OCR y multi-job
- [ ] Documentación de API del worker

## 🔗 Referencias

- [Google Cloud Vision Pricing](https://cloud.google.com/vision/pricing)
- [Supabase Documentation](https://supabase.com/docs)
- [Agno Framework](https://github.com/agno-agi/agno) (agent config format)
- [Arquitectura V3](../.context/ARQUITECTURA_Y_PLAN_V3.md)

---

**Versión**: 3.1.0  
**Fecha**: 2025-12-05  
**Autor**: amBotHs + CENF
