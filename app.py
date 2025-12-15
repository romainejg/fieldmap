"""
Fieldmap - Cadaver Lab Photo Annotation App
A Streamlit-based mobile web app for biomedical engineers to capture, annotate, and organize photos
NEW APPROACH: Simpler drawing interface without streamlit-drawable-canvas
"""

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime
import hashlib

# Configure page for mobile optimization
st.set_page_config(
    page_title="Fieldmap - Lab Photos",
    page_icon="📸",
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
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        background-color: #f9f9f9;
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
        padding: 20px 0;
    }
    .sidebar-logo img {
        max-width: 150px;
        margin-bottom: 10px;
    }
    .sidebar-title {
        font-size: 1.5em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sessions' not in st.session_state:
    st.session_state.sessions = {'Default': []}
if 'current_session' not in st.session_state:
    st.session_state.current_session = 'Default'
if 'photo_counter' not in st.session_state:
    st.session_state.photo_counter = 0
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Fieldmap'

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
    # Create a copy to avoid modifying original
    img_copy = image.copy()
    if img_copy.mode != 'RGB':
        img_copy = img_copy.convert('RGB')
    
    draw = ImageDraw.Draw(img_copy)
    width, height = img_copy.size
    
    # Calculate horizontal position based on percentage, vertical is centered
    center_x = int(width * position_percent)
    center_y = int(height * 0.5)  # Always center vertically
    
    if annotation_type == 'arrow':
        # Draw a simple arrow pointing down, centered at position
        start_x, start_y = center_x, int(height * 0.2)
        end_x, end_y = center_x, int(height * 0.4)
        
        # Main line
        draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=stroke_width)
        
        # Arrowhead
        arrow_size = stroke_width * 3
        draw.polygon([
            (end_x, end_y),
            (end_x - arrow_size, end_y - arrow_size),
            (end_x + arrow_size, end_y - arrow_size)
        ], fill=color)
    
    elif annotation_type == 'circle':
        # Draw a circle centered at position
        radius = min(width, height) // 8
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], outline=color, width=stroke_width)
    
    elif annotation_type == 'box':
        # Draw a rectangle centered at position
        box_size = min(width, height) // 6
        draw.rectangle([
            center_x - box_size, center_y - box_size,
            center_x + box_size, center_y + box_size
        ], outline=color, width=stroke_width)
    
    elif annotation_type == 'text' and text:
        # Draw text annotation
        # Try multiple common font paths for cross-platform compatibility
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"  # Alternative Linux
        ]
        
        font = None
        font_size = max(20, width // 30)
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, size=font_size)
                break
            except (IOError, OSError):
                continue
        
        # Fallback to default font if none found
        if font is None:
            font = ImageFont.load_default()
        
        # Draw text with background for visibility
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = center_x - text_width // 2
        text_y = int(height * 0.1)
        
        # Background rectangle
        padding = 5
        draw.rectangle([
            text_x - padding, text_y - padding,
            text_x + text_width + padding, text_y + text_height + padding
        ], fill='white', outline=color, width=2)
        
        # Text
        draw.text((text_x, text_y), text, fill=color, font=font)
    
    return img_copy

def create_new_session(session_name):
    """Create a new session"""
    if session_name and session_name not in st.session_state.sessions:
        st.session_state.sessions[session_name] = []
        return True
    return False

def add_photo_to_session(image, session_name, comment=""):
    """Add a photo with metadata to a session"""
    st.session_state.photo_counter += 1
    photo_data = {
        'id': st.session_state.photo_counter,
        'original_image': image.copy(),  # Keep original
        'current_image': image.copy(),   # Working copy with annotations
        'comment': comment,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'has_annotations': False
    }
    st.session_state.sessions[session_name].append(photo_data)
    return photo_data['id']

def move_photo(photo_id, from_session, to_session):
    """Move a photo from one session to another"""
    if from_session in st.session_state.sessions and to_session in st.session_state.sessions:
        photos = st.session_state.sessions[from_session]
        for i, photo in enumerate(photos):
            if photo['id'] == photo_id:
                moved_photo = photos.pop(i)
                st.session_state.sessions[to_session].append(moved_photo)
                return True
    return False

def delete_photo(photo_id, session_name):
    """Delete a photo from a session"""
    if session_name in st.session_state.sessions:
        photos = st.session_state.sessions[session_name]
        for i, photo in enumerate(photos):
            if photo['id'] == photo_id:
                photos.pop(i)
                return True
    return False

def update_photo_comment(photo_id, session_name, new_comment):
    """Update the comment for a photo"""
    if session_name in st.session_state.sessions:
        for photo in st.session_state.sessions[session_name]:
            if photo['id'] == photo_id:
                photo['comment'] = new_comment
                return True
    return False

def add_annotation_to_photo(photo_id, session_name, annotation_type, color, stroke_width, text="", position=0.5):
    """Add an annotation directly to the photo"""
    if session_name in st.session_state.sessions:
        for photo in st.session_state.sessions[session_name]:
            if photo['id'] == photo_id:
                # Apply annotation to current image
                photo['current_image'] = draw_annotation_on_image(
                    photo['current_image'],
                    annotation_type,
                    color,
                    stroke_width,
                    text,
                    position
                )
                photo['has_annotations'] = True
                return True
    return False

def reset_photo_annotations(photo_id, session_name):
    """Reset photo to original (remove all annotations)"""
    if session_name in st.session_state.sessions:
        for photo in st.session_state.sessions[session_name]:
            if photo['id'] == photo_id:
                photo['current_image'] = photo['original_image'].copy()
                photo['has_annotations'] = False
                return True
    return False

def export_to_excel():
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

# Sidebar with logo and navigation
with st.sidebar:
    # Display logo
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    try:
        logo_image = Image.open("/home/runner/work/fieldmap/fieldmap/logo.png")
        st.image(logo_image, use_column_width=True)
    except:
        st.write("📸")  # Fallback if logo not found
    st.markdown('</div>', unsafe_allow_html=True)
    
    # App title
    st.markdown('<div class="sidebar-title">Cadaver Lab</div>', unsafe_allow_html=True)
    
    # Navigation
    st.session_state.current_page = st.selectbox(
        "Navigation",
        options=['Fieldmap', 'Gallery', 'About'],
        index=['Fieldmap', 'Gallery', 'About'].index(st.session_state.current_page),
        key="navigation_select"
    )

# Main content area based on selected page
if st.session_state.current_page == 'About':
    # About page
    st.title("About Fieldmap")
    st.markdown("""
    ## Cadaver Lab Photo Annotation App
    
    Fieldmap is a mobile-optimized web application designed for biomedical engineers working in cadaver labs. 
    This app allows users to capture photos, annotate them, add comments, organize them into sessions, and export data.
    
    ### Features
    
    - **📸 Photo Capture**: Take photos directly using your mobile device camera
    - **📝 Annotations**: Draw arrows, circles, boxes, and add text labels to photos
    - **💬 Comments**: Add descriptive notes to each photo
    - **🗂️ Session Organization**: Organize photos into different sessions
    - **📊 Export**: Export all data to Excel for analysis
    
    ### Version
    Fieldmap v2.0 - Biomedical Engineering Lab Documentation System
    
    ---
    *Developed for biomedical engineers and researchers working in cadaver labs and similar settings.*
    """)

elif st.session_state.current_page == 'Gallery':
    # Gallery page
    st.header("Photo Gallery")
    
    # Filter by session
    view_session = st.selectbox(
        "View Session:",
        options=["All Sessions"] + list(st.session_state.sessions.keys()),
        key="gallery_session_filter"
    )
    
    # Collect photos to display
    photos_to_display = []
    if view_session == "All Sessions":
        for session_name, photos in st.session_state.sessions.items():
            for photo in photos:
                photos_to_display.append((session_name, photo))
    else:
        for photo in st.session_state.sessions.get(view_session, []):
            photos_to_display.append((view_session, photo))
    
    if not photos_to_display:
        st.info("No photos yet. Use the Fieldmap page to capture photos!")
    else:
        st.write(f"**{len(photos_to_display)} photo(s) found**")
        
        # Display photos in a grid layout (iPhone-style)
        # Create rows with 3 columns for thumbnails
        cols_per_row = 3
        for i in range(0, len(photos_to_display), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(photos_to_display):
                    session_name, photo = photos_to_display[i + j]
                    with cols[j]:
                        # Thumbnail image
                        st.image(photo['current_image'], use_column_width=True)
                        
                        # Session badge and metadata
                        st.markdown(f"""
                        <div style="font-size: 0.8em; padding: 2px;">
                            <span style="background-color: #4CAF50; color: white; padding: 2px 6px; border-radius: 8px; font-size: 0.75em;">{session_name}</span>
                            <br/>ID: {photo['id']} | 🎨: {"✓" if photo['has_annotations'] else "✗"}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Quick move dropdown
                        other_sessions = [s for s in st.session_state.sessions.keys() if s != session_name]
                        if other_sessions:
                            move_to = st.selectbox(
                                "Move to:",
                                options=[""] + other_sessions,
                                key=f"move_select_{photo['id']}",
                                label_visibility="collapsed"
                            )
                            if move_to:
                                if move_photo(photo['id'], session_name, move_to):
                                    st.success(f"Moved!")
                                    st.rerun()
                        
                        # Click to view/edit button
                        if st.button("📝 View/Edit", key=f"view_{photo['id']}", use_container_width=True):
                            st.session_state[f'expand_photo_{photo['id']}'] = True
                            st.rerun()
                        
                        # Expandable full details
                        if st.session_state.get(f'expand_photo_{photo['id']}', False):
                            with st.expander(f"✏️ Edit Photo {photo['id']}", expanded=True):
                                # Close button
                                if st.button("✖ Close", key=f"close_{photo['id']}"):
                                    st.session_state[f'expand_photo_{photo['id']}'] = False
                                    st.rerun()
                                
                                st.markdown("---")
                                
                                # Show original and current (annotated) images
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
                                    label="📥 Download Photo" + (" (with annotations)" if photo['has_annotations'] else ""),
                                    data=buf,
                                    file_name=f"photo_{photo['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                    mime="image/png",
                                    key=f"download_{photo['id']}"
                                )
                                
                                # Metadata
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
                                if st.button("💾 Update Comment", key=f"update_{photo['id']}"):
                                    update_photo_comment(photo['id'], session_name, new_comment)
                                    st.success("Comment updated!")
                                    st.rerun()
                                
                                st.divider()
                                
                                # Drawing tools
                                st.markdown("**🎨 Add Annotations**")
                                st.info("💡 Annotations are added directly to the photo. Use 'Reset' to remove all.")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    annotation_type = st.selectbox(
                                        "Type:",
                                        options=["arrow", "circle", "box", "text"],
                                        format_func=lambda x: {
                                            "arrow": "↗️ Arrow",
                                            "circle": "⭕ Circle",
                                            "box": "⬜ Box",
                                            "text": "📝 Text"
                                        }[x],
                                        key=f"annotation_type_{photo['id']}"
                                    )
                                with col2:
                                    annotation_color = st.color_picker(
                                        "Color:",
                                        value="#FF0000",
                                        key=f"color_{photo['id']}"
                                    )
                                
                                stroke_width = st.slider(
                                    "Line Width:",
                                    min_value=1,
                                    max_value=10,
                                    value=3,
                                    key=f"stroke_{photo['id']}"
                                )
                                
                                annotation_text = ""
                                if annotation_type == "text":
                                    annotation_text = st.text_input(
                                        "Text:",
                                        key=f"text_{photo['id']}",
                                        placeholder="Enter text..."
                                    )
                                
                                position = st.slider(
                                    "Position (left ← → right):",
                                    min_value=0.0,
                                    max_value=1.0,
                                    value=0.5,
                                    step=0.1,
                                    key=f"position_{photo['id']}"
                                )
                                
                                col_add, col_reset = st.columns(2)
                                with col_add:
                                    can_add = annotation_type != "text" or annotation_text
                                    if st.button("➕ Add", disabled=not can_add, key=f"add_{photo['id']}"):
                                        add_annotation_to_photo(
                                            photo['id'],
                                            session_name,
                                            annotation_type,
                                            annotation_color,
                                            stroke_width,
                                            annotation_text,
                                            position
                                        )
                                        st.success("✅ Annotation added!")
                                        st.rerun()
                                
                                with col_reset:
                                    if st.button("🔄 Reset", key=f"reset_{photo['id']}"):
                                        reset_photo_annotations(photo['id'], session_name)
                                        st.success("Annotations cleared!")
                                        st.rerun()
                                
                                st.divider()
                                
                                # Delete photo
                                if st.button("🗑️ Delete Photo", key=f"delete_{photo['id']}", type="secondary"):
                                    if delete_photo(photo['id'], session_name):
                                        st.success("Photo deleted!")
                                        st.session_state[f'expand_photo_{photo['id']}'] = False
                                        st.rerun()

else:  # Fieldmap page (camera)
    # Initialize auto-save tracking
    if 'last_saved_photo_id' not in st.session_state:
        st.session_state.last_saved_photo_id = None
    if 'camera_photo_hash' not in st.session_state:
        st.session_state.camera_photo_hash = None
    if 'camera_key' not in st.session_state:
        st.session_state.camera_key = 0
    
    # Header with logo
    st.markdown('<div class="header-logo">', unsafe_allow_html=True)
    try:
        logo_image = Image.open("/home/runner/work/fieldmap/fieldmap/logo.png")
        st.image(logo_image, width=100)
    except:
        st.write("📸")  # Fallback if logo not found
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Session management and creation
    st.subheader("Session")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        # Select current session
        current_session = st.selectbox(
            "Active Session",
            options=list(st.session_state.sessions.keys()),
            index=list(st.session_state.sessions.keys()).index(st.session_state.current_session),
            key="fieldmap_session_selector",
            label_visibility="collapsed"
        )
        st.session_state.current_session = current_session
    
    with col2:
        # Create new session button
        if st.button("➕ New", key="create_session_btn"):
            st.session_state['show_create_session'] = True
    
    # Show session creation form if button clicked
    if st.session_state.get('show_create_session', False):
        with st.form("create_session_form"):
            new_session_name = st.text_input("New Session Name", key="new_session_input")
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("Create", type="primary")
                if submitted and new_session_name:
                    if create_new_session(new_session_name):
                        st.session_state.current_session = new_session_name
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
    
    # Photo upload (camera on mobile)
    uploaded_file = st.camera_input("Take a photo", key=f"camera_{st.session_state.camera_key}")
    
    # Process uploaded photo
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        # Convert image to RGB mode to ensure compatibility
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Auto-save the photo when captured
        # Create a unique hash to detect new photos
        image_bytes = uploaded_file.getvalue()
        current_photo_hash = hashlib.md5(image_bytes).hexdigest()
        
        # Only auto-save if this is a new photo (not already saved)
        if current_photo_hash != st.session_state.camera_photo_hash:
            photo_id = add_photo_to_session(image, st.session_state.current_session, "")
            st.session_state.last_saved_photo_id = photo_id
            st.session_state.camera_photo_hash = current_photo_hash
            # Increment camera key to allow taking another photo
            st.session_state.camera_key += 1
            st.success(f"✅ Photo saved! (ID: {photo_id})")
            st.rerun()
    
    # Show annotation interface for last saved photo
    if st.session_state.last_saved_photo_id:
        st.divider()
        st.subheader("Last Photo")
        
        # Get the last saved photo
        last_photo = None
        for photo in st.session_state.sessions[st.session_state.current_session]:
            if photo['id'] == st.session_state.last_saved_photo_id:
                last_photo = photo
                break
        
        if last_photo:
            # Add/Edit comment
            photo_comment = st.text_area(
                "Notes/Comments:",
                value=last_photo['comment'],
                key="last_photo_comment",
                placeholder="Add notes about this photo..."
            )
            if photo_comment != last_photo['comment']:
                update_photo_comment(last_photo['id'], st.session_state.current_session, photo_comment)
            
            st.markdown("#### 🎨 Draw on Photo")
            
            col1, col2 = st.columns(2)
            with col1:
                annotation_type = st.selectbox(
                    "Type:",
                    options=["arrow", "circle", "box", "text"],
                    format_func=lambda x: {
                        "arrow": "↗️ Arrow",
                        "circle": "⭕ Circle",
                        "box": "⬜ Box",
                        "text": "📝 Text"
                    }[x],
                    key="last_photo_annotation_type"
                )
            with col2:
                annotation_color = st.color_picker(
                    "Color:",
                    value="#FF0000",
                    key="last_photo_color"
                )
            
            stroke_width = st.slider(
                "Line Width:",
                min_value=1,
                max_value=10,
                value=3,
                key="last_photo_stroke"
            )
            
            annotation_text = ""
            if annotation_type == "text":
                annotation_text = st.text_input(
                    "Text:",
                    key="last_photo_text",
                    placeholder="Enter text..."
                )
            
            position = st.slider(
                "Position:",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                key="last_photo_position"
            )
            
            can_add = annotation_type != "text" or annotation_text
            if st.button("➕ Add Drawing", disabled=not can_add, key="last_photo_add", type="primary"):
                add_annotation_to_photo(
                    last_photo['id'],
                    st.session_state.current_session,
                    annotation_type,
                    annotation_color,
                    stroke_width,
                    annotation_text,
                    position
                )
                st.success("✅ Drawing added!")
                st.rerun()
