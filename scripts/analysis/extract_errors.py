import json

with open('logs/downloaded-logs-20251226-133147.json', 'r', encoding='utf-8') as f:
    logs = json.load(f)

# Buscar errores del Worker
errors = [l for l in logs 
          if 'textPayload' in l 
          and l.get('resource', {}).get('type') == 'cloud_run_revision'
          and ('error' in l.get('textPayload', '').lower() 
               or 'failed' in l.get('textPayload', '').lower()
               or 'exception' in l.get('textPayload', '').lower())]

print(f"Total error logs found: {len(errors)}\n")
print("=" * 80)

for log in errors[:20]:
    print(f"\n[{log.get('timestamp')}] [{log.get('severity')}]")
    print(log.get('textPayload'))
    print("-" * 80)
