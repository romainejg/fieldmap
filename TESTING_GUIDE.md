# OAuth Fix - Testing Guide

## Pre-Testing Setup

### 1. Update Google Cloud Console

Before testing, you MUST update your OAuth 2.0 Client ID redirect URIs:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click on your OAuth 2.0 Client ID (e.g., "Fieldmap Web Client")
4. Under **Authorized redirect URIs**, update to:
   - **Remove**: `https://fieldmap.streamlit.app/oauth2callback`
   - **Add**: `https://fieldmap.streamlit.app`
   
   For local development:
   - **Remove**: `http://localhost:8501/oauth2callback`
   - **Add**: `http://localhost:8501`

5. Click **Save**

### 2. Verify Streamlit Secrets (if needed)

Your secrets should already be configured, but verify they match:

```toml
GOOGLE_OAUTH_CLIENT_JSON = '''
{
  "web": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    ...
    "redirect_uris": ["https://fieldmap.streamlit.app"]
  }
}
'''

APP_BASE_URL = "https://fieldmap.streamlit.app"
```

## Testing Checklist

### Test 1: Sign-In Flow

1. [ ] Open the app: `https://fieldmap.streamlit.app`
2. [ ] Verify you land on the About page
3. [ ] Verify sidebar shows "Please sign in on the About page to access Fieldmap and Gallery"
4. [ ] Click **"Sign in with Google"** button
5. [ ] **Expected**: Immediate redirect to Google (no delay, no waiting)
6. [ ] **Expected**: You see both JS redirect happening AND a "Continue to Google" link immediately
7. [ ] Complete Google OAuth consent screen
8. [ ] **Expected**: Redirect back to `https://fieldmap.streamlit.app/?code=...&state=...`
9. [ ] **Expected**: "Completing sign-in..." spinner appears briefly
10. [ ] **Expected**: "✅ Successfully signed in!" message appears
11. [ ] **Expected**: Page reloads and shows "Signed in as [your-email]"
12. [ ] **Expected**: Sidebar now shows Fieldmap, Gallery, and About options
13. [ ] **Expected**: NO "missing page /oauth2callback" error at any point

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
5. [ ] Verify clicking Fieldmap or Gallery in URL redirects back to About page

### Test 4: Error Handling

1. [ ] Sign out if signed in
2. [ ] Try to access Fieldmap directly: `https://fieldmap.streamlit.app/?current_page=Fieldmap`
3. [ ] Verify you're redirected to About page with sign-in UI
4. [ ] Click "Sign in with Google"
5. [ ] On Google consent screen, click "Cancel" or "Deny"
6. [ ] Verify error is displayed appropriately

### Test 5: Local Development (Optional)

1. [ ] Update your `.streamlit/secrets.toml` with `APP_BASE_URL = "http://localhost:8501"`
2. [ ] Update Google Cloud Console redirect URI to `http://localhost:8501`
3. [ ] Run `streamlit run app.py`
4. [ ] Repeat Test 1 steps on `http://localhost:8501`
5. [ ] Verify OAuth flow works identically

## Expected Improvements

### Before This Fix

- ❌ After Google login: "You have requested page /oauth2callback, but no corresponding file was found in the app's pages/ directory."
- ❌ ~1 minute delay before "Continue to Google" link appears
- ❌ Token exchange might not complete properly

### After This Fix

- ✅ After Google login: Smooth redirect back to app with immediate token exchange
- ✅ Immediate redirect to Google (no delay)
- ✅ Token exchange completes automatically
- ✅ Clean user experience with no errors

## Troubleshooting

### Issue: "redirect_uri_mismatch" error

**Solution**: Verify your Google Cloud Console redirect URIs exactly match:
- Production: `https://fieldmap.streamlit.app` (no /oauth2callback)
- Local: `http://localhost:8501` (no /oauth2callback)

### Issue: Still seeing "missing page /oauth2callback" error

**Solution**: You may need to clear browser cache or open in incognito mode. The old redirect URI might be cached.

### Issue: Redirect takes a long time

**Solution**: This is expected on first run. Streamlit may need to compile the app. Subsequent redirects should be instant.

### Issue: "Invalid OAuth state" error

**Solution**: This is a security check. If you see this:
1. Clear browser cookies for the app
2. Try again
3. Don't use the browser back button during OAuth flow

## Security Verification

All changes have been validated with CodeQL security scanner - 0 vulnerabilities found.

Key security features maintained:
- ✅ CSRF protection via state parameter validation
- ✅ XSS prevention via json.dumps() for URL escaping
- ✅ No credentials in code or logs
- ✅ Secure token storage in session state

## Support

If you encounter any issues during testing:
1. Check the OAuth Debug Info expander on the About page
2. Verify your Google Cloud Console configuration
3. Check Streamlit Cloud logs for error messages
4. Open an issue on GitHub with details

## Success Criteria

All tests pass and:
- ✅ No "missing page" errors
- ✅ Immediate redirect on sign-in
- ✅ Successful OAuth flow completion
- ✅ User can access Fieldmap and Gallery after sign-in
- ✅ Clean error handling
