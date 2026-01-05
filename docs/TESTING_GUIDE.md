# Testing con Pytest - Guía Conceptual (Sin Programar)

## 🎯 ¿Qué es Testing y Por Qué Importa?

**Testing** = Escribir código que verifica que tu código funciona correctamente.

### Analogía del Chef
Imagina que eres un chef que cocina platos:
- **Sin tests**: Sirves el plato y esperas que el cliente no se intoxique
- **Con tests**: Pruebas cada ingrediente, cada paso de la receta, antes de servir

**Testing te dice:** "Si cambias algo, ¿seguirá funcionando todo?"

---

## 🧪 Tipos de Tests (de Más Simple a Más Complejo)

### **1. Unit Tests (Tests Unitarios)**
**Qué testean:** Una función/método aislado

**Ejemplo:**
```python
# Función a testear
def sumar(a, b):
    return a + b

# Test
def test_sumar():
    resultado = sumar(2, 3)
    assert resultado == 5  # ✅ Pasa
    
    resultado = sumar(-1, 1)
    assert resultado == 0  # ✅ Pasa
```

**Características:**
- ⚡ Muy rápidos (milisegundos)
- 🎯 Enfocados (1 función = 1 test)
- 🔌 Sin dependencias externas (no DB, no APIs)

---

### **2. Integration Tests (Tests de Integración)**
**Qué testean:** Múltiples componentes trabajando juntos

**Ejemplo:**
```python
def test_content_extractor_with_ocr():
    # Setup: crear archivo de prueba
    fake_pdf_bytes = create_scanned_pdf()
    
    # Action: usar ContentExtractor (que usa Vision API internamente)
    extractor = ContentExtractor(enable_ocr=True)
    text = extractor.get_content("scan.pdf", fake_pdf_bytes)
    
    # Assert: verificar que extrajo texto
    assert "Invoice" in text
    assert len(text) > 100
```

**Características:**
- 🐢 Más lentos (segundos)
- 🔗 Testean interacciones entre módulos
- 🌐 Pueden usar servicios reales (con mocks)

---

### **3. End-to-End Tests (E2E)**
**Qué testean:** El flujo completo del usuario

**Ejemplo:**
```python
def test_complete_file_processing_workflow():
    # 1. Subir archivo a Drive (simulado)
    file_id = upload_test_file_to_drive()
    
    # 2. Trigger el endpoint
    response = requests.post("/jobs/manual", json={"file_id": file_id})
    
    # 3. Esperar procesamiento
    time.sleep(10)
    
    # 4. Verificar que el archivo fue renombrado
    new_filename = get_file_name_from_drive(file_id)
    assert "DOCPROCESADO" in new_filename
```

**Características:**
- 🐌 Muy lentos (minutos)
- 🎭 Simulan usuario real
- 💰 Costosos (usan recursos reales)

---

## 🏗️ Estructura de un Test (AAA Pattern)

Todos los tests siguen este patrón:

```python
def test_nombre_descriptivo():
    # 1. ARRANGE (Preparar)
    # - Crear objetos necesarios
    # - Configurar estado inicial
    extractor = ContentExtractor()
    sample_bytes = b"Hello World"
    
    # 2. ACT (Actuar)
    # - Ejecutar la función que quieres testear
    result = extractor.get_content("test.txt", sample_bytes)
    
    # 3. ASSERT (Verificar)
    # - Comprobar que el resultado es el esperado
    assert result == "Hello World"
```

---

## 🎭 Mocking: Simular Dependencias

**Problema:** ¿Cómo testeo algo que usa Google Cloud Vision (cuesta dinero)?

**Solución:** **Mock** = Objeto falso que simula el comportamiento real

### Ejemplo Conceptual:

```python
# Sin mock (❌ caro, lento)
def test_ocr_integration():
    extractor = ContentExtractor()  # Usa Vision API real
    result = extractor._ocr_image_bytes(image)  # $$ 💸
    assert "text" in result

# Con mock (✅ gratis, rápido)
def test_ocr_integration_mocked():
    with mock.patch("google.cloud.vision.ImageAnnotatorClient") as mock_vision:
        # Configurar comportamiento falso
        mock_vision.return_value.document_text_detection.return_value = {
            "full_text_annotation": {"text": "Mocked text"}
        }
        
        extractor = ContentExtractor()
        result = extractor._ocr_image_bytes(image)  # Usa mock, no API real
        
        assert "Mocked text" in result
```

**Ventajas del Mocking:**
- 💰 No gastas dinero en APIs
- ⚡ Tests súper rápidos
- 🎯 Controlas exactamente qué retorna la API

---

## 🔧 Pytest: La Herramienta

**Pytest** es un framework para escribir y ejecutar tests en Python.

### **Conceptos Clave:**

#### **1. Autodescubrimiento**
Pytest encuentra automáticamente tus tests si:
- El archivo empieza con `test_` o termina con `_test.py`
- Las funciones empiezan con `test_`

```
tests/
├── test_content_extractor.py  ✅ Lo encuentra
├── test_config_manager.py     ✅ Lo encuentra
└── helper.py                  ❌ No lo ejecuta (no empieza con test_)
```

---

#### **2. Fixtures: Setup Reutilizable**
**Fixture** = Función que prepara recursos para múltiples tests

```python
import pytest

@pytest.fixture
def sample_pdf_bytes():
    """Crea un PDF de prueba reutilizable."""
    return b"%PDF-1.4 fake content"

def test_pdf_extraction(sample_pdf_bytes):
    # sample_pdf_bytes se inyecta automáticamente
    extractor = ContentExtractor()
    result = extractor.get_content("test.pdf", sample_pdf_bytes)
    assert len(result) > 0

def test_pdf_with_ocr(sample_pdf_bytes):
    # Reutiliza la misma fixture
    extractor = ContentExtractor(enable_ocr=True)
    result = extractor.get_content("scan.pdf", sample_pdf_bytes)
    assert result is not None
```

**Ventaja:** DRY (Don't Repeat Yourself) - defines el setup una vez

---

#### **3. Parametrización: Tests con Múltiples Inputs**

```python
@pytest.mark.parametrize("input,expected", [
    ("hello.txt", "hello"),
    ("document.docx", "document"),
    ("report.pdf", "report"),
])
def test_filename_parsing(input, expected):
    result = parse_filename(input)
    assert result == expected
```

**Ejecuta 3 tests diferentes** con un solo código.

---

#### **4. Markers: Categorizar Tests**

```python
@pytest.mark.slow
def test_full_integration():
    # Test que tarda mucho
    pass

@pytest.mark.unit
def test_simple_function():
    # Test rápido
    pass
```

**Ejecutar solo tests rápidos:**
```bash
pytest -m "not slow"
```

---

## 📊 Coverage: ¿Qué Tan Bien Testas?

**Code Coverage** = Porcentaje de tu código que los tests ejecutan

```bash
pytest --cov=core_renombrador --cov-report=html
```

**Resultado:**
```
Name                          Stmts   Miss  Cover
-------------------------------------------------
content_extractor.py            150     30    80%
config_manager.py               120      0   100%
database_manager.py             200     50    75%
-------------------------------------------------
TOTAL                           470     80    83%
```

**Meta recomendada:** 80%+ coverage

**⚠️ Cuidado:** 100% coverage ≠ código perfecto  
Puedes tener 100% coverage pero tests malos.

---

## 🎯 Mejores Prácticas

### **1. Tests Deben Ser:**
- ✅ **Rápidos**: < 1 segundo cada uno
- ✅ **Independientes**: Un test no depende de otro
- ✅ **Repetibles**: Mismo resultado cada vez
- ✅ **Descriptivos**: El nombre del test explica qué falla

### **2. Nombrar Tests Claramente**
```python
# ❌ MAL
def test_1():
    pass

# ✅ BIEN
def test_content_extractor_handles_empty_pdf():
    pass

def test_config_manager_loads_from_env_vars_first():
    pass
```

### **3. Un Test = Una Cosa**
```python
# ❌ MAL (testea múltiples cosas)
def test_everything():
    assert config.get("key") == "value"
    assert db.find("id", 1) is not None
    assert agent.run("test") == "ok"

# ✅ BIEN (tests separados)
def test_config_loads_correctly():
    assert config.get("key") == "value"

def test_database_finds_records():
    assert db.find("id", 1) is not None

def test_agent_processes_input():
    assert agent.run("test") == "ok"
```

### **4. Test el Comportamiento, No la Implementación**
```python
# ❌ MAL (frágil, se rompe si cambias implementación)
def test_extractor_calls_vision_api_once():
    assert extractor.vision_client.document_text_detection.call_count == 1

# ✅ BIEN (testea resultado, no cómo lo hace)
def test_extractor_returns_text_from_image():
    result = extractor.get_content("image.jpg", image_bytes)
    assert isinstance(result, str)
    assert len(result) > 0
```

---

## 📁 Estructura de Tests Recomendada

```
tests/
├── conftest.py              # Fixtures globales
├── unit/                    # Tests unitarios
│   ├── test_content_extractor.py
│   ├── test_config_manager.py
│   └── test_agent_factory.py
├── integration/             # Tests de integración
│   ├── test_database_operations.py
│   └── test_ocr_pipeline.py
└── e2e/                     # Tests end-to-end
    └── test_full_workflow.py
```

**Ejecutar por categoría:**
```bash
pytest tests/unit/           # Solo unitarios (rápidos)
pytest tests/integration/    # Solo integración
pytest tests/e2e/           # Solo E2E (lentos)
```

---

## 🚦 TDD (Test-Driven Development)

**Filosofía:** Escribe el test ANTES del código

**Flujo Red-Green-Refactor:**
```
1. 🔴 RED: Escribe un test que falla
2. 🟢 GREEN: Escribe mínimo código para que pase
3. 🔵 REFACTOR: Mejora el código manteniendo tests verdes
```

**Ejemplo:**
```python
# 1. RED: Test primero (falla porque la función no existe)
def test_parse_keywords():
    result = parse_keywords("factura impuestos enero")
    assert result == ["factura", "impuestos", "enero"]

# 2. GREEN: Implementación mínima
def parse_keywords(text):
    return text.split()  # ✅ Test pasa

# 3. REFACTOR: Mejorar (eliminar stopwords, etc.)
def parse_keywords(text):
    words = text.lower().split()
    stopwords = ["de", "la", "el"]
    return [w for w in words if w not in stopwords]
```

---

## ✅ Checklist: ¿Entendiste Testing?

Puedes explicar:
- [ ] Diferencia entre unit test e integration test
- [ ] Qué es el patrón AAA (Arrange-Act-Assert)
- [ ] Para qué sirve el mocking
- [ ] Qué es una fixture en pytest
- [ ] Qué es code coverage y por qué no es suficiente

Si respondes SÍ a todas, ¡entiendes lo fundamental! 🎉

---

## 📚 Recursos para Profundizar

- [Pytest Documentation](https://docs.pytest.org/)
- [Real Python - Pytest](https://realpython.com/pytest-python-testing/)
- [Test Driven Development Book](https://www.oreilly.com/library/view/test-driven-development/0321146530/)

---

**Próximo Paso:** Ver ejemplos concretos de tests para `renameDriverFolders`
