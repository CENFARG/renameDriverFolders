import json
import sys

with open('api_error.json', 'r', encoding='utf-8-sig') as f:
    content = f.read()
    # Remove BOM if present
    if content.startswith('\ufeff'):
        content = content[1:]
    logs = json.loads(content)

if logs:
    log = logs[0]
    print("=" * 80)
    print("ERROR LOG DETAILS")
    print("=" * 80)
    print(f"Timestamp: {log.get('timestamp', 'N/A')}")
    print(f"Severity: {log.get('severity', 'N/A')}")
    print("\nText Payload:")
    print("-" * 80)
    print(log.get('textPayload', 'No text payload'))
    print("=" * 80)
else:
    print("No error logs found")
