# Fieldmap - Cadaver Lab Photo Annotation App

A mobile-optimized Streamlit web application designed for biomedical engineers working in cadaver labs. This app allows users to capture photos, annotate them, add comments, organize them into sessions, and export data to Excel.

## Features

### 📸 Photo Capture
- Take photos directly using your mobile device camera
- Upload existing images from your device
- **Automatic save** to current session - no save button needed!
- Immediate preview with annotation options

### 📝 Comments & Drawing
- Add descriptive notes/comments to each photo
- Edit comments at any time
- **Draw directly on photos** with simple annotation tools:
  - ↗️ Arrows for pointing
  - ⭕ Circles for highlighting areas
  - ⬜ Boxes for marking regions
  - 📝 Text labels for notes
- Customize drawing color and line width
- Position control slider for precise placement
- Reset button to remove all annotations and restore original
- Annotations are permanently applied to the image

### 🗂️ Session Management
- Create multiple sessions for different experiments or procedures
- Organize photos into sessions
- Move photos between sessions
- Session selector integrated with camera for easy organization

### 🖼️ Gallery View
- Browse all photos or filter by session
- **iPhone-style thumbnail grid** for easy browsing
- **Quick move** dropdown to reorganize photos between sessions
- Click to view/edit full photo details
- Manage photos: edit comments, draw, move, delete

### 📊 Excel Export
- Export all photos, comments, and drawing status to Excel
- Includes session information and timestamps
- Easy data analysis and record-keeping

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/romainejg/fieldmap.git
cd fieldmap
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your default web browser. For mobile use, access the URL shown in the terminal from your mobile device (ensure both devices are on the same network).

### For Production/Remote Access

To make the app accessible from other devices:
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

### Mobile Optimization

The app is designed with mobile-first principles:
- Responsive layout that adapts to screen size
- Large touch-friendly buttons
- Camera integration for direct photo capture on mobile devices
- Collapsed sidebar to maximize screen space

## How to Use

### 1. Create a Session
- Open the sidebar (☰ icon)
- Click "Create New Session"
- Enter a session name (e.g., "Experiment 1", "Procedure A")
- Click "Create Session"

### 2. Capture Photos
- Go to the "Camera" tab
- The active session is displayed at the top
- Use "Take a photo" to capture with your camera
- OR use "Upload from Device" to select existing images
- **Photo saves automatically** to the current session
- **Click "Clear Camera - Take Another Photo"** to take a new photo
- **Immediately add notes or draw** on the preview:
  - Add or edit comments/notes
  - Add annotations: arrows, circles, boxes, or text labels
  - Choose colors and line widths
  - Use position slider to place annotations
  - Click "Add Annotation" to apply (builds up multiple annotations)
  - Use "Reset All Annotations" to restore original photo
  - Move photo to a different session if needed

### 3. View and Manage Photos
- Go to the "Gallery" tab
- Filter by session or view all photos
- Browse photos in a **compact 3-column thumbnail grid**
- For each photo, you can:
  - Use **Quick Move dropdown** to reorganize between sessions
  - **Click "View/Edit"** to expand full details
  - View the full image and metadata
  - Compare original vs annotated versions side-by-side
  - Edit the notes/comments
  - **Add annotations** directly on photos (arrows, circles, boxes, text)
  - Customize drawing colors and line widths
  - Reset to remove all annotations and restore original
  - Delete the photo
  - Delete the photo

### 4. Export Data
- Open the sidebar
- Click "Export to Excel"
- Click "Download Excel File"
- The Excel file contains all photos' metadata, comments, and drawing status

## File Structure

```
fieldmap/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## Dependencies

- **streamlit**: Web application framework
- **Pillow**: Image processing and annotation
- **pandas**: Data manipulation
- **openpyxl**: Excel file creation

## Mobile Usage Tips

1. **Add to Home Screen**: On mobile browsers, you can add the app to your home screen for quick access
2. **Landscape Mode**: Works in both portrait and landscape orientations
3. **Camera Permissions**: Allow camera access when prompted for the camera feature to work
4. **Offline**: Photos are stored in the browser session (not permanently). Export to Excel regularly for backup

## Data Persistence

**Important**: Data is stored in the Streamlit session state and will be lost when:
- The browser is closed
- The session times out
- The server is restarted

**Best Practice**: Export your data to Excel regularly to preserve your work!

## Future Enhancements

Potential features for future versions:
- Database backend for permanent storage
- User authentication
- Cloud storage integration
- PDF report generation
- Image metadata extraction
- More advanced annotation tools (freehand drawing, polygons)
- Batch annotation operations

## Troubleshooting

### Camera not working
- Ensure you've granted camera permissions in your browser
- Try using the "Upload from Device" option instead
- Check if HTTPS is enabled (required for camera access on some browsers)

### App is slow
- Reduce image size before uploading
- Export and clear old sessions regularly
- Check your internet connection

### Export not working
- Ensure you have photos in at least one session
- Try refreshing the page
- Check browser console for errors

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available for use in academic and research settings.

## Support

For issues or questions, please open an issue on the GitHub repository.

---

**Developed for biomedical engineers and researchers working in cadaver labs and similar settings.**