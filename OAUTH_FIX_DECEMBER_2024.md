# OAuth Authentication Fix - December 2024

## Issues Reported

User reported two OAuth authentication issues:

1. **"Auth session expired" error after logging in to Google** - Users complete the Google OAuth flow but receive an error when returning to the app
2. **"Continue to Google" button must be clicked twice** - The first click on "Sign in with Google" doesn't work; users must click a second time

## Root Cause Analysis

### Issue #2: Double-Click Problem
**Cause:** In `google_oauth.py`, the `build_auth_url()` function set `st.query_params["oauth_state"] = state` (line 154). In Streamlit, modifying `st.query_params` triggers an immediate page rerun. This rerun occurred BEFORE the JavaScript redirect could execute, causing:
- Button click state to be lost
- JavaScript redirect code to not execute
- User having to click button again

**Fix:** Removed the line `st.query_params["oauth_state"] = state` from `build_auth_url()`. The state is now only stored in `session_state`.

### Issue #1: Auth Session Expired

**Potential Causes:**
1. **Session state not persisting across redirects** - In some scenarios, Streamlit's `session_state` may not persist when navigating away to Google OAuth and back
2. **Browser/cookie issues** - Users with cookies disabled or in incognito mode may lose session state
3. **Streamlit version issues** - Older Streamlit versions had less reliable session state persistence

**Current Fix:** Removed the problematic query param line. Session state should persist in modern Streamlit (v1.28+).

**Remaining Risk:** If session_state doesn't reliably persist across OAuth redirects in the deployment environment, users may still see "Auth session expired" errors.

## Changes Made

### google_oauth.py
1. Removed `st.query_params["oauth_state"] = state` from `build_auth_url()` 
2. Updated docstrings to reflect reliance on session_state only
3. Simplified `handle_callback()` to only check session_state for oauth_state

### test_oauth.py
1. Removed test assertions checking for oauth_state in query_params
2. Updated test to verify state is stored in session_state
3. Renamed test from `test_callback_with_query_params` to `test_callback_with_session_state`

## Testing

### Unit Tests
All tests in `test_oauth.py` pass successfully:
- ✅ Configuration functions work correctly
- ✅ Auth URL generation stores state in session_state
- ✅ Auth in-progress flag prevents state overwrite
- ✅ Callback handles authentication with session_state
- ✅ Sign out clears all auth state

### Manual Testing Required

The following should be tested in the actual Streamlit Cloud deployment:

1. **Single-Click Sign-In Test:**
   - Click "Sign in with Google" button once
   - Verify automatic redirect to Google (no need to click "Continue to Google")
   - Complete Google OAuth flow
   - Verify successful return to app

2. **No Auth Expired Error Test:**
   - Click "Sign in with Google"
   - Complete Google OAuth flow
   - Verify NO "Auth session expired" error appears
   - Verify successful sign-in with email displayed

3. **Session State Persistence Test:**
   - Click "Sign in with Google"  
   - Note the state value in browser devtools/network tab
   - Complete OAuth flow
   - Verify the same state is validated successfully

## Potential Future Enhancements

If the "Auth session expired" error persists after this fix, consider implementing:

### Option 1: Cookie-Based State Storage
Store oauth_state in a browser cookie before redirect:
- Pros: Reliable across redirects, works even if session_state is lost
- Cons: Requires additional library (e.g., `streamlit-cookies-manager`) or custom JavaScript

### Option 2: Server-Side State Storage  
Store oauth_state in a database or cache (Redis, etc.):
- Pros: Most reliable, survives all browser scenarios
- Cons: Requires additional infrastructure, complexity

### Option 3: Session Storage via JavaScript
Use browser sessionStorage as backup:
- Pros: Tab-specific, reliable
- Cons: Requires bidirectional JavaScript/Python communication (complex in Streamlit)

## Recommendations

1. **Deploy and monitor** - Deploy this fix to Streamlit Cloud and monitor for "Auth session expired" errors
2. **Check Streamlit version** - Ensure using Streamlit >= 1.28.0 for reliable session_state
3. **Document for users** - If issues persist, add troubleshooting guidance about enabling cookies
4. **Consider fallback** - If session_state proves unreliable, implement Cookie-Based State Storage as a robust fallback

## Technical Details

### OAuth Flow After Fix

1. User clicks "Sign in with Google"
2. `build_auth_url()` generates state and stores in `session_state["oauth_state"]`
3. JavaScript immediately redirects to Google (no rerun interference)
4. User completes Google OAuth consent
5. Google redirects back to app with `?code=...&state=...`
6. `handle_callback()` retrieves `expected_state` from `session_state["oauth_state"]`
7. State verification: `expected_state == returned_state`
8. If match, token exchange completes successfully

### Key Assumptions

- **Streamlit session_state persists across external redirects** - This is true in Streamlit v1.28+ when using session cookies
- **User has cookies enabled** - Required for Streamlit session tracking
- **Single-tab usage** - Session state is tied to the browser tab's WebSocket connection

## Rollback Plan

If issues arise, revert to the previous implementation (with query params):
```bash
git revert a6558c5
```

However, this would bring back the double-click issue.
