"""
Storage abstraction layer for photo persistence.
Supports local folder storage and prepares for future Google Photos integration.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
import io
from typing import Optional


class PhotoStorage(ABC):
    """Abstract base class for photo storage backends"""
    
    @abstractmethod
    def save_image(self, session_name: str, photo_id: int, pil_image: Image.Image) -> str:
        """
        Save an image to storage.
        
        Args:
            session_name: Name of the session
            photo_id: Unique photo ID
            pil_image: PIL Image object to save
        
        Returns:
            URI or path to the saved image
        """
        pass
    
    @abstractmethod
    def load_image(self, uri: str) -> Image.Image:
        """
        Load an image from storage.
        
        Args:
            uri: URI or path to the image
        
        Returns:
            PIL Image object
        """
        pass
    
    @abstractmethod
    def delete_image(self, uri: str) -> bool:
        """
        Delete an image from storage.
        
        Args:
            uri: URI or path to the image
        
        Returns:
            True if successful, False otherwise
        """
        pass


class LocalFolderStorage(PhotoStorage):
    """Local filesystem storage implementation"""
    
    def __init__(self, base_path: str = "./data"):
        """
        Initialize local folder storage.
        
        Args:
            base_path: Base directory for storing photos (default: ./data)
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_image(self, session_name: str, photo_id: int, pil_image: Image.Image) -> str:
        """
        Save an image to local filesystem.
        
        Args:
            session_name: Name of the session
            photo_id: Unique photo ID
            pil_image: PIL Image object to save
        
        Returns:
            File path to the saved image
        """
        # Create session directory if it doesn't exist
        session_dir = self.base_path / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as PNG
        file_path = session_dir / f"photo_{photo_id}.png"
        
        # Ensure image is in RGB mode before saving
        if pil_image.mode not in ('RGB', 'RGBA'):
            pil_image = pil_image.convert('RGB')
        
        pil_image.save(file_path, format='PNG')
        
        return str(file_path)
    
    def load_image(self, uri: str) -> Image.Image:
        """
        Load an image from local filesystem.
        
        Args:
            uri: File path to the image
        
        Returns:
            PIL Image object
        """
        file_path = Path(uri)
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found at {uri}")
        
        return Image.open(file_path)
    
    def delete_image(self, uri: str) -> bool:
        """
        Delete an image from local filesystem.
        
        Args:
            uri: File path to the image
        
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(uri)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False


class GooglePhotosStorage(PhotoStorage):
    """
    Google Photos storage implementation.
    NOT IMPLEMENTED YET - placeholder for future functionality.
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Photos storage.
        
        Args:
            credentials_path: Path to Google Photos API credentials
        """
        raise NotImplementedError("Google Photos storage is not yet implemented")
    
    def save_image(self, session_name: str, photo_id: int, pil_image: Image.Image) -> str:
        """Save image to Google Photos (not implemented)"""
        raise NotImplementedError("Google Photos storage is not yet implemented")
    
    def load_image(self, uri: str) -> Image.Image:
        """Load image from Google Photos (not implemented)"""
        raise NotImplementedError("Google Photos storage is not yet implemented")
    
    def delete_image(self, uri: str) -> bool:
        """Delete image from Google Photos (not implemented)"""
        raise NotImplementedError("Google Photos storage is not yet implemented")
