# How to Use the Debugging Tools - Example Walkthrough

This document shows a real-world example of using the debugging tools to identify and fix signin issues.

## Scenario: User Can't Sign In

You've set up Fieldmap but signin isn't working. Here's how to use the debugging tools.

## Step 1: Run the Diagnostic Script

Open your terminal in the fieldmap directory and run:

```bash
python debug_auth.py
```

### Example Output (With Issues)

```
================================================================================
                        FIELDMAP AUTHENTICATION DEBUGGER                        
================================================================================

ℹ This tool will help diagnose signin issues by validating your configuration.

================================================================================
                         Step 1: Checking Secrets File                          
================================================================================

✓ secrets.toml found at: /path/to/fieldmap/.streamlit/secrets.toml
✓ Successfully loaded secrets using Streamlit

================================================================================
                      Step 2: Validating [auth] Configuration                   
================================================================================

✓ [auth] section found
✗ Field 'cookie_secret' has placeholder value: <generate-a-long-random-secret-here>
✓ Field 'redirect_uri' is configured
  ℹ Value: http://localhost:8501/oauth2callback
✓ Field 'client_id' is configured
  ℹ Value: 123456789-abcdefg.apps.googleusercontent.com
✓ Field 'client_secret' is configured
✓ Field 'server_metadata_url' is configured

================================================================================
                  Step 3: Validating Service Account Configuration              
================================================================================

✓ GOOGLE_SERVICE_ACCOUNT_JSON found
✓ Service account JSON is valid
✓ Field 'type' is present
✓ Field 'project_id' is present
✓ Field 'private_key_id' is present
✓ Field 'private_key' is present
✓ Private key format looks correct
✓ Field 'client_email' is present
  ℹ Service account email: fieldmap@myproject.iam.gserviceaccount.com
✓ Field 'client_id' is present

================================================================================
                        Step 4: Checking Streamlit Version                      
================================================================================

ℹ Streamlit version: 1.42.0
✓ Streamlit version 1.42.0 supports native authentication

================================================================================
                    Step 5: Checking Google API Libraries                       
================================================================================

✓ google-auth is installed
✓ google-auth-httplib2 is installed
✓ google-api-python-client is installed

================================================================================
              Step 6: Testing Service Account Connection to Google Drive        
================================================================================

ℹ Attempting to create credentials...
✓ Credentials created successfully
ℹ Building Drive service...
✓ Drive service built successfully
ℹ Testing Drive API access...
✓ Successfully connected to Google Drive API!
ℹ Searching for 'Fieldmap' folder...
⚠ Fieldmap folder not found in Drive
ℹ You need to:
ℹ   1. Create a folder named 'Fieldmap' in Google Drive
ℹ   2. Share it with the service account email: fieldmap@myproject.iam.gserviceaccount.com
ℹ   3. Grant 'Editor' permission

================================================================================
                    Step 7: Testing Google OIDC Endpoint                        
================================================================================

ℹ Fetching: https://accounts.google.com/.well-known/openid-configuration
✓ Successfully connected to Google OIDC endpoint
ℹ   Authorization endpoint: https://accounts.google.com/o/oauth2/v2/auth...
ℹ   Token endpoint: https://oauth2.googleapis.com/token

================================================================================
                                    SUMMARY                                     
================================================================================

✗ Found 2 issue(s) that need to be fixed:

  1. Placeholder value in: cookie_secret
  2. Service account cannot connect to Google Drive

ℹ ================================================================================
ℹ NEXT STEPS:
ℹ   1. Fix the issues listed above
ℹ   2. Review docs/SETUP.md for detailed setup instructions
ℹ   3. Run this script again to verify fixes
ℹ   4. Restart your Streamlit app after fixing
```

## Step 2: Fix the Issues

Based on the output, we need to:

### Issue 1: Generate cookie_secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output (e.g., `dQw4w9WgXcQ-xyzABC123...`) and paste it into `.streamlit/secrets.toml`:

```toml
[auth]
cookie_secret = "dQw4w9WgXcQ-xyzABC123..."  # Use the actual generated value
```

### Issue 2: Share Fieldmap folder with service account

1. Open Google Drive
2. Create a folder named "Fieldmap" (if it doesn't exist)
3. Right-click the folder → Share
4. Add email: `fieldmap@myproject.iam.gserviceaccount.com`
5. Set permission to "Editor"
6. Uncheck "Notify people"
7. Click "Share"

## Step 3: Re-run the Diagnostic

```bash
python debug_auth.py
```

### Example Output (All Fixed)

```
================================================================================
                        FIELDMAP AUTHENTICATION DEBUGGER                        
================================================================================

... (all steps show ✓) ...

================================================================================
                                    SUMMARY                                     
================================================================================

✓ All checks passed! Your configuration looks good.

ℹ If you're still having signin issues:
ℹ   1. Ensure your redirect_uri in Google Cloud Console matches exactly
ℹ   2. Check that your OAuth consent screen is configured
ℹ   3. Verify you're using the correct Google account
ℹ   4. Try clearing browser cookies/cache
ℹ   5. Check browser console for JavaScript errors
```

## Step 4: Start the App

```bash
streamlit run app.py
```

Watch the terminal output:

```
2024-12-16 18:00:00 - __main__ - INFO - ================================================================================
2024-12-16 18:00:00 - __main__ - INFO - Fieldmap Application Starting
2024-12-16 18:00:00 - __main__ - INFO - ================================================================================
2024-12-16 18:00:01 - __main__ - INFO - Initializing Fieldmap application
2024-12-16 18:00:01 - __main__ - INFO - Service account JSON found in secrets
2024-12-16 18:00:01 - __main__ - INFO - Service account parsed successfully. Email: fieldmap@myproject.iam.gserviceaccount.com
2024-12-16 18:00:01 - __main__ - INFO - Attempting to initialize Google Drive storage...
2024-12-16 18:00:02 - __main__ - INFO - ✓ Google Drive storage (service account) initialized successfully
2024-12-16 18:00:02 - __main__ - INFO - ✓ Successfully connected to Google Drive API
2024-12-16 18:00:02 - __main__ - INFO - ✓ Application initialization complete

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

## Step 5: Test Signin

1. Open browser to `http://localhost:8501`
2. You should see the About page
3. Look for Streamlit's "Log in" button in the top-right corner
4. Click it to start the OAuth flow
5. Sign in with your Google account
6. After successful authentication, you'll be redirected back to the app
7. The About page should now show "✅ Signed In" with your email

## Using the In-App Debugger

If signin still doesn't work after all checks pass:

1. Navigate to the About page
2. Scroll to the signin section
3. Click the "🔍 Debug Information" expander

You'll see:

```
Streamlit Version: 1.42.0

Authentication Attributes:
- hasattr(st, 'experimental_user'): True
- hasattr(st, 'user'): False
- st.experimental_user: None

Secrets Check:
- 'auth' in st.secrets: True
- client_id present: True
- client_secret present: True
- redirect_uri: http://localhost:8501/oauth2callback

Service Account:
- Service account email: fieldmap@myproject.iam.gserviceaccount.com
- Project ID: myproject-12345

Troubleshooting Steps:
1. Run the diagnostic script: python debug_auth.py
2. Check browser console (F12) for JavaScript errors
...
```

## Common Next Issues

### OAuth Consent Screen Not Configured

**Error in browser:** "Error 400: redirect_uri_mismatch"

**Fix:**
1. Go to Google Cloud Console
2. APIs & Services → Credentials
3. Click on your OAuth client
4. Add `http://localhost:8501/oauth2callback` to Authorized redirect URIs
5. Save

### App is in Testing Mode

**Error:** "This app isn't verified"

**Fix (for development):**
1. Click "Advanced" or "Show details"
2. Click "Go to Fieldmap (unsafe)"
3. Proceed with signin

**Fix (for production):**
1. Complete OAuth app verification with Google
2. Or set User Type to "Internal" (if using Google Workspace)

### Still Not Working?

1. Check browser console (F12) for errors
2. Review detailed logs in terminal
3. Consult `DEBUGGING.md` for more solutions
4. Create GitHub issue with:
   - Output from `python debug_auth.py`
   - Browser console errors
   - Terminal log output

## Success!

Once signed in:
- ✅ Your email appears on the About page
- ✅ Fieldmap and Gallery pages are accessible in sidebar
- ✅ You can take photos and annotate them
- ✅ Photos are automatically saved to Google Drive

## Quick Reference Commands

```bash
# Diagnose configuration issues
python debug_auth.py

# Quick validation
python validate_secrets.py

# Generate cookie secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Run the app
streamlit run app.py

# Check Streamlit version
streamlit --version

# Upgrade Streamlit
pip install --upgrade 'streamlit>=1.42.0'
```

## Documentation Index

- **Complete setup:** `docs/SETUP.md`
- **Troubleshooting guide:** `DEBUGGING.md`
- **Quick reference:** `QUICKSTART_DEBUGGING.md`
- **Implementation details:** `IMPLEMENTATION_SUMMARY.md`
- **This guide:** `EXAMPLE_USAGE.md`

---

**Remember:** The debugging tools are your friend! Always run `python debug_auth.py` first when you encounter issues.
