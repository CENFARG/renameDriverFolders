# OAuth Client ID Setup - Quick Guide

## Step 1: Create OAuth Client ID

**URL:** https://console.cloud.google.com/apis/credentials/oauthclient?project=cloud-functions-474716

**Instructions:**
1. Click "Create Credentials" → "OAuth client ID"
2. If prompted to configure consent screen:
   - User Type: Internal (if using Google Workspace) or External
   - App name: "RenameDriverFolders"
   - User support email: cenf.arg@gmail.com
   - Developer contact: cenf.arg@gmail.com
   - Click "Save and Continue" through all steps

3. Create OAuth Client:
   - Application type: **Web application**
   - Name: `api-server-v2`
   - Authorized JavaScript origins:
     - `https://api-server-v2-702567224563.us-central1.run.app`
   - Authorized redirect URIs:
     - `https://api-server-v2-702567224563.us-central1.run.app/auth/callback`
   - Click "Create"

4. **SAVE THE CLIENT ID**
   - It will look like: `123456789-abcdefg.apps.googleusercontent.com`
   - Copy it to a safe place

## Step 2: Provide the Client ID

Once you have the Client ID, provide it to me and I'll:
1. Store it in Secret Manager
2. Update the code
3. Deploy the changes

---

**Note:** This is a one-time manual step. After this, everything else is automated.
