# Índice de Documentación - RenameDriverFolders

**Session**: #C0001#P0007+renameDriverFolders
**Fecha**: 31 de Marzo 2026
**Para**: OpenCode / Continuación de trabajo

---

## 📚 Documentos Principales

### 1. OPENCODE_HANDOVER.md ⭐ **LEER PRIMERO**
**Qué es**: Documento principal de handover para OpenCode
**Contiene**:
- Resumen ejecutivo del proyecto
- Arquitectura del sistema
- OAuth fix explicado en detalle
- Próximos pasos inmediatos
- Checklist de éxito

**Cuándo leer**: ANTES de empezar a trabajar

---

### 2. TASKS_STATUS.md
**Qué es**: Estado detallado de todas las tareas
**Contiene**:
- Tareas críticas pendientes (deploy + test)
- Tareas medium (audit status, Google Picker)
- Tareas completed con referencias
- Métricas de éxito

**Cuándo leer**: Para saber qué hacer ahora

---

### 3. QUICK_REFERENCE.md
**Qué es**: Comandos y paths rápidos
**Contiene**:
- Comandos de deploy
- Comandos de logs
- Paths importantes
- Endpoints útiles
- Troubleshooting guide

**Cuándo leer**: Cuando necesitas un comando rápido

---

### 4. SECURITY_AUDIT_ACTUALIZADO.md 🔐 **IMPORTANTE**
**Qué es**: Auditoría de seguridad actualizada y corregida
**Contiene**:
- Hallazgos reales vs falsas alarmas
- Análisis de autenticación del Worker
- Estado de políticas IAM
- Plan de remediación priorizado
- Checklist de seguridad

**Cuándo leer**: Antes de hacer cualquier cambio de seguridad

---

## 👤 Perfil de Usuario

### 4. memory/user_profile.md
**Qué es**: Perfil detallado de comunicación de Gonzalo
**Contiene**:
- Estilo de comunicación (voseo, tono cálido)
- Preferencias técnicas
- Lo que valora / odia
- Comportamiento en sesiones

**Cuándo leer**: ANTES de enviar primer mensaje

---

## 🔐 Memoria Técnica (Engram)

### Observaciones Guardadas

1. **OAuth Bearer token manual injection fix** (bugfix)
   - Solución completa con código
   - Explicación de por qué AuthorizedHttp no funciona

2. **Docker build cache .pyc cleanup** (discovery)
   - Problema de cache persistente
   - Solución con cleanup en Dockerfile

3. **OAuth scope drive vs drive.readonly** (bugfix)
   - Scope mismatch problem
   - Fix en frontend

4. **Supabase DatabaseManager invalid parameter** (bugfix)
   - Error de parámetro en algorithms endpoint
   - Fix simple pero crítico

5. **Project structure and deployment architecture** (architecture)
   - Arquitectura completa del sistema
   - Services, databases, infra

6. **User communication profile Gonzalo Recalde** (user)
   - Cómo comunicarse efectivamente
   - Tonos, vocabulario, preferencias

### Cómo Acceder

```python
# Desde código Python
from engram import mem_search, mem_get_observation

# Buscar por tema
results = mem_search(query="oauth fix", project="renamedriverfolders")

# Obtener observación completa
obs = mem_get_observation(id=123)
```

---

## 📁 Archivos de Código

### Críticos para OAuth Fix

```
services/worker-renombrador/src/main.py
├── Lines 26-27:     Imports (oauth2_credentials)
├── Lines 240-270:   get_user_credentials() function
├── Lines 273-299:   build_drive_service_with_credentials() ← FIX PRINCIPAL
└── Lines 720-730:   /debug/code endpoint

services/frontend/src/app/app.component.ts
└── Line 104:        OAuth scope (drive vs drive.readonly)

services/api-server/src/main.py
├── Lines 601-622:   /api/v1/algorithms endpoint
└── Lines 754-772:   user_credentials en payload
```

### Configuración de Deploy

```
services/worker-renombrador/
├── Dockerfile.build
│   └── Lines 28-32:  .pyc cleanup step
└── cloudbuild.yaml
    └── Line 5:        --no-cache flag
```

### Database

```
scripts/create_and_insert_algorithms.sql
└── 6 algoritmos preconfigurados
```

---

## 🚀 Flujo de Trabajo Recomendado

### Para OpenCode (Primera Sesión)

1. **LEER** `OPENCODE_HANDOVER.md` completamente
2. **LEER** `memory/user_profile.md` para entender estilo
3. **LEER** `TASKS_STATUS.md` para saber qué hacer
4. **EJECUTAR** deploy command desde `QUICK_REFERENCE.md`
5. **TESTEAR** con folder problemático
6. **VERIFICAR** logs para confirmar success
7. **AVISAR** al usuario con tono cálido y técnico

### Para Continuación (Sesiones Posteriores)

1. **USAR** `mem_context` para ver session summaries previas
2. **LEER** `TASKS_STATUS.md` para ver progreso
3. **CONSULTAR** `QUICK_REFERENCE.md` para comandos
4. **VERIFICAR** `/debug/code` endpoint antes de cambios
5. **EXPLICAR** causa raíz antes de proponer fixes

---

## 🎯 Prioridades

### 🔴 CRÍTICO (Ahora mismo)
1. **Deploy Worker** revisión 00051-qqr
2. **Test** con folder `1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH`
3. **Verificar** que NO hay "Refreshing credentials" en logs

### 🟡 MEDIUM (Esta semana)
1. **Investigar** audit status updates
2. **Considerar** Google Picker verification solution
3. **Documentar** OAuth flow para futuros devs

### 🟢 LOW (Futuro)
1. **Implementar** scheduled jobs UI mejorada
2. **Investigar** extension context error
3. **Optimizar** Docker build process

---

## 📞 Información de Contacto

### Usuario
- **Nombre**: Gonzalo Recalde
- **Email**: gonzalo.f.recalde@gmail.com
- **Proyecto**: renameDriverFolders
- **Path**: `C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders`

### Session
- **ID**: #C0001#P0007+renameDriverFolders
- **Fecha inicio**: 31 Marzo 2026
- **Estado actual**: OAuth fix implementado, pendiente deploy

### Infraestructura
- **Project**: cloud-functions-474716
- **Region**: us-central1
- **Services**: Frontend, API Server, Worker (Cloud Run)
- **Database**: Supabase (PostgreSQL)

---

## 🔍 Búsqueda Rápida

### Buscar por...

**Problema**:
- OAuth fix → `OPENCODE_HANDOVER.md` sección "🔑 CRITICAL"
- Deploy commands → `QUICK_REFERENCE.md` sección "🚀 Comandos de Deploy"
- Logs → `QUICK_REFERENCE.md` sección "📊 Logs y Debugging"
- User profile → `memory/user_profile.md`

**Archivo**:
- Worker → `services/worker-renombrador/src/main.py`
- API Server → `services/api-server/src/main.py`
- Frontend → `services/frontend/src/app/app.component.ts`
- Docker → `services/worker-renombrador/Dockerfile.build`

**Error**:
- "Refreshing credentials" → OAuth problem, ver `OPENCODE_HANDOVER.md`
- "relation does not exist" → Database, ver `create_and_insert_algorithms.sql`
- "App not verified" → Google Picker, ver `TASKS_STATUS.md`

---

## ✅ Checklist de Lectura

Antes de empezar a trabajar:
- [ ] Leí `OPENCODE_HANDOVER.md`
- [ ] Leí `memory/user_profile.md`
- [ ] Leí `TASKS_STATUS.md`
- [ ] Sé qué comando ejecutar (ver `QUICK_REFERENCE.md`)
- [ ] Entiendo el OAuth fix (AuthorizedHttp problem)
- [ ] Sé cómo comunicarme con el usuario

---

## 📝 Notas Finales

### Documentación Mantenida
- ✅ Session summaries en Engram
- ✅ Observaciones técnicas en Engram
- ✅ User profile en memory/
- ✅ Documentos markdown en project root

### Accesibilidad
- Todo en `C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders`
- Engram accesible via API o Python client
- Markdown files legibles en cualquier editor

### Actualización
- Este índice se actualiza con cada session
- Session summaries se guardan automáticamente
- Observaciones se agregan con `mem_save`

---

**¡Buena suerte! 🚀**

Cualquier pregunta, consultar:
1. `OPENCODE_HANDOVER.md` - Documento principal
2. `memory/user_profile.md` - Perfil de usuario
3. `QUICK_REFERENCE.md` - Comandos rápidos
4. Engram memories - Contexto histórico

**Recordatorio**: Usuario es senior developer, explicar technical porqué, usar voseo, ser cálido y directo.
