# Manual Testing Guide - OAuth State Persistence Fix

## Overview

This guide provides step-by-step instructions for manually testing the OAuth state persistence fix in production.

## Prerequisites

- Deploy the branch `copilot/fix-auth-session-expired` to Streamlit Cloud
- Ensure Google Cloud Console has the correct redirect URI configured (e.g., `https://fieldmap.streamlit.app`)
- Ensure your Google account is added as a test user if OAuth consent screen is in Testing mode

## Test Cases

### Test Case 1: Normal Sign-In Flow

**Objective**: Verify that users can successfully sign in without "Auth session expired" errors.

**Steps**:
1. Open the deployed app URL (e.g., `https://fieldmap.streamlit.app`)
2. Navigate to the "About" page (should be the default page)
3. Click the "Sign in with Google" button
4. Verify you are redirected to Google OAuth consent screen in the **same tab**
5. Sign in with your Google account and grant permissions
6. Verify you are redirected back to the app
7. **Expected**: The URL should briefly show `?code=...&state=...&oauth_state=...`
8. **Expected**: You should see "✅ Successfully signed in!" message
9. **Expected**: You should see "Signed in as [your-email]" on the About page
10. **Expected**: Fieldmap and Gallery pages should now be accessible in the sidebar

**Success Criteria**:
- ✅ No "Auth session expired" error
- ✅ Successful sign-in message displayed
- ✅ User email shown on About page
- ✅ All pages accessible

### Test Case 2: Sign-Out and Sign-In Again

**Objective**: Verify that sign-out clears all auth state and sign-in works again.

**Steps**:
1. After successful sign-in (from Test Case 1), click "Sign Out" button on About page
2. **Expected**: "Signed out successfully" message
3. **Expected**: Only "About" page visible in sidebar
4. Click "Sign in with Google" button again
5. Complete the OAuth flow again
6. **Expected**: Successful sign-in

**Success Criteria**:
- ✅ Sign-out clears authentication
- ✅ Can sign in again without errors
- ✅ No stale state from previous session

### Test Case 3: Multiple Reruns During Auth

**Objective**: Verify that Streamlit reruns during the OAuth flow don't cause state mismatches.

**Steps**:
1. Clear browser session (or use incognito mode)
2. Open the app
3. Click "Sign in with Google" button
4. **Before completing the Google OAuth flow**, navigate away from the Google consent screen and back to the app tab
5. This may cause Streamlit to rerun
6. Navigate back to Google consent screen and complete the OAuth flow
7. **Expected**: Successful sign-in (no state mismatch error)

**Success Criteria**:
- ✅ No "Auth session expired" error even after reruns
- ✅ State is preserved across reruns

### Test Case 4: Browser Back Button

**Objective**: Verify that using browser back button doesn't break the flow.

**Steps**:
1. Sign out if already signed in
2. Click "Sign in with Google" button
3. On Google consent screen, click browser back button
4. Click "Sign in with Google" button again
5. Complete the OAuth flow
6. **Expected**: Successful sign-in

**Success Criteria**:
- ✅ Can retry sign-in after using back button
- ✅ No state conflicts

### Test Case 5: Direct URL with Code Param

**Objective**: Verify that manually constructed URLs with `code` and `state` params are rejected (security).

**Steps**:
1. Sign out if signed in
2. Manually construct a URL: `https://fieldmap.streamlit.app/?code=fake_code&state=fake_state`
3. Navigate to this URL
4. **Expected**: "Auth session expired" error (because oauth_state won't match)

**Success Criteria**:
- ✅ Invalid state is rejected
- ✅ Security check works correctly

### Test Case 6: Clean URL After Sign-In

**Objective**: Verify that query params are cleaned up after successful authentication.

**Steps**:
1. Complete a successful sign-in
2. Check the browser URL bar after sign-in completes
3. **Expected**: URL should be clean (e.g., `https://fieldmap.streamlit.app/`) with no `?code=...&state=...` params

**Success Criteria**:
- ✅ URL is clean after authentication
- ✅ No query params visible

### Test Case 7: Session Persistence

**Objective**: Verify that the token persists across page refreshes.

**Steps**:
1. Sign in successfully
2. Refresh the page (F5 or Cmd+R)
3. **Expected**: Still signed in (should show "Signed in as [email]")
4. Navigate to Fieldmap page
5. Refresh again
6. **Expected**: Still signed in

**Success Criteria**:
- ✅ Token persists across refreshes
- ✅ No need to sign in again

## Debugging

If any test fails, check the following:

### Browser Console
1. Open browser DevTools (F12)
2. Check Console tab for JavaScript errors
3. Look for redirect issues or script errors

### Streamlit Logs
1. In Streamlit Cloud, open the app logs
2. Look for error messages containing "oauth_state", "state mismatch", or "Auth session expired"
3. Check which source provided the state (query_params or session_state)

### Expected Log Messages
On successful sign-in, you should see:
```
Retrieved expected_state from query_params: [state]...
Successfully obtained OAuth token
```

### URL Inspection
1. During the OAuth flow, inspect the URL carefully
2. Before Google redirect: Should have `?oauth_state=...` 
3. After Google redirect: Should have `?code=...&state=...` (and possibly `oauth_state=...`)
4. After successful callback: Should be clean

### Google Cloud Console
Verify the redirect URI is exactly configured:
- **Production**: `https://fieldmap.streamlit.app` (no trailing slash)
- **Local**: `http://localhost:8501` (no trailing slash)

## Common Issues and Solutions

### Issue: "Auth session expired" error

**Possible Causes**:
1. `oauth_state` not in query params or session_state
2. State mismatch between expected and returned
3. Query params cleared before callback processing

**Solutions**:
1. Check logs to see which source provided the state
2. Verify `build_auth_url()` is setting `st.query_params["oauth_state"]`
3. Verify URL contains `oauth_state` param during redirect

### Issue: Redirect opens in new tab

**Solution**:
- Verify `window.top.location.href` is being used (not `window.open()`)
- Check that no `target="_blank"` is set on links

### Issue: "redirect_uri_mismatch" error from Google

**Solution**:
- Verify APP_BASE_URL in secrets matches Google Cloud Console exactly
- Check for trailing slash differences
- Ensure redirect URI is the root URL, not `/oauth2callback`

## Test Environment Variables

For local testing, set these environment variables:
```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export APP_BASE_URL="http://localhost:8501"
```

Or configure in `.streamlit/secrets.toml`:
```toml
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"
APP_BASE_URL = "http://localhost:8501"
```

## Success Checklist

After completing all test cases:

- [ ] Test Case 1: Normal sign-in works
- [ ] Test Case 2: Sign-out and re-sign-in works
- [ ] Test Case 3: Reruns don't break auth
- [ ] Test Case 4: Back button doesn't break auth
- [ ] Test Case 5: Invalid states are rejected
- [ ] Test Case 6: URL is clean after auth
- [ ] Test Case 7: Session persists across refreshes

If all test cases pass, the fix is working correctly! ✅

## Reporting Issues

If you encounter issues during testing, please provide:

1. **Test case number** that failed
2. **Browser and version** (e.g., Chrome 120, Safari 17)
3. **Error message** displayed to user
4. **Browser console logs** (if any)
5. **Streamlit app logs** (from Streamlit Cloud)
6. **URL** at the time of error (including query params)
7. **Steps to reproduce** the issue

## Next Steps

After successful manual testing:

1. Mark the "Test the complete OAuth flow manually" checkbox as complete
2. Merge the PR to main branch
3. Deploy to production
4. Monitor for any user-reported issues
5. Consider adding automated integration tests for OAuth flow
