"""
Google OAuth implementation using Authlib for Streamlit Cloud.
Clean, proven approach with root URL redirect and no cookie managers.
Uses stateless signed OAuth state tokens for secure callback validation.
"""

import streamlit as st
import json
import os
import secrets
from typing import Optional, Dict, Any
from authlib.integrations.requests_client import OAuth2Session
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import logging

# Configure logger
logger = logging.getLogger(__name__)

# OAuth endpoints
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth scope
OAUTH_SCOPE = "openid email profile https://www.googleapis.com/auth/drive.file"

# OAuth state configuration
OAUTH_STATE_SALT = "fieldmap-oauth-state"
DEFAULT_OAUTH_STATE_MAX_AGE = 300  # 5 minutes


def get_oauth_state_secret() -> str:
    """
    Get OAuth state secret from environment or Streamlit secrets.
    Falls back to a dev-only random secret for local development.
    
    Returns:
        Secret key string for signing OAuth state tokens
    """
    secret = None
    
    # Try Streamlit secrets first
    try:
        secret = st.secrets.get("OAUTH_STATE_SECRET")
    except Exception:
        pass
    
    # Fall back to environment variable if not found in secrets
    if not secret:
        secret = os.environ.get("OAUTH_STATE_SECRET")
    
    if not secret:
        # For development only: generate a random secret
        # In production, this should always be set explicitly
        logger.warning("OAUTH_STATE_SECRET not set - generating dev-only random secret")
        logger.warning("For production, set OAUTH_STATE_SECRET environment variable")
        secret = secrets.token_urlsafe(32)
    
    return secret


def get_state_serializer() -> URLSafeTimedSerializer:
    """
    Get URLSafeTimedSerializer for signing OAuth state tokens.
    
    Returns:
        URLSafeTimedSerializer instance
    """
    secret = get_oauth_state_secret()
    return URLSafeTimedSerializer(secret, salt=OAUTH_STATE_SALT)


def get_oauth_state_max_age() -> int:
    """
    Get maximum age for OAuth state tokens in seconds.
    
    Returns:
        Max age in seconds (default: 300 = 5 minutes)
    """
    max_age = None
    
    # Try Streamlit secrets first
    try:
        max_age = st.secrets.get("OAUTH_STATE_MAX_AGE")
    except Exception:
        pass
    
    # Fall back to environment variable if not found in secrets
    if not max_age:
        max_age = os.environ.get("OAUTH_STATE_MAX_AGE")
    
    if max_age:
        try:
            return int(max_age)
        except (ValueError, TypeError):
            logger.warning(f"Invalid OAUTH_STATE_MAX_AGE value: {max_age}, using default")
    
    return DEFAULT_OAUTH_STATE_MAX_AGE


def get_oauth_config() -> Optional[Dict[str, str]]:
    """
    Get OAuth client configuration from Streamlit secrets or environment.
    
    Returns:
        Dict with client_id and client_secret, or None if not configured
    """
    client_id = None
    client_secret = None
    
    # Try Streamlit secrets first
    try:
        client_id = st.secrets.get("GOOGLE_CLIENT_ID")
        client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET")
    except Exception:
        pass
    
    # Fall back to environment variables if not found in secrets
    if not client_id:
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not client_secret:
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
    app_base_url = None
    
    # Try Streamlit secrets first
    try:
        app_base_url = st.secrets.get("APP_BASE_URL")
    except Exception:
        pass
    
    # Fall back to environment variable if not found in secrets
    if not app_base_url:
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


def clear_auth_state():
    """
    Clear all OAuth-related state from session_state.
    Helper function to eliminate duplication.
    Note: With signed state tokens, we don't store oauth_state in session anymore.
    """
    logger.info("clear_auth_state() - Clearing OAuth state from session")
    keys_to_clear = ["auth_in_progress", "pending_auth_url"]
    for key in keys_to_clear:
        if key in st.session_state:
            logger.debug(f"Deleting {key} from session_state")
            del st.session_state[key]
    logger.info("Auth state cleared from session_state")


def build_auth_url() -> Optional[str]:
    """
    Generate OAuth authorization URL with cryptographically signed state.
    Uses URLSafeTimedSerializer to create a stateless, time-limited state token.
    State verification does not depend on session_state persistence.
    
    Returns:
        Authorization URL or None if config not available
    """
    logger.info("="*80)
    logger.info("build_auth_url() - Generating OAuth authorization URL")
    logger.info("="*80)
    
    # Check if auth is already in progress to avoid overwriting state
    auth_in_progress = st.session_state.get("auth_in_progress", False)
    logger.info(f"auth_in_progress flag: {auth_in_progress}")
    
    if auth_in_progress:
        logger.warning("Auth already in progress, not generating new state")
        # Return existing auth_url if available
        existing_url = st.session_state.get("pending_auth_url")
        if existing_url:
            logger.info(f"Returning existing auth URL: {existing_url[:60]}...")
            return existing_url
        # If no existing URL but auth in progress, clear the flag and continue
        logger.warning("auth_in_progress=True but no pending_auth_url, clearing flag")
        st.session_state["auth_in_progress"] = False
    
    config = get_oauth_config()
    redirect_uri = get_redirect_uri()
    
    logger.info(f"OAuth config available: {config is not None}")
    logger.info(f"Redirect URI: {redirect_uri}")
    
    if not config or not redirect_uri:
        logger.error("OAuth config or redirect URI not available")
        return None
    
    try:
        # Generate signed state token using URLSafeTimedSerializer
        logger.debug("Generating signed OAuth state token")
        serializer = get_state_serializer()
        
        # Create state payload with a random nonce
        state_payload = {
            "nonce": secrets.token_hex(16)
        }
        
        # Sign and serialize the state
        signed_state = serializer.dumps(state_payload)
        
        logger.info(f"Generated signed OAuth state token (first 20 chars): {signed_state[:20]}...")
        logger.info(f"State payload nonce: {state_payload['nonce'][:16]}...")
        
        # Create OAuth2Session with the signed state
        logger.debug("Creating OAuth2Session")
        client = OAuth2Session(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            scope=OAUTH_SCOPE,
            redirect_uri=redirect_uri,
            state=signed_state  # Use our signed state instead of letting Authlib generate one
        )
        
        # Generate authorization URL
        logger.debug("Calling create_authorization_url()")
        auth_url, _ = client.create_authorization_url(
            GOOGLE_AUTH_ENDPOINT,
            access_type="offline",
            prompt="consent"
        )
        
        # Note: We do NOT store state in session_state for verification
        # The signed state token is self-contained and stateless
        logger.info("Signed state token is stateless - not storing in session_state")
        
        # Set auth_in_progress flag to prevent duplicate auth attempts
        logger.info("Setting auth_in_progress=True")
        st.session_state["auth_in_progress"] = True
        st.session_state["pending_auth_url"] = auth_url
        
        logger.info(f"Generated auth URL: {auth_url[:100]}...")
        logger.info(f"Session state keys after build_auth_url: {list(st.session_state.keys())}")
        logger.info("="*80)
        return auth_url
        
    except Exception as e:
        logger.error(f"Failed to build auth URL: {e}", exc_info=True)
        st.error(f"Failed to generate authorization URL: {str(e)}")
        return None


def handle_callback() -> bool:
    """
    Handle OAuth callback when user returns from Google.
    Verifies cryptographically signed state token (stateless verification).
    Exchanges code for token and stores in session_state.
    
    Returns:
        True if authentication successful, False otherwise
    """
    logger.info("="*80)
    logger.info("handle_callback() - Processing OAuth callback")
    logger.info("="*80)
    
    query_params = st.query_params
    logger.info(f"Query params: {dict(query_params)}")
    logger.info(f"Session state keys: {list(st.session_state.keys())}")
    
    # Check if we have the required params
    if "code" not in query_params:
        logger.warning("No code in query params - cannot proceed")
        return False
    
    code = query_params["code"]
    returned_state = query_params.get("state")
    
    logger.info(f"Code received: {code[:20]}...")
    logger.info(f"State from Google (first 20 chars): {returned_state[:20] if returned_state else 'MISSING'}...")
    
    # Verify signed state token
    if not returned_state:
        logger.error("="*80)
        logger.error("CRITICAL: No state parameter in callback URL")
        logger.error("="*80)
        st.error("❌ Auth session expired. Please click Sign in again.")
        logger.error("Showing 'Auth session expired' error to user")
        return False
    
    try:
        # Verify and decode the signed state token
        logger.info("Verifying signed OAuth state token...")
        serializer = get_state_serializer()
        max_age = get_oauth_state_max_age()
        
        logger.debug(f"Using max_age={max_age} seconds for state verification")
        
        # This will raise SignatureExpired if token is too old
        # or BadSignature if token was tampered with
        state_payload = serializer.loads(returned_state, max_age=max_age)
        
        logger.info("✓ Signed OAuth state token verified successfully!")
        logger.info(f"State payload nonce: {state_payload.get('nonce', 'N/A')[:16]}...")
        logger.info(f"Token age was within {max_age} seconds")
        
    except SignatureExpired as e:
        logger.error("="*80)
        logger.error("CRITICAL: OAuth state token expired")
        logger.error("="*80)
        logger.error(f"Token exceeded max age of {get_oauth_state_max_age()} seconds")
        logger.error(f"Error: {e}")
        st.error("❌ Auth session expired. Please click Sign in again.")
        return False
        
    except BadSignature as e:
        logger.error("="*80)
        logger.error("CRITICAL: Invalid or tampered OAuth state token")
        logger.error("="*80)
        logger.error(f"Signature verification failed - possible tampering or wrong secret")
        logger.error(f"Error: {e}")
        st.error("❌ Auth session expired. Please click Sign in again.")
        return False
        
    except Exception as e:
        logger.error("="*80)
        logger.error("CRITICAL: Unexpected error verifying OAuth state token")
        logger.error("="*80)
        logger.error(f"Error: {e}", exc_info=True)
        st.error("❌ Auth session expired. Please click Sign in again.")
        return False
    
    # Get config
    config = get_oauth_config()
    redirect_uri = get_redirect_uri()
    
    if not config or not redirect_uri:
        st.error("❌ OAuth configuration missing")
        logger.error("OAuth config or redirect URI not available during callback")
        return False
    
    logger.info("OAuth config and redirect URI available")
    
    try:
        # Create OAuth2Session with the same settings
        logger.info("Creating OAuth2Session for token exchange")
        client = OAuth2Session(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            redirect_uri=redirect_uri
        )
        
        # Exchange code for token
        logger.info("Exchanging authorization code for access token...")
        token = client.fetch_token(
            GOOGLE_TOKEN_ENDPOINT,
            grant_type="authorization_code",
            code=code
        )
        
        logger.info("✓ Successfully obtained access token from Google")
        logger.info(f"Token keys: {list(token.keys())}")
        
        # Store token in session_state
        logger.info("Storing token in session_state")
        st.session_state["google_token"] = token
        
        # Clean up OAuth state using helper function
        logger.info("Clearing auth state (auth_in_progress, pending_auth_url)")
        clear_auth_state()
        
        # Save token to Google Drive for persistence
        # Note: This is best-effort; if it fails, user will need to re-auth next session
        try:
            logger.info("Attempting to save token to Google Drive...")
            save_token_to_drive(token)
            logger.info("✓ Token saved to Drive")
        except Exception as e:
            logger.warning(f"Could not save token to Drive (non-critical): {e}")
        
        logger.info("="*80)
        logger.info("OAuth authentication completed successfully!")
        logger.info("="*80)
        return True
        
    except Exception as e:
        logger.error("="*80)
        logger.error("CRITICAL: Token exchange failed")
        logger.error("="*80)
        logger.error(f"Error: {e}", exc_info=True)
        st.error(f"❌ Authentication failed: {str(e)}")
        return False


def is_authenticated() -> bool:
    """
    Check if user is authenticated with a valid token.
    Handles token refresh if expired.
    
    Returns:
        True if authenticated, False otherwise
    """
    token = st.session_state.get("google_token")
    if not token:
        return False
    
    # Check if token has required fields
    if "access_token" not in token:
        return False
    
    # Check if token is expired and needs refresh
    if "expires_at" in token:
        import time
        if time.time() > token["expires_at"]:
            # Token is expired, try to refresh
            if "refresh_token" in token:
                if refresh_token():
                    # Successfully refreshed
                    return True
                else:
                    # Refresh failed, user needs to re-authenticate
                    return False
            else:
                # No refresh token available
                return False
    
    return True


def refresh_token() -> bool:
    """
    Refresh the access token using the refresh token.
    
    Returns:
        True if successful, False otherwise
    """
    token = st.session_state.get("google_token")
    if not token or "refresh_token" not in token:
        logger.error("Cannot refresh: no token or refresh_token")
        return False
    
    config = get_oauth_config()
    if not config:
        logger.error("Cannot refresh: OAuth config not available")
        return False
    
    try:
        import requests
        from authlib.integrations.requests_client import OAuth2Session
        
        # Create OAuth2Session
        client = OAuth2Session(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            token=token
        )
        
        # Refresh the token
        new_token = client.refresh_token(
            GOOGLE_TOKEN_ENDPOINT,
            refresh_token=token["refresh_token"]
        )
        
        # Update stored token
        st.session_state["google_token"] = new_token
        
        # Save refreshed token to Drive
        try:
            save_token_to_drive(new_token)
        except Exception as e:
            logger.warning(f"Could not save refreshed token to Drive: {e}")
        
        logger.info("Successfully refreshed access token")
        return True
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        return False


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
    Sign out by removing stored token and clearing auth state.
    """
    if "google_token" in st.session_state:
        del st.session_state["google_token"]
    
    # Clear all auth state using helper function
    clear_auth_state()
    
    logger.info("User signed out")


def save_token_to_drive(token: Dict[str, Any]) -> bool:
    """
    Save token to Google Drive for persistence across sessions.
    Creates Fieldmap/_meta folder and stores token.json there.
    
    Args:
        token: Token dictionary to save
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        from googleapiclient.http import MediaInMemoryUpload
        
        # Get config to create credentials
        config = get_oauth_config()
        if not config:
            logger.error("Cannot save token: OAuth config not available")
            return False
        
        # Create credentials from token
        creds = Credentials(
            token=token.get("access_token"),
            refresh_token=token.get("refresh_token"),
            token_uri=GOOGLE_TOKEN_ENDPOINT,
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            scopes=OAUTH_SCOPE.split()
        )
        
        # Build Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # Find or create Fieldmap folder
        query = "name='Fieldmap' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        
        if files:
            fieldmap_folder_id = files[0]['id']
        else:
            # Create Fieldmap folder
            file_metadata = {
                'name': 'Fieldmap',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            fieldmap_folder_id = folder.get('id')
        
        # Find or create _meta subfolder
        query = f"name='_meta' and '{fieldmap_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        
        if files:
            meta_folder_id = files[0]['id']
        else:
            # Create _meta folder
            file_metadata = {
                'name': '_meta',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [fieldmap_folder_id]
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            meta_folder_id = folder.get('id')
        
        # Save token as JSON
        token_json = json.dumps(token)
        media = MediaInMemoryUpload(token_json.encode('utf-8'), mimetype='application/json')
        
        # Check if token.json already exists
        query = f"name='token.json' and '{meta_folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        
        if files:
            # Update existing file
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
            logger.info("Updated token.json in Drive")
        else:
            # Create new file
            file_metadata = {
                'name': 'token.json',
                'parents': [meta_folder_id]
            }
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            logger.info("Created token.json in Drive")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save token to Drive: {e}")
        return False


def load_token_from_drive() -> Optional[Dict[str, Any]]:
    """
    Load token from Google Drive if it exists.
    Note: This requires already having a token, so it's mainly useful
    for refreshing or recovering from session state loss.
    
    Returns:
        Token dictionary or None if not found or error
    """
    try:
        # Check if we have a token in session to use for loading
        token = st.session_state.get("google_token")
        if not token:
            logger.info("Cannot load token from Drive: no existing token to authenticate with")
            return None
        
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        
        # Get config to create credentials
        config = get_oauth_config()
        if not config:
            logger.error("Cannot load token: OAuth config not available")
            return None
        
        # Create credentials from current token
        creds = Credentials(
            token=token.get("access_token"),
            refresh_token=token.get("refresh_token"),
            token_uri=GOOGLE_TOKEN_ENDPOINT,
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            scopes=OAUTH_SCOPE.split()
        )
        
        # Build Drive service
        service = build('drive', 'v3', credentials=creds)
        
        # Find Fieldmap/_meta/token.json
        query = "name='token.json' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name, parents)').execute()
        files = results.get('files', [])
        
        if not files:
            logger.info("token.json not found in Drive")
            return None
        
        # Download token.json
        file_id = files[0]['id']
        content = service.files().get_media(fileId=file_id).execute()
        
        # Parse JSON
        loaded_token = json.loads(content.decode('utf-8'))
        logger.info("Loaded token from Drive")
        return loaded_token
        
    except Exception as e:
        logger.error(f"Failed to load token from Drive: {e}")
        return None

