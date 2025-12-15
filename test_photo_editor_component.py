"""
Simple test for photo_editor Streamlit component
Tests that the component can be imported and initialized
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from components.photo_editor import photo_editor, decode_image_from_dataurl, _BUILD_DIR, _DEV_DIR
from PIL import Image
import base64
import io


def test_component_import():
    """Test that component can be imported"""
    assert photo_editor is not None
    print("✓ Component import test passed")


def test_build_directory_exists():
    """Test that build directory exists and has expected structure"""
    assert _BUILD_DIR.exists(), "Build directory should exist"
    
    # Check for index.html
    index_path = _BUILD_DIR / "index.html"
    assert index_path.exists(), "index.html should exist in build directory"
    
    # Check for main.js
    main_js_path = _BUILD_DIR / "main.js"
    assert main_js_path.exists(), "main.js should exist in build directory"
    
    print("✓ Build directory structure test passed")


def test_decode_image_from_dataurl():
    """Test decoding image from data URL"""
    # Create a simple test image
    img = Image.new('RGB', (50, 50), color='blue')
    
    # Convert to data URL
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    b64_str = base64.b64encode(img_bytes).decode('utf-8')
    data_url = f"data:image/png;base64,{b64_str}"
    
    # Decode it back
    decoded_img = decode_image_from_dataurl(data_url)
    
    assert decoded_img is not None
    assert isinstance(decoded_img, Image.Image)
    assert decoded_img.size == (50, 50)
    print("✓ Decode image from data URL test passed")


def test_decode_invalid_dataurl():
    """Test decoding invalid data URL"""
    try:
        result = decode_image_from_dataurl("invalid_data_url")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid data URL" in str(e)
    print("✓ Decode invalid data URL test passed")


def test_component_paths():
    """Test component paths are correctly set"""
    # Check that _BUILD_DIR points to correct location
    assert _BUILD_DIR == Path(__file__).parent / "components" / "photo_editor" / "frontend" / "build"
    
    # Check that _DEV_DIR points to correct location
    assert _DEV_DIR == Path(__file__).parent / "components" / "photo_editor" / "frontend"
    
    print("✓ Component paths test passed")


def run_all_tests():
    """Run all tests"""
    tests = [
        test_component_import,
        test_build_directory_exists,
        test_decode_image_from_dataurl,
        test_decode_invalid_dataurl,
        test_component_paths,
    ]
    
    print("\n" + "="*60)
    print("Running Photo Editor Component Tests")
    print("="*60 + "\n")
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
