# OAuth Fix - Manual Testing Guide

## Quick Test Checklist

After deploying this fix to Streamlit Cloud, follow these steps to verify both issues are resolved:

### Test 1: Single-Click Sign-In ✅

**What to test:** The "Sign in with Google" button should work on the first click

**Steps:**
1. Navigate to your Streamlit app
2. Go to the About page (or wherever sign-in button appears)
3. Click **"Sign in with Google"** button **ONCE**
4. **Expected:** Browser immediately redirects to Google OAuth consent screen
5. **NOT Expected:** Having to click "Continue to Google" button or clicking twice

**Success Criteria:**
- ✅ Single click on "Sign in with Google" redirects to Google immediately
- ✅ No "Continue to Google" fallback button needed
- ✅ No need to click twice

### Test 2: No "Auth Session Expired" Error ✅

**What to test:** OAuth flow completes without errors

**Steps:**
1. Click "Sign in with Google" (should redirect immediately)
2. On Google consent screen, select your Google account
3. Grant permissions if prompted
4. **Expected:** Redirect back to app with successful sign-in
5. **Expected:** See "✅ Successfully signed in!" message
6. **Expected:** See your email displayed in the UI
7. **NOT Expected:** "❌ Auth session expired. Please click Sign in again." error

**Success Criteria:**
- ✅ Successfully redirected back to app
- ✅ No "Auth session expired" error
- ✅ User email displayed correctly
- ✅ Can access Fieldmap and Gallery pages

### Test 3: Multiple Reruns (Edge Case)

**What to test:** OAuth flow handles Streamlit reruns gracefully

**Steps:**
1. Click "Sign in with Google"
2. While on Google consent screen, note that app may rerun in background
3. Complete OAuth flow normally
4. **Expected:** Still works correctly despite any reruns

**Success Criteria:**
- ✅ OAuth completes successfully even with background reruns
- ✅ State is not overwritten during auth flow

## Troubleshooting

### If "Auth session expired" still appears:

This likely means `session_state` is not persisting across the OAuth redirect in your environment.

**Possible causes:**
- User has cookies disabled
- User is in incognito/private browsing mode
- Older Streamlit version (< 1.28.0)
- Specific Streamlit Cloud configuration issue

**Solutions:**
1. Check Streamlit version: `streamlit --version` (should be >= 1.28.0)
2. Ask user to enable cookies and try regular browsing mode
3. If issue persists, implement cookie-based state storage (see OAUTH_FIX_DECEMBER_2024.md)

### If double-click still required:

This would be very unusual after the fix. If it happens:
- Clear browser cache and try again
- Check browser console for JavaScript errors
- Verify the fix was actually deployed (check git commit hash)

## Expected Browser Behavior

### What you should see:

1. **Before clicking button:**
   - App URL: `https://your-app.streamlit.app/`
   - Page shows "Sign in with Google" button

2. **Immediately after clicking:**
   - Browser redirects to: `https://accounts.google.com/o/oauth2/v2/auth?client_id=...&state=...`
   - See Google OAuth consent screen

3. **After granting permissions:**
   - Browser redirects to: `https://your-app.streamlit.app/?code=...&state=...`
   - See "Completing sign-in..." spinner briefly
   - See "✅ Successfully signed in!" message
   - URL changes to: `https://your-app.streamlit.app/` (query params cleared)
   - User email displayed

### What you should NOT see:

- ❌ "Continue to Google" button (should redirect immediately)
- ❌ "Auth session expired" error
- ❌ Need to click button multiple times
- ❌ Stuck on loading screen

## Logging & Debugging

If you need to debug issues, check Streamlit Cloud logs for:

**Successful flow logs:**
```
INFO - Generated auth URL with state: abcd1234...
INFO - Retrieved expected_state from session_state: abcd1234...
INFO - Successfully obtained OAuth token
```

**Error flow logs:**
```
ERROR - No oauth_state found in session_state  # <- Session state lost
ERROR - State mismatch: expected abcd1234..., got efgh5678...  # <- State was overwritten
```

## Success Confirmation

Once both tests pass, you can confirm the fix is working by checking:
- [x] Users can sign in with a single click
- [x] No "Auth session expired" errors appear
- [x] OAuth flow completes smoothly
- [x] Users can access protected features (Fieldmap, Gallery)

## Next Steps

If testing reveals any remaining issues:
1. Document the specific error or behavior
2. Check Streamlit Cloud logs for error details
3. Review `OAUTH_FIX_DECEMBER_2024.md` for potential enhancements (cookie-based storage, etc.)
4. Report findings for further investigation

---

**Note:** This fix has been tested with unit tests and passed code review and security scans. The implementation follows Streamlit best practices for OAuth flows in version 1.28+.
