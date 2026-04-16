# 📦 03. PRODUCT REQUIREMENTS DOCUMENT (PRD)
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Definir los requisitos funcionales y no funcionales del producto **Renombrador** V3.1.2, sistema de automatización inteligente de documentos en Google Drive usando IA (Gemini 2.0/2.5 Flash).

---

## 👤 PERSONAS

### Persona Primaria: El Contador
**Nombre:** María González, Contadora Senior
**Edad:** 45 años
**Ubicación:** Buenos Aires, Argentina
**Empresa:** Estudio Contable de 10 personas

**Pain Points:**
- ❌ "Piero 2 horas diarias buscando facturas"
- ❌ "Los clientes me mandan archivos con nombres horrible"
- ❌ "Se me pierden documentos en la montaña de PDFs"
- ❌ "No tengo tiempo para estar renombrando archivos"

**Goals:**
- ✅ "Quiero que los archivos se nombren solos"
- ✅ "Quiero encontrar cualquier documento en segundos"
- ✅ "Quiero que el sistema entienda nomenclatura contable"
- ✅ "Quiero auditar qué se renombró y qué no"

**Tech Savviness:** Media (usa Excel, Google Drive, pero no coding)

### Persona Secundaria: El Socio del Estudio
**Nombre:** Diego Cutignola, Socio Fundador
**Edad:** 52 años
**Ubicación:** Buenos Aires, Argentina

**Pain Points:**
- ❌ "Perdemos dinero en tareas operativas"
- ❌ "Errores humanos nos cuestan caros"
- ❌ "Necesito transparencia total"

**Goals:**
- ✅ "Automatizar todo lo que se pueda"
- ✅ "Auditoría completa de operaciones"
- ✅ "Escalabilidad sin contratar más gente"

---

## 🎯 REQUISITOS FUNCIONALES

### Epic 1: Autenticación y Autorización

#### FR-1.1: Google Sign-In
**Descripción:** El usuario debe poder autenticarse con su cuenta de Google.

**Requisitos:**
- [x] OAuth 2.0 con Google Sign-In
- [x] Dominios autorizados: estudioanc.com.ar, gmail.com
- [x] Verificación de email en tiempo real
- [x] Session persistente (hasta 1 hora de inactividad)

**Criterios de Aceptación:**
- Given un usuario con cuenta @estudioanc.com.ar
- When hace clic en "Iniciar Sesión con Google"
- Then ve su email y puede acceder al sistema

**Prioridad:** ALTA
**Estado:** ✅ Completado

#### FR-1.2: Dominios Autorizados
**Descripción:** Solo usuarios de dominios autorizados pueden acceder.

**Requisitos:**
- [x] Whitelist de dominios configurables
- [x] Rechazo con mensaje claro si dominio no autorizado
- [x] Logging de intentos de acceso no autorizados

**Prioridad:** ALTA
**Estado:** ✅ Completado

---

### Epic 2: Gestión de Algoritmos de Estudio (Jobs)

#### FR-2.1: Crear Algoritmo
**Descripción:** El usuario puede crear un nuevo algoritmo de renombrado.

**Campos:**
- [x] **Nombre del Algoritmo:** Ej: "Facturas RG 830 - Cliente X"
- [x] **Carpeta de Google Drive:** Selección visual con Picker
- [x] **Frecuencia:**
  - Manual
  - Diario (ej: 8:00 AM)
  - Semanal (ej: Lunes 9:00 AM)
  - Mensual (ej: Día 1)
  - Trimestral (ej: 15 Marzo)
  - Anual (ej: 31 Diciembre)
- [x] **Formato de Nombre:**
  - Placeholders: `{date}`, `{type}`, `{issuer}`, `{entity}`, `{concept}`, `{ext}`
  - Ejemplo: `{date}_{type}_{issuer}_{concept}.{ext}`
- [x] **Algoritmo Preconfigurado:**
  - Facturas RG 830
  - Sueldos Digitales
  - Resúmenes Bancarios
  - Estados Contables
  - Custom

**Prioridad:** ALTA
**Estado:** ✅ Completado

#### FR-2.2: Editar Algoritmo
**Descripción:** El usuario puede modificar un algoritmo existente.

**Criterios de Aceptación:**
- Given un algoritmo existente
- When el usuario hace clic en "Editar"
- Then ve un formulario pre-populado y puede guardar cambios

**Prioridad:** MEDIA
**Estado:** ⚠️ Con errores (requiere fix)

#### FR-2.3: Eliminar Algoritmo
**Descripción:** El usuario puede eliminar un algoritmo.

**Criterios de Aceptación:**
- Given un algoritmo existente
- When el usuario hace clic en "Eliminar"
- Then ve un diálogo de confirmación y el algoritmo se elimina

**Prioridad:** MEDIA
**Estado:** ⚠️ Con errores (requiere fix)

#### FR-2.4: Duplicar Algoritmo
**Descripción:** El usuario puede duplicar un algoritmo para crear uno similar rápidamente.

**Criterios de Aceptación:**
- Given un algoritmo existente
- When el usuario hace clic en "Duplicar"
- Then se crea una copia con "[COPIA]" en el nombre

**Prioridad:** MEDIA
**Estado:** ❌ No implementado (pending)

---

### Epic 3: Ejecución de Algoritmos

#### FR-3.1: Ejecución Manual
**Descripción:** El usuario puede ejecutar un algoritmo inmediatamente.

**Flujo:**
1. Usuario selecciona algoritmo
2. Usuario hace clic en "Procesar Ahora"
3. Sistema confirma: "Tarea enviada. Task ID: xxx"
4. Worker procesa en background
5. Usuario puede ver progreso en dashboard

**Criterios de Aceptación:**
- Given un algoritmo configurado
- When el usuario hace clic en "Procesar Ahora"
- Then ve confirmación y el worker empieza a procesar

**Prioridad:** ALTA
**Estado:** ⚠️ Con errores (requiere fix para cliente Diego)

#### FR-3.2: Ejecución Programada
**Descripción:** El sistema ejecuta algoritmos según su frecuencia configurada.

**Requisitos:**
- [x] Cloud Scheduler para cron jobs
- [x] Dispatch de tareas a Cloud Tasks
- [x] Logging de cada ejecución programada
- [x] Retry en caso de error

**Prioridad:** ALTA
**Estado:** ✅ Completado

---

### Epic 4: Procesamiento de Documentos con IA

#### FR-4.1: Análisis de Documentos
**Descripción:** El sistema analiza cada documento y extrae metadatos.

**Metadatos Extraídos:**
- [x] **Fecha:** Fecha del documento (YYYY-MM-DD)
- [x] **Tipo:** Factura, Recibo, Resumen, etc.
- [x] **Emisor:** Empresa que emite el documento
- [x] **Entidad:** Cliente/Proveedor
- [x] **Concepto:** Descripción breve
- [x] **Monto:** Monto del documento (si aplica)
- [x] **Moneda:** ARS, USD, EUR, etc.

**Criterios de Aceptación:**
- Given un documento PDF o imagen
- When el worker lo procesa
- Then extrae los metadatos con >95% precisión

**Prioridad:** ALTA
**Estado:** ✅ Completado

#### FR-4.2: OCR de Documentos Escaneados
**Descripción:** El sistema puede procesar documentos escaneados (imágenes).

**Requisitos:**
- [x] Google Cloud Vision API para OCR
- [x] Soporte para PDFs escaneados
- [x] Soporte para imágenes (JPG, PNG)
- [x] Fallback a text extraction si OCR falla

**Prioridad:** ALTA
**Estado:** ✅ Completado

#### FR-4.3: Generación de Nombres
**Descripción:** El sistema genera un nombre descriptivo usando los metadatos extraídos.

**Formato de Nombre:**
```
{date}_{type}_{issuer}_{concept}.{ext}
```

**Ejemplo:**
```
2025-03-12_Factura_B_MorganStanley_ServiciosConsultoria.pdf
```

**Criterios de Aceptación:**
- Given metadatos extraídos
- When el worker genera el nombre
- Then el nombre sigue el formato especificado con tokens válidos

**Prioridad:** ALTA
**Estado:** ✅ Completado

#### FR-4.4: Renombrado en Google Drive
**Descripción:** El sistema renombra el archivo en Google Drive.

**Requisitos:**
- [x] Preservar contenido del archivo (sin modificar)
- [x] Mover a misma ubicación (no cambiar carpeta)
- [x] Manejo de colisiones (si nombre existe)
- [x] Log de cada renombrado

**Prioridad:** ALTA
**Estado:** ✅ Completado

---

### Epic 5: Auditoría y Logs

#### FR-5.1: Dashboard de Auditoría
**Descripción:** El usuario puede ver el historial completo de ejecuciones.

**Datos Mostrados:**
- [x] **Timestamp:** Fecha y hora de ejecución
- [x] **Algoritmo:** Nombre del algoritmo ejecutado
- [x] **Estado:** SUBMITTED, IN_PROGRESS, COMPLETED, FAILED
- [x] **Archivos Procesados:** Cantidad
- [x] **Archivos Renombrados:** Cantidad
- [x] **Errores:** Lista de errores si los hubo

**Prioridad:** ALTA
**Estado:** ✅ Completado

#### FR-5.2: Persistencia de Logs
**Descripción:** Los logs se almacenan de forma persistente e inmutable.

**Requisitos:**
- [x] JSON local (desarrollo)
- [x] Google Cloud Storage (Cloud Run)
- [x] Supabase PostgreSQL (producción)
- [x] Retención de 90 días

**Prioridad:** ALTA
**Estado:** ⚠️ Parcial (se perdieron logs históricos)

#### FR-5.3: Exportación de Logs
**Descripción:** El usuario puede exportar logs a CSV/Excel.

**Prioridad:** BAJA
**Estado:** ❌ No implementado

---

### Epic 6: Integraciones

#### FR-6.1: Google Drive Picker
**Descripción:** Selección visual de carpetas de Google Drive.

**Requisitos:**
- [x] Navegación visual de carpetas
- [x] Selección de carpeta única
- [x] Captura automática de Folder ID
- [x] Permisos OAuth granulares

**Prioridad:** ALTA
**Estado:** ✅ Completado

#### FR-6.2: Google Sign-In
**Descripción:** Autenticación con cuenta de Google.

**Requisitos:**
- [x] OAuth 2.0 flow
- [x] Access token + refresh token
- [x] Verificación de dominio
- [x] Session persistente

**Prioridad:** ALTA
**Estado:** ✅ Completado

---

## 🎯 REQUISITOS NO FUNCIONALES

### NFR-1: Performance
- [x] **Latencia:** <30s para procesar 100 archivos
- [x] **Throughput:** >100 archivos/minuto
- [x] **Startup time:** <5s (cold start)

### NFR-2: Disponibilidad
- [x] **Uptime:** >99.5% (objetivo: 99.9%)
- [x] **Retry logic:** Exponential backoff
- [x] **Graceful degradation:** Funciona con features degradados

### NFR-3: Escalabilidad
- [x] **Auto-scaling:** Cloud Run escala automáticamente
- [x] **Horizontal scaling:** Múltiples workers en paralelo
- [x] **Queue-based:** Cloud Tasks para buffering

### NFR-4: Seguridad
- [x] **OAuth 2.0:** Autenticación estándar
- [x] **Domain whitelisting:** Solo usuarios autorizados
- [x] **Rate limiting:** 10 req/min por usuario
- [x] **CORS:** Orígenes permitidos configurables
- [x] **Secrets management:** Google Secret Manager

### NFR-5: Usabilidad
- [x] **UX humana:** Lenguaje no técnico
- [x] **Responsive:** Funciona en desktop y tablet
- [x] **Feedback inmediato:** Confirmación de acciones
- [x] **Error handling:** Mensajes claros y accionables

### NFR-6: Mantenibilidad
- [x] **Core Package:** Módulos reutilizables
- [x] **Logging:** Estructurado y completo
- [x] **Documentation:** README + 10 documentos de gestión
- [x] **Git workflow:** Commits con CONTEXT

### NFR-7: Compatibilidad
- [x] **PDFs:** PDF nativos y escaneados
- [x] **Imágenes:** JPG, PNG, HEIC
- [x] **Navegadores:** Chrome, Firefox, Safari, Edge (últimas 2 versiones)
- [x] **Google Drive:** Cuentas personales y corporate

---

## 🚩 REQUISITOS PENDIENTES (V3.2+)

### FR-7.1: Tests Automatizados
**Descripción:** Suite de tests automatizados.

**Prioridad:** ALTA
**Estado:** ❌ 0% (objetivo: 80%)

### FR-7.2: CI/CD Pipeline
**Descripción:** Pipeline de deployment automático.

**Prioridad:** ALTA
**Estado:** ❌ 0% (objetivo: 100%)

### FR-7.3: Monitoring Dashboard
**Descripción:** Dashboard de métricas en tiempo real.

**Prioridad:** MEDIA
**Estado:** ❌ No implementado

### FR-7.4: Multi-tenancy
**Descripción:** Soporte para múltiples estudios/organizaciones.

**Prioridad:** MEDIA
**Estado:** ⏳ Partial (hardcoded para Estudio Cutignola)

---

## 📊 MATRIZ DE PRIORIDADES

### Must Have (V3.1.2) ✅
- OAuth 2.0 con Google Sign-In
- Gestión de algoritmos (crear, editar, eliminar)
- Ejecución manual y programada
- Procesamiento con IA (Gemini + OCR)
- Renombrado en Google Drive
- Dashboard de auditoría

### Should Have (V3.2) ⏳
- Duplicar algoritmo
- Exportación de logs
- Tests automatizados
- CI/CD pipeline
- Monitoring dashboard

### Could Have (V4.0) 💭
- Multi-tenancy completo
- Mobile app
- Integración con sistemas contables
- Marketplace de algoritmos

### Won't Have (Out of Scope) ❌
- Edición inline de documentos
- OCR de documentos manuscritos
- Soporte offline
- Self-hosted option

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** V3.2 (Q2 2026)

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
