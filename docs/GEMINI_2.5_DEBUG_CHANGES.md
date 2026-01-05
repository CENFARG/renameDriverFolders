# Cambios Implementados para Debugging

## ✅ Actualizaciones

### 1. Modelo Gemini
**Actualizado a**: `gemini-2.5-flash-002`  
**Razón**: Es el modelo más reciente disponible en Vertex AI que soporta structured outputs

### 2. Logging Completo de Gemini I/O
**Agregado en** `main.py` líneas ~340-365:

```python
# LOG COMPLETO DEL PROMPT
print("\n" + "="*80)
print("PROMPT SENT TO GEMINI:")
print("="*80)
print(prompt[:2000])  # Primeros 2000 chars
print("=" *80 + "\n")

response = agent.run(prompt)

# LOG COMPLETO DE LA RESPUESTA
print("\n" + "="*80)
print("RAW RESPONSE FROM GEMINI:")
print("="*80)
print(f"Type: {type(response)}")
print(f"Has .content: {hasattr(response, 'content')}")
if hasattr(response, 'content'):
    print(f"Content type: {type(response.content)}")
    print(f"Content: {response.content}")
print(f"Response repr: {repr(response)[:500]}")
print("="*80 + "\n")
```

**Beneficio**: Ahora veremos EXACTAMENTE:
- Qué prompt se envía a Gemini
- Qué tipo de objeto devuelve Agno
- Si tiene `.content` y de qué tipo es
- El contenido completo de la respuesta

### 3. Guardrails y Pydantic
✅ Ya implementados:
- `PIIDetectionGuardrail()`
- `PromptInjectionGuardrail()`
- `output_schema=FileAnalysis` (Pydantic model)

## 🧪 Cómo Probar

1. **Procesa un archivo** desde el Frontend
2. **Ve a Cloud Console Logs**: https://console.cloud.google.com/logs/query?project=cloud-functions-474716
3. **Busca estos prints** (stdout del container):
   - `PROMPT SENT TO GEMINI:`
   - `RAW RESPONSE FROM GEMINI:`

## 📋 Qué Verificar en Logs

### Si funciona correctamente:
```
RAW RESPONSE FROM GEMINI:
Type: <class 'agno.run.response.RunResponse'>
Has .content: True
Content type: <class 'services.worker_renombrador.src.models.FileAnalysis'>
Content: FileAnalysis(date='2024-05-27', keywords=['galicia', 'valores', 'trimestral'])
```

### Si falla:
```
RAW RESPONSE FROM GEMINI:
Type: <class 'agno.run.response.RunResponse'>
Has .content: True
Content type: <class 'str'>
Content: '{"date": "2024-05-27", ...}'  # ← String en lugar de Pydantic model
```

## 🔍 Debugging Checklist

- [ ] Deploy completado
- [ ] Procesar archivo de prueba
- [ ] Revisar logs en Cloud Console
- [ ] Verificar tipo de `response.content`
- [ ] Si es string en lugar de Pydantic model → problema con output_schema
- [ ] Si es Pydantic model → debería funcionar perfectamente

## 📌 Notas

- Gemini 2.5 Flash es el más nuevo y rápido
- Soporta structured outputs según Google Cloud docs
- DEBUG logging temporal (quitar en producción final)
