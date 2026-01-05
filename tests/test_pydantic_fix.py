
import sys
import os

# Agregamos la ruta del servicio para poder importar models
sys.path.append(os.path.abspath("services/worker-renombrador"))

try:
    from src.models import FileAnalysis
    print("✅ Successfully imported FileAnalysis model")
except ImportError as e:
    print(f"❌ Error importing models: {e}")
    sys.exit(1)

# Payload que estaba fallando (con 'examples')
problematic_payload = {
    "date": "2024-12",
    "category": "RESUMEN",
    "issuer": "Banco-Galicia",
    "brief_detail": "resumen-cuenta-corriente",
    "examples": [  # Este campo era el "extra forbidden"
        {
            "date": "2024-12",
            "category": "RESUMEN",
            "issuer": "Banco-Galicia",
            "brief_detail": "resumen-cuenta-corriente"
        }
    ]
}

print("\n--- Testing Validation ---")
try:
    # Intentamos validar el payload problemático
    model = FileAnalysis(**problematic_payload)
    print("✅ VALIDATION SUCCESS: The model accepted the payload with extra fields!")
    print(f"Parsed data: {model.model_dump()}")
except Exception as e:
    print("❌ VALIDATION FAILED: The model rejected the payload.")
    print(f"Error: {e}")

