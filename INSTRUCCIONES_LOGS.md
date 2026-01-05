# Instrucciones para revisar logs del Worker

## Paso 1: Abrir la consola de logs
1. Abre este link en tu navegador: https://console.cloud.google.com/logs/query?project=cloud-functions-474716

## Paso 2: Buscar logs del Worker
1. En la caja de búsqueda grande (Query), **borra todo** lo que haya
2. **Copia y pega** esto:
```
resource.labels.service_name="renombradorarchivosgdrive-worker-v2"
timestamp>="2025-12-23T15:00:00Z"
```
3. Presiona el botón azul **"Run Query"**

## Paso 3: Revisar los resultados
Busca en los logs líneas que contengan:
- ✅ "Task received from Cloud Tasks" → Significa que el Worker SÍ recibió la tarea
- ❌ "404 Not Found" → El Worker no encontró el job config
- ❌ "ERROR" o "Traceback" → Hubo un error durante el procesamiento
- ✅ "files" o "processed" → El Worker procesó archivos

## Paso 4: Copiar los logs relevantes
Si ves alguna de esas líneas importantes, **cópialas y pégalas aquí**.

Si NO ves NADA relacionado con "Task" o "job" después de las 15:00, eso significa que el Worker nunca recibió ninguna tarea.

---

## ALTERNATIVAMENTE - Logs de Cloud Tasks

Si no ves logs del Worker, busca los logs de Cloud Tasks:

1. En la misma consola, **borra** el query anterior
2. **Copia y pega** esto:
```
protoPayload.serviceName="cloudtasks.googleapis.com"
timestamp>="2025-12-23T15:00:00Z"
```
3. Presiona **"Run Query"**
4. Busca errores como "403", "401", "timeout"
5. Copia cualquier error que veas
