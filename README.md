# Fieldmap - Photo Documentation for Cadaver Lab

A mobile-optimized Streamlit web app for biomedical engineers to capture, annotate, and organize photos with Google Drive cloud storage.

## 🎯 Key Features

- **📸 Photo Capture**: Take photos directly from the camera
- **✏️ Annotation Tools**: Draw, add shapes (including unfilled circles), and annotate photos
- **📝 Derived Photos**: Edits create new copies, keeping originals unchanged
- **📁 Session Organization**: Organize photos into named sessions
- **🔄 Drag & Drop**: Reorganize photos between sessions in the gallery
- **☁️ Google Drive Storage**: Automatic cloud backup (required)
- **📊 Excel Export**: Export photo metadata and comments to Excel
- **🖼️ Gallery View**: Thumbnail tiles with click-to-expand details
- **🔐 Secure OAuth**: Web application OAuth flow with secrets management

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Cloud account with Drive API enabled
- OAuth 2.0 Web Application credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/romainejg/fieldmap.git
cd fieldmap

# Install dependencies
pip install -r requirements.txt
```

### Setup

**For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**

Quick overview:
1. Create OAuth Web Application credentials in Google Cloud Console
2. Set up secrets (Streamlit Cloud or local `.streamlit/secrets.toml`)
3. Run the app and sign in with Google

### Local Development

```bash
# Set OAuth state secret for secure callback validation
export OAUTH_STATE_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Create secrets file
mkdir -p .streamlit
cat > .streamlit/secrets.toml << EOF
GOOGLE_OAUTH_CLIENT_JSON = '''
{
  "web": {
    "client_id": "YOUR_CLIENT_ID",
    ...
  }
}
'''
GOOGLE_REDIRECT_URI = "http://localhost:8501"
OAUTH_STATE_SECRET = "$OAUTH_STATE_SECRET"
EOF

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📖 Usage

### Basic Workflow

1. **Sign In**: Click "Sign in with Google" in the sidebar
2. **Take Photo**: Use the camera input to capture a photo
3. **Add Notes**: Write comments/descriptions for the photo
4. **Annotate**: Use the photo editor to add drawings and annotations
   - Freehand drawing
   - Arrows and lines
   - Unfilled circles/ellipses
   - Unfilled rectangles
   - Text labels
5. **Save**: Annotations are saved as a new photo (original unchanged)
6. **Organize**: Drag photos between sessions in the Gallery
7. **Export**: Download Excel file with all photo metadata

### How Photo Editing Works

When you edit a photo, Fieldmap creates a **new annotated copy** while preserving the original:

- ✅ **Original Photo** (ID: 1) - Remains unchanged in Google Drive
- ✅ **Annotated Copy** (ID: 2) - Links back to original via `source_photo_id`
- ✅ **Multiple Edits** - Create multiple derived photos from the same original
- ✅ **Provenance Tracking** - Always know which original a photo came from
- ✅ **Cloud Backup** - All versions automatically saved to Google Drive

### Gallery Organization

- **Draggable Tiles**: Drag photo thumbnail tiles between session containers
- **Click to Expand**: Click any photo to view full details
- **Variant Badges**: Annotated photos show a 📝 badge
- **Source Tracking**: Derived photos display "Derived from Photo #X"

## ☁️ Google Drive Integration

### Architecture

- **Storage**: Google Drive is the **only** storage backend (no local-only mode)
- **OAuth**: Web Application flow (not Desktop app)
- **Credentials**: Loaded from secrets (not committed files)
- **File Organization**: `Google Drive/Fieldmap/<SessionName>/photo_<ID>.png`
- **Token Storage**: Session state (not filesystem)

### Security Features

- ✅ No credentials in repository
- ✅ OAuth 2.0 Web flow with CSRF protection
- ✅ Limited scope: Only files created by app
- ✅ Tokens not persisted to disk
- ✅ Secrets managed via Streamlit Cloud or local secrets file

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete setup instructions.

## 🏗️ Architecture

### Data Model

Photos are stored with these fields:

```python
{
    'id': int,                    # Unique photo ID
    'original_image': Image,      # PIL Image object
    'current_image': Image,       # PIL Image object
    'thumbnail': Image,           # 100x100 thumbnail
    'thumb_data_url': str,        # Base64 data URL for gallery tiles
    'comment': str,               # User notes
    'timestamp': str,             # ISO format
    'has_annotations': bool,      # Whether photo is edited
    'source_photo_id': int|None,  # Original photo ID (for derived)
    'variant': str,               # 'original' or 'annotated'
    'storage_uri': str|None,      # Cloud storage URI
    'file_id': str|None          # Google Drive file ID
}
```

### Storage Abstraction

All photos are stored in Google Drive using the `GoogleDriveStorage` backend:

- **GoogleDriveStorage**: Save to Google Drive with OAuth2 (required)
- **LocalFolderStorage**: Deprecated (not exposed to users)

### Components

- **SessionStore**: Manages sessions and photo CRUD operations
- **FieldmapPage**: Camera capture and photo editing
- **GalleryPage**: Photo organization with draggable tiles
- **AboutPage**: App information and setup guides
- **GoogleAuthHelper**: OAuth2 Web Application authentication flow

## 🧪 Testing

### Unit Tests

Run all tests:

```bash
python test_derived_photos.py      # Storage tests
python test_integration.py         # Workflow tests
python test_photo_editor_component.py  # Component tests
python test_google_oauth_state.py  # OAuth state signing/verification tests
```

All tests should pass with backward compatibility for existing photos.

### Testing OAuth State Security

To test the stateless OAuth state flow locally:

```bash
# 1. Set up OAuth state secret
export OAUTH_STATE_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export OAUTH_STATE_MAX_AGE=300

# 2. Set up OAuth credentials (if not already in secrets.toml)
export GOOGLE_CLIENT_ID="your-client-id"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export APP_BASE_URL="http://localhost:8501"

# 3. Run the app
streamlit run app.py

# 4. Test the OAuth flow
# - Click "Sign in with Google"
# - Complete the OAuth consent flow
# - Verify successful authentication even if session state is reset
```

**To simulate session loss**:
1. Start the OAuth flow (click "Sign in with Google")
2. In a new browser tab, navigate directly to the app root to reset session state
3. Complete the OAuth consent in the original tab
4. The callback should succeed due to stateless signed state verification

**Expected logs**:
- "Generated signed OAuth state token" when initiating auth
- "Verified signed OAuth state token" when callback succeeds
- No "No oauth_state found in session_state" errors

## 📁 Project Structure

```
fieldmap/
├── app.py                      # Main application
├── storage.py                  # Storage abstraction layer
├── google_auth.py              # Google OAuth2 helper
├── google_oauth.py             # OAuth flow implementation
├── requirements.txt            # Python dependencies
├── components/
│   └── photo_editor/          # Custom Streamlit component
│       ├── __init__.py
│       └── frontend/          # marker.js integration
├── assets/
│   └── logo.png               # App logo
├── test_derived_photos.py
├── test_integration.py
├── test_google_oauth_state.py
├── test_photo_editor_component.py
├── GOOGLE_DRIVE_SETUP.md      # Google Drive setup guide
├── STORAGE_README.md          # Storage module docs
├── SETUP_GUIDE.md             # Complete setup guide
├── TESTING_GUIDE.md           # Testing instructions
└── .gitignore
```

## 🔐 Security

- **OAuth2 Authentication**: Secure Google sign-in with stateless signed state tokens
- **CSRF Protection**: Cryptographically signed, time-limited state tokens prevent CSRF attacks
- **Stateless Verification**: OAuth callbacks work even when session state is lost
- **Limited Scope**: App only accesses files it creates
- **No Plaintext Credentials**: Uses tokens, not passwords
- **Gitignored Secrets**: `credentials.json` and `token.pickle` excluded
- **Local-First**: Photos stored in memory by default

## 🛠️ Configuration

### Environment Variables

#### OAuth State Security (Required for Production)

For secure, stateless OAuth callback validation:

```bash
# Generate and set OAuth state secret (required for production)
export OAUTH_STATE_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Optional: Set OAuth state token max age in seconds (default: 300 = 5 minutes)
export OAUTH_STATE_MAX_AGE=300
```

**Why this matters**: The OAuth state secret is used to cryptographically sign state tokens, enabling stateless verification that works even when session state is lost across redirects. This prevents "No oauth_state found in session_state" errors.

**For local development**: If not set, the app generates a random dev-only secret (but this won't work across app restarts).

**For production (Streamlit Cloud)**: Add these to your app's secrets in Streamlit Cloud settings.

#### Google Credentials (Optional)

```bash
# Set custom credentials path
export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json

# Set custom token path
export GOOGLE_TOKEN_PATH=/path/to/token.pickle
```

### Streamlit Configuration

Edit `.streamlit/config.toml`:

```toml
[server]
port = 8501
headless = true

[theme]
primaryColor = "#4CAF50"
```

## 📝 Development

### Adding a New Storage Backend

1. Extend `PhotoStorage` abstract class in `storage.py`
2. Implement `save_image()`, `load_image()`, `delete_image()`
3. Update `App.__init__()` to support new backend
4. Add configuration option in sidebar

Example:

```python
class S3Storage(PhotoStorage):
    def save_image(self, session_name, photo_id, pil_image):
        # Upload to S3
        return f"s3://{bucket}/{key}"
    
    def load_image(self, uri):
        # Download from S3
        return Image.open(...)
    
    def delete_image(self, uri):
        # Delete from S3
        return True
```

### Running in Production

```bash
# Install production server
pip install streamlit

# Run with production settings
streamlit run app.py --server.port 80 --server.headless true
```

## 📊 Performance

- **In-Memory Storage**: Fast access, limited by RAM
- **Cloud Storage**: Persistent, scalable, slight upload latency
- **Thumbnails**: Pre-generated 100x100 for gallery performance
- **Lazy Loading**: Images loaded on-demand for large sessions

## 🐛 Troubleshooting

### "Credentials file not found"

Download OAuth2 credentials from Google Cloud Console and save as `credentials.json`.

### "Module not found" errors

```bash
pip install -r requirements.txt
```

### Photos not saving to Google Drive

1. Check authentication status in sidebar
2. Verify "Save photos to Google Drive" is enabled
3. Check internet connection
4. Verify Google Drive API is enabled in Cloud Console

### App won't start

```bash
# Check Python version (requires 3.8+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

- **marker.js**: Photo annotation library
- **Streamlit**: Web app framework
- **Google Drive API**: Cloud storage
- **streamlit-sortables**: Drag & drop functionality

## 📞 Support

For issues or questions:

1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for setup instructions
2. Review [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) for Google Drive issues
3. Check [TESTING_GUIDE.md](TESTING_GUIDE.md) for testing guidance
4. Open an issue on GitHub

## 🗺️ Roadmap

Future enhancements:

- [ ] Google Photos API integration
- [ ] Multi-device photo sync
- [ ] Collaborative sessions
- [ ] Advanced search and filtering
- [ ] Batch operations
- [ ] Photo comparison view
- [ ] Export to PDF with annotations
- [ ] Mobile app (React Native)

---

**Version**: 3.0  
**Last Updated**: 2024-12-15  
**Maintained by**: romainejg
