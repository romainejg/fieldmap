"""
Google authentication helper for Fieldmap.
Handles OAuth2 flow and credential management for Google Drive integration.
Uses Web Application OAuth flow with credentials from secrets (not files).
"""

import streamlit as st
import json
import os
from typing import Optional
import io
import secrets
from streamlit_cookies_manager import EncryptedCookieManager


class GoogleAuthHelper:
    """Helper class for Google OAuth2 authentication using Web Application OAuth"""
    
    def __init__(self):
        """
        Initialize Google authentication helper.
        Credentials loaded from st.secrets or environment variables.
        Token stored in session_state and persisted to Google Drive.
        Uses cookie-backed state storage for OAuth flow.
        """
        # Initialize cookie manager for OAuth state persistence
        self.cookies = self._get_cookie_manager()
    
    def _get_cookie_manager(self):
        """
        Get or create cookie manager for OAuth state persistence.
        
        Returns:
            EncryptedCookieManager instance
        """
        # Use a password from secrets or a default one
        # Note: The cookie only stores the OAuth state (a random CSRF token),
        # not credentials. While a custom password is recommended for production,
        # using a default password here is acceptable since:
        # 1. The state itself is a cryptographically random token
        # 2. State is validated server-side against stored value
        # 3. State contains no sensitive user data
        # For production, set COOKIE_PASSWORD in Streamlit secrets
        try:
            password = st.secrets.get("COOKIE_PASSWORD", "fieldmap-oauth-cookie-secret-key-change-me")
        except Exception:
            password = os.environ.get("COOKIE_PASSWORD", "fieldmap-oauth-cookie-secret-key-change-me")
        
        # Create cookie manager if not already in session_state
        if 'cookie_manager' not in st.session_state:
            st.session_state.cookie_manager = EncryptedCookieManager(
                prefix="fieldmap_",
                password=password
            )
        
        # Ensure cookies are ready
        if not st.session_state.cookie_manager.ready():
            st.stop()
        
        return st.session_state.cookie_manager
    
    def _get_credentials_config(self):
        """
        Load OAuth client configuration from secrets.
        Tries st.secrets first, then environment variables.
        Validates that the client is a Web application type.
        
        Returns:
            dict: OAuth client configuration or None if not available
        """
        # Try Streamlit secrets first
        try:
            raw_json = st.secrets.get("GOOGLE_OAUTH_CLIENT_JSON")
        except Exception:
            raw_json = None
        
        # Fallback to environment variable
        if not raw_json:
            raw_json = os.environ.get("GOOGLE_OAUTH_CLIENT_JSON")
        
        if not raw_json:
            return None
        
        try:
            config = json.loads(raw_json)
            
            # Validate that this is a Web application OAuth client
            # The JSON should have a "web" key, not "installed"
            if "web" not in config:
                if "installed" in config:
                    st.error("⚠️ **Configuration Error**: OAuth client type is 'installed' (Desktop app). Please use a 'web' application type for proper redirect flow.")
                else:
                    st.warning("⚠️ **Configuration Warning**: OAuth client configuration doesn't have expected 'web' key. OAuth may not work correctly.")
                return None
            
            # Warn if both web and installed are present (unusual but possible)
            if "installed" in config:
                st.warning("⚠️ **Configuration Warning**: OAuth client has both 'web' and 'installed' keys. Using 'web' configuration.")
            
            return config
        except json.JSONDecodeError:
            return None
    
    def _get_app_base_url(self):
        """
        Get APP_BASE_URL from secrets or environment variables.
        
        Returns:
            str: APP_BASE_URL or None if not configured
        """
        # Try Streamlit secrets first
        try:
            app_base_url = st.secrets.get("APP_BASE_URL")
            if app_base_url:
                return app_base_url
        except Exception:
            pass
        
        # Fallback to environment variable
        app_base_url = os.environ.get("APP_BASE_URL")
        if app_base_url:
            return app_base_url
        
        return None
    
    def _get_redirect_uri(self):
        """
        Get the redirect URI dynamically from APP_BASE_URL.
        
        APP_BASE_URL is REQUIRED and must be set in secrets or environment variables.
        No localhost fallback to prevent production issues.
        
        For Streamlit Cloud, use the root URL to avoid "missing page" errors.
        The OAuth callback will be handled via query parameters on the main app route.
        
        Returns:
            str: Redirect URI or None if APP_BASE_URL is not configured
        """
        app_base_url = self._get_app_base_url()
        if app_base_url:
            # Use root URL (no /oauth2callback path) to avoid Streamlit treating it as a page
            return app_base_url.rstrip('/')
        
        # No fallback - APP_BASE_URL is required
        return None
    
    def _get_expected_state(self):
        """
        Get expected OAuth state from cookie (preferred) or session_state (fallback).
        
        Returns:
            tuple: (state_value, source) where source is 'cookie', 'session', or 'none'
        """
        # Try cookie first (more reliable across redirects)
        cookie_state = self.cookies.get('oauth_state')
        if cookie_state:
            return (cookie_state, 'cookie')
        
        # Fallback to session_state
        session_state = st.session_state.get('oauth_state')
        if session_state:
            return (session_state, 'session')
        
        return (None, 'none')
    
    def _get_stored_token(self):
        """Get stored token from session_state."""
        return st.session_state.get('google_oauth_token')
    
    def _store_token(self, token_dict):
        """Store token in session_state."""
        st.session_state.google_oauth_token = token_dict
    
    def is_authenticated(self) -> bool:
        """Check if user is already authenticated."""
        token_dict = self._get_stored_token()
        if not token_dict:
            return False
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            
            # Reconstruct credentials from dict
            creds = Credentials(
                token=token_dict.get('token'),
                refresh_token=token_dict.get('refresh_token'),
                token_uri=token_dict.get('token_uri'),
                client_id=token_dict.get('client_id'),
                client_secret=token_dict.get('client_secret'),
                scopes=token_dict.get('scopes')
            )
            
            # Check if credentials are valid
            if creds and creds.valid:
                return True
            
            # Try to refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Update stored token
                self._store_token({
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                })
                return True
            
            return False
        except Exception:
            return False
    
    def get_user_email(self) -> Optional[str]:
        """Get authenticated user's email address."""
        if not self.is_authenticated():
            return None
        
        try:
            token_dict = self._get_stored_token()
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            creds = Credentials(
                token=token_dict.get('token'),
                refresh_token=token_dict.get('refresh_token'),
                token_uri=token_dict.get('token_uri'),
                client_id=token_dict.get('client_id'),
                client_secret=token_dict.get('client_secret'),
                scopes=token_dict.get('scopes')
            )
            
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info.get('email')
        except Exception:
            return None
    
    def get_credentials(self):
        """
        Get valid credentials for Google API calls.
        
        Returns:
            Credentials object or None
        """
        if not self.is_authenticated():
            return None
        
        try:
            from google.oauth2.credentials import Credentials
            token_dict = self._get_stored_token()
            
            return Credentials(
                token=token_dict.get('token'),
                refresh_token=token_dict.get('refresh_token'),
                token_uri=token_dict.get('token_uri'),
                client_id=token_dict.get('client_id'),
                client_secret=token_dict.get('client_secret'),
                scopes=token_dict.get('scopes')
            )
        except Exception:
            return None
    
    def get_auth_url(self) -> Optional[str]:
        """
        Generate OAuth authorization URL for web flow.
        Uses cookie-backed state storage to survive redirects.
        Prevents state regeneration on reruns.
        
        Returns:
            Authorization URL or None if config not available
        """
        # Check if auth is already in progress - reuse existing auth_url and state
        if st.session_state.get('auth_in_progress', False):
            stored_auth_url = st.session_state.get('pending_auth_url')
            if stored_auth_url:
                return stored_auth_url
        
        try:
            from google_auth_oauthlib.flow import Flow
            from storage import GOOGLE_DRIVE_SCOPE
            
            client_config = self._get_credentials_config()
            if not client_config:
                return None
            
            redirect_uri = self._get_redirect_uri()
            if not redirect_uri:
                st.error("❌ APP_BASE_URL is not configured. Please set it in Streamlit secrets or environment variables.")
                return None
            
            flow = Flow.from_client_config(
                client_config,
                scopes=[GOOGLE_DRIVE_SCOPE],
                redirect_uri=redirect_uri
            )
            
            # Generate a secure random state token
            # We generate our own state (instead of letting the library generate it)
            # so we can store it in both cookie and session_state before the redirect.
            # The library accepts a custom state parameter and will use it in the auth URL.
            state = secrets.token_urlsafe(32)
            
            # Build auth URL with the state
            # The state parameter is passed to authorization_url() and will be used
            # in the returned URL. The second return value would be the same state.
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=state
            )
            
            # Store state in BOTH cookie and session_state for redundancy
            self.cookies['oauth_state'] = state
            self.cookies.save()
            st.session_state.oauth_state = state
            st.session_state.oauth_flow = flow
            
            # Mark auth as in progress and store the URL
            st.session_state.auth_in_progress = True
            st.session_state.pending_auth_url = auth_url
            
            return auth_url
        except Exception as e:
            st.error(f"Failed to generate auth URL: {str(e)}")
            return None
    
    def handle_oauth_callback(self, authorization_response: str) -> bool:
        """
        Handle OAuth callback and exchange code for token.
        
        Args:
            authorization_response: The full callback URL with code and state
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            flow = st.session_state.get('oauth_flow')
            if not flow:
                error_msg = "OAuth flow not initialized"
                st.session_state.last_oauth_error = error_msg
                st.error(error_msg)
                return False
            
            # Exchange authorization code for token
            flow.fetch_token(authorization_response=authorization_response)
            creds = flow.credentials
            
            # Store credentials in session_state
            self._store_token({
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            })
            
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
            
            # Clear any previous errors
            if 'last_oauth_error' in st.session_state:
                del st.session_state.last_oauth_error
            
            return True
        except Exception as e:
            error_msg = f"Authentication failed: {str(e)}"
            st.session_state.last_oauth_error = error_msg
            st.error(error_msg)
            return False
    
    def sign_out(self):
        """Sign out by removing stored credentials."""
        if 'google_oauth_token' in st.session_state:
            del st.session_state.google_oauth_token
        st.success("Signed out successfully")
    
    def render_auth_ui(self):
        """Render authentication UI in Streamlit sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔐 Google Drive Authentication")
        
        # Check if credentials are configured
        client_config = self._get_credentials_config()
        if not client_config:
            st.sidebar.error(
                "⚠️ OAuth credentials not configured.\n\n"
                "Please set GOOGLE_OAUTH_CLIENT_JSON in:\n"
                "- Streamlit Cloud: Secrets management\n"
                "- Local: Environment variable or .streamlit/secrets.toml"
            )
            with st.sidebar.expander("📖 Setup Instructions"):
                st.markdown("""
                **1. Create OAuth Web Application credentials:**
                - Go to [Google Cloud Console](https://console.cloud.google.com/)
                - Create/select project and enable Google Drive API
                - Create OAuth 2.0 Client ID (Web application type)
                - Add authorized redirect URIs:
                  - For Streamlit Cloud: `https://fieldmap.streamlit.app`
                  - For local: `http://localhost:8501`
                - Download JSON
                
                **2. Set secrets:**
                - Copy the full JSON content
                - In Streamlit Cloud: Paste in Secrets as `GOOGLE_OAUTH_CLIENT_JSON`
                - Locally: Add to `.streamlit/secrets.toml`:
                  ```
                  GOOGLE_OAUTH_CLIENT_JSON = '''{"web": {...}}'''
                  APP_BASE_URL = "http://localhost:8501"
                  ```
                """)
            return
        
        if self.is_authenticated():
            email = self.get_user_email()
            if email:
                st.sidebar.success(f"✅ Signed in as:\n{email}")
            else:
                st.sidebar.success("✅ Signed in")
            
            st.sidebar.info("📂 All photos are saved to Google Drive")
            
            if st.sidebar.button("Sign Out", key="google_signout"):
                self.sign_out()
                st.rerun()
        else:
            st.sidebar.info("Sign in to use Fieldmap (Google Drive storage required)")
            
            # For web OAuth, we need to handle redirect flow
            # Check if we're returning from OAuth
            query_params = st.query_params
            if 'code' in query_params:
                # Handle OAuth callback
                from urllib.parse import urlencode
                redirect_uri = self._get_redirect_uri()
                
                # Build authorization response URL with proper encoding
                params = {'code': query_params['code']}
                if 'state' in query_params:
                    params['state'] = query_params['state']
                
                auth_response_url = f"{redirect_uri}?{urlencode(params)}"
                
                if self.handle_oauth_callback(auth_response_url):
                    st.sidebar.success("✅ Successfully authenticated!")
                    # Clear query params
                    st.query_params.clear()
                    st.rerun()
            else:
                # Show sign-in button
                if st.sidebar.button("Sign in with Google", key="google_signin", type="primary"):
                    auth_url = self.get_auth_url()
                    if auth_url:
                        st.sidebar.markdown(f"[Click here to authorize]({auth_url})")
                        st.sidebar.info("After authorizing, you'll be redirected back to the app.")
