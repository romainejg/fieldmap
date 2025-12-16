# OAuth Setup Guide - New Authlib Implementation

## Overview

This app now uses **Authlib** for OAuth authentication with Google. This is a clean, proven approach that works reliably on Streamlit Cloud.

**Key changes:**
- ✅ No cookie managers
- ✅ No custom callback paths (uses root URL)
- ✅ No "Initializing secure session..." hang
- ✅ Direct redirect with immediate fallback link
- ✅ Token persistence to Google Drive

## Setup Instructions

### 1. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable **Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

4. Create OAuth 2.0 Credentials:
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application" as the application type
   - Give it a name (e.g., "Fieldmap Web Client")
   
5. Add Authorized Redirect URIs:
   - For **Streamlit Cloud**: `https://fieldmap.streamlit.app`
   - For **local development**: `http://localhost:8501`
   - **IMPORTANT**: Use the exact URLs above (no trailing slashes, no /oauth2callback)

6. Copy the credentials:
   - Client ID (looks like: `xxxx.apps.googleusercontent.com`)
   - Client Secret

### 2. Streamlit Cloud Configuration

In your Streamlit Cloud app settings:

1. Go to "Secrets" section
2. Add the following secrets:

```toml
GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
APP_BASE_URL = "https://fieldmap.streamlit.app"
```

### 3. Local Development Configuration

1. Copy the template:
   ```bash
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   ```

2. Edit `.streamlit/secrets.toml` and fill in your credentials:
   ```toml
   GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
   APP_BASE_URL = "http://localhost:8501"
   ```

3. Make sure `.streamlit/secrets.toml` is in `.gitignore` (it already is)

### 4. OAuth Consent Screen

If your OAuth consent screen is in "Testing" mode:
- You must add test users in Google Cloud Console
- Navigate to "APIs & Services" > "OAuth consent screen"
- Scroll down to "Test users" and add email addresses

## How It Works

### Authentication Flow

1. User clicks "Sign in with Google"
2. App generates auth URL with random state token
3. User is redirected to Google (JavaScript redirect + fallback link)
4. User authorizes the app
5. Google redirects back to `APP_BASE_URL?code=...&state=...`
6. App verifies state, exchanges code for token
7. Token is stored in session_state and saved to Google Drive
8. Query params are cleared and user is redirected to app

### Token Persistence

- After successful authentication, the token is saved to `Fieldmap/_meta/token.json` in Google Drive
- This allows the app to potentially recover tokens across sessions
- Note: Drive access requires an existing token, so first-time users must still sign in

## Troubleshooting

### "Auth session expired" Error

**Cause**: State mismatch between what was sent and what was received
**Solution**: 
- Clear browser cache and cookies
- Try signing in again
- Check that APP_BASE_URL matches exactly in secrets and Google Cloud Console

### "OAuth configuration missing" Error

**Cause**: Secrets not configured properly
**Solution**:
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
- Verify APP_BASE_URL is set
- Check for typos in secret names (case-sensitive)

### Infinite Redirect Loop

**Cause**: Redirect URI mismatch
**Solution**:
- In Google Cloud Console, verify redirect URI is exactly: `https://fieldmap.streamlit.app` (for production) or `http://localhost:8501` (for local)
- **Do NOT** include `/oauth2callback` or any other path
- **Do NOT** include trailing slashes

### "Access blocked" from Google

**Cause**: OAuth consent screen in Testing mode and user not added
**Solution**:
- Add user's email to test users in Google Cloud Console
- Or publish the OAuth consent screen (requires verification for sensitive scopes)

## Debug Information

The About page has an "OAuth Debug Info" expander that shows:
- Configured APP_BASE_URL
- Computed redirect URI
- OAuth client configuration status
- Current query parameters
- OAuth state in session
- Token presence

Use this to diagnose configuration issues.

## Security Notes

- State tokens are cryptographically random (32 bytes URL-safe)
- State is verified on callback to prevent CSRF attacks
- Tokens are stored only in session_state (memory) and Google Drive (user's private storage)
- No cookies are used for OAuth state (eliminates cookie-related issues)

## Migration from Old Implementation

If you're migrating from the old cookie-based implementation:

1. **Remove old secrets**: `GOOGLE_OAUTH_CLIENT_JSON`, `COOKIE_PASSWORD` (no longer used)
2. **Add new secrets**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `APP_BASE_URL`
3. **Update redirect URIs** in Google Cloud Console (remove `/oauth2callback` path)
4. **Clear browser cache** to remove old cookies
5. **Sign in again** to get new token

## Requirements

See `requirements.txt` for dependencies:
- `authlib>=1.2.1` - OAuth client library
- `requests>=2.31.0` - HTTP library (used by Authlib)
- Google API libraries (google-auth, google-api-python-client, etc.)

## Support

For issues or questions, please check:
1. This guide
2. OAuth Debug Info in the app
3. Google Cloud Console error messages
4. Browser console for JavaScript errors
