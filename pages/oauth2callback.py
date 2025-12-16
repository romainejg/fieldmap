"""
OAuth2 Callback Handler for Streamlit Cloud.
This page handles the OAuth redirect from Google and exchanges the authorization code for tokens.
"""

import streamlit as st
import logging
from urllib.parse import parse_qs, urlparse

# Import OAuth utilities
import sys
from pathlib import Path

# Add parent directory to path to import oauth_utils
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from oauth_utils import exchange_code_for_tokens, save_tokens_to_session

logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(page_title="Signing In...", layout="centered")

# Hide sidebar on callback page
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Get query parameters
query_params = st.query_params

# Check for authorization code
code = query_params.get("code")
state = query_params.get("state")
error = query_params.get("error")

if error:
    st.error(f"❌ Authentication Error: {error}")
    st.info("Please close this page and try signing in again.")
    st.stop()

if not code:
    st.error("❌ No authorization code received")
    st.info("Please close this page and try signing in again.")
    st.stop()

# Show processing message
with st.spinner("🔐 Completing sign in..."):
    # Verify state token (stored in session state from authorization request)
    expected_state = st.session_state.get("oauth_state")
    
    if not expected_state:
        st.error("❌ OAuth state not found in session")
        st.info("Please close this page and try signing in again.")
        st.stop()
    
    if state != expected_state:
        st.error("❌ Invalid OAuth state - possible CSRF attack")
        st.info("Please close this page and try signing in again.")
        st.stop()
    
    # Exchange code for tokens
    token_info = exchange_code_for_tokens(code, state)
    
    if not token_info:
        st.error("❌ Failed to complete authentication")
        st.info("Please close this page and try signing in again.")
        st.stop()
    
    # Save tokens to session
    save_tokens_to_session(token_info)
    
    # Clear state token
    if "oauth_state" in st.session_state:
        del st.session_state["oauth_state"]

# Success! Redirect to main app
st.success("✅ Sign in successful!")
st.info("Redirecting to Fieldmap...")

# Use JavaScript to redirect to main app (clear query params)
st.markdown("""
<script>
    // Redirect to main app after 1 second
    setTimeout(function() {
        window.location.href = "/";
    }, 1000);
</script>
""", unsafe_allow_html=True)

# Also provide manual link
st.markdown("If you're not redirected automatically, [click here to continue](/).")
