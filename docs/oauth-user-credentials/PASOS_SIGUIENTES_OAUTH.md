# 🚀 PRÓXIMOS PASOS - Implementación OAuth User Credentials
# ================================================================

## 📋 RESUMEN EJECUTIVO

Para solucionar el problema de Diego (y cualquier usuario futuro), necesitamos implementar el flujo de credenciales OAuth del usuario. Esta es la **solución correcta y escalable**.

## ⚠️ PROBLEMA ACTUAL

Diego ejecuta un job manual → Worker usa service account → Service account NO tiene acceso a las carpetas de Diego → **0 archivos encontrados**

## ✅ SOLUCIÓN

Diego ejecuta un job manual → Worker usa credenciales de Diego → Worker accede a Drive de Diego → **✅ Archivos procesados**

---

## 📁 ARCHIVOS CREADOS

1. **`OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md`**
   - Documentación completa de la arquitectura
   - Consideraciones de seguridad
   - Plan de implementación paso a paso
   - Plan de testing y deploy

2. **`OAUTH_API_SERVER_PATCH.md`**
   - Cambios específicos para `services/api-server/src/main.py`
   - Código listo para copiar/pegar
   - Explicación de cada cambio

3. **`OAUTH_WORKER_PATCH.md`**
   - Cambios específicos para `services/worker-renombrador/src/main.py`
   - Código listo para copiar/pegar
   - Ejemplos de logs esperados

---

## 🔧 PLAN DE IMPLEMENTACIÓN

### Fase 1: Preparación (5 minutos)
- [ ] Leer `OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md`
- [ ] Entender la arquitectura propuesta
- [ ] Revisar los cambios propuestos en los patches

### Fase 2: Modificar Worker (15 minutos)
- [ ] Abrir `services/worker-renombrador/src/main.py`
- [ ] Aplicar cambios de `OAUTH_WORKER_PATCH.md`:
  1. Actualizar TaskPayload model (agregar UserCredentials)
  2. Agregar función get_user_credentials()
  3. Agregar función mask_access_token()
  4. Modificar run_task() para usar credenciales de usuario
  5. Agregar import de OAuthCredentials
- [ ] Verificar que no haya errores de sintaxis

### Fase 3: Modificar API Server (15 minutos)
- [ ] Abrir `services/api-server/src/main.py`
- [ ] Aplicar cambios de `OAUTH_API_SERVER_PATCH.md`:
  1. Agregar función sanitize_payload()
  2. Modificar submit_manual_job() para extraer access token
  3. Modificar payload para incluir user_credentials
  4. Modificar create_cloud_task() para sanitizar logs
- [ ] Verificar que no haya errores de sintaxis

### Fase 4: Build y Deploy (10 minutos)
```bash
# 1. Deploy Worker primero (para mantener backward compatibility)
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

### Fase 5: Testing (10 minutos)
- [ ] Test con Gonzalo (su cuenta debe seguir funcionando)
- [ ] Test con Diego (su cuenta ahora debe funcionar)
- [ ] Verificar logs para confirmar uso de user credentials
- [ ] Verificar que scheduled jobs siguen funcionando

### Fase 6: Validación Final (5 minutos)
```bash
# Verificar logs recientes
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
  --project cloud-functions-474716 --limit 50 --freshness=10m \
  --format 'value(timestamp,textPayload)'

# Deberías ver:
# ✅ "Using USER OAUTH credentials" para jobs manuales
# ✅ "Using SERVICE ACCOUNT credentials" para scheduled jobs
# ✅ "Found X files in folder..." con X > 0 para Diego
```

---

## 🎯 RESULTADO ESPERADO

### Antes (Diego):
```
2026-03-18 20:10:36 INFO Found 0 files in folder 10tSqrRY-QaTyIl_8qOQFO98zcLQQbFFP
2026-03-18 20:10:36 INFO Job completed. Processed: 0, Renamed: 0
```

### Después (Diego):
```
2026-03-19 10:00:00 INFO 🔐 Using USER OAUTH credentials
2026-03-19 10:00:00 INFO    User: cutignolad@estudioanc.com.ar
2026-03-19 10:00:00 INFO    Access token: ya29...xyz
2026-03-19 10:00:02 INFO Found 15 files in folder 10tSqrRY-QaTyIl_8qOQFO98zcLQQbFFP
2026-03-19 10:00:10 INFO Job completed. Processed: 15, Renamed: 15
```

---

## 🛡️ SEGURIDAD IMPLEMENTADA

✅ Access tokens validados antes de crear task
✅ Access tokens nunca persistidos
✅ Access tokens nunca logueados completos
✅ Access tokens de corta duración (~60 min)
✅ Scope limitado a drive API
✅ Principio de least privilege
✅ Backward compatible con scheduled jobs
✅ IAP sigue validando tokens (doble capa)

---

## ⚠️ RIESGOS Y PLAN DE ROLLBACK

### Si algo sale mal:

```bash
# Rollback Worker a versión anterior
gcloud run services update-traffic renombradorarchivosgdrive-worker-v2 \
  --to-revisions=v2-00042-d6r=100 \
  --region us-central1 \
  --project cloud-functions-474716

# Rollback API Server a versión anterior
gcloud run services update-traffic renombradorarchivosgdrive-api-server-v2 \
  --to-revisions=v2-00042-d6r=100 \
  --region us-central1 \
  --project cloud-functions-474716
```

### Señales de problema:
- Errors 401/403 en logs
- "Invalid credentials" en logs
- Scheduled jobs dejan de funcionar
- Gonzalo reporta problemas

---

## 📞 SOPORTE

Si tienes preguntas durante la implementación:
1. Revisar `OAUTH_USER_CREDENTIALS_IMPLEMENTATION.md` para arquitectura
2. Revisar `OAUTH_API_SERVER_PATCH.md` para cambios del API Server
3. Revisar `OAUTH_WORKER_PATCH.md` para cambios del Worker
4. Verificar logs en tiempo real para diagnóstico

---

## ✅ CHECKLIST FINAL

Antes de empezar:
- [ ] Entendí la arquitectura propuesta
- [ ] Sé qué archivos modificar
- [ ] Sé en qué orden deployar (Worker primero, luego API Server)
- [ ] Sé cómo hacer rollback si algo sale mal
- [ ] Tengo acceso a los logs para diagnóstico

Durante la implementación:
- [ ] Aplicar cambios al Worker
- [ ] Verificar sintaxis del Worker
- [ ] Deployar Worker
- [ ] Aplicar cambios al API Server
- [ ] Verificar sintaxis del API Server
- [ ] Deployar API Server

Después del deploy:
- [ ] Test con Gonzalo
- [ ] Test con Diego
- [ ] Verificar logs muestran "Using USER OAUTH credentials"
- [ ] Verificar que Diego ya no ve "Found 0 files"
- [ ] Verificar que scheduled jobs siguen funcionando

---

## 🎉 LISTO PARA EMPEZAR

Una vez completada la implementación:
- ✅ Diego podrá procesar sus archivos
- ✅ Cualquier usuario futuro podrá funcionar sin configuración manual
- ✅ Sistema escalable a N usuarios
- ✅ Principio de least privilege implementado
- ✅ Compliance de seguridad mejorado

---

**¿Listo para implementar?**
