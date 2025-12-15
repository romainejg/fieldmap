# Photo Editor Component

A custom Streamlit component that integrates marker.js for photo annotation.

## Overview

This component allows users to edit photos directly by drawing annotations on them. It uses the marker.js 2 library to provide a rich set of annotation tools including freehand drawing, arrows, shapes, and text.

## Architecture

### Frontend Build Structure

The frontend is now a properly bundled Streamlit component:

- **Source**: `components/photo_editor/frontend/src/`
  - `index.html` - HTML template with CDN-loaded marker.js
  - `index.js` - Main JavaScript with Streamlit integration
  
- **Build Output**: `components/photo_editor/frontend/build/`
  - `index.html` - Minified HTML
  - `main.js` - Webpack bundled JavaScript with streamlit-component-lib
  - `main.js.LICENSE.txt` - License information

### Frontend Features
- Integrates with Streamlit using `streamlit-component-lib`
- Loads marker.js 2 from CDN (with integrity hash for security)
- Automatically opens marker.js editor when photo loads
- Provides annotation tools: Freehand, Arrow, Line, Text, Ellipse, Frame
- On save, exports the annotated image as a PNG data URL
- Returns the result to Python via `Streamlit.setComponentValue()`
- Dynamic frame height adjustment based on image size

### Backend (`components/photo_editor/__init__.py`)
- `photo_editor(image, key)`: Main component function
  - Accepts a PIL Image
  - Converts to PNG and base64 encodes it
  - Passes to frontend as data URL
  - Uses build directory when available, falls back to dev directory
  - Returns editor result when user saves/cancels
  
- `decode_image_from_dataurl(data_url)`: Helper function
  - Decodes a data URL back to PIL Image
  - Used to convert the edited image from marker.js

## Building the Frontend

To rebuild the frontend after making changes:

```bash
cd components/photo_editor/frontend
npm install
npm run build
```

The build artifacts in `frontend/build/` are committed to the repository, so the component works immediately on Streamlit Cloud without requiring a build step during deployment.

## Integration in app.py

The component is integrated into both the FieldmapPage and GalleryPage classes:

```python
from components.photo_editor import photo_editor, decode_image_from_dataurl

# In FieldmapPage.render():
# The editor automatically opens when a photo is captured
editor_result = photo_editor(
    image=last_photo['current_image'],
    key=f"photo_editor_{last_photo['id']}"
)

if editor_result is not None:
    if editor_result.get('saved') and editor_result.get('pngDataUrl'):
        edited_image = decode_image_from_dataurl(editor_result['pngDataUrl'])
        last_photo['current_image'] = edited_image
        last_photo['has_annotations'] = True

# In GalleryPage._render_photo_details():
# User clicks "Edit Photo" button to open editor
if st.session_state[f'show_gallery_editor_{photo["id"]}']:
    editor_result = photo_editor(
        image=photo['current_image'],
        key=f"photo_editor_gallery_{photo['id']}"
    )
    # Similar handling as above
```

## User Flow

1. User takes a photo with camera or selects a photo from gallery
2. Photo is saved to session storage with both `original_image` and `current_image`
3. Photo editor (marker.js) automatically opens showing the current photo
4. User draws annotations using available tools (freehand, arrows, shapes, text)
5. User clicks "Save" in marker.js editor
6. Annotated image is returned to Python
7. Photo's `current_image` is updated with annotations (original remains untouched)
8. `has_annotations` flag is set to `True`
9. User can reset to restore the original image at any time

## Key Features

- ✅ User draws directly on the photo (not on separate canvas)
- ✅ Rich set of annotation tools via marker.js
- ✅ Returns edited PNG image (not just metadata)
- ✅ Photo editor automatically opens when photo is captured
- ✅ Supports cancel operation
- ✅ Preserves image quality and dimensions
- ✅ Mobile-friendly interface
- ✅ No button clicks required - streamlined workflow

## Technical Details

### Component Declaration
Uses `streamlit.components.v1.declare_component()` with the build directory path for production:

```python
from pathlib import Path
import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent
_BUILD_DIR = _COMPONENT_DIR / "frontend" / "build"
_DEV_DIR = _COMPONENT_DIR / "frontend"

# Use build directory if it exists, otherwise use dev directory
if _BUILD_DIR.exists():
    _component_func = components.declare_component("photo_editor", path=str(_BUILD_DIR))
else:
    _component_func = components.declare_component("photo_editor", path=str(_DEV_DIR))
```

### Data Flow
1. Python → Frontend: Base64-encoded PNG data URL
2. Frontend → Python: Edited image as PNG data URL with metadata
   ```javascript
   {
       pngDataUrl: "data:image/png;base64,...",
       saved: true
   }
   ```

### Dependencies
- **Frontend**: 
  - marker.js 2 (via CDN with integrity hash)
  - streamlit-component-lib (bundled via webpack)
  - React (bundled via webpack)
  - Apache Arrow (for dataframe support)
- **Backend**: 
  - streamlit>=1.28
  - Pillow

## Error Handling

- Validates data URL format in `decode_image_from_dataurl()`
- Handles image loading errors in frontend
- Gracefully handles cancel operation
- Try-catch wrapper in app.py for decoding errors

## Future Enhancements

Potential improvements:
- Add undo/redo functionality
- Save annotation state separately
- Support for multiple annotation layers
- Export annotations as JSON metadata
- Configurable tool palette
