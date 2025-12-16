#!/usr/bin/env python3
"""
Authentication Debugging Utility for Fieldmap
Validates secrets configuration and provides detailed diagnostics for signin issues.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_secrets_file() -> Tuple[bool, Dict]:
    """Check if secrets.toml exists and is readable"""
    print_header("Step 1: Checking Secrets File")
    
    secrets_path = Path(".streamlit/secrets.toml")
    
    if not secrets_path.exists():
        print_error(f"secrets.toml not found at: {secrets_path.absolute()}")
        print_info("Expected location: .streamlit/secrets.toml")
        print_info("You need to create this file from the template:")
        print_info("  cp .streamlit/secrets.toml.template .streamlit/secrets.toml")
        return False, {}
    
    print_success(f"secrets.toml found at: {secrets_path.absolute()}")
    
    # Try to load secrets using streamlit
    try:
        import streamlit as st
        # Force reload secrets
        st.secrets._parse()
        secrets = dict(st.secrets)
        print_success("Successfully loaded secrets using Streamlit")
        return True, secrets
    except Exception as e:
        print_error(f"Failed to load secrets: {e}")
        return False, {}

def validate_auth_section(secrets: Dict) -> List[str]:
    """Validate [auth] section of secrets"""
    print_header("Step 2: Validating [auth] Configuration")
    
    issues = []
    
    if 'auth' not in secrets:
        print_error("[auth] section not found in secrets.toml")
        issues.append("[auth] section missing")
        return issues
    
    print_success("[auth] section found")
    
    auth_config = secrets['auth']
    required_fields = [
        'redirect_uri',
        'cookie_secret',
        'client_id',
        'client_secret',
        'server_metadata_url'
    ]
    
    for field in required_fields:
        if field not in auth_config:
            print_error(f"Missing required field: {field}")
            issues.append(f"Missing field: {field}")
        elif not auth_config[field] or auth_config[field].startswith('<'):
            print_error(f"Field '{field}' has placeholder value: {auth_config[field][:50]}")
            issues.append(f"Placeholder value in: {field}")
        else:
            print_success(f"Field '{field}' is configured")
            
            # Additional validation
            if field == 'redirect_uri':
                uri = auth_config[field]
                if not uri.endswith('/oauth2callback'):
                    print_warning(f"redirect_uri should end with '/oauth2callback', got: {uri}")
                    issues.append(f"redirect_uri format: {uri}")
                else:
                    print_info(f"  Value: {uri}")
            
            elif field == 'cookie_secret':
                secret = auth_config[field]
                if len(secret) < 32:
                    print_warning(f"cookie_secret is short ({len(secret)} chars). Recommended: 43+ chars")
                    issues.append("cookie_secret too short")
                else:
                    print_info(f"  Length: {len(secret)} chars (good)")
            
            elif field == 'client_id':
                client_id = auth_config[field]
                if not client_id.endswith('.apps.googleusercontent.com'):
                    print_warning(f"client_id should end with '.apps.googleusercontent.com'")
                    issues.append("client_id format suspicious")
                else:
                    print_info(f"  Value: {client_id[:40]}...")
            
            elif field == 'server_metadata_url':
                url = auth_config[field]
                expected = "https://accounts.google.com/.well-known/openid-configuration"
                if url != expected:
                    print_warning(f"server_metadata_url doesn't match expected value")
                    print_info(f"  Expected: {expected}")
                    print_info(f"  Got: {url}")
    
    return issues

def validate_service_account(secrets: Dict) -> List[str]:
    """Validate Google Service Account configuration"""
    print_header("Step 3: Validating Service Account Configuration")
    
    issues = []
    
    if 'GOOGLE_SERVICE_ACCOUNT_JSON' not in secrets:
        print_error("GOOGLE_SERVICE_ACCOUNT_JSON not found in secrets.toml")
        issues.append("Service account JSON missing")
        return issues
    
    print_success("GOOGLE_SERVICE_ACCOUNT_JSON found")
    
    sa_json = secrets['GOOGLE_SERVICE_ACCOUNT_JSON']
    
    # Try to parse as JSON
    try:
        if isinstance(sa_json, str):
            sa_data = json.loads(sa_json)
        else:
            sa_data = sa_json
        print_success("Service account JSON is valid")
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in service account: {e}")
        issues.append("Invalid JSON in service account")
        return issues
    
    # Validate required fields
    required_fields = [
        'type',
        'project_id',
        'private_key_id',
        'private_key',
        'client_email',
        'client_id',
        'auth_uri',
        'token_uri'
    ]
    
    for field in required_fields:
        if field not in sa_data:
            print_error(f"Missing field in service account JSON: {field}")
            issues.append(f"Service account missing: {field}")
        elif not sa_data[field] or (isinstance(sa_data[field], str) and 
                                    (sa_data[field].startswith('<') or 
                                     sa_data[field] == 'YOUR_PRIVATE_KEY' or
                                     sa_data[field] == 'your-project-id')):
            print_error(f"Service account field '{field}' has placeholder value")
            issues.append(f"Service account placeholder: {field}")
        else:
            print_success(f"Field '{field}' is present")
            
            if field == 'type':
                if sa_data[field] != 'service_account':
                    print_warning(f"type should be 'service_account', got: {sa_data[field]}")
                    issues.append("Wrong service account type")
            
            elif field == 'client_email':
                email = sa_data[field]
                if not email.endswith('.iam.gserviceaccount.com'):
                    print_warning(f"client_email should end with '.iam.gserviceaccount.com'")
                    issues.append("Service account email format suspicious")
                else:
                    print_info(f"  Service account email: {email}")
            
            elif field == 'private_key':
                key = sa_data[field]
                if not key.startswith('-----BEGIN PRIVATE KEY-----'):
                    print_error("private_key doesn't start with proper header")
                    issues.append("Invalid private_key format")
                elif not key.strip().endswith('-----END PRIVATE KEY-----'):
                    print_error("private_key doesn't end with proper footer")
                    issues.append("Invalid private_key format")
                else:
                    print_success("Private key format looks correct")
    
    return issues

def test_streamlit_version():
    """Check Streamlit version"""
    print_header("Step 4: Checking Streamlit Version")
    
    try:
        import streamlit as st
        version = st.__version__
        print_info(f"Streamlit version: {version}")
        
        # Parse version
        major, minor, patch = version.split('.')[:3]
        major, minor = int(major), int(minor)
        
        if major > 1 or (major == 1 and minor >= 42):
            print_success(f"Streamlit version {version} supports native authentication")
            return True
        else:
            print_error(f"Streamlit version {version} is too old. Need >= 1.42.0")
            print_info("Upgrade with: pip install --upgrade 'streamlit>=1.42.0'")
            return False
    except Exception as e:
        print_error(f"Error checking Streamlit version: {e}")
        return False

def test_google_api_libraries():
    """Check if Google API libraries are installed"""
    print_header("Step 5: Checking Google API Libraries")
    
    required_libraries = [
        ('google.oauth2', 'google-auth'),
        ('google.auth.transport', 'google-auth-httplib2'),
        ('googleapiclient', 'google-api-python-client')
    ]
    
    all_ok = True
    for module_name, package_name in required_libraries:
        try:
            __import__(module_name)
            print_success(f"{package_name} is installed")
        except ImportError:
            print_error(f"{package_name} is NOT installed")
            print_info(f"  Install with: pip install {package_name}")
            all_ok = False
    
    return all_ok

def test_service_account_connection(secrets: Dict):
    """Test connection to Google Drive with service account"""
    print_header("Step 6: Testing Service Account Connection to Google Drive")
    
    if 'GOOGLE_SERVICE_ACCOUNT_JSON' not in secrets:
        print_error("Cannot test - service account not configured")
        return False
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        print_info("Attempting to create credentials...")
        sa_json = secrets['GOOGLE_SERVICE_ACCOUNT_JSON']
        if isinstance(sa_json, str):
            sa_data = json.loads(sa_json)
        else:
            sa_data = sa_json
        
        credentials = service_account.Credentials.from_service_account_info(
            sa_data,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        print_success("Credentials created successfully")
        
        print_info("Building Drive service...")
        service = build('drive', 'v3', credentials=credentials)
        print_success("Drive service built successfully")
        
        print_info("Testing Drive API access...")
        results = service.files().list(
            pageSize=1,
            fields="files(id, name)"
        ).execute()
        print_success("Successfully connected to Google Drive API!")
        
        # Check for Fieldmap folder
        print_info("Searching for 'Fieldmap' folder...")
        query = "name='Fieldmap' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, permissions)'
        ).execute()
        
        files = results.get('files', [])
        if files:
            print_success(f"Found Fieldmap folder: {files[0]['name']} (ID: {files[0]['id']})")
            print_info("Checking permissions...")
            try:
                permissions = service.permissions().list(fileId=files[0]['id']).execute()
                print_info(f"  Folder has {len(permissions.get('permissions', []))} permission(s)")
                for perm in permissions.get('permissions', []):
                    if perm.get('emailAddress') == sa_data.get('client_email'):
                        print_success(f"  Service account has {perm.get('role')} access")
            except Exception as e:
                print_warning(f"Could not check permissions: {e}")
        else:
            print_warning("Fieldmap folder not found in Drive")
            print_info("You need to:")
            print_info(f"  1. Create a folder named 'Fieldmap' in Google Drive")
            print_info(f"  2. Share it with the service account email: {sa_data.get('client_email')}")
            print_info(f"  3. Grant 'Editor' permission")
        
        return True
        
    except ImportError as e:
        print_error(f"Missing required library: {e}")
        return False
    except Exception as e:
        print_error(f"Failed to connect to Google Drive: {e}")
        print_info("Common causes:")
        print_info("  - Service account JSON is invalid or incomplete")
        print_info("  - Drive API is not enabled in Google Cloud Console")
        print_info("  - Network connectivity issues")
        return False

def test_auth_endpoint():
    """Test Google OIDC metadata endpoint"""
    print_header("Step 7: Testing Google OIDC Endpoint")
    
    try:
        import urllib.request
        
        url = "https://accounts.google.com/.well-known/openid-configuration"
        print_info(f"Fetching: {url}")
        
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
            print_success("Successfully connected to Google OIDC endpoint")
            print_info(f"  Authorization endpoint: {data.get('authorization_endpoint', 'N/A')[:60]}...")
            print_info(f"  Token endpoint: {data.get('token_endpoint', 'N/A')}")
            return True
    except Exception as e:
        print_error(f"Failed to connect to Google OIDC endpoint: {e}")
        print_info("This might indicate network connectivity issues")
        return False

def print_summary(all_issues: List[str]):
    """Print summary of all issues found"""
    print_header("SUMMARY")
    
    if not all_issues:
        print_success("All checks passed! Your configuration looks good.")
        print_info("\nIf you're still having signin issues:")
        print_info("  1. Ensure your redirect_uri in Google Cloud Console matches exactly")
        print_info("  2. Check that your OAuth consent screen is configured")
        print_info("  3. Verify you're using the correct Google account")
        print_info("  4. Try clearing browser cookies/cache")
        print_info("  5. Check browser console for JavaScript errors")
    else:
        print_error(f"Found {len(all_issues)} issue(s) that need to be fixed:\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        print_info("\n" + "="*80)
        print_info("NEXT STEPS:")
        print_info("  1. Fix the issues listed above")
        print_info("  2. Review docs/SETUP.md for detailed setup instructions")
        print_info("  3. Run this script again to verify fixes")
        print_info("  4. Restart your Streamlit app after fixing")

def main():
    """Main entry point"""
    print_header("FIELDMAP AUTHENTICATION DEBUGGER")
    print_info("This tool will help diagnose signin issues by validating your configuration.\n")
    
    all_issues = []
    
    # Step 1: Check secrets file
    has_secrets, secrets = check_secrets_file()
    if not has_secrets:
        all_issues.append("secrets.toml file not found or unreadable")
        print_summary(all_issues)
        sys.exit(1)
    
    # Step 2: Validate [auth] section
    auth_issues = validate_auth_section(secrets)
    all_issues.extend(auth_issues)
    
    # Step 3: Validate service account
    sa_issues = validate_service_account(secrets)
    all_issues.extend(sa_issues)
    
    # Step 4: Check Streamlit version
    if not test_streamlit_version():
        all_issues.append("Streamlit version too old (need >= 1.42.0)")
    
    # Step 5: Check Google API libraries
    if not test_google_api_libraries():
        all_issues.append("Missing required Google API libraries")
    
    # Step 6: Test service account connection (only if no major issues)
    if not sa_issues:
        if not test_service_account_connection(secrets):
            all_issues.append("Service account cannot connect to Google Drive")
    
    # Step 7: Test OIDC endpoint
    if not test_auth_endpoint():
        all_issues.append("Cannot reach Google OIDC endpoint (network issue?)")
    
    # Print summary
    print_summary(all_issues)
    
    # Exit with appropriate code
    sys.exit(0 if not all_issues else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDebug process interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
