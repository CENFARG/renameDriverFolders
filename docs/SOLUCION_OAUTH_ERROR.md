# Solución al Error OAuth "org_internal"

## Problema
Al intentar hacer login en el frontend, aparece el error:
```
Error 403: org_internal
Acceso bloqueado: frontend-702567224563.us-central1.run.app solo se puede usar dentro de su organización
```

## Causa
El OAuth Client está configurado como **"Internal"** (solo para usuarios de Google Workspace de la organización), pero estás intentando acceder con una cuenta de Gmail personal (`gonzalo.f.recalde@gmail.com`).

## Solución

### Paso 1: Cambiar OAuth Client a "External"

1. Ve a la **Pantalla de Consentimiento OAuth:**
   https://console.cloud.google.com/apis/credentials/consent?project=cloud-functions-474716

2. Haz clic en **"EDITAR APLICACIÓN"**

3. En la sección **"User Type"**, cambia de **"Internal"** a **"External"**

4. Completa los campos requeridos:
   - **Nombre de la aplicación:** Renovador de Carpetas
   - **Email de soporte del usuario:** cenf.arg@gmail.com
   - **Logotipo de la aplicación:** (opcional)
   - **Dominios autorizados:** estudioanc.com.ar
   - **Email de contacto del desarrollador:** cenf.arg@gmail.com

5. Haz clic en **"GUARDAR Y CONTINUAR"**

6. En la sección **"Scopes"** (Alcances):
   - Puedes dejar los scopes por defecto o agregar:
     - `openid`
     - `email`
     - `profile`
   - Haz clic en **"GUARDAR Y CONTINUAR"**

7. En la sección **"Test users"** (Usuarios de prueba):
   - Agrega: `gonzalo.f.recalde@gmail.com`
   - Haz clic en **"AGREGAR USUARIOS"**
   - Haz clic en **"GUARDAR Y CONTINUAR"**

8. Revisa el resumen y haz clic en **"VOLVER AL PANEL"**

### Paso 2: Verificar Orígenes Autorizados

1. Ve a **Credenciales:**
   https://console.cloud.google.com/apis/credentials?project=cloud-functions-474716

2. Busca el cliente OAuth: `702567224563-74i4orff38l8afk39j4hsc411mm3d1ma`

3. Haz clic para editarlo

4. Verifica que en **"Orígenes de JavaScript autorizados"** estén:
   - `http://localhost:3000`
   - `http://localhost:8080`
   - `https://frontend-702567224563.us-central1.run.app`

5. Verifica que en **"URI de redireccionamiento autorizados"** esté:
   - `https://frontend-702567224563.us-central1.run.app/auth/callback`

6. Guarda los cambios

### Paso 3: Probar el Login

1. Abre una **ventana de incógnito** en tu navegador

2. Ve a: https://frontend-702567224563.us-central1.run.app

3. Haz clic en **"Sign in with Google"**

4. Selecciona tu cuenta: `gonzalo.f.recalde@gmail.com`

5. Si aparece una advertencia de "Esta app no está verificada":
   - Haz clic en **"Avanzado"**
   - Haz clic en **"Ir a Renovador de Carpetas (no seguro)"**
   - Esto es normal para apps en modo "Testing"

6. Acepta los permisos solicitados

7. Deberías ver el dashboard con tu email y foto

## Notas Importantes

### Modo "Testing" vs "Production"

Mientras la app esté en modo **"Testing"**:
- Solo los usuarios agregados en "Test users" pueden acceder
- Aparecerá la advertencia "Esta app no está verificada"
- Límite de 100 usuarios de prueba

Para modo **"Production"**:
- Requiere verificación de Google (proceso de varios días)
- No aparece la advertencia
- Sin límite de usuarios
- Recomendado solo si vas a tener muchos usuarios externos

### Alternativa: Mantener "Internal" y Usar Solo Workspace

Si prefieres mantener el OAuth como "Internal":
1. Solo usuarios con cuentas `@estudioanc.com.ar` podrán acceder
2. No funcionará con `gonzalo.f.recalde@gmail.com`
3. Necesitarías crear una cuenta de Google Workspace para Gonzalo

## Troubleshooting

### Si sigue sin funcionar:

1. **Limpia cookies y caché del navegador**
   - O usa ventana de incógnito

2. **Verifica que el email esté en la whitelist del backend:**
   ```bash
   gcloud secrets versions access latest --secret="oauth-allowed-domains"
   ```
   Debería mostrar: `estudioanc.com.ar,gonzalo.f.recalde@gmail.com`

3. **Revisa los logs del API Server:**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-server-v2" --limit=50 --format=json
   ```

4. **Verifica que el frontend esté usando el Client ID correcto:**
   - Abre el frontend
   - Abre DevTools (F12)
   - Ve a la pestaña "Console"
   - Busca errores relacionados con OAuth

## Contacto

Si el problema persiste después de seguir estos pasos, contacta a:
- **Email:** cenf.arg@gmail.com
- **Incluye:** Screenshots del error y de la configuración de OAuth
