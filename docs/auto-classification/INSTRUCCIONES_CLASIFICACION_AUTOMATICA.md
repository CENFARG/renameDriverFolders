# 📋 IMPLEMENTACIÓN: Clasificación Automática de Documentos
# ===================================================================
#
# Este documento explica cómo implementar la arquitectura de clasificación
# automática con múltiples algoritmos específicos.
#
# Fecha: 14 de Marzo, 2026
# ===================================================================

## 🎯 Objetivo

Implementar un sistema donde la IA clasifique AUTOMÁTICAMENTE cada documento
y aplique el algoritmo correcto según su tipo, SIN intervención del usuario.

## 📊 Arquitectura a Implementar

### Flujo Actual (SIN clasificación automática):
```
Usuario → Selecciona carpeta
        ↓
Usuario selecciona ALGORITMO (ej: "Genérico")
        ↓
TODOS los archivos se procesan con ESE algoritmo
        ↓
Problema: Una factura RG 830 no se renombra bien con algoritmo genérico
```

### Flujo Propuesto (CON clasificación automática):
```
Usuario → Selecciona carpeta
        ↓
Sistema tiene MULTIPLES algoritmos configurados
        ↓
Por CADA documento en la carpeta:
  1. IA clasifica: "Esto es una Factura RG 830"
  2. Sistema busca algoritmo: factura_rg830
  3. IA usa instrucciones específicas de RG 830
  4. Renombra con formato de RG 830
        ↓
Documento siguiente:
  1. IA clasifica: "Esto es un Recibo de Sueldo"
  2. Sistema busca algoritmo: recibo_sueldo
  3. IA usa instrucciones específicas de Recibos
  4. Renombra con formato de Recibos
```

---

## 🗄️ PASO 1: Crear Tabla de Algoritmos en Supabase

### 1.1 Ir a Supabase SQL Editor:
URL: https://supabase.com/dashboard/project/uenywfvtuulcjelouork/sql/new

### 1.2 Ejecutar los scripts en orden (CRITICO):

**NOTA IMPORTANTE:** Ejecutar en este orden EXACTO, uno a la vez:

**Paso 1:** Abrir `scripts/create_algorithms_table.sql`
- Copiar y ejecutar en el SQL Editor
- Verifica que muestra `table_exists = 1`

**Paso 2:** Abrir `scripts/insert_algorithms_test.sql`
- Copiar y ejecutar en el SQL Editor
- Verifica que se insertó el algoritmo `factura_rg830`

**Paso 3:** Abrir `scripts/insert_remaining_algorithms.sql`
- Copiar y ejecutar en el SQL Editor
- Debería insertar 5 algoritmos más

**Paso 4:** Verificar que todos los algoritmos se crearon:
```sql
SELECT id, name, is_active
FROM document_algorithms
ORDER BY created_at;
```

Deberías ver 6 algoritmos listados:
1. **factura_rg830** - Facturas de servicios públicos
2. **recibo_sueldo** - Recibos de sueldo y nómina
3. **resumen_bancario** - Resúmenes y extractos bancarios
4. **estado_contable** - Estados contables y balances
5. **contrato** - Contratos y acuerdos comerciales
6. **generic** - Algoritmo por defecto (fallback)

---

## 🔧 PASO 2: Modificar el Worker

### 2.1 Copiar el worker:
```bash
cd services/worker-renombrador/src
cp main.py main_backup.py
```

### 2.2 Agregar las nuevas funciones:

Al final del archivo (antes de las definiciones de endpoints), agregar:

1. `load_document_algorithms(db_manager)`
2. `classify_document(file_name, file_content, algorithms)`
3. `process_folder_files_with_auto_classify(...)`

Estas funciones están en: `AUTO_CLASSIFICATION_PATCH.md`

### 2.3 Modificar `process_job()`:

Buscar esta función (línea ~246) y agregar:

```python
def process_job(
    job_config: Dict[str, Any],
    folder_id: Optional[str] = None,
    credentials = None
) -> Dict[str, Any]:
    """
    Process a single job.
    Procesa un solo job.
    """
    job_id = job_config.get("id")
    job_name = job_config.get("name")

    logger.info(f"Starting job '{job_name}' (ID: {job_id})")

    # ============================================
    # NUEVO: Cargar algoritmos de clasificación
    # ============================================
    logger.info("🔍 Loading document algorithms for automatic classification...")
    algorithms = load_document_algorithms(db_manager)
    logger.info(f"✅ Loaded {len(algorithms)} algorithms")

    # ... resto del código existente ...
```

### 2.4 Modificar el loop de carpetas:

Dentro de `process_job()`, buscar donde se llama a `process_folder_files()`:

```python
# Buscar esta sección (línea ~304):
for folder in folders_to_process:
    folder_stats = process_folder_files(
        drive_service=drive_service,
        folder_id=folder,
        agent=agent,
        job_config=job_config
    )
```

Y cambiarla a:

```python
for folder in folders_to_process:
    folder_stats = process_folder_files_with_auto_classify(
        drive_service=drive_service,
        folder_id=folder,
        agent=agent,
        job_config=job_config,
        algorithms=algorithms  # <--- AGREGAR ESTE PARÁMETRO
    )
```

---

## 🚀 PASO 3: Deployar el Worker

### 3.1 Crear Dockerfile:
```bash
cd services/worker-renombrador
# Usar Dockerfile.build existente
```

### 3.2 Build y Deploy:
```bash
cd /c/Dropbox/DOC.RECA/06-Software/renameDriverFolders

gcloud builds submit \
  --config services/worker-renombrador/cloudbuild.yaml \
  --project cloud-functions-474716 \
  .
```

### 3.3 Verificar deployment:
```bash
gcloud run services describe renombradorarchivosgdrive-worker-v2 \
  --region us-central1 \
  --project cloud-functions-474716 \
  --format 'value(status.latestReadyRevisionName)'
```

---

## ✅ PASO 4: Probar

### 4.1 Ejecutar un job manual:
1. Ir al frontend: https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app
2. Seleccionar una carpeta con documentos variados
3. Seleccionar "Genérico" (esto ya no importa tanto, pero el sistema debe clasificar)
4. Ejecutar

### 4.2 Verificar en los logs:
```bash
# Ver logs del Worker
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
  --project cloud-functions-474716 \
  --limit 50 \
  --format 'value(timestamp,textPayload)' \
  --freshness=10m
```

Deberías ver:
```
🔍 Starting classification for: factura_123.pdf
🤖 Executing classification with AI...
✅ Classification result: {'algorithm_id': 'factura_rg830', 'confidence': 0.95}
   → Classified as: factura_rg830 (confidence: 0.95)
📋 Selected algorithm: Facturas RG 830
   Filename format: {fecha_emision}_{servicio}_{tipo_factura}_{numero_factura}.{ext}
ALGORITHM-SPECIFIC PROMPT (Facturas RG 830):
Eres un clasificador experto en documentos contables argentinos...
...
✅ File processed successfully: factura_123.pdf -> 2025-03-14_luz_A_12345.pdf (algorithm: factura_rg830, confidence: 0.95)
```

---

## 📝 Resumen de Cambios

### Archivos Creados:
1. `scripts/create_algorithms_table.sql` - Script SQL para crear la tabla document_algorithms
2. `scripts/insert_algorithms_test.sql` - Script SQL para insertar primer algoritmo (factura_rg830)
3. `scripts/insert_remaining_algorithms.sql` - Script SQL para insertar los 5 algoritmos restantes
4. `AUTO_CLASSIFICATION_PATCH.md` - Código de las nuevas funciones
5. `INSTRUCCIONES_CLASIFICACION_AUTOMATICA.md` - Este documento

### Archivos Modificados:
1. `services/worker-renombrador/src/main.py` - Worker (agregar funciones y modificar loop)

### Archivos Nuevos en Supabase:
1. Tabla `document_algorithms` - 6 algoritmos preconfigurados

---

## 🎯 Resultado Esperado

Después de implementar esto:

✅ **Ventajas:**
- La IA clasifica automáticamente CADA documento
- Cada documento usa el algoritmo CORRECTO
- El usuario NO selecciona qué algoritmo usar
- Más preciso: Factura RG 830 usa algoritmo RG 830, no genérico

✅ **Experiencia del Usuario:**
1. Usuario selecciona carpeta
2. Usuario selecciona algoritmo (ahora es menos importante, el sistema clasifica)
3. Sistema procesa TODOS los documentos
4. Cada documento se renombra con el algoritmo correcto automáticamente

✅ **Ejemplo de resultado:**
```
Carpeta con:
- factura_luz_enero.pdf → 2025-02-28_luz_A_00123.pdf (RG 830)
- recibo_sueldo_marzo.pdf → Marzo 2025_Recibo de sueldo_Juan Perez.pdf (Sueldo)
- resumen_banco_galicia.pdf → 2025-03-31_Galicia_Resumen de cuenta.pdf (Bancario)
- contrato_alquiler.pdf → 2025-01-01_Alquiler_Inmobiliaria SA.pdf (Contrato)
- documento_generico.pdf → 2025-01-15_documento_generico_abc.pdf (Genérico)
```

---

## 🔄 Cómo Agregar MÁS Algoritmos en el Futuro

El usuario podrá crear sus propios algoritmos. Para agregar uno nuevo:

1. INSERT en `document_algorithms`:
```sql
INSERT INTO document_algorithms (id, name, description, classification_criteria, extraction_prompt, output_schema, filename_format, is_active)
VALUES
(
  'mi_algoritmo_personalizado',
  'Mi Algoritmo Personalizado',
  'Descripción de mi algoritmo...',
  'Prompt de clasificación...',
  'Prompt de extracción...',
  '{"campo1": "string", "campo2": "int"}',
  '{campo1}_{campo2}.{ext}',
  true
);
```

2. El sistema automáticamente lo cargará con `load_document_algorithms()`
3. La IA lo considerará en la clasificación

---

## 📚 Documentación de Referencia

- Archivo de algoritmos: `AUTO_CLASSIFICATION_PATCH.md`
- Script SQL (crear tabla): `scripts/create_algorithms_table.sql`
- Script SQL (insertar primer algoritmo): `scripts/insert_algorithms_test.sql`
- Script SQL (insertar algoritmos restantes): `scripts/insert_remaining_algorithms.sql`
- Este documento: `INSTRUCCIONES_CLASIFICACION_AUTOMATICA.md`

---

## ✅ Checklist Final

Antes de probar, verificar:

- [ ] **PASO 1 SQL:** Script `scripts/create_algorithms_table.sql` ejecutado (muestra table_exists = 1)
- [ ] **PASO 2 SQL:** Script `scripts/insert_algorithms_test.sql` ejecutado (factura_rg830 insertado)
- [ ] **PASO 3 SQL:** Script `scripts/insert_remaining_algorithms.sql` ejecutado (5 algoritmos insertados)
- [ ] **VERIFICACION SQL:** Query `SELECT id, name FROM document_algorithms` muestra 6 filas
- [ ] Funciones `load_document_algorithms()`, `classify_document()`, `process_folder_files_with_auto_classify()` agregadas a main.py
- [ ] `process_job()` modificado para cargar algoritmos
- [ ] Loop de carpetas modificado para pasar parámetro `algorithms`
- [ ] Worker deployed a Cloud Run
- [ ] Logs del Worker muestran clasificación correcta
- [ ] Prueba con carpeta de documentos variados exitosa

---

**Fecha de creación:** 14 de Marzo, 2026
**Versión:** 2.0.0
**Autor:** Claude + amBotHs
