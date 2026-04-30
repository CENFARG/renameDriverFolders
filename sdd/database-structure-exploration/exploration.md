# Exploration: Estructura Actual de la Base de Datos

**Fecha**: 2026-04-20
**Objetivo**: Entender la estructura actual de las tablas `jobs` y `document_algorithms` en Supabase, sus diferencias, relación y problemas de escalabilidad.

---

## Current State

### Tabla `jobs`

**Propósito**: Configuraciones de EJECUCIÓN de renombrado (manual o programado)

**Campos principales:**
- `id` (VARCHAR255): PK - ej: "job-manual-auto-classify"
- `name` (VARCHAR500): Nombre descriptivo
- `description` (TEXT): Descripción opcional
- `trigger_type` (VARCHAR50): 'manual' o 'scheduled'
- `schedule` (VARCHAR100): Expresión cron (solo para scheduled) - ej: "0 8 * * *"
- `source_folder_id` (VARCHAR500): ID de carpeta Google Drive o "DYNAMIC"
- `target_folder_names` (TEXT[]): Lista de carpetas objetivo - ej: ["*"] o ["doc de respaldo"]
- `agent_config` (JSONB): Configuración del agente IA
- `active` (BOOLEAN): Estado del job
- `created_at`, `updated_at`: Timestamps

**Estructura de `agent_config` en jobs:**
```json
{
  "model": {
    "name": "gemini-2.5-flash",
    "temperature": 0.1,
    "max_tokens": 4096
  },
  "instructions": "Analiza el documento. Si es factura, usa TIPO=FACTURA...",
  "prompt_template": "Analiza: {content}. Formato: YYYY-MM-DD_FACTURA_EMISOR_DETALLE...",
  "filename_format": "{date}_FACTURA_{issuer}_{detail}"
}
```

### Tabla `document_algorithms`

**Propósito**: REGLAS DE CLASIFICACIÓN de tipos de documentos (patrones de renombrado)

**Campos principales:**
- `id` (VARCHAR255): PK - ej: "estado_contable", "recibo_sueldo"
- `name` (VARCHAR500): Nombre del algoritmo
- `description` (TEXT): Descripción
- `classification_criteria` (TEXT): Criterios para identificar si un documento coincide con este algoritmo
- `extraction_prompt` (TEXT): Prompt para extraer datos específicos del documento
- `output_schema` (JSONB): Schema de salida esperado (campos a extraer)
- `filename_format` (VARCHAR500): Formato de nombre de archivo
- `is_active` (BOOLEAN): Estado del algoritmo
- `created_at`, `updated_at`: Timestamps

**Ejemplo de `output_schema`:**
```json
{
  "date": "string - fecha del documento YYYY-MM-DD",
  "type": "string - tipo de estado contable",
  "company": "string - nombre de la empresa",
  "fiscal_year": "string - año fiscal"
}
```

---

## Affected Areas

### services/api-server/src/main.py
- **Líneas 100-102**: Inicialización de `db_manager` (tabla jobs) y `algorithms_manager` (tabla document_algorithms)
- **Líneas 729-748**: Auto-classify carga TODOS los algorithms activos y los inyecta en el prompt
- **Líneas 753-812**: Creación del job config con `algorithms_prompt` inyectado
- **Líneas 1098-1158**: Endpoints CRUD operan en ambas tablas según el tipo de job

### services/worker-renombrador/src/main.py
- **Líneas 106-111**: Inicializa solo `db_manager` (tabla jobs) - NO accede a document_algorithms
- **Líneas 332-349**: `load_job_config()` carga jobs desde DB
- **Líneas 547-550**: Usa `job_config["agent_config"]["prompt_template"]`
- **Líneas 681-690**: Usa `job_config["agent_config"]["filename_format"]`

### packages/core-renombrador/src/core_renombrador/agent_factory.py
- **Líneas 65-174**: `create_agent_from_job_config()` procesa `agent_config` de jobs
- **Líneas 87-111**: Extrae config del modelo desde `agent_config.model`
- **Líneas 119-163**: Construye agent params desde `agent_config`
- **Líneas 152-163**: Usa `output_schema` si está definido

---

## Relationship Between Tables

### Confusión de Conceptos

**PROBLEMA**: Hay DOS tipos de "algoritmos" que NO están claramente diferenciados:

1. **Scheduled Jobs** (en tabla `jobs`):
   - Configuraciones de ejecución automática programada
   - Ejemplo: "Todos los días a las 8AM renombrar archivos en carpeta X"
   - Tiene `trigger_type='scheduled'` y `schedule` (cron)
   - Tiene `source_folder_id` específico

2. **Classification Algorithms** (en tabla `document_algorithms`):
   - Patrones de clasificación de tipos de documentos
   - Ejemplo: "estado_contable", "recibo_sueldo", "resumen_bancario"
   - Define cómo RENOMBRAR un tipo específico de documento
   - NO tiene `source_folder_id` ni `schedule`

### Cómo Se Relacionan

**En el diseño de auto-classify:**
- Un JOB (ej: "job-manual-auto-classify") carga TODOS los algorithms activos
- Los algorithms se INYECTAN en el prompt de IA con etiquetas XML
- La IA decide cuál algorithm aplicar según el contenido del documento
- La IA usa el `output_schema` y `filename_format` del algorithm seleccionado

**Ejemplo:**
```python
# API Server carga algorithms
all_algorithms = algorithms_manager.find("is_active", True)

# Construye prompt con XML
for algo in all_algorithms:
    algorithm_blocks.append(f"""
<ALGORITHM id="{algo['id']}" name="{algo['name']}">
{algo['classification_criteria']}

EXTRACTION_SCHEMA:
{algo['output_schema']}

FILENAME_FORMAT:
{algo['filename_format']}
</ALGORITHM>
""")

# Crea job config con algorithms inyectados
auto_classify_config = {
    "id": "job-manual-auto-classify",
    "agent_config": {
        "instructions": f"AVAILABLE ALGORITHMS:\n{algorithms_prompt}\n...",
        ...
    }
}
```

**El Worker:**
- NO lee `document_algorithms` directamente
- Recibe el job config ya construido con los algorithms inyectados
- Ejecuta el prompt que incluye la lógica de clasificación

---

## Escalability Problems

### 1. **Redundancia de Información**

**Problema**: La tabla `jobs` tiene un campo `target_folder_names` que está en conflicto con el diseño actual.

**Estado actual:**
- `target_folder_names` en jobs: ¿Para qué sirve si `source_folder_id` ya define la carpeta?
- En document_algorithms: NO tiene `target_folder_names` (correcto, solo define patrones)

**Confusión:**
- Si `target_folder_names=["*"]`, significa "todas las carpetas"
- Si `target_folder_names=["doc de respaldo"]`, significa "solo carpets con ese nombre"
- Pero en document_algorithms no existe este campo

**Evidencia en código:**
```python
# worker-renombrador/main.py line 418
target_folder_names = job_config.get("target_folder_names", ["*"])
```

El Worker usa `target_folder_names` para filtrar qué carpetas procesar.

### 2. **Duplicación de Configuración**

**Problema**: La tabla `jobs` puede contener configuraciones DUPLICADAS de `document_algorithms`.

**Ejemplo:**
- Un algorithm en `document_algorithms`: "estado_contable" con su `filename_format`
- Un job en `jobs` con `agent_config.filename_format` con el MISMO formato

**Riesgo:**
- Si se actualiza el algorithm, ¿se actualiza también el job?
- ¿Cuál es la fuente de verdad?

**Evidencia en código:**
```python
# api-server/main.py lines 153-204
diego_algorithms = [
    {
        "id": "facturas-digitales",
        "agent_config": {
            "filename_format": "{date}_FACTURA_{issuer}_{detail}"
        }
    },
    ...
]
```

Esto crea jobs DUPLICADOS en la tabla jobs cuando ya existen algorithms.

### 3. **Falta de Normalización**

**Problema**: No hay una relación foreign key entre jobs y document_algorithms.

**Estado actual:**
- Jobs puede o no "consumir" algorithms
- No hay campo `algorithm_id` en jobs
- No hay forma de saber qué algorithms usa un job

**Consecuencia:**
- Si eliminas un algorithm, los jobs que lo usan se rompen silenciosamente
- No hay auditoría de dependencias

### 4. **target_folder_names vs source_folder_id**

**Problema**: Semántica confusa entre estos dos campos.

**source_folder_id:**
- ID de carpeta Google Drive
- Puede ser "DYNAMIC" (se define en runtime)
- Define la carpeta RAÍZ a procesar

**target_folder_names:**
- Lista de nombres de carpetas
- Ej: ["*"] o ["doc de respaldo"]
- ¿Es la carpeta de destino o criterio de búsqueda?

**Evidencia en drive_handler.py:**
```python
# lines 43-75
def find_target_folders_recursively(self, start_folder_id: str) -> list:
    # Busca carpetas con nombre en self.target_folder_names
```

El método busca carpetas POR NOMBRE dentro de `start_folder_id`. Esto sugiere que:
- `source_folder_id` = carpeta raíz de búsqueda
- `target_folder_names` = criterio de filtrado de subcarpetas

**Pero esta lógica no está documentada y es confusa.**

---

## Differences in agent_config

### En tabla `jobs`:

```json
{
  "model": {
    "name": "gemini-2.5-flash",
    "temperature": 0.1,
    "max_tokens": 4096
  },
  "instructions": "Analiza el documento...",
  "prompt_template": "Analiza: {content}...",
  "filename_format": "{date}_FACTURA_{issuer}_{detail}"
}
```

**Propósito**: Configura cómo el agente IA debe procesar el documento.

### En tabla `document_algorithms`:

NO existe `agent_config`. En su lugar tiene campos específicos:
- `classification_criteria`: Reglas para identificar si un doc coincide
- `extraction_prompt`: Prompt para extraer datos específicos
- `output_schema`: Schema de salida JSON
- `filename_format`: Formato de nombre

**Propósito**: Define un PATRÓN de renombrado para un tipo de documento.

---

## Data Flow

### Flujo Actual con Auto-Classify:

```
1. Usuario ejecuta /rename en carpeta X
   ↓
2. API Server crea job execution en job_executions
   ↓
3. API Server carga TODOS los algorithms activos de document_algorithms
   ↓
4. API Server construye job config con algorithms inyectados en XML
   ↓
5. API Server envía Cloud Task al Worker con job config
   ↓
6. Worker recibe job config (ya incluye algorithms)
   ↓
7. Worker ejecuta prompt con lógica de clasificación
   ↓
8. IA selecciona algorithm apropiado y extrae datos según su schema
   ↓
9. Worker renombra archivo con formato del algorithm seleccionado
```

**Problema**: El Worker no tiene visibilidad de document_algorithms, depende del API Server para inyectarlos.

---

## Recommendation

**Clarificar los conceptos:**

1. **Jobs** = Configuraciones de EJECUCIÓN (cuándo y dónde correr)
   - Manual (trigger by user)
   - Scheduled (trigger by cron)
   - Tiene `source_folder_id` y `target_folder_names`

2. **Algorithms** = Patrones de CLASIFICACIÓN (cómo renombrar)
   - Define `filename_format` y `output_schema`
   - Define criterios de identificación
   - NO tiene ni necesita `source_folder_id`

3. **Relación**: Un job USE uno o más algorithms
   - Job manual-auto-classify → usa TODOS los algorithms activos
   - Job scheduled específico → podría usar UN algorithm específico

---

## Risks

1. **Alto**: Eliminar un algorithm activo rompe el auto-classify sin advertencia
2. **Medio**: Modificar un algorithm no actualiza jobs que lo referencian (si existieran)
3. **Medio**: `target_folder_names` es ambiguo - puede significar "carpeta destino" o "filtro de búsqueda"
4. **Alto**: No hay forma de auditar qué algorithms está usando un job en producción
5. **Bajo**: El Worker no valida que los algorithms inyectados existan en document_algorithms

---

## Ready for Proposal

**YES** - La estructura actual es comprensible pero tiene problemas de normalización y claridad que deben ser abordados.

**Puntos aclarar antes de proponer cambios:**
1. ¿Qué significa exactamente `target_folder_names`? ¿Carpeta de destino o filtro de búsqueda?
2. ¿Un job puede usar SOLO un subset de algorithms (no todos)?
3. ¿Los scheduled jobs usan algorithms o tienen su propia lógica de renombrado?
4. ¿Por qué el código `seed_default_algorithms()` crea jobs duplicados en `jobs` cuando ya están en `document_algorithms`?

---

## Archivos Clave

- `scripts/create_supabase_tables.sql` - Schema de jobs y job_executions
- `scripts/create_document_algorithms.sql` - Schema de document_algorithms + datos semilla
- `services/api-server/src/main.py` - Lógica de auto-classify y CRUD de jobs/algorithms
- `services/worker-renombrador/src/main.py` - Procesamiento de jobs (no accede a algorithms directamente)
- `packages/core-renombrador/src/core_renombrador/agent_factory.py` - Creación de agentes desde job config
