# OAuth Troubleshooting Guide

## Problem: "Auth session expired. Please click Sign in again."

This guide helps diagnose and fix the OAuth authentication error where users see "Auth session expired" immediately after completing Google login.

## Quick Diagnosis Steps

### 1. Check Streamlit Cloud Logs

**Where:** Streamlit Cloud Dashboard → Your App → Manage App → Logs

**What to look for:**
```
CRITICAL: No oauth_state found in session_state
```

This indicates the OAuth state was lost during the redirect from Google back to your app.

### 2. Check Session State Persistence

The OAuth flow depends on `st.session_state` persisting across the redirect to Google and back. If session state is not persisting, you'll see:

**In logs:**
```
Session state keys: []
oauth_state NOT in session_state
```

**Expected behavior:**
```
Session state keys: ['oauth_state', 'auth_in_progress', 'pending_auth_url', ...]
oauth_state in session_state: FU3lHpVBJ9...
```

### 3. Use the OAuth Debug Panel

1. Go to the About page (before signing in)
2. Expand the "🔧 OAuth Debug Info" panel
3. Check:
   - ✓ OAuth state in session: Should show a value when auth is in progress
   - ✓ auth_in_progress: Should be True during OAuth flow
   - ✓ All session state keys: Should include oauth-related keys

### 4. Run the Diagnostic Tool

```bash
streamlit run oauth_diagnostics.py
```

This shows:
- Query parameters (code, state from Google)
- Session state (oauth_state, auth_in_progress)
- OAuth configuration status
- State verification test

## Common Causes and Solutions

### Cause 1: Session State Not Persisting Across Redirects

**Symptoms:**
- oauth_state is set when clicking "Sign in with Google"
- oauth_state is missing when returning from Google
- Session state keys list is empty on callback

**Root Cause:**
Streamlit session state relies on browser cookies and WebSocket connections. If these are interrupted during the OAuth redirect, session state is lost.

**Solutions:**

#### A. Update Streamlit Version
```bash
# Ensure you're using Streamlit >= 1.28.0
pip install "streamlit>=1.28.0"
```

Streamlit 1.28+ has improved session state persistence.

#### B. Check Browser Settings
- Ensure cookies are enabled
- Disable "Block third-party cookies" for your app domain
- Try in a normal browser window (not incognito/private mode)

#### C. Verify Same-Tab Redirect
The app should redirect in the same tab, not open a new window.

Check in `app.py`:
```python
# ✓ Correct (same tab)
window.top.location.href = {safe_url};

# ✗ Wrong (new window/tab)
window.open({safe_url});
```

### Cause 2: Multiple Reruns Overwriting State

**Symptoms:**
- State is generated multiple times
- State mismatch errors in logs
- Different state values in logs

**Root Cause:**
Streamlit reruns the app frequently. If `build_auth_url()` runs multiple times, it generates a new state each time, overwriting the original.

**Solution:**
Use the `auth_in_progress` flag to prevent state regeneration:

```python
if st.session_state.get("auth_in_progress", False):
    # Return existing URL, don't generate new state
    return st.session_state.get("pending_auth_url")
```

This is already implemented in the current code.

### Cause 3: Query Params Cleared Too Early

**Symptoms:**
- Logs show query params present initially
- Then query params are empty
- oauth_state is lost

**Root Cause:**
If `st.query_params.clear()` is called before the callback is processed, the state is lost.

**Solution:**
Only clear query params AFTER successful authentication:

```python
if google_oauth.handle_callback():
    # Success - now it's safe to clear
    st.query_params.clear()
```

### Cause 4: Redirect URI Mismatch

**Symptoms:**
- Google shows "redirect_uri_mismatch" error
- Or OAuth never completes

**Root Cause:**
The redirect URI configured in Google Cloud Console doesn't match the one your app is using.

**Solution:**

1. Check your APP_BASE_URL:
```bash
# Should be EXACT app URL (no trailing slash)
APP_BASE_URL=https://fieldmap.streamlit.app
```

2. Check Google Cloud Console:
- Go to APIs & Services → Credentials
- Edit OAuth 2.0 Client
- Authorized redirect URIs must include EXACTLY:
  - For production: `https://fieldmap.streamlit.app`
  - For local dev: `http://localhost:8501`

3. No path component (e.g., NOT `/oauth2callback`)

## Detailed Log Analysis

### Successful OAuth Flow Logs

```
[timestamp] - __main__ - INFO - User clicked 'Sign in with Google' button
[timestamp] - google_oauth - INFO - build_auth_url() - Generating OAuth authorization URL
[timestamp] - google_oauth - INFO - Generated state: abc123def456...
[timestamp] - google_oauth - INFO - Storing state in session_state['oauth_state']
[timestamp] - google_oauth - INFO - Setting auth_in_progress=True
[timestamp] - google_oauth - INFO - Generated auth URL: https://accounts.google.com/o/oauth2/v2/auth...

# User redirects to Google, completes OAuth

[timestamp] - __main__ - INFO - OAuth callback detected - processing authentication
[timestamp] - __main__ - INFO - code param: 4/0AfJohXkL...
[timestamp] - __main__ - INFO - state param: abc123def456...
[timestamp] - google_oauth - INFO - handle_callback() - Processing OAuth callback
[timestamp] - google_oauth - INFO - Retrieved expected_state from session_state: abc123def456...
[timestamp] - google_oauth - INFO - ✓ State verification successful - states match!
[timestamp] - google_oauth - INFO - ✓ Successfully obtained access token from Google
[timestamp] - google_oauth - INFO - OAuth authentication completed successfully!
[timestamp] - __main__ - INFO - OAuth callback successful - setting session state
[timestamp] - __main__ - INFO - User email: user@example.com
```

### Failed OAuth Flow Logs (State Lost)

```
[timestamp] - __main__ - INFO - User clicked 'Sign in with Google' button
[timestamp] - google_oauth - INFO - Generated state: abc123def456...
[timestamp] - google_oauth - INFO - Storing state in session_state['oauth_state']

# User redirects to Google, completes OAuth

[timestamp] - __main__ - INFO - OAuth callback detected - processing authentication
[timestamp] - __main__ - WARNING - oauth_state NOT in session_state  # ← PROBLEM!
[timestamp] - __main__ - INFO - Session state keys: []                # ← Session state was cleared
[timestamp] - google_oauth - ERROR - CRITICAL: No oauth_state found in session_state
[timestamp] - google_oauth - ERROR - All session_state keys: []
[timestamp] - google_oauth - ERROR - auth_in_progress not set - this may indicate session was completely reset
```

**Diagnosis:** Session state was completely lost between generating the auth URL and receiving the callback.

### Failed OAuth Flow Logs (State Mismatch)

```
[timestamp] - google_oauth - INFO - Retrieved expected_state from session_state: abc123def456...
[timestamp] - google_oauth - INFO - State from Google: xyz789ghi012...
[timestamp] - google_oauth - ERROR - CRITICAL: State mismatch detected
[timestamp] - google_oauth - ERROR - Expected: abc123def456...
[timestamp] - google_oauth - ERROR - Received: xyz789ghi012...
```

**Diagnosis:** A new state was generated after the user clicked "Sign in with Google", overwriting the original state. Check for multiple reruns.

## Testing OAuth Flow

### Manual Test Procedure

1. **Start Fresh:**
   ```python
   # Clear all state
   st.session_state.clear()
   st.query_params.clear()
   ```

2. **Click "Sign in with Google"**
   - Check logs: "User clicked 'Sign in with Google' button"
   - Check logs: "Generated state: ..."
   - Check logs: "Storing state in session_state['oauth_state']"

3. **Redirect to Google**
   - Should happen automatically (same tab)
   - Complete Google OAuth

4. **Return to App**
   - Check URL: Should have `?code=...&state=...`
   - Check logs: "OAuth callback detected"
   - Check logs: "Retrieved expected_state from session_state"
   - Check logs: "✓ State verification successful"

5. **Success**
   - Check logs: "OAuth authentication completed successfully!"
   - Should see "Signed in as [email]"

### Automated Test

Run the unit tests:
```bash
python3 test_oauth.py
```

Expected output:
```
✅ All tests passed!
```

## Advanced Debugging

### Enable Verbose Logging

Already enabled in the current code. Logs are written to stdout and visible in Streamlit Cloud logs.

### Check Session State Manually

Add this to your app temporarily:
```python
st.sidebar.write("Debug Session State:")
st.sidebar.json({k: str(v)[:50] for k, v in st.session_state.items()})
```

### Monitor Network Traffic

1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "Sign in with Google"
4. Watch for:
   - Redirect to `accounts.google.com`
   - Redirect back with `?code=...&state=...`
   - WebSocket connection maintained

### Check for Session Timeout

If users are taking a very long time at the Google OAuth screen, the Streamlit session might timeout.

**Solution:** Set a longer session timeout in `.streamlit/config.toml`:
```toml
[server]
sessionTimeout = 600  # 10 minutes (default is 300)
```

## Still Having Issues?

1. **Collect logs:**
   - Streamlit Cloud logs (full OAuth flow)
   - Browser console logs (F12 → Console)
   - Network tab (F12 → Network)

2. **Check the OAuth Debug Panel:**
   - Expand "🔧 OAuth Debug Info" on About page
   - Take a screenshot

3. **Run oauth_diagnostics.py:**
   ```bash
   streamlit run oauth_diagnostics.py
   ```
   - Take a screenshot of all sections

4. **Verify environment:**
   - Streamlit version: `streamlit --version` (should be >= 1.28.0)
   - Python version: `python --version` (should be >= 3.8)
   - Browser: Try Chrome/Firefox (latest version)

5. **Test locally:**
   ```bash
   # Set up local secrets
   export GOOGLE_CLIENT_ID="your_client_id"
   export GOOGLE_CLIENT_SECRET="your_secret"
   export APP_BASE_URL="http://localhost:8501"
   
   # Run app
   streamlit run app.py
   ```
   
   Add `http://localhost:8501` to Google Cloud Console Authorized redirect URIs.

## Configuration Checklist

- [ ] Streamlit version >= 1.28.0
- [ ] GOOGLE_CLIENT_ID set in secrets
- [ ] GOOGLE_CLIENT_SECRET set in secrets
- [ ] APP_BASE_URL set (exact URL, no trailing slash)
- [ ] Redirect URI in Google Console matches APP_BASE_URL exactly
- [ ] OAuth consent screen configured
- [ ] Test users added (if in Testing mode)
- [ ] Cookies enabled in browser
- [ ] Not using incognito/private mode

## Code References

**OAuth state generation:** `google_oauth.py` → `build_auth_url()`
**OAuth callback handling:** `google_oauth.py` → `handle_callback()`
**App entry point:** `app.py` → `App.run()`
**Sign-in button:** `app.py` → `AboutPage.render()`

## Related Documentation

- `OAUTH_FIX_DECEMBER_2024.md` - Previous OAuth fix documentation
- `OAUTH_STATE_PERSISTENCE_FIX.md` - State persistence implementation
- `TESTING_OAUTH_FIX.md` - Testing guidelines
- `oauth_diagnostics.py` - Diagnostic tool
