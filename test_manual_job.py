#!/usr/bin/env python3
"""
Script de prueba para enviar un job manual al Worker sin OAuth.
Prueba el flujo completo: API Server → Cloud Tasks → Worker
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuración
API_SERVER_URL = os.getenv("API_SERVER_URL", "https://renombradorarchivosgdrive-api-server-v2-702567224563.us-central1.run.app")
WORKER_URL = os.getenv("WORKER_URL", "https://renombradorarchivosgdrive-worker-v2-orxs26nc4a-uc.a.run.app")

# Folder ID de prueba (REEMPLAZAR con uno real que tenga archivos)
TEST_FOLDER_ID = os.getenv("TEST_FOLDER_ID", "1JD-53D0ONkRvyqW9TbquA9Z15Z8WyKLH")

def test_manual_job():
    """Envía un job manual de prueba"""

    print(f"🧪 Testing manual job to folder: {TEST_FOLDER_ID}")
    print(f"📡 API Server: {API_SERVER_URL}")
    print(f"🔧 Worker: {WORKER_URL}")
    print()

    # Payload del job
    job_payload = {
        "job_id": "job-manual-auto-classify",
        "folder_id": TEST_FOLDER_ID,
        "user_email": "test@example.com"
    }

    # Opción 1: Enviar directamente al Worker (sin OAuth/Cloud Tasks)
    print("⚡ Opción 1: Enviar directamente al Worker (sin OAuth)")
    print("-" * 50)

    try:
        worker_url = f"{WORKER_URL}/run-task"
        print(f"POST {worker_url}")

        # Crear payload simulando Cloud Task
        task_payload = {
            "job_id": "job-manual-auto-classify",
            "folder_id": TEST_FOLDER_ID,
            "execution_id": f"exec-test-{int(os.path.timestamp())}",
            "user_email": "test@example.com"
        }

        print(f"Payload: {json.dumps(task_payload, indent=2)}")
        print()

        response = requests.post(
            worker_url,
            json=task_payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutos timeout
        )

        print(f"✅ Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Result: {json.dumps(result, indent=2)}")

            # Verificar si procesó archivos
            stats = result.get("stats", {})
            files_processed = stats.get("files_processed", 0)
            files_renamed = stats.get("files_renamed", 0)

            print()
            print("📊 ESTADÍSTICAS:")
            print(f"  Archivos procesados: {files_processed}")
            print(f"  Archivos renombrados: {files_renamed}")
            print(f"  Errores: {stats.get('errors', 0)}")

            if files_processed > 0:
                print("✅ EXITO: El Worker encontró y procesó archivos")
            else:
                print("⚠️  ADVERTENCIA: El Worker procesó 0 archivos")
                print("   Revisar Cloud Logs para ver por qué no encontró archivos")

        else:
            print(f"❌ Error: {response.text}")

    except requests.exceptions.Timeout:
        print("⏱️  Timeout - El job tomó más de 2 minutos")
        print("   Esto puede ser normal si hay muchos archivos")
    except Exception as e:
        print(f"❌ Exception: {e}")

    print()

    # Opción 2: Enviar via API Server (requiere OAuth token)
    print("⚡ Opción 2: Enviar via API Server (requiere OAuth)")
    print("-" * 50)
    print("⚠️  Esta opción requiere un OAuth token válido")
    print("   Para obtenerlo, ejecuta la UI y haz login con Google")
    print()
    print("Comando para enviar con OAuth token:")
    print(f'curl -X POST "{API_SERVER_URL}/api/v1/jobs/manual" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -H "Authorization: Bearer YOUR_OAUTH_TOKEN" \\')
    print(f'  -d \'{{"folder_id": "{TEST_FOLDER_ID}"}}\'')
    print()

def check_worker_health():
    """Verifica que el Worker esté respondiendo"""
    print("🏥 Verificando salud del Worker...")
    print("-" * 50)

    try:
        # Health check (endpoint raíz)
        response = requests.get(f"{WORKER_URL}/", timeout=10)
        print(f"✅ Worker Status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Worker está respondiendo correctamente")
        else:
            print(f"⚠️  Worker respondió con status {response.status_code}")

    except Exception as e:
        print(f"❌ Error conectando al Worker: {e}")
        return False

    print()
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE JOB MANUAL - WORKER RENOMBRADOR")
    print("=" * 60)
    print()

    # Verificar salud del Worker primero
    if check_worker_health():
        # Ejecutar test
        test_manual_job()
    else:
        print("❌ El Worker no está disponible. Cancelando test.")
        exit(1)

    print()
    print("=" * 60)
    print("📋 PASOS SIGUIENTES:")
    print("=" * 60)
    print()
    print("1. Revisar Cloud Logs del Worker:")
    print(f"   gcloud logs read 'resource.labels.service_name=renombradorarchivosgdrive-worker-v2' --limit=50 --freshness=10m")
    print()
    print("2. Buscar los DEBUG logs que agregamos:")
    print("   - [process_job] target_folder_id")
    print("   - [process_folder_files] Searching for files")
    print("   - [process_folder_files] Files found:")
    print()
    print("3. Si procesó 0 archivos, revisar:")
    print("   - ¿El folder_id es correcto?")
    print("   - ¿La carpeta tiene archivos?")
    print("   - ¿El OAuth token tiene permisos?")
    print()
