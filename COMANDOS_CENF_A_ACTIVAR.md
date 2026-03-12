# 🎯 COMANDOS CENF A ACTIVAR - Análisis Previo
## Proyecto Renombrador (#amBotHsOS) - V3.1.2

---

## ⚠️ INSTRUCCIÓN: NO HACER NINGÚN CAMBIO TODAVÍA

Este documento es un **análisis previo** para tu aprobación. **No se ejecutará ningún código** hasta que me lo indiques explícitamente.

---

## 📋 SISTEMA CENF IDENTIFICADO

**Ubicación del Sistema:** `C:\Dropbox\DOC.RECA\06-Software\equipo-programacion-cenf`

**Versión:** 2.3.0 (última versión disponible)

**Componentes Principales:**
- ✅ ORCHESTRATOR (Project Manager)
- ✅ 8 Agentes Especializados (Frontend, Backend, Infra)
- ✅ Memoria Persistente (Engram)
- ✅ 10 Documentos Vivientes
- ✅ Workflow Híbrido (OPSX + SDD)

---

## 🚀 COMANDOS DISPONIBLES SEGÚN METODOLOGÍA CENF

### Comandos Principales (Slash Commands):

| Comando | Descripción | Cuándo Usar |
|---------|-------------|-------------|
| `/sdd-init` | Inicializar proyecto con 10 documentos | Primera vez o si faltan documentos |
| `/sdd-explore <topic>` | Investigar/research tema | Antes de proponer cambios |
| `/sdd-new <change>` | Crear nueva propuesta | Para cambios estructurales |
| `/sdd-continue` | Continuar siguiente fase | Para avanzar en el workflow |
| `/sdd-ff <change>` | Fast-forward plan | Para cambios rápidos |
| `/sdd-apply` | Implementar cambios | Para ejecutar lo planificado |
| `/sdd-verify` | Verificar implementación | Para testing y validación |
| `/sdd-archive` | Archivar cambios completados | Para cierre de ciclo |

### Comandos de Memoria (Engram):

| Comando | Descripción | Cuándo Usar |
|---------|-------------|-------------|
| `session_start(project="...")` | Iniciar sesión | Al comenzar trabajo |
| `mem_context(project="...")` | Recuperar contexto | Para recuperar sesiones previas |
| `mem_search("palabras clave")` | Buscar decisiones previas | Antes de implementar |
| `mem_save(title, content, type, project)` | Guardar decisiones | Cada decisión importante |
| `mem_session_summary(summary)` | Resumir sesión | Antes de cerrar |
| `session_end(summary)` | Cerrar sesión | Al terminar trabajo |

---

## 📊 ANÁLISIS DE TUS REQUERIMIENTOS vs COMANDOS CENF

### Requerimiento 1: Autenticación Fluida
**Problema:** El usuario quiere entrar sin re-autenticarse si ya está logueado en Google.

**Análisis CENF:**
- **Comando recomendado:** `/sdd-explore "autenticación OAuth Google sin re-login"`
- **Por qué:** Investigar primero la mejor práctica antes de proponer cambios
- **Workflow:** Explore → Proposal → Spec → Design → Tasks → Apply

### Requerimiento 2: Error al enviar carpeta
**Problema:** Error cuando se envía una carpeta al job.

**Análisis CENF:**
- **Comando recomendado:** `/sdd-new "fix error al enviar carpeta al job"`
- **Por qué:** Es un cambio estructural que requiere investigación
- **Workflow:** Proposal → Spec → Design → Tasks → Apply → Verify

### Requerimiento 3: UI de Algoritmos
**Problemas:**
- Símbolos en vez de editar/eliminar
- Falta botón de duplicar
- Errores al editar/eliminar

**Análisis CENF:**
- **Comando recomendado:** `/sdd-new "mejorar UI de algoritmos: duplicar, editar, eliminar"`
- **Por qué:** Cambios múltiples en la UI que requieren diseño
- **Workflow:** Proposal → Spec → Design → Tasks → Apply → Verify

### Requerimiento 4: Historial de Caja Negra
**Problema:** Se perdió el historial anterior y no se está guardando el actual.

**Análisis CENF:**
- **Comando recomendado:** `/sdd-explore "recuperar logs históricos y sistema de auditoría inmutable"`
- **Por qué:** Requiere investigación de opciones (Google Cloud Logging, etc.)
- **Workflow:** Explore → Proposal → Spec → Design → Tasks → Apply

### Requerimiento 5: Mensaje "Solo para Desarrolladores"
**Problema:** Aparece advertencia en producción al usar Google Drive Picker.

**Análisis CENF:**
- **Comando recomendado:** `/sdd-ff "eliminar mensaje de advertencia de Google Drive Picker"`
- **Por qué:** Es un cambio rápido (fast-forward)
- **Workflow:** Apply → Verify

### Requerimiento 6: Botón no se resetea después de error
**Problema:** El botón de procesar no vuelve a estar disponible después de un error.

**Análisis CENF:**
- **Comando recomendado:** `/sdd-ff "fix botón procesar no se resetea después de error"`
- **Por qué:** Es un cambio rápido de UX
- **Workflow:** Apply → Verify

---

## 🎯 RECOMENDACIÓN DE EJECUCIÓN

### Opción A: Enfoque Estructurado Completo (Recomendado)

**Ventajas:**
- Máxima trazabilidad
- Decisiones documentadas
- Mejor calidad

**Tiempo estimado:** 2-3 horas

**Workflow:**
1. Verificar/crear los 10 documentos de gestión
2. Iniciar sesión Engram
3. Para cada requerimiento:
   - `/sdd-explore` (investigación)
   - `/sdd-new` (propuesta)
   - `/sdd-apply` (implementación)
   - `/sdd-verify` (verificación)
   - `/sdd-archive` (archivo)

### Opción B: Enfoque Ágil (Rápido)

**Ventajas:**
- Más rápido
- Menos documentación

**Tiempo estimado:** 1-1.5 horas

**Workflow:**
1. Para cambios rápidos (5, 6): `/sdd-ff` directo
2. Para cambios medios (1, 3): `/sdd-apply` con documentación mínima
3. Para cambios complejos (2, 4): `/sdd-new` completo

---

## 📋 PASOS PREVIOS ANTES DE COMENZAR

### Paso 1: Verificar Instalación del Sistema CENF

```bash
# Verificar que el sistema existe
ls "C:\Dropbox\DOC.RECA\06-Software\equipo-programacion-cenf"

# Verificar que existan los scripts
ls "C:\Dropbox\DOC.RECA\06-Software\equipo-programacion-cenf\scripts"
```

### Paso 2: Verificar Instalación de Engram

```bash
# Verificar que Engram está instalado
engram version

# Si NO está instalado:
brew install gentleman-programming/tap/engram
```

### Paso 3: Verificar Configuración de Claude Code

```bash
# Verificar que Engram esté configurado en Claude Code
cat ~/.claude/.mcp.json | grep engram
```

### Paso 4: Verificar los 10 Documentos de Gestión

**En tu proyecto:** `C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders`

**Documentos requeridos:**
1. 01-Project-Charter.md
2. 02-Vision.md
3. 03-PRD.md
4. 04-Technical-Design.md
5. 05-Test-Strategy.md
6. 06-Implementation-Plan.md
7. 07-CI-CD-Strategy.md
8. 08-Monitoring.md
9. 09-Disaster-Recovery.md
10. 10-Risk-Register.md

**Si NO existen:**
```
Comando: /sdd-init
```

**Si existen:**
```
Continuar al siguiente paso
```

---

## 🔧 CONFIGURACIÓN DE GIT PARA COMMITS CON CONTEXT

### Formato de Commit Requerido:

```bash
git add .
git commit -m "<type>(<scope>): <descripción>

CONTEXT:
- ESTADO: Qué se acaba de hacer
- ARCHIVOS: Lista de archivos modificados
- NEXT: Qué viene después

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>"
```

**Tipos permitidos:**
- `feat` - Nueva feature
- `fix` - Corrección de bug
- `docs` - Cambios en documentación
- `style` - Cambios de formato
- `refactor` - Refactorización
- `test` - Tests
- `chore` - Mantenimiento

---

## 📊 PLAN DE TRABAJO PROPUESTO

### Fase 1: Preparación (15 min)
- [ ] Verificar instalación del sistema CENF
- [ ] Verificar instalación de Engram
- [ ] Verificar los 10 documentos de gestión
- [ ] Iniciar sesión Engram: `session_start(project="renameDriverFolders")`
- [ ] Recuperar contexto: `mem_context(project="renameDriverFolders")`

### Fase 2: Requerimientos Críticos (45 min)
- [ ] **Req 2:** Error al enviar carpeta (`/sdd-new`)
- [ ] **Req 4:** Historial de caja negra (`/sdd-explore`)
- [ ] Commit intermedio con CONTEXT

### Fase 3: Requerimientos Media Prioridad (30 min)
- [ ] **Req 1:** Autenticación fluida (`/sdd-new`)
- [ ] **Req 3:** UI de algoritmos (`/sdd-new`)
- [ ] Commit intermedio con CONTEXT

### Fase 4: Requerimientos Baja Prioridad (20 min)
- [ ] **Req 5:** Mensaje "solo desarrolladores" (`/sdd-ff`)
- [ ] **Req 6:** Botón no se resetea (`/sdd-ff`)
- [ ] Commit final con CONTEXT

### Fase 5: Verificación y Archivo (15 min)
- [ ] Verificar todos los cambios (`/sdd-verify`)
- [ ] Archivar cambios completados (`/sdd-archive`)
- [ ] Push a GitHub
- [ ] Cerrar sesión Engram: `session_end(summary="...")`

---

## 💾 GUARDAR DECISIONES EN ENGRAM

### Formato de mem_save:

```
mem_save(
  title="Decisión: [título]",
  content="[por qué, dónde, qué se aprendió]",
  type="architectural_decision",  # o "bug_fix", "ui_change", etc.
  project="renameDriverFolders"
)
```

### Ejemplos de decisiones a guardar:

1. **Decisión sobre autenticación:**
   ```
   mem_save(
     title="OAuth sin re-login",
     content="Decidimos usar Google Identity Services con sesión persistente. El token expira cada 1 hora pero se renueva automáticamente si el usuario está activo. User aceptó el riesgo de seguridad por UX.",
     type="architectural_decision",
     project="renameDriverFolders"
   )
   ```

2. **Decisión sobre logs:**
   ```
   mem_save(
     title="Sistema de auditoría inmutable",
     content="Decidimos usar Google Cloud Logging con retención de 90 días para auditoría. Costo estimado: $0.50/GB. User aprobó el costo.",
     type="architectural_decision",
     project="renameDriverFolders"
   )
   ```

---

## ⚠️ PREGUNTAS PARA TI ANTES DE COMENZAR

1. **¿Tienes Engram instalado?** Si no, ¿quieres que te ayude a instalarlo?

2. **¿Prefieres enfoque estructurado completo (Opción A) o ágil rápido (Opción B)?**

3. **¿Están los 10 documentos de gestión creados en tu proyecto?** Si no, ¿quieres que los cree?

4. **¿Cuál es la prioridad de los requerimientos?** ¿Hay alguno más urgente que otros?

5. **¿Tienes un repositorio GitHub conectado?** Necesitamos hacer commits con CONTEXT.

6. **¿Aceptas que cada decisión importante se guarde en Engram?**

7. **¿Confirmas que debo hacer commits con CONTEXT completo cada 10-15 minutos?**

---

## 🚀 COMANDO PARA INICIAR (Cuando estés listo)

```
Usa el Sistema de Desarrollo Autónomo v2.3.0 para:

Proyecto: C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
Sistema CENF: C:\Dropbox\DOC.RECA\06-Software\equipo-programacion-cenf

Requerimientos prioritarios (en orden):
1. Error al enviar carpeta al job
2. Recuperar y guardar historial de caja negra
3. Autenticación fluida sin re-login
4. Mejorar UI de algoritmos (duplicar, editar, eliminar)
5. Eliminar mensaje "solo para desarrolladores"
6. Fix botón no se resetea después de error

Enfoque: [Estructurado / Ágil] (tú decides)
```

---

## 📋 RESUMEN EJECUTIVO

**Sistema CENF:** ✅ Disponible en `C:\Dropbox\DOC.RECA\06-Software\equipo-programacion-cenf`

**Versión:** 2.3.0 (última)

**Comandos a activar:**
- `/sdd-init` - Si faltan los 10 documentos
- `/sdd-explore` - Para investigar soluciones
- `/sdd-new` - Para cambios estructurales
- `/sdd-ff` - Para cambios rápidos
- `/sdd-apply` - Para implementar
- `/sdd-verify` - Para verificar
- `/sdd-archive` - Para archivar

**Memoria:**
- `session_start(project="renameDriverFolders")`
- `mem_context(project="renameDriverFolders")`
- `mem_search("palabras clave")`
- `mem_save(title, content, type, project)`

**Commits:**
- Cada 10-15 minutos
- Con CONTEXT completo (ESTADO, ARCHIVOS, NEXT)
- Co-Authored-By: Claude Sonnet

---

## ⏸️ ESTADO: ESPERANDO TU APROBACIÓN

**NO haré ningún cambio hasta que me lo indiques explícitamente.**

**Por favor confirma:**
1. ¿Qué enfoque prefieres (Estructurado o Ágil)?
2. ¿Quieres que verifique/instale las dependencias (Engram, etc.)?
3. ¿Qué requerimiento es la PRIORIDAD #1 para empezar?

---

*Documento creado: 2026-03-12*
*Análisis completado. Esperando aprobación del usuario.*
