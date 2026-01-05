# Investigación: Problema de Nombres Genéricos

## 🔍 Problema Reportado

Los archivos siguen siendo renombrados con datos genéricos:
- `2025-01-01_documento_...pdf`
- No extrae fechas ni keywords reales del contenido

## 🐛 Causa Raíz Identificada

### 1. Función `parse_agent_response()` - Línea 394
**Problema**: Cuando falla el parsing de la respuesta de Gemini, retorna valores hardcoded por defecto:
```python
except:
    return {"date": "2025-01-01", "keywords": ["documento"]}
```

**Consecuencia**: Si Gemini devuelve lo que sea en formato incorrecto, se usan valores genéricos.

### 2. Falta de Logging
**Problema**: No había forma de saber:
- ¿Qué contenido se extrajo del PDF?
- ¿Qué prompt se envió a Gemini?
- ¿Qué respondió Gemini exactamente?
- ¿Por qué falló el parsing?

### 3. Job Config Incorrecto
**Problema**: Frontend envió `job_type: 'report'` pero solo existe `job-manual-generic` en jobs.json.
**Resultado**: Probablemente usa job config default o falla silenciosamente.

## ✅ Soluciones Implementadas

### 1. Logging Detallado (v00007 - Worker)
Agregado logging en cada paso crítico:
```python
logger.info(f"Extracted content length: {len(content)} chars")
logger.info(f"Sending prompt to Gemini (length: {len(prompt)} chars)")
logger.info(f"Gemini response received")
logger.info(f"Parsed analysis: {analysis}")
logger.info(f"Generated filename: {new_name}")
```

### 2. Mejor Manejo de Errores en Parsing
```python
except Exception as e:
    logger.error(f"Failed to parse: {e}. Raw response: {text[:1000]}")
    return {"date": "2025-01-01", "keywords": ["documento"]}
```

Ahora sabemos POR QUÉ falla.

### 3. Soporte para Múltiples Formatos de Code Blocks
```python
if "```json" in text:
    text = text.split("```json")[1].split("```")[0]
elif "```" in text:  # ← NUEVO
    text = text.split("```")[1].split("```")[0]
```

## 📋 Próximas Acciones

### Inmediato (Deploy en progreso)
- [x] Agregar logging detallado
- [x] Mejorar manejo de errores
- [/] Redesplegar Worker (Cloud Build en progreso)
- [ ] Probar con un archivo y revisar logs detallados

### Después del Deploy
1. **Probar** un archivo y ver los logs para identificar:
   - ¿Se extrae contenido del PDF? (ver "Extracted content length")
   - ¿Gemini responde? (ver "Gemini response received")
   - ¿En qué formato responde? (ver "Raw response")
   - ¿Por qué falla el parsing? (ver error message)

2. **Posibles problemas a investigar**:
   - El `content_extractor` no está extrayendo texto de PDFs correctamente
   - Gemini no responde en el formato JSON esperado
   - El `output_schema` de Agno no está funcionando
   - El prompt es ambiguo o confuso

3. **Soluciones potenciales**:
   - Usar `response_format` de Gemini para forzar JSON
   - Simplificar el prompt
   - Aumentar el límite de contenido de 8000 chars
   - Mejorar la extracción de texto de PDFs

## 🧪 Plan de Prueba

1. Esperar a que termine el deploy
2. Procesar 1 archivo de prueba desde el Frontend
3. Revisar logs del Worker con:
   ```bash
   gcloud logging read "resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
     --limit 100 --freshness=5m --format="value(textPayload)" | \
     findstr "Extracted Gemini Parsed Failed"
   ```
4. Identificar el problema específico
5. Aplicar fix dirigido

## 📝 Notas Adicionales

- El job config mejorado con el prompt detallado está en GCS
- Frontend debe usar `job_type: 'generic'` (no 'report') para que funcione
- Alternativamente, agregar config para `job-manual-report` en jobs.json
