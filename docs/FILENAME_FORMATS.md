# Configuración de Formatos de Nombres de Archivo

## Formato actual de producción

```json
"filename_format": "{date}_{keywords}{ext}"
```

**Ejemplo de salida:**
- Archivo original: `Galicia Securities.pdf`
- Fecha extraída: `2024-12-20`
- Keywords: `["galicia", "securities", "informe"]`
- **Resultado**: `2024-12-20_galicia_securities_informe.pdf`

## Variables disponibles

| Variable | Descripción | Tipo | Ejemplo |
|----------|-------------|------|---------|
| `{date}` | Fecha extraída del documento (YYYY-MM-DD) | string | `2024-12-20` |
| `{keywords}` | Keywords separadas por `_` | string | `galicia_securities_informe` |
| `{ext}` | Extensión del archivo original | string | `.pdf` |
| `{original_filename}` | Nombre original sin extensión | string | `Galicia Securities` |

## Formatos recomendados

### 1. **Fecha + Keywords + Extensión** (Actual - Producción)
```json
"filename_format": "{date}_{keywords}{ext}"
```
✅ Mejor para: Organización cronológica con categorización

### 2. **Keywords + Fecha**
```json
"filename_format": "{keywords}_{date}{ext}"
```
✅ Mejor para: Categorización por tipo de documento

### 3. **Solo Fecha**
```json
"filename_format": "{date}_{original_filename}{ext}"
```
✅ Mejor para: Mantener nombres originales con fecha

### 4. **Formato con separador personalizado**
```json
"filename_format": "{date} - {keywords}{ext}"
```
✅ Mejor para: Legibilidad humana

## Mejores prácticas

1. **Siempre incluir `{ext}`** - Preserva el tipo de archivo
2. **Usar `_` en lugar de espacios** - Evita problemas en sistemas de archivos
3. **Fecha al principio** - Facilita ordenamiento cronológico
4. **Keywords limitadas** - El prompt solicita máximo 3 para evitar nombres muy largos

## Cómo actualizar el formato

### Método 1: Actualizar jobs.json y subir a GCS
```bash
# 1. Editar jobs.json localmente
# 2. Subir a GCS
gcloud storage cp jobs.json gs://renamedriverfolderbucket/data/jobs.json
# 3. El cambio se aplica inmediatamente en el próximo job
```

### Método 2: Futuro - Base de datos (TODO)
- Los formatos se configurarán desde una interfaz web
- Cada cliente podrá tener su propio formato
- Validación automática del template antes de guardar

## Campos personalizados

Si Gemini devuelve campos adicionales en el análisis, se pueden usar automáticamente:

```json
"output_schema": {
  "date": "str",
  "keywords": "list",
  "tipo_documento": "str",  // ← Nuevo campo
  "autor": "str"             // ← Otro campo
}
```

```json
"filename_format": "{tipo_documento}_{date}_{autor}{ext}"
```

**IMPORTANTE**: Solo se aceptan campos que sean `str`, `int` o `float`. Las listas se convierten automáticamente a string con `_`.
