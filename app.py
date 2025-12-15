"""
Fieldmap - Cadaver Lab Photo Annotation App
A Streamlit-based mobile web app for biomedical engineers to capture, annotate, and organize photos
Refactored with OOP architecture
"""

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
from pathlib import Path
from streamlit_drawable_canvas import st_canvas
import numpy as np
import logging

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
        max-width: 400px;
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
    
    def __init__(self):
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
        photo_data = {
            'id': st.session_state.photo_counter,
            'original_image': image.copy(),
            'current_image': image.copy(),
            'comment': comment,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_annotations': False,
            'draw_version': 0
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


class Annotator:
    """Handles image annotation operations"""
    
    @staticmethod
    def draw_annotation_on_image(image, annotation_type, color, stroke_width, text="", position_percent=0.5):
        """
        Draw a simple annotation directly on the image using PIL.
        
        Args:
            image: PIL Image object
            annotation_type: Type of annotation ('arrow', 'circle', 'box', 'text')
            color: Color in hex format (e.g., '#FF0000')
            stroke_width: Width of the stroke
            text: Text to add (for text annotations)
            position_percent: Horizontal position on image (0.0=left to 1.0=right)
        
        Returns:
            PIL Image with annotation drawn
        """
        img_copy = image.copy()
        if img_copy.mode != 'RGB':
            img_copy = img_copy.convert('RGB')
        
        draw = ImageDraw.Draw(img_copy)
        width, height = img_copy.size
        
        center_x = int(width * position_percent)
        center_y = int(height * 0.5)
        
        if annotation_type == 'arrow':
            start_x, start_y = center_x, int(height * 0.2)
            end_x, end_y = center_x, int(height * 0.4)
            
            draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=stroke_width)
            
            arrow_size = stroke_width * 3
            draw.polygon([
                (end_x, end_y),
                (end_x - arrow_size, end_y - arrow_size),
                (end_x + arrow_size, end_y - arrow_size)
            ], fill=color)
        
        elif annotation_type == 'circle':
            radius = min(width, height) // 8
            draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], outline=color, width=stroke_width)
        
        elif annotation_type == 'box':
            box_size = min(width, height) // 6
            draw.rectangle([
                center_x - box_size, center_y - box_size,
                center_x + box_size, center_y + box_size
            ], outline=color, width=stroke_width)
        
        elif annotation_type == 'text' and text:
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "C:\\Windows\\Fonts\\arial.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
            ]
            
            font = None
            font_size = max(20, width // 30)
            
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, size=font_size)
                    break
                except (IOError, OSError):
                    continue
            
            if font is None:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = center_x - text_width // 2
            text_y = int(height * 0.1)
            
            padding = 5
            draw.rectangle([
                text_x - padding, text_y - padding,
                text_x + text_width + padding, text_y + text_height + padding
            ], fill='white', outline=color, width=2)
            
            draw.text((text_x, text_y), text, fill=color, font=font)
        
        return img_copy
    
    @staticmethod
    def merge_canvas_with_image(background_image, canvas_result):
        """
        Merge drawable canvas result with background image.
        
        Args:
            background_image: PIL Image (background)
            canvas_result: Canvas result from streamlit-drawable-canvas
        
        Returns:
            PIL Image with canvas drawing merged
        """
        if canvas_result is None or canvas_result.image_data is None:
            return background_image
        
        # Convert background to RGBA for alpha compositing
        bg = background_image.copy()
        if bg.mode != 'RGBA':
            bg = bg.convert('RGBA')
        
        # Get canvas drawing layer
        canvas_array = canvas_result.image_data
        canvas_img = Image.fromarray(canvas_array.astype('uint8'), 'RGBA')
        
        # Resize canvas to match background if needed
        if canvas_img.size != bg.size:
            canvas_img = canvas_img.resize(bg.size, Image.Resampling.LANCZOS)
        
        # Composite the images
        result = Image.alpha_composite(bg, canvas_img)
        
        # Convert back to RGB
        if result.mode == 'RGBA':
            rgb_result = Image.new('RGB', result.size, (255, 255, 255))
            rgb_result.paste(result, mask=result.split()[3])
            return rgb_result
        
        return result


class BasePage:
    """Base class for all pages"""
    
    def __init__(self, session_store, annotator):
        self.session_store = session_store
        self.annotator = annotator
    
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
                
                # Drawing section with canvas
                st.markdown("#### Draw on Photo")
                st.info("Draw directly on the photo with freehand or use shapes. Click 'Apply Drawing' to save.")
                
                # Initialize draw_version if not present (for backward compatibility)
                if 'draw_version' not in last_photo:
                    last_photo['draw_version'] = 0
                
                # Choose drawing mode
                col1, col2 = st.columns(2)
                with col1:
                    drawing_mode = st.selectbox(
                        "Drawing Mode:",
                        options=["freedraw", "line", "rect", "circle", "transform"],
                        format_func=lambda x: {
                            "freedraw": "Freehand",
                            "line": "Line",
                            "rect": "Rectangle",
                            "circle": "Circle",
                            "transform": "Transform"
                        }[x],
                        key="last_photo_drawing_mode"
                    )
                with col2:
                    stroke_color = st.color_picker(
                        "Color:",
                        value="#FF0000",
                        key="last_photo_stroke_color"
                    )
                
                stroke_width = st.slider(
                    "Stroke Width:",
                    min_value=1,
                    max_value=20,
                    value=3,
                    key="last_photo_stroke_width"
                )
                
                # Create a resized copy for display (fixed width 700px, preserve aspect ratio)
                display_image = last_photo['current_image'].copy()
                original_width, original_height = display_image.size
                display_width = min(700, original_width)
                aspect_ratio = original_height / original_width
                display_height = int(display_width * aspect_ratio)
                display_image = display_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                
                # Ensure display image is RGB
                if display_image.mode != 'RGB':
                    display_image = display_image.convert('RGB')
                
                # Display canvas with background image
                canvas_result = st_canvas(
                    fill_color="rgba(0, 0, 0, 0)",
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    background_image=display_image,
                    drawing_mode=drawing_mode,
                    key=f"canvas_{last_photo['id']}_{last_photo['draw_version']}",
                    height=display_height,
                    width=display_width,
                )
                
                # Apply drawing button
                if st.button("Apply Drawing", key="apply_drawing", type="primary"):
                    if canvas_result.image_data is not None:
                        # Merge canvas with display image
                        merged_display = self.annotator.merge_canvas_with_image(
                            display_image,
                            canvas_result
                        )
                        
                        # Scale back to original size if needed
                        if (display_width, display_height) != (original_width, original_height):
                            merged_image = merged_display.resize((original_width, original_height), Image.Resampling.LANCZOS)
                        else:
                            merged_image = merged_display
                        
                        last_photo['current_image'] = merged_image
                        last_photo['has_annotations'] = True
                        last_photo['draw_version'] += 1
                        st.success("Drawing applied to photo!")
                        st.rerun()


class GalleryPage(BasePage):
    """Gallery page for viewing and managing photos"""
    
    def render_photo_card(self, photo, session_name, cols):
        """Render a single photo card with clean iPhone-like styling"""
        with cols:
            st.markdown('<div class="photo-card">', unsafe_allow_html=True)
            
            # Thumbnail with container width for responsive sizing
            st.image(photo['current_image'], use_column_width=True)
            
            # Minimal metadata - extract time from timestamp
            timestamp_parts = photo['timestamp'].split()
            time_str = timestamp_parts[1] if len(timestamp_parts) > 1 else timestamp_parts[0]
            
            st.caption(f"**{session_name}** • ID {photo['id']}")
            st.caption(time_str)
            
            # Move control - compact
            other_sessions = [s for s in self.session_store.sessions.keys() if s != session_name]
            if other_sessions:
                col_move_label, col_move_btn = st.columns([3, 1])
                with col_move_label:
                    move_to = st.selectbox(
                        "Move to",
                        options=[""] + other_sessions,
                        key=f"move_select_{photo['id']}",
                        label_visibility="collapsed"
                    )
                with col_move_btn:
                    if move_to and st.button("Go", key=f"move_btn_{photo['id']}", use_container_width=True):
                        if self.session_store.move_photo(photo['id'], session_name, move_to):
                            st.success("Moved!")
                            st.rerun()
            
            if st.button("View", key=f"view_{photo['id']}", use_container_width=True):
                st.session_state[f'expand_photo_{photo['id']}'] = True
                st.rerun()
            
            if st.session_state.get(f'expand_photo_{photo['id']}', False):
                self._render_photo_details(photo, session_name)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render(self):
        st.header("Photo Gallery")
        
        view_session = st.selectbox(
            "View Session:",
            options=["All Sessions"] + list(self.session_store.sessions.keys()),
            key="gallery_session_filter"
        )
        
        photos_to_display = []
        if view_session == "All Sessions":
            for session_name, photos in self.session_store.sessions.items():
                for photo in photos:
                    photos_to_display.append((session_name, photo))
        else:
            for photo in self.session_store.sessions.get(view_session, []):
                photos_to_display.append((view_session, photo))
        
        if not photos_to_display:
            st.info("No photos yet. Use the Fieldmap page to capture photos!")
        else:
            st.write(f"**{len(photos_to_display)} photo(s) found**")
            
            # Display photos in responsive grid - 4 columns desktop, 2 mobile handled by Streamlit
            cols_per_row = 4
            for i in range(0, len(photos_to_display), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(photos_to_display):
                        session_name, photo = photos_to_display[i + j]
                        self.render_photo_card(photo, session_name, cols[j])
    
    def _render_photo_details(self, photo, session_name):
        """Render detailed photo view with edit capabilities"""
        with st.expander(f"Edit Photo {photo['id']}", expanded=True):
            if st.button("Close", key=f"close_{photo['id']}"):
                st.session_state[f'expand_photo_{photo['id']}'] = False
                st.rerun()
            
            st.markdown("---")
            
            # Show images
            if photo['has_annotations']:
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
                label="Download Photo" + (" (with annotations)" if photo['has_annotations'] else ""),
                data=buf,
                file_name=f"photo_{photo['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                key=f"download_{photo['id']}"
            )
            
            st.caption(f"**Session:** {session_name}")
            st.caption(f"**Time:** {photo['timestamp']}")
            
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
            
            # Drawing tools with canvas
            st.markdown("**Add Annotations**")
            st.info("Draw directly on the photo. Use 'Reset' to restore original.")
            
            # Initialize draw_version if not present (for backward compatibility)
            if 'draw_version' not in photo:
                photo['draw_version'] = 0
            
            col1, col2 = st.columns(2)
            with col1:
                drawing_mode = st.selectbox(
                    "Drawing Mode:",
                    options=["freedraw", "line", "rect", "circle"],
                    format_func=lambda x: {
                        "freedraw": "Freehand",
                        "line": "Line",
                        "rect": "Rectangle",
                        "circle": "Circle"
                    }[x],
                    key=f"drawing_mode_{photo['id']}"
                )
            with col2:
                stroke_color = st.color_picker(
                    "Color:",
                    value="#FF0000",
                    key=f"stroke_color_{photo['id']}"
                )
            
            stroke_width = st.slider(
                "Stroke Width:",
                min_value=1,
                max_value=20,
                value=3,
                key=f"stroke_width_{photo['id']}"
            )
            
            # Create a resized copy for display (fixed width 700px, preserve aspect ratio)
            display_image = photo['current_image'].copy()
            original_width, original_height = display_image.size
            display_width = min(700, original_width)
            aspect_ratio = original_height / original_width
            display_height = int(display_width * aspect_ratio)
            display_image = display_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            # Ensure display image is RGB
            if display_image.mode != 'RGB':
                display_image = display_image.convert('RGB')
            
            # Canvas for drawing
            canvas_result = st_canvas(
                fill_color="rgba(0, 0, 0, 0)",
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                background_image=display_image,
                drawing_mode=drawing_mode,
                key=f"gallery_canvas_{photo['id']}_{photo['draw_version']}",
                height=display_height,
                width=display_width,
            )
            
            col_apply, col_reset = st.columns(2)
            with col_apply:
                if st.button("Apply", key=f"apply_{photo['id']}"):
                    if canvas_result.image_data is not None:
                        # Merge canvas with display image
                        merged_display = self.annotator.merge_canvas_with_image(
                            display_image,
                            canvas_result
                        )
                        
                        # Scale back to original size if needed
                        if (display_width, display_height) != (original_width, original_height):
                            merged_image = merged_display.resize((original_width, original_height), Image.Resampling.LANCZOS)
                        else:
                            merged_image = merged_display
                        
                        photo['current_image'] = merged_image
                        photo['has_annotations'] = True
                        photo['draw_version'] += 1
                        st.success("Drawing applied!")
                        st.rerun()
            
            with col_reset:
                if st.button("Reset", key=f"reset_{photo['id']}"):
                    photo['current_image'] = photo['original_image'].copy()
                    photo['has_annotations'] = False
                    photo['draw_version'] += 1
                    st.success("Annotations cleared!")
                    st.rerun()
            
            st.divider()
            
            # Delete photo
            if st.button("Delete Photo", key=f"delete_{photo['id']}", type="secondary"):
                if self.session_store.delete_photo(photo['id'], session_name):
                    st.success("Photo deleted!")
                    st.session_state[f'expand_photo_{photo['id']}'] = False
                    st.rerun()


class AboutPage(BasePage):
    """About page with app information"""
    
    def render(self):
        st.title("About Fieldmap")
        st.markdown("""
        A mobile-optimized web app for cadaver lab photo documentation and annotation.
        
        **Key Features:**
        - Capture and annotate photos with freehand drawing
        - Organize photos into sessions
        - Export data to Excel
        
        **Version:** 2.0
        """)


class App:
    """Main application class that orchestrates the UI and routing"""
    
    def __init__(self):
        self.session_store = SessionStore()
        self.annotator = Annotator()
        self.pages = {
            'Fieldmap': FieldmapPage(self.session_store, self.annotator),
            'Gallery': GalleryPage(self.session_store, self.annotator),
            'About': AboutPage(self.session_store, self.annotator)
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
            st.markdown('<div class="sidebar-subtitle">Lab Photo Documentation</div>', unsafe_allow_html=True)
            
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
