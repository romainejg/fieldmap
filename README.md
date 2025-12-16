# Fieldmap - Photo Documentation for Cadaver Lab

A mobile-optimized Streamlit web app for biomedical engineers to capture, annotate, and organize photos with Google Drive cloud storage.

## 🎯 Key Features

- **📸 Photo Capture**: Take photos directly from the camera
- **✏️ Annotation Tools**: Draw, add shapes, and annotate photos with MarkerJS 3
- **📝 Derived Photos**: Edits create new copies, keeping originals unchanged
- **📁 Session Organization**: Organize photos into named sessions (albums)
- **🔄 Drag & Drop**: Reorganize photos between sessions in the gallery
- **☁️ Google Drive Storage**: Photos stored in YOUR Google Drive (no quota issues)
- **📊 Excel Export**: Export photo metadata and comments to Excel
- **🖼️ Gallery View**: Thumbnail tiles with click-to-expand details
- **🔐 User OAuth**: Sign in with Google to access your Drive

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Streamlit >= 1.42.0
- Google Cloud account with Drive API enabled
- Google OAuth 2.0 Web Application credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/romainejg/fieldmap.git
cd fieldmap

# Install dependencies
pip install -r requirements.txt
```

### Setup

**For detailed setup instructions, see [docs/SETUP.md](docs/SETUP.md)**

Quick overview:
1. Create Google OAuth 2.0 Web Application credentials in Google Cloud Console
2. Configure secrets in `.streamlit/secrets.toml` or Streamlit Cloud
3. Run the app and sign in with Google
4. Photos will be uploaded to a "Fieldmap" folder in your Google Drive

### Local Development

```bash
# Create secrets file from template
cp .streamlit/secrets.toml.template .streamlit/secrets.toml

# Edit .streamlit/secrets.toml with your credentials:
# - [auth] section with OAuth Web App credentials
# - Set redirect_uri to http://localhost:8501/oauth2callback for local dev

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

See [docs/SETUP.md](docs/SETUP.md) for complete setup instructions.

## 📖 Usage

### Basic Workflow

1. **Sign In**: Click "Sign in with Google" on the About page
2. **Take Photo**: Use the camera input to capture a photo
3. **Add Notes**: Write comments/descriptions for the photo
4. **Annotate**: Use the photo editor to add drawings and annotations
5. **Save**: Annotations are saved as a new photo (original unchanged, both stored in Drive)
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

- **Authentication**: User OAuth for Google Drive access
- **Storage**: Photos uploaded to user's own Google Drive (no quota issues)
- **Organization**: All photos in `Fieldmap/<SessionName>/photo_<ID>.png` folder
- **Access**: User has full control - photos are in their own Drive

### How It Works

1. User signs in with Google OAuth
2. App requests Drive file creation permissions
3. App creates/finds "Fieldmap" folder in user's Drive
4. Session folders are created as subfolders (e.g., "Fieldmap/Default/")
5. Photos uploaded directly to user's Drive
6. Thumbnails generated from Drive API
7. Drag-and-drop updates folder parents in Drive

### Security Features

- ✅ No credentials in repository
- ✅ User OAuth with Google OIDC
- ✅ Photos stored in user's own Drive
- ✅ Minimal permissions (drive.file scope only)
- ✅ Secrets managed via Streamlit Cloud or local secrets file
- ✅ Cookie-based session with secure secrets

See [docs/SETUP.md](docs/SETUP.md) for complete setup instructions.

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
    'storage_uri': str|None,      # Cloud storage URI (gdrive://file_id)
    'file_id': str|None          # Google Drive file ID
}
```

### Storage

All photos are stored in Google Drive using user OAuth:

- **GoogleDriveStorage**: Save to user's Google Drive with OAuth tokens
- No local storage option - Drive is mandatory
- Photos uploaded to user's own Drive (no quota issues)

### Components

- **SessionStore**: Manages sessions and photo CRUD operations
- **FieldmapPage**: Camera capture and photo editing with MarkerJS 3
- **GalleryPage**: Photo organization with draggable tiles
- **AboutPage**: Clean sign-in page with Google OAuth
- **GoogleDriveStorage**: User OAuth-based Drive storage
- **oauth_utils**: OAuth flow management and token handling

## 🧪 Testing

### Unit Tests

Run all tests:

```bash
python test_derived_photos.py      # Storage tests
python test_integration.py         # Workflow tests
python test_photo_editor_component.py  # Component tests
```

All tests should pass with backward compatibility for existing photos.

## 📁 Project Structure

```
fieldmap/
├── app.py                      # Main application with Streamlit-native auth
├── storage.py                  # Storage abstraction layer (service account)
├── requirements.txt            # Python dependencies
├── components/
│   └── photo_editor/          # Custom Streamlit component
│       ├── __init__.py
│       └── frontend/          # marker.js integration
├── assets/
│   ├── logo.png               # App logo
│   └── biomedical.jpg         # Hero image
├── docs/
│   └── SETUP.md               # Complete setup guide
├── test_derived_photos.py
├── test_integration.py
├── test_photo_editor_component.py
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.template  # Template for local secrets
└── .gitignore
```

## 🔐 Security

- **User OAuth**: Google OAuth 2.0 for Drive access
- **Drive File Scope**: Minimal permissions (drive.file scope only - app can only access files it creates)
- **User's Drive**: Photos stored in user's own Drive account
- **No Service Account**: No quota issues - users upload to their own storage
- **Cookie-Based Sessions**: Secure session management with secrets
- **No Plaintext Credentials**: All credentials in Streamlit secrets
- **Gitignored Secrets**: `.streamlit/secrets.toml` excluded from repo

## 🛠️ Configuration

All configuration is done via `.streamlit/secrets.toml` (local) or Streamlit Cloud Secrets (production).

### Required Secrets

```toml
[auth]
redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"  # or http://localhost:8501/oauth2callback for local
cookie_secret = "<generate-random-secret>"
client_id = "<oauth-client-id>"
client_secret = "<oauth-client-secret>"

# Optional: Specify an existing Drive folder ID
# DRIVE_ROOT_FOLDER_ID = "your-folder-id-here"
```

### Generate cookie_secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Streamlit Configuration

`.streamlit/config.toml`:

```toml
[server]
enableXsrfProtection = true
enableCORS = true

[theme]
primaryColor = "#4CAF50"
```

## 📝 Development

### OAuth Callback Page

The app uses a separate OAuth callback page at `/oauth2callback` to handle Google OAuth redirects:

1. User clicks "Sign in with Google" → Redirects to Google OAuth
2. User authorizes → Google redirects to `/oauth2callback?code=...`
3. Callback page exchanges code for tokens
4. Tokens saved in session state
5. User redirected back to main app

### Adding Features

To add new storage backends (though Drive is mandatory):

1. Extend `PhotoStorage` abstract class in `storage.py`
2. Implement `save_image()`, `load_image()`, `delete_image()`
3. Add `load_index()` and `save_index()` for metadata persistence
4. Update `App.__init__()` to support new backend

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

### Quick Fixes

#### "Failed to initiate sign-in"

1. Verify `[auth]` section exists in `.streamlit/secrets.toml`
2. Check `client_id` and `client_secret` are valid
3. Ensure `redirect_uri` matches your deployment URL:
   - Local: `http://localhost:8501/oauth2callback`
   - Production: `https://fieldmap.streamlit.app/oauth2callback`
4. Verify redirect URI is added to Google Cloud Console OAuth settings

#### "Gallery Unavailable"

After signing in, if Gallery shows as unavailable:
1. Click "Refresh Page" button
2. If issue persists, sign out and sign in again
3. Check browser console (F12) for errors

#### "OAuth state not found"

This means the OAuth flow was interrupted:
1. Clear browser cookies
2. Try signing in again
3. Ensure cookies are enabled in your browser

#### "Module not found" errors

```bash
pip install -r requirements.txt
```

### Google Cloud Console Setup

1. **Create OAuth 2.0 credentials**:
   - Go to Google Cloud Console → APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8501/oauth2callback` (for local dev)
     - `https://fieldmap.streamlit.app/oauth2callback` (for production)
   - Save client_id and client_secret to secrets.toml

2. **Enable Drive API**:
   - Go to APIs & Services → Library
   - Search for "Google Drive API"
   - Click "Enable"

3. **Configure OAuth consent screen**:
   - Go to APIs & Services → OAuth consent screen
   - Add your email as a test user (if in testing mode)
   - Configure app name, support email, etc.

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

1. Check [docs/SETUP.md](docs/SETUP.md) for complete setup instructions
2. Review troubleshooting section above
3. Check browser console (F12) for error messages
4. Open an issue on GitHub

## 🗺️ Roadmap

Future enhancements:

- [ ] Shared folders for team collaboration
- [ ] Multi-device photo sync (already supported via Drive)
- [ ] Advanced search and filtering
- [ ] Batch operations
- [ ] Photo comparison view
- [ ] Export to PDF with annotations
- [ ] Mobile app (PWA)

---

**Version**: 5.0 (User OAuth + Drive API)  
**Last Updated**: 2024-12-16  
**Maintained by**: romainejg
