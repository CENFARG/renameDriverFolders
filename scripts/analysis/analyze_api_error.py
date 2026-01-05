import json
import sys

try:
    with open('logs/api_error_debug.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content or content == '[]':
            print("No logs found in the specified time range")
            sys.exit(0)
        logs = json.loads(content)
except Exception as e:
    print(f"Error reading logs: {e}")
    sys.exit(1)

print(f"Total logs: {len(logs)}\n")
print("=" * 100)

# Buscar logs relevantes
for log in logs:
    text = log.get('textPayload', '')
    json_payload = log.get('jsonPayload', {})
    timestamp = log.get('timestamp', 'N/A')
    severity = log.get('severity', 'INFO')
    
    # Combinar ambos payloads
    combined_text = str(text) + str(json_payload)
    
    # Filtrar logs importantes
    if any(keyword in combined_text.lower() for keyword in ['error', 'exception', 'traceback', 'post', 'manual', '500', 'failed']):
        print(f"\n[{timestamp}] [{severity}]")
        if text:
            print("TEXT:", text[:1000])
        if json_payload:
            print("JSON:", json.dumps(json_payload, indent=2)[:1000])
        print("-" * 100)
