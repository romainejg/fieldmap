"""
Fieldmap - Gradio Photo Editor
A minimal Gradio app demonstrating ImageEditor for photo annotation
This can be expanded or used alongside the existing Streamlit app
"""

import gradio as gr
from PIL import Image
import pandas as pd
import io
from datetime import datetime
import numpy as np


class PhotoSession:
    """Simple photo session manager"""
    def __init__(self):
        self.photos = []
        self.counter = 0
    
    def add_photo(self, image, comment=""):
        if image is None:
            return None
        
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image.astype('uint8'))
        
        self.counter += 1
        photo = {
            'id': self.counter,
            'original': image.copy(),
            'current': image.copy(),
            'comment': comment,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'edited': False
        }
        self.photos.append(photo)
        return self.counter
    
    def get_photo(self, photo_id):
        for p in self.photos:
            if p['id'] == photo_id:
                return p
        return None
    
    def update_image(self, photo_id, new_image):
        photo = self.get_photo(photo_id)
        if photo and new_image is not None:
            if isinstance(new_image, dict):
                # ImageEditor returns dict with 'background' and 'layers'
                img = new_image.get('background') or new_image.get('composite')
            else:
                img = new_image
            
            if img is not None:
                if isinstance(img, np.ndarray):
                    img = Image.fromarray(img.astype('uint8'))
                photo['current'] = img
                photo['edited'] = True
                return True
        return False
    
    def get_photo_list(self):
        return [(f"ID {p['id']} - {p['timestamp']}", p['id']) for p in self.photos]


# Global session
photo_session = PhotoSession()


def capture_and_save(image):
    """Capture photo and add to session"""
    if image is None:
        return None, "Please capture a photo first", None, []
    
    photo_id = photo_session.add_photo(image, "")
    photo_list = photo_session.get_photo_list()
    
    return image, f"✓ Photo saved! (ID: {photo_id})", image, gr.update(choices=photo_list, value=photo_id)


def load_photo_for_edit(photo_id):
    """Load photo into editor"""
    if photo_id is None:
        return None, "No photo selected"
    
    photo = photo_session.get_photo(photo_id)
    if photo:
        return photo['current'], f"Editing Photo ID: {photo_id}"
    return None, "Photo not found"


def save_edits(editor_data, photo_id):
    """Save edited photo"""
    if photo_id is None:
        return None, "No photo selected", []
    
    if editor_data is None:
        return None, "No edits made", []
    
    # Handle ImageEditor output
    img_to_save = None
    if isinstance(editor_data, dict):
        # Try to get the composite or background
        img_to_save = editor_data.get('background') or editor_data.get('composite')
    elif isinstance(editor_data, (Image.Image, np.ndarray)):
        img_to_save = editor_data
    
    if img_to_save is not None:
        if photo_session.update_image(photo_id, img_to_save):
            photo = photo_session.get_photo(photo_id)
            return photo['current'], f"✓ Photo {photo_id} updated!", photo_session.get_photo_list()
    
    return None, "Failed to save edits", []


def update_comment(photo_id, comment):
    """Update photo comment"""
    if photo_id is None:
        return "No photo selected"
    
    photo = photo_session.get_photo(photo_id)
    if photo:
        photo['comment'] = comment
        return f"✓ Comment updated for Photo {photo_id}"
    return "Photo not found"


def export_to_excel():
    """Export data to Excel"""
    if not photo_session.photos:
        return None
    
    data = []
    for p in photo_session.photos:
        data.append({
            'Photo ID': p['id'],
            'Timestamp': p['timestamp'],
            'Comment': p['comment'],
            'Edited': 'Yes' if p['edited'] else 'No'
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Photos')
    output.seek(0)
    
    # Save to temp file
    temp_path = f"/tmp/fieldmap_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    with open(temp_path, 'wb') as f:
        f.write(output.getvalue())
    return temp_path


# Create the Gradio interface
with gr.Blocks(title="Fieldmap - Photo Editor", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔬 Fieldmap - Lab Photo Editor")
    gr.Markdown("*Powered by Gradio ImageEditor for reliable photo annotation*")
    
    with gr.Tabs():
        # Tab 1: Capture & Edit
        with gr.Tab("📷 Capture & Edit"):
            gr.Markdown("## Capture Photo")
            
            with gr.Row():
                with gr.Column():
                    camera = gr.Image(
                        label="Camera",
                        sources=["webcam"],
                        type="pil"
                    )
                    capture_btn = gr.Button("Save Photo", variant="primary", size="lg")
                    capture_status = gr.Textbox(label="Status", interactive=False)
                
                with gr.Column():
                    preview = gr.Image(label="Last Saved Photo", type="pil", interactive=False)
            
            gr.Markdown("---")
            gr.Markdown("## Edit Photo")
            
            photo_selector = gr.Dropdown(
                label="Select Photo to Edit",
                choices=[],
                interactive=True
            )
            load_btn = gr.Button("Load Photo")
            editor_status = gr.Textbox(label="Status", interactive=False)
            
            editor = gr.ImageEditor(
                label="Photo Editor - Draw annotations here",
                type="pil"
            )
            
            with gr.Row():
                save_edits_btn = gr.Button("Save Edits", variant="primary")
                
            edited_preview = gr.Image(label="Edited Photo", type="pil", interactive=False)
            
            gr.Markdown("---")
            gr.Markdown("## Add Comment")
            
            comment_box = gr.Textbox(label="Notes/Comments", lines=3, placeholder="Add notes about this photo...")
            update_comment_btn = gr.Button("Update Comment")
            comment_status = gr.Textbox(label="Status", interactive=False)
        
        # Tab 2: Gallery
        with gr.Tab("🖼️ Gallery"):
            gr.Markdown("## Photo Gallery")
            
            refresh_btn = gr.Button("Refresh Gallery")
            
            def create_gallery():
                if not photo_session.photos:
                    return []
                return [(p['current'], f"ID {p['id']} - {p['timestamp']}\nEdited: {'Yes' if p['edited'] else 'No'}") 
                        for p in photo_session.photos]
            
            gallery = gr.Gallery(
                label="All Photos",
                columns=3,
                height="auto"
            )
            
            refresh_btn.click(
                fn=create_gallery,
                outputs=[gallery]
            )
        
        # Tab 3: Export
        with gr.Tab("📊 Export"):
            gr.Markdown("## Export Data")
            gr.Markdown("Download all photos and metadata as Excel")
            
            export_btn = gr.Button("Export to Excel", variant="primary", size="lg")
            export_file = gr.File(label="Download")
            
            export_btn.click(
                fn=export_to_excel,
                outputs=[export_file]
            )
        
        # Tab 4: About
        with gr.Tab("ℹ️ About"):
            gr.Markdown("""
            ## About Fieldmap
            
            A mobile-optimized photo annotation app for biomedical engineers.
            
            ### Key Features:
            - 📷 Camera capture
            - ✏️ Photo annotation with Gradio ImageEditor
            - 💬 Comments and notes
            - 📊 Excel export
            - 🖼️ Photo gallery
            
            ### Version
            **3.0** - Gradio Edition
            
            ### Why Gradio?
            This version uses Gradio's native ImageEditor component which provides:
            - Reliable image editing with brushes, shapes, and layers
            - Better stability compared to Streamlit canvas components
            - Built-in tools for drawing, cropping, and image manipulation
            
            Gradio ImageEditor is designed specifically for editing existing images and returns
            the edited image directly, making it ideal for annotation workflows.
            """)
    
    # Event handlers
    capture_btn.click(
        fn=capture_and_save,
        inputs=[camera],
        outputs=[preview, capture_status, editor, photo_selector]
    )
    
    load_btn.click(
        fn=load_photo_for_edit,
        inputs=[photo_selector],
        outputs=[editor, editor_status]
    )
    
    save_edits_btn.click(
        fn=save_edits,
        inputs=[editor, photo_selector],
        outputs=[edited_preview, editor_status, photo_selector]
    )
    
    update_comment_btn.click(
        fn=update_comment,
        inputs=[photo_selector, comment_box],
        outputs=[comment_status]
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
