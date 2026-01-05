import json

with open('logs/api_server_debug.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

print(f"Total logs: {len(logs)}\n")
print("=" * 100)

# Buscar logs relacionados con el POST request
for log in logs:
    text = log.get('textPayload', log.get('jsonPayload', {}))
    timestamp = log.get('timestamp', 'N/A')
    severity = log.get('severity', 'INFO')
    
    # Convertir jsonPayload a string si existe
    if isinstance(text, dict):
        text = json.dumps(text, indent=2)
    
    # Filtrar logs relevantes
    if any(keyword in str(text).lower() for keyword in ['post', 'manual', 'error', 'exception', 'traceback', '500']):
        print(f"\n[{timestamp}] [{severity}]")
        print(str(text)[:1500])  # Primeros 1500 chars
        print("-" * 100)
