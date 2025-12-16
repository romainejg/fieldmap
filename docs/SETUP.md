# Fieldmap Setup Guide

Complete setup instructions for Fieldmap using Google OAuth 2.0 for user authentication and Drive access.

## Overview

Fieldmap uses **user OAuth** for both authentication and Google Drive access:
- ✅ Users sign in with their Google account
- ✅ Photos uploaded to **user's own Drive** (no quota issues)
- ✅ Single OAuth flow (no service account needed)
- ✅ Minimal permissions (drive.file scope only)
- ✅ Clean separation: `/oauth2callback` page handles OAuth redirect

This architecture:
- **Solves quota issues**: Photos go to user's Drive, not a service account
- **Simple**: One OAuth flow, one set of credentials
- **Secure**: Minimal permissions, user controls their data
- **No sharing needed**: Each user's photos in their own Drive

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
   - **Google+ API** (for user info)

### 1.3 Configure OAuth Consent Screen

1. Navigate to **APIs & Services** → **OAuth consent screen**
2. User Type: **External** (unless you have Google Workspace)
3. Click **CREATE**

4. Fill in required fields:
   - App name: `Fieldmap`
   - User support email: your email
   - Developer contact email: your email
   - Click **SAVE AND CONTINUE**

5. Scopes:
   - Click **ADD OR REMOVE SCOPES**
   - Add these scopes:
     - `openid`
     - `email`
     - `profile`
     - `https://www.googleapis.com/auth/drive.file` (for Drive file creation)
   - Click **UPDATE**
   - Click **SAVE AND CONTINUE**

6. Test users (if app is in testing mode):
   - Click **+ ADD USERS**
   - Add your email and any other test users
   - Click **SAVE AND CONTINUE**

7. Review and click **BACK TO DASHBOARD**

### 1.4 Create OAuth 2.0 Client (Web Application)

1. Navigate to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `Fieldmap Web Client`
5. Authorized JavaScript origins:
   - Production: `https://fieldmap.streamlit.app`
   - Local dev: `http://localhost:8501`
6. Authorized redirect URIs:
   - Production: `https://fieldmap.streamlit.app/oauth2callback`
   - Local dev: `http://localhost:8501/oauth2callback`
7. Click **CREATE**

8. **Save these credentials**:
   - Copy the **Client ID** (ends with `.apps.googleusercontent.com`)
   - Copy the **Client Secret**
   - You'll need both for Streamlit secrets

---

Now the service account can read/write to this folder!

---

## Part 2: Streamlit Cloud Deployment

### 2.1 Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select:
   - Repository: `romainejg/fieldmap`
## Part 2: Streamlit Cloud Deployment

### 2.1 Deploy App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Repository: `romainejg/fieldmap`
   - Branch: `main`
   - Main file path: `app.py`
5. Click **Deploy**

### 2.2 Configure Streamlit Secrets

1. Click **Settings** (gear icon) → **Secrets**
2. Paste the following (replace placeholders):

```toml
[auth]
redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"
cookie_secret = "<GENERATE_RANDOM_SECRET>"  # See note below
client_id = "<YOUR_OAUTH_CLIENT_ID>.apps.googleusercontent.com"
client_secret = "<YOUR_OAUTH_CLIENT_SECRET>"

# Optional: Specify an existing Drive folder ID to use as root
# DRIVE_ROOT_FOLDER_ID = "your-folder-id-here"
```

**To generate `cookie_secret`:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Notes:**
- `redirect_uri` must match exactly what you configured in Google Cloud Console
- For production, use: `https://fieldmap.streamlit.app/oauth2callback`
- `cookie_secret` is used for secure session storage
- `DRIVE_ROOT_FOLDER_ID` is optional - if not provided, a "Fieldmap" folder will be created

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

# Optional: Specify an existing Drive folder ID
# DRIVE_ROOT_FOLDER_ID = "your-folder-id-here"
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

### 4.1 Sign In Process

1. Open the app at `http://localhost:8501` (local) or `https://fieldmap.streamlit.app` (cloud)
2. You'll see the About page with a **"Sign in with Google"** button
3. Click the button
4. Google's sign-in page opens
5. Sign in with your Google account
6. Grant permissions:
   - View your email address
   - Create files in your Google Drive
7. Redirected back to app automatically via `/oauth2callback`
8. Your email displays: "Signed in as your@email.com"
9. Navigation unlocks - Fieldmap and Gallery pages become accessible

**What happens behind the scenes:**
1. App generates authorization URL with state token for CSRF protection
2. User redirects to Google for authentication
3. Google redirects to `/oauth2callback` with authorization code
4. Callback page exchanges code for access & refresh tokens
5. Tokens stored in session state (encrypted)
6. User redirected to main app
7. Photos uploaded to user's own Drive using their OAuth tokens

### 4.2 Take Photos

1. Navigate to **Fieldmap** page
2. Select or create a session
3. Use camera input to take a photo
4. Photo automatically saves to **your Google Drive** in `Fieldmap/<Session>/` folder
5. Add notes/comments
6. Annotate photos (creates new copy in same folder)

### 4.3 Organize Photos

1. Navigate to **Gallery** page
2. View draggable photo tiles organized by session
3. Drag photos between sessions
   - This moves the file between Drive folders automatically
4. Click selection buttons to view photo details
5. Download, edit, or delete photos

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

## Part 5: How It Works (Architecture)

### OAuth Flow

1. User clicks "Sign in with Google" button
2. App generates authorization URL with:
   - `client_id` (your OAuth client)
   - `redirect_uri` (`/oauth2callback`)
   - `scope` (email, drive.file)
   - `state` token (CSRF protection)
3. User redirects to Google's OAuth page
4. User authenticates and grants permissions
5. Google redirects to `https://yourapp/oauth2callback?code=...&state=...`
6. Callback page (`pages/oauth2callback.py`):
   - Verifies state token
   - Exchanges code for access & refresh tokens
   - Saves tokens in session state
   - Redirects back to main app
7. Main app uses tokens to access user's Drive

### Drive Integration

**User's Drive:**
- Photos uploaded to user's own Google Drive
- Folder structure: `Fieldmap/<Session>/photo_<ID>.png`
- No quota issues - user's storage quota used
- User has full control over their data

**Permissions:**
- `drive.file` scope - app can only access files it creates
- App cannot see or modify other Drive files
- Minimal permissions for security

**Photo Organization:**
- Each session = subfolder in `Fieldmap/`
- Drag-and-drop moves files between folders
- Annotations create new files (originals preserved)

---

## Troubleshooting

### Common Issues

#### "Failed to initiate sign-in"

**Solution:**
1. Verify `[auth]` section exists in secrets with all required fields
2. Check `client_id` and `client_secret` are correct
3. Ensure `redirect_uri` matches exactly:
   - Local: `http://localhost:8501/oauth2callback`
   - Production: `https://fieldmap.streamlit.app/oauth2callback`
4. Verify redirect URI is added in Google Cloud Console

#### "OAuth state not found" or "Invalid OAuth state"

**Solution:**
1. Clear browser cookies
2. Try signing in again
3. Ensure cookies are enabled
4. Check browser isn't blocking third-party cookies

#### "Gallery Unavailable"

**Solution:**
1. Click "Refresh Page" button
2. If issue persists, sign out and sign in again
3. Check browser console (F12) for errors

#### "redirect_uri_mismatch" error

**Solution:**
1. In Google Cloud Console → Credentials → OAuth client
2. Verify redirect URIs are exactly:
   - Production: `https://fieldmap.streamlit.app/oauth2callback`
   - Local: `http://localhost:8501/oauth2callback`
3. No trailing slashes
4. Case-sensitive match required

#### Photos not saving to Drive

**Solution:**
1. Check Drive API is enabled in Google Cloud Console
2. Verify permissions were granted during sign-in
3. Try signing out and signing in again
4. Check app logs for errors

#### "Access blocked: fieldmap hasn't completed verification"

**Solution:**
1. This appears if OAuth consent screen is not verified
2. For personal/testing use:
   - User Type: External
   - Add yourself as test user
   - Keep in "Testing" mode
3. For public use:
   - Submit app for Google verification
   - Or keep in Testing with limited test users

### Browser Requirements

- Modern browser with JavaScript enabled
- Cookies enabled
- Pop-ups allowed for OAuth flow

---

## Security Best Practices

1. ✅ **Never commit secrets** to Git (`.gitignore` protects this)
2. ✅ **Rotate credentials** periodically
3. ✅ **Use minimal OAuth scopes** (drive.file only)
4. ✅ **Keep client_secret secure** - never expose in client-side code
5. ✅ **Monitor OAuth usage** in Google Cloud Console
6. ✅ **Review Drive permissions** regularly

---

## Data Privacy

### Where Your Data Lives

- **Photos**: Stored in YOUR Google Drive account
- **Metadata**: Stored in `index.json` in your Drive
- **Session State**: Temporarily in browser session (not persisted)
- **OAuth Tokens**: Encrypted in session state (not stored on server)

### What the App Can Access

With `drive.file` scope, the app can **ONLY**:
- ✅ Create files in your Drive
- ✅ Read/modify files it created
- ❌ **CANNOT** see other Drive files
- ❌ **CANNOT** access your Gmail, Calendar, etc.

### Data Control

- **You own all data** - it's in your Drive
- **You control access** - revoke OAuth anytime at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
- **You can delete everything** - just delete the Fieldmap folder from Drive
- **No server storage** - app doesn't store photos on any server

---

## Additional Resources

- **Repository**: [github.com/romainejg/fieldmap](https://github.com/romainejg/fieldmap)
- **Issues**: [GitHub Issues](https://github.com/romainejg/fieldmap/issues)
- **Google OAuth Docs**: [developers.google.com/identity/protocols/oauth2](https://developers.google.com/identity/protocols/oauth2)
- **Drive API Docs**: [developers.google.com/drive/api](https://developers.google.com/drive/api)

---

**Need help?** Open an issue on GitHub or check the README for troubleshooting tips.
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
