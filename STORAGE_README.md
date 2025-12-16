# Storage Module

This module provides an abstraction layer for photo persistence in the Fieldmap application.

## Overview

The storage module separates photo data from storage implementation. Fieldmap currently uses Google Drive as the exclusive storage backend.

## Current Implementation

### GoogleDriveStorage

Stores photos in Google Drive under `Fieldmap/<session_name>/photo_<id>.png`

**Features:**
- OAuth 2.0 Web Application authentication
- Automatic folder creation and management
- File ID tracking for efficient updates
- Limited scope (only accesses files it creates)

**Example:**
```python
from storage import GoogleDriveStorage
from PIL import Image

# Initialize storage with OAuth credentials
storage = GoogleDriveStorage(credentials)

# Save an image
image = Image.new('RGB', (100, 100), color='blue')
uri = storage.save_image('session1', 1, image)
# Returns: Google Drive URI with file ID

# Load an image
loaded = storage.load_image(uri)

# Delete an image
storage.delete_image(uri)
```

## Photo Storage Integration

The storage abstraction is integrated with SessionStore:

1. Photos are stored both in memory (PIL Image) and in Google Drive
2. Each photo has a `storage_uri` and `file_id` for Drive tracking
3. Photos are automatically saved when added or updated
4. Photos are loaded from Drive when needed

## Storage Abstraction

The `PhotoStorage` abstract base class defines the interface:

```python
class PhotoStorage(ABC):
    @abstractmethod
    def save_image(self, session_name: str, photo_id: int, pil_image: Image.Image) -> str:
        """Save image and return storage URI"""
        pass
    
    @abstractmethod
    def load_image(self, uri: str) -> Image.Image:
        """Load image from storage URI"""
        pass
    
    @abstractmethod
    def delete_image(self, uri: str) -> bool:
        """Delete image from storage"""
        pass
```

This abstraction allows for future storage backends while maintaining a consistent interface.

## Design Principles

- **Cloud-first**: Google Drive is the primary storage for persistence
- **Abstract interface**: Easy to add new storage backends if needed
- **Dual storage**: Photos kept in memory for performance, Drive for persistence
- **Error handling**: Graceful degradation if storage operations fail
- **Security**: OAuth-based authentication, limited API scope
