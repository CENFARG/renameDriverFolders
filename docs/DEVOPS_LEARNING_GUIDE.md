# DevOps & Automation - Guía de Aprender desde Cero

## 🎯 ¿Qué es DevOps?

**DevOps** = **Dev**elopment (Desarrollo) + **Op**eration**s** (Operaciones)

Es una **cultura y conjunto de prácticas** que busca:
1. **Automatizar** tareas repetitivas
2. **Acelerar** el ciclo de desarrollo
3. **Reducir errores** humanos
4. **Hacer que el código llegue a producción** rápido y seguro

### Analogía Simple
Imagina que tienes una panadería:
- **Sin DevOps**: Cada vez que horneas un pan, mides ingredientes manualmente, mezclas a mano, esperas, sacas del horno, empacas manualmente.
- **Con DevOps**: Tienes una máquina que hace todo automáticamente. Pones la receta (código), presionas un botón, y sale el pan listo.

---

## 🧩 Componentes Clave de DevOps

### **1. Version Control (Control de Versiones)**
**Qué es:** Sistema para rastrear cambios en el código.  
**Herramienta:** Git + GitHub/GitLab

**Concepto:**
- Cada cambio queda registrado (como un historial)
- Puedes volver atrás si algo sale mal
- Múltiples personas pueden trabajar sin pisarse

**Comandos básicos:**
```bash
git add .                    # Preparar cambios
git commit -m "Mensaje"      # Guardar cambios
git push                     # Enviar a servidor remoto (GitHub)
```

---

### **2. CI/CD (Continuous Integration / Continuous Deployment)**
**Qué es:** Automatización del proceso desde que escribes código hasta que llega a producción.

**Continuous Integration (Integración Continua):**
- Cada vez que haces `git push`, automáticamente:
  1. Se ejecutan los tests
  2. Se verifica que el código compile
  3. Se ejecutan análisis de calidad (linting)

**Continuous Deployment (Despliegue Continuo):**
- Si todos los tests pasan:
  1. Se construye la aplicación (Docker image)
  2. Se sube a producción automáticamente

**Flujo Visual:**
```
Código → Push a GitHub → Tests automáticos → Build Docker → Deploy a Cloud Run
         (desarrollador)    (GitHub Actions)    (Cloud Build)   (Google Cloud)
```

**Herramientas:**
- GitHub Actions
- Google Cloud Build
- Jenkins
- GitLab CI/CD

---

### **3. Containerization (Contenedorización)**
**Qué es:** Empaquetar tu aplicación con TODAS sus dependencias en un "contenedor" portátil.  
**Herramienta:** Docker

**Problema que resuelve:**
- "En mi máquina funciona" → ¿Por qué no funciona en producción?
- Docker garantiza que funcione igual en todos lados

**Dockerfile = Receta**
```dockerfile
# 1. Base: sistema operativo + Python
FROM python:3.11-slim

# 2. Instalar dependencias del sistema
RUN apt-get update && apt-get install -y poppler-utils

# 3. Copiar código
COPY . /app
WORKDIR /app

# 4. Instalar dependencias de Python
RUN pip install -r requirements.txt

# 5. Comando para ejecutar
CMD ["python", "main.py"]
```

**Comandos básicos:**
```bash
docker build -t mi-app .           # Construir imagen
docker run mi-app                  # Ejecutar contenedor
docker push gcr.io/project/mi-app  # Subir a registry
```

---

### **4. Infrastructure as Code (IaC)**
**Qué es:** Definir tu infraestructura (servidores, redes, etc.) en archivos de código.

**Problema que resuelve:**
- Sin IaC: clicks manuales en consola → error humano, no reproducible
- Con IaC: archivo que describe todo → reproducible, versionado

**Ejemplo con Terraform:**
```hcl
resource "google_cloud_run_service" "app" {
  name     = "rename-driver-folders"
  location = "us-central1"
  
  template {
    spec {
      containers {
        image = "gcr.io/project/app:latest"
        env {
          name  = "GEMINI_API_KEY"
          value = var.gemini_key
        }
      }
    }
  }
}
```

---

### **5. Monitoring & Observability**
**Qué es:** Ver qué está pasando en tu aplicación en producción.

**Tres Pilares:**
1. **Logs**: Mensajes que escribe tu app ("Usuario X hizo Y")
2. **Metrics**: Números (requests/seg, CPU%, memoria)
3. **Traces**: Seguimiento de una petición de principio a fin

**Herramientas:**
- Google Cloud Logging
- Prometheus + Grafana
- Datadog

**Dashboard ejemplo:**
```
┌─────────────────────────────────┐
│ Error Rate:    0.5% ┃ ✅        │
│ Response Time: 234ms ┃ ✅       │
│ Requests/min:  1,234 ┃ ⚠️ Alto  │
└─────────────────────────────────┘
```

---

## 🛠️ Herramientas para Tu Proyecto

### **Stack Recomendado:**
1. **Git + GitHub** - Control de versiones
2. **GitHub Actions** - CI/CD pipeline
3. **Docker** - Contenedorización
4. **Google Cloud Run** - Hosting serverless
5. **Google Cloud Build** - Build automation
6. **Cloud Logging + Monitoring** - Observabilidad

---

## 📝 Tu Primer Pipeline CI/CD

Voy a mostrarte cómo crear un pipeline completo:

### **Archivo `.github/workflows/deploy.yml`**
```yaml
name: Deploy to Cloud Run

# Cuándo se ejecuta
on:
  push:
    branches: [main]  # Solo cuando haces push a rama main

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      # 1. Descargar código
      - name: Checkout code
        uses: actions/checkout@v3
      
      # 2. Autenticarse con Google Cloud
      - name: Auth to GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      # 3. Setup Cloud SDK
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      # 4. Build Docker image
      - name: Build image
        run: |
          docker build -t gcr.io/${{ secrets.GCP_PROJECT }}/app:${{ github.sha }} .
          docker push gcr.io/${{ secrets.GCP_PROJECT }}/app:${{ github.sha }}
      
      # 5. Deploy a Cloud Run
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy rename-driver-folders \
            --image gcr.io/${{ secrets.GCP_PROJECT }}/app:${{ github.sha }} \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated
```

**¿Qué hace esto?**
1. Cada vez que haces `git push` a la rama `main`
2. GitHub Actions:
   - Descarga tu código
   - Construye la imagen Docker
   - La sube a Google Container Registry
   - Despliega a Cloud Run automáticamente

**Resultado:** Código en producción en 5-10 minutos, sin tocar nada manual.

---

## 🎓 Conceptos Clave para Entender

### **1. Build vs Deploy**
- **Build**: Convertir código fuente → ejecutable/imagen
- **Deploy**: Tomar ese ejecutable → ponerlo en servidor

### **2. Staging vs Production**
- **Staging**: Entorno de prueba (copia de producción)
- **Production**: Donde los usuarios reales usan la app

### **3. Blue-Green Deployment**
```
Antes: [Blue (v1.0) ← 100% tráfico]

Durante despliegue:
  [Blue (v1.0) ← 50%]
  [Green (v1.1) ← 50%]

Después (si todo OK):
  [Blue (v1.0) ← 0%]
  [Green (v1.1) ← 100%]

Si falla → rollback inmediato a Blue
```

### **4. Secrets Management**
**Problema:** ¿Dónde guardar API keys, passwords?

**❌ Nunca:**
- Hardcodear en código
- Commitear en Git

**✅ Usar:**
- GitHub Secrets (para CI/CD)
- Google Secret Manager (para runtime)
- Variables de entorno

```python
# ❌ MAL
api_key = "abc123xyz"

# ✅ BIEN
api_key = os.environ.get("API_KEY")
```

---

## 🚀 Roadmap de Aprendizaje Sugerido

### **Semana 1: Fundamentos**
- [ ] Aprender Git básico (add, commit, push, pull)
- [ ] Crear cuenta GitHub
- [ ] Hacer tu primer commit y push

### **Semana 2: Docker**
- [ ] Instalar Docker Desktop
- [ ] Crear tu primer Dockerfile
- [ ] Buildear y correr un contenedor localmente

### **Semana 3: CI/CD Básico**
- [ ] Crear archivo `.github/workflows/test.yml`
- [ ] Ejecutar tests automáticos en cada push
- [ ] Ver resultados en GitHub Actions tab

### **Semana 4: Deploy Automatizado**
- [ ] Configurar Secret Manager en GCP
- [ ] Crear pipeline de deploy a Cloud Run
- [ ] Hacer un cambio → ver deploy automático

---

## 📚 Recursos para Aprender Más

### **Videos/Cursos:**
- [GitHub Actions Tutorial](https://www.youtube.com/watch?v=R8_veQiYBjI) (inglés)
- [Docker en 100 Segundos](https://www.youtube.com/watch?v=Gjnup-PuquQ)
- [DevOps Roadmap](https://roadmap.sh/devops)

### **Documentación:**
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Docker Get Started](https://docs.docker.com/get-started/)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)

### **Práctica:**
- Crea un proyecto pequeño y despliégalo automáticamente
- Ejemplo: API Flask simple → Docker → Cloud Run → GitHub Actions

---

## ✅ Checklist: ¿Entendiste DevOps?

Puedes explicar:
- [ ] ¿Por qué usamos Git?
- [ ] ¿Qué problema resuelve Docker?
- [ ] ¿Qué es CI/CD y para qué sirve?
- [ ] ¿Qué hace un pipeline de GitHub Actions?
- [ ] ¿Dónde guardamos secrets/passwords?

Si respondes SÍ a todas, ¡entiendes lo básico! 🎉

---

**Siguiente Paso:** Implementar tu primer pipeline para `renameDriverFolders`
