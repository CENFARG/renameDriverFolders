
# tests/test_gemini_import.py
import unittest
import google.generativeai as genai

class TestGeminiImport(unittest.TestCase):
    def test_import(self):
        print(f"google-generativeai version: {genai.__version__}")
        self.assertTrue(hasattr(genai, 'GenerativeModel'))

if __name__ == '__main__':
    unittest.main()
