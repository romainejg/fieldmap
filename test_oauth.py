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
    del os.environ['GOOGLE_CLIENT_ID']
    del os.environ['GOOGLE_CLIENT_SECRET']
    del os.environ['APP_BASE_URL']

def test_auth_url_generation():
    """Test auth URL generation"""
    print("\n=== Testing Auth URL Generation ===")
    
    # Set up config
    os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test_secret'
    os.environ['APP_BASE_URL'] = 'https://test.example.com'
    
    # Clear any existing state
    st.session_state.clear()
    st.query_params.clear()
    
    auth_url = google_oauth.build_auth_url()
    
    # Check that state was stored in session_state
    assert 'oauth_state' in st.session_state
    state = st.session_state['oauth_state']
    assert state is not None
    assert len(state) > 20  # Should be a long random string
    print(f"✓ build_auth_url() generated state in session_state: {state[:10]}...")
    
    # Check that state was ALSO stored in query_params
    assert 'oauth_state' in st.query_params
    assert st.query_params['oauth_state'] == state
    print(f"✓ build_auth_url() also stored state in query_params")
    
    # Check that auth_in_progress flag was set
    assert st.session_state.get('auth_in_progress') == True
    print(f"✓ build_auth_url() set auth_in_progress flag")
    
    # Check that pending_auth_url was stored
    assert st.session_state.get('pending_auth_url') == auth_url
    print(f"✓ build_auth_url() stored pending_auth_url")
    
    # Check that URL was generated
    assert auth_url is not None
    assert 'accounts.google.com' in auth_url
    assert 'client_id=test_client_id' in auth_url
    assert f'state={state}' in auth_url
    print(f"✓ build_auth_url() generated valid URL")
    
    # Test that calling again doesn't overwrite state
    old_state = state
    old_url = auth_url
    auth_url2 = google_oauth.build_auth_url()
    assert auth_url2 == old_url  # Should return same URL
    assert st.session_state['oauth_state'] == old_state  # State should not change
    print(f"✓ build_auth_url() doesn't overwrite state when auth_in_progress is True")
    
    # Cleanup
    st.session_state.clear()
    st.query_params.clear()
    del os.environ['GOOGLE_CLIENT_ID']
    del os.environ['GOOGLE_CLIENT_SECRET']
    del os.environ['APP_BASE_URL']

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
    st.session_state['oauth_state'] = 'test_state'
    st.session_state['auth_in_progress'] = True
    st.session_state['pending_auth_url'] = 'https://example.com'
    
    google_oauth.sign_out()
    
    assert 'google_token' not in st.session_state
    assert 'oauth_state' not in st.session_state
    assert 'auth_in_progress' not in st.session_state
    assert 'pending_auth_url' not in st.session_state
    print("✓ sign_out() clears token, state, and auth flags")

def test_callback_with_query_params():
    """Test callback handling with state in query params"""
    print("\n=== Testing Callback with Query Params ===")
    
    # Set up config
    os.environ['GOOGLE_CLIENT_ID'] = 'test_client_id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test_secret'
    os.environ['APP_BASE_URL'] = 'https://test.example.com'
    
    # Simulate state stored in query params (but not session_state)
    # This simulates what happens after redirect
    st.session_state.clear()
    st.query_params.clear()
    test_state = 'test_oauth_state_12345'
    st.query_params['oauth_state'] = test_state
    st.query_params['state'] = test_state
    st.query_params['code'] = 'test_auth_code'
    
    # Note: We can't fully test handle_callback without mocking the OAuth2 client
    # But we can verify it retrieves state from query params
    from unittest.mock import patch, MagicMock
    
    # Mock the OAuth2Session to avoid actual API calls
    with patch('google_oauth.OAuth2Session') as mock_session_class:
        mock_client = MagicMock()
        mock_session_class.return_value = mock_client
        mock_client.fetch_token.return_value = {
            'access_token': 'test_token',
            'refresh_token': 'test_refresh',
            'expires_in': 3600
        }
        
        # Mock save_token_to_drive to avoid API calls
        with patch('google_oauth.save_token_to_drive'):
            result = google_oauth.handle_callback()
            
            # Should succeed because state matches
            assert result == True
            print("✓ handle_callback() succeeds with state from query params")
            
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
    del os.environ['GOOGLE_CLIENT_ID']
    del os.environ['GOOGLE_CLIENT_SECRET']
    del os.environ['APP_BASE_URL']

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
        test_callback_with_query_params()
        
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
