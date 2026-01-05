import re

# Leer logs
with open('worker_full_logs.txt', 'r', encoding='utf-8', errors='ignore') as f:
    logs = f.read()

# Filtrar líneas relevantes para el procesamiento
relevant_keywords = [
    'Task received',
    'Job',
    'file',
    'folder',
    'renamed',
    'ERROR',
    'WARNING',
    'complete',
    'processed',
    'Found',
    'Processing',
    'Analyzing',
    'Gemini',
    'drive'
]

print("=" * 80)
print("LOGS RELEVANTES DEL WORKER (últimos 10 minutos)")
print("=" * 80)

for line in logs.split('\n'):
    line_lower = line.lower()
    if any(keyword.lower() in line_lower for keyword in relevant_keywords):
        print(line)

print("=" * 80)
print("FIN DE LOGS")
print("=" * 80)
