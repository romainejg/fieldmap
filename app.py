"""
Fieldmap - Cadaver Lab Photo Annotation App
A Streamlit-based mobile web app for biomedical engineers to capture, annotate, and organize photos
Refactored with OOP architecture and Google Drive integration
"""

import streamlit as st
import pandas as pd
from PIL import Image
import io
import base64
from datetime import datetime
from pathlib import Path
import numpy as np
import logging
from components.photo_editor import photo_editor, decode_image_from_dataurl
from streamlit_sortables import sort_items
from google_auth import GoogleAuthHelper
from storage import LocalFolderStorage, GoogleDriveStorage

# Configure logger for this module
logger = logging.getLogger(__name__)

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
    
    def _initialize_state(self):
        """Initialize session state variables"""
        if 'sessions' not in st.session_state:
            st.session_state.sessions = {'Default': []}
        if 'current_session' not in st.session_state:
            st.session_state.current_session = 'Default'
        if 'photo_counter' not in st.session_state:
            st.session_state.photo_counter = 0
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'Fieldmap'
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
        
        # Save to storage backend (Google Drive)
        storage_uri = None
        file_id = None
        if self.storage:
            try:
                storage_uri = self.storage.save_image(session_name, photo_id, image)
                # Extract file ID from gdrive:// URI
                if storage_uri and storage_uri.startswith('gdrive://'):
                    file_id = storage_uri.replace('gdrive://', '')
            except Exception as e:
                logger.warning(f"Failed to save to storage: {e}")
        
        photo_data = {
            'id': photo_id,
            'original_image': image.copy(),
            'current_image': image.copy(),
            'thumbnail': thumbnail,  # Pre-generated thumbnail
            'thumb_data_url': thumb_data_url,  # Base64 for gallery tiles
            'comment': comment,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_annotations': False,
            'source_photo_id': None,  # None for original photos
            'variant': 'original',  # "original" or "annotated"
            'storage_uri': storage_uri,  # URI in cloud storage (if any)
            'file_id': file_id  # Google Drive file ID
        }
        st.session_state.sessions[session_name].append(photo_data)
        return photo_data['id']
    
    def add_derived_photo(self, base_photo_id, session_name, image, comment=None):
        """
        Create a new photo derived from an existing photo (e.g., annotated version).
        
        Args:
            base_photo_id: ID of the source photo
            session_name: Session to add the derived photo to
            image: PIL Image of the derived photo
            comment: Optional comment (defaults to base photo's comment)
        
        Returns:
            New photo ID
        """
        # Get the base photo
        base_photo = self.get_photo(base_photo_id, session_name)
        if not base_photo:
            raise ValueError(f"Base photo {base_photo_id} not found in session {session_name}")
        
        # Increment counter
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
        
        # Use base photo's comment if not provided
        if comment is None:
            comment = base_photo['comment']
        
        # Save to storage backend (Google Drive)
        storage_uri = None
        file_id = None
        if self.storage:
            try:
                storage_uri = self.storage.save_image(session_name, photo_id, image)
                # Extract file ID from gdrive:// URI
                if storage_uri and storage_uri.startswith('gdrive://'):
                    file_id = storage_uri.replace('gdrive://', '')
            except Exception as e:
                logger.warning(f"Failed to save to storage: {e}")
        
        photo_data = {
            'id': photo_id,
            'original_image': image.copy(),  # For derived photos, this is the annotated version
            'current_image': image.copy(),
            'thumbnail': thumbnail,
            'thumb_data_url': thumb_data_url,  # Base64 for gallery tiles
            'comment': comment,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_annotations': True,  # Derived photos are annotated by definition
            'source_photo_id': base_photo_id,  # Link to original
            'variant': 'annotated',
            'storage_uri': storage_uri,  # URI in cloud storage (if any)
            'file_id': file_id  # Google Drive file ID
        }
        st.session_state.sessions[session_name].append(photo_data)
        return photo_data['id']
    
    def move_photo(self, photo_id, from_session, to_session):
        """Move a photo from one session to another"""
        if from_session in st.session_state.sessions and to_session in st.session_state.sessions:
            photos = st.session_state.sessions[from_session]
            for i, photo in enumerate(photos):
                if photo['id'] == photo_id:
                    moved_photo = photos.pop(i)
                    st.session_state.sessions[to_session].append(moved_photo)
                    return True
        return False
    
    def delete_photo(self, photo_id, session_name):
        """Delete a photo from a session"""
        if session_name in st.session_state.sessions:
            photos = st.session_state.sessions[session_name]
            for i, photo in enumerate(photos):
                if photo['id'] == photo_id:
                    photos.pop(i)
                    return True
        return False
    
    def update_photo_comment(self, photo_id, session_name, new_comment):
        """Update the comment for a photo"""
        if session_name in st.session_state.sessions:
            for photo in st.session_state.sessions[session_name]:
                if photo['id'] == photo_id:
                    photo['comment'] = new_comment
                    return True
        return False
    
    def get_photo(self, photo_id, session_name):
        """Get a photo by ID from a session"""
        if session_name in st.session_state.sessions:
            for photo in st.session_state.sessions[session_name]:
                if photo['id'] == photo_id:
                    return photo
        return None
    
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
                st.warning("Logo not found at assets/logo.png")
        except Exception as e:
            st.markdown('<div class="logo-fallback">Fieldmap</div>', unsafe_allow_html=True)
            st.error(f"Error loading logo: {str(e)}")
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
                # Comment section
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
                
                # Photo editor section
                st.markdown("#### Edit Photo")
                st.info("Use the annotation tools below. Click Save to apply changes or Cancel to discard.")
                
                # Call the photo editor component automatically
                editor_result = photo_editor(
                    image=last_photo['current_image'],
                    key=f"photo_editor_{last_photo['id']}"
                )
                
                # Handle editor result
                if editor_result is not None:
                    if editor_result.get('saved') and editor_result.get('pngDataUrl'):
                        # Decode the edited image
                        try:
                            edited_image = decode_image_from_dataurl(editor_result['pngDataUrl'])
                            
                            # Create a NEW derived photo instead of modifying the original
                            new_photo_id = self.session_store.add_derived_photo(
                                base_photo_id=last_photo['id'],
                                session_name=self.session_store.current_session,
                                image=edited_image,
                                comment=last_photo['comment']
                            )
                            
                            # Update last_saved_photo_id to point to the new annotated photo
                            st.session_state.last_saved_photo_id = new_photo_id
                            
                            st.success(f"Annotated copy created! (Photo #{new_photo_id})")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error processing edited image: {str(e)}")
                    elif editor_result.get('cancelled'):
                        # User cancelled editing
                        st.info("Editing cancelled")
                        st.rerun()


class GalleryPage(BasePage):
    """Gallery page for viewing and managing photos"""
    
    def render(self):
        st.header("Photo Gallery")
        
        # Session filter only (no view mode selector)
        view_session = st.selectbox(
            "View Session:",
            options=["All Sessions"] + list(self.session_store.sessions.keys()),
            key="gallery_session_filter"
        )
        
        # Always use draggable view with small tiles
        self._render_draggable_view()
    
    def _render_draggable_view(self):
        """Render draggable view with photo thumbnails as tiles"""
        st.info("📱 Drag photos between sessions to organize them. Click a tile to view details.")
        
        # Build the list of containers with items
        sortable_containers = []
        original_structure = {}  # Track original session -> photo mapping
        session_name_map = {}  # Map container index to session name
        
        for idx, session_name in enumerate(sorted(self.session_store.sessions.keys())):
            photos = self.session_store.sessions[session_name]
            items = []
            for photo in photos:
                # Generate thumbnail data URL if not already present
                if 'thumb_data_url' not in photo or not photo['thumb_data_url']:
                    thumb = photo.get('thumbnail')
                    if not thumb:
                        thumb = photo['current_image'].copy()
                        thumb.thumbnail((100, 100), Image.Resampling.LANCZOS)
                        photo['thumbnail'] = thumb
                    
                    # Convert to data URL
                    thumb_buffer = io.BytesIO()
                    thumb.save(thumb_buffer, format='PNG')
                    thumb_buffer.seek(0)
                    thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
                    photo['thumb_data_url'] = f"data:image/png;base64,{thumb_base64}"
                
                # Validate data URL format to prevent XSS
                thumb_url = photo['thumb_data_url']
                if not thumb_url.startswith('data:image/'):
                    # Invalid format, regenerate
                    thumb = photo.get('thumbnail', photo['current_image'].copy())
                    thumb.thumbnail((100, 100), Image.Resampling.LANCZOS)
                    thumb_buffer = io.BytesIO()
                    thumb.save(thumb_buffer, format='PNG')
                    thumb_buffer.seek(0)
                    thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode()
                    thumb_url = f"data:image/png;base64,{thumb_base64}"
                    photo['thumb_data_url'] = thumb_url
                
                # Use HTML with embedded image for the tile (data URL is safe, generated internally)
                # Variant badge is emoji only (safe)
                variant_badge = "📝 " if photo.get('variant') == 'annotated' else ""
                # Create HTML item with image
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
                # Also map by HTML content (streamlit-sortables returns HTML)
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
        
        # Custom CSS for tiles - fixed size, only shadow changes on hover
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
        
        # Render sortables
        sorted_containers = sort_items(
            sortable_containers,
            multi_containers=True,
            direction="vertical",
            custom_style=custom_style,
            key="gallery_sortable"
        )
        
        # Detect changes and update session store
        if sorted_containers != sortable_containers:
            # Build new structure from sorted containers
            new_structure = {}
            changes_made = False
            
            for idx, container in enumerate(sorted_containers):
                # Use the session name map for robust session name retrieval
                if idx < len(session_name_map):
                    session_name = session_name_map[idx]
                else:
                    # Fallback: extract from header
                    session_name = container["header"].split(" (")[0].replace("📁 ", "").strip()
                
                new_photos = []
                for item_id in container["items"]:
                    if item_id in original_structure:
                        photo_info = original_structure[item_id]
                        new_photos.append(photo_info['photo'])
                
                new_structure[session_name] = new_photos
            
            # Update session state with new structure, ensuring all sessions exist
            for session_name, photos in new_structure.items():
                # Ensure session exists in session state
                if session_name not in st.session_state.sessions:
                    st.session_state.sessions[session_name] = []
                
                # Only update if there's an actual change
                if st.session_state.sessions[session_name] != photos:
                    st.session_state.sessions[session_name] = photos
                    changes_made = True
            
            # Only show success and rerun if actual changes were made
            if changes_made:
                st.success("✓ Photos reorganized!")
                st.rerun()
        
        # Click-to-select interface below the draggable board
        st.divider()
        st.markdown("**Select a photo to view details:**")
        
        # Create a minimal grid of clickable thumbnails
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
                            # Ensure thumbnail data URL exists
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
                            
                            # Display thumbnail using markdown with data URL
                            st.markdown(
                                f'<img src="{photo["thumb_data_url"]}" style="width:100%;border-radius:4px;cursor:pointer;" />',
                                unsafe_allow_html=True
                            )
                            
                            # Button to select
                            variant_badge = "📝" if photo.get('variant') == 'annotated' else ""
                            button_label = f"{variant_badge}#{photo['id']}" if variant_badge else f"#{photo['id']}"
                            
                            if st.button(button_label, key=f"select_{photo['id']}", use_container_width=True):
                                st.session_state['gallery_selected'] = {
                                    'photo_id': photo['id'],
                                    'session': session_name
                                }
                                st.rerun()
        
        # Show details panel in expander if a photo is selected
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
        
        # Show variant and source info
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
        
        # Show images
        if photo.get('variant') == 'annotated' and photo.get('source_photo_id'):
            # For annotated photos, show the annotated version
            st.markdown("**Annotated Image:**")
            st.image(photo['current_image'], use_column_width=True)
        elif photo['has_annotations']:
            # Legacy support for old annotated photos
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
        
        # Download button
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
        
        # Edit comment
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
        
        # Drawing tools with marker.js
        st.markdown("**Add Annotations**")
        
        col_edit, col_reset = st.columns(2)
        with col_edit:
            # Edit photo button
            if st.button("Edit Photo", key=f"edit_photo_gallery_{photo['id']}", type="primary"):
                st.session_state[f'show_gallery_editor_{photo["id"]}'] = True
                st.rerun()
        
        with col_reset:
            # Only show reset for old-style annotated photos
            if photo['has_annotations'] and not photo.get('source_photo_id'):
                if st.button("Reset Annotations", key=f"reset_{photo['id']}", type="secondary"):
                    photo['current_image'] = photo['original_image'].copy()
                    photo['has_annotations'] = False
                    st.success("Annotations cleared!")
                    st.rerun()
        
        # Display photo editor component when requested
        if st.session_state.get(f'show_gallery_editor_{photo["id"]}', False):
            st.info("Use the annotation tools below. Click Save to apply changes or Cancel to discard.")
            
            # Call the photo editor component
            editor_result = photo_editor(
                image=photo['current_image'],
                key=f"photo_editor_gallery_{photo['id']}"
            )
            
            # Handle editor result
            if editor_result is not None:
                if editor_result.get('saved') and editor_result.get('pngDataUrl'):
                    # Decode the edited image
                    try:
                        edited_image = decode_image_from_dataurl(editor_result['pngDataUrl'])
                        
                        # Create a NEW derived photo instead of modifying the original
                        new_photo_id = self.session_store.add_derived_photo(
                            base_photo_id=photo['id'],
                            session_name=session_name,
                            image=edited_image,
                            comment=photo['comment']
                        )
                        
                        # Reset editor state
                        st.session_state[f'show_gallery_editor_{photo["id"]}'] = False
                        
                        # Update selected photo to the new one
                        st.session_state['gallery_selected'] = {
                            'photo_id': new_photo_id,
                            'session': session_name
                        }
                        
                        st.success(f"Annotated copy created! (Photo #{new_photo_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error processing edited image: {str(e)}")
                elif editor_result.get('cancelled'):
                    # User cancelled editing
                    st.session_state[f'show_gallery_editor_{photo["id"]}'] = False
                    st.info("Editing cancelled")
                    st.rerun()
        
        st.divider()
        
        # Move photo to another session
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
        
        # Delete photo
        if st.button("🗑️ Delete Photo", key=f"delete_{photo['id']}", type="secondary"):
            if self.session_store.delete_photo(photo['id'], session_name):
                st.session_state['gallery_selected'] = None
                st.success("Photo deleted!")
                st.rerun()


class AboutPage(BasePage):
    """About page with app information"""
    
    def render(self):
        st.title("About Fieldmap")
        st.markdown("""
        A mobile-optimized web app for cadaver lab photo documentation and annotation.
        
        **Key Features:**
        - 📸 Capture and annotate photos with drawing tools
        - 📁 Organize photos into sessions
        - 📝 Create annotated copies (keeps originals unchanged)
        - ☁️ Google Drive cloud storage (required)
        - 📊 Export data to Excel
        - 🔐 Secure Google OAuth authentication
        - 🖼️ Drag-and-drop gallery organization
        
        **Version:** 4.0
        
        ---
        
        ### Google Drive Storage (Required)
        
        Fieldmap uses Google Drive as its exclusive storage backend. All photos are automatically 
        saved to your Google Drive under `Fieldmap/<SessionName>/`.
        
        **Setup Requirements:**
        
        1. **OAuth Credentials (Web Application)**
           - Type: Web application (not Desktop)
           - Credentials stored in GitHub Secrets or Streamlit Cloud Secrets
           - No credentials.json file in repository
        
        2. **For Streamlit Cloud Deployment:**
           - Set `GOOGLE_OAUTH_CLIENT_JSON` secret in Streamlit Cloud UI
           - Set `GOOGLE_REDIRECT_URI` secret (e.g., `https://fieldmap.streamlit.app`)
           - Sign in with Google using the sidebar button
        
        3. **For Local Development:**
           - Create `.streamlit/secrets.toml` with:
             ```toml
             GOOGLE_OAUTH_CLIENT_JSON = '''{"web": {...}}'''
             GOOGLE_REDIRECT_URI = "http://localhost:8501"
             ```
        
        **See README.md for detailed setup instructions.**
        
        ---
        
        ### How Photo Editing Works
        
        When you edit a photo, the app creates a **new annotated copy** while keeping the original unchanged:
        
        - ✅ Original photo remains pristine
        - ✅ Annotated copy links back to original
        - ✅ Multiple edits create multiple copies
        - ✅ Easy to track photo provenance
        - ✅ All versions saved to Google Drive
        
        ### Annotation Tools
        
        The editor provides several drawing tools:
        - ✏️ Freehand drawing
        - ➡️ Arrows
        - ━ Lines
        - ⭕ Unfilled circles/ellipses
        - ▭ Unfilled rectangles
        - 🔤 Text annotations
        
        This ensures you never lose your original data!
        """)




class App:
    """Main application class that orchestrates the UI and routing"""
    
    def __init__(self):
        # Initialize Google authentication
        self.google_auth = GoogleAuthHelper()
        
        # Initialize storage backend based on authentication
        # Google Drive is the ONLY storage option
        storage_backend = None
        if self.google_auth.is_authenticated():
            try:
                storage_backend = GoogleDriveStorage(self.google_auth)
                logger.info("Google Drive storage initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Drive storage: {e}")
                st.warning(f"⚠️ Could not connect to Google Drive: {str(e)}")
        
        self.session_store = SessionStore(storage_backend=storage_backend)
        self.pages = {
            'Fieldmap': FieldmapPage(self.session_store),
            'Gallery': GalleryPage(self.session_store),
            'About': AboutPage(self.session_store)
        }
    
    def render_sidebar(self):
        """Render sidebar with logo and navigation"""
        with st.sidebar:
            # Display logo with larger size
            st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
            try:
                logo_path = Path(__file__).parent / "assets" / "logo.png"
                if logo_path.exists():
                    logo_image = Image.open(logo_path)
                    st.image(logo_image, use_column_width=True)
                else:
                    st.markdown('<div class="logo-fallback">Fieldmap</div>', unsafe_allow_html=True)
                    st.warning("Logo not found at assets/logo.png")
            except Exception as e:
                st.markdown('<div class="logo-fallback">Fieldmap</div>', unsafe_allow_html=True)
                st.error(f"Error loading logo: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # App title and subtitle
            st.markdown('<div class="sidebar-title">Fieldmap</div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-subtitle">Documentation support for the cadaver lab.</div>', unsafe_allow_html=True)
            
            # Navigation section with label
            st.markdown('<div class="sidebar-section-label">Sections</div>', unsafe_allow_html=True)
            current_index = ['Fieldmap', 'Gallery', 'About'].index(self.session_store.current_page)
            selected_page = st.radio(
                "Navigation",
                options=['Fieldmap', 'Gallery', 'About'],
                index=current_index,
                key="navigation_radio",
                label_visibility="collapsed"
            )
            self.session_store.current_page = selected_page
            
            # Google authentication UI (always shown, storage is Google-only)
            self.google_auth.render_auth_ui()
    
    def run(self):
        """Main application entry point"""
        self.render_sidebar()
        
        # Render the selected page
        current_page = self.pages.get(self.session_store.current_page)
        if current_page:
            current_page.render()


# Run the application
if __name__ == "__main__":
    app = App()
    app.run()
