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


class GoogleAuthHelper:
    """Helper class for Google OAuth2 authentication using Web Application OAuth"""
    
    def __init__(self):
        """
        Initialize Google authentication helper.
        Credentials loaded from st.secrets or environment variables.
        Token stored in session_state and persisted to Google Drive.
        """
        pass
    
    def _get_credentials_config(self):
        """
        Load OAuth client configuration from secrets.
        Tries st.secrets first, then environment variables.
        
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
            return json.loads(raw_json)
        except json.JSONDecodeError:
            return None
    
    def _get_redirect_uri(self):
        """Get the redirect URI from secrets or environment."""
        # Try Streamlit secrets first
        try:
            redirect_uri = st.secrets.get("GOOGLE_REDIRECT_URI")
        except Exception:
            redirect_uri = None
        
        # Fallback to environment variable
        if not redirect_uri:
            redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
        
        # Default for local development
        if not redirect_uri:
            redirect_uri = "http://localhost:8501"
        
        return redirect_uri
    
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
        
        Returns:
            Authorization URL or None if config not available
        """
        try:
            from google_auth_oauthlib.flow import Flow
            from storage import GOOGLE_DRIVE_SCOPE
            
            client_config = self._get_credentials_config()
            if not client_config:
                return None
            
            redirect_uri = self._get_redirect_uri()
            
            flow = Flow.from_client_config(
                client_config,
                scopes=[GOOGLE_DRIVE_SCOPE],
                redirect_uri=redirect_uri
            )
            
            # Generate auth URL with state for CSRF protection
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store state in session for verification
            st.session_state.oauth_state = state
            st.session_state.oauth_flow = flow
            
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
                st.error("OAuth flow not initialized")
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
            
            # Clean up flow state
            if 'oauth_flow' in st.session_state:
                del st.session_state.oauth_flow
            if 'oauth_state' in st.session_state:
                del st.session_state.oauth_state
            
            return True
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
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
                  GOOGLE_REDIRECT_URI = "http://localhost:8501"
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
