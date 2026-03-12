# ⚠️ 10. RISK REGISTER
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Identificar, evaluar y monitorear riesgos del proyecto **Renombrador** V3.1.2, con planes de mitigación y owners asignados.

---

## 📊 MATRIZ DE PROBABILIDAD vs IMPACTO

```
              IMPACTO
            Alta   Media   Baja
         ┌───────┬───────┬───────┐
     Alta │   1   │   2   │   3   │
Prob ────┼───────┼───────┼───────┤
    Media │   4   │   5   │   6   │
      Baja│   7   │   8   │   9   │
         └───────┴───────┴───────┘

1 = CRÍTICO (Acción inmediata)
2-3 = ALTO (Plan de mitigación)
4-6 = MEDIO (Monitorear)
7-9 = BAJO (Aceptar)
```

---

## 🔴 RIESGOS CRÍTICOS (Prioridad 1)

### R1: Pérdida de Datos de Clientes

**Descripción:** Pérdida irrecoverable de configuraciones de jobs o logs de auditoría.

**Probabilidad:** Media
**Impacto:** Alto
**Prioridad:** 🔴 CRÍTICO

**Indicadores:**
- Sin backups últimos 7 días
- Logs sin exportar a GCS
- Base de datos sin backups

**Plan de Mitigación:**
1. **Inmediato:**
   - [ ] Configurar backups diarios de Supabase
   - [ ] Exportar logs a GCS
   - [ ] Documentar procedimiento de restore

2. **Corto plazo (1 semana):**
   - [ ] Automatizar backups con scripts
   - [ ] Test de restore mensual
   - [ ] Alertas si falla backup

**Owner:** Gonzalo Recalde
**Fecha de Revisión:** Semanal

---

### R2: Caída de Servicio >4 horas

**Descripción:** Regional outage en us-central1 afectando todos los servicios.

**Probabilidad:** Baja
**Impacto:** Alto
**Prioridad:** 🔴 CRÍTICO

**Indicadores:**
- Google Cloud Status Page mostrando incidents
- Todos los servicios retornando 503
- Monitoreo mostrando 0% uptime

**Plan de Mitigación:**
1. **Inmediato:**
   - [ ] Verificar Google Cloud Status
   - [ ] Comunicar a usuarios (email, status page)
   - [ ] Activar plan de contingencia

2. **Mediano plazo (1 mes):**
   - [ ] Configurar multi-regional deployment
   - [ ] DNS failover automático

**Owner:** Gonzalo Recalde
**Fecha de Revisión:** Mensual

---

### R3: Brecha de Seguridad - Exposición de Datos

**Descripción:** Acceso no autorizado a datos de clientes o tokens OAuth.

**Probabilidad:** Baja
**Impacto:** Alto
**Prioridad:** 🔴 CRÍTICO

**Indicadores:**
- Access desde IPs desconocidas
- Aumento en rate de requests
- Errores de autenticación inusuales

**Plan de Mitigación:**
1. **Inmediato:**
   - [ ] Rotar secrets comprometidas
   - [ ] Revocar tokens OAuth
   - [ ] Forzar re-login
   - [ ] Reportar a Google Security

2. **Preventivo:**
   - [x] Rate limiting implementado
   - [x] Domain whitelisting
   - [ ] Security review trimestral
   - [ ] Penetration testing anual

**Owner:** Gonzalo Recalde
**Fecha de Revisión:** Trimestral

---

## 🟠 RIESGOS ALTOS (Prioridad 2-3)

### R4: Costos de IA Escalan Sin Control

**Descripción:** Consumo excesivo de Gemini API aumenta costos operativos más de 3x.

**Probabilidad:** Media
**Impacto:** Medio
**Prioridad:** 🟠 ALTO

**Indicadores:**
- Cuenta de Gemini API > $100/mes
- Documentos procesados > 10,000/mes
- Latencia de Gemini > 10s promedio

**Plan de Mitigación:**
1. **Inmediato:**
   - [ ] Monitorear consumo de tokens
   - [ ] Alerta si > $50/mes
   - [ ] Revisar prompts para optimizar

2. **Corto plazo:**
   - [ ] Caching de resultados
   - [ ] Token optimization
   - [ ] Modelos más baratos para casos simples

**Owner:** Gonzalo Recalde
**Fecha de Revisión:** Mensual

---

### R5: Cliente No Adopta la Solución

**Descripción:** Diego (cliente piloto) deja de usar el sistema por UX o bugs.

**Probabilidad:** Media
**Impacto:** Alto
**Prioridad:** 🟠 ALTO

**Indicadores:**
- 0 jobs ejecutados en 7 días
- 0 archivos renombrados en 30 días
- Feedback negativo recurrente

**Plan de Mitigación:**
1. **Inmediato:**
   - [ ] Contactar Diego para entender problema
   - [ ] Priorizar fixes críticos
   - [ ] Onboarding presencial

2. **Preventivo:**
   - [x] UX humana implementada
   - [ ] Manual de usuario
   - [ ] Soporte dedicado (primeros 3 meses)

**Owner:** Gonzalo Recalde
**Fecha de Revisión:** Semanal

---

### R6: Precisión de IA <90%

**Descripción:** Nombres generados no son correctos, requieren corrección manual.

**Probabilidad:** Media
**Impacto:** Medio
**Prioridad:** 🟠 ALTO

**Indicadores:**
- Tasa de rechazo de nombres >10%
- Errores en fecha/tipo/emisor >5%
- Feedback negativo sobre calidad

**Plan de Mitigación:**
1. **Inmediato:**
   - [ ] Analizar errores de Gemini
   - [ ] Ajustar prompts
   - [ ] Agregar validación post-IA

2. **Largo plazo:**
   - [ ] Fine-tuning de modelo
   - [ ] Human-in-the-loop para correcciones
   - [ ] Learning automático de errores

**Owner:** Gonzalo Recalde
**Fecha de Revisión:** Quincenal

---

## 🟡 RIESGOS MEDIOS (Prioridad 4-6)

### R7: Rate Limiting de Google APIs

**Descripción:** Google Drive, Cloud Vision o Gemini tienen rate limiting.

**Probabilidad:** Media
**Impacto:** Medio
**Prioridad:** 🟡 MEDIO

**Plan de Mitigación:**
- [x] Cloud Tasks para cola
- [x] Retry con exponential backoff
- [ ] Monitorear cuotas

**Owner:** Gonzalo Recalde

---

### R8: Deplyment Falla en Producción

**Descripción:** Error en deployment causa downtime.

**Probabilidad:** Media
**Impacto:** Medio
**Prioridad:** 🟡 MEDIO

**Plan de Mitigación:**
- [ ] Tests antes de deploy
- [ ] Staging environment
- [ ] Rollback procedure documentado
- [ ] Deploy en horarios de bajo uso

**Owner:** Gonzalo Recalde

---

### R9: Developer Key Leaked

**Descripción:** API key de Gemini o Google Cloud es expuesta en código.

**Probabilidad:** Baja
**Impacto:** Alto
**Prioridad:** 🟡 MEDIO

**Plan de Mitigación:**
- [x] Secrets en Google Secret Manager
- [x] Nunca commitear .env
- [ ] Pre-commit hooks para detectar keys
- [ ] Rotación de keys trimestral

**Owner:** Gonzalo Recalde

---

## 🟢 RIESGOS BAJO (Prioridad 7-9)

### R10: Cambios en Google APIs

**Descripción:** Google deprecia o cambia APIs que usamos.

**Probabilidad:** Baja
**Impacto:** Medio
**Prioridad:** 🟢 BAJO

**Plan de Mitigación:**
- [ ] Suscribirse a Google Cloud changelog
- [ ] Actualizar dependencias regularmente
- [ ] Tests de integración con APIs

**Owner:** Monitorear

---

### R11: Competencia Entra al Mercado

**Descripción:** Otro producto similar aparece en el mercado.

**Probabilidad:** Media
**Impacto:** Bajo
**Prioridad:** 🟢 BAJO

**Plan de Mitigación:**
- [x] Diferenciación por nomenclatura contable
- [x] UX humana
- [ ] Primeros 6 meses de ventaja (first-mover)

**Owner:** Monitorear

---

## 📋 MATRIZ DE RIESGOS RESUMIDA

| ID | Riesgo | Probabilidad | Impacto | Prioridad | Owner | Estado |
|----|--------|--------------|---------|-----------|-------|--------|
| **R1** | Pérdida de datos | Media | Alto | 🔴 CRÍTICO | Gonzalo | ⚠️ Mitigación en progreso |
| **R2** | Caída servicio >4hs | Baja | Alto | 🔴 CRÍTICO | Gonzalo | ⚠️ Plan contingente |
| **R3** | Brecha seguridad | Baja | Alto | 🔴 CRÍTICO | Gonzalo | ✅ Controles en lugar |
| **R4** | Costos IA escalan | Media | Medio | 🟠 ALTO | Gonzalo | ⚠️ Monitorear mensualmente |
| **R5** | Cliente no adopta | Media | Alto | 🟠 ALTO | Gonzalo | ⚠️ Prioridad #1 |
| **R6** | Precisión IA <90% | Media | Medio | 🟠 ALTO | Gonzalo | ⚠️ Optimizar prompts |
| **R7** | Rate limiting | Media | Medio | 🟡 MEDIO | Gonzalo | ✅ Mitigado |
| **R8** | Deployment falla | Media | Medio | 🟡 MEDIO | Gonzalo | ⏳ Pendiente |
| **R9** | Key leaked | Baja | Alto | 🟡 MEDIO | Gonzalo | ✅ Mitigado |
| **R10** | Cambios APIs | Baja | Medio | 🟢 BAJO | Monitorear | ⏳ Monitorear |
| **R11** | Competencia | Media | Bajo | 🟢 BAJO | Monitorear | ⏳ Monitorear |

---

## 🔄 PROCESO DE GESTIÓN DE RIESGOS

### 1. Identificación
- Reunión quincenal para identificar nuevos riesgos
- Revisión de incidentes pasados
- Análisis de cambios en el entorno

### 2. Evaluación
- Calcular probabilidad e impacto
- Asignar prioridad
- Actualizar matriz

### 3. Mitigación
- Asignar owner
- Definir plan de acción
- Establecer indicadores

### 4. Monitoreo
- Revisión según frecuencia (semanal, mensual, trimestral)
- Actualizar estado
- Cerrar riesgos mitigados

---

## 📊 MÉTRICAS DE RIESGO

**Riesgo Total del Proyecto:** MEDIO

**Tendencia:** Estable (últimos 30 días)

**Riesgos Críticos Abiertos:** 3 (R1, R2, R3)

**Próxima Revisión:** 19 de Marzo, 2026

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** Quincenal

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
