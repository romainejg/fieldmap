# OAuth State Cookie Fix - Implementation Summary

## Problem Solved

The app was experiencing "Invalid OAuth state" errors after redirect from Google OAuth, especially on Streamlit Cloud. This was caused by:

1. **State not persisting across redirect**: `st.session_state` doesn't reliably survive external redirects or new tab opens
2. **State regeneration on reruns**: The state was being regenerated on each rerun before the callback
3. **Session isolation**: Redirect might return to a fresh session without the stored state

## Solution Implemented

### 1. Cookie-Backed State Storage

**File: `google_auth.py`**

- Added `streamlit-cookies-manager` dependency for persistent cookie storage
- Implemented `_get_cookie_manager()` to initialize encrypted cookies
- State is now stored in **BOTH** cookie and `st.session_state` for redundancy

```python
# Store state in both locations
self.cookies['oauth_state'] = state
self.cookies.save()
st.session_state.oauth_state = state
```

### 2. Smart State Retrieval with Fallback

**File: `google_auth.py` - `_get_expected_state()` method**

When validating state on callback:
1. First checks cookie (most reliable across redirects)
2. Falls back to `st.session_state` if cookie unavailable
3. Returns source information for debugging

```python
def _get_expected_state(self):
    # Try cookie first (more reliable across redirects)
    cookie_state = self.cookies.get('oauth_state')
    if cookie_state:
        return (cookie_state, 'cookie')
    
    # Fallback to session_state
    session_state = st.session_state.get('oauth_state')
    if session_state:
        return (session_state, 'session')
    
    return (None, 'none')
```

### 3. Prevent State Regeneration on Reruns

**File: `google_auth.py` - `get_auth_url()` method**

Added `auth_in_progress` flag to prevent regenerating the auth URL and state:

```python
# Check if auth is already in progress - reuse existing auth_url and state
if st.session_state.get('auth_in_progress', False):
    stored_auth_url = st.session_state.get('pending_auth_url')
    if stored_auth_url:
        return stored_auth_url

# ... generate new state and URL ...

# Mark auth as in progress and store the URL
st.session_state.auth_in_progress = True
st.session_state.pending_auth_url = auth_url
```

### 4. Proper Cleanup After Auth

**File: `google_auth.py` - `handle_oauth_callback()` method**

After successful authentication, clean up all OAuth-related state:

```python
# Clean up OAuth state from both cookie and session_state
if 'oauth_state' in self.cookies:
    del self.cookies['oauth_state']
    self.cookies.save()

if 'oauth_flow' in st.session_state:
    del st.session_state.oauth_flow
if 'oauth_state' in st.session_state:
    del st.session_state.oauth_state
if 'auth_in_progress' in st.session_state:
    del st.session_state.auth_in_progress
if 'pending_auth_url' in st.session_state:
    del st.session_state.pending_auth_url
```

### 5. Enhanced Debug Information

**File: `app.py` - `run()` method**

When state mismatch occurs, display comprehensive debug info:

```python
if not expected_state or expected_state != received_state:
    st.error("❌ Invalid OAuth state. Possible CSRF attack detected.")
    
    # Debug information
    st.warning("**Debug Information:**")
    col1, col2 = st.columns(2)
    with col1:
        st.text("Returned state (first 8 chars):")
        st.code(received_state[:8] if received_state else "(none)")
    with col2:
        st.text("Expected state (first 8 chars):")
        st.code(expected_state[:8] if expected_state else "(none)")
    
    st.text(f"State source: {state_source}")
    st.text(f"Cookie present: {'oauth_state' in self.google_auth.cookies}")
```

**File: `app.py` - AboutPage OAuth Debug Info**

Added additional debug fields:
- OAuth State in Cookie
- Auth In Progress flag

### 6. Same-Tab Redirect (Already Implemented)

The code already uses `window.top.location.href` which keeps the user in the same tab, increasing the likelihood that cookies and session state persist.

## Files Modified

1. **requirements.txt**: Added `streamlit-cookies-manager>=0.2.0`
2. **google_auth.py**: 
   - Added cookie manager initialization
   - Updated `get_auth_url()` to prevent state regeneration
   - Added `_get_expected_state()` method
   - Updated `handle_oauth_callback()` to clean up cookies
3. **app.py**:
   - Updated `run()` to use cookie-backed state validation
   - Enhanced state mismatch debug output
   - Updated `_cleanup_oauth_state()` to clear cookies
   - Added cookie debug info to About page

## Configuration Required

### Streamlit Cloud Secrets

Add this optional secret for cookie encryption (if not set, uses a default):

```toml
COOKIE_PASSWORD = "your-secure-random-password-here"
```

All other secrets remain the same (GOOGLE_OAUTH_CLIENT_JSON, APP_BASE_URL).

## Testing Instructions

### Manual Testing on Streamlit Cloud

1. **Deploy** the updated code to Streamlit Cloud
2. **Clear browser cookies** for the app domain (to start fresh)
3. **Navigate** to the app and go to About page
4. **Open OAuth Debug Info** expander to monitor state
5. **Click "Sign in with Google"**
   - Note the OAuth state values in debug info
6. **Complete Google OAuth flow**
7. **Return to app** and verify:
   - ✅ No "Invalid OAuth state" error
   - ✅ Successfully signed in
   - ✅ Cookie was used for state validation (check debug logs)

### Debug Checklist

If state mismatch still occurs, check:

1. **State source**: Should be "cookie" (most reliable)
2. **Cookie present**: Should show "True"
3. **Returned vs Expected state**: First 8 chars should match
4. **Auth in progress**: Should be True during auth flow

### Expected Behavior

**Before Fix:**
- State stored only in `st.session_state`
- Redirect might lose session data
- State regenerated on reruns
- Result: "Invalid OAuth state" error

**After Fix:**
- State stored in cookie (persists across redirects)
- Fallback to `st.session_state` if needed
- State not regenerated once auth starts
- Result: Successful OAuth flow

## Rollback Plan

If issues occur, revert by:
1. `git revert` this commit
2. Remove `streamlit-cookies-manager` from requirements.txt
3. Redeploy

## Benefits

1. ✅ **Reliable state persistence** across OAuth redirects
2. ✅ **Cookie-backed storage** survives session changes
3. ✅ **No state regeneration** on reruns
4. ✅ **Better debugging** with detailed mismatch info
5. ✅ **Fallback mechanism** for backward compatibility
6. ✅ **Security maintained** with state validation

## Technical Details

### Cookie Security

- Uses `EncryptedCookieManager` for secure cookie storage
- Cookies encrypted with password (from secrets or default)
- Cookie prefix: `fieldmap_`
- Cookie key: `oauth_state`

### State Flow

1. **User clicks "Sign in"**
   - Generate random state: `secrets.token_urlsafe(32)`
   - Store in cookie: `cookies['oauth_state'] = state`
   - Store in session: `st.session_state.oauth_state = state`
   - Set flag: `st.session_state.auth_in_progress = True`

2. **User redirected to Google**
   - State included in auth URL
   - Cookie persists in browser

3. **User returns from Google**
   - App receives: `?code=...&state=...`
   - Retrieve expected state from cookie (or session fallback)
   - Compare with returned state
   - If match: proceed with token exchange
   - If mismatch: show debug info and abort

4. **After successful auth**
   - Clear cookie: `del cookies['oauth_state']`
   - Clear session state
   - Reset flags

## Limitations & Notes

1. **Cookie Manager Initialization**: Requires `st.stop()` if cookies not ready - this is normal behavior
2. **Browser Compatibility**: Requires cookies enabled in browser
3. **HTTPS Required**: Cookies work best over HTTPS (Streamlit Cloud uses HTTPS)
4. **State Expiry**: States don't expire automatically - cleared after use

## Future Improvements

Potential enhancements (not implemented in this fix):
- Add state timestamp for expiration
- Implement rate limiting on auth attempts
- Add more detailed logging for production debugging
