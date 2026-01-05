# Instrucciones para obtener logs completos del Worker

## Paso 1: Ir a Cloud Console Logs
1. Abre: https://console.cloud.google.com/logs/query?project=cloud-functions-474716

## Paso 2: Configurar el Query
1. **Borra** todo en el Query
2. **Copia y pega** esto:
```
resource.labels.service_name="renombradorarchivosgdrive-worker-v2"
timestamp>="2025-12-24T02:45:00Z"
```
3. Presiona **"Run Query"**

## Paso 3: Expandir y copiar logs
1. Busca la línea que dice: `"POST /run-task HTTP/1.1" 200 OK`
2. **EXPANDE** esa entrada (click en la flecha)
3. Busca TODAS las líneas entre:
   - `Task received from Cloud Tasks`
   - `Job 'Manual Job Generic' complete`

## Paso 4: Copiar los logs aquí
**Específicamente busca líneas que mencionen:**
- ✅ "Found X files" o "Processing files"
- ✅ "Analyzing file"
- ❌ "No files found"
- ❌ "ERROR" o "WARNING"
- ✅ "Renamed" o "Renaming"
- ❌ Cualquier mensaje sobre permisos o Drive API

**Copia y pega TODAS esas líneas aquí.**

## ALTERNATIVA MÁS RÁPIDA
Simplemente toma una captura de pantalla de todos los logs entre "Task received" y "Job complete" y compártela.
