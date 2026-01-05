import requests
import json

url = "https://renombradorarchivosgdrive-worker-v2-702567224563.us-central1.run.app/run-task"
payload = {
    "job_id": "job-manual-generic",
    "folder_id": "1Q4by0XHi5S_4qOdZH_Fl4jBaX5flIXjn",
    "trigger_type": "manual"
}

print("Sending test request to Worker...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"\nError: {e}")
