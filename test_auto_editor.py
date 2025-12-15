"""
Test for auto-edit photo feature
Verifies that the photo editor is automatically available for the last photo
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
import io


def test_photo_editor_component_exists():
    """Test that the photo_editor component can be imported"""
    try:
        from components.photo_editor import photo_editor, decode_image_from_dataurl
        print("✓ Photo editor component imports successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import photo editor: {e}")
        return False


def test_decode_image_from_dataurl():
    """Test the decode_image_from_dataurl function"""
    from components.photo_editor import decode_image_from_dataurl
    
    # Create a test image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Convert to data URL
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    import base64
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    data_url = f"data:image/png;base64,{img_base64}"
    
    # Test decoding
    try:
        decoded_img = decode_image_from_dataurl(data_url)
        assert isinstance(decoded_img, Image.Image)
        assert decoded_img.size == (100, 100)
        print("✓ decode_image_from_dataurl works correctly")
        return True
    except Exception as e:
        print(f"✗ decode_image_from_dataurl failed: {e}")
        return False


def test_app_structure():
    """Test that app.py has the correct structure"""
    try:
        with open('/home/runner/work/fieldmap/fieldmap/app.py', 'r') as f:
            content = f.read()
        
        # Check that the old "Edit Photo" button is removed from the Fieldmap page
        # We should not have "Edit Photo" button in the last photo section
        lines = content.split('\n')
        
        # Find the "Last Photo" section
        in_last_photo_section = False
        has_edit_button_in_last_photo = False
        has_photo_editor_call = False
        has_preview_image = False
        
        for i, line in enumerate(lines):
            if 'st.subheader("Last Photo")' in line:
                in_last_photo_section = True
            elif in_last_photo_section and 'class GalleryPage' in line:
                # Exited the last photo section
                break
            elif in_last_photo_section:
                if 'st.button("Edit Photo"' in line and 'edit_photo_btn' in line:
                    has_edit_button_in_last_photo = True
                if 'photo_editor(' in line:
                    has_photo_editor_call = True
                if 'st.image(last_photo[\'current_image\'], caption="Current Photo"' in line:
                    has_preview_image = True
        
        # Verify expectations
        if has_edit_button_in_last_photo:
            print("✗ 'Edit Photo' button still exists in Last Photo section (should be removed)")
            return False
        else:
            print("✓ 'Edit Photo' button removed from Last Photo section")
        
        if has_preview_image:
            print("✗ Photo preview still exists in Last Photo section (should be removed)")
            return False
        else:
            print("✓ Photo preview removed from Last Photo section")
        
        if not has_photo_editor_call:
            print("✗ photo_editor() not called in Last Photo section")
            return False
        else:
            print("✓ photo_editor() is called in Last Photo section")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to analyze app.py: {e}")
        return False


def test_no_show_editor_state():
    """Test that show_editor state is no longer used in Fieldmap page"""
    try:
        with open('/home/runner/work/fieldmap/fieldmap/app.py', 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Find FieldmapPage class
        in_fieldmap_class = False
        uses_show_editor = False
        
        for i, line in enumerate(lines):
            if 'class FieldmapPage' in line:
                in_fieldmap_class = True
            elif in_fieldmap_class and 'class GalleryPage' in line:
                # Exited FieldmapPage class
                break
            elif in_fieldmap_class:
                if 'show_editor' in line and 'show_gallery_editor' not in line:
                    uses_show_editor = True
                    print(f"✗ Line {i+1} still uses 'show_editor' state: {line.strip()}")
        
        if not uses_show_editor:
            print("✓ 'show_editor' state removed from FieldmapPage")
            return True
        else:
            print("✗ 'show_editor' state still used in FieldmapPage")
            return False
        
    except Exception as e:
        print(f"✗ Failed to check show_editor state: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    tests = [
        test_photo_editor_component_exists,
        test_decode_image_from_dataurl,
        test_app_structure,
        test_no_show_editor_state,
    ]
    
    print("\n" + "="*60)
    print("Running Auto-Edit Photo Feature Tests")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED with exception: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
