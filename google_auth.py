"""
Google authentication helper for Fieldmap.
Handles OAuth2 flow and credential management for Google Drive integration.
Clean implementation using Authlib with root URL redirect.
"""

import streamlit as st
from typing import Optional
import google_oauth
from google.oauth2.credentials import Credentials
import logging

# Configure logger
logger = logging.getLogger(__name__)


class GoogleAuthHelper:
    """Helper class for Google OAuth2 authentication - wrapper around google_oauth module"""
    
    def __init__(self):
        """
        Initialize Google authentication helper.
        Uses Authlib-based OAuth with root redirect URI.
        No cookie managers, no custom callback paths.
        """
        pass
    
    def is_authenticated(self) -> bool:
        """Check if user is already authenticated."""
        return google_oauth.is_authenticated()
    
    def get_user_email(self) -> Optional[str]:
        """Get authenticated user's email address."""
        return google_oauth.get_user_email()
    
    def get_credentials(self):
        """
        Get valid credentials for Google API calls.
        Returns google.oauth2.credentials.Credentials object compatible with Google API client.
        
        Returns:
            Credentials object or None
        """
        token = st.session_state.get("google_token")
        if not token:
            return None
        
        try:
            config = google_oauth.get_oauth_config()
            if not config:
                return None
            
            # Create Credentials object from token
            creds = Credentials(
                token=token.get("access_token"),
                refresh_token=token.get("refresh_token"),
                token_uri=google_oauth.GOOGLE_TOKEN_ENDPOINT,
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                scopes=google_oauth.OAUTH_SCOPE.split()
            )
            
            return creds
        except Exception as e:
            logger.error(f"Failed to create credentials: {e}")
            return None
    
    def sign_out(self):
        """Sign out by removing stored credentials."""
        google_oauth.sign_out()
        st.success("Signed out successfully")
