# OAuth Callback Handling Fix - Implementation Summary

## Problem Statement

The app was experiencing OAuth callback issues on Streamlit Cloud:

1. **Missing Page Error**: After Google login, users were redirected to `https://fieldmap.streamlit.app/oauth2callback?code=...&state=...`, which Streamlit interpreted as a missing page in the `pages/` directory.
2. **Delayed Redirect**: After clicking "Sign in with Google", users had to wait ~1 minute before the "Continue to Google" link appeared.
3. **Incomplete Token Exchange**: The OAuth callback wasn't being processed immediately on return from Google.

## Solution Implemented (Option A)

We implemented **Option A** from the requirements: Use the main app URL as redirect URI (no /oauth2callback path).

### Key Changes

#### 1. Updated Redirect URI (google_auth.py)

**Before:**
```python
def _get_redirect_uri(self):
    app_base_url = self._get_app_base_url()
    if app_base_url:
        base = app_base_url.rstrip('/')
        return f"{base}/oauth2callback"
    return None
```

**After:**
```python
def _get_redirect_uri(self):
    app_base_url = self._get_app_base_url()
    if app_base_url:
        # Use root URL (no /oauth2callback path) to avoid Streamlit treating it as a page
        return app_base_url.rstrip('/')
    return None
```

**Impact**: The redirect URI is now just `https://fieldmap.streamlit.app` instead of `https://fieldmap.streamlit.app/oauth2callback`. This avoids Streamlit's page routing mechanism entirely.

#### 2. Early OAuth Callback Processing (app.py - App.run())

**Added at the very beginning of `App.run()`:**

```python
def run(self):
    """Main application entry point"""
    # Handle OAuth callback FIRST, before any rendering
    # This processes query params from Google OAuth redirect at the root URL
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        # Validate state for CSRF protection
        expected_state = st.session_state.get('oauth_state')
        received_state = query_params['state']
        
        if not expected_state or expected_state != received_state:
            st.error("❌ Invalid OAuth state. Possible CSRF attack detected. Please try again.")
            st.query_params.clear()
            # Clear OAuth state
            if 'oauth_state' in st.session_state:
                del st.session_state['oauth_state']
            if PENDING_AUTH_URL_KEY in st.session_state:
                del st.session_state[PENDING_AUTH_URL_KEY]
            st.stop()
        else:
            # State is valid, proceed with token exchange
            redirect_uri = self.google_auth._get_redirect_uri()
            params = {'code': query_params['code'], 'state': query_params['state']}
            auth_response_url = f"{redirect_uri}?{urlencode(params)}"
            
            with st.spinner("Completing sign-in..."):
                try:
                    if self.google_auth.handle_oauth_callback(auth_response_url):
                        st.session_state.google_authed = True
                        st.session_state.google_user_email = self.google_auth.get_user_email()
                        # Clear query params and OAuth state
                        st.query_params.clear()
                        # Clear all OAuth state keys
                        st.success("✅ Successfully signed in!")
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed. Please try again.")
                        st.query_params.clear()
                except Exception as e:
                    error_msg = str(e)
                    st.error(f"❌ Authentication error: {error_msg}")
                    st.query_params.clear()
            st.stop()
    
    # Continue with normal app flow...
```

**Impact**: 
- OAuth callback is processed immediately when the user returns from Google
- No page rendering happens during callback processing (uses `st.stop()`)
- State validation ensures CSRF protection
- Query parameters are cleared after processing
- User is automatically redirected after successful authentication

#### 3. Removed Duplicate Callback Handling (app.py - AboutPage)

**Removed from `AboutPage.render()`:**
- Duplicate OAuth callback processing with code/state (now handled in App.run())

**Kept in `AboutPage.render()`:**
- OAuth error handling (for when Google returns an error)
- Sign-in UI

#### 4. Immediate Redirect on Sign-In Button Click (app.py - AboutPage)

**Before:**
```python
if st.button("Sign in with Google", ...):
    auth_url = self.google_auth.get_auth_url()
    if auth_url:
        st.session_state[PENDING_AUTH_URL_KEY] = auth_url
        st.session_state[REDIRECT_INITIATED_KEY] = True
        st.rerun()  # Requires rerun to show redirect

# On next render:
if st.session_state.get(REDIRECT_INITIATED_KEY, False):
    # Show JS redirect
    # Don't show fallback in same render
elif PENDING_AUTH_URL_KEY in st.session_state:
    # Show fallback link on subsequent render
```

**After:**
```python
if st.button("Sign in with Google", ...):
    auth_url = self.google_auth.get_auth_url()
    if auth_url:
        st.session_state[PENDING_AUTH_URL_KEY] = auth_url
        
        # Immediately show JS redirect
        safe_url = json.dumps(auth_url)
        components.html(
            f"""
            <script>
                window.top.location.href = {safe_url};
            </script>
            """,
            height=0
        )
        
        # Immediately show fallback link in the same render
        st.link_button(
            "Continue to Google",
            auth_url,
            type="primary",
            use_container_width=True
        )
        st.caption("⬆️ Click above if you weren't automatically redirected")
```

**Impact**:
- No delay between button click and redirect
- Both JS redirect and fallback link appear immediately in the same render
- No need for multiple reruns or delayed state flags
- User experience is immediate and seamless

#### 5. Updated Documentation

Updated all references to redirect URI in:
- `SETUP_GUIDE.md`: Changed redirect URI from `https://fieldmap.streamlit.app/oauth2callback` to `https://fieldmap.streamlit.app`
- `google_auth.py`: Updated setup instructions
- `app.py`: Updated debug info and setup instructions in AboutPage

**Example changes in SETUP_GUIDE.md:**
```markdown
- Authorized redirect URIs:
  - For Streamlit Cloud: `https://fieldmap.streamlit.app`
  - For local dev: `http://localhost:8501`
```

## Configuration Changes Required

### Google Cloud Console

Update the **Authorized redirect URIs** in your OAuth 2.0 Client ID:

**Remove:**
- `https://fieldmap.streamlit.app/oauth2callback`
- `http://localhost:8501/oauth2callback`

**Add:**
- `https://fieldmap.streamlit.app`
- `http://localhost:8501`

### Streamlit Cloud Secrets

No changes required to existing secrets. The same configuration works:

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

- [ ] Update Google Cloud Console redirect URIs
- [ ] Deploy to Streamlit Cloud
- [ ] Click "Sign in with Google" button
- [ ] Verify immediate redirect (no ~1 minute wait)
- [ ] Complete Google OAuth flow
- [ ] Verify redirect back to `https://fieldmap.streamlit.app/?code=...&state=...`
- [ ] Verify automatic sign-in completion
- [ ] Verify no "missing page /oauth2callback" error
- [ ] Verify "Signed in as [email]" message appears
- [ ] Verify Fieldmap and Gallery pages are accessible
- [ ] Test sign-out and sign-in again

## Benefits

1. **No Missing Page Error**: Using the root URL avoids Streamlit's page routing
2. **Immediate Redirect**: Users see the redirect immediately on button click
3. **Single Point of Processing**: OAuth callback handled once in App.run()
4. **Better UX**: No delays, no waiting for reruns
5. **Cleaner Code**: Removed duplicate callback handling logic
6. **Maintained Security**: State validation still enforced for CSRF protection

## Rollback Plan

If issues arise, you can revert to the previous approach by:
1. Reverting the changes in this PR
2. Updating Google Cloud Console redirect URIs back to `/oauth2callback`
3. Redeploying the app

However, this would bring back the "missing page" error and delayed redirect issues.
