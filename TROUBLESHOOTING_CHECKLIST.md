# Signin Troubleshooting Checklist

Use this checklist to systematically debug signin issues. Check off items as you verify them.

## Pre-Flight Checks

- [ ] Python 3.8+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Google Cloud project created
- [ ] Drive API enabled in Google Cloud Console
- [ ] OAuth 2.0 Web Application credentials created
- [ ] Service account created and JSON key downloaded

## Configuration Checks

### Secrets File

- [ ] `.streamlit/secrets.toml` file exists
- [ ] File is not empty
- [ ] File is valid TOML format
- [ ] File is in the correct location (`.streamlit/` directory)

### [auth] Section

- [ ] `[auth]` section exists in secrets.toml
- [ ] `redirect_uri` is set (not placeholder)
- [ ] `redirect_uri` ends with `/oauth2callback`
- [ ] `redirect_uri` matches environment:
  - Local: `http://localhost:8501/oauth2callback`
  - Production: `https://fieldmap.streamlit.app/oauth2callback`
- [ ] `cookie_secret` is set (not placeholder)
- [ ] `cookie_secret` is at least 32 characters
- [ ] `client_id` is set (not placeholder)
- [ ] `client_id` ends with `.apps.googleusercontent.com`
- [ ] `client_secret` is set (not placeholder)
- [ ] `server_metadata_url` is set to Google's OIDC URL

### Service Account

- [ ] `GOOGLE_SERVICE_ACCOUNT_JSON` exists in secrets.toml
- [ ] JSON is wrapped in triple quotes `'''...'''`
- [ ] JSON is valid (no copy/paste errors)
- [ ] `type` field equals `"service_account"`
- [ ] `project_id` matches your Google Cloud project
- [ ] `private_key` starts with `-----BEGIN PRIVATE KEY-----`
- [ ] `private_key` ends with `-----END PRIVATE KEY-----`
- [ ] `client_email` ends with `.iam.gserviceaccount.com`

## Google Cloud Console Checks

### OAuth Credentials

- [ ] OAuth 2.0 Web Application client exists
- [ ] Client ID matches what's in secrets.toml
- [ ] Authorized redirect URIs includes your redirect_uri
- [ ] No trailing slashes in redirect URIs
- [ ] OAuth consent screen is configured
- [ ] App name is set
- [ ] User support email is set
- [ ] For testing: You're added as a test user

### Service Account

- [ ] Service account exists in project
- [ ] JSON key has been downloaded
- [ ] Service account email is noted

### Google Drive

- [ ] "Fieldmap" folder exists in Drive
- [ ] Folder is shared with service account email
- [ ] Service account has "Editor" permission
- [ ] Share notification was disabled when sharing

## Software Checks

### Streamlit

- [ ] Streamlit version >= 1.42.0
  ```bash
  streamlit --version
  ```
- [ ] If too old, upgrade:
  ```bash
  pip install --upgrade 'streamlit>=1.42.0'
  ```

### Google API Libraries

- [ ] `google-auth` installed
- [ ] `google-auth-httplib2` installed
- [ ] `google-api-python-client` installed
- [ ] Verify all:
  ```bash
  pip list | grep google
  ```

## Diagnostic Tool Checks

- [ ] Run automated diagnostic:
  ```bash
  python debug_auth.py
  ```
- [ ] All checks pass (green ✓)
- [ ] No errors (red ✗) in output
- [ ] Review warnings (yellow ⚠) and address if needed

## Runtime Checks

### App Startup

- [ ] App starts without errors
- [ ] No exceptions in terminal output
- [ ] Log shows: "Application initialization complete"
- [ ] Log shows: "Google Drive storage initialized successfully"
- [ ] Log shows: "Successfully connected to Google Drive API"

### UI Checks

- [ ] About page loads
- [ ] No configuration error messages shown
- [ ] If errors shown, they're specific and actionable
- [ ] In-app debug panel (🔍 Debug Information) accessible
- [ ] Debug panel shows correct Streamlit version
- [ ] Debug panel shows auth attributes available
- [ ] Debug panel shows secrets configured

### Authentication Flow

- [ ] Streamlit "Log in" button appears
  - Check top-right corner
  - Check sidebar
- [ ] Clicking "Log in" opens Google signin
- [ ] Can select Google account
- [ ] OAuth consent screen appears (if in testing)
- [ ] Can grant permissions
- [ ] Redirected back to app after signin
- [ ] About page shows "✅ Signed In"
- [ ] User email is displayed
- [ ] Fieldmap and Gallery pages become accessible

## Browser Checks

- [ ] JavaScript is enabled
- [ ] Cookies are enabled
- [ ] Browser console (F12) shows no errors
- [ ] Network tab shows successful auth requests
- [ ] No CORS errors
- [ ] No CSP errors

### Try Different Browsers

- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### Clear Browser Data

- [ ] Cookies cleared
- [ ] Cache cleared
- [ ] Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
- [ ] Try incognito/private mode

## Network Checks

- [ ] Internet connection working
- [ ] Can access https://accounts.google.com
- [ ] Can access https://www.googleapis.com
- [ ] No firewall blocking Google domains
- [ ] No proxy issues

### Test Connectivity

```bash
# Test OIDC endpoint
curl https://accounts.google.com/.well-known/openid-configuration
```

- [ ] Returns JSON (not error)

## Common Fixes Applied

### Fixed placeholder values

- [ ] Generated new cookie_secret
- [ ] Replaced `<...>` values with real credentials

### Fixed redirect_uri issues

- [ ] Updated secrets.toml with correct URI
- [ ] Added URI to Google Cloud Console
- [ ] Restarted app after change

### Fixed service account

- [ ] Re-downloaded JSON key
- [ ] Copied complete JSON (no truncation)
- [ ] Shared Drive folder with service account

### Fixed Streamlit version

- [ ] Upgraded to >= 1.42.0
- [ ] Restarted app after upgrade

## Validation Steps

After making fixes:

- [ ] Re-run diagnostic: `python debug_auth.py`
- [ ] All checks pass
- [ ] Restart app: `streamlit run app.py`
- [ ] Check logs for errors
- [ ] Test signin flow end-to-end
- [ ] Verify can access Fieldmap page
- [ ] Take test photo
- [ ] Verify photo saved to Drive

## Still Not Working?

If all checks pass but signin still fails:

### Collect Information

- [ ] Save diagnostic output:
  ```bash
  python debug_auth.py > debug_output.txt 2>&1
  ```
- [ ] Save app logs (copy terminal output)
- [ ] Screenshot browser console errors (F12)
- [ ] Note exact error messages

### Review Documentation

- [ ] Read `DEBUGGING.md` completely
- [ ] Check `QUICKSTART_DEBUGGING.md`
- [ ] Review `EXAMPLE_USAGE.md`
- [ ] Consult `docs/SETUP.md`

### Get Help

- [ ] Search existing GitHub issues
- [ ] Create new issue with:
  - Debug output (`debug_output.txt`)
  - Relevant log messages (secrets redacted!)
  - Browser console errors
  - What you've tried
  - Environment details (OS, Python version, etc.)

## Quick Wins

Most common issues and their fixes:

| Issue | Fix | Check |
|-------|-----|-------|
| No login button | Upgrade Streamlit to >= 1.42.0 | ✓ |
| redirect_uri_mismatch | Match Google Console exactly | ✓ |
| Placeholder values | Replace all `<...>` in secrets | ✓ |
| Drive connection fails | Share folder with service account | ✓ |
| Old Streamlit | `pip install --upgrade streamlit` | ✓ |

## Success Criteria

You know everything is working when:

- ✅ `python debug_auth.py` shows all green ✓
- ✅ App starts without errors
- ✅ "Log in" button appears in UI
- ✅ Can sign in with Google account
- ✅ Email shown on About page after signin
- ✅ Can access Fieldmap and Gallery pages
- ✅ Can take and save photos
- ✅ Photos appear in Google Drive

## Notes Section

Use this space to track what you've tried:

```
Date: __________
Issue: _________________________________________________
Attempted Fix: _________________________________________
Result: ________________________________________________

Date: __________
Issue: _________________________________________________
Attempted Fix: _________________________________________
Result: ________________________________________________
```

---

**Remember:** Work through this checklist systematically. Don't skip steps!
