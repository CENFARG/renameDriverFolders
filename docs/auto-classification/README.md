# 🤖 Clasificación Automática de Documentos

## 📋 Descripción

Esta carpeta contiene la documentación para implementar el sistema de clasificación automática de documentos, donde la IA determina automáticamente qué algoritmo aplicar a cada documento.

## 🎯 Objetivo

Implementar un sistema donde la IA clasifique AUTOMÁTICAMENTE cada documento y aplique el algoritmo correcto según su tipo, SIN intervención del usuario.

## 📁 Archivos

### 1. INSTRUCCIONES_CLASIFICACION_AUTOMATICA.md ⭐
**Guía completa de implementación**

- Arquitectura de clasificación automática
- Paso 1: Crear tabla de algoritmos en Supabase
- Paso 2: Modificar el Worker
- Paso 3: Deploy
- Paso 4: Testing
- Resultados esperados
- Checklist final

### 2. AUTO_CLASSIFICATION_PATCH.md
**Código de las nuevas funciones del Worker**

- `load_document_algorithms(db_manager)` - Cargar algoritmos
- `classify_document(file_name, file_content, algorithms)` - Clasificar con IA
- `process_folder_files_with_auto_classify()` - Procesar con clasificación

## 🗄️ Scripts SQL

### scripts/create_algorithms_table.sql
Crea la tabla `document_algorithms` en Supabase.

### scripts/insert_algorithms_test.sql
Inserta el primer algoritmo (factura_rg830) para testing.

### scripts/insert_remaining_algorithms.sql
Inserta los 5 algoritmos restantes:
- recibo_sueldo
- resumen_bancario
- estado_contable
- contrato
- generic

## 🚀 Estado Actual

**Estado:** ⏸️ PAUSADO - Prioridad resolver problema de Diego primero

**Por qué pausado:**
- El problema de Diego (OAuth User Credentials) es más crítico
- Diego no puede procesar archivos actualmente
- Clasificación automática es una mejora, no un fix crítico

**Próximos pasos:**
1. ✅ Completar implementación de OAuth User Credentials
2. ⏸️ Retomar clasificación automática

## 📊 Algoritmos Preconfigurados

| ID | Nombre | Descripción |
|----|--------|-------------|
| factura_rg830 | Facturas RG 830 | Facturas de servicios públicos con resolución 830 |
| recibo_sueldo | Recibos de Sueldo | Recibos de haberes y liquidaciones de nómina |
| resumen_bancario | Resumenes Bancarios | Resúmenes de cuenta y extractos bancarios |
| estado_contable | Estados Contables | Balances generales y estados patrimoniales |
| contrato | Contratos y Acuerdos | Contratos de alquiler, servicios, venta, compra |
| generic | Genérico - Detección Automática | Algoritmo por defecto para documentos sin clasificación específica |

## 🎯 Flujo de Clasificación Automática

```
Usuario selecciona carpeta
        ↓
Sistema tiene MÚLTIPLES algoritmos configurados
        ↓
Por CADA documento en la carpeta:
  1. IA clasifica: "Esto es una Factura RG 830"
  2. Sistema busca algoritmo: factura_rg830
  3. IA usa instrucciones específicas de RG 830
  4. Renombra con formato de RG 830
        ↓
Documento siguiente:
  1. IA clasifica: "Esto es un Recibo de Sueldo"
  2. Sistema busca algoritmo: recibo_sueldo
  3. IA usa instrucciones específicas de Recibos
  4. Renombra con formato de Recibos
```

## 🔗 Relacionado

- Implementación OAuth: `../oauth-user-credentials/`
- Memoria del día: `../../RESUMEN_DIA_19_MARZ_2026.md`
- Scripts SQL: `../../scripts/`

---

**Estado:** Diseño completado, pendiente implementación
**Prioridad:** MEDIA (después de OAuth User Credentials)
