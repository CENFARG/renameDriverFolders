# Sistema de Renombrado Automático de Archivos con IA
## Informe Técnico y Comercial para Cliente

**Fecha:** 10 de Diciembre de 2025  
**Versión del Sistema:** 2.0  
**Estado:** Producción  
**Proveedor:** CENF

---

## 1. Resumen Ejecutivo

El sistema **renameDriverFolders V2** es una solución cloud-native que automatiza el renombrado inteligente de archivos en Google Drive utilizando Inteligencia Artificial (Gemini Pro). El sistema procesa documentos, analiza su contenido y genera nombres descriptivos automáticamente, ahorrando tiempo y mejorando la organización documental.

### Beneficios Clave
- ✅ **Automatización completa:** Procesa carpetas sin intervención manual
- ✅ **IA Avanzada:** Utiliza Gemini Pro para análisis contextual de documentos
- ✅ **Seguridad robusta:** OAuth 2.0 + control de acceso por dominio
- ✅ **Escalable:** Arquitectura serverless que crece con la demanda
- ✅ **Costo-efectivo:** Pago por uso, sin infraestructura fija

---

## 2. Arquitectura del Sistema

### 2.1 Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO FINAL                            │
│              (Navegador Web)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND (Angular)                             │
│  • Interfaz web moderna                                     │
│  • Google Sign-In                                           │
│  • Gestión de trabajos                                      │
│  URL: https://frontend-702567224563.us-central1.run.app    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS + OAuth Token
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              API SERVER (Gateway)                           │
│  • Autenticación OAuth 2.0                                  │
│  • Validación de permisos                                   │
│  • Gestión de cola de tareas                                │
│  URL: https://api-server-v2-702567224563.us-central1.run.app│
└────────────────────┬────────────────────────────────────────┘
                     │ Cloud Tasks (OIDC)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              WORKER (Procesador IA)                         │
│  • Análisis de archivos con Gemini Pro                      │
│  • Generación de nombres inteligentes                       │
│  • Renombrado en Google Drive                               │
│  URL: https://worker-renombrador-v2-702567224563.us-central1.run.app│
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              GOOGLE DRIVE                                   │
│  • Almacenamiento de documentos                             │
│  • Gestión de permisos                                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Tecnologías Utilizadas

| Componente | Tecnología | Propósito |
|------------|------------|-----------|
| Frontend | Angular 17 + TypeScript | Interfaz de usuario moderna |
| API Server | Python + FastAPI | Gateway de API REST |
| Worker | Python + Agno AI | Procesamiento con IA |
| IA | Google Gemini Pro | Análisis de contenido |
| Infraestructura | Google Cloud Run | Serverless, auto-escalable |
| Autenticación | OAuth 2.0 | Seguridad de acceso |
| Cola de Tareas | Cloud Tasks | Procesamiento asíncrono |
| Automatización | Cloud Scheduler | Ejecución programada |
| Secretos | Secret Manager | Gestión segura de credenciales |

---

## 3. Funcionalidades

### 3.1 Procesamiento Manual
- Usuario inicia sesión con Google
- Selecciona carpeta de Google Drive
- Sistema procesa todos los archivos
- Genera nombres descriptivos automáticamente
- Renombra archivos en Drive

### 3.2 Procesamiento Automático
- Ejecución diaria programada (2:00 AM UTC)
- Procesa carpetas predefinidas
- Genera reportes de actividad
- Sin intervención manual

### 3.3 Seguridad
- **Autenticación:** Google Sign-In (OAuth 2.0)
- **Autorización:** Control por dominio de email
- **Whitelist:** Solo usuarios de `estudioanc.com.ar` + emails específicos
- **Rate Limiting:** Máximo 10 requests por minuto por usuario
- **Encriptación:** HTTPS en todas las comunicaciones
- **Headers de Seguridad:** HSTS, CSP, XSS-Protection

---

## 4. Análisis de Costos

### 4.1 Estructura de Costos (Google Cloud Platform)

**Modelo de Facturación:** Pago por uso (Pay-as-you-go)

| Servicio | Métrica | Precio Unitario | Costo Mensual Estimado* |
|----------|---------|-----------------|-------------------------|
| **Cloud Run - Worker** | vCPU-segundos + RAM | $0.00002400/vCPU-seg<br>$0.00000250/GiB-seg | $5.00 |
| **Cloud Run - API Server** | vCPU-segundos + RAM | $0.00002400/vCPU-seg<br>$0.00000250/GiB-seg | $1.00 |
| **Cloud Run - Frontend** | vCPU-segundos + RAM | $0.00002400/vCPU-seg<br>$0.00000250/GiB-seg | $0.50 |
| **Cloud Tasks** | Operaciones | Gratis hasta 1M/mes | $0.00 |
| **Cloud Scheduler** | Jobs | $0.10/job/mes | $0.10 |
| **Secret Manager** | Secrets activos | $0.06/secret/mes | $0.18 |
| **Gemini API** | Requests | Variable según uso | $2.00** |
| **Networking** | Egress | $0.12/GiB | $0.50 |
| **TOTAL MENSUAL** | | | **~$9.28** |

\* Basado en 100 trabajos/día (3,000 trabajos/mes)  
\** Estimado para 3,000 análisis de documentos/mes

### 4.2 Escalabilidad de Costos

| Volumen de Trabajos | Costo Mensual Estimado |
|---------------------|------------------------|
| 50 trabajos/día | ~$5.00 |
| 100 trabajos/día | ~$9.28 |
| 500 trabajos/día | ~$35.00 |
| 1,000 trabajos/día | ~$65.00 |

**Nota:** Los costos escalan linealmente con el uso. No hay costos fijos de infraestructura.

### 4.3 Comparación con Alternativas

| Opción | Costo Mensual | Ventajas | Desventajas |
|--------|---------------|----------|-------------|
| **Solución Actual (Cloud)** | $9-65 | Escalable, sin mantenimiento, IA avanzada | Requiere conexión a internet |
| **Servidor Dedicado** | $50-200 | Control total | Mantenimiento, actualizaciones, costos fijos |
| **Proceso Manual** | $0 (tiempo humano) | Sin costo directo | Alto costo de tiempo, errores humanos |

---

## 5. Seguridad y Cumplimiento

### 5.1 Medidas de Seguridad Implementadas

1. **Autenticación Multi-Factor**
   - OAuth 2.0 con Google
   - Tokens JWT con expiración
   - Validación de dominio de email

2. **Autorización Granular**
   - Whitelist de dominios (`estudioanc.com.ar`)
   - Whitelist de emails específicos
   - Rate limiting por usuario

3. **Protección de Datos**
   - Encriptación en tránsito (HTTPS/TLS 1.3)
   - Secrets en Secret Manager (no en código)
   - Sin almacenamiento de datos sensibles

4. **Defensa en Profundidad**
   - Worker privado (no accesible públicamente)
   - API Server con validación de tokens
   - Security headers (HSTS, CSP, XSS-Protection)
   - Input validation y sanitization

### 5.2 Cumplimiento

- ✅ **GDPR:** No se almacenan datos personales
- ✅ **OWASP Top 10:** Mitigaciones implementadas
- ✅ **Google Cloud Security:** Infraestructura certificada
- ✅ **Audit Logs:** Registro completo de actividad

---

## 6. Mantenimiento y Soporte

### 6.1 Actualizaciones del Sistema
- **Automáticas:** Parches de seguridad de Google Cloud
- **Manuales:** Nuevas funcionalidades (bajo demanda)
- **Frecuencia:** Trimestral para mejoras, inmediato para seguridad

### 6.2 Monitoreo
- **Disponibilidad:** 99.5% SLA (Google Cloud Run)
- **Logs:** Centralizados en Cloud Logging
- **Alertas:** Configurables para errores críticos
- **Métricas:** CPU, RAM, latencia, errores

### 6.3 Soporte Técnico
- **Nivel 1:** Documentación y guías de usuario
- **Nivel 2:** Soporte por email (respuesta en 24-48h)
- **Nivel 3:** Soporte urgente (bajo contrato SLA)

---

## 7. Roadmap y Mejoras Futuras

### 7.1 Corto Plazo (1-3 meses)
- [ ] Dashboard de estadísticas de uso
- [ ] Historial de trabajos procesados
- [ ] Notificaciones por email
- [ ] Soporte para más tipos de documentos

### 7.2 Mediano Plazo (3-6 meses)
- [ ] Reglas personalizadas de renombrado
- [ ] Integración con otros servicios de almacenamiento (Dropbox, OneDrive)
- [ ] API pública para integraciones
- [ ] Procesamiento por lotes mejorado

### 7.3 Largo Plazo (6-12 meses)
- [ ] Machine Learning personalizado por cliente
- [ ] Clasificación automática de documentos
- [ ] OCR para documentos escaneados
- [ ] Análisis de contenido avanzado

---

## 8. Instrucciones de Uso

### 8.1 Acceso al Sistema

1. **URL del Sistema:** https://frontend-702567224563.us-central1.run.app
2. **Hacer clic en "Sign in with Google"**
3. **Usar cuenta de email autorizada:**
   - Dominio: `@estudioanc.com.ar`
   - O email específico: `gonzalo.f.recalde@gmail.com`

### 8.2 Procesar una Carpeta

1. Iniciar sesión
2. Ingresar el **ID de la carpeta de Google Drive**
   - Ejemplo: `1ABC-123xyz...`
   - Se encuentra en la URL de la carpeta en Drive
3. Seleccionar **tipo de trabajo** (Genérico, Facturas, Reportes)
4. Hacer clic en **"Procesar Carpeta"**
5. Esperar confirmación de éxito

### 8.3 Obtener ID de Carpeta de Google Drive

1. Abrir Google Drive
2. Navegar a la carpeta deseada
3. Copiar el ID de la URL:
   ```
   https://drive.google.com/drive/folders/[ESTE_ES_EL_ID]
   ```

---

## 9. Contacto y Soporte

**Proveedor:** CENF  
**Email de Soporte:** cenf.arg@gmail.com  
**Documentación Técnica:** Disponible en el repositorio del proyecto  
**Horario de Soporte:** Lunes a Viernes, 9:00 - 18:00 (GMT-3)

---

## 10. Anexos

### 10.1 Glosario Técnico

- **OAuth 2.0:** Protocolo de autenticación estándar de la industria
- **Serverless:** Arquitectura sin servidores dedicados, escalado automático
- **Cloud Run:** Servicio de Google Cloud para contenedores serverless
- **Gemini Pro:** Modelo de IA de Google para análisis de lenguaje natural
- **JWT:** JSON Web Token, estándar para tokens de autenticación
- **OIDC:** OpenID Connect, extensión de OAuth para autenticación

### 10.2 URLs del Sistema

| Componente | URL | Propósito |
|------------|-----|-----------|
| Frontend | https://frontend-702567224563.us-central1.run.app | Interfaz de usuario |
| API Server | https://api-server-v2-702567224563.us-central1.run.app | API REST |
| Worker | https://worker-renombrador-v2-702567224563.us-central1.run.app | Procesador (privado) |

### 10.3 Configuración Actual

- **Proyecto GCP:** cloud-functions-474716
- **Región:** us-central1 (Iowa, USA)
- **Dominio Autorizado:** estudioanc.com.ar
- **Horario de Ejecución Automática:** 02:00 AM UTC (23:00 hora Argentina)

---

**Documento generado automáticamente el 10/12/2025**  
**Versión:** 1.0
