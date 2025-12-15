# Fieldmap - Photo Documentation for Cadaver Lab

A mobile-optimized Streamlit web app for biomedical engineers to capture, annotate, and organize photos with optional Google Drive cloud storage.

## 🎯 Key Features

- **📸 Photo Capture**: Take photos directly from the camera
- **✏️ Annotation Tools**: Draw, add shapes, and annotate photos using marker.js
- **📝 Derived Photos**: Edits create new copies, keeping originals unchanged
- **📁 Session Organization**: Organize photos into named sessions
- **🔄 Drag & Drop**: Reorganize photos between sessions
- **☁️ Google Drive Integration**: Optional cloud storage with OAuth2 authentication
- **📊 Excel Export**: Export photo metadata and comments to Excel
- **🖼️ Gallery View**: Click-to-expand photo details with source tracking

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/romainejg/fieldmap.git
cd fieldmap

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage

### Basic Workflow

1. **Take Photo**: Use the camera input to capture a photo
2. **Add Notes**: Write comments/descriptions for the photo
3. **Annotate**: Use the photo editor to add drawings and annotations
4. **Save**: Annotations are saved as a new photo (original unchanged)
5. **Organize**: Drag photos between sessions in the Gallery
6. **Export**: Download Excel file with all photo metadata

### How Photo Editing Works

When you edit a photo, Fieldmap creates a **new annotated copy** while preserving the original:

- ✅ **Original Photo** (ID: 1) - Remains unchanged
- ✅ **Annotated Copy** (ID: 2) - Links back to original via `source_photo_id`
- ✅ **Multiple Edits** - Create multiple derived photos from the same original
- ✅ **Provenance Tracking** - Always know which original a photo came from

### Gallery Organization

- **Draggable Board**: Drag photo tiles between session containers
- **Click to Expand**: Click any photo tile to view full details
- **Variant Badges**: Annotated photos show a 📝 badge
- **Source Tracking**: Derived photos display "Derived from Photo #X"

## ☁️ Google Drive Integration

### Setup

1. **Create Google Cloud Project** and enable Drive API
2. **Download OAuth2 credentials** as `credentials.json`
3. **Place credentials** in the app directory
4. **Sign in** using the sidebar button
5. **Enable cloud storage** with the toggle switch

See [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) for detailed instructions.

### How It Works

- Photos saved to `Google Drive/Fieldmap/<SessionName>/photo_<ID>.png`
- OAuth2 authentication (no API keys or passwords)
- Limited scope: Only accesses files the app creates
- Automatic upload when photos are taken or edited

## 🏗️ Architecture

### Data Model

Photos are stored with these fields:

```python
{
    'id': int,                    # Unique photo ID
    'original_image': Image,      # PIL Image object
    'current_image': Image,       # PIL Image object
    'thumbnail': Image,           # 100x100 thumbnail
    'comment': str,               # User notes
    'timestamp': str,             # ISO format
    'has_annotations': bool,      # Whether photo is edited
    'source_photo_id': int|None,  # Original photo ID (for derived)
    'variant': str,               # 'original' or 'annotated'
    'storage_uri': str|None       # Cloud storage URI (if enabled)
}
```

### Storage Abstraction

Pluggable storage backends via `PhotoStorage` interface:

- **LocalFolderStorage**: Save to local `./data/` folder
- **GoogleDriveStorage**: Save to Google Drive with OAuth2
- **GooglePhotosStorage**: Placeholder for future implementation

### Components

- **SessionStore**: Manages sessions and photo CRUD operations
- **FieldmapPage**: Camera capture and photo editing
- **GalleryPage**: Photo organization and management
- **AboutPage**: App information and setup guides
- **GoogleAuthHelper**: OAuth2 authentication flow

## 🧪 Testing

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
├── app.py                      # Main application
├── storage.py                  # Storage abstraction layer
├── google_auth.py              # Google OAuth2 helper
├── requirements.txt            # Python dependencies
├── components/
│   └── photo_editor/          # Custom Streamlit component
│       ├── __init__.py
│       └── frontend/          # marker.js integration
├── assets/
│   └── logo.png               # App logo
├── tests/
│   ├── test_derived_photos.py
│   ├── test_integration.py
│   └── test_photo_editor_component.py
├── docs/
│   ├── GOOGLE_DRIVE_SETUP.md  # Google Drive setup guide
│   ├── STORAGE_README.md      # Storage module docs
│   └── IMPLEMENTATION_SUMMARY.md  # Implementation details
└── .gitignore
```

## 🔐 Security

- **OAuth2 Authentication**: Secure Google sign-in
- **Limited Scope**: App only accesses files it creates
- **No Plaintext Credentials**: Uses tokens, not passwords
- **Gitignored Secrets**: `credentials.json` and `token.pickle` excluded
- **Local-First**: Photos stored in memory by default

## 🛠️ Configuration

### Environment Variables (Optional)

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

1. Check [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md) for Google Drive issues
2. Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details
3. Open an issue on GitHub

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
