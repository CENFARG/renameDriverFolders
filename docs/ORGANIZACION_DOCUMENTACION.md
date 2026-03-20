# 📚 Organización de Documentación - Estado Actual

## 📁 Estructura de Carpetas

```
docs/
├── oauth-user-credentials/       ← Documentación OAuth User Credentials
│   ├── README.md                  ← Quick start guide
│   ├── OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md  ← Arquitectura completa
│   ├── OAUTH_API_SERVER_PATCH.md  ← Cambios API Server
│   ├── OAUTH_WORKER_PATCH.md      ← Cambios Worker
│   ├── PASOS_SIGUIENTES_OAUTH.md  ← Checklist de implementación
│   └── OAUTH_SETUP_GUIDE.md       ← (Ya existía)
│
├── auto-classification/          ← Documentación Clasificación Automática
│   ├── README.md                  ← Quick overview
│   ├── INSTRUCCIONES_CLASIFICACION_AUTOMATICA.md  ← Guía completa
│   └── AUTO_CLASSIFICATION_PATCH.md  ← Código Worker
│
├── examples/                      ← (Ya existía)
├── AGNO_STRUCTURED_OUTPUTS_REFACTOR.md  ← (Ya existía)
├── CLIENT_REQUIREMENTS_IMPLEMENTATION.md  ← (Ya existía)
├── DEBUGGING_GENERIC_NAMES.md     ← (Ya existía)
├── DEVOPS_LEARNING_GUIDE.md       ← (Ya existía)
├── FILENAME_FORMATS.md            ← (Ya existía)
├── FRONTEND_FIXES_V00004.md       ← (Ya existía)
├── GEMINI_2.5_DEBUG_CHANGES.md    ← (Ya existía)
├── INFORME_CLIENTE.md             ← (Ya existía)
├── OAUTH_SETUP_GUIDE.md           ← (Ya existía, duplicado en oauth-user-credentials/)
├── SOLUCION_OAUTH_ERROR.md        ← (Ya existía)
├── TESTING_GUIDE.md               ← (Ya existía)
├── howto_view_env_vars.md         ← (Ya existía)
└── oauth_update_instructions.md   ← (Ya existía)
```

## 📋 Memorias del Proyecto

Archivos `RESUMEN_*.md` en la raíz:

- `RESUMEN_DIA_13_MARZ_2026.md` - Memoria del 13/03 (deploy v2-00042-d6r)
- `RESUMEN_DIA_19_MARZ_2026.md` - Memoria de hoy (OAuth User Credentials design)
- `RESUMEN_TAREA_1.2_COMPLETADA.md` - Resumen tarea 1.2
- `RESUMEN_SESION_COMPLETA_1.5-1.6-1.7.md` - Resumen sesiones 1.5-1.7

## 🗄️ Scripts SQL

En `scripts/`:

- `create_algorithms_table.sql` - Crear tabla document_algorithms
- `insert_algorithms_test.sql` - Insertar primer algoritmo (test)
- `insert_remaining_algorithms.sql` - Insertar 5 algoritmos restantes
- `setup_auto_classification.sql` - Script completo (original)
- `test_simple_insert.sql` - Test básico
- `test_without_json.sql` - Test sin JSON
- `create_document_algorithms.sql` - Script alternativo

## 📊 Commits Recientes

```
ba7724d docs: Add Auto Classification documentation (PAUSED)
86caf19 docs: Add OAuth User Credentials Flow implementation guide
74177bc docs: update daily summary with v2-00040-897 deployment
332df09 chore: add local Dockerfile for api-server deployment
8f7eb8b debug: add detailed queue path logging for 404 error investigation
```

## 🎯 Prioridades Actuales

### 1. OAuth User Credentials (ALTA PRIORIDAD)
- **Estado:** Diseño completado ✅
- **Documentación:** Completa en `docs/oauth-user-credentials/`
- **Próximo paso:** Implementación (~50 min)
- **Bloquea:** Problema de Diego (0 archivos encontrados)

### 2. Clasificación Automática (MEDIA PRIORIDAD)
- **Estado:** Diseño completado ✅
- **Documentación:** Completa en `docs/auto-classification/`
- **Próximo paso:** Implementación (después de OAuth)
- **Estado:** ⏸️ PAUSADO

## 📝 Próximos Pasos

1. **Implementar OAuth User Credentials**
   - Revisar `docs/oauth-user-credentials/PASOS_SIGUIENTES_OAUTH.md`
   - Aplicar parches en Worker y API Server
   - Deploy y testing
   - Commit: `feat: Implement OAuth user credentials flow`

2. **Retomar Clasificación Automática**
   - Revisar `docs/auto-classification/README.md`
   - Crear tabla en Supabase
   - Modificar Worker
   - Deploy y testing
   - Commit: `feat: Implement automatic document classification`

3. **Organización pendiente**
   - Mover memorias del proyecto a carpeta `memorias/` o `diario/`
   - Actualizar README principal con links a documentación
   - Crear índice de documentación

---

**Fecha:** 19 de Marzo, 2026
**Estado:** Documentación organizada y commiteada ✅
**Próxima sesión:** Implementación OAuth User Credentials
