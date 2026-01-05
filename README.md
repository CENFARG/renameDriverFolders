# Renombrador Archivos GDrive (#amBotHsOS) - v2.0.0

## Descripción General
Sistema de procesamiento inteligente de documentos en Google Drive. Utiliza IA (Gemini 2.0 Flash) para analizar, categorizar y renombrar archivos automáticamente basándose en su contenido visual y textual.

**Arquitectura v2.0.0:**
- **Microservicio Worker:** Procesa los documentos (OCR + IA).
- **Microservicio API Server:** Gestiona la autenticación OAuth2 y el dispatch de tareas vía Cloud Tasks.
- **Frontend Angular:** Interfaz gráfica para disparar jobs manuales.
- **Core Package:** Lógica compartida en `packages/core-renombrador`.

## 🚀 Despliegue en Producción (Cloud Run)

### IMPORTANTE: Build Context
Debido a la estructura de monorepo, los despliegues **DEBEN** realizarse desde la raíz del proyecto para que Docker pueda acceder al paquete `core-renombrador`.

### 1. Desplegar Worker
```powershell
gcloud builds submit --config services/worker-renombrador/cloudbuild.yaml --substitutions=_IMAGE_NAME=gcr.io/cloud-functions-474716/renombradorarchivosgdrive-worker-v2 . --project=cloud-functions-474716
```

### 2. Desplegar API Server
```powershell
# Usar el deploy_runner.py para asegurar el mapeo de variables de entorno correcto
python deployment/deploy_runner.py
```

## 🛠️ Configuración (Worker)
El Worker utiliza una lógica de renombrado resiliente (`CaseInsensitiveDict` + Aliases). 
- **Alias Soportados:** `issuer`, `entity`, `type`, `concept`.
- **Formato por Defecto:** `{date}_{keywords}_{ext}`

## 📖 Documentación y Auditoría
- [Lecciones Aprendidas](.lessons/lesson_20260105_full_stabilization.md)
- [Auditoría de Seguridad](.lessons/audit_20260105_security_quality.md)
- [Memory Bank](.memorybank/)

## 📝 Registro de Cambios Recientes
- **v2.0.24:** Estabilización total, fix de `KeyError`, robustez en nombres y corrección de auth UI.
- **v2.0.0:** Migración a arquitectura de microservicios y Agno (antiguo Phidata).

---
*Desarrollado con ❤️ por Anti-Gravity Agent para Gonzalo Recalde (#CENF)*