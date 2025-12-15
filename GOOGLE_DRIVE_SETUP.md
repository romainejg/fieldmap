# Google Drive Integration Guide

This guide explains how to set up Google Drive integration for Fieldmap, allowing you to automatically save photos to your Google Drive.

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

### 3. Create OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External (for personal use) or Internal (for organization)
   - App name: "Fieldmap"
   - User support email: Your email
   - Developer contact: Your email
   - Add scope: `https://www.googleapis.com/auth/drive.file`
   - Add test users (your email) if using External
4. Back to "Create Credentials" → "OAuth client ID"
5. Application type: **Desktop app**
6. Name: "Fieldmap Desktop Client"
7. Click "Create"

### 4. Download Credentials

1. After creating, click the download button (↓) next to your OAuth client
2. This downloads a JSON file
3. Rename it to **`credentials.json`**
4. Move it to your Fieldmap app directory (same folder as `app.py`)

### 5. First-Time Authentication

1. Start the Fieldmap app: `streamlit run app.py`
2. In the sidebar, click **"Sign in with Google"**
3. A browser window will open for authentication
4. Sign in with your Google account
5. Grant permissions to Fieldmap
6. You'll see "Authentication successful" message
7. A `token.pickle` file is created (stores your auth token)

### 6. Enable Cloud Storage

1. After signing in, you'll see your email in the sidebar
2. Check the box **"Save photos to Google Drive"**
3. Photos will now automatically save to Google Drive!

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

- **In-Memory First**: Photos are always kept in memory for fast access
- **Optional Cloud Backup**: When enabled, photos are also saved to Google Drive
- **Automatic Upload**: Happens when you take or annotate photos
- **URIs Stored**: Photo metadata includes Google Drive file ID for retrieval

### Authentication Token

- The `token.pickle` file stores your authentication
- **Never commit this to git** (it's in `.gitignore`)
- Valid for extended periods (auto-refreshes)
- To sign out: Click "Sign Out" in sidebar (deletes token)

## Troubleshooting

### "Credentials file not found"

**Problem:** `credentials.json` is missing

**Solution:**
1. Download OAuth2 credentials from Google Cloud Console
2. Rename to `credentials.json`
3. Place in app directory

### "Authentication failed"

**Problem:** OAuth consent screen not properly configured

**Solution:**
1. Go to Google Cloud Console
2. APIs & Services → OAuth consent screen
3. Add your email as a test user
4. Ensure app status is "Testing" or "Published"

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
3. Verify "Save photos to Google Drive" is enabled

## Security Best Practices

1. **Never share `credentials.json`**: Contains OAuth client secret
2. **Never commit `token.pickle`**: Contains your access token
3. **Use OAuth2**: More secure than API keys
4. **Scope Limitation**: App only requests `drive.file` scope (can only access files it creates)
5. **Revoke Access**: Can revoke in [Google Account Settings](https://myaccount.google.com/permissions)

## Permissions Explained

The app requests these Google permissions:

- **`https://www.googleapis.com/auth/drive.file`**
  - Allows app to create and manage only files it created
  - Cannot see or modify other files in your Drive
  - Most restrictive Drive permission available

## Advanced Configuration

### Custom Credentials Location

You can specify a custom credentials path:

```python
# In google_auth.py, modify:
google_auth = GoogleAuthHelper(
    credentials_path='/path/to/credentials.json',
    token_path='/path/to/token.pickle'
)
```

### Disabling Cloud Storage

To temporarily disable cloud storage:
1. Uncheck "Save photos to Google Drive" in sidebar
2. Photos will only be stored in memory
3. Previously uploaded photos remain in Drive

### Re-authentication

If you need to re-authenticate:
1. Click "Sign Out" in sidebar
2. Click "Sign in with Google"
3. Authorize again

## Limitations

- **Upload Only**: Current implementation doesn't auto-download from Drive
- **Session-based**: Photos are in-memory during session
- **Manual Backup**: For persistent local storage, use LocalFolderStorage instead
- **Single Account**: One Google account per session

## Future Enhancements

Potential future features:
- Download photos from Google Drive on startup
- Sync photos across devices
- Shared albums for collaboration
- Automatic conflict resolution
- Google Photos integration (in addition to Drive)

## Support

If you encounter issues:
1. Check logs in terminal where Streamlit is running
2. Verify credentials.json is valid JSON
3. Ensure Google Drive API is enabled
4. Check Google Cloud Console quotas

For more help, refer to:
- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth2 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
