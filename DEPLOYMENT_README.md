# 🚀 Deployment - Resumen Ejecutivo

## ✅ ARCHIVOS CREADOS PARA DEPLOYMENT

### **Guías y Scripts:**
1. ✅ `DEPLOYMENT_GUIDE.md` - Guía paso a paso completa (manual)
2. ✅ `deploy.sh` - Script automatizado de deployment
3. ✅ `.env.deploy.example` - Template de configuración

---

## 🎯 OPCIONES DE DEPLOYMENT

### **Opción 1: Script Automatizado (Recomendado)** ⚡

**Pasos:**
```bash
# 1. Copiar template de configuración
cp .env.deploy.example .env.deploy

# 2. Editar con tus valores
nano .env.deploy  # o tu editor favorito

# 3. Hacer ejecutable el script
chmod +x deploy.sh

# 4. Ejecutar
./deploy.sh
```

**Tiempo:** ~20-30 minutos  
**Dificultad:** Fácil  
**Automatiza:** APIs, Service Accounts, Builds, Deploys, Cloud Tasks, Scheduler

---

### **Opción 2: Manual con Guía** 📖

**Pasos:**
```bash
# Seguir DEPLOYMENT_GUIDE.md paso a paso
# Copiar y pegar comandos uno por uno
```

**Tiempo:** ~40-50 minutos  
**Dificultad:** Media  
**Ventaja:** Mayor control y comprensión

---

## 📋 CHECKLIST PRE-DEPLOYMENT

Antes de deployar, asegúrate de tener:

### **Google Cloud:**
- [ ] Cuenta de GCP con billing habilitado
- [ ] Proyecto creado
- [ ] `gcloud` CLI instalado
- [ ] Autenticado con `gcloud auth login`

### **Credenciales:**
- [ ] OAuth Client ID (de Google Cloud Console)
- [ ] Gemini API Key
- [ ] Supabase URL y Key (si usas Supabase)

### **Configuración:**
- [ ] Dominios autorizados definidos
- [ ] Folder IDs de Drive identificados
- [ ] Jobs configurados (al menos uno de prueba)

---

## 🔧 CONFIGURACIÓN MÍNIMA REQUERIDA

### **Secrets a Crear:**
```bash
oauth-client-id       # OAuth Client ID de Google
gemini-api-key        # API Key de Gemini
supabase-url          # URL de Supabase (opcional)
supabase-key          # Key de Supabase (opcional)
```

### **Service Accounts:**
```bash
worker-renombrador    # Para el Worker
api-server            # Para el API Server
scheduler-trigger     # Para Cloud Scheduler
```

### **Recursos de GCP:**
```bash
Cloud Run Services:
  - api-server (público)
  - worker-renombrador (privado)

Cloud Tasks:
  - document-processing-queue

Cloud Scheduler:
  - daily-processing (o el schedule que necesites)
```

---

## 🎯 DESPUÉS DEL DEPLOYMENT

### **1. Configurar Supabase**

Ejecutar SQL en Supabase:
```sql
-- Ver DEPLOYMENT_GUIDE.md sección 7.1
CREATE TABLE app_config (...);
CREATE TABLE jobs (...);
INSERT INTO jobs VALUES (...);
```

### **2. Test Health Checks**

```bash
# API Server
curl https://api-server-xxx.run.app/health

# Respuesta esperada:
{
  "status": "healthy",
  "service": "api-server",
  "version": "2.0.0",
  "oauth_enabled": true,
  "tasks_enabled": true
}
```

### **3. Test Manual Job**

Necesitas un OAuth token real:
- Opción 1: [Google OAuth Playground](https://developers.google.com/oauthplayground/)
- Opción 2: Implementar frontend con Google Sign-In

```bash
curl -X POST https://api-server-xxx.run.app/api/v1/jobs/manual \
  -H "Authorization: Bearer YOUR_OAUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"folder_id": "YOUR_FOLDER_ID", "job_type": "generic"}'
```

### **4. Test Scheduled Job**

```bash
# Trigger manual del scheduler
gcloud scheduler jobs run daily-processing --location=us-central1

# Ver logs
gcloud logging read "resource.type=cloud_run_revision" --limit 20
```

---

## 📊 COSTOS ESTIMADOS

### **Tier Gratuito:**
- Cloud Run: 2M requests/mes
- Cloud Vision: 1,000 unidades/mes
- Cloud Tasks: 1M ops/mes
- Cloud Scheduler: Primeros 3 jobs gratis

### **Uso Típico (estimado):**
- **Bajo uso** (100 docs/día): ~$5-10/mes
- **Uso medio** (1,000 docs/día): ~$20-30/mes
- **Uso alto** (10,000 docs/día): ~$100-150/mes

**Principales costos:**
1. Cloud Vision OCR (después de 1,000 unidades)
2. Cloud Run (compute time)
3. Cloud Storage (si guardas muchos archivos)

---

## 🔍 MONITORING POST-DEPLOYMENT

### **Dashboards a Revisar:**
```bash
# Cloud Run
https://console.cloud.google.com/run?project=YOUR_PROJECT_ID

# Cloud Tasks
https://console.cloud.google.com/cloudtasks?project=YOUR_PROJECT_ID

# Cloud Scheduler
https://console.cloud.google.com/cloudscheduler?project=YOUR_PROJECT_ID

# Logs
https://console.cloud.google.com/logs?project=YOUR_PROJECT_ID
```

### **Métricas Clave:**
- Request count (cuántos jobs se procesan)
- Error rate (tasa de errores)
- Response latency (tiempo de respuesta)
- Memory usage (especialmente Worker con OCR)
- Cloud Vision API usage (para controlar costos)

---

## ⚠️ TROUBLESHOOTING COMÚN

### **Error: "Permission denied"**
**Solución:** Verificar que service accounts tienen los roles correctos
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID
```

### **Error: "Secret not found"**
**Solución:** Crear secrets en Secret Manager
```bash
gcloud secrets list
```

### **Error: "Cloud Tasks queue not found"**
**Solución:** Crear queue
```bash
gcloud tasks queues create document-processing-queue --location=us-central1
```

### **Error: "OIDC verification failed"**
**Solución:** Verificar que Cloud Scheduler usa el service account correcto y el audience es la URL del API Server

---

## 🎉 DEPLOYMENT EXITOSO

Si todo salió bien, deberías tener:

✅ API Server funcionando  
✅ Worker funcionando  
✅ Cloud Tasks queue activa  
✅ Cloud Scheduler configurado  
✅ Health checks respondiendo OK  
✅ Logs mostrando actividad  

**¡Sistema listo para procesar documentos!** 🚀

---

## 📞 PRÓXIMOS PASOS

1. **Configurar Frontend** - Para que usuarios puedan enviar jobs manuales
2. **Agregar Jobs Reales** - Configurar jobs de producción en Supabase
3. **Configurar Alertas** - Para monitorear errores
4. **Optimizar Costos** - Ajustar recursos según uso real
5. **Implementar Tests** - Para validar cambios futuros

---

## 📚 DOCUMENTACIÓN RELACIONADA

- `DEPLOYMENT_GUIDE.md` - Guía detallada paso a paso
- `SISTEMA_COMPLETO.md` - Arquitectura y componentes
- `services/api-server/README.md` - API Server usage
- `services/worker-renombrador/README.md` - Worker usage
- `OAUTH_SETUP_GUIDE.md` - OAuth configuration

---

**¿Necesitas ayuda con el deployment?**  
Revisa `DEPLOYMENT_GUIDE.md` o ejecuta `./deploy.sh` 🚀
