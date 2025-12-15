"""
Google authentication helper for Fieldmap.
Handles OAuth2 flow and credential management for Google Drive integration.
"""

import streamlit as st
import pickle
import os
from pathlib import Path
from typing import Optional


class GoogleAuthHelper:
    """Helper class for Google OAuth2 authentication"""
    
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.pickle'):
        """
        Initialize Google authentication helper.
        
        Args:
            credentials_path: Path to Google OAuth2 credentials JSON file
            token_path: Path to store/load authentication token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
    
    def is_authenticated(self) -> bool:
        """Check if user is already authenticated."""
        if not os.path.exists(self.token_path):
            return False
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
            
            # Check if credentials are valid
            if creds and creds.valid:
                return True
            
            # Try to refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)
                return True
            
            return False
        except Exception:
            return False
    
    def get_user_email(self) -> Optional[str]:
        """Get authenticated user's email address."""
        if not self.is_authenticated():
            return None
        
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
            
            service = build('oauth2', 'v2', credentials=creds)
            user_info = service.userinfo().get().execute()
            return user_info.get('email')
        except Exception:
            return None
    
    def authenticate(self) -> bool:
        """
        Perform OAuth2 authentication flow.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError:
            st.error(
                "Google API libraries not installed. "
                "Please install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            return False
        
        if not os.path.exists(self.credentials_path):
            st.error(
                f"Credentials file not found at `{self.credentials_path}`. "
                "\n\nTo enable Google Drive integration:\n"
                "1. Go to [Google Cloud Console](https://console.cloud.google.com/)\n"
                "2. Create a new project or select existing one\n"
                "3. Enable Google Drive API\n"
                "4. Create OAuth2 credentials (Desktop app)\n"
                "5. Download credentials as `credentials.json`\n"
                "6. Place the file in the app directory"
            )
            return False
        
        from storage import GOOGLE_DRIVE_SCOPE
        SCOPES = [GOOGLE_DRIVE_SCOPE]
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save the credentials
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            
            st.success("✅ Successfully authenticated with Google!")
            return True
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
    
    def sign_out(self):
        """Sign out by removing stored credentials."""
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            st.success("Signed out successfully")
    
    def render_auth_ui(self):
        """Render authentication UI in Streamlit sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔐 Google Drive")
        
        if self.is_authenticated():
            email = self.get_user_email()
            if email:
                st.sidebar.success(f"✅ Signed in as:\n{email}")
            else:
                st.sidebar.success("✅ Signed in")
            
            if st.sidebar.button("Sign Out", key="google_signout"):
                self.sign_out()
                st.rerun()
        else:
            st.sidebar.info("Sign in to save photos to Google Drive")
            
            if st.sidebar.button("Sign in with Google", key="google_signin", type="primary"):
                if self.authenticate():
                    st.rerun()
