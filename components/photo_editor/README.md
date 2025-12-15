# Photo Editor Component

A custom Streamlit component that integrates marker.js for photo annotation.

## Overview

This component allows users to edit photos directly by drawing annotations on them. It uses the marker.js 2 library to provide a rich set of annotation tools including freehand drawing, arrows, shapes, and text.

## Architecture

### Frontend (`components/photo_editor/frontend/index.html`)
- Loads marker.js 2 from CDN
- Automatically opens marker.js editor when photo loads
- Provides annotation tools: Freehand, Arrow, Line, Text, Ellipse, Frame
- On save, exports the annotated image as a PNG data URL
- Returns the result to Python via `Streamlit.setComponentValue()`

### Backend (`components/photo_editor/__init__.py`)
- `photo_editor(image, key)`: Main component function
  - Accepts a PIL Image
  - Converts to PNG and base64 encodes it
  - Passes to frontend as data URL
  - Returns editor result when user saves/cancels
  
- `decode_image_from_dataurl(data_url)`: Helper function
  - Decodes a data URL back to PIL Image
  - Used to convert the edited image from marker.js

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
Uses `streamlit.components.v1.declare_component()` with a local path to the frontend directory.

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
- **Frontend**: marker.js 2 (via CDN), streamlit-component-lib (via CDN)
- **Backend**: streamlit>=1.28, Pillow

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
