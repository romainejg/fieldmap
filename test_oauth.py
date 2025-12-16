#!/usr/bin/env python3
"""
Test script to verify google_oauth module functionality.
This tests the logic without requiring actual OAuth credentials.
"""

import sys
import os

# Mock Streamlit before importing our modules
class MockSessionState(dict):
    """Mock session_state that behaves like a dict and object"""
    def __getattr__(self, name):
        return self.get(name)
    
    def __setattr__(self, name, value):
        self[name] = value

class MockStreamlit:
    """Mock Streamlit module"""
    session_state = MockSessionState()
    query_params = {}
    secrets = {}
    
    def get(self, key, default=None):
        return self.secrets.get(key, default)
    
    def error(self, msg):
        print(f"[ERROR] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def success(self, msg):
        print(f"[SUCCESS] {msg}")
    
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Install mocks
sys.modules['streamlit'] = MockStreamlit()
st = MockStreamlit()

# Now import our module
import google_oauth

def test_config_functions():
    """Test configuration retrieval functions"""
    print("\n=== Testing Configuration Functions ===")
    
    # Test without any config
    config = google_oauth.get_oauth_config()
    assert config is None, "Should return None when no config set"
    print("✓ get_oauth_config() returns None when not configured")
    
    # Test with environment variables
    os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test_secret'
    
    config = google_oauth.get_oauth_config()
    assert config is not None, "Should return config when env vars set"
    assert config['client_id'] == 'test_client_id'
    assert config['client_secret'] == 'test_secret'
    print("✓ get_oauth_config() works with environment variables")
    
    # Test APP_BASE_URL
    os.environ['APP_BASE_URL'] = 'https://test.example.com'
    base_url = google_oauth.get_app_base_url()
    assert base_url == 'https://test.example.com'
    print("✓ get_app_base_url() works")
    
    # Test redirect URI
    redirect_uri = google_oauth.get_redirect_uri()
    assert redirect_uri == 'https://test.example.com'
    print("✓ get_redirect_uri() returns APP_BASE_URL")
    
    # Cleanup
    for key in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'APP_BASE_URL']:
        if key in os.environ:
            del os.environ[key]

def test_auth_url_generation():
    """Test auth URL generation with signed state tokens"""
    print("\n=== Testing Auth URL Generation ===")
    
    # Set up config
    os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test_secret'
    os.environ['APP_BASE_URL'] = 'https://test.example.com'
    os.environ['OAUTH_STATE_SECRET'] = 'test-secret-for-signing'
    
    # Clear any existing state
    st.session_state.clear()
    st.query_params.clear()
    
    auth_url = google_oauth.build_auth_url()
    
    # With stateless signed tokens, oauth_state is NOT stored in session_state
    assert 'oauth_state' not in st.session_state
    print(f"✓ build_auth_url() does not store state in session_state (stateless)")
    
    # Check that auth_in_progress flag was set
    assert st.session_state.get('auth_in_progress') == True
    print(f"✓ build_auth_url() set auth_in_progress flag")
    
    # Check that pending_auth_url was stored
    assert st.session_state.get('pending_auth_url') == auth_url
    print(f"✓ build_auth_url() stored pending_auth_url")
    
    # Check that URL was generated with state parameter
    assert auth_url is not None
    assert 'accounts.google.com' in auth_url
    assert 'client_id=test_client_id' in auth_url
    
    # Extract state from URL
    import urllib.parse
    parsed = urllib.parse.urlparse(auth_url)
    params = urllib.parse.parse_qs(parsed.query)
    assert 'state' in params
    state = params['state'][0]
    assert state is not None
    assert len(state) > 20  # Should be a signed token string
    print(f"✓ build_auth_url() generated valid URL with signed state: {state[:20]}...")
    
    # Test that calling again doesn't regenerate when auth_in_progress
    old_url = auth_url
    auth_url2 = google_oauth.build_auth_url()
    assert auth_url2 == old_url  # Should return same URL
    print(f"✓ build_auth_url() doesn't regenerate URL when auth_in_progress is True")
    
    # Cleanup
    st.session_state.clear()
    st.query_params.clear()
    for key in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'APP_BASE_URL', 'OAUTH_STATE_SECRET']:
        if key in os.environ:
            del os.environ[key]

def test_authentication_check():
    """Test authentication status check"""
    print("\n=== Testing Authentication Check ===")
    
    # No token
    st.session_state.clear()
    assert not google_oauth.is_authenticated()
    print("✓ is_authenticated() returns False when no token")
    
    # With token
    st.session_state['google_token'] = {
        'access_token': 'test_token',
        'refresh_token': 'test_refresh',
        'expires_in': 3600
    }
    assert google_oauth.is_authenticated()
    print("✓ is_authenticated() returns True when token present")
    
    # Cleanup
    st.session_state.clear()

def test_sign_out():
    """Test sign out functionality"""
    print("\n=== Testing Sign Out ===")
    
    # Set up some state
    st.session_state['google_token'] = {'access_token': 'test'}
    st.session_state['auth_in_progress'] = True
    st.session_state['pending_auth_url'] = 'https://example.com'
    
    google_oauth.sign_out()
    
    assert 'google_token' not in st.session_state
    # Note: oauth_state is not stored in session_state anymore with signed tokens
    assert 'auth_in_progress' not in st.session_state
    assert 'pending_auth_url' not in st.session_state
    print("✓ sign_out() clears token and auth flags")

def test_callback_with_signed_state():
    """Test callback handling with signed state tokens (stateless)"""
    print("\n=== Testing Callback with Signed State ===")
    
    # Set up config
    os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test_secret'
    os.environ['APP_BASE_URL'] = 'https://test.example.com'
    os.environ['OAUTH_STATE_SECRET'] = 'test-secret-for-callback'
    os.environ['OAUTH_STATE_MAX_AGE'] = '300'
    
    # Clear session state (simulating session loss)
    st.session_state.clear()
    st.query_params.clear()
    
    # Generate a signed state token (similar to what build_auth_url does)
    serializer = google_oauth.get_state_serializer()
    import secrets
    state_payload = {"nonce": secrets.token_hex(16)}
    signed_state = serializer.dumps(state_payload)
    
    # Simulate callback with signed state in query params
    st.query_params['state'] = signed_state
    st.query_params['code'] = 'test_auth_code'
    
    print(f"Signed state token: {signed_state[:30]}...")
    
    # Note: We can't fully test handle_callback without mocking the OAuth2 client
    # But we can verify it verifies the signed state token
    from unittest.mock import patch, MagicMock
    
    # Mock the OAuth2Session to avoid actual API calls
    with patch('google_oauth.OAuth2Session') as mock_session_class:
        mock_client = MagicMock()
        mock_session_class.return_value = mock_client
        # Explicitly set the return value for fetch_token
        mock_client.fetch_token.return_value = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_in': 3600
        }
        
        # Mock save_token_to_drive to avoid API calls (expect it to succeed)
        with patch('google_oauth.save_token_to_drive', return_value=True):
            result = google_oauth.handle_callback()
            
            # Should succeed because signed state is valid
            assert result == True
            print("✓ handle_callback() succeeds with stateless signed state verification")
            
            # Check that token was stored
            assert 'google_token' in st.session_state
            print("✓ handle_callback() stored token in session_state")
            
            # Check that auth flags were cleared
            assert 'auth_in_progress' not in st.session_state
            assert 'pending_auth_url' not in st.session_state
            print("✓ handle_callback() cleared auth_in_progress flags")
    
    # Cleanup
    st.session_state.clear()
    st.query_params.clear()
    for key in ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'APP_BASE_URL', 'OAUTH_STATE_SECRET', 'OAUTH_STATE_MAX_AGE']:
        if key in os.environ:
            del os.environ[key]

def main():
    """Run all tests"""
    print("=" * 60)
    print("Google OAuth Module Test Suite")
    print("=" * 60)
    
    try:
        test_config_functions()
        test_auth_url_generation()
        test_authentication_check()
        test_sign_out()
        test_callback_with_signed_state()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
