# Google Drive Integration Guide

This guide explains how to set up Google Drive integration for Fieldmap. Google Drive is the exclusive storage backend for Fieldmap - all photos are automatically saved to your Google Drive.

## Prerequisites

- Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)
- Fieldmap app installed with latest dependencies

## Setup Steps

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "Fieldmap Photos")
4. Click "Create"

### 2. Enable Google Drive API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

### 3. Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. User Type: **External** (for personal use) or **Internal** (for organization)
3. Click "Create"
4. Fill in the required information:
   - App name: "Fieldmap"
   - User support email: Your email
   - Developer contact: Your email
5. Click "Save and Continue"
6. On the Scopes page, click "Add or Remove Scopes"
7. Add scope: `https://www.googleapis.com/auth/drive.file`
8. Click "Save and Continue"
9. If using External, add test users (your email)
10. Click "Save and Continue" → "Back to Dashboard"

### 4. Create OAuth2 Web Application Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **Web application**
4. Name: "Fieldmap Web Client"
5. Add Authorized redirect URIs:
   - For Streamlit Cloud: `https://your-app.streamlit.app`
   - For local development: `http://localhost:8501`
6. Click "Create"
7. Copy the entire JSON (including client_id and client_secret)

### 5. Configure App Secrets

#### For Streamlit Cloud:

1. Go to your app in Streamlit Cloud
2. Click "Settings" → "Secrets"
3. Add the following secrets:

```toml
GOOGLE_OAUTH_CLIENT_JSON = '''
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["https://your-app.streamlit.app"]
  }
}
'''

GOOGLE_REDIRECT_URI = "https://your-app.streamlit.app"

# Generate this with: python -c "import secrets; print(secrets.token_urlsafe(32))"
OAUTH_STATE_SECRET = "your-generated-secret-here"
```

#### For Local Development:

1. Create `.streamlit/secrets.toml` file in your Fieldmap directory
2. Add the following (replace with your credentials):

```toml
GOOGLE_OAUTH_CLIENT_JSON = '''
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "YOUR_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost:8501"]
  }
}
'''

GOOGLE_REDIRECT_URI = "http://localhost:8501"

# Generate this with: python -c "import secrets; print(secrets.token_urlsafe(32))"
OAUTH_STATE_SECRET = "your-generated-secret-here"
```

3. Never commit this file to git (it's in `.gitignore`)

### 6. First-Time Authentication

1. Start the Fieldmap app: `streamlit run app.py`
2. Navigate to the About page
3. Click **"Sign in with Google"**
4. Complete the Google OAuth consent screen
5. Grant permissions to Fieldmap
6. You'll be redirected back to the app
7. You should see "✅ Successfully signed in!" message

## How It Works

### Folder Structure

Photos are organized in your Google Drive as follows:

```
Google Drive/
└── Fieldmap/
    ├── Default/
    │   ├── photo_1.png
    │   ├── photo_2.png
    │   └── photo_3.png
    ├── Session1/
    │   ├── photo_4.png
    │   └── photo_5.png
    └── Session2/
        └── photo_6.png
```

- **Fieldmap**: Root folder for all Fieldmap photos
- **Session folders**: Each session gets its own subfolder
- **Photos**: Saved as PNG with photo ID in filename

### Storage Behavior

- **Cloud-First**: All photos are automatically saved to Google Drive
- **Dual Storage**: Photos kept in memory for fast access, Drive for persistence
- **Automatic Upload**: Happens when you take or annotate photos
- **File ID Tracking**: Photo metadata includes Google Drive file ID for retrieval

### Authentication Token

- Tokens are stored in session state (memory only)
- Tokens are not persisted to disk
- Valid for the duration of your session
- To sign out: Click "Sign Out" in sidebar

## Troubleshooting

### "OAuth credentials not configured"

**Problem:** Secrets are not properly set

**Solution:**
1. For Streamlit Cloud: Add secrets in app settings
2. For local: Create `.streamlit/secrets.toml` with credentials
3. See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions

### "redirect_uri_mismatch"

**Problem:** Redirect URI in Google Cloud Console doesn't match deployment URL

**Solution:**
1. Go to Google Cloud Console → Credentials
2. Edit your OAuth client
3. Ensure redirect URI exactly matches:
   - Production: `https://your-app.streamlit.app` (no trailing slash, no /oauth2callback)
   - Local: `http://localhost:8501`
4. Save and try again

### "Invalid OAuth state"

**Problem:** CSRF protection detected a potential attack or session was reset

**Solution:**
1. Clear browser cookies for the app
2. Try the sign-in flow again
3. Don't use browser back button during OAuth
4. Ensure `OAUTH_STATE_SECRET` is configured in secrets

### "Failed to save to storage"

**Problem:** Network issues or insufficient permissions

**Solution:**
1. Check internet connection
2. Verify Google Drive API is enabled
3. Ensure OAuth scope includes `drive.file`
4. Try signing out and back in

### "Files not appearing in Google Drive"

**Problem:** Files may take a moment to sync

**Solution:**
1. Refresh Google Drive in browser
2. Check the "Fieldmap" folder in "My Drive"
3. Verify you're signed in (check About page)

## Security Best Practices

1. **Never commit secrets**: Keep `.streamlit/secrets.toml` out of git
2. **Use environment-specific secrets**: Different credentials for local vs production
3. **Use OAuth2**: More secure than API keys
4. **Scope Limitation**: App only requests `drive.file` scope (can only access files it creates)
5. **Stateless OAuth**: Uses cryptographically signed state tokens for CSRF protection
6. **Revoke Access**: Can revoke in [Google Account Settings](https://myaccount.google.com/permissions)

## Permissions Explained

The app requests these Google permissions:

- **`https://www.googleapis.com/auth/drive.file`**
  - Allows app to create and manage only files it created
  - Cannot see or modify other files in your Drive
  - Most restrictive Drive permission available

## Advanced Configuration

### Custom OAuth State Secret

For production deployments, always set a strong OAuth state secret:

```bash
# Generate a secure secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to secrets.toml
OAUTH_STATE_SECRET = "generated-secret-here"
```

### Environment Variables

You can also use environment variables instead of secrets.toml:

```bash
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export APP_BASE_URL="http://localhost:8501"
export OAUTH_STATE_SECRET="your-generated-secret"
```

## Limitations

- **Cloud-Only**: Google Drive is the only storage option
- **Authentication Required**: Must sign in to use the app
- **Single Account**: One Google account per session
- **Session-Based**: Tokens not persisted across app restarts

## Support

If you encounter issues:
1. Check the app logs in terminal or Streamlit Cloud
2. Verify secrets are correctly configured
3. Ensure Google Drive API is enabled
4. Check Google Cloud Console quotas
5. Review [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete setup instructions

For more help, refer to:
- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth2 for Web Apps](https://developers.google.com/identity/protocols/oauth2/web-server)
