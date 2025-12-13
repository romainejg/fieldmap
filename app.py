"""
Fieldmap - Cadaver Lab Photo Annotation App
A Streamlit-based mobile web app for biomedical engineers to capture, annotate, and organize photos
"""

import streamlit as st
import pandas as pd
from PIL import Image
import io
from datetime import datetime
from streamlit_drawable_canvas import st_canvas
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
        'comment': comment,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'annotations': [],
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

def add_annotation_to_photo(photo_id, session_name, annotation_text):
    """Add an annotation to a specific photo"""
    if session_name in st.session_state.sessions:
        for photo in st.session_state.sessions[session_name]:
            if photo['id'] == photo_id:
                photo['annotations'].append({
                    'text': annotation_text,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
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

def update_photo_drawing(photo_id, session_name, drawing_data):
    """Update the drawing annotation for a photo"""
    if session_name in st.session_state.sessions:
        for photo in st.session_state.sessions[session_name]:
            if photo['id'] == photo_id:
                photo['drawing_data'] = drawing_data
                return True
    return False

def export_to_excel():
    """Export all photos and comments to Excel"""
    data = []
    for session_name, photos in st.session_state.sessions.items():
        for photo in photos:
            annotations_text = "; ".join([f"{ann['text']} ({ann['timestamp']})" for ann in photo['annotations']])
            data.append({
                'Session': session_name,
                'Photo ID': photo['id'],
                'Timestamp': photo['timestamp'],
                'Comment': photo['comment'],
                'Annotations': annotations_text,
                'Annotation Count': len(photo['annotations'])
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
    if st.button("Export to Excel", use_container_width=True):
        excel_data = export_to_excel()
        if excel_data:
            st.download_button(
                label="📥 Download Excel File",
                data=excel_data,
                file_name=f"fieldmap_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("No data to export")

# Main content area
tab1, tab2 = st.tabs(["📷 Camera", "🖼️ Gallery"])

# Camera Tab
with tab1:
    st.header("Capture Photo")
    st.info(f"📍 Active Session: **{st.session_state.current_session}**")
    
    # Photo upload (camera on mobile)
    uploaded_file = st.camera_input("Take a photo", key="camera")
    
    # Alternative file upload
    st.markdown("---")
    st.subheader("Or Upload from Device")
    file_upload = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'], key="file_upload")
    
    # Process uploaded photo
    image_to_add = uploaded_file if uploaded_file else file_upload
    
    if image_to_add is not None:
        image = Image.open(image_to_add)
        st.image(image, caption="Preview", use_container_width=True)
        
        # Add comment
        photo_comment = st.text_area("Add a comment (optional)", key="photo_comment")
        
        # Session selector for this photo
        photo_session = st.selectbox(
            "Add to session:",
            options=list(st.session_state.sessions.keys()),
            index=list(st.session_state.sessions.keys()).index(st.session_state.current_session),
            key="photo_session_selector"
        )
        
        if st.button("💾 Save Photo", type="primary", use_container_width=True):
            photo_id = add_photo_to_session(image, photo_session, photo_comment)
            st.success(f"Photo saved to '{photo_session}' session! (ID: {photo_id})")
            st.balloons()

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
        
        # Display photos in a grid
        for session_name, photo in photos_to_display:
            with st.container():
                st.markdown(f"""
                <div class="photo-card">
                    <span class="session-badge">{session_name}</span>
                    <p><strong>Photo ID:</strong> {photo['id']} | <strong>Time:</strong> {photo['timestamp']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.image(photo['image'], use_container_width=True)
                
                with col2:
                    st.markdown(f"**Comment:**")
                    st.text(photo['comment'] if photo['comment'] else "No comment")
                    
                    # Display annotations
                    if photo['annotations']:
                        st.markdown("**Annotations:**")
                        for ann in photo['annotations']:
                            st.caption(f"• {ann['text']} ({ann['timestamp']})")
                
                # Action buttons in expander
                with st.expander(f"⚙️ Actions for Photo {photo['id']}", expanded=False):
                    # Edit comment
                    new_comment = st.text_area(
                        "Edit Comment",
                        value=photo['comment'],
                        key=f"edit_comment_{photo['id']}"
                    )
                    if st.button("Update Comment", key=f"update_{photo['id']}"):
                        update_photo_comment(photo['id'], session_name, new_comment)
                        st.success("Comment updated!")
                        st.rerun()
                    
                    # Add annotation
                    new_annotation = st.text_input(
                        "Add Annotation",
                        key=f"annotation_{photo['id']}"
                    )
                    if st.button("Add Annotation", key=f"add_ann_{photo['id']}"):
                        if new_annotation:
                            add_annotation_to_photo(photo['id'], session_name, new_annotation)
                            st.success("Annotation added!")
                            st.rerun()
                    
                    st.divider()
                    
                    # Drawing Annotation
                    st.markdown("**🎨 Draw on Photo** (circles, arrows, highlights)")
                    
                    # Drawing mode selector
                    drawing_mode = st.selectbox(
                        "Drawing Tool:",
                        options=["freedraw", "line", "rect", "circle", "transform"],
                        format_func=lambda x: {
                            "freedraw": "✏️ Free Draw",
                            "line": "↗️ Line/Arrow",
                            "rect": "⬜ Rectangle",
                            "circle": "⭕ Circle",
                            "transform": "🔄 Move/Resize"
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
                            if canvas_result.json_data is not None:
                                update_photo_drawing(photo['id'], session_name, canvas_result.json_data)
                                st.success("Drawing saved!")
                                st.rerun()
                    with col_clear:
                        if st.button("🗑️ Clear Drawing", key=f"clear_drawing_{photo['id']}"):
                            update_photo_drawing(photo['id'], session_name, None)
                            st.success("Drawing cleared!")
                            st.rerun()
                    
                    st.divider()
                    
                    # Move to different session
                    move_to_session = st.selectbox(
                        "Move to Session:",
                        options=[s for s in st.session_state.sessions.keys() if s != session_name],
                        key=f"move_session_{photo['id']}"
                    )
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("📦 Move", key=f"move_{photo['id']}"):
                            if move_photo(photo['id'], session_name, move_to_session):
                                st.success(f"Moved to '{move_to_session}'!")
                                st.rerun()
                    
                    # Delete photo
                    with col_b:
                        if st.button("🗑️ Delete", key=f"delete_{photo['id']}", type="secondary"):
                            if delete_photo(photo['id'], session_name):
                                st.success("Photo deleted!")
                                st.rerun()
                
                st.divider()

# Footer
st.markdown("---")
st.caption("Fieldmap v1.0 - Biomedical Engineering Lab Documentation System")
