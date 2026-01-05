#!/usr/bin/env python3
"""
Test script para invocar al Worker manualmente simulando Cloud Tasks
"""
import subprocess
import json

# Configuración
WORKER_URL = "https://renombradorarchivosgdrive-worker-v2-702567224563.us-central1.run.app/run-task"
SERVICE_ACCOUNT = "drive-902@cloud-functions-474716.iam.gserviceaccount.com"
PAYLOAD = {
    "job_id": "job-manual-generic",
    "folder_id": "1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn",
    "trigger_type": "manual"
}

print("=" * 80)
print("Testing Worker Invocation with OIDC Token")
print("=" * 80)
print(f"URL: {WORKER_URL}")
print(f"Service Account: {SERVICE_ACCOUNT}")
print(f"Payload: {json.dumps(PAYLOAD, indent=2)}")
print("=" * 80)

# Generar OIDC token
print("\n🔐 Generando OIDC token...")
token_cmd = [
    "gcloud", "auth", "print-identity-token",
    f"--impersonate-service-account={SERVICE_ACCOUNT}",
    f"--audiences={WORKER_URL}"
]

try:
    token_result = subprocess.run(token_cmd, capture_output=True, text=True, check=True)
    token = token_result.stdout.strip()
    print(f"✅ Token generado (primeros 50 chars): {token[:50]}...")
except subprocess.CalledProcessError as e:
    print(f"❌ Error generando token: {e.stderr}")
    exit(1)

# Invocar Worker
print("\n📤 Invocando Worker...")
curl_cmd = [
    "curl", "-X", "POST",
    WORKER_URL,
    "-H", "Content-Type: application/json",
    "-H", f"Authorization: Bearer {token}",
    "-d", json.dumps(PAYLOAD),
    "-w", "\\n\\nHTTP Status: %{http_code}\\n",
    "-s"
]

try:
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    print(f"\n📥 Respuesta del Worker:")
    print("=" * 80)
    print(result.stdout)
    print("=" * 80)
    
    if result.returncode == 0:
        print("\n✅ Invocación exitosa")
    else:
        print(f"\n❌ Error en invocación: {result.stderr}")
        
except Exception as e:
    print(f"❌ Error: {e}")
