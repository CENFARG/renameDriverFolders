# Lección I: La Trampa de `set-env-vars` en Google Cloud Run

**Condición:** Actualizando variables de entorno en un servicio Cloud Run existente.
**Disparador:** Uso del flag `--set-env-vars` para agregar una nueva variable (ej: `GCP_PROJECT`).
**Regla:** MUST usar `--update-env-vars` para agregar/modificar variables SIN borrar las existentes.
**Consecuencia:** Si se usa `--set-env-vars`, TODAS las variables de entorno previas que no estén en lista explícita serán ELIMINADAS.

---

## 🚫 El Anti-Patrón (Lo que causó el error 500)

```bash
# Intentando agregar GCP_PROJECT...
gcloud run services update my-service \
  --set-env-vars "GCP_PROJECT=my-project"
```

**Resultado:** Se agrega `GCP_PROJECT`, pero se **BORRAN** `WORKER_URL`, `DB_HOST`, etc. El servicio falla silenciosamente hasta que alguien intenta usar la configuración faltante.

---

## ✅ El Patrón Seguro

```bash
# Agregando GCP_PROJECT manteniendo las demás...
gcloud run services update my-service \
  --update-env-vars "GCP_PROJECT=my-project"
```

**Resultado:** Se agrega/actualiza `GCP_PROJECT` y se **PRESERVAN** las demás variables.

---

## 🛡️ Algoritmo de Decisión

1. **¿Es el primer deploy?**
   - SI → Usar `--set-env-vars` (define el estado inicial limpio).
   
2. **¿Es una actualización incremental?**
   - SI → Usar `--update-env-vars`.

3. **¿Quiero borrar todo y dejar solo lo nuevo?**
   - SI → Usar `--set-env-vars` (raro, pero posible).

---

## 🔍 Checklist de Recuperación

Si accidentalmente borraste variables:
1. Buscar la revisión anterior en Cloud Console o logs de `gcloud`.
2. Listar las variables de esa revisión.
3. Volver a aplicarlas con `--update-env-vars`.
