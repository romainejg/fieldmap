"""
Demo script to test the photo editor component
This will show how the editor automatically opens
"""

import streamlit as st
from PIL import Image, ImageDraw
import sys
from pathlib import Path

# Add components to path
sys.path.insert(0, str(Path(__file__).parent))

from components.photo_editor import photo_editor, decode_image_from_dataurl

st.set_page_config(page_title="Photo Editor Test", layout="wide")

st.title("Photo Editor Auto-Open Test")

st.markdown("""
This demo tests the automatic photo editor functionality.
The marker.js editor should open automatically when a photo is loaded.
""")

# Initialize session state
if 'test_photo' not in st.session_state:
    # Create a test photo
    img = Image.new('RGB', (640, 480), color='lightblue')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 590, 430], outline='darkblue', width=5)
    draw.text((200, 220), "TEST PHOTO", fill='black')
    draw.text((150, 250), "Draw on me!", fill='gray')
    st.session_state.test_photo = img
    st.session_state.edited_photo = None

st.markdown("---")
st.markdown("## Step 1: Create Test Photo")

if st.button("Generate New Test Photo"):
    img = Image.new('RGB', (640, 480), color='lightgreen')
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 540, 380], outline='darkgreen', width=5)
    draw.text((220, 220), "NEW PHOTO", fill='black')
    st.session_state.test_photo = img
    st.session_state.edited_photo = None
    st.rerun()

st.markdown("---")
st.markdown("## Step 2: Photo Editor (Auto-Opens)")
st.info("The marker.js editor popup should open automatically below. Use the drawing tools to annotate, then click 'Save' in the popup.")

# Call the photo editor - it should auto-open
editor_result = photo_editor(
    image=st.session_state.test_photo,
    key="demo_editor"
)

# Handle editor result
if editor_result is not None:
    if editor_result.get('saved') and editor_result.get('pngDataUrl'):
        try:
            edited_image = decode_image_from_dataurl(editor_result['pngDataUrl'])
            st.session_state.edited_photo = edited_image
            st.success("✅ Photo edited and saved!")
            st.rerun()
        except Exception as e:
            st.error(f"Error processing edited image: {str(e)}")
    elif editor_result.get('cancelled'):
        st.info("Editing cancelled")

st.markdown("---")
st.markdown("## Step 3: Results")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Original Photo:**")
    st.image(st.session_state.test_photo, use_column_width=True)

with col2:
    st.markdown("**Edited Photo:**")
    if st.session_state.edited_photo:
        st.image(st.session_state.edited_photo, use_column_width=True)
        st.success("Photo has been annotated!")
    else:
        st.info("No edits yet. Use the editor above to annotate the photo.")
