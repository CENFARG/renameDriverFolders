# INSTRUCCIONES PARA REVISAR LOGS EN CLOUD CONSOLE

## Problema Actual
Los archivos siguen siendo renombrados con valores genéricos (`2025-01-01_documento_`).

## Cómo Ver Logs DEBUG

### Método 1: Cloud Console (Recomendado)
1. Ve a: https://console.cloud.google.com/logs/query?project=cloud-functions-474716

2. Usa este query:
```
resource.labels.service_name="renombradorarchivosgdrive-worker-v2"
timestamp>="2025-12-26T16:20:00Z"
severity>=DEBUG
```

3. **Busca estos mensajes clave**:
   - ✅ "Using FileAnalysis Pydantic model"
   - ✅ "Extracted content length: X chars"
   - ✅ "Sending prompt to Gemini"
   - ✅ "Gemini response received"
   - ✅ "Parsed analysis"
   - ❌ "Failed to parse"
   - ❌ "Unable to parse response"

### Qué Buscar

#### Si ves "Extracted content length: 0 chars"
**Problema**: PDFs no se están extrayendo correctamente
**Solución**: Revisar content_extractor

#### Si ves "Failed to parse agent response"
**Problema**: Gemini no devuelve formato correcto
**Solución**: Revisar que output_schema esté funcionando

#### Si ves "Using fallback values"
**Problema**: Parsing falló completamente
**Solución**: Ver el raw response de Gemini

### Método 2: CLI (Si tienes acceso)
```bash
gcloud logging read \
  "resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
  --limit 200 \
  --freshness=5m \
  --project cloud-functions-474716
```

## Lo Que Necesito Saber

1. ¿Gemini respondió algo?
2. ¿Qué formato tiene la respuesta?
3. ¿Cuántos caracteres se extrajeron del PDF?
4. ¿Hay algún error específico?

**Copia y pega las líneas relevantes que encuentres**
