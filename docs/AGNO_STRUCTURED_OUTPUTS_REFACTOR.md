# Refactoring to Agno Structured Outputs

## 🎯 Cambios Implementados

### 1. Pydantic Model para Structured Outputs (`models.py`)
**Creado**: `FileAnalysis` Pydantic model en:
- `services/worker-renombrador/src/models.py`
- `packages/core-renombrador/src/core_renombrador/models.py`

**Ventaja**: Agno usa este model para forzar JSON estructurado desde Gemini.

```python
class FileAnalysis(BaseModel):
    date: str = Field(description="...")
    keywords: List[str] = Field(min_length=3, max_length=3, description="...")
```

### 2. AgentFactory Actualizado
**Cambios** en `agent_factory.py`:
- Importa `FileAnalysis` model
- `_create_pydantic_model()` ahora retorna `FileAnalysis` directamente
- Agno usa esto con `output_schema` parameter

**Resultado**: Gemini **DEBE** devolver JSON válido en formato FileAnalysis.

### 3. Parse Response Simplificado
**Antes**: Parsing manual de JSON con fallbacks
**Ahora**: Conversión directa de Pydantic model a dict

```python
# Response es FileAnalysis Pydantic model
if hasattr(response, 'model_dump'):
    return response.model_dump()  # {'date': '...', 'keywords': [...]}
```

**Beneficio**: Eliminado parsing manual propenso a errores.

### 4. DEBUG Logging Habilitado
**Configuración**:
```python
logging.basicConfig(level=logging.DEBUG)
logger.setLevel(logging.DEBUG)
```

**Logs disponibles ahora**:
- Tipo de response de Gemini
- Contenido extraído de PDFs
- Análisis parseado
- Nombres generados
- Errores detallados

### 5. Mejores Fallbacks
**Soporta**:
- Pydantic v2 (`model_dump()`)
- Pydantic v1 (`dict()`)
- Response.content as Pydantic
- Response.content as dict
- Response.content as string (JSON parsing)

## 🧪 Cómo Probar

**Después del deploy**:
1. Procesar un archivo PDF desde Frontend
2. Verificar logs con:
```bash
gcloud logging read "resource.labels.service_name=renombradorarchivosgdrive-worker-v2" \
  --limit 100 --freshness=5m | findstr "DEBUG Successfully Pydantic FileAnalysis"
```

**Esperar ver**:
```
DEBUG: Response has Pydantic model_dump() method
DEBUG: Successfully converted Pydantic model to dict: {'date': '2024-05-27', 'keywords': ['galicia', 'valores', 'trimestral']}
```

## ✅ Beneficios

1. **Structured Outputs Garantizados**: Gemini **no puede** devolver formato incorrecto
2. **Menos Parsing Manual**: Agno maneja validación
3. **Debug Fácil**: DEBUG logging muestra TODO el flujo
4. **Type Safety**: Pydantic valida tipos automáticamente
5. **Mejor Error Handling**: Sabemos EXACTAMENTE dónde falla

## 📋 TODO

- [ ] Desplegar Worker v00008
- [ ] Probar con PDF real
- [ ] Revisar logs DEBUG
- [ ] Si funciona, quitar DEBUG logging para producción (solo INFO)
- [ ] Actualizar job config si es necesario

## 🔍 Troubleshooting

Si siguen apareciendo nombres genéricos después del deploy:

1. **Revisar logs** en Cloud Console para:
   - "Using FileAnalysis Pydantic model"
   - "Successfully converted Pydantic model"
   - "Response has .content attribute"

2. **Verificar** que el content_extractor extraiga texto:
   - "Extracted content length: X chars"

3. **Confirmar** que Gemini responda:
   - "Gemini response received"
   - "Response has structured content"

