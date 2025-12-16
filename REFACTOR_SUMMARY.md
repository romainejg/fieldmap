# Fieldmap Refactor Summary

## Changes Made

### 1. OAuth Infrastructure (User OAuth Instead of Service Account)

**Problem**: Service account uploads were failing with `403 storageQuotaExceeded` because service accounts don't have storage quota. Photos never reached the user's Drive.

**Solution**: Implemented user OAuth flow for Google Drive access.

#### New Files Created:
- `oauth_utils.py`: OAuth utilities for user authentication and token management
  - `get_authorization_url()`: Generates OAuth authorization URL
  - `exchange_code_for_tokens()`: Exchanges authorization code for tokens
  - `get_user_credentials()`: Returns Google credentials from stored tokens
  - `is_authenticated()`: Checks authentication status
  - `logout()`: Clears authentication state

- `pages/oauth2callback.py`: OAuth callback handler for Streamlit Cloud
  - Handles OAuth redirect from Google
  - Exchanges authorization code for tokens
  - Stores tokens in session state
  - Redirects back to main app

#### Modified Files:
- `requirements.txt`: Added `google-auth-oauthlib>=1.0.0`
- `.streamlit/secrets.toml.template`: Updated to use only user OAuth (removed service account)

### 2. Storage Refactor (User OAuth-based Drive Access)

**File**: `storage.py`

**Changes**:
- `GoogleDriveStorage.__init__()`: Now accepts user OAuth credentials instead of service account info
- `_get_service()`: Builds Drive service with user credentials
- `_get_root_folder_id()`: Gets or creates Fieldmap root folder, supports DRIVE_ROOT_FOLDER_ID from secrets
- `save_image()`: Uploads to user's Drive using their OAuth tokens
- Added `move_image()`: Moves files between Drive folders (for drag-and-drop)
- Added `get_thumbnail_url()`: Gets thumbnail URL from Drive API

### 3. About Page Redesign

**File**: `app.py` - `AboutPage.render()`

**Changes**:
- Removed all debug UI and manual login sections
- Implemented clean two-column layout:
  - Left: Logo, "Hello!", "Welcome to Fieldmap", feature bullets, sign-in button
  - Right: biomedical.jpg hero image
- No header on About page (per requirements)
- "Sign in with Google" button directly opens OAuth flow (no intermediate steps)
- Removed service account diagnostics and configuration checks

### 4. App Initialization Updates

**File**: `app.py` - `App.__init__()`

**Changes**:
- Initialize storage with user OAuth credentials instead of service account
- Storage is only initialized when user is authenticated
- Removed service account validation and connection testing

### 5. Gallery Improvements

**File**: `app.py` - `GalleryPage`

**Changes**:
- Removed separate photo preview section (only draggable tiles shown)
- Added selection buttons below draggable area for viewing details
- Implemented Drive folder parent updates when photos are dragged between sessions
- Drag-and-drop now calls `storage.move_image()` to update Drive folder structure
- Cleaner error handling when Drive storage is unavailable

### 6. Authentication Gating

**File**: `app.py` - `App.render_sidebar()` and `App.run()`

**Changes**:
- Use `is_authenticated()` from oauth_utils instead of multiple auth checks
- Force About page when not authenticated
- Only show Fieldmap and Gallery in navigation after sign-in

### 7. Documentation Updates

**Files**: `README.md`, `docs/SETUP.md`

**Changes**:
- Updated architecture diagrams to show user OAuth flow
- Removed service account setup instructions
- Added comprehensive OAuth setup guide
- Added data privacy section (photos in user's Drive)
- Updated troubleshooting for user OAuth issues
- Added deployment guide for Streamlit Cloud

## What Was NOT Changed

### MarkerJS Component
- MarkerJS 3 was already properly configured in the build
- Outline circle tool (EllipseMarker) already available
- Filled shape tools already removed
- No changes needed to `components/photo_editor/`

### Fieldmap Page
- Already clean with only camera, comment, and annotation editor
- No extra preview sections
- No changes needed

### Core Functionality
- Photo annotation still creates new derived photos
- Session management unchanged
- Excel export unchanged
- Thumbnail generation unchanged (though Drive thumbnails are available via `get_thumbnail_url()`)

## Benefits of User OAuth Approach

1. **No Quota Issues**: Photos uploaded to user's own Drive using their storage quota
2. **Simpler Setup**: No service account needed, no folder sharing required
3. **Better Security**: Minimal permissions (drive.file scope only)
4. **User Control**: Users own their data, can delete anytime
5. **No Sharing**: Each user's photos in their own Drive, no shared folder needed

## Testing Checklist

Before deploying to production:

- [ ] Test OAuth flow end-to-end on Streamlit Cloud
- [ ] Verify photos upload to user's Drive
- [ ] Test annotation creates new file (not overwrites)
- [ ] Test Gallery drag-and-drop updates Drive folders
- [ ] Verify no 403 quota errors
- [ ] Test sign out and sign in again
- [ ] Verify OAuth callback works on production URL
- [ ] Test with multiple users
- [ ] Verify Drive permissions are minimal (drive.file only)

## Deployment Instructions

1. Update Google Cloud Console OAuth credentials:
   - Add redirect URI: `https://fieldmap.streamlit.app/oauth2callback`
   - Add scopes: `openid`, `email`, `profile`, `https://www.googleapis.com/auth/drive.file`

2. Update Streamlit Cloud secrets:
   ```toml
   [auth]
   redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"
   cookie_secret = "<generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'>"
   client_id = "<your-oauth-client-id>.apps.googleusercontent.com"
   client_secret = "<your-oauth-client-secret>"
   ```

3. Deploy the branch to Streamlit Cloud

4. Test OAuth flow and photo uploads

## Breaking Changes

**For existing deployments**:
- Service account credentials no longer used
- Need to reconfigure with user OAuth credentials
- Users will need to sign in with Google and grant Drive permissions
- Existing photos in shared Drive folder won't be accessible (need migration if required)

**Migration Path** (if needed):
1. Keep service account temporarily
2. Add migration script to copy photos from shared folder to user's Drive
3. Update app to use user OAuth
4. Run migration for each user
5. Remove service account

## Files Changed

- `app.py`: Refactored authentication and About page
- `storage.py`: User OAuth credentials instead of service account
- `oauth_utils.py`: NEW - OAuth flow management
- `pages/oauth2callback.py`: NEW - OAuth callback handler
- `requirements.txt`: Added google-auth-oauthlib
- `.streamlit/secrets.toml.template`: Updated for user OAuth
- `README.md`: Updated documentation
- `docs/SETUP.md`: Complete rewrite for user OAuth
