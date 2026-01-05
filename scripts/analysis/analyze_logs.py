import json
import sys

try:
    with open('worker_logs.json', 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    print(f"Total logs: {len(logs)}")
    print("=" * 80)
    
    # Find task-related logs
    task_logs = []
    for log in logs:
        text = log.get('textPayload', '') or log.get('jsonPayload', {}).get('message', '')
        if 'task' in text.lower() or 'job' in text.lower() or 'error' in text.lower():
            task_logs.append(log)
    
    print(f"\nTask-related logs: {len(task_logs)}")
    print("=" * 80)
    
    # Show relevant logs
    for log in task_logs[-20:]:  # Last 20 relevant logs
        timestamp = log.get('timestamp', 'N/A')
        text = log.get('textPayload', '') or str(log.get('jsonPayload', {}))
        severity = log.get('severity', 'INFO')
        print(f"\n[{timestamp}] [{severity}]")
        print(text[:500])  # First 500 chars
        
except FileNotFoundError:
    print("ERROR: worker_logs.json not found. Waiting for file to be created...")
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON: {e}")
except Exception as e:
    print(f"ERROR: {e}")
