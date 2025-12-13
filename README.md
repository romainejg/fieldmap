# Fieldmap - Cadaver Lab Photo Annotation App

A mobile-optimized Streamlit web application designed for biomedical engineers working in cadaver labs. This app allows users to capture photos, annotate them, add comments, organize them into sessions, and export data to Excel.

## Features

### 📸 Photo Capture
- Take photos directly using your mobile device camera
- Upload existing images from your device
- **Automatic save** to current session - no save button needed!
- Immediate preview with annotation options

### 📝 Annotation & Comments
- Add descriptive comments to each photo
- Add multiple annotations with timestamps
- Edit comments at any time
- **Draw on photos** with circles, arrows, rectangles, and freehand drawing
- Customize drawing color and line width
- Save and clear drawing annotations

### 🗂️ Session Management
- Create multiple sessions for different experiments or procedures
- Organize photos into sessions
- Move photos between sessions
- Session selector integrated with camera for easy organization

### 🖼️ Gallery View
- Browse all photos or filter by session
- View photos in a mobile-friendly grid layout
- Manage photos: edit, move, delete

### 📊 Excel Export
- Export all photos, comments, and annotations to Excel
- Includes session information, timestamps, and annotation counts
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
- **Immediately annotate or draw** on the preview:
  - Add or edit comments
  - Add quick annotations
  - Draw with various tools (freehand, arrows, boxes, circles)
  - Choose colors and line widths
  - Move photo to a different session if needed

### 3. View and Manage Photos
- Go to the "Gallery" tab
- Filter by session or view all photos
- See photo count, annotations, and drawing status at a glance
- For each photo, you can:
  - **Click "View Details"** for full information
  - **Quick Move** to organize photos between sessions
  - View the image and metadata
  - Edit the comment
  - Add text annotations
  - **Draw on photos** with various tools (circles, arrows, rectangles, freehand)
  - Customize drawing colors and line widths
  - Save or clear drawing annotations
  - Delete the photo

### 4. Export Data
- Open the sidebar
- Click "Export to Excel"
- Click "Download Excel File"
- The Excel file contains all photos' metadata, comments, and annotations

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
- **Pillow**: Image processing
- **pandas**: Data manipulation
- **openpyxl**: Excel file creation
- **streamlit-drawable-canvas**: For potential drawing features

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
- Export drawings as overlaid images

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