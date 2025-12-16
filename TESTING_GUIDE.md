# Testing Guide

This guide covers testing the Fieldmap application, including OAuth authentication, photo workflows, and integration tests.

## Running Unit Tests

Fieldmap includes several test suites that can be run independently:

### Storage Tests
Tests for photo storage, derived photos, and Google Drive integration:

```bash
python test_derived_photos.py
```

### Integration Tests
Tests for complete workflows (capture, annotate, organize):

```bash
python test_integration.py
```

### OAuth State Tests
Tests for OAuth state signing and verification:

```bash
python test_google_oauth_state.py
```

### Component Tests
Tests for the photo editor component:

```bash
python test_photo_editor_component.py
```

### Run All Tests

```bash
python test_derived_photos.py && \
python test_integration.py && \
python test_google_oauth_state.py && \
python test_photo_editor_component.py
```

All tests should pass. If you encounter failures, check that you have all dependencies installed:

```bash
pip install -r requirements.txt
```

## Manual Testing

### Prerequisites

Before testing, ensure you have:

1. **Google Cloud Console Setup**: OAuth 2.0 Client ID configured with correct redirect URIs
2. **Secrets Configured**: Either in Streamlit Cloud or local `.streamlit/secrets.toml`
3. **Dependencies Installed**: Run `pip install -r requirements.txt`

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Testing Checklist

### Test 1: OAuth Authentication Flow

1. [ ] Open the app (either `https://your-app.streamlit.app` or `http://localhost:8501`)
2. [ ] Verify you land on the About page
3. [ ] Verify sidebar shows "Please sign in on the About page to access Fieldmap and Gallery"
4. [ ] Click **"Sign in with Google"** button
5. [ ] **Expected**: Redirect to Google OAuth consent screen
6. [ ] Complete Google OAuth consent (approve permissions)
7. [ ] **Expected**: Redirect back to app
8. [ ] **Expected**: "✅ Successfully signed in!" message appears
9. [ ] **Expected**: Page shows "Signed in as [your-email]"
10. [ ] **Expected**: Sidebar now shows Fieldmap, Gallery, and About options

### Test 2: Navigation While Authenticated

1. [ ] Click **Fieldmap** in sidebar
2. [ ] Verify Fieldmap page loads correctly
3. [ ] Click **Gallery** in sidebar
4. [ ] Verify Gallery page loads correctly
5. [ ] Click **About** in sidebar
6. [ ] Verify About page shows "✅ Signed In" with your email
7. [ ] Verify message: "📱 Access Fieldmap and Gallery from the sidebar"

### Test 3: Sign-Out Flow

1. [ ] On About page, click **"Sign Out"** button
2. [ ] Verify "Signed out successfully" message appears
3. [ ] Verify page shows sign-in UI again
4. [ ] Verify sidebar only shows "About" option

### Test 4: Photo Workflow

1. [ ] Sign in if not already signed in
2. [ ] Navigate to Fieldmap page
3. [ ] Take a photo using the camera input
4. [ ] Add a comment/description
5. [ ] Verify photo appears in the session
6. [ ] Click "Edit Photo" to annotate
7. [ ] Draw some annotations (lines, shapes, text)
8. [ ] Save the annotated photo
9. [ ] Verify a new derived photo is created
10. [ ] Verify original photo remains unchanged
11. [ ] Navigate to Gallery page
12. [ ] Verify both photos appear
13. [ ] Verify derived photo shows "Derived from Photo #X" badge

### Test 5: Gallery Organization

1. [ ] In Gallery page, create a new session
2. [ ] Drag photos between sessions
3. [ ] Verify photos move correctly
4. [ ] Export session to Excel
5. [ ] Verify Excel file contains photo metadata

### Test 6: Error Handling

1. [ ] Sign out if signed in
2. [ ] Try to access Fieldmap directly via URL
3. [ ] Verify you're redirected to About page with sign-in UI
4. [ ] Click "Sign in with Google"
5. [ ] On Google consent screen, click "Cancel" or "Deny"
6. [ ] Verify error is handled gracefully

### Test 7: Local Development (Optional)

1. [ ] Set up local `.streamlit/secrets.toml` (see [SETUP_GUIDE.md](SETUP_GUIDE.md))
2. [ ] Run `streamlit run app.py`
3. [ ] Open `http://localhost:8501`
4. [ ] Repeat authentication and photo workflow tests
5. [ ] Verify all functionality works locally

## Troubleshooting

### Issue: "redirect_uri_mismatch" error

**Solution**: Verify your Google Cloud Console redirect URIs exactly match your deployment URL:
- Production: `https://your-app.streamlit.app`
- Local: `http://localhost:8501`

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed configuration instructions.

### Issue: "Invalid OAuth state" error

**Solution**: This is a security check to prevent CSRF attacks. If you see this:
1. Clear browser cookies for the app
2. Try the sign-in flow again
3. Don't use the browser back button during OAuth flow

### Issue: Photos not saving to Google Drive

**Solution**:
1. Verify you're signed in (check About page)
2. Check internet connection
3. Verify Google Drive API is enabled in Google Cloud Console
4. Check app logs for specific errors

### Issue: Tests failing

**Solution**:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check that you're using Python 3.8 or higher
3. For OAuth tests, ensure `OAUTH_STATE_SECRET` is set

## Support

If you encounter issues during testing:
1. Check the logs in Streamlit Cloud or terminal output
2. Verify your Google Cloud Console configuration
3. Review [SETUP_GUIDE.md](SETUP_GUIDE.md) for setup details
4. Check [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) for Drive-specific issues
5. Open an issue on GitHub with error details

## Success Criteria

All manual tests pass and:
- ✅ OAuth authentication works smoothly
- ✅ Photos can be captured and annotated
- ✅ Derived photos are created correctly
- ✅ Gallery drag-and-drop works
- ✅ Excel export includes correct metadata
- ✅ Sign-out clears authentication properly
