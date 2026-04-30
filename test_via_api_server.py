#!/usr/bin/env python3
"""
Script para enviar un job a través del API Server con un OAuth token de prueba
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuración
API_SERVER_URL = "https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app"
TEST_FOLDER_ID = "1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH"

print("=" * 60)
print("INSTRUCCIONES PARA PROBAR EL WORKER")
print("=" * 60)
print()
print("Opción 1: Desde la UI (Más fácil)")
print("-" * 60)
print("1. Abre la UI: https://renombradorarchivosgdrive-frontend-v2-702567224563.us-central1.run.app")
print("2. Haz login con Google OAuth")
print("3. Selecciona la carpeta de prueba:", TEST_FOLDER_ID)
print("4. Haz clic en 'Renombrar Archivos'")
print("5. Revisa los logs del Worker:")
print()
print("Opción 2: Via API Server (requiere OAuth token)")
print("-" * 60)
print("1. Haz login en la UI para obtener el token")
print("2. Abre DevTools → Application → Local Storage")
print("3. Copia el valor de 'oauth_token'")
print("4. Ejecuta:")
print()
print(f'curl -X POST "{API_SERVER_URL}/api/v1/jobs/manual" \\')
print(f'  -H "Content-Type: application/json" \\')
print(f'  -H "Authorization: Bearer YOUR_OAUTH_TOKEN" \\')
print(f'  -d \'{{"folder_id": "{TEST_FOLDER_ID}"}}\'')
print()
print("Opción 3: Ver logs del Worker en tiempo real")
print("-" * 60)
print("gcloud logs tail 'resource.labels.service_name=renombradorarchivosgdrive-worker-v2' --filter='severity>=DEBUG'")
print()
print("=" * 60)
print("DESPUÉS DE ENVIAR EL JOB:")
print("=" * 60)
print("1. Buscar en los logs estos mensajes DEBUG:")
print("   - [process_job] target_folder_id:")
print("   - [process_folder_files] Searching for files in folder_id:")
print("   - [process_folder_files] Files found:")
print()
print("2. Si ves 'NO FILES FOUND', el problema es:")
print("   - Folder ID incorrecto")
print("   - OAuth token sin permisos")
print("   - La carpeta está vacía")
print()
print("3. Si ves archivos procesados pero 0 renombrados:")
print("   - La IA no pudo clasificar los documentos")
print("   - Revisar logs de Gemini/API calls")
print()
