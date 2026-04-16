# GitHub Actions CI/CD Setup

## ¿Qué hace?

Automatiza el deployment de los 3 servicios:
- **Frontend** → Cloud Run
- **API Server** → Cloud Run
- **Worker** → Cloud Run

### Triggers:
- **Pull Request**: Build y test (NO deploy a producción)
- **Push a main**: Build + Deploy automático a producción

---

## 🔧 Configuración Requerida (UNA SOLA VEZ)

### Paso 1: Crear Service Account en GCP

```bash
# Crear Service Account
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer" \
  --project=cloud-functions-474716
```

### Paso 2: Dar permisos a la Service Account

```bash
# Permiso para deploy a Cloud Run
gcloud projects add-iam-policy-binding cloud-functions-474716 \
  --member="serviceAccount:github-actions-deployer@cloud-functions-474716.iam.gserviceaccount.com" \
  --role="roles/run.developer"

# Permiso para push/push de imágenes Docker
gcloud projects add-iam-policy-binding cloud-functions-474716 \
  --member="serviceAccount:github-actions-deployer@cloud-functions-474716.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Permiso para acceder a secrets y configuraciones
gcloud projects add-iam-policy-binding cloud-functions-474716 \
  --member="serviceAccount:github-actions-deployer@cloud-functions-474716.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Paso 3: Crear y descargar la key JSON

```bash
# Crear key
gcloud iam service-accounts keys create gcp-sa-key.json \
  --iam-account="github-actions-deployer@cloud-functions-474716.iam.gserviceaccount.com"

# El archivo gcp-sa-key.json se descarga
```

### Paso 4: Agregar el secret a GitHub

1. Ir a: https://github.com/CENFARG/renameDriverFolders/settings/secrets/actions
2. Click en "New repository secret"
3. Name: `GCP_SA_KEY`
4. Value: **Contenido completo del archivo `gcp-sa-key.json`**
5. Click "Add secret"

---

## 🚀 Uso

### Deploy automático (push a main)
```bash
git add .
git commit -m "mi cambio"
git push origin main
```
→ GitHub Actions hace build y deploy automáticamente

### Deploy solo cuando se aprueba el PR
```bash
git checkout -b mi-feature
# hacer cambios
git add .
git commit -m "mi feature"
git push origin mi-feature
```
→ Crear PR en GitHub
→ Al hacer merge a main, se deploya automáticamente

---

## 📊 Monitorear deployments

Ir a: https://github.com/CENFARG/renameDriverFolders/actions

Vas a ver:
- ✅ Workflows ejecutándose
- 📦 Logs de cada paso
- 🔴 Errores si falla algo

---

## ⚠️ Seguridad

- **Nunca** commitear `gcp-sa-key.json` en el repo
- El archivo está en `.gitignore` por defecto
- Solo está guardado como secret en GitHub (encriptado)

---

## 🔍 Troubleshooting

### Error: "Permission denied"
→ Verificá que la Service Account tenga los roles correctos

### Error: "GCP_SA_KEY not found"
→ Verificaste que el secret se llame exactamente `GCP_SA_KEY` (mayúsculas)

### Workflow no se ejecuta
→ Verificá que los paths del workflow coincidan con los archivos modificados

---

## 📝 Notas

- Los workflows solo se ejecutan cuando hay cambios en `services/*/` o en los mismos workflows
- Si cambiás código en múltiples servicios, se deployan todos los afectados
- Los PRs hacen build pero NO deployan a producción (solo testing)
