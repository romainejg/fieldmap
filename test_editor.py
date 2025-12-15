"""
Simple tests for the Gradio editor app
Tests core functionality without requiring a browser
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
import numpy as np
from editor_app import PhotoSession, capture_and_save, save_edits, update_comment, export_to_excel


def test_photo_session_creation():
    """Test creating a photo session"""
    session = PhotoSession()
    assert session.counter == 0
    assert len(session.photos) == 0
    print("✓ PhotoSession creation test passed")


def test_add_photo_pil():
    """Test adding a PIL image"""
    session = PhotoSession()
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    
    photo_id = session.add_photo(img, "Test photo")
    
    assert photo_id == 1
    assert len(session.photos) == 1
    assert session.photos[0]['id'] == 1
    assert session.photos[0]['comment'] == "Test photo"
    assert session.photos[0]['edited'] == False
    print("✓ Add PIL photo test passed")


def test_add_photo_numpy():
    """Test adding a numpy array image"""
    session = PhotoSession()
    
    # Create a numpy array image
    img_array = np.zeros((100, 100, 3), dtype=np.uint8)
    img_array[:, :] = [255, 0, 0]  # Red
    
    photo_id = session.add_photo(img_array, "Numpy photo")
    
    assert photo_id == 1
    assert isinstance(session.photos[0]['current'], Image.Image)
    print("✓ Add numpy photo test passed")


def test_get_photo():
    """Test retrieving a photo"""
    session = PhotoSession()
    img = Image.new('RGB', (100, 100), color='blue')
    
    photo_id = session.add_photo(img)
    photo = session.get_photo(photo_id)
    
    assert photo is not None
    assert photo['id'] == photo_id
    print("✓ Get photo test passed")


def test_update_image():
    """Test updating photo image"""
    session = PhotoSession()
    original_img = Image.new('RGB', (100, 100), color='green')
    photo_id = session.add_photo(original_img)
    
    # Create edited image
    edited_img = Image.new('RGB', (100, 100), color='yellow')
    
    success = session.update_image(photo_id, edited_img)
    
    assert success == True
    photo = session.get_photo(photo_id)
    assert photo['edited'] == True
    print("✓ Update image test passed")


def test_update_image_with_dict():
    """Test updating image when editor returns dict"""
    session = PhotoSession()
    original_img = Image.new('RGB', (100, 100), color='cyan')
    photo_id = session.add_photo(original_img)
    
    # Simulate ImageEditor output (dict with background)
    edited_img = Image.new('RGB', (100, 100), color='magenta')
    editor_output = {'background': edited_img, 'layers': []}
    
    success = session.update_image(photo_id, editor_output)
    
    assert success == True
    photo = session.get_photo(photo_id)
    assert photo['edited'] == True
    print("✓ Update image with dict test passed")


def test_photo_list():
    """Test getting photo list for dropdown"""
    session = PhotoSession()
    
    # Add multiple photos
    for i in range(3):
        img = Image.new('RGB', (50, 50), color=(i*80, 0, 0))
        session.add_photo(img, f"Photo {i+1}")
    
    photo_list = session.get_photo_list()
    
    assert len(photo_list) == 3
    assert all(isinstance(item, tuple) and len(item) == 2 for item in photo_list)
    print("✓ Photo list test passed")


def test_export_empty_session():
    """Test exporting empty session"""
    result = export_to_excel()
    assert result is None
    print("✓ Export empty session test passed")


def test_export_with_photos():
    """Test exporting session with photos"""
    global photo_session
    from editor_app import photo_session
    
    # Add a test photo
    img = Image.new('RGB', (100, 100), color='white')
    photo_session.add_photo(img, "Export test")
    
    result = export_to_excel()
    
    assert result is not None
    assert result.startswith('/tmp/fieldmap_export_')
    assert result.endswith('.xlsx')
    
    # Verify file exists
    import os
    assert os.path.exists(result)
    print("✓ Export with photos test passed")
    
    # Clean up
    os.remove(result)


def test_capture_and_save_function():
    """Test the capture_and_save function"""
    img = Image.new('RGB', (200, 200), color='orange')
    
    preview, status, editor_img, dropdown_update = capture_and_save(img)
    
    assert preview is not None
    assert "saved" in status.lower()
    assert editor_img is not None
    print("✓ Capture and save function test passed")


def test_capture_none_image():
    """Test capturing with None image"""
    preview, status, editor_img, dropdown_update = capture_and_save(None)
    
    assert preview is None
    assert "capture" in status.lower()
    print("✓ Capture None image test passed")


def run_all_tests():
    """Run all tests"""
    tests = [
        test_photo_session_creation,
        test_add_photo_pil,
        test_add_photo_numpy,
        test_get_photo,
        test_update_image,
        test_update_image_with_dict,
        test_photo_list,
        test_export_empty_session,
        test_export_with_photos,
        test_capture_and_save_function,
        test_capture_none_image,
    ]
    
    print("\n" + "="*60)
    print("Running Gradio Editor App Tests")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
