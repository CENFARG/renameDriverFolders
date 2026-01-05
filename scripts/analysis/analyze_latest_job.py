import json
import sys

try:
    with open('latest_job_logs.json', 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    print("=" * 80)
    print("ANÁLISIS DE PROCESAMIENTO DE GEMINI")
    print("=" * 80)
    
    # Buscar logs relevantes
    relevant_keywords = ['gemini', 'analyzing', 'analysis', 'response', 'keywords', 'date', 'content', 'extract', 'file', 'renamed', 'error']
    
    for log in logs:
        text = log.get('textPayload', '')
        if text and any(kw in text.lower() for kw in relevant_keywords):
            timestamp = log.get('timestamp', 'N/A')
            print(f"\n[{timestamp}]")
            print(text[:500])  # Primeros 500 chars
            print("-" * 80)
            
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
