# Implementación de Especificaciones del Cliente
## Estudio Cutignola - Diego Cutignola (Nov 2025)

### 📄 Documento Fuente
`.context/Informe_de_Proyecto_renombre_archivos.pdf`

---

## ✅ Cambios Implementados

### 1. Formato de Nomenclatura

**Formato Objetivo del Cliente**:
```
[FECHA]_[CATEGORÍA]_[EMISOR]_[DETALLE_BREVE].[EXT]
```

**Antes** (genérico):
```
{date}_{keywords}{ext}
Ejemplo: 2024-05-27_galicia_valores_trimestral.pdf
```

**Ahora** (según cliente):
```
{date}_{category}_{issuer}_{brief_detail}{ext}
Ejemplo: 2024-12_RESUMEN_Banco-Galicia_resumen-cuenta-corriente.pdf
```

---

### 2. Taxonomía de Categorías (Exclusivas)

| Categoría | Descripción | Ejemplos |
|-----------|-------------|----------|
| **CONTABLE** | Documentación formal contable | Balances, Libro Diario, Sumas y Saldos |
| **FACTURA** | Comprobantes fiscales | Facturas A/B/C, Tickets, Notas de Crédito |
| **SUELDO** | Documentación laboral | Recibos de Haberes, F931, Liquidaciones |
| **RESUMEN** | Extractos financieros | Resúmenes Bancarios,  Tarjetas, Brokers |
| **IMPUESTO** | Obligaciones tributarias | VEPs, DDJJ IIBB/Ganancias, Tasas |
| **LEGAL** | Documentos jurídicos | Contratos, Estatutos, Actas |
| **DOC-INTERNA** | Papeles de trabajo | Excel auxiliares, borradores |
| **CONSTANCIA** | Identificación fiscal | Inscripciones, CUIT |

---

### 3. Reglas de Inferencia de Fecha

| Tipo de Documento | Formato | Ejemplo |
|-------------------|---------|---------|
| **Puntuales** | YYYY-MM-DD | Facturas: `2024-05-27` |
| **Mensuales** | YYYY-MM | Resúmenes: `2024-12` |
| **Anuales** | YYYY | Balances: `2024` |

---

### 4. Pydantic Model Actualizado

**Archivo**: `services/worker-renombrador/src/models.py`

```python
class FileAnalysis(BaseModel):
    date: str  # YYYY-MM-DD, YYYY-MM, o YYYY
    category: Literal[
        "CONTABLE", "FACTURA", "SUELDO", "RESUMEN", 
        "IMPUESTO", "LEGAL", "DOC-INTERNA", "CONSTANCIA"
    ]
    issuer: str  # Max 30 chars, sin espacios
    brief_detail: str  # Max 50 chars, lowercase, hyphens
```

**Ventaja**: `Literal` fuerza a Gemini a elegir solo UNA categoría válida.

---

### 5. Prompt Actualizado

**Archivo**: `jobs.json`

**Mejoras**:
- ✅ Instrucciones específicas para cada campo
- ✅ Ejemplos concretos del cliente
- ✅ Reglas de fecha según tipo de documento
- ✅ Taxonomía completa de categorías
- ✅ Formato más estricto y descriptivo

**Extracto del prompt**:
```
CATEGORÍA (elige UNA exclusivamente):
- CONTABLE: Balances, Libro Diario, Sumas y Saldos
- FACTURA: Facturas A/B/C, Tickets, Notas de Crédito
- RESUMEN: Resúmenes Bancarios, Tarjetas, Brokers
...
```

---

## 🧪 Ejemplos de Salida Esperada

### Resumen Bancario
```json
{
  "date": "2024-12",
  "category": "RESUMEN",
  "issuer": "Banco-Galicia",
  "brief_detail": "resumen-cuenta-corriente"
}
```
**Nombre**: `2024-12_RESUMEN_Banco-Galicia_resumen-cuenta-corriente.pdf`

### Factura de Proveedor
```json
{
  "date": "2024-05-27",
  "category": "FACTURA",
  "issuer": "Proveedor-ABC",
  "brief_detail": "factura-b-servicios"
}
```
**Nombre**: `2024-05-27_FACTURA_Proveedor-ABC_factura-b-servicios.pdf`

### Balance Anual
```json
{
  "date": "2024",
  "category": "CONTABLE",
  "issuer": "Estudio",
  "brief_detail": "balance-anual"
}
```
**Nombre**: `2024_CONTABLE_Estudio_balance-anual.pdf`

---

## 📌 Notas de Implementación

1. **Gemini 2.5 Flash-002**: Modelo más reciente en Vertex AI
2. **Logging Completo**: Veremos prompt + respuesta en logs
3. **Guardrails**: PII Detection + Prompt Injection Prevention
4. **Pydantic Validation**: Gemini DEBE devolver formato correcto

---

## 🚀 Próximo Paso

1. Esperar build (Worker v00010)
2. Desplegar
3. Probar con archivo real del cliente
4. Revisar logs para confirmar formato correcto

---

**Fecha de Implementación**: 26 de Diciembre 2025  
**Based on**: Informe de Diego Cutignola (Nov 2025)
