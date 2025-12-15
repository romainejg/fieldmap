# Photo Editor Component

A custom Streamlit component that integrates marker.js for photo annotation.

## Overview

This component allows users to edit photos directly by drawing annotations on them. It uses the marker.js 2 library to provide a rich set of annotation tools including freehand drawing, arrows, shapes, and text.

## Architecture

### Frontend (`components/photo_editor/frontend/index.html`)
- Loads marker.js 2 from CDN
- Displays the photo in an `<img>` element
- Launches marker.js editor when "Edit Photo" button is clicked
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

The component is integrated into the FieldmapPage class to replace the previous canvas-based drawing system:

```python
from components.photo_editor import photo_editor, decode_image_from_dataurl

# In FieldmapPage.render():
if st.session_state.show_editor:
    editor_result = photo_editor(
        image=last_photo['current_image'],
        key=f"photo_editor_{last_photo['id']}"
    )
    
    if editor_result is not None:
        if editor_result.get('saved') and editor_result.get('pngDataUrl'):
            edited_image = decode_image_from_dataurl(editor_result['pngDataUrl'])
            last_photo['current_image'] = edited_image
            last_photo['has_annotations'] = True
```

## User Flow

1. User takes a photo with camera
2. Photo is saved to session storage
3. User clicks "Edit Photo" button
4. marker.js editor opens showing the photo
5. User draws annotations using available tools
6. User clicks "Save" in marker.js editor
7. Annotated image is returned to Python
8. Photo is updated with annotations
9. `has_annotations` flag is set to `True`

## Key Features

- ✅ User draws directly on the photo (not on separate canvas)
- ✅ Rich set of annotation tools via marker.js
- ✅ Returns edited PNG image (not just metadata)
- ✅ Photo remains visible as canvas background at all times
- ✅ Supports cancel operation
- ✅ Preserves image quality and dimensions
- ✅ Mobile-friendly interface

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
