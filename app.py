"""
Fieldmap - Cadaver Lab Photo Annotation App
A Streamlit-based mobile web app for biomedical engineers to capture, annotate, and organize photos
Uses Google Drive with user OAuth for storage (no service account quota issues)
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
from oauth_utils import (
    is_authenticated,
    get_user_email,
    get_user_name,
    get_user_credentials,
    get_authorization_url,
    logout
)

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
    
    /* Mobile sidebar fix - ensure it fully collapses when closed */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"][aria-expanded="false"] {
            transform: translateX(-100%) !important;
            margin-left: 0 !important;
        }
        section[data-testid="stSidebar"] {
            transition: transform 0.3s ease-in-out !important;
        }
    }
</style>
""", unsafe_allow_html=True)


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
            st.error("⚠️ **Gallery Unavailable**")
            st.info("Google Drive storage is not initialized. This may happen if you just signed in. Please refresh the page.")
            if st.button("Refresh Page", type="primary"):
                st.rerun()
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
                # Add a data attribute to store photo info for click handling
                item_html = f'''<div style="text-align:center;" data-photo-id="{photo['id']}" data-session="{session_name}">
                    <img src="{thumb_url}" style="width:84px;height:84px;object-fit:cover;border-radius:4px;cursor:pointer;" />
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
            move_operations = []  # Track files that need to be moved in Drive
            
            for idx, container in enumerate(sorted_containers):
                if idx < len(session_name_map):
                    session_name = session_name_map[idx]
                else:
                    session_name = container["header"].split(" (")[0].replace("📁 ", "").strip()
                
                new_photos = []
                for item_id in container["items"]:
                    if item_id in original_structure:
                        photo_info = original_structure[item_id]
                        photo = photo_info['photo']
                        original_session = photo_info['session']
                        
                        new_photos.append(photo)
                        
                        # Check if photo moved to a different session
                        if original_session != session_name and photo.get('file_id'):
                            move_operations.append({
                                'file_id': photo['file_id'],
                                'from_session': original_session,
                                'to_session': session_name
                            })
                
                new_structure[session_name] = new_photos
            
            # Update in-memory structure
            for session_name, photos in new_structure.items():
                if session_name not in st.session_state.sessions:
                    st.session_state.sessions[session_name] = []
                
                if st.session_state.sessions[session_name] != photos:
                    st.session_state.sessions[session_name] = photos
                    changes_made = True
            
            # Update Drive folder parents if storage is available
            if self.session_store.storage and move_operations:
                for move_op in move_operations:
                    try:
                        success = self.session_store.storage.move_image(
                            move_op['file_id'],
                            move_op['from_session'],
                            move_op['to_session']
                        )
                        if success:
                            logger.info(f"Moved photo in Drive: {move_op['file_id']} from {move_op['from_session']} to {move_op['to_session']}")
                    except Exception as e:
                        logger.error(f"Failed to move photo in Drive: {e}")
                        st.error(f"⚠️ Failed to update Drive folder for some photos. Changes saved locally.")
            
            if changes_made:
                st.success("✓ Photos reorganized!" + (" Drive folders updated." if move_operations else ""))
                st.rerun()
        
        # Add selection buttons for viewing details
        st.divider()
        st.markdown("**Click a photo to view details:**")
        
        # Group photos by session for display
        for session_name in sorted(self.session_store.sessions.keys()):
            photos = self.session_store.sessions[session_name]
            if photos:
                st.markdown(f"**📁 {session_name}**")
                cols = st.columns(min(len(photos), 8))
                for idx, photo in enumerate(photos):
                    with cols[idx % 8]:
                        variant_icon = "📝" if photo.get('variant') == 'annotated' else "📷"
                        if st.button(f"{variant_icon} #{photo['id']}", key=f"view_{photo['id']}", use_container_width=True):
                            st.session_state['gallery_selected'] = {
                                'photo_id': photo['id'],
                                'session': session_name
                            }
                            st.rerun()
        
        # Handle tile click for details
        if st.session_state.get('gallery_selected'):
            selected_info = st.session_state['gallery_selected']
            selected_photo = self.session_store.get_photo(
                selected_info['photo_id'],
                selected_info['session']
            )
            if selected_photo:
                st.divider()
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
        # No header on About page per requirements
        
        st.markdown("""
        <style>
            .hero-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem 1rem;
            }
            .hero-title {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                color: #1f1f1f;
            }
            .hero-greeting {
                font-size: 2rem;
                color: #666;
                margin-bottom: 0.5rem;
            }
            .hero-subtitle {
                font-size: 1.2rem;
                color: #666;
                margin-bottom: 2rem;
                line-height: 1.6;
            }
            .feature-list {
                font-size: 1.1rem;
                line-height: 2;
                margin-bottom: 2rem;
            }
            .feature-list li {
                margin-bottom: 0.5rem;
            }
            .signin-button {
                margin-top: 2rem;
            }
            .hero-image {
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                margin-top: 2rem;
            }
            /* Mobile responsive design - stack content vertically with image below login */
            @media (max-width: 768px) {
                .hero-title {
                    font-size: 2rem;
                }
                .hero-greeting {
                    font-size: 1.5rem;
                }
                .hero-subtitle {
                    font-size: 1rem;
                }
                .hero-image {
                    margin-top: 1rem;
                    margin-bottom: 2rem;
                }
                /* Reverse column order on mobile so image appears after login */
                div[data-testid="column"] {
                    display: flex;
                    flex-direction: column-reverse;
                }
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Check authentication status
        user_authenticated = is_authenticated()
        user_email = get_user_email()
        
        col_left, col_right = st.columns([1.2, 1])
        
        with col_left:
            # Logo
            try:
                logo_path = Path(__file__).parent / "assets" / "logo.png"
                if logo_path.exists():
                    logo_image = Image.open(logo_path)
                    st.image(logo_image, width=250)
            except Exception:
                pass
            
            st.markdown('<div class="hero-greeting">Hello!</div>', unsafe_allow_html=True)
            st.markdown('<div class="hero-title">Welcome to Fieldmap.</div>', unsafe_allow_html=True)
            
            st.markdown("""
            <div class="hero-subtitle">
            A non-profit app to assist biomedical engineers with lab efficiency and documentation.
            </div>
            """, unsafe_allow_html=True)
            
            # Feature bullets
            st.markdown("""
            <div class="feature-list">
            <ul style="list-style-type: disc; padding-left: 1.5rem;">
                <li>📸 Capture and annotate photos directly in your browser</li>
                <li>📁 Organize images into sessions (albums)</li>
                <li>☁️ Auto-sync to your Google Drive</li>
                <li>✏️ Edits create new copies, originals stay untouched</li>
                <li>🔐 Secure, private storage in your own Drive</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Authentication section
            st.markdown('<div class="signin-button">', unsafe_allow_html=True)
            
            if user_authenticated:
                # User is signed in
                st.success(f"✅ Signed in as **{user_email}**")
                st.info("📱 Use the sidebar to access Fieldmap and Gallery")
                
                if st.button("Sign Out", key="signout_btn", type="secondary", use_container_width=True):
                    logout()
                    st.rerun()
            else:
                # User is not signed in
                st.markdown("### Sign in with Google")
                st.markdown("Click below to sign in and start using Fieldmap")
                
                if st.button("🔐 Sign in with Google", key="signin_btn", type="primary", use_container_width=True):
                    # Generate authorization URL and redirect
                    try:
                        auth_url, state = get_authorization_url()
                        
                        # Store state in session for CSRF protection
                        st.session_state["oauth_state"] = state
                        
                        # Redirect to Google OAuth
                        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}" />', unsafe_allow_html=True)
                        st.info("Redirecting to Google sign-in...")
                        
                    except Exception as e:
                        st.error(f"❌ Failed to initiate sign-in: {str(e)}")
                        logger.error(f"OAuth initialization failed: {e}", exc_info=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_right:
            # Hero image
            try:
                hero_path = Path(__file__).parent / "assets" / "biomedical.jpg"
                if hero_path.exists():
                    hero_image = Image.open(hero_path)
                    st.markdown('<div class="hero-image">', unsafe_allow_html=True)
                    st.image(hero_image, use_column_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                logger.warning(f"Failed to load hero image: {e}")


class App:
    """Main application class that orchestrates the UI and routing"""
    
    def __init__(self):
        logger.info("Initializing Fieldmap application")
        
        # Initialize storage backend with user OAuth credentials
        storage_backend = None
        
        if is_authenticated():
            user_credentials = get_user_credentials()
            
            if user_credentials:
                try:
                    logger.info("Attempting to initialize Google Drive storage with user OAuth...")
                    storage_backend = GoogleDriveStorage(user_credentials)
                    logger.info("✓ Google Drive storage (user OAuth) initialized successfully")
                    
                    # Test connection
                    try:
                        storage_backend.test_connection()
                        logger.info("✓ Successfully connected to Google Drive API")
                    except Exception as e:
                        logger.error(f"✗ Failed to connect to Google Drive API: {e}", exc_info=True)
                        logger.warning("⚠️ Drive storage may be unavailable")
                        storage_backend = None
                except Exception as e:
                    logger.error(f"✗ Failed to initialize Google Drive storage: {e}", exc_info=True)
                    storage_backend = None
            else:
                logger.warning("⚠️ User credentials not available")
        else:
            logger.info("User not authenticated - Drive storage will be initialized after sign-in")
        
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
            
            # Check if user is authenticated
            user_is_authenticated = is_authenticated()
            
            st.markdown('<div class="sidebar-section-label">Sections</div>', unsafe_allow_html=True)
            
            if not user_is_authenticated:
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
        # Check authentication status
        user_is_authenticated = is_authenticated()
        
        # Implement navigation gating: force About page if not authenticated
        if not user_is_authenticated:
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
