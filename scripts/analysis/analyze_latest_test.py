import json

with open('logs/worker_test_latest.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

print(f"Total logs: {len(logs)}\n")
print("=" * 80)

# Buscar los prints específicos
for log in logs:
    text = log.get('textPayload', '')
    if any(keyword in text for keyword in ['PROMPT SENT', 'RAW RESPONSE', 'validation error', 'Error processing']):
        timestamp = log.get('timestamp', 'N/A')
        print(f"\n[{timestamp}]")
        print(text[:2000])  # Primeros 2000 chars
        print("-" * 80)
