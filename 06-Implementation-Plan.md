# 📋 06. IMPLEMENTATION PLAN
## Proyecto Renombrador (#amBotHsOS) - V3.1.2 "Estudio Inteligente"

---

## 🎯 PROPÓSITO DEL DOCUMENTO

Definir el plan de implementación para los arreglos pendientes del sistema **Renombrador** V3.1.3, priorizando funcionalidad crítica con cliente Diego y maximizando trazabilidad.

---

## 🚀 ORDEN DE IMPLEMENTACIÓN (Minimizando Retrabajo)

### Fase 1: Diagnóstico y Stabilización (Prioridad ALTA)

**Objetivo:** Hacer que el sistema funcione correctamente con el cliente Diego.

#### Tarea 1.1: Investigar Error con Cliente Diego
**Problema:** El sistema no funciona con el mail de Diego (@estudioanc.com.ar), pero sí con el mail de Gonzalo (@gmail.com).

**Hipótesis:**
1. Permisos de OAuth insuficientes para @estudioanc.com.ar
2. Folder ID incorrecto o sin permisos
3. Dominio whitelist mal configurado
4. Scope de OAuth incorrecto

**Pasos de Investigación:**
```bash
1. Verificar logs de API Server cuando Diego ejecuta
2. Verificar token de OAuth de Diego
3. Verificar permisos en la carpeta de Drive
4. Verificar configuración de dominios autorizados
5. Probar manual con credenciales de Diego
```

**Criterios de Aceptación:**
- [x] Diego puede ejecutar algoritmos manualmente
- [x] Los archivos se renombran correctamente
- [x] Dashboard muestra ejecuciones exitosas

**Estado:** ✅ **COMPLETADO** (13 de Marzo, 2026)
**Solución:** Agregar campo `audience` al `oidc_token` en Cloud Tasks
**Commit:** `add411d`
**Deploy:** v2-00036-pqx

**Prioridad:** 🔴 CRÍTICA
**Tiempo Estimado:** 2-3 horas
**Tiempo Real:** ~3 horas
**Depende de:** Nada

---

#### Tarea 1.2: Recuperar Historial de Auditoría
**Problema:** Se perdieron los logs históricos y no se está guardando el historial actual.

**Solución Propuesta:**
1. **Verificar si hay logs en Google Cloud Logging:**
   ```bash
   gcloud logs read \
     --project=cloud-functions-474716 \
     --filter="resource.type=cloud_run_revision" \
     --limit=1000
   ```

2. **Implementar persistencia robusta:**
   - Crear tabla `audit_logs` en Supabase
   - Insertar log en cada paso del pipeline
   - Exportar a GCS para backup

3. **Crear dashboard de auditoría:**
   - Vista de ejecuciones por algoritmo
   - Filtros por fecha, estado, usuario
   - Exportar a CSV/Excel

**Criterios de Aceptación:**
- [ ] Logs se guardan en Supabase
- [ ] Dashboard muestra historial completo
- [ ] Se puede exportar a Excel

**Prioridad:** 🔴 ALTA
**Tiempo Estimado:** 3-4 horas
**Depende de:** Nada

---

#### Tarea 1.3: Fix Botón No Se Resetea Después de Error
**Problema:** Cuando falla la ejecución, el botón de "Procesar" no vuelve a estar disponible.

**Solución:**
```typescript
// services/frontend/src/app/app.component.ts

submitJob() {
  this.isSubmitting = true;

  this.jobService.submitManualJob(this.selectedFolderId)
    .finally(() => {
      this.isSubmitting = false;  // Reset siempre
      this.selectedFolderId = null;
    });
}
```

**Criterios de Aceptación:**
- [ ] Botón se resetea después de error
- [ ] Usuario puede reintentar
- [ ] Mensaje de error es claro

**Prioridad:** 🟡 MEDIA
**Tiempo Estimado:** 30 min
**Depende de:** Nada

---

### Fase 2: Mejoras de UI (Prioridad MEDIA)

#### Tarea 2.1: Agregar Botón "Duplicar" Algoritmo
**Problema:** No existe forma de duplicar un algoritmo para crear uno similar rápidamente.

**Solución:**
```typescript
// services/frontend/src/app/job-list/job-list.component.ts

duplicateJob(job: Job) {
  const duplicatedJob = {
    ...job,
    id: null,
    name: `${job.name} [COPIA]`,
    created_at: new Date().toISOString()
  };

  this.jobService.createJob(duplicatedJob).subscribe();
}
```

**UI:**
```html
<button mat-icon-button (click)="duplicateJob(job)" title="Duplicar">
  <mat-icon>content_copy</mat-icon>
</button>
```

**Criterios de Aceptación:**
- [ ] Botón "Duplicar" visible en cada algoritmo
- [ ] Al hacer clic, se crea copia con "[COPIA]" en nombre
- [ ] Copia se puede editar independientemente

**Prioridad:** 🟡 MEDIA
**Tiempo Estimado:** 1 hora
**Depende de:** Nada

---

#### Tarea 2.2: Arreglar Editar/Eliminar Algoritmo
**Problema:** Al editar o eliminar, tira error.

**Investigación Requerida:**
1. Verificar endpoint de API
2. Verificar payload enviado desde frontend
3. Verificar validación en backend
4. Verificar permisos en Supabase

**Solución Propuesta:**
```typescript
// Backend - Verificar que el endpoint exista
@router.put("/api/v1/jobs/{job_id}")
async def update_job(job_id: str, job: JobUpdate, user: User = Depends(get_current_user)):
    # Implementar update en Supabase

// Frontend - Enviar IDs correctos
updateJob(job: Job) {
  this.jobService.updateJob(job.id, job).subscribe();
}
```

**Criterios de Aceptación:**
- [ ] Editar funciona sin errores
- [ ] Eliminar funciona con confirmación
- [ ] Cambios se persisten en Supabase

**Prioridad:** 🟡 MEDIA
**Tiempo Estimado:** 1-2 horas
**Depende de:** Investigación previa

---

### Fase 3: Mejoras de Autenticación (Prioridad MEDIA)

#### Tarea 3.1: Eliminar Re-login Innecesario
**Problema:** El usuario tiene que re-autenticarse constantemente, incluso si ya está logueado en Google.

**Análisis de Requerimiento:**
- **UX Deseada:** Si el usuario ya está logueado en Google (en el navegador), debería poder acceder directamente.
- **Restricción de Seguridad:** El token OAuth debe expirar por seguridad.

**Solución de Compromiso:**
1. **Session persistente de 1 hora:**
   - El token OAuth es válido por 1 hora
   - Si el usuario está activo, se renueva automáticamente
   - Si pasa 1 hora sin actividad, se pide re-login

2. **Auto-renewal con refresh token:**
   ```python
   # services/api-server/src/main.py

   @router.get("/api/v1/auth/refresh")
   async def refresh_token(refresh_token: str):
       new_token = exchange_refresh_token(refresh_token)
       return {"access_token": new_token}
   ```

3. **Frontend auto-renewal:**
   ```typescript
   // Refrescar token 5 min antes de expirar
   setInterval(() => {
     if (tokenExpiresIn < 5 min) {
       authService.refreshToken();
     }
   }, 60000);
   ```

**Criterios de Aceptación:**
- [ ] Usuario no ve pantalla de login si tiene sesión activa
- [ ] Token se renueva automáticamente si el usuario está activo
- [ ] Después de 1 hora de inactividad, se pide re-login

**Prioridad:** 🟡 MEDIA
**Tiempo Estimado:** 2-3 horas
**Depende de:** Nada

---

#### Tarea 3.2: Eliminar Mensaje "Solo para Desarrolladores"
**Problema:** Aparece advertencia en producción al usar Google Drive Picker.

**Solución:**
El mensaje "Solo continúes si eres desarrollador" es nativo de Google Drive Picker. No se puede eliminar.

**Workaround:**
1. **Verificar que la app esté verificada en Google Cloud Console:**
   ```bash
   gcloud auth application verify default
   ```

2. **Usar Client ID de producción (no de testing):**
   ```typescript
   // Verificar que uses el Client ID correcto
   const picker = new google.picker.PickerBuilder()
     .setOAuthToken(oauthToken)
     .setDeveloperKey('PRODUCTION_API_KEY')  // No la de testing
     .build();
   ```

**Criterios de Aceptación:**
- [ ] Mensaje de advertencia eliminado o minimizado
- [ ] Google Drive Picker funciona en producción

**Prioridad:** 🟢 BAJA
**Tiempo Estimado:** 1 hora
**Depende de:** Nada

---

### Fase 4: Documentación para Cliente (Prioridad ALTA)

#### Tarea 4.1: Crear Manual de Usuario para Diego
**Objetivo:** Documentar cómo usar los algoritmos preconfigurados y qué hacen.

**Contenido:**
1. **Qué es un Algoritmo de Estudio**
2. **Cómo crear un nuevo algoritmo**
3. **Algoritmos Preconfigurados:**
   - Facturas RG 830
   - Sueldos Digitales
   - Resúmenes Bancarios
   - Estados Contables
4. **Formato de Nombres (Placeholders)**
5. **Ejecución Manual vs Programada**
6. **Dashboard de Auditoría**

**Formato:** PDF con screenshots

**Criterios de Aceptación:**
- [ ] Manual creado en PDF
- [ ] Diego puede seguir los pasos sin ayuda
- [ ] Incluye screenshots de la UI actual

**Prioridad:** 🔴 ALTA
**Tiempo Estimado:** 2 horas
**Depende de:** Tareas 1.1-1.3 completadas

---

## 📊 MATRIZ DE DEPENDENCIAS

```
1.1 (Error Diego) ──────┐
                       ├──> 4.1 (Manual Diego)
1.2 (Auditoría)   ──────┤
                       │
1.3 (Botón reset)  ─────┤
                       │
2.1 (Duplicar)    ──────┤
                       │
2.2 (Editar/Eliminar) ──┤
                       │
3.1 (Re-login)     ─────┘
3.2 (Mensaje dev)  ────> (Independiente)
```

---

## 📋 CRONOGRAMA

### Semana 1 (13-19 Marzo)
- [ ] Lunes: Tarea 1.1 (Error Diego) + Commit
- [ ] Martes: Tarea 1.2 (Auditoría) + Commit
- [ ] Miércoles: Tarea 1.3 (Botón reset) + Commit
- [ ] Jueves: Tarea 2.1 (Duplicar) + Commit
- [ ] Viernes: Tarea 2.2 (Editar/Eliminar) + Commit

### Semana 2 (20-26 Marzo)
- [ ] Lunes: Tarea 3.1 (Re-login) + Commit
- [ ] Martes: Tarea 3.2 (Mensaje dev) + Commit
- [ ] Miércoles: Tarea 4.1 (Manual Diego) + Commit
- [ ] Jueves: Testing end-to-end con Diego
- [ ] Viernes: Deploy a producción + Documentación final

---

## 🔄 ESTRATEGIA DE COMMITS

**Cada Tarea = 1 Commit con CONTEXT:**

```bash
git add .
git commit -m "fix(job-status): arreglar edición de algoritmos

CONTEXT:
- ESTADO: Implementado update endpoint y fix frontend
- ARCHIVOS: services/api-server/src/main.py, services/frontend/src/app/job-list/*.ts
- CAMBIOS: Agregado PUT /api/v1/jobs/{id}, verificado payload desde frontend
- TEST: Manual testing exitoso con @estudioanc.com.ar
- NEXT: Deploy a staging para validación de Diego

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## ✅ CRITERIOS DE FINALIZACIÓN

El plan se considera completado cuando:

- [ ] Diego puede ejecutar algoritmos sin errores
- [ ] Historial de auditoría visible y persistente
- [ ] UI de algoritmos funciona completamente (CRUD + Duplicar)
- [ ] Autenticación es fluida (máximo 1 login por hora)
- [ ] Manual de usuario entregado a Diego
- [ ] Todos los cambios están en Git con CONTEXT
- [ ] Deploy en producción validado

---

**Creado:** 12 de Marzo, 2026
**Versión:** 1.0
**Próxima revisión:** Semanalmente durante implementación

---

*Este documento es parte de los 10 documentos de gestión CENF v2.3.0*
