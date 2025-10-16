# tests/test_gemini_import.py

# English: Import necessary libraries for testing.
# Español: Importación de las bibliotecas necesarias para las pruebas.
import unittest
import google.generativeai as genai

# English: A test class to verify that the Google Generative AI library is installed and accessible.
# Español: Una clase de prueba para verificar que la biblioteca de Google Generative AI está instalada y es accesible.
class TestGeminiImport(unittest.TestCase):
    
    # English: This test checks if the 'genai' module can be imported and has the expected 'GenerativeModel' attribute.
    # Español: Esta prueba comprueba si el módulo 'genai' se puede importar y si tiene el atributo esperado 'GenerativeModel'.
    def test_import(self):
        # English: Print the library version for debugging purposes.
        # Español: Imprime la versión de la biblioteca para fines de depuración.
        print(f"google-generativeai version: {genai.__version__}")
        
        # English: Assert that the 'GenerativeModel' class exists in the module.
        # Español: Afirma que la clase 'GenerativeModel' existe en el módulo.
        self.assertTrue(hasattr(genai, 'GenerativeModel'))

# English: Main execution block to run the tests.
# Español: Bloque de ejecución principal para correr las pruebas.
if __name__ == '__main__':
    unittest.main()