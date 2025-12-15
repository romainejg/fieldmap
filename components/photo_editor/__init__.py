"""
Photo Editor Component
A Streamlit custom component that uses marker.js to edit photos.
"""

import streamlit.components.v1 as components
import os
from PIL import Image
import base64
import io

# Get the absolute path to the frontend directory
_COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))
_FRONTEND_DIR = os.path.join(_COMPONENT_DIR, "frontend")

# Declare the component
_component_func = components.declare_component(
    "photo_editor",
    path=_FRONTEND_DIR,
)


def photo_editor(image, key=None):
    """
    Display a photo editor component that allows users to annotate images using marker.js.
    
    Args:
        image: PIL Image object to edit
        key: Optional unique key for this component instance
    
    Returns:
        dict or None: 
            - If user saves: {'pngDataUrl': 'data:image/png;base64,...', 'saved': True}
            - If user cancels: {'pngDataUrl': None, 'saved': False, 'cancelled': True}
            - If no action yet: None
    """
    # Convert PIL image to PNG bytes
    img_byte_arr = io.BytesIO()
    
    # Ensure image is in RGB mode
    if image.mode not in ('RGB', 'RGBA'):
        image = image.convert('RGB')
    
    # Save as PNG
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # Base64 encode
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    
    # Create data URL
    image_data = f"data:image/png;base64,{img_base64}"
    
    # Call the component
    component_value = _component_func(
        image_data=image_data,
        key=key,
        default=None
    )
    
    return component_value


def decode_image_from_dataurl(data_url):
    """
    Decode a data URL to a PIL Image.
    
    Args:
        data_url: String in format "data:image/png;base64,..."
    
    Returns:
        PIL Image object
    """
    if not data_url or not data_url.startswith('data:image'):
        raise ValueError("Invalid data URL")
    
    # Extract base64 data after the comma
    base64_data = data_url.split(',', 1)[1]
    
    # Decode base64 to bytes
    image_bytes = base64.b64decode(base64_data)
    
    # Convert to PIL Image
    image = Image.open(io.BytesIO(image_bytes))
    
    return image
