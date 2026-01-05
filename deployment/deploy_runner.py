import os
import subprocess
import sys
from dotenv import load_dotenv

# Load .env
load_dotenv('.env')

# Configuration
SERVICE_NAME = "renombradorarchivosgdrive-worker-v2"
PROJECT_ID = "cloud-functions-474716"
GCP_REGION = "us-central1"
IMAGE_NAME = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}"

print(f"Preparing deployment for {SERVICE_NAME}...")

# Environment Variables to inject
env_keys = [
    "ROOT_FOLDER_ID", 
    "TARGET_FOLDER_NAMES",
    "GCS_BUCKET_NAME",
    "GCP_PROJECT_ID",   # This should be the project ID
    "GCP_REGION",
    "GEMINI_API_KEY",
    "SERVICE_ACCOUNT_KEY_B64"
]

env_pairs = []
for key in env_keys:
    val = os.getenv(key)
    if not val:
        # Check if already in env (e.g. GCP_PROJECT_ID might be set by logic or env)
        if key == "GCP_PROJECT_ID": val = PROJECT_ID
        elif key == "GCP_REGION": val = GCP_REGION
        else:
            print(f"CRITICAL ERROR: Environment variable {key} is missing.")
            sys.exit(1)
    
    # Clean value (strip quotes if any)
    val = val.strip('"').strip("'")
    env_pairs.append(f"{key}={val}")

# Fix for "GOOGLE_API_KEY not set" error in google-genai library
# We map the existing GEMINI_API_KEY to GOOGLE_API_KEY
if "GEMINI_API_KEY" in env_keys:
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        cleaned_key = gemini_key.strip('"').strip("'")
        env_pairs.append(f"GOOGLE_API_KEY={cleaned_key}")

# Join with comma
env_vars_arg = ",".join(env_pairs)

# Resolve gcloud executable
import shutil
gcloud_exe = shutil.which("gcloud")
if not gcloud_exe:
    # Try with .cmd extension explicitly for Windows
    gcloud_exe = shutil.which("gcloud.cmd")
    
if not gcloud_exe:
    print("CRITICAL ERROR: 'gcloud' executable not found in PATH.")
    sys.exit(1)

print(f"Using gcloud executable: {gcloud_exe}")

# Construct command args - Bypass shell/batch limits if possible
cmd = [
    gcloud_exe, "run", "deploy", SERVICE_NAME,
    "--image", IMAGE_NAME,
    "--platform", "managed",
    "--region", GCP_REGION,
    "--allow-unauthenticated",
    "--project", PROJECT_ID,
    "--set-env-vars", env_vars_arg
]

print("Executing gcloud run deploy directly (bypassing batch file)...")
try:
    # shell=False to avoid cmd.exe length limits/parsing issues
    subprocess.run(cmd, check=True, shell=False)
    print("\nSUCCESS: Service deployed to Cloud Run.")
except subprocess.CalledProcessError as e:
    print(f"\nERROR: Deployment failed with exit code {e.returncode}")
    sys.exit(e.returncode)
except FileNotFoundError:
    print("\nERROR: 'gcloud' executable not found in PATH.")
    sys.exit(1)
