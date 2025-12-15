# Fieldmap - Integration Guide

## Choosing Your Implementation

This repository now includes both **Streamlit** and **Gradio** implementations for the photo annotation app. Choose the one that best fits your needs.

## Quick Start

### Option 1: Minimal Gradio Editor (Recommended for Testing)
Best for: Quick testing, minimal setup, standalone photo editor

```bash
pip install -r requirements.txt
python editor_app.py
```

**Features:**
- Camera capture
- ImageEditor for annotations
- Photo gallery
- Excel export
- ~250 lines of code

**Use when:** You want a simple, reliable photo annotation tool without complexity.

---

### Option 2: Full Gradio Migration
Best for: Production deployment, new installations, avoiding Streamlit issues

```bash
pip install -r requirements.txt
python gradio_app.py
```

**Features:**
- Full session management
- All features from Streamlit version
- Multiple sessions support
- Photo organization
- Comprehensive gallery
- Excel export
- ~700 lines of code

**Use when:** You want all features and are ready to migrate away from Streamlit completely.

---

### Option 3: Original Streamlit App
Best for: Existing users, no migration needed (but has canvas issues)

```bash
pip install -r requirements.txt
streamlit run app.py
```

**Features:**
- Original application
- Custom marker.js component
- Full feature set
- **Known issue:** Background image display issues in st_canvas on some deployments

**Use when:** You're already using it and haven't experienced canvas issues, or for development/testing.

---

## Why Consider Gradio?

### Problem with Streamlit Canvas
The Streamlit community has multiple reports of background image issues with `st_canvas` in deployed/multipage contexts:
- Background images not displaying on Streamlit Cloud
- Inconsistent behavior across deployments
- Complex custom component integration

### Gradio ImageEditor Benefits
1. **Built-in image editing:** No custom components needed
2. **Reliable:** Designed specifically for image editing workflows
3. **Direct output:** Returns edited PIL Image, not data URLs
4. **Production-ready:** Stable in deployment
5. **Mobile-friendly:** Responsive design out of the box

## Feature Comparison

| Feature | Streamlit (app.py) | Gradio Full (gradio_app.py) | Gradio Minimal (editor_app.py) |
|---------|-------------------|---------------------------|------------------------------|
| Camera Capture | ✅ | ✅ | ✅ |
| Photo Annotation | ✅ (marker.js) | ✅ (ImageEditor) | ✅ (ImageEditor) |
| Multiple Sessions | ✅ | ✅ | ❌ |
| Photo Gallery | ✅ | ✅ | ✅ (Simple) |
| Comments/Notes | ✅ | ✅ | ✅ |
| Excel Export | ✅ | ✅ | ✅ |
| Move Photos | ✅ | ✅ | ❌ |
| Background Reliability | ⚠️ Issues | ✅ Stable | ✅ Stable |
| Deployment Complexity | High | Low | Low |
| Code Size | ~860 lines | ~700 lines | ~250 lines |

## Migration Path

### For New Installations
Start with **editor_app.py** (Option 1) to test Gradio's ImageEditor. If you need session management and organization features, move to **gradio_app.py** (Option 2).

### For Existing Streamlit Users

#### Path A: Full Migration (Recommended)
1. Test your workflow with `editor_app.py`
2. Export your data from the Streamlit app
3. Switch to `gradio_app.py`
4. Recreate sessions and import photos

#### Path B: Hybrid Approach
1. Keep `app.py` for main interface
2. Run `editor_app.py` on a different port (e.g., 7860)
3. Link from Streamlit to Gradio for photo editing
4. Use shared storage (files, S3, database) for photos
5. Streamlit reloads edited photos from storage

Example hybrid workflow:
```python
# In Streamlit app.py
if st.button("Edit Photo"):
    # Save photo to shared storage
    photo_path = save_to_storage(photo)
    st.info(f"Open the editor: http://localhost:7860")
    st.info(f"Photo ID: {photo_id}")
    
# User edits in Gradio editor at localhost:7860
# Gradio saves edited photo back to shared storage

# In Streamlit, reload from storage
if st.button("Reload Edited Photo"):
    edited_photo = load_from_storage(photo_id)
```

## Deployment

### Streamlit Deployment
```bash
streamlit run app.py --server.port 8501
```

### Gradio Deployment
```bash
# Minimal editor
python editor_app.py

# Full app
python gradio_app.py

# Or with custom settings
python editor_app.py --server-port 7860 --share
```

### Docker Deployment
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# For Gradio
CMD ["python", "editor_app.py"]

# Or for Streamlit
# CMD ["streamlit", "run", "app.py"]
```

## Testing Locally

### Test Minimal Gradio Editor
```bash
python editor_app.py
# Open browser to http://localhost:7860
# Capture photo → Edit → Save → Check gallery
```

### Test Full Gradio App
```bash
python gradio_app.py
# Test: Create session → Capture → Edit → Comment → Export
```

### Test Original Streamlit
```bash
streamlit run app.py
# Test all features including canvas drawing
```

## Troubleshooting

### Gradio "localhost not accessible" error
This is normal in sandboxed environments. In production:
```python
demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
```

### Gradio API warnings (TypeError: argument of type 'bool' is not iterable)
These are internal Gradio warnings that don't affect functionality. They're related to API info generation and can be ignored.

### Image not showing in Gradio ImageEditor
Make sure you're loading the image correctly:
```python
# ✅ Correct
editor = gr.ImageEditor(type="pil")

# When setting value
photo = Image.open("photo.jpg")
editor.update(value=photo)

# ❌ Incorrect
editor = gr.ImageEditor(value="path/to/image.jpg")  # Won't work
```

## Performance Considerations

### Streamlit
- Reruns entire script on interaction
- Session state management required
- Can be slower with many photos

### Gradio
- Event-driven, only runs specific functions
- Built-in state management
- Better performance with large galleries

## Security Notes

- Both apps store photos in memory by default
- For production, implement persistent storage
- Add authentication for multi-user deployments
- Sanitize user inputs in comments
- Consider HTTPS for camera access in browsers

## Next Steps

1. **Try it:** Start with `python editor_app.py`
2. **Test editing:** Capture a photo and use the ImageEditor tools
3. **Compare:** Try both Streamlit and Gradio versions
4. **Decide:** Choose the best option for your use case
5. **Deploy:** Follow deployment guide for your chosen platform

## Support

- **Gradio docs:** https://www.gradio.app/docs/
- **Streamlit docs:** https://docs.streamlit.io/
- **Issues:** Open a GitHub issue in this repository

## Conclusion

- **For reliability:** Choose Gradio (editor_app.py or gradio_app.py)
- **For simplicity:** Choose editor_app.py
- **For features:** Choose gradio_app.py
- **For compatibility:** Keep app.py but consider migration if you experience canvas issues
