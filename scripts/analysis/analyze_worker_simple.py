import json

# Leer logs
with open('logs/downloaded-logs-20251223-235130.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

# Filtrar logs del Worker
worker_logs = [l for l in logs if 'worker' in l.get('resource', {}).get('labels', {}).get('service_name', '')]

print(f"=" * 80)
print(f"TOTAL WORKER LOGS: {len(worker_logs)}")
print(f"=" * 80)

# Mostrar logs con textPayload
for log in worker_logs:
    timestamp = log.get('timestamp', 'N/A')
    text = log.get('textPayload', '')
    
    if text:
        print(f"\n[{timestamp}]")
        print(text)

print(f"\n" + "=" * 80)
print("FIN DE ANÁLISIS")
print("=" * 80)
