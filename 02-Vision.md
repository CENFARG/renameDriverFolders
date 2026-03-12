# 🔭 02. VISIÓN
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 VISIÓN GENERAL

**Convertirse en la solución estándar de automatización documental para estudios contables y profesionales latinoamericanos, transformando la gestión de archivos digitales de una tarea manual tediosa a un proceso inteligente y transparente.**

---

## 🌟 EL PROBLEMA QUE RESOLVEMOS

### Problema Actual
Los estudios contables y profesionales manejan miles de documentos digitales mensuales:
- Facturas electrónicas (RG 830)
- Recibos de sueldos
- Resúmenes bancarios
- Estados contables
- Contratos y documentos legales

**El desafío:** Estos archivos llegan con nombres sin sentido:
- `scan001.pdf`
- `documento.pdf`
- `20250312_143022.pdf`
- `descarga (1).pdf`

**Consecuencias:**
- ❌ Pérdida de tiempo buscando documentos (horas/semana)
- ❌ Errores humanos en la organización
- ❌ Dificultad para auditorías y vencimientos
- ❌ Frustración del equipo contable

### Nuestra Solución
**IA que analiza el contenido visual y textual del documento, extrae los metadatos clave, y genera un nombre descriptivo siguiendo nomenclaturas contables profesionales.**

**Ejemplo de transformación:**
```
ANTES: scan001.pdf
DESPUÉS: 2025-03-12_Factura_B_MorganStanley_ServiciosConsultoria.pdf
```

**Metadatos extraídos automáticamente:**
- 📅 Fecha: 2025-03-12
- 📄 Tipo: Factura B
- 🏢 Emisor: Morgan Stanley
- 📝 Concepto: Servicios de Consultoría
- 💱 Moneda y monto: USD 5,000

---

## 🎯 VALORES CENTRALES

### 1. Transparencia ("Lo que ves, es lo que hay")
- **Auditoría completa:** Cada acción se registra
- **Logs inmutables:** Caja negra de todas las operaciones
- **Trazabilidad end-to-end:** Desde el documento original hasta el renombrado

### 2. Simplicidad ("Hecho para contadores, no para técnicos")
- **UX humana:** Lenguaje no técnico
- **Google Drive Picker:** Selección visual de carpetas
- **Algoritmos preconfigurados:** No requiere prompts complejos

### 3. Confiabilidad ("Funciona, siempre")
- **Arquitectura serverless:** Alta disponibilidad
- **Retry con exponential backoff:** Manejo robusto de errores
- **Validación de permisos:** No se pierden documentos

### 4. Seguridad ("Tus datos, tus documentos")
- **OAuth 2.0:** Autenticación con Google
- **Domain whitelisting:** Solo usuarios autorizados
- **No almacenamos contenido:** Solo metadatos y nombres

### 5. Escalabilidad ("Crece contigo")
- **Multi-job:** Un sistema, múltiples algoritmos
- **Programación flexible:** Diario, semanal, mensual
- **Core Package:** Módulos reutilizables

---

## 🚀 ROADMAP VISIÓN 2026

### Fase 1: Estudio Piloto (Q1 2026) ✅
- **Objetivo:** Validar solución con Estudio Cutignola
- **Estado:** Completado
- **Lecciones:** UX humana es crítica, Google Drive Picker essential

### Fase 2: Multi-Cliente (Q2 2026) ⏳
- **Objetivo:** Incorporar 5 estudios contables piloto
- **Features:**
  - Multi-tenancy completo
  - Onboarding automatizado
  - Billing integrado
  - Dashboard de métricas

### Fase 3: Liderazgo Regional (Q3-Q4 2026) ⏳
- **Objetivo:** 50 estudios activos en Argentina y LATAM
- **Features:**
  - Mobile app (iOS/Android)
  - Integración con sistemas contables (Tango, Contabilium)
  - API para terceros
  - Marketplace de algoritmos

### Fase 4: Expansión Vertical (2027) ⏳
- **Objetivo:** Expandir a otros sectores legales, médicos, RRHH
- **Features:**
  - IA multimodal (audio, video)
  - Workflow automation
  - OCR mejorado para documentos manuscritos

---

## 🎯 DEFINICIÓN DE ÉXITO

### Corto Plazo (3 meses)
- ✅ **Estudio Cutignola 100% operativo**
- ✅ **0 errores de producción**
- ✅ **Respuesta a bugs <24hs**

### Mediano Plazo (6-12 meses)
- ⏳ **5 estudios piloto activos**
- ⏳ **NPS >50**
- ⏳ **90% reducción tiempo organización**

### Largo Plazo (18-24 meses)
- ⏳ **50 estudios activos**
- ⏳ **Líder en LATAM**
- ⏳ **MRR >$10,000**

---

## 🏆 FACTORES DIFERENCIALES

### 1. Nomenclatura Contable Profesional
**No es solo renombrar, es organizar como lo haría un contador:**
- Fechas al formato ISO (YYYY-MM-DD)
- Tipos de documentos estandarizados
- Emisores identificados correctamente
- Conceptos descriptivos

### 2. Algoritmos Preconfigurados
**No requiere prompts ni configuración técnica:**
- Facturas RG 830
- Sueldos Digitales
- Resúmenes Bancarios
- Estados Contables

### 3. UX Humana
**Diseñado para personas que no son técnicas:**
- "Algoritmo de Estudio" (no "Job")
- "Frecuencia" (no "Trigger")
- Selección visual de carpetas (no "Folder ID")

### 4. Google Drive Integration Nativa
**No requiere mover documentos:**
- Google Drive Picker
- Permisos OAuth granulares
- Sin descargas ni re-subidas

### 5. Auditoría Inmutable
**Transparencia total:**
- Logs de cada operación
- Historial completo de renombrados
- Caja negra de errores

---

## 🎯 PRINCIPIOS DE DISEÑO

### 1. Serverless First
**Sin servidores que mantener:**
- Google Cloud Run (auto-scaling)
- Pago por uso (no idle time)
- Alta disponibilidad (99.9%)

### 2. AI-Native
**IA en el core, no como add-on:**
- Gemini 2.0/2.5 Flash para análisis
- Cloud Vision para OCR
- Agentes Agno para orquestación

### 3. Event-Driven
**Reacciona a cambios, no polling:**
- Webhooks de Google Drive
- Cloud Tasks para cola
- Cloud Scheduler para jobs

### 4. Microservicios
**Desacoplados y escalables:**
- API Gateway (seguridad, rate limiting)
- Worker (procesamiento)
- Frontend (UX)

### 5. Observability First
**Si no se mide, no existe:**
- Logging estructurado
- Métricas en tiempo real
- Dashboard de auditoría

---

## 🌟 IMPACTO SOCIAL Y ECONÓMICO

### Impacto Económico
- **Reducción costos operativos:** -80% en tiempo de organización
- **Reducción errores humanos:** -95% en clasificación
- **Aumento productividad:** +10h/semana por contador

### Impacto Social
- **Digitalización:** Acelera transformación digital PyMEs
- **Transparencia:** Mejora auditorías y compliance
- **Competitividad:** Estudios argentinos compiten globalmente

---

## 🎯 IDENTIDAD DE MARCA

### Nombre
**"Renombrador"** (#amBotHsOS - código interno)

### Tagline
**"Organización inteligente de documentos, contadores felices."**

### Personalidad
- **Profesional:** Hablamos el lenguaje contable
- **Simple:** No tecnicismos innecesarios
- **Confiable:** No perdemos documentos
- **Transparente:** Auditoría completa

### Colores
- **Azul:** Confianza, profesionalismo
- **Verde:** Éxito,Documents processed
- **Naranja:** IA, inteligencia

---

## 🎯 VISIÓN DE FUTURO (2030)

**En 2030, queremos que:**
1. **Todo documento digital en LATAM** que llegue a un estudio contable se organice automáticamente
2. **"Renombrado con IA"** sea un estándar de la industria
3. **Los contadores** puedan dedicarse a análisis estratégico, no a renombrar archivos
4. **Haya creado** 50 empleos directos y 500 indirectos
5. **Seamos el "Stripe de la documentación contable"** en LATAM

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** Q2 2026

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
