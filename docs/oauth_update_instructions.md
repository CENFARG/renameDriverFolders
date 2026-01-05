# Guía Visual: Actualizar OAuth Client ID

**Basado en tu pantalla actual de Google Cloud Console**

---

## ✅ Estás en el Lugar Correcto

Ya estás en **APIs & Services** → **Credenciales** → **IDs de clientes de OAuth 2.0**

---

## Paso 1: Identificar el Client ID Correcto

En tu lista veo 3 OAuth 2.0 Client IDs:

1. **api-server-v2-renomtime** - ID: `702567224563-74i...` ← **ESTE ES EL CORRECTO**
2. **renameserverfolder** - ID: `789467774851-c8fr...`
3. **Cliente de drive-902** - ID: `1888596644865186...`

---

## Paso 2: Editar el Client ID

1. **Click en el nombre** `api-server-v2-renomtime` (primera fila)
   - O click en el ícono de **lápiz** (editar) a la derecha de esa fila

2. Se abrirá la página de edición del Client ID

---

## Paso 3: Agregar la Nueva URL

En la página de edición, buscar la sección **"Orígenes de JavaScript autorizados"** o **"Authorized JavaScript origins"**

### Agregar esta URL:
```
https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app
```

### URLs que deberías tener (total 3):
1. `http://localhost:3000`
2. `http://localhost:8080`
3. `https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app` ← **NUEVA**

---

## Paso 4: Verificar Redirect URIs (si existe)

Si hay una sección **"URIs de redireccionamiento autorizados"** o **"Authorized redirect URIs"**, verificar que incluya las rutas de callback de tu app.

Ejemplo (ajustar según tu código):
```
https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app/callback
```

---

## Paso 5: Guardar

1. Scroll hasta el final de la página
2. Click en **GUARDAR** o **SAVE**
3. Esperar confirmación

---

## Paso 6: Validar

1. **Esperar 2-3 minutos** para propagación
2. **Abrir ventana de incógnito** en el navegador
3. **Ir a:** https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app
4. **Intentar login** con `gonzalo.f.recalde@gmail.com`
5. Debería funcionar sin error `origin_mismatch`

---

## 🔍 Cómo Se Ve la Página de Edición

Cuando hagas click en `api-server-v2-renomtime`, verás una página con:

- **Nombre del cliente:** (puedes dejarlo como está)
- **Orígenes de JavaScript autorizados:** (aquí agregas la nueva URL)
- **URIs de redireccionamiento autorizados:** (verificar que estén correctas)

---

## ⚠️ Importante

- **NO edites** los otros Client IDs (`renameserverfolder` o `Cliente de drive-902`)
- **Solo edita** `api-server-v2-renomtime` que tiene el ID `702567224563-74i...`

---

## Screenshot de Referencia

![Pantalla de Credenciales](C:/Users/gonza/.gemini/antigravity/brain/bcb859df-9415-47d6-9306-c4ad2953e33e/uploaded_image_1766095167445.png)

**En esta pantalla:** Click en `api-server-v2-renomtime` (primera fila de la tabla)

---

**Preparado por:** Gemini (Antigravity Agent)  
**Fecha:** 2025-12-18  
**Versión:** 1.2 (Con screenshot del usuario)
