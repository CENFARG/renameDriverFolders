# 🔐 OAuth User Credentials Flow - Documentación

## 📋 Descripción

Esta carpeta contiene toda la documentación para implementar el flujo de credenciales OAuth de usuario, permitiendo que el Worker acceda a Google Drive en nombre del usuario en lugar de usar una service account con permisos universales.

## 🎯 Problema que Resuelve

**Problema actual:** Diego (y cualquier usuario futuro) no puede procesar sus archivos porque el Worker usa una service account que no tiene permisos en sus carpetas personales.

**Solución:** El Worker recibe y usa las credenciales OAuth del usuario para acceder a sus archivos.

## 📁 Archivos

### 1. OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md ⭐
**Guía completa de implementación**

- Arquitectura actual vs. nueva
- Consideraciones de seguridad detalladas
- Análisis de riesgos y mitigaciones
- Plan de implementación paso a paso
- Estrategia de testing y validación
- Plan de deploy y rollback
- Checklist de seguridad

**Cuándo leerlo:** Antes de empezar la implementación

### 2. OAUTH_API_SERVER_PATCH.md
**Cambios específicos para el API Server**

Cambios necesarios en `services/api-server/src/main.py`:
- Función `sanitize_payload()` - Máscaras access tokens en logs
- Modificación de `submit_manual_job()` - Extraer access token del request
- Payload actualizado - Incluir `user_credentials`
- Modificación de `create_cloud_task()` - Sanitizar logs

**Cuándo usarlo:** Durante la implementación del API Server

### 3. OAUTH_WORKER_PATCH.md
**Cambios específicos para el Worker**

Cambios necesarios en `services/worker-renombrador/src/main.py`:
- Modelo `UserCredentials` - Validar credenciales de usuario
- Función `get_user_credentials()` - Crear credenciales OAuth desde token
- Función `mask_access_token()` - Máscara para safe logging
- Modificación de `run_task()` - Usar credenciales de usuario
- Modificación de `process_job()` - Loggear tipo de credenciales

**Cuándo usarlo:** Durante la implementación del Worker

### 4. PASOS_SIGUIENTES_OAUTH.md
**Checklist de implementación rápida**

- Plan paso a paso con tiempos estimados (~50 min total)
- Comandos de deploy listos para ejecutar
- Comandos de rollback en caso de problemas
- Resultados esperados
- Logs de diagnóstico

**Cuándo usarlo:** Como guía rápida durante la implementación

## 🚀 Flujo de Implementación Recomendado

### Paso 1: Lectura (10 min)
1. Leer `OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md` - Entender arquitectura
2. Leer `PASOS_SIGUIENTES_OAUTH.md` - Entender checklist

### Paso 2: Implementación Worker (15 min)
1. Abrir `services/worker-renombrador/src/main.py`
2. Seguir `OAUTH_WORKER_PATCH.md`
3. Aplicar los 5 cambios listados
4. Verificar sintaxis

### Paso 3: Implementación API Server (15 min)
1. Abrir `services/api-server/src/main.py`
2. Seguir `OAUTH_API_SERVER_PATCH.md`
3. Aplicar los 4 cambios listados
4. Verificar sintaxis

### Paso 4: Deploy (10 min)
```bash
# 1. Deploy Worker primero (backward compatibility)
cd services/worker-renombrador
gcloud builds submit --config cloudbuild.yaml --project cloud-functions-474716 .

# 2. Verificar Worker
gcloud run services describe renombradorarchivosgdrive-worker-v2 \
  --region us-central1 --project cloud-functions-474716

# 3. Deploy API Server
cd ../api-server
gcloud builds submit --config cloudbuild.yaml --project cloud-functions-474716 .

# 4. Verificar API Server
gcloud run services describe renombradorarchivosgdrive-api-server-v2 \
  --region us-central1 --project cloud-functions-474716
```

### Paso 5: Testing (10 min)
1. Test con Gonzalo (su cuenta debe seguir funcionando)
2. **Test con Diego (ahora debe funcionar)** ✅
3. Verificar logs muestran "Using USER OAUTH credentials"
4. Verificar que scheduled jobs siguen funcionando

## 🔒 Seguridad

### Medidas implementadas:

| Medida | Archivo |
|--------|---------|
| Validación de tokens | `OAUTH_API_SERVER_PATCH.md` |
| Sanitización de logs | `OAUTH_API_SERVER_PATCH.md` |
| No persistencia de tokens | `OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md` |
| Scope limitado | `OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md` |
| IAP protection | `OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md` |
| Backward compatibility | `OAUTH_WORKER_PATCH.md` |

## 📊 Resultados Esperados

### Antes (Diego):
```
Found 0 files in folder 10tSqrRY-QaTyIl_8qOQFO98zcLQQbFFP
Job completed. Processed: 0, Renamed: 0
```

### Después (Diego):
```
🔐 Using USER OAUTH credentials
   User: cutignolad@estudioanc.com.ar
   Access token: ya29...xyz
Found 15 files in folder 10tSqrRY-QaTyIl_8qOQFO98zcLQQbFFP
Job completed. Processed: 15, Renamed: 15
```

## 🆘 Problemas?

Si algo sale mal, ver:
- **Plan de rollback:** `OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md` sección 7
- **Diagnóstico:** `OAUTH_WORKER_PATCH.md` sección "DIAGNÓSTICO DE PROBLEMAS"
- **Logs esperados:** `OAUTH_WORKER_PATCH.md` sección "EJEMPLO DE LOGS ESPERADOS"

## 📝 Contexto

- **Fecha de creación:** 19 de Marzo, 2026
- **Autor:** Claude + amBotHs
- **Problema identificado:** Diego no puede procesar archivos
- **Solución diseñada:** OAuth User Credentials Flow
- **Estado:** Listo para implementación

## 🔗 Relacionado

- Memoria del día: `../../RESUMEN_DIA_19_MARZ_2026.md`
- Clasificación automática: `../../INSTRUCCIONES_CLASIFICACION_AUTOMATICA.md`

---

**¿Listo para implementar?** Empieza con `PASOS_SIGUIENTES_OAUTH.md` 🚀
