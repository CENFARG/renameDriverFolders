# Lección Aprendida: Renombrado de Servicios Cloud Run

**Fecha:** 2025-12-18  
**Proyecto:** renameDriverFolders  
**Contexto:** Renombrado organizacional de servicios Cloud Run con prefijo `renombradorarchivosgdrive-`

---

## Metadata

```yaml
---
tipo: lección_aprendida
proyecto: renameDriverFolders
fecha: 2025-12-18
tags: [cloud-run, gcr, docker, naming-conventions, cloud-build]
complejidad: media
impacto: alto
---
```

---

## Directivas Algorítmicas

### Directiva 1: Nomenclatura de Imágenes en GCR

**Condition:** Construyendo imágenes Docker para Google Container Registry (GCR)  
**Trigger:** Ejecutando `gcloud builds submit` con nombre de imagen que contiene mayúsculas  
**Rule:** MUST usar SOLO minúsculas en nombres de imágenes Docker (repository name)  
**Reasoning:** GCR sigue las convenciones estrictas de Docker Registry que requieren nombres de repositorio en minúsculas. Los tags pueden contener mayúsculas, pero los nombres de imagen no.

**Ejemplo de Error:**
```
ERROR: (gcloud.builds.submit) INVALID_ARGUMENT: invalid image name
```

**Solución:**
```yaml
# ❌ INCORRECTO
images:
  - 'gcr.io/$PROJECT_ID/renombradorArchivosGdrive-api-server-v2:latest'

# ✅ CORRECTO
images:
  - 'gcr.io/$PROJECT_ID/renombradorarchivosgdrive-api-server-v2:latest'
```

**Checklist de Validación:**
- [ ] Nombre de imagen contiene solo: `[a-z0-9-._]`
- [ ] No hay mayúsculas en el nombre del repositorio
- [ ] Tags pueden tener mayúsculas (son case-sensitive)

---

### Directiva 2: Formato de Timeout en Cloud Build

**Condition:** Configurando `cloudbuild.yaml` con campo `timeout`  
**Trigger:** Build falla con error "Illegal duration format; duration must end with 's'"  
**Rule:** MUST usar formato de segundos con sufijo `'s'` (ej: `'1200s'`), NO formato de minutos con `'m'`  
**Reasoning:** Cloud Build espera duración en formato `google.protobuf.Duration` que requiere sufijo 's' para segundos

**Ejemplo de Error:**
```
Invalid value at 'build.timeout' (google.protobuf.Duration), field: build.timeout
description: Illegal duration format; duration must end with 's'
```

**Solución:**
```yaml
# ❌ INCORRECTO
timeout: '20m'

# ✅ CORRECTO
timeout: '1200s'  # 20 minutos = 1200 segundos
```

**Conversión Rápida:**
- 5 minutos = `'300s'`
- 10 minutos = `'600s'`
- 20 minutos = `'1200s'`
- 30 minutos = `'1800s'`

---

### Directiva 3: Actualización de Referencias Cruzadas en Arquitecturas Distribuidas

**Condition:** Renombrando servicios en arquitectura de microservicios (Frontend → API → Worker)  
**Trigger:** Servicios desplegados con nuevos nombres pero sin comunicación entre ellos  
**Rule:** MUST actualizar TODAS las referencias de URLs en:
1. Variables de entorno de servicios dependientes
2. Archivos de configuración de aplicaciones
3. Rebuild y redeploy de servicios que consumen las URLs

**Reasoning:** Los servicios se comunican mediante URLs que cambian al renombrar. Las referencias antiguas quedan "hardcoded" hasta que se actualicen explícitamente.

**Checklist de Actualización:**

1. **Identificar Dependencias:**
   ```
   Frontend → API Server (apiUrl en environment.prod.ts)
   API Server → Worker (WORKER_URL en env vars)
   Cloud Scheduler → Worker (target URL en job config)
   ```

2. **Actualizar Variables de Entorno:**
   ```bash
   # Obtener nueva URL
   NEW_WORKER_URL=$(gcloud run services describe <NEW_SERVICE_NAME> --region <REGION> --format="value(status.url)")
   
   # Actualizar servicio dependiente
   gcloud run services update <DEPENDENT_SERVICE> \
     --region <REGION> \
     --update-env-vars WORKER_URL=$NEW_WORKER_URL
   ```

3. **Actualizar Archivos de Configuración:**
   ```typescript
   // services/frontend/src/environments/environment.prod.ts
   export const environment = {
       production: true,
       apiUrl: 'https://<NEW_API_SERVICE_URL>',  // ← Actualizar aquí
       oauthClientId: '...'
   };
   ```

4. **Rebuild y Redeploy:**
   ```bash
   # Build nueva imagen con configuración actualizada
   gcloud builds submit --config=services/frontend/cloudbuild.yaml .
   
   # Redeploy servicio
   gcloud run deploy <SERVICE_NAME> --image <NEW_IMAGE> ...
   ```

**Orden de Ejecución:**
1. Deploy servicios de "hoja" primero (Worker)
2. Actualizar servicios intermedios (API Server)
3. Actualizar servicios de "raíz" al final (Frontend)

---

## Checklist de Validación Post-Renombrado

### Pre-Deploy
- [ ] Todos los nombres de imagen están en minúsculas
- [ ] Formato de timeout es `'<segundos>s'`
- [ ] Identificadas todas las referencias cruzadas

### Post-Deploy
- [ ] Health checks de todos los servicios responden OK
- [ ] Variables de entorno actualizadas correctamente
- [ ] Servicios pueden comunicarse entre sí
- [ ] Frontend puede llamar al API Server
- [ ] API Server puede llamar al Worker

### Limpieza
- [ ] Servicios antiguos eliminados
- [ ] Imágenes antiguas eliminadas (opcional)
- [ ] Documentación actualizada con nuevos nombres

---

## Aplicación Futura

### Template de Renombrado de Servicios

```bash
#!/bin/bash
# Template para renombrar servicios Cloud Run

# 1. Definir nombres
OLD_SERVICE_NAME="old-service"
NEW_SERVICE_NAME="new-service"
PROJECT_ID="your-project-id"
REGION="us-central1"

# 2. Actualizar cloudbuild.yaml (manual)
# Cambiar nombre de imagen a minúsculas

# 3. Build nueva imagen
gcloud builds submit --config=services/${OLD_SERVICE_NAME}/cloudbuild.yaml .

# 4. Deploy nuevo servicio
gcloud run deploy ${NEW_SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${NEW_SERVICE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  # ... otras flags

# 5. Obtener nueva URL
NEW_URL=$(gcloud run services describe ${NEW_SERVICE_NAME} --region ${REGION} --format="value(status.url)")

# 6. Actualizar servicios dependientes
# (manual: actualizar env vars, archivos de config, rebuild)

# 7. Validar
curl ${NEW_URL}/health

# 8. Eliminar servicio antiguo (después de validación)
gcloud run services delete ${OLD_SERVICE_NAME} --region ${REGION} --quiet
```

---

## Valor de Esta Lección

Esta lección documenta **errores comunes y sus soluciones** en el proceso de renombrado de servicios Cloud Run, específicamente:

1. **Nomenclatura de GCR:** Evita errores de build por mayúsculas
2. **Formato de Timeout:** Evita errores de configuración en Cloud Build
3. **Referencias Cruzadas:** Asegura que servicios renombrados puedan comunicarse

**Tiempo Ahorrado:** ~30 minutos en futuros renombrados al evitar estos errores

---

**Preparado por:** Gemini (Antigravity Agent)  
**Tipo:** Lección Aprendida (Algorítmica)  
**Fecha:** 2025-12-18  
**Versión:** 1.0
