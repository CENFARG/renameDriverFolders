# tests/test_integration.py

# English: Import necessary libraries for system path manipulation, testing, and file I/O.
# Español: Importación de las bibliotecas necesarias para la manipulación de rutas del sistema, pruebas y E/S de archivos.
import os
import sys
import unittest
from io import BytesIO

# English: Add the root directory to the system path to allow importing the 'main' module.
# Español: Añade el directorio raíz a la ruta del sistema para permitir la importación del módulo 'main'.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# English: Load environment variables from .env file for the test configuration.
# Español: Carga las variables de entorno desde el archivo .env para la configuración de la prueba.
from dotenv import load_dotenv
load_dotenv()

# English: Import Google API client helpers and the functions to be tested from the main module.
# Español: Importa los ayudantes del cliente de la API de Google y las funciones a probar desde el módulo principal.
from googleapiclient.http import MediaIoBaseUpload
from main import (
    drive_service, 
    get_file_content,
    rename_drive_file, 
    update_html_index,
    analyze_content_with_gemini,
    find_target_folders_recursively
)

# --- Test Configuration from Environment / Configuración de Prueba desde el Entorno ---
# English: The root folder ID for testing must be set in the .env file.
# Español: El ID de la carpeta raíz para las pruebas debe estar configurado en el archivo .env.
TEST_ROOT_FOLDER_ID = os.environ.get("TEST_ROOT_FOLDER_ID")

# English: This class defines an integration test for the complete file processing workflow.
# Español: Esta clase define una prueba de integración para el flujo de trabajo completo de procesamiento de archivos.
class TestFileProcessingIntegration(unittest.TestCase):
    TEST_SUB_FOLDER_NAME = "_TEST_SUB_FOLDER_RENAME_APP_"
    TEST_FILE_NAME = "sample_document.txt"
    test_sub_folder_id = None
    test_file_id = None

    @classmethod
    def setUpClass(cls):
        """
        English: This method runs once before all tests in the class. It sets up the test environment in Google Drive.
        Español: Este método se ejecuta una vez antes de todas las pruebas de la clase. Configura el entorno de prueba en Google Drive.
        """
        if not TEST_ROOT_FOLDER_ID:
            raise ValueError("The TEST_ROOT_FOLDER_ID environment variable is not set in the .env file")

        print("--- Starting test environment setup ---")
        try:
            # English: 1. Create a temporary test folder inside the shared root folder.
            # Español: 1. Crear una carpeta de prueba temporal DENTRO de la carpeta raíz compartida.
            file_metadata = {
                'name': cls.TEST_SUB_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [TEST_ROOT_FOLDER_ID]
            }
            target_folder = drive_service.files().create(body=file_metadata, fields='id').execute()
            cls.test_sub_folder_id = target_folder.get('id')
            print(f"Test subfolder created: '{cls.TEST_SUB_FOLDER_NAME}' (ID: {cls.test_sub_folder_id})")

            # English: 2. Upload a sample test file to the new folder.
            # Español: 2. Subir un archivo de prueba de muestra a la nueva carpeta.
            file_metadata = {
                'name': cls.TEST_FILE_NAME,
                'parents': [cls.test_sub_folder_id]
            }
            
            with open(os.path.join(os.path.dirname(__file__), cls.TEST_FILE_NAME), 'rb') as sample_content:
                media = MediaIoBaseUpload(sample_content, mimetype='text/plain', resumable=True)
                file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

            cls.test_file_id = file.get('id')
            print(f"Test file uploaded: '{cls.TEST_FILE_NAME}' (ID: {cls.test_file_id})")
            print("--- Setup complete ---")

        except Exception as e:
            print(f"Error during setup: {e}")
            cls.tearDownClass() # English: Attempt to clean up if setup fails. / Español: Intenta limpiar si la configuración falla.
            raise

    @classmethod
    def tearDownClass(cls):
        """
        English: This method runs once after all tests in the class. It cleans up the test environment from Google Drive.
        Español: Este método se ejecuta una vez después de todas las pruebas de la clase. Limpia el entorno de prueba de Google Drive.
        """
        print("--- Starting test environment cleanup ---")
        if cls.test_sub_folder_id:
            try:
                # English: Delete the temporary test folder.
                # Español: Elimina la carpeta de prueba temporal.
                drive_service.files().delete(fileId=cls.test_sub_folder_id).execute()
                print(f"Test subfolder '{cls.TEST_SUB_FOLDER_NAME}' deleted.")
            except Exception as e:
                print(f"Error during cleanup: {e}. Please delete the subfolder manually (ID: {cls.test_sub_folder_id}).")
        print("--- Cleanup complete ---")

    def test_full_workflow(self):
        """
        English: This test executes the entire workflow: find folder, process file, rename, and update index.
        Español: Esta prueba ejecuta el flujo de trabajo completo: encontrar carpeta, procesar archivo, renombrar y actualizar el índice.
        """
        print("--- Running full workflow test ---")
        
        # English: 1. Find the target folder.
        # Español: 1. Encontrar la carpeta objetivo.
        target_folders = find_target_folders_recursively(TEST_ROOT_FOLDER_ID)
        self.assertIn(self.test_sub_folder_id, target_folders, "Test subfolder was not found.")
        
        # English: 2. Process the file content.
        # Español: 2. Procesar el contenido del archivo.
        content = get_file_content(self.test_file_id)
        self.assertIsNotNone(content, "File content could not be read.")
        
        analysis = analyze_content_with_gemini(content)
        self.assertIn("keywords", analysis)
        self.assertIn("date", analysis)
        
        # English: 3. Rename the file.
        # Español: 3. Renombrar el archivo.
        keywords_str = "_".join(analysis.get("keywords", ["doc"])).replace(" ", "")
        date_str = analysis.get("date", "nodate")
        file_extension = os.path.splitext(self.TEST_FILE_NAME)[1]
        new_name_expected = f"{date_str}_{keywords_str}_DOCPROCESADO{file_extension}"
        
        renamed_file_name = rename_drive_file(self.test_file_id, new_name_expected)
        self.assertEqual(renamed_file_name, new_name_expected, "File was not renamed correctly.")
        
        # English: 4. Update the index.
        # Español: 4. Actualizar el índice.
        summary = " ".join(analysis.get("keywords", []))
        update_html_index(self.test_sub_folder_id, self.TEST_FILE_NAME, renamed_file_name, summary)
        
        # English: 5. Verify that the renamed file and the index exist.
        # Español: 5. Verificar que el archivo renombrado y el índice existen.
        query = f"'{self.test_sub_folder_id}' in parents and trashed=false"
        response = drive_service.files().list(q=query, fields='files(id, name)').execute()
        files_after = {f['name']: f['id'] for f in response.get('files', [])}
        
        self.assertIn(new_name_expected, files_after, "The renamed file is not in the folder.")
        self.assertIn("index.html", files_after, "The index.html file was not created.")
        
        # English: 6. Verify the content of the index.
        # Español: 6. Verificar el contenido del índice.
        index_content = get_file_content(files_after["index.html"])
        self.assertIn(self.TEST_FILE_NAME, index_content, "The original name is not in the index.")
        self.assertIn(new_name_expected, index_content, "The new name is not in the index.")
        self.assertIn(summary, index_content, "The summary is not in the index.")
        
        print("--- Full workflow test finished successfully ---")

# English: Main execution block to run the tests.
# Español: Bloque de ejecución principal para correr las pruebas.
if __name__ == '__main__':
    unittest.main()