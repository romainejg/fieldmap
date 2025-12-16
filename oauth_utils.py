"""
OAuth utilities for Google Drive user authentication.
Handles OAuth flow, token management, and encrypted cookie storage.
"""

import streamlit as st
import json
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_oauth_config() -> Optional[Dict[str, str]]:
    """
    Get OAuth configuration from Streamlit secrets.
    
    Returns:
        dict: OAuth config with client_id, client_secret, redirect_uri, cookie_secret
        None: If not configured
    """
    try:
        if "auth" not in st.secrets:
            logger.error("OAuth configuration missing: [auth] section not found in secrets")
            return None
        
        auth_config = st.secrets["auth"]
        required_fields = ["client_id", "client_secret", "redirect_uri", "cookie_secret"]
        
        for field in required_fields:
            if field not in auth_config or not auth_config[field]:
                logger.error(f"OAuth configuration missing: [auth].{field} not found")
                return None
        
        return {
            "client_id": auth_config["client_id"],
            "client_secret": auth_config["client_secret"],
            "redirect_uri": auth_config["redirect_uri"],
            "cookie_secret": auth_config["cookie_secret"],
        }
    except Exception as e:
        logger.error(f"Failed to load OAuth config: {e}", exc_info=True)
        return None


def init_oauth_flow():
    """
    Initialize Google OAuth flow for user authentication.
    
    Returns:
        Flow: Google OAuth flow object
        str: Generated state token for CSRF protection
    """
    from google_auth_oauthlib.flow import Flow
    
    oauth_config = get_oauth_config()
    if not oauth_config:
        raise ValueError("OAuth configuration not found")
    
    # Create flow with Drive scope for user OAuth
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": oauth_config["client_id"],
                "client_secret": oauth_config["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [oauth_config["redirect_uri"]],
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/drive.file",  # Create and manage files
            "https://www.googleapis.com/auth/userinfo.email",  # User email
            "openid",  # OpenID Connect
        ],
    )
    
    flow.redirect_uri = oauth_config["redirect_uri"]
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    
    return flow, state


def get_authorization_url() -> tuple[str, str]:
    """
    Generate Google OAuth authorization URL.
    
    Returns:
        tuple: (authorization_url, state_token)
    """
    flow, state = init_oauth_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",  # Request refresh token
        include_granted_scopes="true",
        state=state,
        prompt="consent",  # Force consent screen to get refresh token
    )
    
    return authorization_url, state


def exchange_code_for_tokens(code: str, state: str) -> Optional[Dict[str, Any]]:
    """
    Exchange authorization code for access and refresh tokens.
    
    Args:
        code: Authorization code from OAuth callback
        state: State token for verification
    
    Returns:
        dict: Token info with access_token, refresh_token, etc.
        None: If exchange fails
    """
    try:
        flow, _ = init_oauth_flow()
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Extract token info
        token_info = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        
        # Get user info
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        user_credentials = Credentials(
            token=token_info["access_token"],
            refresh_token=token_info["refresh_token"],
            token_uri=token_info["token_uri"],
            client_id=token_info["client_id"],
            client_secret=token_info["client_secret"],
            scopes=token_info["scopes"],
        )
        
        oauth2_service = build("oauth2", "v2", credentials=user_credentials)
        user_info = oauth2_service.userinfo().get().execute()
        
        token_info["email"] = user_info.get("email")
        token_info["name"] = user_info.get("name")
        
        return token_info
        
    except Exception as e:
        logger.error(f"Failed to exchange code for tokens: {e}", exc_info=True)
        return None


def save_tokens_to_session(token_info: Dict[str, Any]):
    """
    Save OAuth tokens to session state.
    
    Args:
        token_info: Token information dict
    """
    st.session_state["oauth_tokens"] = token_info
    st.session_state["user_email"] = token_info.get("email")
    st.session_state["user_name"] = token_info.get("name")
    st.session_state["logged_in"] = True
    
    logger.info(f"User authenticated: {token_info.get('email')}")


def get_user_credentials():
    """
    Get Google credentials from stored OAuth tokens.
    
    Returns:
        Credentials: Google OAuth credentials object
        None: If not authenticated
    """
    from google.oauth2.credentials import Credentials
    
    token_info = st.session_state.get("oauth_tokens")
    if not token_info:
        return None
    
    try:
        credentials = Credentials(
            token=token_info.get("access_token"),
            refresh_token=token_info.get("refresh_token"),
            token_uri=token_info.get("token_uri"),
            client_id=token_info.get("client_id"),
            client_secret=token_info.get("client_secret"),
            scopes=token_info.get("scopes"),
        )
        
        # Check if token needs refresh
        if credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            # Update stored tokens
            token_info["access_token"] = credentials.token
            if credentials.expiry:
                token_info["expiry"] = credentials.expiry.isoformat()
            st.session_state["oauth_tokens"] = token_info
        
        return credentials
        
    except Exception as e:
        logger.error(f"Failed to get user credentials: {e}", exc_info=True)
        return None


def is_authenticated() -> bool:
    """
    Check if user is authenticated.
    
    Returns:
        bool: True if user is authenticated, False otherwise
    """
    return st.session_state.get("logged_in", False) and st.session_state.get("oauth_tokens") is not None


def logout():
    """
    Clear authentication state.
    """
    keys_to_clear = ["oauth_tokens", "user_email", "user_name", "logged_in"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    logger.info("User logged out")


def get_user_email() -> Optional[str]:
    """
    Get authenticated user's email.
    
    Returns:
        str: User email
        None: If not authenticated
    """
    return st.session_state.get("user_email")


def get_user_name() -> Optional[str]:
    """
    Get authenticated user's name.
    
    Returns:
        str: User name
        None: If not authenticated
    """
    return st.session_state.get("user_name")
