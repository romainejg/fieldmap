# OAuth Debugging Quick Reference

## How to View Logs

### Streamlit Cloud
1. Go to Streamlit Cloud Dashboard
2. Click on your app
3. Click "Manage app"
4. Click "Logs" tab
5. Watch logs in real-time or search for specific messages

### Local Development
Logs are printed to the terminal where you run `streamlit run app.py`

## Key Log Messages to Look For

### ✅ Successful OAuth Flow

```
INFO - User clicked 'Sign in with Google' button
INFO - build_auth_url() - Generating OAuth authorization URL
INFO - Generated state: abc123def456...
INFO - Storing state in session_state['oauth_state']
INFO - Setting auth_in_progress=True
```

Then after returning from Google:

```
INFO - OAuth callback detected - processing authentication
INFO - handle_callback() - Processing OAuth callback
INFO - Retrieved expected_state from session_state: abc123def456...
INFO - ✓ State verification successful - states match!
INFO - ✓ Successfully obtained access token from Google
INFO - OAuth authentication completed successfully!
```

### ❌ Failed: State Lost

```
INFO - User clicked 'Sign in with Google' button
INFO - Generated state: abc123def456...
INFO - Storing state in session_state['oauth_state']
```

Then after returning from Google:

```
WARNING - oauth_state NOT in session_state        ← PROBLEM
INFO - Session state keys: []                      ← Session was cleared
ERROR - CRITICAL: No oauth_state found in session_state
ERROR - All session_state keys: []
ERROR - auth_in_progress not set - this may indicate session was completely reset
```

**What this means:** Session state was lost during the redirect. See troubleshooting guide.

### ❌ Failed: State Mismatch

```
INFO - Retrieved expected_state from session_state: abc123def456...
INFO - State from Google: xyz789ghi012...
ERROR - CRITICAL: State mismatch detected
ERROR - Expected: abc123def456...
ERROR - Received: xyz789ghi012...
```

**What this means:** A new state was generated, overwriting the original. Check for multiple reruns.

## Browser Console Logs

Open browser DevTools (F12) → Console tab

### On "Sign in with Google" Click

```
================================================================================
Fieldmap OAuth Flow - Client Side
================================================================================
Timestamp: 2024-12-16T04:30:00.000Z
OAuth state (first 16 chars): abc123def456...
Redirect URL: https://accounts.google.com/o/oauth2/v2/auth?...
Initiating redirect to Google...
✓ Stored state in sessionStorage
================================================================================
```

### On Return from Google

```
================================================================================
Fieldmap Page Load
================================================================================
Timestamp: 2024-12-16T04:30:15.000Z
Current URL: https://fieldmap.streamlit.app/?code=4/0AfJohX...&state=abc123def456...
URL search params: ?code=4/0AfJohX...&state=abc123def456...
Query parameters found:
  code: 4/0AfJohXkL...
  state: abc123def456...
OAuth state in sessionStorage: abc123def456...
================================================================================
```

## Using the Debug Panel

1. Go to About page (before signing in)
2. Scroll down to "Sign In" section
3. Click "🔧 OAuth Debug Info" to expand
4. Check the following:

### What to Look For

**Session State (OAuth-related):**
```
✓ oauth_state: abc123def456... (length: 43)    ← Should be present during auth
✓ auth_in_progress: True                        ← Should be True during auth
✓ pending_auth_url: https://accounts...         ← Auth URL stored
✗ google_token: (not set)                       ← Should be set after successful auth
✓ google_authed: True                           ← Should be True after auth
✓ google_user_email: user@example.com           ← Your email after auth
```

**Query Parameters:**
```
code: 4/0AfJohXkL...                            ← Present on callback
state: abc123def456...                          ← Should match oauth_state
```

## Using oauth_diagnostics.py

Run the diagnostic tool:

```bash
streamlit run oauth_diagnostics.py
```

### What It Shows

1. **Query Parameters** - Shows code and state from Google
2. **Session State** - Shows oauth_state and other OAuth keys
3. **OAuth Configuration** - Verifies CLIENT_ID, APP_BASE_URL, etc.
4. **Authentication Status** - Shows if user is authenticated
5. **State Verification Test** - Compares session state to query param state
6. **Actions** - Buttons to clear state and test

### When to Use

- **Before** clicking "Sign in" - Check that config is correct
- **After** returning from Google - Check if state matches
- **When troubleshooting** - See all OAuth-related information in one place

## Common Debugging Scenarios

### Scenario 1: "Auth session expired" Error

**What to check:**
1. Streamlit Cloud Logs → Search for "No oauth_state found"
2. Browser Console → Check if sessionStorage has state
3. Debug Panel → Check if oauth_state is in session state

**Most likely cause:** Session state lost during redirect

**Next steps:** See OAUTH_TROUBLESHOOTING_GUIDE.md → "Cause 1: Session State Not Persisting"

### Scenario 2: Button Does Nothing

**What to check:**
1. Browser Console → Check for JavaScript errors
2. Browser Console → Check for redirect message
3. Streamlit Logs → Check if build_auth_url() was called

**Most likely cause:** JavaScript redirect failed

**Next steps:** Try clicking the "Continue to Google" fallback link

### Scenario 3: State Mismatch

**What to check:**
1. Streamlit Logs → Count how many times "Generated state:" appears
2. Streamlit Logs → Check if "Auth already in progress" message appears
3. Debug Panel → Check auth_in_progress flag

**Most likely cause:** Multiple reruns generating new states

**Next steps:** See OAUTH_TROUBLESHOOTING_GUIDE.md → "Cause 2: Multiple Reruns"

### Scenario 4: Redirect URI Mismatch

**What to check:**
1. Google error page → Look for "redirect_uri_mismatch"
2. Debug Panel → Check "Computed Redirect URI"
3. Google Cloud Console → Check "Authorized redirect URIs"

**Most likely cause:** URI in console doesn't match APP_BASE_URL

**Next steps:** See OAUTH_TROUBLESHOOTING_GUIDE.md → "Cause 4: Redirect URI Mismatch"

## Log Search Tips

### Streamlit Cloud Logs

**Search for specific flow:**
```
"User clicked 'Sign in'"    # Start of OAuth flow
"OAuth callback detected"    # User returned from Google
"OAuth authentication completed successfully"  # Success
```

**Search for errors:**
```
"CRITICAL"                   # Critical errors
"No oauth_state found"       # State lost
"State mismatch"             # State overwritten
```

**Filter by module:**
```
"google_oauth"               # OAuth module logs
"__main__"                   # App-level logs
```

### Browser Console

**Filter:**
```
"Fieldmap"                   # Our custom logs
"OAuth"                      # OAuth-specific logs
```

## Next Steps

- See **OAUTH_TROUBLESHOOTING_GUIDE.md** for detailed troubleshooting
- See **TESTING_OAUTH_FIX.md** for testing procedures
- See **OAUTH_FIX_DECEMBER_2024.md** for implementation details

## Quick Actions

```bash
# Run tests
python3 test_oauth.py

# Run diagnostics
streamlit run oauth_diagnostics.py

# Run app locally
streamlit run app.py

# View logs (if redirected to file)
tail -f logs/oauth.log
```

## Getting Help

When reporting issues, include:

1. **Logs:** Relevant section from Streamlit Cloud logs
2. **Browser Console:** Screenshot or copy of console output
3. **Debug Panel:** Screenshot of OAuth Debug Info panel
4. **oauth_diagnostics.py:** Screenshot of all sections
5. **Steps to reproduce:** What you clicked and when

This gives us complete visibility into what's happening during the OAuth flow.
