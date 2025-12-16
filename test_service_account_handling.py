#!/usr/bin/env python3
"""
Test to verify that the app handles missing service account gracefully.

This test validates the transition from GOOGLE_SERVICE_ACCOUNT_JSON string format
to [google_service_account] TOML table format. It ensures:
- Service account loads correctly from TOML table
- No json.loads() is called on dict data
- App doesn't crash when service account is missing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from unittest.mock import Mock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_missing_service_account():
    """Test that app doesn't crash when service account is missing"""
    print("\n" + "="*80)
    print("Testing Service Account Handling")
    print("="*80 + "\n")
    
    # Test 1: Verify get_service_account_info returns None gracefully
    print("Test 1: get_service_account_info with missing service account...")
    
    # Mock st.secrets to simulate missing google_service_account
    mock_secrets = Mock()
    mock_secrets.keys.return_value = ['auth']  # Only auth, no service account
    mock_secrets.__contains__ = lambda self, key: key == 'auth'
    mock_secrets.__getitem__ = lambda self, key: {} if key == 'auth' else None
    
    with patch('streamlit.secrets', mock_secrets):
        # Import after patching
        from app import get_service_account_info
        
        result = get_service_account_info()
        
        if result is None:
            print("✓ get_service_account_info returned None (expected)")
        else:
            print(f"✗ get_service_account_info returned {result} (expected None)")
            return False
    
    # Test 2: Verify TOML table format is used correctly
    print("\nTest 2: get_service_account_info with TOML table...")
    
    mock_sa_table = {
        'type': 'service_account',
        'project_id': 'test-project',
        'client_email': 'test@test-project.iam.gserviceaccount.com',
        'private_key': '-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n'
    }
    
    mock_secrets_with_sa = Mock()
    mock_secrets_with_sa.keys.return_value = ['auth', 'google_service_account']
    mock_secrets_with_sa.__contains__ = lambda self, key: key in ['auth', 'google_service_account']
    mock_secrets_with_sa.__getitem__ = lambda self, key: mock_sa_table if key == 'google_service_account' else {}
    
    with patch('streamlit.secrets', mock_secrets_with_sa):
        # Re-import to get fresh module state
        import importlib
        import app as app_module
        importlib.reload(app_module)
        
        result = app_module.get_service_account_info()
        
        if result is not None and result.get('client_email') == 'test@test-project.iam.gserviceaccount.com':
            print("✓ Service account loaded from TOML table (expected)")
        else:
            print(f"✗ Unexpected result: {result}")
            return False
    
    # Test 3: Verify no JSON parsing is attempted
    print("\nTest 3: Verify no json.loads is called...")
    
    # If there's a json.loads call on the service account data, it would fail
    # because we're passing a dict, not a string
    try:
        with patch('streamlit.secrets', mock_secrets_with_sa):
            import importlib
            import app as app_module
            importlib.reload(app_module)
            
            result = app_module.get_service_account_info()
            # If we get here without error, json.loads was NOT called on dict
            print("✓ No json.loads called on service account dict (expected)")
    except Exception as e:
        print(f"✗ Error occurred (possibly json.loads on dict): {e}")
        return False
    
    print("\n" + "="*80)
    print("All Tests Passed!")
    print("="*80 + "\n")
    return True


if __name__ == "__main__":
    try:
        success = test_missing_service_account()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
