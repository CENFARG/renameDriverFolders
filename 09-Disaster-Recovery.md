# 🛡️ 09. DISASTER RECOVERY
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Definir la estrategia de recuperación ante desastres para el sistema **Renombrador** V3.1.2, incluyendo backups, rollback procedures y planes de contingencia.

---

## 🎯 OBJETIVOS DE RECUPERACIÓN

| Métrica | Objetivo | Actual |
|---------|----------|--------|
| **RPO (Recovery Point Objective)** | <1 hora | ⚠️ No definido |
| **RTO (Recovery Time Objective)** | <1 hora | ⚠️ No definido |
| **Data Loss** | 0 en producción | ⚠️ Riesgo alto |
| **Service Availability** | 99.9% | 99.5% |

---

## 💾 BACKUP STRATEGY

### 1. Database Backups (Supabase)

**Actual:**
- ⚠️ Sin backups automatizados
- ⚠️ Solo replicación de Supabase

**Propuesto:**
```bash
# Backup diario de Supabase
supabase db dump -f backup_$(date +%Y%m%d).sql

# Subir a Google Cloud Storage
gsutil cp backup_*.sql gs://renombrador-backups/database/

# Retención: 30 días
gsutil lifecycle set lifecycle.json gs://renombrador-backups/database/
```

### 2. Configuration Backups

**Actual:**
- ⚠️ Configuración en código
- ⚠️ Sin versionado de secrets

**Propuesto:**
```bash
# Backup de configuración diaria
gcloud secrets versions add secret-name --data-file=- < secret-file

# Backup de jobs configuration
supabase db dump -t jobs > jobs_config_$(date +%Y%m%d).sql
```

### 3. Audit Logs Backups

**Actual:**
- ⚠️ Logs en Google Cloud Logging (30 días retención)
- ⚠️ Sin exportación a largo plazo

**Propuesto:**
```bash
# Exportar logs diarios a GCS
gcloud logging sinks create audit-log-sink \
  storage.googleapis.com/renombrador-audit-logs

# Retención: 7 años (requerimientos legales)
```

---

## 🔄 ROLLBACK PROCEDURES

### Procedimiento 1: Rollback de Deployment

**Síntoma:** Nuevo deployment está causando errores

**Pasos:**
```bash
# 1. Identificar última versión funcional
gcloud run revisions list \
  --service=renombradorarchivosgdrive-api-server-v2 \
  --region=us-central1

# 2. Traffic a versión anterior
gcloud run services update-traffic renombradorarchivosgdrive-api-server-v2 \
  --to-revisions=REVISION_ID=100 \
  --region=us-central1

# 3. Verificar que funciona
curl https://renombradorarchivosgdrive-api-server-v2-.../health

# 4. Investigar error en logs
gcloud logs tail /projects/cloud-functions-474716/logs/renombradorarchivosgdrive-api-server-v2
```

**Tiempo estimado:** 5 minutos

### Procedimiento 2: Rollback de Base de Datos

**Síntoma:** Migración de DB corrompió datos

**Pasos:**
```bash
# 1. Parar servicios (evitar nuevos cambios)
gcloud run services update renombradorarchivosgdrive-worker-v2 \
  --no-traffic \
  --region=us-central1

# 2: Restaurar backup
supabase db restore --file backup_20260312.sql

# 3. Verificar datos
supabase db dump -t jobs

# 4. Reiniciar servicios
gcloud run services update renombradorarchivosgdrive-worker-v2 \
  --traffic=100 \
  --region=us-central1
```

**Tiempo estimado:** 15 minutos

### Procedimiento 3: Git Reset (Código)

**Síntoma:** Último commit introdujo bug crítico

**Pasos:**
```bash
# 1. Identificar commit funcional
git log --oneline -10

# 2. Reset a commit anterior (CONSERVANDO CAMBIOS)
git reset --soft HEAD~1

# 3. Crear branch de hotfix
git checkout -b hotfix/v3.1.3-critical-bug

# 4. Fix y commit
git add .
git commit -m "hotfix: critical bug fix

CONTEXT:
- ESTADO: Revertido commit xxx que causaba error 500
- ARCHIVOS: services/api-server/src/main.py
- FIX: Removida línea que causaba exception
- TEST: Manual testing exitoso
- NEXT: Deploy urgente a producción

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

# 5. Deploy
python deployment/deploy_runner.py
```

**Tiempo estimado:** 10 minutos

---

## 🚨 DISASTER SCENARIOS

### Escenario 1: Regional Outage (us-central1)

**Síntoma:** Toda la región us-central1 está down

**Impacto:** 100% downtime

**RTO:** 4-24 horas (depende de Google)

**Plan de Acción:**
1. **Verificar estado de Google Cloud:**
   ```bash
   gcloud services health-check list
   ```

2. **Comunicar a usuarios:**
   - Email: "Estamos experimentando problemas..."
   - Status page: Actualizar estado

3. **Si es extended outage (>4hs):**
   - Considerar deploy en región alternativa (e.g., southamerica-east1)
   - Reconfigurar DNS

**Prevención:**
- Multi-regional deployment (futuro V4.0)

---

### Escenario 2: Data Corruption

**Síntoma:** Base de datos corrupta, datos inconsistentes

**Impacto:** Pérdida de configuraciones de jobs

**RTO:** 1 hora

**Plan de Acción:**
1. **Detectar corrupción:**
   ```bash
   supabase db dump --schema-only | grep "ERROR"
   ```

2. **Parar servicios inmediatamente:**
   ```bash
   gcloud run services update renombradorarchivosgdrive-worker-v2 --no-traffic
   ```

3. **Restaurar backup más reciente:**
   ```bash
   supabase db restore --file backup_20260312.sql
   ```

4. **Verificar integridad:**
   ```bash
   supabase db dump -t jobs | jq '.data | length'
   ```

5. **Reiniciar servicios:**
   ```bash
   gcloud run services update renombradorarchivosgdrive-worker-v2 --traffic=100
   ```

**Prevención:**
- Backups diarios automatizados
- Validación de integridad semanal

---

### Escenario 3: Security Breach

**Síntomo:** Acceso no autorizado detectado

**Impacto:** Exposición de datos de clientes

**RTO:** Variable (depende de severidad)

**Plan de Acción:**
1. **Contener breach:**
   ```bash
   # Rotar todas las secrets
   gcloud secrets versions access latest --secret="GEMINI_API_KEY"
   gcloud secrets add-version --secret="GEMINI_API_KEY" --data-file=new_key.txt

   # Revocar tokens OAuth comprometidos
   ```

2. **Investigar:**
   ```bash
   # Verificar logs de acceso
   gcloud logs read --filter="protoPayload.authenticationInfo.principalEmail:attacker"
   ```

3. **Comunicar:**
   - Notificar usuarios afectados
   - Reportar a Google Security

4. **Remediar:**
   - Deploy fix de seguridad
   - Forzar re-login de todos los usuarios

**Prevención:**
- Security reviews periódicos
- Penetration testing anual
- Rate limiting ya implementado

---

### Escenario 4: Vendor Lock-in (Google Gemini Down)

**Síntomo:** Gemini API no responde

**Impacto:** No se pueden procesar documentos

**RTO:** Variable (depende de Google)

**Plan de Acción:**
1. **Verificar estado:**
   ```bash
   curl https://generativelanguage.googleapis.com/v1beta/models
   ```

2. **Si es extended outage (>1hora):**
   - Cambiar a modelo alternativo (GPT-4o)
   - Configurar fallback en AgentFactory

3. **Comunicar a usuarios:**
   - "Estamos experimentando problemas con nuestro proveedor de IA..."

**Prevención:**
- Fallback a modelo alternativo (futuro V4.0)
- Queue de procesamiento (ya implementado con Cloud Tasks)

---

## 📋 CHECKLIST DE RECUPERACIÓN

### Pre-Desastre (Preparación)
- [ ] Backups automatizados configurados
- [ ] Procedimientos documentados
- [ ] Equipo entrenado
- [ ] Alertas configuradas
- [ ] Contactos de emergencia actualizados

### Durante Desastre (Respuesta)
- [ ] Detectar y diagnosticar problema
- [ ] Activar plan de contingencia
- [ ] Comunicar a stakeholders
- [ ] Documentar incidente

### Post-Desastre (Recuperación)
- [ ] Verificar que todo funciona
- [ ] Restaurar servicios
- [ ] Análisis post-incidente
- [ ] Implementar mejoras
- [ ] Actualizar documentación

---

## 📞 CONTACTOS DE EMERGENCIA

| Rol | Nombre | Email | Teléfono |
|-----|--------|-------|----------|
| **Lead Developer** | Gonzalo Recalde | gonzalo.f.recalde@gmail.com | +54 9 11 XXXX-XXXX |
| **Cliente Piloto** | Diego Cutignola | diego@estudioanc.com.ar | +54 9 11 XXXX-XXXX |
| **Google Support** | - | - | Available 24/7 |

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión: Semestral

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
