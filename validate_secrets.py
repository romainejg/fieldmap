#!/usr/bin/env python3
"""
Quick secrets validator - checks if secrets.toml is properly formatted.
Useful for CI/CD pipelines or quick validation.
"""

import sys
import json
from pathlib import Path

def validate_secrets():
    """Validate secrets.toml file format and completeness."""
    
    secrets_path = Path(".streamlit/secrets.toml")
    
    if not secrets_path.exists():
        print("❌ ERROR: .streamlit/secrets.toml not found")
        print("   Create it from template: cp .streamlit/secrets.toml.template .streamlit/secrets.toml")
        return False
    
    print("✓ secrets.toml file exists")
    
    # Read and parse TOML
    try:
        import toml
    except ImportError:
        print("⚠️  WARNING: 'toml' package not installed. Install with: pip install toml")
        print("   Skipping TOML parsing validation")
        return True
    
    try:
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
        print("✓ secrets.toml is valid TOML format")
    except Exception as e:
        print(f"❌ ERROR: Failed to parse secrets.toml: {e}")
        return False
    
    # Validate [auth] section
    issues = []
    
    if 'auth' not in secrets:
        print("❌ ERROR: [auth] section missing")
        issues.append("[auth] section")
    else:
        print("✓ [auth] section present")
        
        required_auth_fields = ['redirect_uri', 'cookie_secret', 'client_id', 'client_secret', 'server_metadata_url']
        for field in required_auth_fields:
            if field not in secrets['auth']:
                print(f"  ❌ Missing: [auth].{field}")
                issues.append(f"[auth].{field}")
            elif not secrets['auth'][field] or secrets['auth'][field].startswith('<'):
                print(f"  ❌ Placeholder value in: [auth].{field}")
                issues.append(f"[auth].{field} (placeholder)")
            else:
                print(f"  ✓ [auth].{field} is set")
    
    # Validate service account
    if 'google_service_account' not in secrets:
        print("❌ ERROR: [google_service_account] section missing")
        issues.append("[google_service_account] section")
    else:
        print("✓ [google_service_account] section present")
        
        sa_data = secrets['google_service_account']
        
        # Validate it's a dict/table
        if not isinstance(sa_data, dict):
            print(f"  ❌ Service account should be a TOML table (e.g., [google_service_account]) not a string, got: {type(sa_data)}")
            issues.append("Service account format (should be TOML table)")
        else:
            print("  ✓ Service account is a TOML table")
            
            required_sa_fields = ['type', 'project_id', 'private_key', 'client_email']
            for field in required_sa_fields:
                if field not in sa_data:
                    print(f"    ❌ Missing: {field}")
                    issues.append(f"Service account: {field}")
                else:
                    print(f"    ✓ {field} present")
    
    # Summary
    print("\n" + "="*60)
    if not issues:
        print("✅ SUCCESS: All validations passed!")
        print("   Your secrets.toml appears to be properly configured.")
        print("\n   Next steps:")
        print("   1. Run the full diagnostics: python debug_auth.py")
        print("   2. Start the app: streamlit run app.py")
        return True
    else:
        print(f"❌ FAILED: Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"   - {issue}")
        print("\n   Fix these issues, then run this script again.")
        print("   For detailed help, run: python debug_auth.py")
        return False

if __name__ == "__main__":
    try:
        success = validate_secrets()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
