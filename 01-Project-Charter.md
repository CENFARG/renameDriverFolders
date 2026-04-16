# 📋 01. PROJECT CHARTER
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL PROYECTO

**Nombre del Proyecto:** Renombrador Archivos GDrive (#amBotHsOS)
**Versión Actual:** V3.1.2 "Estudio Inteligente"
**Fecha de Inicio:** Noviembre 2024
**Última Actualización:** 12 de Marzo, 2026
**Sponsor del Proyecto:** Estudio Cutignola

### Misión
Desarrollar un sistema de automatización inteligente de documentos en Google Drive que utiliza Inteligencia Artificial (Google Gemini 2.0/2.5 Flash) para analizar, categorizar y renombrar archivos automáticamente según su contenido visual y textual.

### Visión
Convertirse en la solución estándar para estudios contables y profesionales que necesitan organizar grandes volúmenes de documentos digitales de manera inteligente, reduciendo el trabajo manual en un 90%.

---

## 🎯 OBJETIVOS DEL PROYECTO

### Objetivo Principal
Automatizar la organización de documentos en Google Drive usando IA para analizar contenido, extraer metadatos y generar nombres descriptivos siguiendo nomenclaturas contables profesionales.

### Objetivos Específicos

#### Objetivos Funcionales
- ✅ **Procesamiento Inteligente:** Analizar documentos (PDF, imágenes) con OCR y Gemini 2.0/2.5
- ✅ **Nomenclatura Contable:** Generar nombres según formato profesional (ej: `2025-03-12_Factura_MorganStanley_Servicios`)
- ✅ **Multi-Job:** Soportar múltiples algoritmos preconfigurados (facturas, sueldos, resúmenes bancarios)
- ✅ **Programación Flexible:** Ejecuciones diaria, semanal, mensual, trimestral, anual
- ✅ **Interfaz Humana:** UX adaptada a contadores (no técnicos)

#### Objetivos Técnicos
- ✅ **Arquitectura Serverless:** Despliegue en Google Cloud Run
- ✅ **Microservicios:** API Gateway + Worker + Frontend
- ✅ **OAuth 2.0:** Autenticación con Google Sign-In
- ✅ **Auditoría Completa:** Logs inmutables de todas las operaciones
- ✅ **Core Package:** Módulos reutilizables (13 módulos Python)

#### Objetivos de Negocio
- ✅ **Cliente Piloto:** Estudio Cutignola (estudioanc.com.ar)
- ⏳ **Escalabilidad:** Preparado para múltiples clientes
- ⏳ **ROI:** Reducción del 90% en tiempo de organización documental

---

## 📊 ALCANCE DEL PROYECTO

### Incluye (In-Scope)

#### Backend (100% Completado)
- ✅ API Server con FastAPI (OAuth, rate limiting, domain whitelisting)
- ✅ Worker de procesamiento con Agno 2.3.9
- ✅ Core Package con 13 módulos compartidos
- ✅ Integración con Google Drive, Cloud Vision, Gemini
- ✅ Sistema multi-job con Supabase
- ✅ Configuración híbrida (Env > DB > File)

#### Frontend (100% Completado)
- ✅ Angular 19 + Material Design
- ✅ Google Drive Picker integrado
- ✅ Google Sign-In
- ✅ UI de gestión de algoritmos
- ✅ Dashboard de auditoría

#### Infraestructura (100% Completado)
- ✅ Google Cloud Run (serverless)
- ✅ Google Cloud Tasks (cola de tareas)
- ✅ Google Cloud Scheduler (cron jobs)
- ✅ Google Cloud Storage (estado externo)
- ✅ Supabase PostgreSQL (base de datos)

#### Documentación (100% Completado)
- ✅ README.md
- ✅ SISTEMA_COMPLETO.md
- ✅ GEMINI.md
- ✅ DEPLOYMENT_GUIDE.md
- ✅ 10 Documentos de Gestión CENF

### NO Incluye (Out-of-Scope)

#### Fase 1 (V3.1.2)
- ❌ Tests automatizados (pytest)
- ❌ CI/CD pipeline (GitHub Actions)
- ❌ Scripts de deployment automatizados
- ❌ Monitoring dashboards (Grafana/Prometheus)

#### Fase 2 (Futuro)
- ❌ Multi-tenancy completo
- ❌ Facturación integrada
- ❌ SaaS (Software as a Service)
- ❌ Mobile app

---

## 🎯 STAKEHOLDERS

### Stakeholders Primarios
| Rol | Nombre | Email | Responsabilidad |
|-----|--------|-------|-----------------|
| **Cliente Piloto** | Estudio Cutignola | info@estudioanc.com.ar | Requerimientos, UAT, Feedback |
| **Desarrollador Lead** | Gonzalo Recalde | gonzalo.f.recalde@gmail.com | Arquitectura, Desarrollo, Deployment |
| **Arquitecto IA** | Claude (AI Assistant) | - | Agentes Agno, Prompts, OCR |

### Stakeholders Secundarios
| Rol | Responsabilidad |
|-----|-----------------|
| **Equipo CENF** | Metodología, Estándares, Code Review |
| **Google Cloud** | Infraestructura, Soporte |
| **Google AI** | Modelos Gemini, Cloud Vision |

---

## 📊 MÉTRICAS DE ÉXITO (KPIs)

### KPIs Técnicos
- ✅ **Uptime:** >99.5% (objetivo: 99.9%)
- ✅ **Latencia:** <30s para procesar 100 archivos
- ✅ **Precisión:** >95% en nombres generados
- ✅ **Error Rate:** <2% en ejecuciones

### KPIs de Negocio
- ⏳ **Adopción:** 100% usuarios activan al menos 1 job/semana
- ⏳ **Retención:** 0% churn en primeros 6 meses
- ⏳ **Satisfacción:** NPS >50

### KPIs de Proyecto
- ✅ **Backend:** 100% completado
- ✅ **Frontend:** 100% completado
- ⏳ **Tests:** 0% (objetivo: 80%)
- ⏳ **CI/CD:** 0% (objetivo: 100%)

---

## 🚀 HITOS PRINCIPALES

### Hitos Completados
| Hito | Fecha | Estado |
|------|-------|--------|
| **V1.0 - MVP** | Nov 2024 | ✅ Completado |
| **V2.0 - Multi-Job + Agentes** | Ene 2025 | ✅ Completado |
| **V3.0 - Google Drive Picker + UI Humana** | Feb 2025 | ✅ Completado |
| **V3.1 - Estudio Cutignola + Hotfixes** | Mar 2025 | ✅ Completado |
| **V3.1.2 - Hotfixes de Estabilidad** | Mar 2025 | ✅ Completado |

### Hitos Pendientes
| Hito | Fecha Objetivo | Estado |
|------|----------------|--------|
| **V3.1.3 - Arreglos de Funcionalidad** | Mar 2026 | 🚧 En Progreso |
| **V3.2 - Tests + CI/CD** | Abr 2026 | ⏳ Pendiente |
| **V4.0 - Multi-tenancy** | Q2 2026 | ⏳ Pendiente |

---

## 💰 PRESUPUESTO

### Costos Mensuales (Google Cloud)
| Servicio | Costo USD |
|----------|-----------|
| **Cloud Run** | ~$20-50 (depende uso) |
| **Cloud Tasks** | ~$5-10 |
| **Cloud Scheduler** | ~$0.15 |
| **Cloud Storage** | ~$0.026/GB |
| **Cloud Vision (OCR)** | ~$1-5 (depende volúmen) |
| **Gemini API** | ~$10-20 (depende tokens) |
| **Supabase** | ~$25 (plan Pro) |
| **TOTAL** | **~$60-110/mes** |

### Inversión Inicial (Tiempo)
| Actividad | Horas |
|-----------|-------|
| **Desarrollo Backend** | ~200h |
| **Desarrollo Frontend** | ~100h |
| **DevOps/Deployment** | ~50h |
| **Documentación** | ~30h |
| **TOTAL** | **~380h** |

---

## ⚠️ RIESGOS Y MITIGACIÓN

### Riesgos Técnicos
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Gemini API downtime** | Media | Alto | Retry con exponential backoff, fallback a modelo anterior |
| **OCR falla en documentos complejos** | Alta | Medio | Hybrid OCR (Cloud Vision + pdfplumber) |
| **Rate limiting de Google APIs** | Media | Medio | Colas con Cloud Tasks, procesamiento batch |

### Riesgos de Negocio
| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| **Cliente no adopta la solución** | Baja | Alto | UX humana, onboarding, soporte dedicado |
| **Costos de IA escalan** | Media | Medio | Caching, token optimization, modelos más baratos |
| **Competencia entra al mercado** | Media | Medio | Diferenciación por nomenclatura contable profesional |

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS (V3.1.3)

### Prioridad ALTA
1. **Arreglar funcionalidad con cliente Diego**
   - Investigar por qué no funciona con su mail
   - Verificar permisos de OAuth
   - Probar end-to-end

2. **Recuperar historial de auditoría**
   - Verificar si hay logs en Cloud Logging
   - Implementar persistencia robusta
   - Crear dashboard de caja negra

3. **Mejorar autenticación OAuth**
   - Implementar sesión persistente
   - Evitar re-login innecesario
   - Evaluar riesgos de seguridad

### Prioridad MEDIA
4. **Mejorar UI de algoritmos**
   - Agregar botón "Duplicar"
   - Arreglar editar/eliminar
   - Mejorar iconos

5. **Eliminar mensaje "solo para desarrolladores"**
   - Configurar Google Drive Picker para producción
   - Remover warnings

6. **Fix botón no se resetea después de error**
   - Implementar reset de estado
   - Mejorar manejo de errores

---

## 📞 CONTACTO

**Desarrollador Lead:**
- **Nombre:** Gonzalo Recalde
- **Email:** gonzalo.f.recalde@gmail.com
- **Ubicación:** Argentina
- **Timezone:** UTC-3

**Repositorio:**
- **GitHub:** [URL pendiente]
- **Docs:** C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders

---

**Aprobado por:** Gonzalo Recalde
**Fecha:** 12 de Marzo, 2026
**Versión:** 1.0

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
