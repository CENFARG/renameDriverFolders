# Guía de Configuración OAuth con Domain Whitelisting

## 🔐 Configuración del Sistema de Seguridad

### **1. Configurar Google OAuth Client**

#### **Paso 1: Crear OAuth Client en Google Cloud Console**
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Navega a **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **OAuth client ID**
4. Tipo: **Web application**
5. Configurar:
   - **Authorized JavaScript origins**:
     - `https://tu-frontend.com`
     - `http://localhost:3000` (para desarrollo)
   - **Authorized redirect URIs**:
     - `https://tu-frontend.com/auth/callback`
     - `http://localhost:3000/auth/callback`
6. **Guardar CLIENT_ID** (lo necesitarás)

---

### **2. Configurar Whitelist de Dominios**

#### **Opción A: En config.json (Desarrollo)**
```json
{
  "oauth": {
    "client_id": "123456-abc.apps.googleusercontent.com",
    "allowed_domains": [
      "miempresa.com",
      "cenf.com.ar",
      "coutinholla.com"
    ],
    "allowed_emails": [
      "admin@miempresa.com",
      "gonzalo@cenf.com.ar"
    ]
  }
}
```

#### **Opción B: En Supabase (Producción)**
```sql
-- Tabla: app_config
INSERT INTO app_config (key, value) VALUES
('oauth.client_id', '"123456-abc.apps.googleusercontent.com"'),
('oauth.allowed_domains', '["miempresa.com", "cenf.com.ar", "coutinholla.com"]'),
('oauth.allowed_emails', '["admin@miempresa.com"]');
```

#### **Opción C: En Variables de Entorno (Cloud Run)**
```bash
RENOMBRADOR_OAUTH_CLIENT_ID="123456-abc.apps.googleusercontent.com"
RENOMBRADOR_OAUTH_ALLOWED_DOMAINS='["miempresa.com", "cenf.com.ar"]'
RENOMBRADOR_OAUTH_ALLOWED_EMAILS='["admin@miempresa.com"]'
```

---

### **3. Implementar en Frontend**

#### **HTML + JavaScript (Google Sign-In)**
```html
<!DOCTYPE html>
<html>
<head>
  <meta name="google-signin-client_id" content="TU_CLIENT_ID.apps.googleusercontent.com">
  <script src="https://accounts.google.com/gsi/client" async defer></script>
</head>
<body>
  <div id="g_id_onload"
       data-client_id="TU_CLIENT_ID.apps.googleusercontent.com"
       data-callback="handleCredentialResponse">
  </div>
  <div class="g_id_signin" data-type="standard"></div>

  <script>
    function handleCredentialResponse(response) {
      // response.credential es el JWT token
      const token = response.credential;
      
      // Llamar a tu API con el token
      fetch('https://tu-api.com/jobs/manual', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          folder_id: '1AbCdEf...',
          job_type: 'invoice'
        })
      })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          alert(`Error: ${data.message}`);
        } else {
          alert('Job submitted successfully!');
        }
      });
    }
  </script>
</body>
</html>
```

---

### **4. Flujo de Autenticación**

```
1. Usuario → Click "Sign in with Google"
   ↓
2. Google → Muestra popup de login
   ↓
3. Usuario → Selecciona cuenta (ej: juan@miempresa.com)
   ↓
4. Google → Genera JWT token
   ↓
5. Frontend → Envía request con token:
   Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
   ↓
6. Backend (tu API) → Verifica token:
   - ✅ Firma válida?
   - ✅ No expirado?
   - ✅ Cliente ID correcto?
   - ✅ Email verificado?
   ↓
7. Backend → Verifica autorización:
   - ✅ Dominio en whitelist? (miempresa.com)
   - ✅ Rate limit OK?
   ↓
8. Backend → Procesa request
   ↓
9. Frontend → Recibe respuesta
```

---

### **5. Casos de Uso por Tipo de Usuario**

#### **Caso A: Usuario Autorizado**
```
Email: juan@miempresa.com
Dominio: miempresa.com ✅ (está en whitelist)
Resultado: ✅ Acceso permitido
```

#### **Caso B: Usuario con Email Específico**
```
Email: admin@otrodominio.com
Dominio: otrodominio.com ❌ (no en whitelist)
Email: admin@otrodominio.com ✅ (en allowed_emails)
Resultado: ✅ Acceso permitido
```

#### **Caso C: Usuario No Autorizado**
```
Email: hacker@gmail.com
Dominio: gmail.com ❌ (no en whitelist)
Email: hacker@gmail.com ❌ (no en allowed_emails)
Resultado: ❌ 403 Forbidden
```

---

### **6. Rate Limiting por Usuario**

```python
# Configuración por defecto
@require_auth(oauth_manager, 
              rate_limit_requests=5,   # 5 requests
              rate_limit_minutes=1)     # por minuto

# Diferentes límites según endpoint
@app.route("/jobs/manual")
@require_auth(oauth_manager, rate_limit_requests=5, rate_limit_minutes=1)
def submit_job():
    pass  # Límite estricto para envíos

@app.route("/jobs/list")
@require_auth(oauth_manager, rate_limit_requests=20, rate_limit_minutes=1)
def list_jobs():
    pass  # Límite relajado para consultas
```

**Respuesta si excede límite:**
```json
{
  "error": "Too Many Requests",
  "message": "Max 5 requests per 1 minute(s)"
}
```

---

### **7. Testing Manual**

#### **Obtener Token de Test**
1. Ve a [Google OAuth Playground](https://developers.google.com/oauthplayground/)
2. Configura tu Client ID
3. Autoriza y obtén ID token
4. Úsalo para probar:

```bash
curl -X POST https://tu-api.com/jobs/manual \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"folder_id": "1AbCdEf", "job_type": "invoice"}'
```

---

### **8. Monitoring & Logs**

El sistema loguea automáticamente:
- ✅ Tokens verificados exitosamente
- ⚠️ Intentos de acceso rechazados (dominio no autorizado)
- ⚠️ Rate limits excedidos
- ❌ Tokens inválidos

**Ver logs en Cloud Run:**
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

---

### **9. Agregar Nuevo Dominio**

#### **Sin redesplegar:**
1. **Opción A - Supabase:**
   ```sql
   UPDATE app_config 
   SET value = jsonb_set(value, '{allowed_domains}', 
                        value->'allowed_domains' || '["nuevodominio.com"]')
   WHERE key = 'oauth.allowed_domains';
   ```

2. **Opción B - Variable de entorno en Cloud Run:**
   ```bash
   gcloud run services update rename-driver-folders \
     --update-env-vars RENOMBRADOR_OAUTH_ALLOWED_DOMAINS='["miempresa.com","nuevodominio.com"]'
   ```

3. **Recargar config en runtime:**
   ```python
   # El ConfigManager recargará automáticamente desde env/db
   config.reload_db_config()
   ```

---

### **10. Troubleshooting**

#### **Error: "Invalid or missing token"**
- Verificar que el header sea: `Authorization: Bearer <token>`
- Verificar que el token no haya expirado (duran 1 hora)
- Verificar CLIENT_ID correcto

#### **Error: "Unauthorized domain"**
- Verificar que el dominio esté en `allowed_domains`
- O que el email esté en `allowed_emails`
- Verificar que el email esté verificado en Google

#### **Error: "Rate limit exceeded"**
- Esperar 1 minuto antes de reintentar
- Contactar admin para aumentar límite si es necesario

---

## ✅ Checklist de Implementación

- [ ] Crear OAuth Client en Google Cloud Console
- [ ] Configurar `allowed_domains` en config/db
- [ ] Implementar frontend con Google Sign-In
- [ ] Proteger endpoints con `@require_auth`
- [ ] Probar con usuario autorizado
- [ ] Probar con usuario NO autorizado
- [ ] Configurar rate limiting apropiado
- [ ] Documentar para tu equipo

---

**¡Listo!** Tu API ahora tiene seguridad OAuth con whitelist de dominios 🔒
