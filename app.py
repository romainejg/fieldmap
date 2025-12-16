"""
Fieldmap - Cadaver Lab Photo Annotation App
A Streamlit-based mobile web app for biomedical engineers to capture, annotate, and organize photos
Uses Streamlit-native OAuth/OIDC flow with Google service account for Drive storage
"""

import base64
import io
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from streamlit_sortables import sort_items

from components.photo_editor import photo_editor, decode_image_from_dataurl
from storage import GoogleDriveStorage

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)
logger.info("="*80)
logger.info("Fieldmap Application Starting")
logger.info("="*80)

# Diagnostic: Log count of secret keys at startup (avoid exposing sensitive key names)
# Detailed key names will be logged only when get_service_account_info() is called
try:
    secret_count = len(list(st.secrets.keys()))
    logger.info(f"Startup diagnostic - Found {secret_count} secret key(s) in st.secrets")
except Exception as e:
    logger.error(f"Failed to access st.secrets during startup diagnostic: {e}")





# Configure page for mobile optimization
st.set_page_config(
    page_title="Fieldmap - Lab Photos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for mobile-friendly UI
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    .stButton > button {
        width: 100%;
        margin-top: 0.5rem;
    }
    .photo-card {
        border: none;
        border-radius: 8px;
        padding: 8px;
        margin: 4px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: box-shadow 0.2s ease;
    }
    .photo-card:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }
    .photo-card img {
        border-radius: 4px;
    }
    .photo-card-metadata {
        font-size: 0.8em;
        color: #666;
        margin-top: 8px;
        line-height: 1.4;
    }
    .session-badge {
        background-color: #4CAF50;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.9em;
        display: inline-block;
        margin: 5px 0;
    }
    .header-logo {
        text-align: center;
        padding: 10px 0;
        border-bottom: 2px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .sidebar-logo {
        text-align: center;
        padding: 20px 0 15px 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 15px;
    }
    .sidebar-logo img {
        max-width: 240px;
        width: 100%;
        margin-bottom: 0px;
    }
    .header-logo img {
        max-width: 500px;
        width: 100%;
    }
    .sidebar-title {
        font-size: 1.3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }
    .sidebar-subtitle {
        text-align: center;
        font-size: 0.85em;
        color: #666;
        margin-bottom: 15px;
    }
    .sidebar-section-label {
        font-size: 0.75em;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .logo-fallback {
        font-size: 2em;
        text-align: center;
    }
    .stRadio > div {
        padding-left: 0;
    }
    .stRadio > div > label > div {
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)


def log_available_secret_keys():
    """Log available secret keys for diagnostic purposes (keys only, not values)"""
    try:
        available_keys = list(st.secrets.keys())
        logger.info(f"Available secret keys in st.secrets: {available_keys}")
        if "google_service_account" in st.secrets:
            logger.info("✓ google_service_account is present in st.secrets")
        else:
            logger.error("✗ google_service_account is MISSING from st.secrets")
            logger.error(f"   Available keys: {available_keys}")
        return available_keys
    except Exception as e:
        logger.error(f"Failed to access st.secrets during diagnostic check: {e}")
        return []


def get_service_account_info():
    """
    Get Google service account credentials from secrets.
    
    Returns:
        dict: Service account info or None if not configured
    """
    available_keys = []
    try:
        # Get available keys for diagnostic purposes (only when needed)
        available_keys = log_available_secret_keys()
        
        # Try to get service account from TOML table (new format)
        if "google_service_account" in st.secrets:
            service_account_dict = dict(st.secrets["google_service_account"])
            logger.info("Service account found in secrets (TOML table format)")
            logger.info(f"Service account email: {service_account_dict.get('client_email', 'N/A')}")
            return service_account_dict
        
        # Log warning if not found
        logger.warning("google_service_account is missing from Streamlit secrets.")
        logger.info(f"Available secret keys: {available_keys}")
        logger.info("Please add [google_service_account] table to your secrets:")
        logger.info("  - Streamlit Cloud: Settings > Secrets")
        logger.info("  - Local development: .streamlit/secrets.toml")
        return None
        
    except Exception as e:
        logger.error(f"Failed to load service account info: {e}", exc_info=True)
        return None


def check_auth_configuration():
    """
    Check if authentication is properly configured.
    
    Returns:
        tuple: (is_configured, issues_list)
    """
    issues = []
    
    logger.info("Checking authentication configuration...")
    
    # Check for [auth] section
    try:
        if "auth" not in st.secrets:
            issues.append("[auth] section missing in secrets.toml")
            logger.error("[auth] section not found in secrets")
        else:
            auth_config = st.secrets["auth"]
            logger.info("[auth] section found in secrets")
            
            # Check required fields
            required_fields = ['client_id', 'client_secret', 'redirect_uri', 'cookie_secret', 'server_metadata_url']
            for field in required_fields:
                if field not in auth_config or not auth_config.get(field):
                    issues.append(f"[auth].{field} is missing or empty")
                    logger.error(f"[auth].{field} is missing or empty")
                else:
                    logger.info(f"[auth].{field} is configured")
                    
                    # Log partial values for verification (not full secrets)
                    if field == 'redirect_uri':
                        logger.info(f"  redirect_uri: {auth_config[field]}")
                    elif field == 'client_id':
                        logger.info(f"  client_id: {auth_config[field][:30]}...")
                    elif field == 'cookie_secret':
                        logger.info(f"  cookie_secret length: {len(auth_config[field])} chars")
    except Exception as e:
        issues.append(f"Error accessing secrets: {str(e)}")
        logger.error(f"Error accessing secrets: {e}", exc_info=True)
    
    # Check service account (don't raise, just check)
    service_account = get_service_account_info()
    if not service_account:
        issues.append("google_service_account is missing or invalid")
        logger.error("Service account configuration is missing or invalid")
    else:
        logger.info("Service account configuration validated")
    
    is_configured = len(issues) == 0
    
    if is_configured:
        logger.info("✓ All authentication configuration checks passed")
    else:
        logger.error(f"✗ Found {len(issues)} configuration issue(s):")
        for issue in issues:
            logger.error(f"  - {issue}")
    
    return is_configured, issues


class SessionStore:
    """Manages session state and CRUD operations for sessions and photos"""
    
    def __init__(self, storage_backend=None):
        """
        Initialize SessionStore with optional storage backend.
        
        Args:
            storage_backend: Optional PhotoStorage instance for persistent storage
        """
        self.storage = storage_backend
        self._initialize_state()
        
        # Load from Drive index if storage available
        if self.storage and hasattr(self.storage, 'load_index'):
            try:
                self._load_from_drive_index()
            except Exception as e:
                logger.warning(f"Failed to load from Drive index: {e}")
    
    def _load_from_drive_index(self):
        """Load sessions and photos from Drive index.json"""
        try:
            index_data = self.storage.load_index()
            
            if index_data.get('sessions'):
                st.session_state.sessions = {}
                
                for session_name, photos_meta in index_data['sessions'].items():
                    st.session_state.sessions[session_name] = []
                    
                    for photo_meta in photos_meta:
                        photo_data = {
                            'id': photo_meta['id'],
                            'original_image': None,  # Load on demand
                            'current_image': None,  # Load on demand
                            'thumbnail': None,  # Load on demand
                            'thumb_data_url': photo_meta.get('thumb_data_url', ''),
                            'comment': photo_meta.get('comment', ''),
                            'timestamp': photo_meta.get('timestamp', ''),
                            'has_annotations': photo_meta.get('has_annotations', False),
                            'source_photo_id': photo_meta.get('source_photo_id'),
                            'variant': photo_meta.get('variant', 'original'),
                            'storage_uri': photo_meta.get('storage_uri'),
                            'file_id': photo_meta.get('file_id'),
                            '_loaded': False
                        }
                        st.session_state.sessions[session_name].append(photo_data)
                
                if 'photo_counter' in index_data:
                    st.session_state.photo_counter = index_data['photo_counter']
                
                logger.info(f"Loaded {len(st.session_state.sessions)} sessions from Drive index")
        except Exception as e:
            logger.error(f"Error loading from Drive index: {e}")
    
    def _save_to_drive_index(self):
        """Save sessions and photos metadata to Drive index.json"""
        if not self.storage or not hasattr(self.storage, 'save_index'):
            return
        
        try:
            index_data = {
                'sessions': {},
                'photo_counter': st.session_state.photo_counter,
                'version': '1.0'
            }
            
            for session_name, photos in st.session_state.sessions.items():
                index_data['sessions'][session_name] = []
                
                for photo in photos:
                    photo_meta = {
                        'id': photo['id'],
                        'comment': photo['comment'],
                        'timestamp': photo['timestamp'],
                        'has_annotations': photo['has_annotations'],
                        'source_photo_id': photo.get('source_photo_id'),
                        'variant': photo.get('variant', 'original'),
                        'storage_uri': photo.get('storage_uri'),
                        'file_id': photo.get('file_id'),
                        'thumb_data_url': photo.get('thumb_data_url', '')
                    }
                    index_data['sessions'][session_name].append(photo_meta)
            
            self.storage.save_index(index_data)
            logger.info("Saved index to Drive")
        except Exception as e:
            logger.error(f"Error saving to Drive index: {e}")
    
    def _initialize_state(self):
        """Initialize session state variables"""
        if 'sessions' not in st.session_state:
            st.session_state.sessions = {'Default': []}
        if 'current_session' not in st.session_state:
            st.session_state.current_session = 'Default'
        if 'photo_counter' not in st.session_state:
            st.session_state.photo_counter = 0
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'About'
        if 'last_saved_photo_id' not in st.session_state:
            st.session_state.last_saved_photo_id = None
        if 'camera_photo_hash' not in st.session_state:
            st.session_state.camera_photo_hash = None
        if 'camera_key' not in st.session_state:
            st.session_state.camera_key = 0
    
    @property
    def sessions(self):
        return st.session_state.sessions
    
    @property
    def current_session(self):
        return st.session_state.current_session
    
    @current_session.setter
    def current_session(self, value):
        st.session_state.current_session = value
    
    @property
    def current_page(self):
        return st.session_state.current_page
    
    @current_page.setter
    def current_page(self, value):
        st.session_state.current_page = value
    
    def create_session(self, session_name):
        """Create a new session"""
        if session_name and session_name not in st.session_state.sessions:
            st.session_state.sessions[session_name] = []
            self._save_to_drive_index()
            return True
        return False
    
    def add_photo(self, image, session_name, comment=""):
        """Add a photo with metadata to a session"""
        st.session_state.photo_counter += 1
        photo_id = st.session_state.photo_counter
        
        # Create thumbnail for efficient gallery display
        thumbnail = image.copy()
        thumbnail.thumbnail((100, 100), Image.Resampling.LANCZOS)
        
        # Convert thumbnail to base64 data URL for gallery tiles
        thumb_buffer = io.BytesIO()
        thumbnail.save(thumb_buffer, format='PNG')
        thumb_buffer.seek(0)
        thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
        thumb_data_url = f"data:image/png;base64,{thumb_base64}"
        
        # Save to storage backend (Google Drive with service account)
        storage_uri = None
        file_id = None
        if self.storage:
            try:
                storage_uri = self.storage.save_image(session_name, photo_id, image)
                if storage_uri and storage_uri.startswith('gdrive://'):
                    file_id = storage_uri.replace('gdrive://', '')
            except Exception as e:
                logger.warning(f"Failed to save to storage: {e}")
        
        photo_data = {
            'id': photo_id,
            'original_image': image.copy(),
            'current_image': image.copy(),
            'thumbnail': thumbnail,
            'thumb_data_url': thumb_data_url,
            'comment': comment,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_annotations': False,
            'source_photo_id': None,
            'variant': 'original',
            'storage_uri': storage_uri,
            'file_id': file_id,
            '_loaded': True
        }
        st.session_state.sessions[session_name].append(photo_data)
        
        self._save_to_drive_index()
        
        return photo_data['id']
    
    def add_derived_photo(self, base_photo_id, session_name, image, comment=None):
        """Create a new photo derived from an existing photo (e.g., annotated version)"""
        base_photo = self.get_photo(base_photo_id, session_name)
        if not base_photo:
            raise ValueError(f"Base photo {base_photo_id} not found in session {session_name}")
        
        st.session_state.photo_counter += 1
        photo_id = st.session_state.photo_counter
        
        thumbnail = image.copy()
        thumbnail.thumbnail((100, 100), Image.Resampling.LANCZOS)
        
        thumb_buffer = io.BytesIO()
        thumbnail.save(thumb_buffer, format='PNG')
        thumb_buffer.seek(0)
        thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
        thumb_data_url = f"data:image/png;base64,{thumb_base64}"
        
        if comment is None:
            comment = base_photo['comment']
        
        storage_uri = None
        file_id = None
        if self.storage:
            try:
                storage_uri = self.storage.save_image(session_name, photo_id, image)
                if storage_uri and storage_uri.startswith('gdrive://'):
                    file_id = storage_uri.replace('gdrive://', '')
            except Exception as e:
                logger.warning(f"Failed to save to storage: {e}")
        
        photo_data = {
            'id': photo_id,
            'original_image': image.copy(),
            'current_image': image.copy(),
            'thumbnail': thumbnail,
            'thumb_data_url': thumb_data_url,
            'comment': comment,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_annotations': True,
            'source_photo_id': base_photo_id,
            'variant': 'annotated',
            'storage_uri': storage_uri,
            'file_id': file_id,
            '_loaded': True
        }
        st.session_state.sessions[session_name].append(photo_data)
        
        self._save_to_drive_index()
        
        return photo_data['id']
    
    def move_photo(self, photo_id, from_session, to_session):
        """Move a photo from one session to another"""
        if from_session in st.session_state.sessions and to_session in st.session_state.sessions:
            photos = st.session_state.sessions[from_session]
            for i, photo in enumerate(photos):
                if photo['id'] == photo_id:
                    moved_photo = photos.pop(i)
                    st.session_state.sessions[to_session].append(moved_photo)
                    self._save_to_drive_index()
                    return True
        return False
    
    def delete_photo(self, photo_id, session_name):
        """Delete a photo from a session"""
        if session_name in st.session_state.sessions:
            photos = st.session_state.sessions[session_name]
            for i, photo in enumerate(photos):
                if photo['id'] == photo_id:
                    photos.pop(i)
                    self._save_to_drive_index()
                    return True
        return False
    
    def update_photo_comment(self, photo_id, session_name, new_comment):
        """Update the comment for a photo"""
        if session_name in st.session_state.sessions:
            for photo in st.session_state.sessions[session_name]:
                if photo['id'] == photo_id:
                    photo['comment'] = new_comment
                    self._save_to_drive_index()
                    return True
        return False
    
    def get_photo(self, photo_id, session_name):
        """Get a photo by ID from a session"""
        if session_name in st.session_state.sessions:
            for photo in st.session_state.sessions[session_name]:
                if photo['id'] == photo_id:
                    if not photo.get('_loaded', True) and photo.get('storage_uri'):
                        self._load_photo_image(photo)
                    return photo
        return None
    
    def _load_photo_image(self, photo):
        """Load image data from Drive for a photo"""
        if not self.storage or not photo.get('storage_uri'):
            return
        
        try:
            image = self.storage.load_image(photo['storage_uri'])
            
            photo['original_image'] = image.copy()
            photo['current_image'] = image.copy()
            
            if not photo.get('thumbnail'):
                thumbnail = image.copy()
                thumbnail.thumbnail((100, 100), Image.Resampling.LANCZOS)
                photo['thumbnail'] = thumbnail
            
            if not photo.get('thumb_data_url'):
                thumb = photo.get('thumbnail')
                if thumb:
                    thumb_buffer = io.BytesIO()
                    thumb.save(thumb_buffer, format='PNG')
                    thumb_buffer.seek(0)
                    thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
                    photo['thumb_data_url'] = f"data:image/png;base64,{thumb_base64}"
            
            photo['_loaded'] = True
            logger.info(f"Loaded image for photo {photo['id']} from Drive")
        except Exception as e:
            logger.error(f"Failed to load image for photo {photo['id']}: {e}")
    
    def export_to_excel(self):
        """Export all photos and comments to Excel"""
        data = []
        for session_name, photos in st.session_state.sessions.items():
            for photo in photos:
                data.append({
                    'Session': session_name,
                    'Photo ID': photo['id'],
                    'Timestamp': photo['timestamp'],
                    'Comment': photo['comment'],
                    'Has Annotations': 'Yes' if photo['has_annotations'] else 'No'
                })
        
        if data:
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Photo Annotations')
            return output.getvalue()
        return None


class BasePage:
    """Base class for all pages"""
    
    def __init__(self, session_store):
        self.session_store = session_store
    
    def render(self):
        """Render the page - to be implemented by subclasses"""
        raise NotImplementedError


class FieldmapPage(BasePage):
    """Main fieldmap page with camera and annotation"""
    
    def render(self):
        import hashlib
        
        # Header with logo
        st.markdown('<div class="header-logo">', unsafe_allow_html=True)
        try:
            logo_path = Path(__file__).parent / "assets" / "logo.png"
            if logo_path.exists():
                logo_image = Image.open(logo_path)
                st.image(logo_image, width=180)
            else:
                st.markdown('<div class="logo-fallback">Fieldmap</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown('<div class="logo-fallback">Fieldmap</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Session management
        st.subheader("Session")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            current_session = st.selectbox(
                "Active Session",
                options=list(self.session_store.sessions.keys()),
                index=list(self.session_store.sessions.keys()).index(self.session_store.current_session),
                key="fieldmap_session_selector",
                label_visibility="collapsed"
            )
            self.session_store.current_session = current_session
        
        with col2:
            if st.button("New", key="create_session_btn"):
                st.session_state['show_create_session'] = True
        
        if st.session_state.get('show_create_session', False):
            with st.form("create_session_form"):
                new_session_name = st.text_input("New Session Name", key="new_session_input")
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("Create", type="primary")
                    if submitted and new_session_name:
                        if self.session_store.create_session(new_session_name):
                            self.session_store.current_session = new_session_name
                            st.session_state['show_create_session'] = False
                            st.success(f"Session '{new_session_name}' created!")
                            st.rerun()
                        else:
                            st.error("Session already exists or invalid name")
                with col_cancel:
                    cancel = st.form_submit_button("Cancel")
                    if cancel:
                        st.session_state['show_create_session'] = False
                        st.rerun()
        
        st.divider()
        
        # Camera section
        st.subheader("Camera")
        
        uploaded_file = st.camera_input("Take a photo", key=f"camera_{st.session_state.camera_key}")
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            image_bytes = uploaded_file.getvalue()
            current_photo_hash = hashlib.md5(image_bytes).hexdigest()
            
            if current_photo_hash != st.session_state.camera_photo_hash:
                photo_id = self.session_store.add_photo(image, self.session_store.current_session, "")
                st.session_state.last_saved_photo_id = photo_id
                st.session_state.camera_photo_hash = current_photo_hash
                st.session_state.camera_key += 1
                st.success(f"Photo saved! (ID: {photo_id})")
                st.rerun()
        
        # Annotation interface for last saved photo
        if st.session_state.last_saved_photo_id:
            st.divider()
            st.subheader("Last Photo")
            
            last_photo = self.session_store.get_photo(
                st.session_state.last_saved_photo_id,
                self.session_store.current_session
            )
            
            if last_photo:
                photo_comment = st.text_area(
                    "Notes/Comments:",
                    value=last_photo['comment'],
                    key="last_photo_comment",
                    placeholder="Add notes about this photo..."
                )
                if photo_comment != last_photo['comment']:
                    self.session_store.update_photo_comment(
                        last_photo['id'],
                        self.session_store.current_session,
                        photo_comment
                    )
                
                st.markdown("#### Edit Photo")
                st.info("Use the annotation tools below. Click Save to apply changes or Cancel to discard.")
                
                editor_result = photo_editor(
                    image=last_photo['current_image'],
                    key=f"photo_editor_{last_photo['id']}"
                )
                
                if editor_result is not None:
                    if editor_result.get('saved') and editor_result.get('pngDataUrl'):
                        try:
                            edited_image = decode_image_from_dataurl(editor_result['pngDataUrl'])
                            
                            new_photo_id = self.session_store.add_derived_photo(
                                base_photo_id=last_photo['id'],
                                session_name=self.session_store.current_session,
                                image=edited_image,
                                comment=last_photo['comment']
                            )
                            
                            st.session_state.last_saved_photo_id = new_photo_id
                            
                            st.success(f"Annotated copy created! (Photo #{new_photo_id})")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error processing edited image: {str(e)}")
                    elif editor_result.get('cancelled'):
                        st.info("Editing cancelled")
                        st.rerun()


class GalleryPage(BasePage):
    """Gallery page for viewing and managing photos"""
    
    def render(self):
        st.header("Photo Gallery")
        
        # Check if Drive storage is available
        if not self.session_store.storage:
            st.error("⚠️ **Gallery Disabled**")
            st.info("Google Drive storage is not configured. Gallery requires Drive to be set up.")
            st.markdown("""
            **To enable Gallery:**
            1. Add `[google_service_account]` table to your `.streamlit/secrets.toml`
            2. Ensure the service account has access to the 'Fieldmap' Drive folder
            3. Restart the app
            
            See the About page for detailed setup instructions.
            """)
            return
        
        view_session = st.selectbox(
            "View Session:",
            options=["All Sessions"] + list(self.session_store.sessions.keys()),
            key="gallery_session_filter"
        )
        
        self._render_draggable_view()
    
    def _render_draggable_view(self):
        """Render draggable view with photo thumbnails as tiles"""
        st.info("📱 Drag photos between sessions to organize them. Click a tile to view details.")
        
        sortable_containers = []
        original_structure = {}
        session_name_map = {}
        
        for idx, session_name in enumerate(sorted(self.session_store.sessions.keys())):
            photos = self.session_store.sessions[session_name]
            items = []
            for photo in photos:
                if 'thumb_data_url' not in photo or not photo['thumb_data_url']:
                    thumb = photo.get('thumbnail')
                    if not thumb:
                        thumb = photo['current_image'].copy()
                        thumb.thumbnail((100, 100), Image.Resampling.LANCZOS)
                        photo['thumbnail'] = thumb
                    
                    thumb_buffer = io.BytesIO()
                    thumb.save(thumb_buffer, format='PNG')
                    thumb_buffer.seek(0)
                    thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
                    photo['thumb_data_url'] = f"data:image/png;base64,{thumb_base64}"
                
                thumb_url = photo['thumb_data_url']
                if not thumb_url.startswith('data:image/'):
                    thumb = photo.get('thumbnail', photo['current_image'].copy())
                    thumb.thumbnail((100, 100), Image.Resampling.LANCZOS)
                    thumb_buffer = io.BytesIO()
                    thumb.save(thumb_buffer, format='PNG')
                    thumb_buffer.seek(0)
                    thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
                    thumb_url = f"data:image/png;base64,{thumb_base64}"
                    photo['thumb_data_url'] = thumb_url
                
                variant_badge = "📝 " if photo.get('variant') == 'annotated' else ""
                item_html = f'''<div style="text-align:center;">
                    <img src="{thumb_url}" style="width:84px;height:84px;object-fit:cover;border-radius:4px;" />
                    <div style="font-size:10px;margin-top:2px;">{variant_badge}#{int(photo['id'])}</div>
                </div>'''
                
                item_id = f"photo_{photo['id']}"
                items.append(item_html)
                original_structure[item_id] = {
                    'photo_id': photo['id'],
                    'session': session_name,
                    'photo': photo
                }
                original_structure[item_html] = {
                    'photo_id': photo['id'],
                    'session': session_name,
                    'photo': photo
                }
            
            session_name_map[idx] = session_name
            sortable_containers.append({
                "header": f"📁 {session_name} ({len(photos)} photo{'s' if len(photos) != 1 else ''})",
                "items": items
            })
        
        custom_style = """
        .sortable-item {
            background-color: #ffffff;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 4px;
            margin: 6px;
            cursor: move;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: box-shadow 0.2s ease;
            display: inline-block;
            width: 100px;
            height: 100px;
            text-align: center;
            font-size: 11px;
            overflow: hidden;
            line-height: 1.2;
        }
        .sortable-item:hover {
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }
        .sortable-container {
            background-color: #f5f5f5;
            border-radius: 8px;
            padding: 12px;
            min-height: 120px;
            margin: 8px 0;
        }
        .sortable-container-header {
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 8px;
        }
        """
        
        sorted_containers = sort_items(
            sortable_containers,
            multi_containers=True,
            direction="vertical",
            custom_style=custom_style,
            key="gallery_sortable"
        )
        
        if sorted_containers != sortable_containers:
            new_structure = {}
            changes_made = False
            
            for idx, container in enumerate(sorted_containers):
                if idx < len(session_name_map):
                    session_name = session_name_map[idx]
                else:
                    session_name = container["header"].split(" (")[0].replace("📁 ", "").strip()
                
                new_photos = []
                for item_id in container["items"]:
                    if item_id in original_structure:
                        photo_info = original_structure[item_id]
                        new_photos.append(photo_info['photo'])
                
                new_structure[session_name] = new_photos
            
            for session_name, photos in new_structure.items():
                if session_name not in st.session_state.sessions:
                    st.session_state.sessions[session_name] = []
                
                if st.session_state.sessions[session_name] != photos:
                    st.session_state.sessions[session_name] = photos
                    changes_made = True
            
            if changes_made:
                st.success("✓ Photos reorganized!")
                st.rerun()
        
        st.divider()
        st.markdown("**Select a photo to view details:**")
        
        all_photos = []
        for session_name in sorted(self.session_store.sessions.keys()):
            for photo in self.session_store.sessions[session_name]:
                all_photos.append((session_name, photo))
        
        if all_photos:
            cols_per_row = 8
            for i in range(0, len(all_photos), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(all_photos):
                        session_name, photo = all_photos[i + j]
                        with cols[j]:
                            if 'thumb_data_url' not in photo or not photo['thumb_data_url']:
                                thumb = photo.get('thumbnail')
                                if not thumb:
                                    thumb = photo['current_image'].copy()
                                    thumb.thumbnail((100, 100), Image.Resampling.LANCZOS)
                                    photo['thumbnail'] = thumb
                                
                                thumb_buffer = io.BytesIO()
                                thumb.save(thumb_buffer, format='PNG')
                                thumb_buffer.seek(0)
                                thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
                                photo['thumb_data_url'] = f"data:image/png;base64,{thumb_base64}"
                            
                            st.markdown(
                                f'<img src="{photo["thumb_data_url"]}" style="width:100%;border-radius:4px;cursor:pointer;" />',
                                unsafe_allow_html=True
                            )
                            
                            variant_badge = "📝" if photo.get('variant') == 'annotated' else ""
                            button_label = f"{variant_badge}#{photo['id']}" if variant_badge else f"#{photo['id']}"
                            
                            if st.button(button_label, key=f"select_{photo['id']}", use_container_width=True):
                                st.session_state['gallery_selected'] = {
                                    'photo_id': photo['id'],
                                    'session': session_name
                                }
                                st.rerun()
        
        if st.session_state.get('gallery_selected'):
            selected_info = st.session_state['gallery_selected']
            selected_photo = self.session_store.get_photo(
                selected_info['photo_id'],
                selected_info['session']
            )
            if selected_photo:
                with st.expander("📸 Photo Details", expanded=True):
                    self._render_photo_details(selected_photo, selected_info['session'])
    
    def _render_photo_details(self, photo, session_name):
        """Render detailed photo view with edit capabilities"""
        st.subheader(f"Photo #{photo['id']}")
        
        if st.button("✕ Close Details", key=f"close_details_{photo['id']}", type="secondary"):
            st.session_state['gallery_selected'] = None
            st.rerun()
        
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            st.caption(f"**Session:** {session_name}")
            st.caption(f"**Time:** {photo['timestamp']}")
        with col_meta2:
            if photo.get('variant') == 'annotated':
                st.caption(f"**Type:** 📝 Edited")
                if photo.get('source_photo_id'):
                    st.caption(f"**Derived from:** Photo #{photo['source_photo_id']}")
            else:
                st.caption(f"**Type:** Original")
        
        st.markdown("---")
        
        if photo.get('variant') == 'annotated' and photo.get('source_photo_id'):
            st.markdown("**Annotated Image:**")
            st.image(photo['current_image'], use_column_width=True)
        elif photo['has_annotations']:
            col_orig, col_curr = st.columns(2)
            with col_orig:
                st.markdown("**Original:**")
                st.image(photo['original_image'], use_column_width=True)
            with col_curr:
                st.markdown("**With Annotations:**")
                st.image(photo['current_image'], use_column_width=True)
        else:
            st.markdown("**Image:**")
            st.image(photo['current_image'], use_column_width=True)
        
        buf = io.BytesIO()
        photo['current_image'].save(buf, format='PNG')
        buf.seek(0)
        st.download_button(
            label="Download Photo" + (" (annotated)" if photo.get('variant') == 'annotated' or photo['has_annotations'] else ""),
            data=buf,
            file_name=f"photo_{photo['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png",
            key=f"download_{photo['id']}"
        )
        
        st.divider()
        
        new_comment = st.text_area(
            "Notes/Comments:",
            value=photo['comment'],
            key=f"edit_comment_{photo['id']}",
            placeholder="Add notes or description..."
        )
        if st.button("Update Comment", key=f"update_{photo['id']}"):
            self.session_store.update_photo_comment(photo['id'], session_name, new_comment)
            st.success("Comment updated!")
            st.rerun()
        
        st.divider()
        
        st.markdown("**Add Annotations**")
        
        col_edit, col_reset = st.columns(2)
        with col_edit:
            if st.button("Edit Photo", key=f"edit_photo_gallery_{photo['id']}", type="primary"):
                st.session_state[f'show_gallery_editor_{photo["id"]}'] = True
                st.rerun()
        
        with col_reset:
            if photo['has_annotations'] and not photo.get('source_photo_id'):
                if st.button("Reset Annotations", key=f"reset_{photo['id']}", type="secondary"):
                    photo['current_image'] = photo['original_image'].copy()
                    photo['has_annotations'] = False
                    st.success("Annotations cleared!")
                    st.rerun()
        
        if st.session_state.get(f'show_gallery_editor_{photo["id"]}', False):
            st.info("Use the annotation tools below. Click Save to apply changes or Cancel to discard.")
            
            editor_result = photo_editor(
                image=photo['current_image'],
                key=f"photo_editor_gallery_{photo['id']}"
            )
            
            if editor_result is not None:
                if editor_result.get('saved') and editor_result.get('pngDataUrl'):
                    try:
                        edited_image = decode_image_from_dataurl(editor_result['pngDataUrl'])
                        
                        new_photo_id = self.session_store.add_derived_photo(
                            base_photo_id=photo['id'],
                            session_name=session_name,
                            image=edited_image,
                            comment=photo['comment']
                        )
                        
                        st.session_state[f'show_gallery_editor_{photo["id"]}'] = False
                        
                        st.session_state['gallery_selected'] = {
                            'photo_id': new_photo_id,
                            'session': session_name
                        }
                        
                        st.success(f"Annotated copy created! (Photo #{new_photo_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing edited image: {str(e)}")
                elif editor_result.get('cancelled'):
                    st.session_state[f'show_gallery_editor_{photo["id"]}'] = False
                    st.info("Editing cancelled")
                    st.rerun()
        
        st.divider()
        
        st.markdown("**Move Photo**")
        other_sessions = [s for s in self.session_store.sessions.keys() if s != session_name]
        if other_sessions:
            col_move_to, col_move_btn = st.columns([3, 1])
            with col_move_to:
                move_to_session = st.selectbox(
                    "Move to session:",
                    options=[""] + other_sessions,
                    key=f"move_to_{photo['id']}"
                )
            with col_move_btn:
                if move_to_session and st.button("Move", key=f"move_btn_{photo['id']}", use_container_width=True):
                    if self.session_store.move_photo(photo['id'], session_name, move_to_session):
                        st.session_state['gallery_selected'] = None
                        st.success(f"Moved to {move_to_session}!")
                        st.rerun()
        else:
            st.caption("No other sessions available")
        
        st.divider()
        
        if st.button("🗑️ Delete Photo", key=f"delete_{photo['id']}", type="secondary"):
            if self.session_store.delete_photo(photo['id'], session_name):
                st.session_state['gallery_selected'] = None
                st.success("Photo deleted!")
                st.rerun()


class AboutPage(BasePage):
    """About page with app information and authentication"""
    
    def render(self):
        st.markdown("""
        <style>
            .hero-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .hero-header img {
                max-width: 300px;
                margin: 0 auto;
            }
            .hero-title {
                font-size: 3rem;
                font-weight: 700;
                margin-top: 1rem;
                margin-bottom: 0.5rem;
                color: #1f1f1f;
            }
            .hero-subtitle {
                font-size: 1.2rem;
                color: #666;
                margin-bottom: 2rem;
            }
            .feature-list {
                font-size: 1.1rem;
                line-height: 2;
                margin-bottom: 2rem;
            }
            .feature-list li {
                margin-bottom: 0.5rem;
            }
            .signin-card {
                background-color: #f8f9fa;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 2rem;
                margin-top: 2rem;
                text-align: center;
            }
            .signin-card h3 {
                margin-top: 0;
                margin-bottom: 1rem;
                color: #1f1f1f;
            }
            .hero-image {
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            @media (max-width: 768px) {
                .hero-title {
                    font-size: 2rem;
                }
                .hero-subtitle {
                    font-size: 1rem;
                }
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Header with logo
        st.markdown('<div class="hero-header">', unsafe_allow_html=True)
        try:
            logo_path = Path(__file__).parent / "assets" / "logo.png"
            if logo_path.exists():
                logo_image = Image.open(logo_path)
                st.image(logo_image, width=250)
        except Exception:
            pass
        st.markdown('</div>', unsafe_allow_html=True)
        
        col_left, col_right = st.columns([1.2, 1])
        
        with col_left:
            st.markdown('<div style="font-size: 3rem; color: #666; margin-bottom: 0.5rem;">Hello!</div>', unsafe_allow_html=True)
            st.markdown('<div class="hero-title">Welcome to Fieldmap.</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-list">
            <ul style="list-style-type: none; padding-left: 0;">
            A non-profit app to assist biomedical engineers with lab efficiency and documentation. Capture and organize photos, annotate images, and sync automatically to Google Drive.
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="signin-card">', unsafe_allow_html=True)
            
            # Check if user is logged in using Streamlit's native auth
            # In Streamlit 1.42+, when [auth] is configured in secrets.toml,
            # user info is available via st.user
            user_authenticated = False
            user_email = None
            auth_method = None
            
            # Try to get user info from Streamlit's native auth
            try:
                # Streamlit 1.42+ provides st.user when auth is configured
                if hasattr(st, 'user'):
                    user_info = st.user
                    logger.info(f"st.user exists: {user_info}")
                    if user_info and user_info.get('email'):
                        user_authenticated = True
                        user_email = user_info.get('email')
                        auth_method = "st.user"
                        logger.info(f"User authenticated via st.user: {user_email}")
                    else:
                        logger.info("st.user exists but no email found")
                else:
                    logger.warning("st.user not available")
            except Exception as e:
                logger.error(f"Error checking Streamlit auth: {e}", exc_info=True)
            
            # Fallback: check manual session state for compatibility
            if not user_authenticated:
                user_authenticated = st.session_state.get("logged_in", False)
                if user_authenticated:
                    user_info = st.session_state.get("user_info", {})
                    user_email = user_info.get("email", "Unknown")
                    auth_method = "manual_session_state"
                    logger.info(f"User authenticated via manual session state: {user_email}")
                else:
                    logger.info("User not authenticated via any method")
            
            if user_authenticated:
                # User is authenticated
                st.markdown("### ✅ Signed In")
                st.success(f"Signed in as **{user_email}**")
                
                st.info("📱 Access Fieldmap and Gallery from the sidebar")
                
                # For Streamlit native auth, logout is typically handled via st.experimental_rerun
                # or by having user clear cookies
                if st.button("Sign Out", key="signout_btn", type="secondary", use_container_width=True):
                    # Clear manual session state (if used)
                    st.session_state["logged_in"] = False
                    st.session_state.pop("user_info", None)
                    st.info("Please clear your browser cookies to fully sign out.")
                    st.rerun()
            else:
                # User is not authenticated - show sign-in
                st.markdown("### Sign In")
                st.markdown("Sign in with Google to access Fieldmap")
                
                # Run configuration check
                auth_configured, config_issues = check_auth_configuration()
                
                if not auth_configured:
                    st.error("⚠️ **Authentication Configuration Issues Detected**")
                    st.markdown("**Issues found:**")
                    for issue in config_issues:
                        st.markdown(f"- {issue}")
                    
                    st.divider()
                    
                    with st.expander("📋 Detailed Setup Instructions", expanded=True):
                        st.markdown("""
                        **Required secrets in `.streamlit/secrets.toml`:**
                        
                        ```toml
                        [auth]
                        redirect_uri = "https://fieldmap.streamlit.app/oauth2callback"
                        cookie_secret = "<generate a long random secret>"
                        client_id = "<Google Web OAuth client_id>"
                        client_secret = "<Google Web OAuth client_secret>"
                        server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
                        
                        # Service account as TOML table (NOT JSON string)
                        [google_service_account]
                        type = "service_account"
                        project_id = "your-project-id"
                        private_key_id = "key-id"
                        private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR_KEY\\n-----END PRIVATE KEY-----\\n"
                        client_email = "your-sa@your-project.iam.gserviceaccount.com"
                        client_id = "123456789"
                        auth_uri = "https://accounts.google.com/o/oauth2/auth"
                        token_uri = "https://oauth2.googleapis.com/token"
                        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
                        client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
                        ```
                        
                        **To generate cookie_secret:**
                        ```bash
                        python -c "import secrets; print(secrets.token_urlsafe(32))"
                        ```
                        
                        See [docs/SETUP.md](https://github.com/romainejg/fieldmap/blob/main/docs/SETUP.md) for complete setup instructions.
                        """)
                    
                    with st.expander("🔧 Debugging Tools"):
                        st.markdown("""
                        **Run the debugging script:**
                        
                        ```bash
                        python debug_auth.py
                        ```
                        
                        This script will:
                        - Validate your secrets.toml configuration
                        - Check Streamlit version compatibility
                        - Test Google Drive service account connection
                        - Verify OAuth endpoint accessibility
                        - Provide detailed diagnostic information
                        
                        **Common Issues:**
                        
                        1. **Missing secrets.toml**: Copy from template
                           ```bash
                           cp .streamlit/secrets.toml.template .streamlit/secrets.toml
                           ```
                        
                        2. **Placeholder values**: Replace all `<...>` placeholders with actual values
                        
                        3. **Wrong redirect_uri**: Must match exactly in Google Cloud Console OAuth settings
                           - Local: `http://localhost:8501/oauth2callback`
                           - Production: `https://fieldmap.streamlit.app/oauth2callback`
                        
                        4. **Service account not shared**: Share "Fieldmap" Drive folder with service account email
                        
                        5. **Old Streamlit version**: Ensure >= 1.42.0
                           ```bash
                           pip install --upgrade 'streamlit>=1.42.0'
                           ```
                        """)
                else:
                    # Configuration is valid
                    st.success("✓ Configuration appears valid")
                    
                    st.markdown("""
                    **How to sign in:**
                    
                    Streamlit's native authentication should automatically add a **"Log in"** button to the UI.
                    Look for it in the **top-right corner** of the page.
                    """)
                    
                    # Show debugging info in expander
                    with st.expander("🔍 Debug Information"):
                        import streamlit as st_module
                        st.markdown(f"**Streamlit Version:** {st_module.__version__}")
                        
                        st.markdown("**Authentication Attributes:**")
                        st.markdown(f"- `hasattr(st, 'user')`: {hasattr(st, 'user')}")
                        
                        if hasattr(st, 'user'):
                            try:
                                user_info = st.user
                                st.markdown(f"- `st.user`: {user_info}")
                            except Exception as e:
                                st.markdown(f"- `st.user` error: {e}")
                        
                        st.markdown("**Secrets Check:**")
                        try:
                            auth_present = "auth" in st.secrets
                            st.markdown(f"- `'auth' in st.secrets`: {auth_present}")
                            if auth_present:
                                st.markdown(f"- `client_id present`: {bool(st.secrets['auth'].get('client_id'))}")
                                st.markdown(f"- `client_secret present`: {bool(st.secrets['auth'].get('client_secret'))}")
                                st.markdown(f"- `redirect_uri`: {st.secrets['auth'].get('redirect_uri', 'N/A')}")
                        except Exception as e:
                            st.markdown(f"- Error checking secrets: {e}")
                        
                        st.markdown("**Service Account:**")
                        service_account_info = get_service_account_info()
                        if service_account_info:
                            st.markdown(f"- Service account email: {service_account_info.get('client_email', 'N/A')}")
                            st.markdown(f"- Project ID: {service_account_info.get('project_id', 'N/A')}")
                        else:
                            st.markdown("- Service account: Not configured")
                        
                        st.divider()
                        st.markdown("""
                        **Troubleshooting Steps:**
                        
                        1. Run the diagnostic script: `python debug_auth.py`
                        2. Check browser console (F12) for JavaScript errors
                        3. Verify redirect_uri in Google Cloud Console matches exactly
                        4. Clear browser cookies and cache
                        5. Try in incognito/private browsing mode
                        6. Check that OAuth consent screen is configured in Google Cloud
                        7. Ensure you're added as a test user (if app is in testing mode)
                        """)
                    
                    # Provide manual fallback for testing/development
                    st.divider()
                    if st.button("Manual Login (Dev Only)", key="manual_signin_btn", type="secondary", use_container_width=True):
                        st.warning("⚠️ This is a development-only manual login. In production, use Streamlit's native auth.")
                        # Simulate login for development
                        st.session_state["logged_in"] = True
                        st.session_state["user_info"] = {"email": "test@example.com"}
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_right:
            try:
                hero_path = Path(__file__).parent / "assets" / "biomedical.jpg"
                if hero_path.exists():
                    hero_image = Image.open(hero_path)
                    st.markdown('<div class="hero-image">', unsafe_allow_html=True)
                    st.image(hero_image, use_column_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            except Exception:
                pass


class App:
    """Main application class that orchestrates the UI and routing"""
    
    def __init__(self):
        logger.info("Initializing Fieldmap application")
        
        # Initialize storage backend with service account
        storage_backend = None
        service_account_info = get_service_account_info()
        
        if service_account_info:
            try:
                logger.info("Attempting to initialize Google Drive storage...")
                storage_backend = GoogleDriveStorage(service_account_info)
                logger.info("✓ Google Drive storage (service account) initialized successfully")
                
                # Test connection using public method
                try:
                    storage_backend.test_connection()
                    logger.info("✓ Successfully connected to Google Drive API")
                except Exception as e:
                    logger.error(f"✗ Failed to connect to Google Drive API: {e}", exc_info=True)
                    logger.warning("⚠️ Gallery will be disabled - Drive connection failed")
                    storage_backend = None
            except Exception as e:
                logger.error(f"✗ Failed to initialize Google Drive storage: {e}", exc_info=True)
                logger.warning("⚠️ Gallery will be disabled - storage initialization failed")
                storage_backend = None
        else:
            logger.warning("⚠️ Service account not configured - Gallery will be disabled")
            logger.info("To enable Gallery, add [google_service_account] to secrets.toml")
        
        self.session_store = SessionStore(storage_backend=storage_backend)
        self.pages = {
            'Fieldmap': FieldmapPage(self.session_store),
            'Gallery': GalleryPage(self.session_store),
            'About': AboutPage(self.session_store)
        }
        logger.info("✓ Application initialization complete")
    
    def render_sidebar(self):
        """Render sidebar with logo and navigation"""
        with st.sidebar:
            st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
            try:
                logo_path = Path(__file__).parent / "assets" / "logo.png"
                if logo_path.exists():
                    logo_image = Image.open(logo_path)
                    st.image(logo_image, use_column_width=True)
                else:
                    st.markdown('<div class="logo-fallback">Fieldmap</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown('<div class="logo-fallback">Fieldmap</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="sidebar-title">Fieldmap</div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-subtitle">Documentation support for the cadaver lab.</div>', unsafe_allow_html=True)
            
            # Check if user is authenticated using Streamlit's native auth or fallback
            is_authenticated = False
            try:
                if hasattr(st, 'user'):
                    user_info = st.user
                    if user_info and user_info.get('email'):
                        is_authenticated = True
            except Exception:
                pass
            
            # Fallback: check manual session state
            if not is_authenticated:
                is_authenticated = st.session_state.get("logged_in", False)
            
            st.markdown('<div class="sidebar-section-label">Sections</div>', unsafe_allow_html=True)
            
            if not is_authenticated:
                st.info("Please sign in on the About page to access Fieldmap and Gallery.")
                current_index = 0
                selected_page = st.radio(
                    "Navigation",
                    options=['About'],
                    index=current_index,
                    key="navigation_radio",
                    label_visibility="collapsed"
                )
            else:
                current_index = ['Fieldmap', 'Gallery', 'About'].index(self.session_store.current_page)
                selected_page = st.radio(
                    "Navigation",
                    options=['Fieldmap', 'Gallery', 'About'],
                    index=current_index,
                    key="navigation_radio",
                    label_visibility="collapsed"
                )
            
            self.session_store.current_page = selected_page
    
    def run(self):
        """Main application entry point"""
        # Check authentication status using Streamlit's native auth or fallback
        is_authenticated = False
        
        # Try to get user info from Streamlit's native auth
        try:
            if hasattr(st, 'user'):
                user_info = st.user
                if user_info and user_info.get('email'):
                    is_authenticated = True
        except Exception:
            pass
        
        # Fallback: check manual session state
        if not is_authenticated:
            is_authenticated = st.session_state.get("logged_in", False)
        
        # Implement navigation gating: force About page if not authenticated
        if not is_authenticated:
            if self.session_store.current_page != 'About':
                self.session_store.current_page = 'About'
        
        # Render sidebar
        self.render_sidebar()
        
        # Render the selected page
        current_page = self.pages.get(self.session_store.current_page)
        if current_page:
            current_page.render()


# Run the application
if __name__ == "__main__":
    app = App()
    app.run()
