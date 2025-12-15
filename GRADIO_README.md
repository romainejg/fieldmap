# Gradio Editor App

## Overview

This is a Gradio-based photo editor application that replaces the Streamlit canvas-based drawing system with Gradio's native `ImageEditor` component for more reliable photo annotation.

## Why Gradio ImageEditor?

The Streamlit `st_canvas` component has known reliability issues with background images, especially in deployed/multipage contexts. Gradio's `ImageEditor` provides:

- ✅ Built-in image editing with brushes, shapes, and layers
- ✅ Photo remains visible as the editable surface at all times
- ✅ Returns the edited image directly (not just metadata)
- ✅ Better stability in production deployments
- ✅ Mobile-friendly interface

## Running the App

### Option 1: Run the standalone Gradio editor

```bash
python editor_app.py
```

The app will be available at `http://localhost:7860`

### Option 2: Run the full Gradio app (migration)

```bash
python gradio_app.py
```

This is a complete migration of the Streamlit app to Gradio, including all features:
- Session management
- Camera capture
- Photo gallery
- Comments and metadata
- Excel export

## Features

### Capture & Edit Tab
- **Camera Capture**: Use your webcam to take photos
- **Photo Editor**: Draw annotations directly on images using Gradio's ImageEditor
  - Freehand drawing
  - Shapes and lines
  - Text annotations  
  - Crop and transform
- **Comments**: Add notes and descriptions to photos

### Gallery Tab
- View all captured photos
- See edit history
- Quick access to all images

### Export Tab
- Export all photos and metadata to Excel format
- Includes timestamps, comments, and edit status

## Integration Options

### Option A: Full Migration (Recommended)
Use `gradio_app.py` as the main application. This provides the most stable experience with all features migrated to Gradio.

### Option B: Hybrid Approach
Keep the existing Streamlit app (`app.py`) for the main interface and use `editor_app.py` as a separate service for photo editing:

1. Run `editor_app.py` on a different port (e.g., 7860)
2. From Streamlit, provide a link/button to open the Gradio editor
3. Use shared storage (disk/S3/database) to exchange photos between apps
4. Streamlit reloads updated photos after editing

### Option C: Editor Component Only
Use `editor_app.py` as a minimal starting point and integrate Gradio ImageEditor into your existing workflow.

## Dependencies

```
gradio>=4.0.0
Pillow>=10.2.0
pandas>=2.0.0
openpyxl>=3.1.0
numpy
```

Install with:
```bash
pip install -r requirements.txt
```

## Architecture

### PhotoSession Class
Manages photo storage and operations:
- `add_photo()`: Store captured images
- `get_photo()`: Retrieve photos by ID
- `update_image()`: Save edited versions
- Photo metadata tracking (timestamps, edit status, comments)

### ImageEditor Integration
The Gradio `ImageEditor` component:
- Accepts PIL Images or numpy arrays
- Returns edited image as dict with 'background' and 'layers'
- Supports all standard image editing operations
- Mobile-responsive design

## Comparison: Streamlit vs Gradio

| Feature | Streamlit (Current) | Gradio (New) |
|---------|---------------------|--------------|
| Drawing Tool | st_canvas (marker.js) | ImageEditor (native) |
| Background Image | Reliability issues | Stable |
| Mobile Support | Limited | Excellent |
| Deployment | Complex | Simple |
| Image Output | Data URL conversion | Direct PIL Image |
| Edit Tools | Custom component | Built-in |

## Migration Notes

The Gradio version preserves all functionality from the Streamlit app:

1. **Session Management** → Supported in `gradio_app.py`
2. **Camera Capture** → `gr.Image(sources=["webcam"])`
3. **Photo Annotation** → `gr.ImageEditor`
4. **Gallery** → `gr.Gallery` with thumbnails
5. **Comments** → `gr.Textbox` inputs
6. **Export** → Excel export via `pandas`

## Known Issues

- The Gradio API info generation may show warnings about type checking, but these don't affect functionality
- In sandboxed environments, you may need to use `share=True` for external access

## Future Enhancements

Potential improvements:
- Batch photo editing
- Undo/redo support
- Annotation layers export
- Cloud storage integration
- Advanced filtering and search

## Support

For issues related to:
- **Gradio ImageEditor**: See [Gradio documentation](https://www.gradio.app/docs/gradio/imageeditor)
- **Streamlit canvas issues**: See [community discussions](https://discuss.streamlit.io/)
- **This app**: Open an issue in the repository
