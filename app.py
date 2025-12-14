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
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly UI
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
    }
    .main .block-container {
        padding-top: 2rem;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'sessions' not in st.session_state:
    st.session_state.sessions = {'Default': []}
if 'current_session' not in st.session_state:
    st.session_state.current_session = 'Default'
if 'photo_counter' not in st.session_state:
    st.session_state.photo_counter = 0

def draw_annotation_on_image(image, annotation_type, color, stroke_width, text="", position_percent=0.5):
    """
    Draw a simple annotation directly on the image using PIL.
    
    Args:
        image: PIL Image object
        annotation_type: Type of annotation ('arrow', 'circle', 'box', 'text')
        color: Color in hex format (e.g., '#FF0000')
        stroke_width: Width of the stroke
        text: Text to add (for text annotations)
        position_percent: Position on image (0.0 to 1.0) - used for simple placement
    
    Returns:
        PIL Image with annotation drawn
    """
    # Create a copy to avoid modifying original
    img_copy = image.copy()
    if img_copy.mode != 'RGB':
        img_copy = img_copy.convert('RGB')
    
    draw = ImageDraw.Draw(img_copy)
    width, height = img_copy.size
    
    # Calculate position based on percentage
    center_x = int(width * position_percent)
    center_y = int(height * position_percent)
    
    if annotation_type == 'arrow':
        # Draw a simple arrow pointing down
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
        # Draw a circle in the center-ish area
        radius = min(width, height) // 8
        draw.ellipse([
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius
        ], outline=color, width=stroke_width)
    
    elif annotation_type == 'box':
        # Draw a rectangle in the center area
        box_size = min(width, height) // 6
        draw.rectangle([
            center_x - box_size, center_y - box_size,
            center_x + box_size, center_y + box_size
        ], outline=color, width=stroke_width)
    
    elif annotation_type == 'text' and text:
        # Draw text annotation
        try:
            # Try to use a larger font
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=max(20, width // 30))
        except:
            # Fallback to default font
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

# Main App Title
st.title("📸 Fieldmap - Cadaver Lab")
st.markdown("*Photo Annotation & Documentation System*")

# Sidebar for session management
with st.sidebar:
    st.header("🗂️ Session Management")
    
    # Create new session
    with st.expander("➕ Create New Session", expanded=False):
        new_session_name = st.text_input("Session Name", key="new_session_input")
        if st.button("Create Session"):
            if create_new_session(new_session_name):
                st.success(f"Session '{new_session_name}' created!")
                st.rerun()
            else:
                st.error("Session already exists or invalid name")
    
    # Select current session
    st.subheader("Current Session")
    current_session = st.selectbox(
        "Active Session",
        options=list(st.session_state.sessions.keys()),
        index=list(st.session_state.sessions.keys()).index(st.session_state.current_session),
        key="session_selector"
    )
    st.session_state.current_session = current_session
    
    # Session statistics
    st.metric("Photos in Session", len(st.session_state.sessions[current_session]))
    total_photos = sum(len(photos) for photos in st.session_state.sessions.values())
    st.metric("Total Photos", total_photos)
    
    # Export functionality
    st.divider()
    st.subheader("📊 Export Data")
    if st.button("Export to Excel"):
        excel_data = export_to_excel()
        if excel_data:
            st.download_button(
                label="📥 Download Excel File",
                data=excel_data,
                file_name=f"fieldmap_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No data to export")

# Main content area
tab1, tab2 = st.tabs(["📷 Camera", "🖼️ Gallery"])

# Initialize auto-save tracking
if 'last_saved_photo_id' not in st.session_state:
    st.session_state.last_saved_photo_id = None
if 'camera_photo_hash' not in st.session_state:
    st.session_state.camera_photo_hash = None
if 'camera_key' not in st.session_state:
    st.session_state.camera_key = 0

# Camera Tab
with tab1:
    st.header("Capture Photo")
    st.info(f"📍 Active Session: **{st.session_state.current_session}**")
    
    # Photo upload (camera on mobile)
    uploaded_file = st.camera_input("Take a photo", key=f"camera_{st.session_state.camera_key}")
    
    # Alternative file upload
    st.markdown("---")
    st.subheader("Or Upload from Device")
    file_upload = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'], key=f"file_upload_{st.session_state.camera_key}")
    
    # Process uploaded photo
    image_to_add = uploaded_file if uploaded_file else file_upload
    
    if image_to_add is not None:
        image = Image.open(image_to_add)
        # Convert image to RGB mode to ensure compatibility
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Auto-save the photo when captured
        # Create a unique hash to detect new photos
        image_bytes = image_to_add.getvalue()
        current_photo_hash = hashlib.md5(image_bytes).hexdigest()
        
        # Only auto-save if this is a new photo (not already saved)
        if current_photo_hash != st.session_state.camera_photo_hash:
            photo_id = add_photo_to_session(image, st.session_state.current_session, "")
            st.session_state.last_saved_photo_id = photo_id
            st.session_state.camera_photo_hash = current_photo_hash
            st.success(f"✅ Photo automatically saved to '{st.session_state.current_session}' session! (ID: {photo_id})")
        
        # Clear camera button
        if st.button("📸 Clear Camera - Take Another Photo", type="primary"):
            st.session_state.camera_key += 1
            st.session_state.camera_photo_hash = None
            st.session_state.last_saved_photo_id = None
            st.rerun()
        
        # Show preview with annotation options
        st.subheader("📸 Preview & Annotate")
        
        # Get the saved photo data
        saved_photo = None
        if st.session_state.last_saved_photo_id:
            for photo in st.session_state.sessions[st.session_state.current_session]:
                if photo['id'] == st.session_state.last_saved_photo_id:
                    saved_photo = photo
                    break
        
        if saved_photo:
            # Show current image (with any annotations)
            st.image(saved_photo['current_image'], caption="Photo Preview", use_column_width=True)
            
            # Download button for current image
            buf = io.BytesIO()
            saved_photo['current_image'].save(buf, format='PNG')
            buf.seek(0)
            st.download_button(
                label="📥 Download Photo" + (" (with annotations)" if saved_photo['has_annotations'] else ""),
                data=buf,
                file_name=f"photo_{saved_photo['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                key="download_preview"
            )
            
            st.markdown("### ✏️ Add Notes & Draw")
            
            # Add/Edit comment
            photo_comment = st.text_area(
                "Notes/Comments:",
                value=saved_photo['comment'],
                key="preview_comment",
                placeholder="Enter a description or note for this photo..."
            )
            if st.button("💾 Update Comment"):
                update_photo_comment(saved_photo['id'], st.session_state.current_session, photo_comment)
                st.success("Comment updated!")
                st.rerun()
            
            st.divider()
            
            # Simple drawing tools
            st.markdown("#### 🎨 Add Annotations to Photo")
            st.info("💡 Annotations are added directly to the photo. Use 'Reset' to remove all.")
            
            col1, col2 = st.columns(2)
            with col1:
                annotation_type = st.selectbox(
                    "Annotation Type:",
                    options=["arrow", "circle", "box", "text"],
                    format_func=lambda x: {
                        "arrow": "↗️ Arrow",
                        "circle": "⭕ Circle",
                        "box": "⬜ Box",
                        "text": "📝 Text"
                    }[x],
                    key="preview_annotation_type"
                )
            with col2:
                annotation_color = st.color_picker(
                    "Color:",
                    value="#FF0000",
                    key="preview_color"
                )
            
            stroke_width = st.slider(
                "Line Width:",
                min_value=1,
                max_value=10,
                value=3,
                key="preview_stroke"
            )
            
            annotation_text = ""
            if annotation_type == "text":
                annotation_text = st.text_input(
                    "Text to add:",
                    key="preview_text",
                    placeholder="Enter text..."
                )
            
            position = st.slider(
                "Position (left ← → right):",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.1,
                key="preview_position"
            )
            
            col_add, col_reset = st.columns(2)
            with col_add:
                can_add = annotation_type != "text" or annotation_text
                if st.button("➕ Add Annotation", disabled=not can_add, key="preview_add"):
                    add_annotation_to_photo(
                        saved_photo['id'],
                        st.session_state.current_session,
                        annotation_type,
                        annotation_color,
                        stroke_width,
                        annotation_text,
                        position
                    )
                    st.success("✅ Annotation added!")
                    st.rerun()
            
            with col_reset:
                if st.button("🔄 Reset All Annotations", key="preview_reset"):
                    reset_photo_annotations(saved_photo['id'], st.session_state.current_session)
                    st.success("Annotations cleared!")
                    st.rerun()
            
            st.divider()
            
            # Option to move to a different session
            st.markdown("### 📦 Organize")
            move_to_session = st.selectbox(
                "Move to different session:",
                options=[s for s in st.session_state.sessions.keys()],
                index=list(st.session_state.sessions.keys()).index(st.session_state.current_session),
                key="preview_move_session"
            )
            if move_to_session != st.session_state.current_session:
                if st.button(f"📦 Move to '{move_to_session}'"):
                    if move_photo(saved_photo['id'], st.session_state.current_session, move_to_session):
                        st.success(f"Moved to '{move_to_session}'!")
                        st.session_state.last_saved_photo_id = None
                        st.session_state.camera_photo_hash = None
                        st.rerun()

# Gallery Tab
with tab2:
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
        st.info("No photos yet. Use the Camera tab to add photos!")
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

# Footer
st.markdown("---")
st.caption("Fieldmap v2.0 - Biomedical Engineering Lab Documentation System")
