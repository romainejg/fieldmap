"""
Fieldmap - Cadaver Lab Photo Annotation App
A Streamlit-based mobile web app for biomedical engineers to capture, annotate, and organize photos
"""

import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw
import io
from datetime import datetime
from streamlit_drawable_canvas import st_canvas
import hashlib
import numpy as np

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

def render_drawing_on_image(image, drawing_data, canvas_width, canvas_height):
    """
    Render canvas drawing data onto a PIL Image.
    
    Args:
        image: PIL Image object (original image)
        drawing_data: JSON data from streamlit_drawable_canvas
        canvas_width: Width of the canvas used for drawing
        canvas_height: Height of the canvas used for drawing
    
    Returns:
        PIL Image with drawings overlaid
    """
    if drawing_data is None or 'objects' not in drawing_data:
        return image.copy()
    
    # Create a copy of the original image
    img_copy = image.copy()
    
    # Get original image dimensions
    img_width, img_height = image.size
    
    # Calculate scaling factors (canvas may be scaled differently from original image)
    scale_x = img_width / canvas_width
    scale_y = img_height / canvas_height
    
    # Create a transparent overlay for drawings
    overlay = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Process each drawing object
    for obj in drawing_data['objects']:
        obj_type = obj.get('type')
        stroke = obj.get('stroke', '#FF0000')
        stroke_width = int(obj.get('strokeWidth', 3) * max(scale_x, scale_y))
        
        # Parse stroke color (handle hex colors)
        if stroke.startswith('#'):
            stroke_color = stroke
        else:
            stroke_color = '#FF0000'  # Default to red
        
        if obj_type == 'path':
            # Freehand drawing
            path = obj.get('path', [])
            if len(path) > 1:
                points = []
                for segment in path:
                    if len(segment) >= 3:
                        x = segment[1] * scale_x
                        y = segment[2] * scale_y
                        points.append((x, y))
                
                if len(points) > 1:
                    draw.line(points, fill=stroke_color, width=stroke_width, joint='curve')
        
        elif obj_type == 'line':
            # Line/Arrow
            x1 = obj.get('x1', 0) * scale_x
            y1 = obj.get('y1', 0) * scale_y
            x2 = obj.get('x2', 0) * scale_x
            y2 = obj.get('y2', 0) * scale_y
            draw.line([(x1, y1), (x2, y2)], fill=stroke_color, width=stroke_width)
        
        elif obj_type == 'rect':
            # Rectangle
            left = obj.get('left', 0) * scale_x
            top = obj.get('top', 0) * scale_y
            width = obj.get('width', 0) * scale_x
            height = obj.get('height', 0) * scale_y
            
            x1, y1 = left, top
            x2, y2 = left + width, top + height
            
            fill_color = obj.get('fill')
            if fill_color and fill_color != 'transparent':
                # Draw filled rectangle
                draw.rectangle([x1, y1, x2, y2], outline=stroke_color, fill=fill_color, width=stroke_width)
            else:
                # Draw outline only
                draw.rectangle([x1, y1, x2, y2], outline=stroke_color, width=stroke_width)
        
        elif obj_type == 'circle':
            # Circle
            left = obj.get('left', 0) * scale_x
            top = obj.get('top', 0) * scale_y
            radius = obj.get('radius', 0) * max(scale_x, scale_y)
            
            x1 = left - radius
            y1 = top - radius
            x2 = left + radius
            y2 = top + radius
            
            fill_color = obj.get('fill')
            if fill_color and fill_color != 'transparent':
                # Draw filled circle
                draw.ellipse([x1, y1, x2, y2], outline=stroke_color, fill=fill_color, width=stroke_width)
            else:
                # Draw outline only
                draw.ellipse([x1, y1, x2, y2], outline=stroke_color, width=stroke_width)
    
    # Convert original image to RGBA if needed
    if img_copy.mode != 'RGBA':
        img_copy = img_copy.convert('RGBA')
    
    # Composite the overlay onto the image
    result = Image.alpha_composite(img_copy, overlay)
    
    # Convert back to RGB
    if result.mode == 'RGBA':
        rgb_result = Image.new('RGB', result.size, (255, 255, 255))
        rgb_result.paste(result, mask=result.split()[3])
        return rgb_result
    
    return result

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
        'image': image,
        'annotated_image': None,  # Store image with drawings overlaid
        'comment': comment,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'drawing_data': None  # Store drawing annotations
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

def update_photo_drawing(photo_id, session_name, drawing_data, canvas_width=None, canvas_height=None):
    """Update the drawing annotation for a photo and create annotated image"""
    if session_name in st.session_state.sessions:
        for photo in st.session_state.sessions[session_name]:
            if photo['id'] == photo_id:
                photo['drawing_data'] = drawing_data
                
                # If drawing data exists and canvas dimensions provided, create annotated image
                if drawing_data is not None and canvas_width is not None and canvas_height is not None:
                    annotated_img = render_drawing_on_image(
                        photo['image'], 
                        drawing_data, 
                        canvas_width, 
                        canvas_height
                    )
                    photo['annotated_image'] = annotated_img
                else:
                    # Clear annotated image if no drawing
                    photo['annotated_image'] = None
                
                return True
    return False

def export_to_excel():
    """Export all photos and comments to Excel"""
    data = []
    for session_name, photos in st.session_state.sessions.items():
        for photo in photos:
            has_drawing = photo.get('drawing_data') is not None
            has_annotated_image = photo.get('annotated_image') is not None
            data.append({
                'Session': session_name,
                'Photo ID': photo['id'],
                'Timestamp': photo['timestamp'],
                'Comment': photo['comment'],
                'Has Drawing': 'Yes' if has_drawing else 'No',
                'Annotated Image Saved': 'Yes' if has_annotated_image else 'No'
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
        # Convert image to RGB mode to ensure compatibility with Streamlit
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
        
        # Show original image and annotated if exists
        if saved_photo and saved_photo.get('annotated_image') is not None:
            col_orig, col_annot = st.columns(2)
            with col_orig:
                st.markdown("**Original:**")
                st.image(image, use_column_width=True)
            with col_annot:
                st.markdown("**📝 With Drawings:**")
                st.image(saved_photo['annotated_image'], use_column_width=True)
            
            # Download button for annotated image
            buf = io.BytesIO()
            saved_photo['annotated_image'].save(buf, format='PNG')
            buf.seek(0)
            st.download_button(
                label="📥 Download Annotated Image",
                data=buf,
                file_name=f"annotated_photo_{saved_photo['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                mime="image/png",
                key="download_preview_annotated"
            )
        else:
            st.image(image, caption="Photo Preview", use_column_width=True)
        
        if saved_photo:
            # Immediate annotation options
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
            
            # Drawing tools (part of annotation)
            st.markdown("#### 🎨 Draw on Photo")
            
            col_mode, col_color, col_width = st.columns(3)
            with col_mode:
                drawing_mode = st.selectbox(
                    "Tool:",
                    options=["freedraw", "line", "rect", "circle"],
                    format_func=lambda x: {
                        "freedraw": "✏️ Draw",
                        "line": "↗️ Arrow",
                        "rect": "⬜ Box",
                        "circle": "⭕ Circle"
                    }[x],
                    key="preview_drawing_mode"
                )
            with col_color:
                stroke_color = st.color_picker(
                    "Color:",
                    value="#FF0000",
                    key="preview_stroke_color"
                )
            with col_width:
                stroke_width = st.slider(
                    "Width:",
                    min_value=1,
                    max_value=20,
                    value=3,
                    key="preview_stroke_width"
                )
            
            # Get image dimensions for canvas
            img_width, img_height = image.size
            max_canvas_width = 600
            if img_width > max_canvas_width:
                scale = max_canvas_width / img_width
                canvas_width = max_canvas_width
                canvas_height = int(img_height * scale)
            else:
                canvas_width = img_width
                canvas_height = img_height
            
            # Create drawable canvas
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                background_image=image,
                update_streamlit=True,
                height=canvas_height,
                width=canvas_width,
                drawing_mode=drawing_mode,
                initial_drawing=saved_photo.get('drawing_data'),
                key="preview_canvas"
            )
            
            # Save drawing button
            col_save, col_clear = st.columns(2)
            with col_save:
                if st.button("💾 Save Drawing", key="preview_save_drawing"):
                    if canvas_result is not None and canvas_result.json_data is not None:
                        update_photo_drawing(
                            saved_photo['id'], 
                            st.session_state.current_session, 
                            canvas_result.json_data,
                            canvas_width,
                            canvas_height
                        )
                        st.success("✅ Drawing saved and overlaid on image!")
                        st.rerun()
            with col_clear:
                if st.button("🗑️ Clear Drawing", key="preview_clear_drawing"):
                    update_photo_drawing(saved_photo['id'], st.session_state.current_session, None)
                    st.success("Drawing cleared!")
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
        
        # Instructions
        st.info("💡 **Tip**: Click on a photo thumbnail to view/edit. Use 'Quick Move' dropdown to move photos between sessions.")
        
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
                        st.image(photo['image'], use_column_width=True)
                        
                        # Session badge and metadata
                        st.markdown(f"""
                        <div style="font-size: 0.8em; padding: 2px;">
                            <span style="background-color: #4CAF50; color: white; padding: 2px 6px; border-radius: 8px; font-size: 0.75em;">{session_name}</span>
                            <br/>ID: {photo['id']} | 🎨: {"✓" if photo.get('drawing_data') else "✗"}
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
                                
                                # Show original and annotated images
                                if photo.get('annotated_image') is not None:
                                    st.markdown("**Original Image:**")
                                    st.image(photo['image'], use_column_width=True)
                                    
                                    st.markdown("**📝 Annotated Image (with drawings):**")
                                    st.image(photo['annotated_image'], use_column_width=True)
                                    
                                    # Download annotated image button
                                    buf = io.BytesIO()
                                    photo['annotated_image'].save(buf, format='PNG')
                                    buf.seek(0)
                                    st.download_button(
                                        label="📥 Download Annotated Image",
                                        data=buf,
                                        file_name=f"annotated_photo_{photo['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                        mime="image/png",
                                        key=f"download_annotated_{photo['id']}"
                                    )
                                else:
                                    st.markdown("**Image:**")
                                    st.image(photo['image'], use_column_width=True)
                                
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
                                
                                # Drawing Annotation
                                st.markdown("**🎨 Draw on Photo**")
                                
                                # Drawing mode selector
                                drawing_mode = st.selectbox(
                                    "Tool:",
                                    options=["freedraw", "line", "rect", "circle", "transform"],
                                    format_func=lambda x: {
                                        "freedraw": "✏️ Draw",
                                        "line": "↗️ Arrow",
                                        "rect": "⬜ Box",
                                        "circle": "⭕ Circle",
                                        "transform": "🔄 Move"
                                    }[x],
                                    key=f"drawing_mode_{photo['id']}"
                                )
                                
                                # Color and stroke width
                                col_color, col_stroke = st.columns(2)
                                with col_color:
                                    stroke_color = st.color_picker(
                                        "Color:",
                                        value="#FF0000",
                                        key=f"stroke_color_{photo['id']}"
                                    )
                                with col_stroke:
                                    stroke_width = st.slider(
                                        "Width:",
                                        min_value=1,
                                        max_value=20,
                                        value=3,
                                        key=f"stroke_width_{photo['id']}"
                                    )
                                
                                # Get image dimensions
                                img_width, img_height = photo['image'].size
                                
                                # Scale down large images for canvas display
                                max_canvas_width = 600
                                if img_width > max_canvas_width:
                                    scale = max_canvas_width / img_width
                                    canvas_width = max_canvas_width
                                    canvas_height = int(img_height * scale)
                                else:
                                    canvas_width = img_width
                                    canvas_height = img_height
                                
                                # Create drawable canvas
                                canvas_result = st_canvas(
                                    fill_color="rgba(255, 165, 0, 0.3)",
                                    stroke_width=stroke_width,
                                    stroke_color=stroke_color,
                                    background_image=photo['image'],
                                    update_streamlit=True,
                                    height=canvas_height,
                                    width=canvas_width,
                                    drawing_mode=drawing_mode,
                                    initial_drawing=photo.get('drawing_data'),
                                    key=f"canvas_{photo['id']}"
                                )
                                
                                # Save drawing button
                                col_save, col_clear = st.columns(2)
                                with col_save:
                                    if st.button("💾 Save Drawing", key=f"save_drawing_{photo['id']}"):
                                        if canvas_result is not None and canvas_result.json_data is not None:
                                            update_photo_drawing(
                                                photo['id'], 
                                                session_name, 
                                                canvas_result.json_data,
                                                canvas_width,
                                                canvas_height
                                            )
                                            st.success("✅ Drawing saved and overlaid on image!")
                                            st.rerun()
                                with col_clear:
                                    if st.button("🗑️ Clear Drawing", key=f"clear_drawing_{photo['id']}"):
                                        update_photo_drawing(photo['id'], session_name, None)
                                        st.success("Drawing cleared!")
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
st.caption("Fieldmap v1.0 - Biomedical Engineering Lab Documentation System")
