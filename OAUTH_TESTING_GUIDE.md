# OAuth Cookie Fix - Testing Guide

## Pre-Testing Setup

### 1. Update Google Cloud Console Redirect URIs

Ensure your OAuth 2.0 Client has the correct redirect URIs:

**Required URIs:**
- Production: `https://fieldmap.streamlit.app`
- Local dev: `http://localhost:8501`

**Remove old URIs (if present):**
- `https://fieldmap.streamlit.app/oauth2callback`
- `http://localhost:8501/oauth2callback`

### 2. Optional: Set Cookie Password (Recommended for Production)

In Streamlit Cloud Secrets, add:

```toml
COOKIE_PASSWORD = "your-secure-random-password-here-at-least-32-chars"
```

Generate a secure password with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Note:** This is optional. The default password is acceptable since cookies only store random CSRF tokens, not credentials.

### 3. Deploy to Streamlit Cloud

1. Push this branch to GitHub
2. Deploy or redeploy on Streamlit Cloud
3. Wait for deployment to complete

## Testing Checklist

### Test 1: Fresh Sign-In (No Existing Session)

**Steps:**
1. Open app in **incognito/private browser window** (ensures fresh start)
2. Navigate to About page
3. Open "🔧 OAuth Debug Info" expander
4. Note the current state values (should show "(not set)")
5. Click "Sign in with Google" button
6. **Observe:** Should redirect immediately (no delay)
7. Complete Google OAuth consent flow
8. **Expected Result:**
   - ✅ Redirect back to app
   - ✅ No "Invalid OAuth state" error
   - ✅ "Successfully signed in!" message
   - ✅ Email displayed on About page
   - ✅ Fieldmap and Gallery pages accessible

**If state mismatch error appears:**
- Check the debug information displayed
- Note: "State source" (should be "cookie")
- Note: "Cookie present" (should be "True")
- Note: Returned vs Expected state (first 8 chars should match)
- Take screenshot for debugging

### Test 2: Verify Cookie Storage

**Steps:**
1. Before clicking "Sign in with Google"
2. Open browser developer tools (F12)
3. Go to Application/Storage > Cookies
4. Look for cookies with prefix `fieldmap_`
5. Click "Sign in with Google"
6. **Check:** A cookie named `fieldmap_oauth_state` should appear
7. Complete OAuth flow
8. **Check:** Cookie should be deleted after successful sign-in

**Expected Cookie Behavior:**
- ✅ Cookie created when clicking "Sign in with Google"
- ✅ Cookie persists during redirect to/from Google
- ✅ Cookie deleted after successful authentication

### Test 3: State Persistence Across Redirect

**Steps:**
1. Sign out if already signed in
2. Open "🔧 OAuth Debug Info" expander
3. Click "Sign in with Google"
4. **Before** completing Google consent:
   - Note the "OAuth State in Session" value
   - Note the "OAuth State in Cookie" value
   - These should match
5. Complete Google OAuth
6. **Expected Result:**
   - ✅ State from cookie matches state from Google callback
   - ✅ No state mismatch error

### Test 4: No State Regeneration on Reruns

**Steps:**
1. Sign out if already signed in
2. Click "Sign in with Google"
3. **Instead of following the redirect:** 
   - Scroll down or interact with the page
   - This triggers a Streamlit rerun
4. Open "🔧 OAuth Debug Info"
5. Check "Auth In Progress" value
6. Check "OAuth State in Session" and "OAuth State in Cookie"
7. **Expected Result:**
   - ✅ "Auth In Progress" shows "True"
   - ✅ State values remain unchanged
   - ✅ Same state persists across reruns

### Test 5: Debug Information Display

**When state mismatch occurs (if ever):**

The app should display:
```
❌ Invalid OAuth state. Possible CSRF attack detected.

⚠️ Debug Information:
Returned state (first 8 chars):    Expected state (first 8 chars):
abcd1234                           efgh5678

State source: cookie
Cookie present: True

ℹ️ Please try signing in again.
```

**Verify:**
- ✅ Debug info is clear and helpful
- ✅ State source indicates "cookie" (most reliable)
- ✅ Cookie presence is shown
- ✅ State comparison helps identify mismatch

### Test 6: Sign Out and Sign In Again

**Steps:**
1. After successful sign-in
2. Click "Sign Out"
3. **Expected Result:**
   - ✅ "Signed out successfully" message
   - ✅ Redirected to About page
   - ✅ OAuth state cleared from session
4. Click "Sign in with Google" again
5. Complete OAuth flow
6. **Expected Result:**
   - ✅ New state generated
   - ✅ Sign-in succeeds again
   - ✅ No old state conflicts

### Test 7: Browser with Cookies Disabled

**Steps:**
1. Disable cookies in browser settings
2. Try to sign in
3. **Expected Result:**
   - ⚠️ Warning: "Unable to store OAuth state in cookie"
   - ✅ Falls back to session_state only
   - ✅ Auth may work or fail depending on browser behavior
   - ✅ Clear error message if it fails

### Test 8: Multiple Browser Tabs

**Steps:**
1. Open app in Tab 1
2. Start sign-in process in Tab 1
3. Open app in Tab 2 (same browser)
4. **Do not** start sign-in in Tab 2
5. Complete OAuth in Tab 1
6. **Expected Result:**
   - ✅ Tab 1: Sign-in succeeds
   - ✅ Tab 2: Shows signed-in state after refresh
   - ✅ No state conflicts between tabs

## Common Issues and Solutions

### Issue: "Invalid OAuth state" Error

**Diagnosis:**
- Check "State source" in debug info
- Check "Cookie present" value

**Solutions:**
1. If "State source" is "none":
   - Cookie and session state both lost
   - Ensure cookies are enabled
   - Check browser privacy settings

2. If "State source" is "session":
   - Cookie not available (blocked or failed)
   - Auth might still work if session persists
   - Consider allowing cookies for the domain

3. If "Cookie present" is "False":
   - Cookies blocked by browser
   - Check browser cookie settings
   - Check for ad blockers interfering

### Issue: Cookie Not Appearing in Browser Dev Tools

**Diagnosis:**
- Check browser console for errors
- Verify cookies are enabled
- Check cookie domain/path

**Solutions:**
1. Ensure HTTPS is used (Streamlit Cloud uses HTTPS)
2. Check browser privacy/security settings
3. Disable browser extensions temporarily
4. Try different browser

### Issue: State Regenerates on Reruns

**Diagnosis:**
- Check "Auth In Progress" in debug info

**Expected:** Should be "True" after clicking "Sign in with Google"

**Solutions:**
1. If "False" when it should be "True":
   - State management logic not working
   - Check for errors in browser console
   - Report this as a bug

### Issue: Redirect Delays or Doesn't Happen

**Diagnosis:**
- JavaScript redirect might be blocked

**Solutions:**
1. Use the fallback "Continue to Google" button
2. Check browser console for errors
3. Disable pop-up blockers
4. Try different browser

## Success Criteria

**All tests passed if:**
- ✅ Sign-in completes without "Invalid OAuth state" error
- ✅ State stored in cookie (visible in browser dev tools)
- ✅ Cookie persists across redirect to/from Google
- ✅ State not regenerated on reruns
- ✅ Debug info shows "State source: cookie"
- ✅ Sign out and sign in again works
- ✅ Graceful fallback when cookies disabled

## Reporting Issues

If tests fail, please provide:

1. **Browser and Version:** (e.g., Chrome 120, Firefox 121)
2. **Cookie Settings:** Enabled/Disabled
3. **Error Message:** Full text of error
4. **Debug Information:** Screenshot of OAuth Debug Info
5. **Console Errors:** Browser console messages (F12 > Console)
6. **Cookie Storage:** Screenshot of cookies in browser dev tools
7. **Steps to Reproduce:** Detailed steps leading to the issue

## Next Steps After Testing

### If All Tests Pass:
1. ✅ Merge this PR to main branch
2. ✅ Deploy to production
3. ✅ Monitor for any OAuth errors in production
4. ✅ Close related issues

### If Tests Fail:
1. ❌ Document the failure (screenshots, error messages)
2. ❌ Check browser console for errors
3. ❌ Review debug information displayed
4. ❌ Report issues with details above
5. ❌ May need to adjust implementation

## Additional Testing (Optional)

### Performance Testing
- Measure time from clicking "Sign in" to redirect
- Should be < 1 second

### Security Testing
- Verify state is cryptographically random
- Verify state is validated on callback
- Verify old states are rejected

### Cross-Browser Testing
- Chrome/Edge (Chromium)
- Firefox
- Safari (if available)
- Mobile browsers (iOS Safari, Android Chrome)

## Notes

- **Cookie Manager Initialization:** First load may take slightly longer as cookie manager initializes
- **HTTPS Requirement:** Cookies work best over HTTPS (Streamlit Cloud uses HTTPS by default)
- **State Expiration:** States don't expire automatically but are cleared after use
- **Multiple Sessions:** Each OAuth flow gets a unique state token

## Questions?

If you encounter unexpected behavior not covered in this guide, please:
1. Check browser console for errors
2. Review OAUTH_COOKIE_FIX.md for implementation details
3. Open an issue with details from "Reporting Issues" section above
