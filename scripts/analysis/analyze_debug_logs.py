import json

try:
    with open('worker_debug_logs.json', 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    print("=" * 80)
    print(f"TOTAL LOGS: {len(logs)}")
    print("=" * 80)
    
    # Buscar logs relevantes
    keywords = ['DEBUG', 'gemini', 'pydantic', 'fileanalysis', 'parsed', 'extracted', 'guardrail', 'processed', 'renamed', 'error']
    
    found_count = 0
    for log in logs:
        text = log.get('textPayload', '')
        if text and any(kw in text.lower() for kw in keywords):
            timestamp = log.get('timestamp', 'N/A')
            severity = log.get('severity', 'INFO')
            print(f"\n[{timestamp}] [{severity}]")
            print(text[:800])  # Primeros 800 chars
            print("-" * 80)
            found_count += 1
    
    print(f"\n{'='*80}")
    print(f"FOUND {found_count} relevant log entries")
    print("=" * 80)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
