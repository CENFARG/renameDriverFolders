# tests/test_integration.py

import os
import sys
import unittest
from io import BytesIO

# Añadir el directorio raíz al path para poder importar main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from googleapiclient.http import MediaIoBaseUpload
from main import (
    drive_service, 
    get_file_content,
    rename_drive_file, 
    update_html_index,
    analyze_content_with_gemini,
    find_target_folders_recursively
)

# --- LEER LA CONFIGURACIÓN DE PRUEBA DESDE EL ENTORNO ---
# El ID de la carpeta raíz para las pruebas debe estar en el archivo .env
TEST_ROOT_FOLDER_ID = os.environ.get("TEST_ROOT_FOLDER_ID")

class TestFileProcessingIntegration(unittest.TestCase):
    TEST_SUB_FOLDER_NAME = "_TEST_SUB_FOLDER_RENAME_APP_"
    TEST_FILE_NAME = "sample_document.txt"
    test_sub_folder_id = None
    test_file_id = None

    @classmethod
    def setUpClass(cls):
        if not TEST_ROOT_FOLDER_ID:
            raise ValueError("La variable de entorno TEST_ROOT_FOLDER_ID no está configurada en el archivo .env")

        print("--- Iniciando configuración del entorno de prueba ---")
        try:
            # 1. Crear carpeta objetivo de prueba DENTRO de la raíz compartida
            file_metadata = {
                'name': cls.TEST_SUB_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [TEST_ROOT_FOLDER_ID]
            }
            target_folder = drive_service.files().create(body=file_metadata, fields='id').execute()
            cls.test_sub_folder_id = target_folder.get('id')
            print(f"Subcarpeta de prueba creada: '{cls.TEST_SUB_FOLDER_NAME}' (ID: {cls.test_sub_folder_id})")

            # 2. Subir archivo de prueba
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
            print(f"Archivo de prueba subido: '{cls.TEST_FILE_NAME}' (ID: {cls.test_file_id})")
            print("--- Configuración completada ---")

        except Exception as e:
            print(f"Error durante la configuración: {e}")
            cls.tearDownClass() # Intentar limpiar si algo falló
            raise

    @classmethod
    def tearDownClass(cls):
        print("--- Iniciando limpieza del entorno de prueba ---")
        if cls.test_sub_folder_id:
            try:
                drive_service.files().delete(fileId=cls.test_sub_folder_id).execute()
                print(f"Subcarpeta de prueba '{cls.TEST_SUB_FOLDER_NAME}' eliminada.")
            except Exception as e:
                print(f"Error durante la limpieza: {e}. Por favor, elimina la subcarpeta manualmente (ID: {cls.test_sub_folder_id}).")
        print("--- Limpieza completada ---")

    def test_full_workflow(self):
        print("--- Ejecutando prueba de flujo completo ---")
        
        # 1. Encontrar la carpeta objetivo
        target_folders = find_target_folders_recursively(TEST_ROOT_FOLDER_ID)
        self.assertIn(self.test_sub_folder_id, target_folders, "La subcarpeta de prueba no fue encontrada.")
        
        # 2. Procesar el archivo
        content = get_file_content(self.test_file_id)
        self.assertIsNotNone(content, "El contenido del archivo no pudo ser leído.")
        
        analysis = analyze_content_with_gemini(content)
        self.assertIn("keywords", analysis)
        self.assertIn("date", analysis)
        
        # 3. Renombrar el archivo
        keywords_str = "_".join(analysis.get("keywords", ["doc"])).replace(" ", "")
        date_str = analysis.get("date", "nodate")
        file_extension = os.path.splitext(self.TEST_FILE_NAME)[1]
        new_name_expected = f"{date_str}_{keywords_str}_DOCPROCESADO{file_extension}"
        
        renamed_file_name = rename_drive_file(self.test_file_id, new_name_expected)
        self.assertEqual(renamed_file_name, new_name_expected, "El archivo no fue renombrado correctamente.")
        
        # 4. Actualizar el índice
        summary = " ".join(analysis.get("keywords", []))
        update_html_index(self.test_sub_folder_id, self.TEST_FILE_NAME, renamed_file_name, summary)
        
        # 5. Verificar que el índice y el archivo renombrado existen
        query = f"'{self.test_sub_folder_id}' in parents and trashed=false"
        response = drive_service.files().list(q=query, fields='files(id, name)').execute()
        files_after = {f['name']: f['id'] for f in response.get('files', [])}
        
        self.assertIn(new_name_expected, files_after, "El archivo renombrado no se encuentra en la carpeta.")
        self.assertIn("index.html", files_after, "El archivo index.html no fue creado.")
        
        # 6. Verificar contenido del índice
        index_content = get_file_content(files_after["index.html"])
        self.assertIn(self.TEST_FILE_NAME, index_content, "El nombre original no está en el índice.")
        self.assertIn(new_name_expected, index_content, "El nuevo nombre no está en el índice.")
        self.assertIn(summary, index_content, "El resumen no está en el índice.")
        
        print("--- Prueba de flujo completo finalizada con éxito ---")

if __name__ == '__main__':
    unittest.main()
