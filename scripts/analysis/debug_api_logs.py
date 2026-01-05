import subprocess
import json
import sys

# Get latest logs
result = subprocess.run(
    ['gcloud', 'logging', 'read', 
     'resource.labels.service_name=renombradorarchivosgdrive-api-server-v2',
     '--limit', '50', '--freshness', '15m', '--format', 'json'],
    capture_output=True,
    text=True,
    cwd=r'c:\Dropbox\DOC.RECA\06-Software\renameDriverFolders'
)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
    sys.exit(1)

try:
    logs = json.loads(result.stdout)
except:
    print("No logs or invalid JSON")
    sys.exit(0)

print(f"Total logs: {len(logs)}\n")
print("=" * 100)

# Find error logs
for log in logs:
    text = log.get('textPayload', '')
    severity = log.get('severity', 'INFO')
    timestamp = log.get('timestamp', 'N/A')
    
    # Show ERROR logs and logs mentioning "task" or "500"
    if severity == 'ERROR' or any(keyword in text.lower() for keyword in ['error', 'task', '500', 'failed']):
        print(f"\n[{timestamp}] [{severity}]")
        print(text[:500])
        print("-" * 100)
