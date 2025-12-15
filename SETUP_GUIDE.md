# Fieldmap Setup Guide

This guide explains how to set up Fieldmap with Google OAuth Web Application credentials and GitHub/Streamlit Cloud secrets.

## Overview

Fieldmap uses **Google Drive as the exclusive storage backend**. All photos are automatically saved to Google Drive under `Fieldmap/<SessionName>/`. Authentication is handled via OAuth 2.0 Web Application flow (not Desktop app flow).

**Key Security Features:**
- ✅ No credentials committed to repository
- ✅ Credentials loaded from secrets at runtime
- ✅ Web OAuth flow with redirect URI
- ✅ Token stored in session state (not filesystem)

---

## Part 1: Google Cloud Console Setup

### 1.1 Create/Select Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note the project name/ID

### 1.2 Enable Google Drive API

1. Navigate to **APIs & Services** → **Library**
2. Search for "Google Drive API"
3. Click **Enable**

### 1.3 Create OAuth 2.0 Credentials (Web Application)

1. Navigate to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for testing) or **Internal** (for organization)
   - App name: `Fieldmap`
   - User support email: your email
   - Scopes: Add `../auth/drive.file` (allows app to access only files it creates)
   - Test users: Add your email (if External)
   - Save and continue

4. Create OAuth client ID:
   - Application type: **Web application**
   - Name: `Fieldmap Web Client`
   - Authorized JavaScript origins:
     - For Streamlit Cloud: `https://fieldmap.streamlit.app`
     - For local dev: `http://localhost:8501`
   - Authorized redirect URIs:
     - For Streamlit Cloud: `https://fieldmap.streamlit.app`
     - For local dev: `http://localhost:8501`
   - Click **CREATE**

5. **Download the JSON**:
   - Click the download icon next to your newly created client
   - Save as `client_secret.json` (you'll copy its contents in the next step)

The JSON should look like:
```json
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["https://fieldmap.streamlit.app"]
  }
}
```

---

## Part 2: GitHub Repository Secrets (Optional but Recommended)

GitHub Secrets allow you to store sensitive data without committing it to your repository.

### 2.1 Add GitHub Repository Secrets

1. Go to your GitHub repository: `https://github.com/romainejg/fieldmap`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

**Secret 1: GOOGLE_OAUTH_CLIENT_JSON**
- Name: `GOOGLE_OAUTH_CLIENT_JSON`
- Value: Paste the **entire JSON content** from the downloaded file (including outer braces)
- Click **Add secret**

**Secret 2: APP_BASE_URL**
- Name: `APP_BASE_URL`
- Value: `https://fieldmap.streamlit.app` (or your deployment URL)
- Click **Add secret**

> **Note:** `APP_BASE_URL` replaces the legacy `GOOGLE_REDIRECT_URI` and is used as the OAuth redirect URI.

> **Note:** GitHub Secrets cannot automatically sync to Streamlit Cloud. You'll need to manually add them to Streamlit Cloud in the next step.

---

## Part 3: Streamlit Cloud Deployment

### 3.1 Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select:
   - Repository: `romainejg/fieldmap`
   - Branch: `main` (or your deployment branch)
   - Main file path: `app.py`
5. Click **Deploy**

### 3.2 Configure Streamlit Cloud Secrets

1. While the app is deploying, click **Settings** (gear icon)
2. Click **Secrets**
3. In the text editor, paste:

```toml
GOOGLE_OAUTH_CLIENT_JSON = '''
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["https://fieldmap.streamlit.app"]
  }
}
'''

APP_BASE_URL = "https://fieldmap.streamlit.app"
```

**Important:**
- Replace the JSON content with your actual OAuth client JSON
- Keep the triple quotes `'''` around the JSON
- Set `APP_BASE_URL` to your actual Streamlit Cloud URL
- `APP_BASE_URL` is used as the OAuth redirect URI (replaces legacy `GOOGLE_REDIRECT_URI`)

4. Click **Save**
5. The app will automatically restart with the new secrets

---

## Part 4: Local Development Setup

### 4.1 Install Dependencies

```bash
git clone https://github.com/romainejg/fieldmap.git
cd fieldmap
pip install -r requirements.txt
```

### 4.2 Create Local Secrets File

Create `.streamlit/secrets.toml` in your project directory:

```bash
mkdir -p .streamlit
touch .streamlit/secrets.toml
```

Add the following content:

```toml
GOOGLE_OAUTH_CLIENT_JSON = '''
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost:8501"]
  }
}
'''

APP_BASE_URL = "http://localhost:8501"
```

**Important:**
- Use `http://localhost:8501` for local development
- `APP_BASE_URL` is used as the OAuth redirect URI
- This file is already in `.gitignore` and won't be committed

### 4.3 Run Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Part 5: Using the App

### 5.1 Sign In

1. Open the app (Streamlit Cloud or local)
2. You'll see the About page with a clean hero layout
3. Click **Sign in with Google** button
4. You'll be immediately redirected to Google's OAuth consent screen (no extra steps)
5. Sign in with your Google account and grant permissions to Fieldmap
6. You'll be automatically redirected back to the app
7. The sidebar will now show Fieldmap and Gallery options

### 5.2 Take Photos

1. Select or create a session
2. Use the camera input to take a photo
3. Photo is automatically saved to Google Drive under `Fieldmap/<SessionName>/`
4. Add notes/comments
5. Use the editor to annotate (creates a new copy)

### 5.3 Organize Photos

1. Go to **Gallery** page
2. Drag photos between session containers
3. Click a photo tile to view details
4. Download, edit, or delete photos as needed

---

## Troubleshooting

### "OAuth credentials not configured"

**Solution:** Ensure `GOOGLE_OAUTH_CLIENT_JSON` is set in Streamlit Cloud secrets or `.streamlit/secrets.toml`

### "redirect_uri_mismatch" error

**Solution:** 
1. Check that `GOOGLE_REDIRECT_URI` matches your deployment URL
2. Verify redirect URI is added in Google Cloud Console OAuth settings
3. For local dev, use `http://localhost:8501` (not https)

### Photos not saving to Google Drive

**Solution:**
1. Ensure you're signed in (check sidebar)
2. Verify Google Drive API is enabled in Cloud Console
3. Check that your Google account has sufficient Drive storage

### Authentication fails after clicking link

**Solution:**
1. Clear browser cache and cookies
2. Try incognito/private browsing mode
3. Verify OAuth consent screen is configured correctly
4. For local dev, ensure redirect URI is `http://localhost:8501`

### "No valid credentials available"

**Solution:**
1. Sign out and sign in again
2. Check that OAuth client JSON is valid (no syntax errors)
3. Verify the client hasn't been deleted from Cloud Console

---

## Security Best Practices

1. ✅ **Never commit credentials** to version control
2. ✅ **Use GitHub Secrets** for sensitive data in CI/CD
3. ✅ **Restrict OAuth scopes** to minimum required (`drive.file` only)
4. ✅ **Regularly rotate** client secrets
5. ✅ **Monitor OAuth consent screen** for suspicious activity
6. ✅ **Use HTTPS** in production (Streamlit Cloud handles this)

---

## Architecture Notes

### OAuth Flow

1. User clicks "Sign in with Google"
2. App generates authorization URL with state (CSRF protection)
3. User redirected to Google OAuth consent screen
4. User grants permissions
5. Google redirects back with authorization code
6. App exchanges code for access/refresh tokens
7. Tokens stored in `st.session_state` (not filesystem)
8. Subsequent API calls use stored credentials

### Token Persistence

- Tokens stored in Streamlit session state (memory)
- Not persisted to disk (for security)
- User must re-authenticate after session expires
- Future enhancement: Store encrypted tokens in Google Drive

### Storage Architecture

- **Only storage option:** Google Drive
- **File organization:** `Fieldmap/<SessionName>/photo_<ID>.png`
- **Metadata:** File IDs stored in session state
- **Thumbnails:** Generated locally and cached as base64 data URLs

---

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Google Drive API](https://developers.google.com/drive/api/v3/about-sdk)

---

**Questions?** Open an issue on GitHub: https://github.com/romainejg/fieldmap/issues
