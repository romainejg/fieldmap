# OAuth State Persistence Fix - Implementation Summary

## Problem Statement

The app was experiencing "Auth session expired" errors after users returned from Google OAuth:

1. **Lost OAuth State**: When clicking "Sign in with Google", the app generates an OAuth state and stores it in `st.session_state`. However, Streamlit session state doesn't persist across redirects, so when the user returns from Google, the state is lost.
2. **State Mismatch**: Without the original state, the callback handler cannot verify the returned state from Google, causing a security check failure and displaying "Auth session expired".
3. **State Overwrite on Reruns**: On Streamlit reruns (which happen frequently), the auth URL generation code would run again, generating a new state and overwriting the original one.

## Solution Implemented

We implemented a comprehensive fix that addresses all aspects of OAuth state persistence and management:

### 1. Persist oauth_state in Query Parameters

**File: `google_oauth.py` - `build_auth_url()` function**

```python
# Store state in session_state for verification
st.session_state["oauth_state"] = state

# ALSO persist oauth_state in query params before redirect
# This ensures state survives the redirect roundtrip
st.query_params["oauth_state"] = state
```

**Why this works:**
- Query parameters are included in the browser URL
- When the user is redirected to Google, the URL contains `?oauth_state=...`
- When Google redirects back, the `oauth_state` param is still in the URL
- This provides a reliable fallback even if session state is lost

### 2. Retrieve State from Query Params OR Session State

**File: `google_oauth.py` - `handle_callback()` function**

```python
# Verify state - try query params first (more reliable), then session_state
expected_state = query_params.get("oauth_state") or st.session_state.get("oauth_state")

if not expected_state:
    st.error("❌ Auth session expired. Please click Sign in again.")
    logger.error("No oauth_state in query params or session_state")
    return False
```

**Why this works:**
- Tries query params first (most reliable across redirects)
- Falls back to session state if available
- Only shows error if state is not found in either location
- This ensures state verification succeeds even after redirect

### 3. Prevent State Overwrite on Reruns

**File: `google_oauth.py` - `build_auth_url()` function**

```python
# Check if auth is already in progress to avoid overwriting state
if st.session_state.get("auth_in_progress", False):
    logger.warning("Auth already in progress, not generating new state")
    # Return existing auth_url if available
    existing_url = st.session_state.get("pending_auth_url")
    if existing_url:
        return existing_url
    # If no existing URL but auth in progress, clear the flag and continue
    st.session_state["auth_in_progress"] = False
```

**Why this works:**
- Sets `auth_in_progress` flag when auth URL is first generated
- On subsequent reruns (which happen during the OAuth flow), the flag prevents generating a new state
- Returns the existing auth URL instead
- This prevents state mismatches caused by multiple state generations

### 4. Clear Auth Flags After Success or Failure

**File: `google_oauth.py` - `handle_callback()` function**

```python
# Clear auth_in_progress flag after successful authentication
if "auth_in_progress" in st.session_state:
    del st.session_state["auth_in_progress"]
if "pending_auth_url" in st.session_state:
    del st.session_state["pending_auth_url"]
```

**File: `app.py` - `App.run()` method**

```python
# Clean up any OAuth state on failure
if "oauth_state" in st.session_state:
    del st.session_state["oauth_state"]
if "auth_in_progress" in st.session_state:
    del st.session_state["auth_in_progress"]
if "pending_auth_url" in st.session_state:
    del st.session_state["pending_auth_url"]
```

**Why this works:**
- Clears auth flags after successful token exchange
- Clears flags on failure to allow retry
- Prevents stale flags from interfering with future auth attempts

### 5. Clear ALL Query Params After Success

**File: `app.py` - `App.run()` method**

```python
if google_oauth.handle_callback():
    st.session_state.google_authed = True
    st.session_state.google_user_email = google_oauth.get_user_email()
    # Clear ALL query params (including oauth_state, code, state)
    st.query_params.clear()
    st.success("✅ Successfully signed in!")
    st.rerun()
```

**Why this works:**
- Removes oauth_state, code, and state from URL after successful auth
- Prevents query params from interfering with app navigation
- Keeps the URL clean for the user

### 6. Enhanced Sign Out

**File: `google_oauth.py` - `sign_out()` function**

```python
def sign_out():
    """
    Sign out by removing stored token and clearing auth state.
    """
    if "google_token" in st.session_state:
        del st.session_state["google_token"]
    if "oauth_state" in st.session_state:
        del st.session_state["oauth_state"]
    if "auth_in_progress" in st.session_state:
        del st.session_state["auth_in_progress"]
    if "pending_auth_url" in st.session_state:
        del st.session_state["pending_auth_url"]
    logger.info("User signed out")
```

**Why this works:**
- Clears all auth-related state on sign out
- Prevents stale state from interfering with next sign in

## Other Verification (Already Implemented)

### Same-Tab Redirect
**File: `app.py` - `AboutPage.render()` method**

```python
components.html(
    f"""
    <script>
        window.top.location.href = {safe_url};
    </script>
    """,
    height=0
)
```

✅ **Already using `window.top.location.href`** - ensures same-tab redirect, not `window.open()` or `target="_blank"`.

### Exact Redirect URI Match
**File: `google_oauth.py` - `get_app_base_url()` function**

```python
if app_base_url:
    return app_base_url.rstrip('/')
```

✅ **Already strips trailing slashes** - ensures redirect URI matches exactly what's configured in Google Cloud Console.

## Testing

### Automated Tests

Added comprehensive tests in `test_oauth.py`:

1. **Test state persistence in query params**: Verifies `build_auth_url()` stores state in both `session_state` and `query_params`
2. **Test auth_in_progress flag**: Verifies the flag prevents state overwrite on reruns
3. **Test callback with query params**: Verifies `handle_callback()` retrieves state from query params
4. **Test flag cleanup**: Verifies auth flags are cleared after success and sign out

All tests pass successfully! ✅

### Manual Testing Checklist

To fully verify the fix works in production:

- [ ] Deploy to Streamlit Cloud
- [ ] Click "Sign in with Google" button
- [ ] Verify redirect to Google OAuth consent screen (same tab)
- [ ] Complete Google OAuth flow (sign in and consent)
- [ ] Verify redirect back to app (URL should contain `?code=...&state=...&oauth_state=...`)
- [ ] Verify automatic sign-in completion (no "Auth session expired" error)
- [ ] Verify "Signed in as [email]" message appears
- [ ] Verify Fieldmap and Gallery pages are accessible
- [ ] Test sign-out and sign-in again
- [ ] Verify multiple reruns during auth flow don't cause issues

## Benefits

1. **No More "Auth Session Expired" Errors**: State persists across redirects via query params
2. **Reliable State Verification**: Fallback to session state if query params are somehow lost
3. **Prevents State Overwrites**: Auth in progress flag prevents reruns from generating new states
4. **Better User Experience**: Users can successfully sign in without errors
5. **Enhanced Security**: State verification still enforced for CSRF protection
6. **Clean URL After Auth**: All query params cleared after successful authentication

## Configuration Requirements

No configuration changes required! The fix works with existing setup:

- **Google Cloud Console**: Continue using the same redirect URI (e.g., `https://fieldmap.streamlit.app`)
- **Streamlit Secrets**: No changes to `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, or `APP_BASE_URL`

## Technical Details

### OAuth Flow Sequence

1. **User clicks "Sign in with Google"**:
   - `build_auth_url()` generates state
   - Stores state in `session_state["oauth_state"]`
   - Stores state in `query_params["oauth_state"]`
   - Sets `session_state["auth_in_progress"] = True`
   - Stores `session_state["pending_auth_url"]`
   - Returns auth URL

2. **User is redirected to Google** (same tab):
   - URL includes `?oauth_state=...` (persisted from query params)
   - User sees Google OAuth consent screen

3. **User returns from Google**:
   - Google redirects to: `https://app.url/?code=...&state=...`
   - Importantly, `oauth_state=...` is still in the URL from step 1
   - `handle_callback()` is triggered

4. **Callback processing**:
   - Retrieves `expected_state` from `query_params["oauth_state"]` (reliable!) or `session_state["oauth_state"]` (fallback)
   - Retrieves `returned_state` from `query_params["state"]` (from Google)
   - Compares: `expected_state == returned_state`
   - If match, exchanges code for token
   - Clears all query params and auth flags
   - Redirects to main app

### Why Query Params Work

Query parameters in Streamlit are **part of the browser URL** and persist across:
- Page navigation
- External redirects (like OAuth)
- Browser back/forward
- Page refreshes

This makes them ideal for persisting OAuth state across the redirect roundtrip to Google and back.

## Rollback Plan

If issues arise, you can revert by:
1. Reverting the commit that introduced these changes
2. Redeploying the app

However, this would bring back the "Auth session expired" errors.
