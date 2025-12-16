#!/usr/bin/env python3
"""
Unit tests for OAuth state signing and verification.
Tests the stateless signed state token functionality.
"""

import sys
import os
import time
from unittest.mock import patch

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


def test_state_sign_and_verify_success():
    """Test successful state token generation and verification"""
    print("\n=== Test: State Sign and Verify Success ===")
    
    # Set a test secret
    os.environ['OAUTH_STATE_SECRET'] = 'test-secret-key-for-signing'
    os.environ['OAUTH_STATE_MAX_AGE'] = '300'
    
    # Get serializer and create a state token
    serializer = google_oauth.get_state_serializer()
    
    # Generate a state payload (similar to what build_auth_url does)
    import secrets
    state_payload = {"nonce": secrets.token_hex(16)}
    
    # Sign the state
    signed_state = serializer.dumps(state_payload)
    
    print(f"Generated signed state: {signed_state[:40]}...")
    assert signed_state is not None
    assert len(signed_state) > 20
    print("✓ State token generated successfully")
    
    # Verify the state immediately (should succeed)
    max_age = google_oauth.get_oauth_state_max_age()
    verified_payload = serializer.loads(signed_state, max_age=max_age)
    
    print(f"Verified payload: {verified_payload}")
    assert verified_payload == state_payload
    assert verified_payload['nonce'] == state_payload['nonce']
    print("✓ State token verified successfully")
    
    # Cleanup
    del os.environ['OAUTH_STATE_SECRET']
    del os.environ['OAUTH_STATE_MAX_AGE']


def test_state_expiry():
    """Test that expired state tokens are rejected"""
    print("\n=== Test: State Token Expiry ===")
    
    # Set a test secret and very short max age
    os.environ['OAUTH_STATE_SECRET'] = 'test-secret-key-for-expiry'
    
    # Get serializer and create a state token
    serializer = google_oauth.get_state_serializer()
    
    import secrets
    state_payload = {"nonce": secrets.token_hex(16)}
    signed_state = serializer.dumps(state_payload)
    
    print(f"Generated signed state: {signed_state[:40]}...")
    print("Waiting 2 seconds...")
    time.sleep(2)
    
    # Try to verify with max_age=1 second (should fail)
    from itsdangerous import SignatureExpired
    try:
        verified_payload = serializer.loads(signed_state, max_age=1)
        print("❌ ERROR: Expired token was accepted!")
        assert False, "Expired token should have been rejected"
    except SignatureExpired as e:
        print(f"✓ Expired token rejected as expected: {e}")
    
    # Cleanup
    del os.environ['OAUTH_STATE_SECRET']


def test_state_tamper():
    """Test that tampered state tokens are rejected"""
    print("\n=== Test: Tampered State Token Detection ===")
    
    # Set a test secret
    os.environ['OAUTH_STATE_SECRET'] = 'test-secret-key-for-tampering'
    os.environ['OAUTH_STATE_MAX_AGE'] = '300'
    
    # Get serializer and create a state token
    serializer = google_oauth.get_state_serializer()
    
    import secrets
    state_payload = {"nonce": secrets.token_hex(16)}
    signed_state = serializer.dumps(state_payload)
    
    print(f"Original signed state: {signed_state[:40]}...")
    
    # Tamper with the token by changing a character
    if len(signed_state) > 10:
        tampered_state = signed_state[:10] + 'X' + signed_state[11:]
    else:
        tampered_state = signed_state + 'X'
    
    print(f"Tampered signed state: {tampered_state[:40]}...")
    
    # Try to verify tampered token (should fail)
    from itsdangerous import BadSignature
    max_age = google_oauth.get_oauth_state_max_age()
    
    try:
        verified_payload = serializer.loads(tampered_state, max_age=max_age)
        print("❌ ERROR: Tampered token was accepted!")
        assert False, "Tampered token should have been rejected"
    except BadSignature as e:
        print(f"✓ Tampered token rejected as expected: {e}")
    
    # Cleanup
    del os.environ['OAUTH_STATE_SECRET']
    del os.environ['OAUTH_STATE_MAX_AGE']


def test_different_secrets_reject():
    """Test that tokens signed with different secrets are rejected"""
    print("\n=== Test: Different Secrets Rejection ===")
    
    # Sign with one secret
    os.environ['OAUTH_STATE_SECRET'] = 'secret-one'
    serializer1 = google_oauth.get_state_serializer()
    
    import secrets
    state_payload = {"nonce": secrets.token_hex(16)}
    signed_state = serializer1.dumps(state_payload)
    
    print(f"Signed state with secret-one: {signed_state[:40]}...")
    
    # Try to verify with a different secret
    os.environ['OAUTH_STATE_SECRET'] = 'secret-two'
    serializer2 = google_oauth.get_state_serializer()
    
    from itsdangerous import BadSignature
    try:
        verified_payload = serializer2.loads(signed_state, max_age=300)
        print("❌ ERROR: Token signed with different secret was accepted!")
        assert False, "Token should be rejected when verified with different secret"
    except BadSignature as e:
        print(f"✓ Token rejected when using different secret: {e}")
    
    # Cleanup
    del os.environ['OAUTH_STATE_SECRET']


def test_get_oauth_state_secret_fallback():
    """Test that a dev secret is generated when OAUTH_STATE_SECRET is not set"""
    print("\n=== Test: OAuth State Secret Fallback ===")
    
    # Clear any existing secret
    if 'OAUTH_STATE_SECRET' in os.environ:
        del os.environ['OAUTH_STATE_SECRET']
    
    # Clear Streamlit secrets
    st.secrets = {}
    
    # Get secret (should generate a dev-only random one)
    secret1 = google_oauth.get_oauth_state_secret()
    
    print(f"Generated dev secret: {secret1[:20]}...")
    assert secret1 is not None
    assert len(secret1) > 20
    print("✓ Dev secret generated when OAUTH_STATE_SECRET not set")
    
    # Note: Each call generates a new random secret in dev mode
    # This is expected behavior


def test_get_oauth_state_max_age():
    """Test OAuth state max age configuration"""
    print("\n=== Test: OAuth State Max Age Configuration ===")
    
    # Test default value
    if 'OAUTH_STATE_MAX_AGE' in os.environ:
        del os.environ['OAUTH_STATE_MAX_AGE']
    st.secrets = {}
    
    max_age = google_oauth.get_oauth_state_max_age()
    assert max_age == 300  # Default is 5 minutes
    print(f"✓ Default max age: {max_age} seconds")
    
    # Test custom value
    os.environ['OAUTH_STATE_MAX_AGE'] = '600'
    max_age = google_oauth.get_oauth_state_max_age()
    assert max_age == 600
    print(f"✓ Custom max age from env: {max_age} seconds")
    
    # Test invalid value (should fall back to default)
    os.environ['OAUTH_STATE_MAX_AGE'] = 'invalid'
    max_age = google_oauth.get_oauth_state_max_age()
    assert max_age == 300  # Should fall back to default
    print(f"✓ Invalid value falls back to default: {max_age} seconds")
    
    # Cleanup
    if 'OAUTH_STATE_MAX_AGE' in os.environ:
        del os.environ['OAUTH_STATE_MAX_AGE']


def main():
    """Run all tests"""
    print("=" * 60)
    print("OAuth State Signing/Verification Test Suite")
    print("=" * 60)
    
    try:
        test_state_sign_and_verify_success()
        test_state_expiry()
        test_state_tamper()
        test_different_secrets_reject()
        test_get_oauth_state_secret_fallback()
        test_get_oauth_state_max_age()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
