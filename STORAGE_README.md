# Storage Module

This module provides an abstraction layer for photo persistence in the Fieldmap application.

## Overview

The storage module separates photo data from storage implementation, allowing the application to support multiple storage backends:
- **LocalFolderStorage**: Stores photos as PNG files in local directories
- **GooglePhotosStorage**: (Future) Will support Google Photos API integration

## Current Implementation

### LocalFolderStorage

Stores photos in the local filesystem under `./data/<session_name>/photo_<id>.png`

**Example:**
```python
from storage import LocalFolderStorage
from PIL import Image

# Initialize storage
storage = LocalFolderStorage(base_path="./data")

# Save an image
image = Image.new('RGB', (100, 100), color='blue')
uri = storage.save_image('session1', 1, image)
# Returns: './data/session1/photo_1.png'

# Load an image
loaded = storage.load_image(uri)

# Delete an image
storage.delete_image(uri)
```

## Future Integration

The storage abstraction is designed to be pluggable. To integrate storage with SessionStore:

1. Add storage backend to SessionStore initialization
2. Store URIs in photo data instead of PIL Image objects
3. Use storage.save_image() when photos are added
4. Use storage.load_image() when photos need to be displayed

This keeps the in-memory PIL Images for backward compatibility while allowing optional persistence.

## Google Photos Integration (Future)

To add Google Photos support:

1. Implement GooglePhotosStorage class
2. Use Google Photos API for upload/download
3. Store photo metadata and Google Photos IDs
4. Handle authentication and permissions

## Design Principles

- **Backward compatible**: Existing code works without changes
- **Abstract interface**: Easy to swap storage backends
- **Minimal dependencies**: Each backend has its own dependencies
- **Error handling**: Graceful degradation if storage fails
