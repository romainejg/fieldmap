# Fieldmap - Photo Documentation for Cadaver Lab

A mobile-optimized Streamlit web app for biomedical engineers to capture, annotate, and organize photos with Google Drive cloud storage.

## 🎯 Key Features

- **📸 Photo Capture**: Take photos directly from the camera
- **✏️ Annotation Tools**: Draw, add shapes, and annotate photos
- **📝 Derived Photos**: Edits create new copies, keeping originals unchanged
- **📁 Session Organization**: Organize photos into named sessions
- **🔄 Drag & Drop**: Reorganize photos between sessions in the gallery
- **☁️ Google Drive Storage**: Automatic cloud backup via service account (required)
- **📊 Excel Export**: Export photo metadata and comments to Excel
- **🖼️ Gallery View**: Thumbnail tiles with click-to-expand details
- **🔐 Streamlit Native Auth**: Simple Google OIDC login with `st.login()` / `st.logout()`

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Streamlit >= 1.42.0 (for native authentication)
- Google Cloud account with Drive API enabled
- Google OAuth 2.0 Web Application credentials (for user identity)
- Google Service Account (for Drive storage)

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
1. Create Google OAuth 2.0 Web Application credentials (for user identity)
2. Create Google Service Account (for Drive storage)
3. Share "Fieldmap" Drive folder with service account email
4. Configure secrets in `.streamlit/secrets.toml` or Streamlit Cloud
5. Run the app and sign in with Google using Streamlit's native auth

### Local Development

```bash
# Create secrets file from template
cp .streamlit/secrets.toml.template .streamlit/secrets.toml

# Edit .streamlit/secrets.toml with your credentials:
# - [auth] section with OAuth Web App credentials
# - GOOGLE_SERVICE_ACCOUNT_JSON with service account JSON

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

See [docs/SETUP.md](docs/SETUP.md) for complete setup instructions.

## 📖 Usage

### Basic Workflow

1. **Sign In**: Click "Sign in with Google" on the About page (uses Streamlit's native auth)
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

- **Authentication**: Streamlit-native OAuth/OIDC for user identity (no Drive scopes)
- **Storage**: Google service account for server-to-server Drive access
- **Organization**: All photos in shared `Fieldmap/<SessionName>/photo_<ID>.png` folder
- **Access**: Service account has Editor permission on shared "Fieldmap" folder
- **No Dual OAuth**: Users only authenticate once (for identity, not Drive)

### Security Features

- ✅ No credentials in repository
- ✅ Streamlit native auth with Google OIDC
- ✅ Service account isolation (only shared folder access)
- ✅ No user Drive OAuth flow needed
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
    'storage_uri': str|None,      # Cloud storage URI
    'file_id': str|None          # Google Drive file ID
}
```

### Storage Abstraction

All photos are stored in Google Drive using the `GoogleDriveStorage` backend:

- **GoogleDriveStorage**: Save to Google Drive with service account (required)
- No local storage option available

### Components

- **SessionStore**: Manages sessions and photo CRUD operations
- **FieldmapPage**: Camera capture and photo editing
- **GalleryPage**: Photo organization with draggable tiles
- **AboutPage**: Login gate with Streamlit native auth and app information
- **GoogleDriveStorage**: Service account-based Drive storage

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

- **Streamlit Native Auth**: Built-in Google OIDC authentication
- **Service Account**: Server-to-server Drive access (no user OAuth for storage)
- **Isolated Access**: Service account only accesses shared "Fieldmap" folder
- **Cookie-Based Sessions**: Secure session management with secrets
- **No Plaintext Credentials**: All credentials in Streamlit secrets
- **Gitignored Secrets**: `.streamlit/secrets.toml` excluded from repo

## 🛠️ Configuration

All configuration is done via `.streamlit/secrets.toml` (local) or Streamlit Cloud Secrets (production).

### Required Secrets

```toml
[auth]
redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"
cookie_secret = "<generate-random-secret>"
client_id = "<oauth-client-id>"
client_secret = "<oauth-client-secret>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# IMPORTANT: Use triple double quotes ("""), NOT triple single quotes (''')
GOOGLE_SERVICE_ACCOUNT_JSON = """<service-account-json>"""
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

### Adding a New Storage Backend

Google Drive via service account is the only supported backend. To add another:

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

**Having signin issues?** Run the diagnostic script:

```bash
python debug_auth.py
```

This automated script will diagnose configuration issues and provide specific solutions.

### Quick Fixes

#### "Service account not configured"

Add `GOOGLE_SERVICE_ACCOUNT_JSON` to `.streamlit/secrets.toml`. See [docs/SETUP.md](docs/SETUP.md).

#### "Could not connect to Google Drive"

1. Verify Drive API is enabled in Google Cloud Console
2. Check service account has Editor access to "Fieldmap" folder
3. Ensure service account JSON is complete and valid

Run `python debug_auth.py` for detailed diagnostics.

#### "Login button doesn't appear"

1. Ensure Streamlit >= 1.42.0: `pip install --upgrade streamlit>=1.42.0`
2. Verify [auth] section in `.streamlit/secrets.toml` is complete
3. Check redirect_uri matches exactly in Google Cloud Console
4. Restart the app

Run `python debug_auth.py` for detailed diagnostics.

#### "Module not found" errors

```bash
pip install -r requirements.txt
```

### Debugging Tools

1. **Automated diagnostics:** `python debug_auth.py`
2. **Setup guide:** [docs/SETUP.md](docs/SETUP.md)

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
3. Open an issue on GitHub

## 🗺️ Roadmap

Future enhancements:

- [ ] Role-based access control using st.user.email
- [ ] Multi-device photo sync (already supported via Drive)
- [ ] Collaborative sessions with sharing
- [ ] Advanced search and filtering
- [ ] Batch operations
- [ ] Photo comparison view
- [ ] Export to PDF with annotations

---

**Version**: 4.0 (Streamlit Native Auth + Service Account)  
**Last Updated**: 2024-12-16  
**Maintained by**: romainejg
