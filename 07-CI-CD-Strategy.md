# 🚀 07. CI/CD STRATEGY
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Definir la estrategia de Integración Continua (CI) y Deployment Continuo (CD) para el sistema **Renombrador** V3.1.2.

---

## 📊 ESTADO ACTUAL

| Aspecto | Estado | Herramienta |
|---------|--------|-------------|
| **CI (Tests)** | ❌ 0% | No implementado |
| **CD (Deploy)** | ⚠️ Manual | Scripts Python + gcloud CLI |
| **IaC** | ⚠️ Parcial | Docker, sin Terraform |
| **Monitoring** | ⚠️ Básico | Google Cloud Logging |

---

## 🎯 ESTRATEGIA PROPUESTA

### Fase 1: CI (Integración Continua)

#### Pipeline de Tests

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop, main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          pytest tests/unit/ --cov=services --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: cd services/frontend && npm ci

      - name: Run tests
        run: cd services/frontend && npm test -- --code-coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Python lint
        run: |
          pip install flake8 black
          flake8 services/
          black --check services/

      - name: TypeScript lint
        run: |
          cd services/frontend
          npm run lint
```

---

### Fase 2: CD (Deployment Continuo)

#### Pipeline de Deploy

```yaml
# .github/workflows/cd.yml
name: CD

on:
  push:
    branches: [main]
  workflow_dispatch:  # Deploy manual

jobs:
  deploy-api-server:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure gcloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Build and push API Server
        run: |
          gcloud builds submit \
            --config services/api-server/cloudbuild.yaml \
            --substitutions=_IMAGE_NAME=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-api-server-v2 \
            .

      - name: Deploy API Server
        run: |
          gcloud run deploy renombradorarchivosgdrive-api-server-v2 \
            --image=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-api-server-v2 \
            --region=us-central1 \
            --platform=managed

  deploy-worker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure gcloud
        uses: google-github-actions/auth@v1

      - name: Build and push Worker
        run: |
          gcloud builds submit \
            --config services/worker-renombrador/cloudbuild.yaml \
            --substitutions=_IMAGE_NAME=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-worker-v2 \
            .

      - name: Deploy Worker
        run: |
          gcloud run deploy renombradorarchivosgdrive-worker-v2 \
            --image=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-worker-v2 \
            --region=us-central1 \
            --platform=managed

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure gcloud
        uses: google-github-actions/auth@v1

      - name: Build and push Frontend
        run: |
          gcloud builds submit \
            --config services/frontend/cloudbuild.yaml \
            --substitutions=_IMAGE_NAME=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-frontend-v2 \
            .

      - name: Deploy Frontend
        run: |
          gcloud run deploy renombradorarchivosgdrive-frontend-v2 \
            --image=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-frontend-v2 \
            --region=us-central1 \
            --platform=managed
```

---

### Fase 3: IaC (Infrastructure as Code)

#### Terraform para Google Cloud

```hcl
# main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = "cloud-functions-474716"
  region  = "us-central1"
}

# Cloud Run Services
resource "google_cloud_run_service" "api_server" {
  name     = "renombradorarchivosgdrive-api-server-v2"
  location = "us-central1"

  template {
    spec {
      containers {
        image = "gcr.io/cloud-functions-474716/renombradorarchivosgdrive-api-server-v2"
      }
    }
  }
}

# Cloud Tasks Queue
resource "google_cloud_tasks_queue" "rename_queue" {
  name     = "rename-queue"
  location = "us-central1"

  rate_limits {
    max_concurrent_dispatches = 1000
    max_dispatches_per_second = 500
  }

  retry_config {
    max_attempts = 3
    max_retry_duration = "900s"
  }
}

# Cloud Scheduler
resource "google_cloud_scheduler_job" "rename_jobs_trigger" {
  name             = "rename-jobs-trigger"
  schedule         = "0 8 * * *"
  time_zone        = "America/Argentina/Buenos_Aires"

  http_target {
    http_method = "POST"
    uri         = google_cloud_run_service.api_server.status[0].url
    oidc_token {
      service_account_email = var.scheduler_sa_email
    }
  }
}
```

---

## 🔄 WORKFLOW DE DEVELOPMENT

### Branch Strategy

```
main (producción)
  ↑
  └── develop (staging)
        ↑
        └── feature/* (features)
        └── bugfix/* (bugs)
        └── hotfix/* (emergencias)
```

### Reglas

1. **Develop → Main:**
   - Requiere Pull Request
   - Debe pasar todos los tests
   - Requiere approval de 1 reviewer
   - Deploy automático a staging

2. **Main:**
   - Deploy automático a producción
   - Tags para versiones (v3.1.3, etc.)

---

## 📊 MATRIZ DE RESPONSABILIDAD

| Acción | Quién | Automatizado |
|--------|-------|--------------|
| Tests | CI | ✅ |
| Build | CI | ✅ |
| Deploy Staging | CD (develop) | ✅ |
| Deploy Production | CD (main) | ✅ |
| Rollback | Manual | ⚠️ |
| Monitoring | Manual | ⚠️ |

---

## 🚀 IMPLEMENTACIÓN ROADMAP

### Fase 1: CI Basics (V3.2)
- [ ] Configurar GitHub Actions
- [ ] Agregar tests unitarios
- [ ] Agregar linting
- [ ] Coverage reports

### Fase 2: CD (V3.2)
- [ ] Deploy automático a staging
- [ ] Deploy automático a producción
- [ ] Rollback scripts

### Fase 3: IaC (V4.0)
- [ ] Terraform para infraestructura
- [ ] Terraform para secrets
- [ ] Terraform para monitoring

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** V3.2 (Q2 2026)

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
