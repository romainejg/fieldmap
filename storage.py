"""
Storage abstraction layer for photo persistence.
Supports local folder storage and Google Drive integration.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
import io
from typing import Optional
import pickle
import os


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
    
    This is a PLACEHOLDER for future functionality.
    Google Photos integration is not yet implemented.
    
    When implemented, this class will:
    - Authenticate with Google Photos API using OAuth2
    - Upload images to Google Photos albums
    - Download images from Google Photos
    - Maintain metadata and sync state
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Photos storage.
        
        Args:
            credentials_path: Path to Google Photos API credentials (not used yet)
        
        Raises:
            NotImplementedError: This storage backend is not yet implemented
        """
        raise NotImplementedError(
            "Google Photos storage is not yet implemented. "
            "Use GoogleDriveStorage or LocalFolderStorage instead."
        )
    
    def save_image(self, session_name: str, photo_id: int, pil_image: Image.Image) -> str:
        """Save image to Google Photos (not implemented)"""
        raise NotImplementedError("Google Photos storage is not yet implemented")
    
    def load_image(self, uri: str) -> Image.Image:
        """Load image from Google Photos (not implemented)"""
        raise NotImplementedError("Google Photos storage is not yet implemented")
    
    def delete_image(self, uri: str) -> bool:
        """Delete image from Google Photos (not implemented)"""
        raise NotImplementedError("Google Photos storage is not yet implemented")


class GoogleDriveStorage(PhotoStorage):
    """
    Google Drive storage implementation.
    Stores photos in user's Google Drive using OAuth2 authentication.
    """
    
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.pickle'):
        """
        Initialize Google Drive storage.
        
        Args:
            credentials_path: Path to Google OAuth2 credentials JSON file
            token_path: Path to store/load authentication token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.folder_cache = {}  # Cache folder IDs
    
    def _get_service(self):
        """Get or create Google Drive service."""
        if self.service:
            return self.service
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError(
                "Google API libraries not installed. "
                "Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        creds = None
        # Load token if it exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Download OAuth2 credentials from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        return self.service
    
    def _get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Get or create a folder in Google Drive.
        
        Args:
            folder_name: Name of the folder
            parent_id: ID of parent folder (None for root)
        
        Returns:
            Folder ID
        """
        cache_key = f"{parent_id}:{folder_name}"
        if cache_key in self.folder_cache:
            return self.folder_cache[cache_key]
        
        service = self._get_service()
        
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            folder_id = files[0]['id']
        else:
            # Create folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            folder_id = folder.get('id')
        
        self.folder_cache[cache_key] = folder_id
        return folder_id
    
    def save_image(self, session_name: str, photo_id: int, pil_image: Image.Image) -> str:
        """
        Save an image to Google Drive.
        
        Args:
            session_name: Name of the session
            photo_id: Unique photo ID
            pil_image: PIL Image object to save
        
        Returns:
            Google Drive file ID
        """
        from googleapiclient.http import MediaIoBaseUpload
        
        service = self._get_service()
        
        # Get or create Fieldmap folder
        fieldmap_folder_id = self._get_or_create_folder('Fieldmap')
        
        # Get or create session folder
        session_folder_id = self._get_or_create_folder(session_name, fieldmap_folder_id)
        
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        if pil_image.mode not in ('RGB', 'RGBA'):
            pil_image = pil_image.convert('RGB')
        pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Upload file
        file_name = f'photo_{photo_id}.png'
        file_metadata = {
            'name': file_name,
            'parents': [session_folder_id]
        }
        
        media = MediaIoBaseUpload(img_byte_arr, mimetype='image/png', resumable=True)
        
        # Check if file already exists
        query = f"name='{file_name}' and '{session_folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            # Update existing file
            file_id = files[0]['id']
            file = service.files().update(
                fileId=file_id,
                media_body=media
            ).execute()
        else:
            # Create new file
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            file_id = file.get('id')
        
        return f"gdrive://{file_id}"
    
    def load_image(self, uri: str) -> Image.Image:
        """
        Load an image from Google Drive.
        
        Args:
            uri: Google Drive URI in format "gdrive://<file_id>"
        
        Returns:
            PIL Image object
        """
        from googleapiclient.http import MediaIoBaseDownload
        
        if not uri.startswith('gdrive://'):
            raise ValueError(f"Invalid Google Drive URI: {uri}")
        
        file_id = uri.replace('gdrive://', '')
        service = self._get_service()
        
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.seek(0)
        return Image.open(fh)
    
    def delete_image(self, uri: str) -> bool:
        """
        Delete an image from Google Drive.
        
        Args:
            uri: Google Drive URI in format "gdrive://<file_id>"
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not uri.startswith('gdrive://'):
                return False
            
            file_id = uri.replace('gdrive://', '')
            service = self._get_service()
            
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception:
            return False
