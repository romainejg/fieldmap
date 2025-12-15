"""
Fieldmap - Cadaver Lab Photo Annotation App (Gradio Version)
A Gradio-based mobile web app for biomedical engineers to capture, annotate, and organize photos
Migrated from Streamlit to use Gradio's ImageEditor for reliable photo annotation
"""

import gradio as gr
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
from datetime import datetime
from pathlib import Path
import logging
import base64
import numpy as np

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionStore:
    """Manages session state and CRUD operations for sessions and photos"""
    
    def __init__(self):
        self.sessions = {'Default': []}
        self.current_session = 'Default'
        self.photo_counter = 0
        self.last_saved_photo_id = None
    
    def get_session_names(self):
        """Get list of session names"""
        return list(self.sessions.keys())
    
    def create_session(self, session_name):
        """Create a new session"""
        if session_name and session_name not in self.sessions:
            self.sessions[session_name] = []
            return True
        return False
    
    def add_photo(self, image, session_name, comment=""):
        """Add a photo with metadata to a session"""
        if image is None:
            return None
        
        # Convert numpy array to PIL Image if needed
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Ensure image is PIL Image
        if not isinstance(image, Image.Image):
            logger.error(f"Invalid image type: {type(image)}")
            return None
        
        self.photo_counter += 1
        photo_data = {
            'id': self.photo_counter,
            'original_image': image.copy(),
            'current_image': image.copy(),
            'comment': comment,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_annotations': False
        }
        self.sessions[session_name].append(photo_data)
        return photo_data['id']
    
    def get_photo(self, photo_id, session_name=None):
        """Get a photo by ID from a session or all sessions"""
        if session_name:
            sessions_to_search = [session_name]
        else:
            sessions_to_search = self.sessions.keys()
        
        for sess_name in sessions_to_search:
            if sess_name in self.sessions:
                for photo in self.sessions[sess_name]:
                    if photo['id'] == photo_id:
                        return photo, sess_name
        return None, None
    
    def update_photo_image(self, photo_id, new_image, session_name=None):
        """Update a photo's image"""
        photo, sess_name = self.get_photo(photo_id, session_name)
        if photo:
            if isinstance(new_image, np.ndarray):
                new_image = Image.fromarray(new_image.astype('uint8'))
            photo['current_image'] = new_image
            photo['has_annotations'] = True
            return True
        return False
    
    def update_photo_comment(self, photo_id, new_comment, session_name=None):
        """Update the comment for a photo"""
        photo, sess_name = self.get_photo(photo_id, session_name)
        if photo:
            photo['comment'] = new_comment
            return True
        return False
    
    def delete_photo(self, photo_id, session_name=None):
        """Delete a photo from a session"""
        photo, sess_name = self.get_photo(photo_id, session_name)
        if photo and sess_name:
            photos = self.sessions[sess_name]
            for i, p in enumerate(photos):
                if p['id'] == photo_id:
                    photos.pop(i)
                    return True
        return False
    
    def move_photo(self, photo_id, from_session, to_session):
        """Move a photo from one session to another"""
        if from_session in self.sessions and to_session in self.sessions:
            photos = self.sessions[from_session]
            for i, photo in enumerate(photos):
                if photo['id'] == photo_id:
                    moved_photo = photos.pop(i)
                    self.sessions[to_session].append(moved_photo)
                    return True
        return False
    
    def get_all_photos(self, session_name=None):
        """Get all photos from a session or all sessions"""
        photos_list = []
        if session_name and session_name != "All Sessions":
            for photo in self.sessions.get(session_name, []):
                photos_list.append((session_name, photo))
        else:
            for sess_name, photos in self.sessions.items():
                for photo in photos:
                    photos_list.append((sess_name, photo))
        return photos_list
    
    def export_to_excel(self):
        """Export all photos and comments to Excel"""
        data = []
        for session_name, photos in self.sessions.items():
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
            output.seek(0)
            return output
        return None


# Global session store
session_store = SessionStore()


def capture_photo(image):
    """Handle photo capture"""
    if image is None:
        return None, "Please capture a photo first", None
    
    # Add photo to current session
    photo_id = session_store.add_photo(image, session_store.current_session, "")
    if photo_id:
        session_store.last_saved_photo_id = photo_id
        return image, f"✓ Photo saved! (ID: {photo_id})", photo_id
    else:
        return None, "Error saving photo", None


def create_new_session(new_session_name):
    """Create a new session"""
    if not new_session_name:
        return gr.update(), "Please enter a session name"
    
    if session_store.create_session(new_session_name):
        session_store.current_session = new_session_name
        return gr.update(choices=session_store.get_session_names(), value=new_session_name), f"✓ Session '{new_session_name}' created!"
    else:
        return gr.update(), "Session already exists or invalid name"


def change_session(session_name):
    """Change the current session"""
    session_store.current_session = session_name
    return f"Current session: {session_name}"


def update_comment(photo_id, comment):
    """Update photo comment"""
    if photo_id is None:
        return "No photo selected"
    
    if session_store.update_photo_comment(photo_id, comment):
        return f"✓ Comment updated for photo {photo_id}"
    return "Error updating comment"


def save_edited_image(editor_value, photo_id):
    """Save the edited image from ImageEditor"""
    if photo_id is None:
        return None, "No photo to edit", None
    
    if editor_value is None:
        return None, "No edits to save", None
    
    # ImageEditor returns a dict with 'background' and 'layers'
    # The 'background' is the composite image with all edits
    edited_image = None
    
    if isinstance(editor_value, dict):
        # Get the composite/background image
        bg = editor_value.get("background", None)
        if bg is not None:
            edited_image = bg
        else:
            # Fallback: try to get the image from composite
            composite = editor_value.get("composite", None)
            if composite is not None:
                edited_image = composite
    elif isinstance(editor_value, (Image.Image, np.ndarray)):
        edited_image = editor_value
    
    if edited_image is None:
        return None, "Could not extract edited image", None
    
    # Update the photo
    if session_store.update_photo_image(photo_id, edited_image):
        photo, _ = session_store.get_photo(photo_id)
        return photo['current_image'], f"✓ Photo {photo_id} updated with annotations!", photo_id
    
    return None, "Error saving edited image", None


def load_photo_for_editing(photo_id):
    """Load a photo for editing in ImageEditor"""
    if photo_id is None:
        return None
    
    photo, _ = session_store.get_photo(photo_id)
    if photo:
        return photo['current_image']
    return None


def get_photo_info(photo_id):
    """Get photo information for display"""
    if photo_id is None:
        return "No photo captured yet", ""
    
    photo, session_name = session_store.get_photo(photo_id)
    if photo:
        info = f"**Photo ID:** {photo['id']}\n**Session:** {session_name}\n**Time:** {photo['timestamp']}\n**Has Annotations:** {'Yes' if photo['has_annotations'] else 'No'}"
        return info, photo['comment']
    return "Photo not found", ""


def get_gallery_photos(session_filter):
    """Get photos for gallery display"""
    photos_list = session_store.get_all_photos(session_filter)
    return photos_list


def format_gallery_html(session_filter):
    """Format photos as HTML gallery"""
    photos_list = get_gallery_photos(session_filter)
    
    if not photos_list:
        return "<p>No photos yet. Use the Fieldmap page to capture photos!</p>"
    
    html = f"<h3>{len(photos_list)} photo(s) found</h3>"
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; padding: 10px;">'
    
    for session_name, photo in photos_list:
        time_str = photo['timestamp'].split()[1] if len(photo['timestamp'].split()) > 1 else photo['timestamp']
        
        # Convert PIL Image to base64 for HTML display
        buffered = io.BytesIO()
        photo['current_image'].save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        html += f'''
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: white;">
            <img src="data:image/png;base64,{img_str}" style="width: 100%; border-radius: 4px;">
            <p style="margin: 5px 0; font-size: 0.9em;"><strong>{session_name}</strong> • ID {photo['id']}</p>
            <p style="margin: 5px 0; font-size: 0.8em; color: #666;">{time_str}</p>
            <p style="margin: 5px 0; font-size: 0.8em; color: #666;">Annotations: {'Yes' if photo['has_annotations'] else 'No'}</p>
        </div>
        '''
    
    html += '</div>'
    return html


def get_photo_list_for_dropdown(session_filter):
    """Get photo list for dropdown selection"""
    photos_list = get_gallery_photos(session_filter)
    if not photos_list:
        return []
    
    choices = []
    for session_name, photo in photos_list:
        label = f"ID {photo['id']} - {session_name} - {photo['timestamp']}"
        choices.append((label, photo['id']))
    
    return choices


def load_selected_photo(photo_selection):
    """Load selected photo from gallery"""
    if photo_selection is None:
        return None, "", "", [], gr.update(choices=[])
    
    photo, session_name = session_store.get_photo(photo_selection)
    if photo:
        # Prepare move options
        other_sessions = [s for s in session_store.get_session_names() if s != session_name]
        
        images_to_show = []
        if photo['has_annotations']:
            images_to_show = [
                (photo['original_image'], "Original"),
                (photo['current_image'], "With Annotations")
            ]
        else:
            images_to_show = [(photo['current_image'], "Current")]
        
        info = f"**Session:** {session_name}\n**Timestamp:** {photo['timestamp']}\n**Has Annotations:** {'Yes' if photo['has_annotations'] else 'No'}"
        
        return images_to_show, photo['comment'], info, other_sessions, gr.update(choices=other_sessions, value=None)
    
    return None, "", "", [], gr.update(choices=[])


def move_photo_to_session(photo_id, current_session_name, target_session):
    """Move photo to another session"""
    if not photo_id or not target_session:
        return "Please select a target session", gr.update()
    
    photo, source_session = session_store.get_photo(photo_id)
    if photo and source_session:
        if session_store.move_photo(photo_id, source_session, target_session):
            return f"✓ Photo {photo_id} moved to {target_session}", gr.update(value=None)
    
    return "Error moving photo", gr.update()


def delete_selected_photo(photo_id):
    """Delete selected photo"""
    if not photo_id:
        return "No photo selected", gr.update()
    
    if session_store.delete_photo(photo_id):
        return f"✓ Photo {photo_id} deleted", gr.update(value=None)
    
    return "Error deleting photo", gr.update()


def download_photo(photo_id):
    """Prepare photo for download"""
    if not photo_id:
        return None
    
    photo, _ = session_store.get_photo(photo_id)
    if photo:
        return photo['current_image']
    return None


def export_data():
    """Export data to Excel"""
    excel_file = session_store.export_to_excel()
    if excel_file:
        # Save to temporary file and return path
        temp_path = f"/tmp/fieldmap_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with open(temp_path, 'wb') as f:
            f.write(excel_file.getvalue())
        return temp_path
    return None


# Build the Gradio interface
def create_app():
    """Create the Gradio app interface"""
    
    with gr.Blocks(title="Fieldmap - Lab Photos", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🔬 Fieldmap - Lab Photo Documentation")
        gr.Markdown("*A mobile-optimized app for cadaver lab photo annotation and organization*")
        
        with gr.Tabs():
            # Tab 1: Fieldmap (Capture & Edit)
            with gr.Tab("📷 Fieldmap"):
                gr.Markdown("## Session Management")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        session_dropdown = gr.Dropdown(
                            choices=session_store.get_session_names(),
                            value=session_store.current_session,
                            label="Active Session",
                            interactive=True
                        )
                    with gr.Column(scale=1):
                        new_session_btn = gr.Button("New Session", size="sm")
                
                session_status = gr.Textbox(label="Status", interactive=False, visible=False)
                
                # New session creation (initially hidden)
                with gr.Row(visible=False) as new_session_row:
                    new_session_input = gr.Textbox(label="New Session Name", placeholder="Enter session name")
                    create_session_btn = gr.Button("Create", variant="primary")
                
                gr.Markdown("---")
                gr.Markdown("## Camera")
                
                camera = gr.Image(
                    label="Take a Photo",
                    sources=["webcam"],
                    type="pil",
                    interactive=True
                )
                
                capture_btn = gr.Button("Save Photo", variant="primary", size="lg")
                capture_status = gr.Textbox(label="Status", interactive=False)
                saved_photo_id = gr.State(None)
                
                gr.Markdown("---")
                gr.Markdown("## Last Photo")
                
                photo_preview = gr.Image(label="Last Captured Photo", type="pil", interactive=False)
                photo_info = gr.Markdown("No photo captured yet")
                
                comment_input = gr.Textbox(
                    label="Notes/Comments",
                    placeholder="Add notes about this photo...",
                    lines=3
                )
                update_comment_btn = gr.Button("Update Comment")
                comment_status = gr.Textbox(label="Status", interactive=False, visible=False)
                
                gr.Markdown("### Edit Photo")
                gr.Markdown("*Use the ImageEditor below to draw annotations on your photo. Click Save when done.*")
                
                editor = gr.ImageEditor(
                    label="Photo Editor",
                    sources=[],  # No upload, we'll set image programmatically
                    interactive=True
                )
                
                with gr.Row():
                    save_edit_btn = gr.Button("Save Edits", variant="primary")
                    reset_edit_btn = gr.Button("Reset to Original")
                
                edit_status = gr.Textbox(label="Status", interactive=False)
                
                # Event handlers for Fieldmap tab
                def toggle_new_session():
                    return gr.update(visible=True)
                
                def on_session_change(sess_name):
                    session_store.current_session = sess_name
                    return f"Switched to session: {sess_name}"
                
                new_session_btn.click(
                    fn=toggle_new_session,
                    outputs=[new_session_row]
                )
                
                create_session_btn.click(
                    fn=create_new_session,
                    inputs=[new_session_input],
                    outputs=[session_dropdown, session_status]
                ).then(
                    fn=lambda: (gr.update(visible=False), ""),
                    outputs=[new_session_row, new_session_input]
                )
                
                session_dropdown.change(
                    fn=on_session_change,
                    inputs=[session_dropdown],
                    outputs=[session_status]
                )
                
                capture_btn.click(
                    fn=capture_photo,
                    inputs=[camera],
                    outputs=[photo_preview, capture_status, saved_photo_id]
                ).then(
                    fn=load_photo_for_editing,
                    inputs=[saved_photo_id],
                    outputs=[editor]
                ).then(
                    fn=get_photo_info,
                    inputs=[saved_photo_id],
                    outputs=[photo_info, comment_input]
                )
                
                update_comment_btn.click(
                    fn=update_comment,
                    inputs=[saved_photo_id, comment_input],
                    outputs=[comment_status]
                )
                
                save_edit_btn.click(
                    fn=save_edited_image,
                    inputs=[editor, saved_photo_id],
                    outputs=[photo_preview, edit_status, saved_photo_id]
                ).then(
                    fn=load_photo_for_editing,
                    inputs=[saved_photo_id],
                    outputs=[editor]
                )
                
                def reset_to_original(photo_id):
                    if photo_id is None:
                        return None, "No photo to reset"
                    
                    photo, _ = session_store.get_photo(photo_id)
                    if photo:
                        photo['current_image'] = photo['original_image'].copy()
                        photo['has_annotations'] = False
                        return photo['current_image'], f"✓ Photo {photo_id} reset to original"
                    return None, "Error resetting photo"
                
                reset_edit_btn.click(
                    fn=reset_to_original,
                    inputs=[saved_photo_id],
                    outputs=[editor, edit_status]
                )
            
            # Tab 2: Gallery
            with gr.Tab("🖼️ Gallery"):
                gr.Markdown("## Photo Gallery")
                
                gallery_session_filter = gr.Dropdown(
                    choices=["All Sessions"] + session_store.get_session_names(),
                    value="All Sessions",
                    label="View Session",
                    interactive=True
                )
                
                refresh_gallery_btn = gr.Button("Refresh Gallery", size="sm")
                
                gallery_html = gr.HTML(format_gallery_html("All Sessions"))
                
                gr.Markdown("---")
                gr.Markdown("## Photo Details & Management")
                
                def update_photo_dropdown(session_filter):
                    choices = get_photo_list_for_dropdown(session_filter)
                    if choices:
                        return gr.update(choices=choices, value=choices[0][1])
                    return gr.update(choices=[], value=None)
                
                photo_selector = gr.Dropdown(
                    label="Select Photo",
                    choices=[],
                    interactive=True
                )
                
                load_photo_btn = gr.Button("Load Photo", variant="primary")
                
                photo_gallery_display = gr.Gallery(
                    label="Photo View",
                    columns=2,
                    height="auto"
                )
                
                photo_detail_info = gr.Markdown("")
                
                detail_comment = gr.Textbox(label="Comment", lines=3)
                update_detail_comment_btn = gr.Button("Update Comment")
                
                with gr.Row():
                    download_btn = gr.Button("Download Photo")
                
                download_file = gr.File(label="Download", visible=False)
                
                gr.Markdown("### Move Photo")
                move_to_dropdown = gr.Dropdown(label="Move to Session", choices=[], interactive=True)
                move_btn = gr.Button("Move Photo")
                move_status = gr.Textbox(label="Status", interactive=False, visible=False)
                
                gr.Markdown("### Delete Photo")
                delete_btn = gr.Button("Delete Photo", variant="stop")
                delete_status = gr.Textbox(label="Status", interactive=False, visible=False)
                
                # Gallery event handlers
                gallery_session_filter.change(
                    fn=format_gallery_html,
                    inputs=[gallery_session_filter],
                    outputs=[gallery_html]
                ).then(
                    fn=update_photo_dropdown,
                    inputs=[gallery_session_filter],
                    outputs=[photo_selector]
                )
                
                refresh_gallery_btn.click(
                    fn=format_gallery_html,
                    inputs=[gallery_session_filter],
                    outputs=[gallery_html]
                ).then(
                    fn=update_photo_dropdown,
                    inputs=[gallery_session_filter],
                    outputs=[photo_selector]
                )
                
                load_photo_btn.click(
                    fn=load_selected_photo,
                    inputs=[photo_selector],
                    outputs=[photo_gallery_display, detail_comment, photo_detail_info, move_to_dropdown, move_to_dropdown]
                )
                
                update_detail_comment_btn.click(
                    fn=update_comment,
                    inputs=[photo_selector, detail_comment],
                    outputs=[move_status]
                )
                
                download_btn.click(
                    fn=download_photo,
                    inputs=[photo_selector],
                    outputs=[download_file]
                ).then(
                    fn=lambda: gr.update(visible=True),
                    outputs=[download_file]
                )
                
                move_btn.click(
                    fn=lambda pid, target: move_photo_to_session(pid, None, target),
                    inputs=[photo_selector, move_to_dropdown],
                    outputs=[move_status, move_to_dropdown]
                )
                
                delete_btn.click(
                    fn=delete_selected_photo,
                    inputs=[photo_selector],
                    outputs=[delete_status, photo_selector]
                ).then(
                    fn=format_gallery_html,
                    inputs=[gallery_session_filter],
                    outputs=[gallery_html]
                )
                
                # Initialize gallery on load
                app.load(
                    fn=update_photo_dropdown,
                    inputs=[gallery_session_filter],
                    outputs=[photo_selector]
                )
            
            # Tab 3: Export
            with gr.Tab("📊 Export"):
                gr.Markdown("## Export Data")
                gr.Markdown("Export all photos and metadata to Excel format")
                
                export_btn = gr.Button("Export to Excel", variant="primary", size="lg")
                export_file = gr.File(label="Download Excel File")
                
                export_btn.click(
                    fn=export_data,
                    outputs=[export_file]
                )
            
            # Tab 4: About
            with gr.Tab("ℹ️ About"):
                gr.Markdown("""
                ## About Fieldmap
                
                A mobile-optimized web app for cadaver lab photo documentation and annotation.
                
                ### Key Features:
                - 📷 Capture photos with webcam
                - ✏️ Annotate photos with Gradio's ImageEditor (draw, crop, layers)
                - 📁 Organize photos into sessions
                - 💬 Add comments and notes
                - 📊 Export data to Excel
                - 🖼️ View and manage photo gallery
                
                ### Version
                **3.0** - Gradio Edition
                
                ### Technology
                Built with Gradio for reliable image editing capabilities. Replaces Streamlit canvas-based 
                drawing with Gradio's native ImageEditor component for better stability and user experience.
                
                ### Migration Notes
                This version migrates from Streamlit to Gradio to address reliability issues with canvas 
                background images in Streamlit deployments. All features from the original app are preserved.
                """)
    
    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
