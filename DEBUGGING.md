# Debugging Signin Issues

This guide will help you diagnose and fix authentication/signin problems with Fieldmap.

## Quick Diagnosis

Run the automated debugging script:

```bash
python debug_auth.py
```

This will check:
- ✓ Secrets file exists and is readable
- ✓ [auth] section is properly configured
- ✓ Service account JSON is valid
- ✓ Streamlit version compatibility
- ✓ Google API libraries are installed
- ✓ Service account can connect to Google Drive
- ✓ Google OIDC endpoint is reachable

## Common Issues and Solutions

### 1. "secrets.toml not found"

**Problem:** The secrets file doesn't exist.

**Solution:**
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Then edit `.streamlit/secrets.toml` with your actual credentials.

---

### 2. "Placeholder values detected"

**Problem:** You haven't replaced the template placeholders with real values.

**Solution:** Edit `.streamlit/secrets.toml` and replace all values that look like `<...>` with your actual credentials:

- `<generate-a-long-random-secret-here>` → Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `<Google Web OAuth client_id>` → From Google Cloud Console OAuth credentials
- `<Google Web OAuth client_secret>` → From Google Cloud Console OAuth credentials
- Service account JSON → Complete JSON from downloaded service account key file

---

### 3. "redirect_uri_mismatch" error

**Problem:** The redirect_uri in secrets doesn't match what's configured in Google Cloud Console.

**Solution:**

1. For **local development**, use:
   ```toml
   redirect_uri = "http://localhost:8501/oauth2callback"
   ```

2. For **Streamlit Cloud**, use:
   ```toml
   redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"
   ```

3. In Google Cloud Console → APIs & Services → Credentials → Your OAuth Client:
   - Add the exact redirect_uri to "Authorized redirect URIs"
   - No trailing slashes
   - Must match EXACTLY

---

### 4. "Login button doesn't appear"

**Problem:** Streamlit's native auth login button is not showing.

**Possible causes and solutions:**

**a) Streamlit version too old**
```bash
pip install --upgrade 'streamlit>=1.42.0'
streamlit --version  # Should be >= 1.42.0
```

**b) [auth] section not configured**
- Verify all required fields in `.streamlit/secrets.toml`:
  ```toml
  [auth]
  redirect_uri = "..."
  cookie_secret = "..."
  client_id = "..."
  client_secret = "..."
  server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
  ```

**c) App needs restart**
```bash
# Stop the app (Ctrl+C)
streamlit run app.py
```

---

### 5. "Service account not configured"

**Problem:** GOOGLE_SERVICE_ACCOUNT_JSON is missing or invalid.

**Solution:**

1. Create service account in Google Cloud Console
2. Download JSON key file
3. Copy entire contents into secrets.toml:
   ```toml
   GOOGLE_SERVICE_ACCOUNT_JSON = '''
   {
     "type": "service_account",
     "project_id": "your-project-id",
     "private_key_id": "...",
     "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
     "client_email": "your-sa@your-project.iam.gserviceaccount.com",
     ...
   }
   '''
   ```

**Important:** Keep the triple quotes `'''` around the JSON.

---

### 6. "Could not connect to Google Drive"

**Problem:** Service account can't access Drive.

**Solutions:**

**a) Drive API not enabled**
- Go to Google Cloud Console → APIs & Services → Library
- Search for "Google Drive API"
- Click "Enable"

**b) Fieldmap folder not shared**
- Create a folder named "Fieldmap" in Google Drive
- Right-click → Share
- Add service account email (e.g., `your-sa@your-project.iam.gserviceaccount.com`)
- Set permission to "Editor"
- Uncheck "Notify people"

**c) Invalid service account JSON**
- Verify the JSON is complete and unmodified
- Check for copy/paste errors
- Ensure private key has proper line breaks (`\n`)

---

### 7. "User authenticated but can't access pages"

**Problem:** Logged in but Fieldmap/Gallery pages won't load.

**Check:**
1. Look at browser console (F12) for JavaScript errors
2. Check app logs for Python exceptions
3. Verify service account is working (photos need Drive access)

**Solution:**
```bash
python debug_auth.py  # Check service account
```

---

### 8. OAuth consent screen issues

**Problem:** Google shows "This app isn't verified" or blocks signin.

**Solutions:**

**For development/testing:**
1. In Google Cloud Console → OAuth consent screen
2. User Type: "External"
3. Add yourself as a test user
4. You can proceed through the warning screen

**For production:**
- Complete OAuth app verification process with Google
- Or limit to internal users (if using Google Workspace)

---

## Debugging Workflow

### Step 1: Run the debug script

```bash
python debug_auth.py
```

This will tell you exactly what's wrong.

### Step 2: Check the app logs

When running locally, watch the terminal output:
```bash
streamlit run app.py
```

Look for log messages like:
- `✓ Configuration appears valid`
- `Service account email: ...`
- `User authenticated via ...`

### Step 3: Use the in-app debugger

1. Go to the About page
2. Scroll to the signin section
3. Click "🔍 Debug Information" expander
4. Review:
   - Streamlit version
   - Auth attributes availability
   - Secrets configuration
   - Service account status

### Step 4: Check browser console

1. Press F12 to open developer tools
2. Go to Console tab
3. Look for errors (red messages)
4. Common issues:
   - Network errors (check internet connection)
   - CORS errors (check redirect_uri configuration)
   - Cookie errors (try incognito mode)

## Advanced Debugging

### Enable verbose logging

Edit `app.py` and change logging level:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
```

### Test service account directly

Create a test script `test_drive.py`:

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import streamlit as st

# Load service account
sa_json = st.secrets["GOOGLE_SERVICE_ACCOUNT_JSON"]
if isinstance(sa_json, str):
    sa_data = json.loads(sa_json)
else:
    sa_data = sa_json

# Create credentials
credentials = service_account.Credentials.from_service_account_info(
    sa_data,
    scopes=['https://www.googleapis.com/auth/drive']
)

# Build service
service = build('drive', 'v3', credentials=credentials)

# List files
results = service.files().list(pageSize=10).execute()
files = results.get('files', [])

print(f"Found {len(files)} files")
for f in files:
    print(f"- {f['name']} ({f['id']})")
```

Run: `streamlit run test_drive.py`

### Check network connectivity

```bash
# Test Google OIDC endpoint
curl https://accounts.google.com/.well-known/openid-configuration

# Should return JSON with endpoints
```

### Verify OAuth credentials

1. Go to Google Cloud Console
2. APIs & Services → Credentials
3. Click on your OAuth client
4. Verify:
   - Client ID matches secrets.toml
   - Redirect URIs include your callback URL
   - Consent screen is configured

## Still Having Issues?

### Collect diagnostic information

Run and save output:
```bash
python debug_auth.py > debug_output.txt 2>&1
```

### Check these details

1. **Streamlit version:** `streamlit --version`
2. **Python version:** `python --version`
3. **Operating system:** `uname -a` (Linux/Mac) or `ver` (Windows)
4. **Browser:** Chrome, Firefox, Safari, etc.
5. **Environment:** Local dev, Streamlit Cloud, other hosting

### Create an issue

If still stuck, create a GitHub issue with:
- Output from `debug_auth.py`
- Relevant log messages (with secrets redacted)
- Steps to reproduce
- What you've already tried

## Security Reminders

⚠️ **Never commit secrets to git!**
- `.streamlit/secrets.toml` is in `.gitignore`
- Don't share secrets in screenshots or issues
- Rotate credentials if accidentally exposed

✓ **Use environment-specific configs:**
- Different redirect_uri for local vs production
- Separate OAuth clients if needed
- Different service accounts for dev/prod

## Reference Documentation

- [SETUP.md](docs/SETUP.md) - Complete setup guide
- [Streamlit Auth Docs](https://docs.streamlit.io/develop/api-reference/connections/st.login)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
