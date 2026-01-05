import json

with open('logs/downloaded-logs-20251226-133147.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

print(f"Total logs: {len(logs)}\n")
print("=" * 80)

# Buscar logs relevantes del Worker (no build logs)
keywords = ['worker initialized', 'processing file', 'extracted content', 'gemini', 'pydantic', 'parsed analysis', 'renamed', 'error processing', 'failed', 'guardrail']

relevant = []
for log in logs:
    text = log.get('textPayload', '')
    resource_type = log.get('resource', {}).get('type', '')
    
    # Solo logs de Cloud Run (no builds)
    if resource_type == 'cloud_run_revision' and text:
        if any(kw in text.lower() for kw in keywords):
            relevant.append(log)

print(f"Relevant Worker logs: {len(relevant)}\n")
print("=" * 80)

for log in relevant[:30]:
    timestamp = log.get('timestamp', 'N/A')
    severity = log.get('severity', 'INFO')
    text = log.get('textPayload', '')
    print(f"\n[{timestamp}] [{severity}]")
    print(text[:600])
    print("-" * 80)
