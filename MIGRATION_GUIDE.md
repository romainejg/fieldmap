# Migration Guide: Version 3.0 → 4.0

This document summarizes the key changes from version 3.0 to 4.0 of Fieldmap.

## Breaking Changes

### 1. OAuth Flow Changed

**Before (v3.0):**
- Desktop Application OAuth flow
- Credentials loaded from `credentials.json` file
- Tokens stored in `token.pickle` file
- Used `InstalledAppFlow.run_local_server()`

**After (v4.0):**
- Web Application OAuth flow
- Credentials loaded from secrets (no file)
- Tokens stored in session state (memory)
- Uses `Flow` with redirect URIs

**Action Required:**
1. Create new OAuth Web Application credentials (not Desktop)
2. Add authorized redirect URIs in Google Cloud Console
3. Set up secrets in Streamlit Cloud or `.streamlit/secrets.toml`
4. Remove old `credentials.json` and `token.pickle` files

### 2. Storage Model Changed

**Before (v3.0):**
- Optional Google Drive storage (toggle in sidebar)
- Default: In-memory storage only
- User could choose to enable/disable cloud storage

**After (v4.0):**
- Google Drive is the ONLY storage option
- No toggle - automatic cloud backup when authenticated
- Must sign in to use the app

**Action Required:**
- Users must have Google account and sign in
- All photos automatically saved to Google Drive
- No offline-only mode

### 3. Gallery Tiles Now Show Thumbnails

**Before (v3.0):**
- Draggable tiles showed text labels only (e.g., "Photo #1")
- Separate grid below showed thumbnail images

**After (v4.0):**
- Draggable tiles show actual thumbnail images
- Thumbnails generated as base64 data URLs
- Minimal clickable grid for selection (thumbnail + button)
- Fixed 100x100 tile size

**Action Required:**
- None - automatic upgrade
- Existing photos will have thumbnails generated on first view

### 4. Photo Metadata Extended

**Before (v3.0):**
```python
{
    'id': int,
    'original_image': Image,
    'current_image': Image,
    'thumbnail': Image,
    'comment': str,
    'timestamp': str,
    'has_annotations': bool,
    'source_photo_id': int|None,
    'variant': str,
    'storage_uri': str|None
}
```

**After (v4.0):**
```python
{
    'id': int,
    'original_image': Image,
    'current_image': Image,
    'thumbnail': Image,
    'thumb_data_url': str,        # NEW: Base64 data URL
    'comment': str,
    'timestamp': str,
    'has_annotations': bool,
    'source_photo_id': int|None,
    'variant': str,
    'storage_uri': str|None,
    'file_id': str|None           # NEW: Google Drive file ID
}
```

**Action Required:**
- None - backward compatible
- New fields populated automatically on save

## New Features

### 1. Unfilled Circle Tool in Editor

The photo editor now explicitly includes an unfilled circle/ellipse tool:
- Tool: `EllipseMarker`
- Appearance: Outline only (no fill)
- Usage: Select from tool palette, drag to draw

This was already in the code but is now documented and highlighted.

### 2. Secrets-Based Configuration

OAuth credentials now loaded from:
1. Streamlit Cloud Secrets UI
2. Local `.streamlit/secrets.toml` file
3. Environment variables

**Never from committed files.**

### 3. Improved Documentation

New documentation files:
- `SETUP_GUIDE.md`: Complete setup instructions
- `.streamlit/secrets.toml.template`: Template for local secrets
- `.github/workflows/ci.yml`: CI/CD with secrets validation
- Updated `README.md`: New architecture and setup info

## Deployment Checklist

### For Streamlit Cloud

- [ ] Create OAuth Web Application credentials
- [ ] Add redirect URI: `https://your-app.streamlit.app`
- [ ] Set `GOOGLE_OAUTH_CLIENT_JSON` in Streamlit Cloud Secrets
- [ ] Set `GOOGLE_REDIRECT_URI` in Streamlit Cloud Secrets
- [ ] Deploy app from GitHub
- [ ] Test sign-in flow
- [ ] Verify photos save to Google Drive

### For Local Development

- [ ] Create OAuth Web Application credentials
- [ ] Add redirect URI: `http://localhost:8501`
- [ ] Copy `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml`
- [ ] Fill in OAuth credentials in `secrets.toml`
- [ ] Run `streamlit run app.py`
- [ ] Test sign-in flow
- [ ] Verify photos save to Google Drive

## Security Improvements

1. ✅ No credentials in repository
2. ✅ Tokens not persisted to disk
3. ✅ CSRF protection in OAuth flow (state parameter)
4. ✅ Limited OAuth scope (drive.file only)
5. ✅ Secrets validation in CI/CD

## Backward Compatibility

### What Still Works

- ✅ Existing photo data structure (with extensions)
- ✅ Derived photo workflow
- ✅ Session organization
- ✅ Drag-and-drop gallery
- ✅ Excel export
- ✅ All annotation tools

### What Changed

- ❌ Old OAuth Desktop flow no longer supported
- ❌ Local-only storage mode removed
- ❌ File-based credentials no longer supported
- ❌ Optional cloud storage toggle removed

## Troubleshooting

### "OAuth credentials not configured"

**Solution:** Set up secrets properly (see SETUP_GUIDE.md)

### "redirect_uri_mismatch"

**Solution:** Verify redirect URI in Google Cloud Console matches your deployment URL

### Photos not saving

**Solution:** Ensure you're signed in and Google Drive API is enabled

### Old credentials.json in repo

**Solution:** Delete it - it's no longer used or needed

## Questions?

See:
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete setup instructions
- [README.md](README.md) - Architecture overview
- GitHub Issues: https://github.com/romainejg/fieldmap/issues
