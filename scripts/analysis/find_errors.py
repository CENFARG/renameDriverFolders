import json

with open('logs/downloaded-logs-20251223-235130.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

worker_logs = [l for l in logs if 'worker' in l.get('resource', {}).get('labels', {}).get('service_name', '')]

print("BUSCANDO ERRORES:")
print("=" * 80)

for log in worker_logs:
    text = log.get('textPayload', '')
    if 'error' in text.lower() or 'keyword' in text.lower() or 'traceback' in text.lower():
        print(f"\n[{log.get('timestamp')}]")
        print(text)
        print("-" * 80)
