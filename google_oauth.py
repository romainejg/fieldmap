"""
Google OAuth implementation using Authlib for Streamlit Cloud.
Clean, proven approach with root URL redirect and no cookie managers.
"""

import streamlit as st
import json
import os
from typing import Optional, Dict, Any
from authlib.integrations.requests_client import OAuth2Session
import logging

# Configure logger
logger = logging.getLogger(__name__)

# OAuth endpoints
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth scope
OAUTH_SCOPE = "openid email profile https://www.googleapis.com/auth/drive.file"


def get_oauth_config() -> Optional[Dict[str, str]]:
    """
    Get OAuth client configuration from Streamlit secrets or environment.
    
    Returns:
        Dict with client_id and client_secret, or None if not configured
    """
    try:
        client_id = st.secrets.get("GOOGLE_CLIENT_ID")
        client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET")
    except Exception:
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    if client_id and client_secret:
        return {
            "client_id": client_id,
            "client_secret": client_secret
        }
    return None


def get_app_base_url() -> Optional[str]:
    """
    Get APP_BASE_URL from secrets or environment variables.
    
    Returns:
        str: APP_BASE_URL or None if not configured
    """
    try:
        app_base_url = st.secrets.get("APP_BASE_URL")
        if app_base_url:
            return app_base_url.rstrip('/')
    except Exception:
        pass
    
    app_base_url = os.environ.get("APP_BASE_URL")
    if app_base_url:
        return app_base_url.rstrip('/')
    
    return None


def get_redirect_uri() -> Optional[str]:
    """
    Get the OAuth redirect URI.
    MUST be the app root URL (APP_BASE_URL), not /oauth2callback.
    
    Returns:
        str: Redirect URI or None if APP_BASE_URL is not configured
    """
    return get_app_base_url()


def build_auth_url() -> Optional[str]:
    """
    Generate OAuth authorization URL with state and nonce.
    Uses Authlib OAuth2Session.
    
    Returns:
        Authorization URL or None if config not available
    """
    config = get_oauth_config()
    redirect_uri = get_redirect_uri()
    
    if not config or not redirect_uri:
        logger.error("OAuth config or redirect URI not available")
        return None
    
    try:
        # Create OAuth2Session
        client = OAuth2Session(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            scope=OAUTH_SCOPE,
            redirect_uri=redirect_uri
        )
        
        # Generate authorization URL with state
        auth_url, state = client.create_authorization_url(
            GOOGLE_AUTH_ENDPOINT,
            access_type="offline",
            prompt="consent"
        )
        
        # Store state in session_state for verification
        st.session_state["oauth_state"] = state
        
        logger.info(f"Generated auth URL with state: {state[:8]}...")
        return auth_url
        
    except Exception as e:
        logger.error(f"Failed to build auth URL: {e}")
        st.error(f"Failed to generate authorization URL: {str(e)}")
        return None


def handle_callback() -> bool:
    """
    Handle OAuth callback when user returns from Google.
    Verifies state, exchanges code for token, and stores in session_state.
    
    Returns:
        True if authentication successful, False otherwise
    """
    query_params = st.query_params
    
    # Check if we have the required params
    if "code" not in query_params:
        logger.warning("No code in query params")
        return False
    
    code = query_params["code"]
    returned_state = query_params.get("state")
    
    # Verify state
    expected_state = st.session_state.get("oauth_state")
    
    if not expected_state:
        st.error("❌ Auth session expired. Please click Sign in again.")
        logger.error("No oauth_state in session_state")
        return False
    
    if returned_state != expected_state:
        st.error("❌ Auth session expired. Please click Sign in again.")
        logger.error(f"State mismatch: expected {expected_state[:8]}..., got {returned_state[:8] if returned_state else 'None'}...")
        return False
    
    # Get config
    config = get_oauth_config()
    redirect_uri = get_redirect_uri()
    
    if not config or not redirect_uri:
        st.error("❌ OAuth configuration missing")
        logger.error("OAuth config or redirect URI not available during callback")
        return False
    
    try:
        # Create OAuth2Session with the same settings
        client = OAuth2Session(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=redirect_uri
        )
        
        # Exchange code for token
        token = client.fetch_token(
            GOOGLE_TOKEN_ENDPOINT,
            grant_type="authorization_code",
            code=code
        )
        
        # Store token in session_state
        st.session_state["google_token"] = token
        
        # Clean up OAuth state
        if "oauth_state" in st.session_state:
            del st.session_state["oauth_state"]
        
        logger.info("Successfully obtained OAuth token")
        return True
        
    except Exception as e:
        st.error(f"❌ Authentication failed: {str(e)}")
        logger.error(f"Token exchange failed: {e}")
        return False


def is_authenticated() -> bool:
    """
    Check if user is authenticated with a valid token.
    
    Returns:
        True if authenticated, False otherwise
    """
    token = st.session_state.get("google_token")
    if not token:
        return False
    
    # Check if token has required fields
    if "access_token" not in token:
        return False
    
    # TODO: Add token expiration check and refresh logic
    return True


def get_user_email() -> Optional[str]:
    """
    Get authenticated user's email address.
    
    Returns:
        Email address or None if not authenticated
    """
    if not is_authenticated():
        return None
    
    token = st.session_state.get("google_token")
    if not token:
        return None
    
    try:
        # Make request to userinfo endpoint
        import requests
        
        headers = {
            "Authorization": f"Bearer {token['access_token']}"
        }
        
        response = requests.get(GOOGLE_USERINFO_ENDPOINT, headers=headers)
        response.raise_for_status()
        
        user_info = response.json()
        return user_info.get("email")
        
    except Exception as e:
        logger.error(f"Failed to get user email: {e}")
        return None


def get_access_token() -> Optional[str]:
    """
    Get the access token for API calls.
    
    Returns:
        Access token or None if not authenticated
    """
    if not is_authenticated():
        return None
    
    token = st.session_state.get("google_token")
    return token.get("access_token") if token else None


def sign_out():
    """
    Sign out by removing stored token.
    """
    if "google_token" in st.session_state:
        del st.session_state["google_token"]
    if "oauth_state" in st.session_state:
        del st.session_state["oauth_state"]
    logger.info("User signed out")
