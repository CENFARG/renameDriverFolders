# 🔧 Configurar Google API Key para Google Drive Picker

## 📋 Propósito

Eliminar el mensaje **"Solo continúes si eres desarrollador"** que aparece al abrir el Google Drive Picker.

---

## 🎯 Por qué aparece este mensaje

Google Drive Picker muestra el mensaje "Solo continúes si eres desarrollador" cuando:

1. **No se usa una API Key** de Google Cloud Console
2. **La API Key es de testing/desarrollo** (no está restringida)
3. **La app no está verificada** en Google Cloud Console

---

## ✅ Solución: Configurar API Key de Producción

### Paso 1: Obtener API Key de Google Cloud Console

1. Ir a [Google Cloud Console - APIs & Services](https://console.cloud.google.com/apis/credentials)
2. Seleccionar el proyecto: `cloud-functions-474716`
3. Hacer clic en **"Create credentials"** → **"API key"**
4. Copiar la API Key generada

### Paso 2: Configurar restricciones de la API Key

**IMPORTANTE:** Para usar la API Key en producción, DEBE configurar restricciones:

1. Hacer clic en la API Key creada
2. En **"Application restrictions"**:
   - Seleccionar **"HTTP referrers"**
   - Agregar los siguientes referrers:
     ```
     https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app/*
     https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app/
     localhost*
     ```

3. En **"API restrictions"**:
   - Seleccionar **"Restrict key"**
   - Buscar y seleccionar:
     - **Google Picker API**
     - **Google Drive API**

4. Hacer clic en **"Save"**

### Paso 3: Configurar la API Key en el Frontend

Editar el archivo de ambiente de producción:

```typescript
// services/frontend/src/environments/environment.prod.ts

export const environment = {
    production: true,
    apiUrl: 'https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app',
    oauthClientId: '702567224563-74i4orff38l8afk39j4hsc411mm3d1ma.apps.googleusercontent.com',
    googleApiKey: 'TU_API_KEY_AQUI' // ← Pegar la API Key aquí
};
```

### Paso 4: Deploy del Frontend

```bash
cd C:\Dropbox\DOC.RECA\06-Software\renameDriverFolders
gcloud builds submit --config services/frontend/cloudbuild.yaml --project=cloud-functions-474716
```

---

## 🔍 Verificación

Después de configurar la API Key:

1. Abrir la aplicación
2. Hacer clic en **"📁 Seleccionar"** carpeta
3. Verificar que **NO** aparezca el mensaje "Solo continúes si eres desarrollador"

---

## 🚨 Notas Importantes

### Seguridad de la API Key

- ✅ La API Key es visible en el código del frontend (esto es normal)
- ✅ Las restricciones de HTTP referrer previenen uso no autorizado
- ✅ Las restricciones de API limitan qué APIs pueden usarla
- ❌ **NUNCA** commitear una API Key sin restricciones

### Verificación de App

Para eliminar COMPLETAMENTE el mensaje, la app debe estar verificada:

1. Ir a [Google Cloud Console - OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
2. Completar el **"OAuth consent screen"** con:
   - Logo de la app
   - Dominios autorizados
   - Email de soporte
3. Enviar para verificación
4. Esperar aprobación de Google

**Nota:** La verificación puede tomar varios días.

---

## 📊 Resumen

| Configuración | Estado | Mensaje que aparece |
|--------------|--------|---------------------|
| Sin API Key | ❌ Desarrollo | "Solo continúes si eres desarrollador" |
| Con API Key restringida | ✅ Producción | Mensaje eliminado o minimizado |
| App verificada + API Key | ✅✅ Óptimo | Sin mensajes de advertencia |

---

**Documento creado:** 13 de Marzo, 2026
**Versión:** 1.0
