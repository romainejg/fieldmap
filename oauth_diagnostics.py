#!/usr/bin/env python3
"""
OAuth Diagnostics Tool for Fieldmap
Provides detailed information about OAuth flow state for debugging
"""

import streamlit as st
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def display_oauth_diagnostics():
    """Display comprehensive OAuth diagnostics information"""
    
    st.title("🔧 OAuth Diagnostics")
    st.markdown("This page shows detailed OAuth flow information for debugging purposes.")
    
    # Query Parameters Section
    st.header("1. Query Parameters")
    query_params = st.query_params
    if query_params:
        st.success(f"✓ Query parameters present: {len(query_params)} parameter(s)")
        for key, value in query_params.items():
            with st.expander(f"Parameter: {key}"):
                if key == 'code':
                    st.code(f"Value (truncated): {value[:40]}...")
                    st.code(f"Length: {len(value)}")
                elif key == 'state':
                    st.code(f"Value: {value}")
                    st.code(f"Length: {len(value)}")
                else:
                    st.code(f"Value: {value}")
    else:
        st.info("No query parameters present")
    
    # Session State Section
    st.header("2. Session State")
    st.markdown("**OAuth-related session state keys:**")
    
    oauth_related_keys = [
        'oauth_state',
        'auth_in_progress', 
        'pending_auth_url',
        'google_token',
        'google_authed',
        'google_user_email'
    ]
    
    found_keys = []
    missing_keys = []
    
    for key in oauth_related_keys:
        if key in st.session_state:
            found_keys.append(key)
            with st.expander(f"✓ {key}"):
                value = st.session_state[key]
                if key == 'oauth_state':
                    st.code(f"Value (first 32 chars): {value[:32]}...")
                    st.code(f"Full length: {len(value)}")
                elif key == 'google_token':
                    st.code(f"Token keys: {list(value.keys())}")
                    if 'expires_at' in value:
                        import time
                        expires_at = value['expires_at']
                        now = time.time()
                        if now < expires_at:
                            remaining = int(expires_at - now)
                            st.success(f"Token valid for {remaining} more seconds")
                        else:
                            st.error("Token expired!")
                elif key == 'pending_auth_url':
                    st.code(f"URL (truncated): {value[:80]}...")
                else:
                    st.code(f"Value: {value}")
        else:
            missing_keys.append(key)
    
    if found_keys:
        st.success(f"Found {len(found_keys)} OAuth-related keys in session state")
    
    if missing_keys:
        st.warning(f"Missing keys: {', '.join(missing_keys)}")
    
    st.markdown("**All session state keys:**")
    all_keys = list(st.session_state.keys())
    st.code(f"Total keys: {len(all_keys)}\n{all_keys}")
    
    # Configuration Section
    st.header("3. OAuth Configuration")
    
    try:
        import google_oauth
        
        config = google_oauth.get_oauth_config()
        if config:
            st.success("✓ OAuth config available")
            st.code(f"Client ID: {config['client_id'][:30]}...")
            st.code(f"Client Secret: {'*' * 20} (hidden)")
        else:
            st.error("✗ OAuth config NOT available")
        
        app_base_url = google_oauth.get_app_base_url()
        if app_base_url:
            st.success(f"✓ APP_BASE_URL: {app_base_url}")
        else:
            st.error("✗ APP_BASE_URL not set")
        
        redirect_uri = google_oauth.get_redirect_uri()
        if redirect_uri:
            st.success(f"✓ Redirect URI: {redirect_uri}")
        else:
            st.error("✗ Redirect URI not available")
            
    except Exception as e:
        st.error(f"Error loading OAuth config: {e}")
    
    # Authentication Status
    st.header("4. Authentication Status")
    
    try:
        import google_oauth
        
        is_authed = google_oauth.is_authenticated()
        if is_authed:
            st.success("✓ User is authenticated")
            email = google_oauth.get_user_email()
            if email:
                st.code(f"Email: {email}")
        else:
            st.warning("✗ User is NOT authenticated")
    except Exception as e:
        st.error(f"Error checking authentication: {e}")
    
    # State Verification Test
    st.header("5. State Verification Test")
    st.markdown("This tests whether oauth_state in session matches state in query params (if present)")
    
    session_state = st.session_state.get('oauth_state')
    query_state = query_params.get('state')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Session State:**")
        if session_state:
            st.code(f"{session_state[:32]}...")
        else:
            st.warning("(not set)")
    
    with col2:
        st.markdown("**Query Param:**")
        if query_state:
            st.code(f"{query_state[:32]}...")
        else:
            st.info("(not present)")
    
    with col3:
        st.markdown("**Match:**")
        if session_state and query_state:
            if session_state == query_state:
                st.success("✓ MATCH")
            else:
                st.error("✗ MISMATCH")
        else:
            st.info("N/A")
    
    # Timestamp
    st.header("6. Diagnostic Info")
    st.code(f"Timestamp: {datetime.now().isoformat()}")
    st.code(f"Python version: {sys.version}")
    
    # Actions
    st.header("7. Actions")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("Clear All Query Params"):
            st.query_params.clear()
            st.success("Cleared!")
            st.rerun()
    
    with col_b:
        if st.button("Clear OAuth Session State"):
            try:
                import google_oauth
                google_oauth.clear_auth_state()
                st.success("Cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col_c:
        if st.button("Refresh Page"):
            st.rerun()


if __name__ == "__main__":
    # This can be run as a standalone Streamlit page
    st.set_page_config(
        page_title="OAuth Diagnostics",
        layout="wide"
    )
    display_oauth_diagnostics()
