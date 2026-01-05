import json

with open('logs/downloaded-logs-20251226-133147.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

# Buscar logs de parsing y Gemini response
keywords = ['parsing agent response', 'gemini response received', 'successfully parsed', 'attempting to parse', 'failed to parse', 'unable to parse response']

relevant = []
for log in logs:
    text = log.get('textPayload', '')
    resource_type = log.get('resource', {}).get('type', '')
    
    if resource_type == 'cloud_run_revision' and text:
        if any(kw in text.lower() for kw in keywords):
            relevant.append(log)

print(f"Found {len(relevant)} parsing-related logs\n")
print("=" * 80)

for log in relevant[:30]:
    timestamp = log.get('timestamp', 'N/A')
    severity = log.get('severity', 'INFO')
    text = log.get('textPayload', '')
    print(f"\n[{timestamp}] [{severity}]")
    print(text[:1000])
    print("-" * 80)
