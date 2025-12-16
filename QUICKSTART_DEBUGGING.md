# Quick Start: Debugging Signin Issues

If you're experiencing signin issues with Fieldmap, follow these steps:

## Step 1: Run the Diagnostic Script

The fastest way to identify issues is to run the automated diagnostic:

```bash
cd /path/to/fieldmap
python debug_auth.py
```

This will check:
- ✓ Secrets file configuration
- ✓ Authentication settings
- ✓ Service account setup
- ✓ Google API connectivity
- ✓ Streamlit version compatibility

The script will tell you exactly what's wrong and how to fix it.

## Step 2: Review the Output

The script uses color coding:
- 🟢 **Green ✓**: Everything is configured correctly
- 🔴 **Red ✗**: Problem detected (needs fixing)
- 🟡 **Yellow ⚠**: Warning (should check)
- 🔵 **Blue ℹ**: Information (helpful hint)

## Step 3: Fix Issues

Follow the suggestions in the output. Common fixes:

### Missing secrets file
```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Then edit the file with your credentials
```

### Placeholder values
Edit `.streamlit/secrets.toml` and replace all `<...>` values with real credentials.

### Wrong Streamlit version
```bash
pip install --upgrade 'streamlit>=1.42.0'
```

### Service account issues
1. Download service account JSON from Google Cloud Console
2. Copy entire contents into `GOOGLE_SERVICE_ACCOUNT_JSON` in secrets.toml
3. Share "Fieldmap" folder in Drive with the service account email

## Step 4: Check In-App Debugger

After starting the app:

```bash
streamlit run app.py
```

1. Navigate to the **About** page
2. Scroll to the signin section
3. Look for **"🔍 Debug Information"** expander
4. Click to see detailed runtime diagnostics

This shows:
- Current authentication status
- Available Streamlit auth attributes
- Secrets configuration
- Service account details
- Troubleshooting checklist

## Step 5: Review Logs

Watch the terminal output when running the app. Look for messages like:

```
✓ Service account parsed successfully. Email: your-sa@project.iam.gserviceaccount.com
✓ All authentication configuration checks passed
✓ Google Drive storage (service account) initialized successfully
```

Or error messages like:

```
✗ [auth] section not found in secrets
✗ Failed to connect to Google Drive API
⚠️ Service account not configured
```

## Need More Help?

See the full debugging guide: [DEBUGGING.md](DEBUGGING.md)

It includes:
- Complete troubleshooting workflow
- Solutions for all common issues
- Advanced debugging techniques
- How to collect diagnostic information for support

## Quick Reference

| Issue | Solution |
|-------|----------|
| No login button | Check Streamlit version >= 1.42.0 |
| redirect_uri_mismatch | Match Google Cloud Console exactly |
| Service account error | Verify JSON and Drive folder sharing |
| Configuration errors | Run `python debug_auth.py` |
| Drive connection fails | Enable Drive API, check permissions |

## Emergency Fallback

For testing/development only, the app includes a "Manual Login (Dev Only)" button that bypasses authentication. This should NOT be used in production.

---

**Still stuck?** Create a GitHub issue with:
1. Output from `python debug_auth.py`
2. Relevant log messages (redact secrets!)
3. What you've already tried
