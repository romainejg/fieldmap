# Fieldmap Setup Guide

Complete setup instructions for Fieldmap using Streamlit-native OAuth/OIDC authentication and Google Drive service account storage.

## Important: How Streamlit Native Auth Works

When you configure the `[auth]` section in `.streamlit/secrets.toml` with an OIDC provider (like Google), **Streamlit automatically handles authentication** without needing explicit `st.login()` calls in your code:

1. Streamlit adds a built-in **"Log in"** button to the UI (usually top-right corner)
2. When a user clicks it, Streamlit manages the entire OAuth/OIDC flow
3. After authentication, user info becomes available via `st.experimental_user` or `st.user`
4. The app code checks this to gate content (show About page only until logged in)

**You don't write OAuth code** - Streamlit handles it all when `[auth]` is configured!

## Overview

Fieldmap uses:
- **Streamlit native authentication** (via `[auth]` config) for user identity via Google OIDC
- **Google service account** for Drive storage (no second user OAuth flow)
- **One shared "Fieldmap" folder** in Google Drive for all photo storage

This architecture:
- ✅ Avoids dual OAuth flows
- ✅ Simplifies token management
- ✅ Uses server-to-server authentication for Drive
- ✅ Provides clean user identity via Streamlit
- ✅ No custom OAuth code needed

---

## Part 1: Google Cloud Console Setup

### 1.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project named "Fieldmap" (or use existing)
3. Note the project ID

### 1.2 Enable Required APIs

1. Navigate to **APIs & Services** → **Library**
2. Enable these APIs:
   - **Google Drive API**

### 1.3 Create OAuth 2.0 Client (Web Application)

**Purpose:** For Streamlit native authentication (user identity only)

1. Navigate to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - User Type: **External** (for testing)
   - App name: `Fieldmap`
   - User support email: your email
   - Scopes: **openid, email, profile** (NO Drive scopes here)
   - Test users: Add your email
   - Save and continue

4. Create OAuth client ID:
   - Application type: **Web application**
   - Name: `Fieldmap Web Client`
   - Authorized redirect URIs:
     - Production: `https://fieldmap.streamlit.app/oauth2callback`
     - Local dev: `http://localhost:8501/oauth2callback`
   - Click **CREATE**

5. Copy the **Client ID** and **Client Secret** - you'll need these for Streamlit secrets

### 1.4 Create Service Account (for Drive Storage)

**Purpose:** Server-to-server Drive access without user OAuth

1. Navigate to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **Service account**
3. Service account details:
   - Name: `fieldmap-drive-storage`
   - ID: `fieldmap-drive-storage` (auto-generated)
   - Description: "Service account for Fieldmap Drive storage"
   - Click **CREATE AND CONTINUE**
4. Skip optional steps, click **DONE**

5. Click on the newly created service account
6. Go to **KEYS** tab
7. Click **ADD KEY** → **Create new key**
8. Choose **JSON** format
9. Click **CREATE** - a JSON file will download
10. **Save this file securely** - you'll need it for secrets

11. **Important:** Copy the service account email address (e.g., `fieldmap-drive-storage@your-project.iam.gserviceaccount.com`)

### 1.5 Share Drive Folder with Service Account

1. Open Google Drive
2. Create a folder named **"Fieldmap"** (if not exists)
3. Right-click → **Share**
4. Add the service account email (from step 1.4.11)
5. Set permission to **Editor**
6. Uncheck "Notify people"
7. Click **Share**

Now the service account can read/write to this folder!

---

## Part 2: Streamlit Cloud Deployment

### 2.1 Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select:
   - Repository: `romainejg/fieldmap`
   - Branch: `main`
   - Main file path: `app.py`
5. Click **Deploy**

### 2.2 Configure Streamlit Secrets

1. Click **Settings** (gear icon) → **Secrets**
2. Paste the following (replace placeholders):

```toml
# Streamlit Native Authentication Config
[auth]
redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"
cookie_secret = "<GENERATE_RANDOM_SECRET>"  # See note below
client_id = "<YOUR_OAUTH_CLIENT_ID>.apps.googleusercontent.com"
client_secret = "<YOUR_OAUTH_CLIENT_SECRET>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# Google Service Account for Drive Storage
# IMPORTANT: Use TOML table format, NOT JSON string
[google_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "fieldmap-drive-storage@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

**To generate `cookie_secret`:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**For `[google_service_account]`:**
- Open the JSON file downloaded in Part 1.4.9
- Copy each field from the JSON into the TOML table format shown above
- **IMPORTANT: Use TOML table format (shown above), NOT a JSON string**
- This ensures proper parsing and no need for json.loads in the code

3. Click **Save**
4. App will restart automatically

---

## Part 3: Local Development Setup

### 3.1 Clone and Install

```bash
git clone https://github.com/romainejg/fieldmap.git
cd fieldmap
pip install -r requirements.txt
```

### 3.2 Create Local Secrets

Create `.streamlit/secrets.toml`:

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your credentials:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "<GENERATE_RANDOM_SECRET>"
client_id = "<YOUR_OAUTH_CLIENT_ID>.apps.googleusercontent.com"
client_secret = "<YOUR_OAUTH_CLIENT_SECRET>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# Service account as TOML table (NOT JSON string)
[google_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "fieldmap-drive-storage@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

**Important:**
- Use `http://localhost:8501/oauth2callback` for local dev
- Ensure this redirect URI is added in Google Cloud Console OAuth settings
- File is in `.gitignore` and won't be committed

### 3.3 Run Locally

```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## Part 4: Using the App

### 4.1 What You'll See When Launching

**When [auth] is configured in secrets.toml:**

1. Open the app at `http://localhost:8501` (local) or `https://fieldmap.streamlit.app` (cloud)
2. **Streamlit adds a "Log in" button** automatically in the top-right corner or sidebar
3. You'll see the About page (only page accessible before login)
4. The sidebar shows: "Please sign in on the About page to access Fieldmap and Gallery"

**If auth is NOT configured:**
- The About page shows setup instructions
- A "Manual Login (Dev Only)" button appears for testing without full auth setup

### 4.2 Sign In Process

1. Click Streamlit's **"Log in"** button (added automatically by Streamlit when [auth] is configured)
2. Streamlit's native OAuth/OIDC flow initiates (no custom code!)
3. Google's sign-in page opens in a popup or redirect
4. Sign in with your Google account
5. Grant permissions (only identity scopes: openid, email, profile - no Drive access)
6. Redirected back to app automatically
7. Your email displays in the About page: "Signed in as your@email.com"
8. Navigation unlocks - Fieldmap and Gallery pages become accessible

**Note:** You never see a second Drive authorization. Drive access happens via the service account in the background.

### 4.3 Take Photos

1. Navigate to **Fieldmap** page
2. Select or create a session
3. Use camera input to take a photo
4. Photo automatically saves to Google Drive via service account
5. Add notes/comments
6. Annotate photos (creates new copy)

### 4.4 Organize Photos

1. Navigate to **Gallery** page
2. Drag photos between sessions
3. Click photo tiles for details
4. Download, edit, delete photos

---

## Architecture Notes

### Authentication Flow

**User Identity (OIDC via Streamlit):**
- User clicks "Sign in with Google"
- `st.login()` initiates OAuth flow
- User authenticates with Google
- App receives ID token with email/name
- No Drive scopes requested

**Drive Storage (Service Account):**
- App uses service account credentials
- Server-to-server authentication
- No user OAuth needed for Drive
- Service account has Editor access to shared "Fieldmap" folder
- All photos saved under `Fieldmap/<SessionName>/photo_<ID>.png`

### Why Service Account?

- **No dual OAuth flows:** Users only authenticate once for identity
- **Centralized storage:** All photos in one shared folder
- **Simpler token management:** Service account credentials are static
- **Better UX:** No "Sign in with Google for Drive" prompts
- **Access control:** Use `st.user.email` for future permissions

---

## Troubleshooting

**🐛 Having issues?** Use our comprehensive debugging tools!

### Quick Diagnosis

Run the automated debugging script to identify problems:

```bash
python debug_auth.py
```

This will check:
- Secrets file configuration
- Authentication settings validity
- Service account setup
- Google API connectivity
- Streamlit version compatibility

See [docs/SETUP.md](SETUP.md) for complete troubleshooting guide.

### Common Issues

#### "Service account not configured"

**Solution:** Ensure `[google_service_account]` table is set in secrets with all required fields

Run: `python debug_auth.py` for detailed diagnostics

#### "Could not connect to Google Drive"

**Solution:**
1. Verify Drive API is enabled in Google Cloud Console
2. Check service account has Editor access to "Fieldmap" folder
3. Verify service account JSON is complete and unmodified

Run: `python debug_auth.py` to test Drive connection

#### "Sign in with Google" shows error

**Solution:**
1. Verify Streamlit version >= 1.42.0: `pip install --upgrade streamlit>=1.42.0`
2. Check `[auth]` section in secrets is complete
3. Ensure redirect URI matches exactly in Google Cloud Console
4. For local dev, use `http://localhost:8501/oauth2callback`

Run: `python debug_auth.py` to validate configuration

#### Photos not saving

**Solution:**
1. Check service account JSON is correct
2. Verify "Fieldmap" folder exists in Drive
3. Confirm service account email has Editor permission on folder
4. Check app logs for Drive API errors

Run: `python debug_auth.py` to test service account

#### "redirect_uri_mismatch" error

**Solution:**
1. In Google Cloud Console → Credentials → OAuth client
2. Verify redirect URI is exactly:
   - Production: `https://fieldmap.streamlit.app/oauth2callback`
   - Local: `http://localhost:8501/oauth2callback`
3. No trailing slashes, exact match required

#### Login button doesn't appear

**Solution:**
1. Ensure Streamlit >= 1.42.0
2. Verify complete [auth] section in secrets.toml
3. Check browser console (F12) for errors
4. Restart the app

### Debugging Resources

- **Automated diagnostics:** Run `python debug_auth.py`
- **In-app debugger:** About page → 🔍 Debug Information
- **Setup guide:** [SETUP.md](SETUP.md)

---

## Security Best Practices

1. ✅ **Never commit secrets** to Git (`.gitignore` protects this)
2. ✅ **Rotate credentials** periodically
3. ✅ **Use minimal OAuth scopes** (only openid/email/profile for users)
4. ✅ **Service account isolation** (only access to shared folder)
5. ✅ **HTTPS in production** (Streamlit Cloud handles this)
6. ✅ **Monitor service account activity** in Google Cloud Console

---

## Required Secrets Summary

**For Streamlit Cloud:**

```toml
[auth]
redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"
cookie_secret = "<generated-secret>"
client_id = "<oauth-client-id>"
client_secret = "<oauth-client-secret>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# Service account as TOML table
[google_service_account]
type = "service_account"
project_id = "your-project-id"
# ... all other fields from service account JSON ...
```

**For Local Development:**

Same as above, but `redirect_uri = "http://localhost:8501/oauth2callback"`

---

## Additional Resources

- [Streamlit Authentication Docs](https://docs.streamlit.io/develop/api-reference/connections/st.login)
- [Google Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth 2.0 OIDC](https://developers.google.com/identity/protocols/oauth2/openid-connect)

---

**Questions?** Open an issue: https://github.com/romainejg/fieldmap/issues
