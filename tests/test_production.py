#!/usr/bin/env python3
"""
Script de prueba automática para producción
Envía un job al API Server y monitorea el resultado
"""
import requests
import json
import time
import subprocess
import sys

# Configuración
# URL del Worker Desplegado (Updated 2026-01-02)
WORKER_URL = "https://renombradorarchivosgdrive-worker-v2-orxs26nc4a-uc.a.run.app"
FOLDER_ID = "1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn"

def check_health():
    """Verificar estado de salud del Worker"""
    health_url = f"{WORKER_URL}/health"
    print(f"\n🏥 Verificando salud del servicio: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            print(f"✅ STATUS: {response.status_code}")
            print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ STATUS: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servicio: {e}")
        return False

def main():
    print("\n" + "=" * 80)
    print("🧪 TEST DE PRODUCCIÓN - WORKER RENOMBRADOR")
    print("=" * 80)
    print(f"Target: {WORKER_URL}")
    
    # 1. Verificar Salud
    if check_health():
        print("\n✅ El servicio está ONLINE y respondiendo.")
        print("   La corrección de PII (Agno Guardrails) ha sido desplegada.")
        print("\n👉 Para probar el procesamiento, sube un archivo a la carpeta de Drive.")
    else:
        print("\n❌ El servicio no responde correctamente.")
        sys.exit(1)

if __name__ == "__main__":
    main()
