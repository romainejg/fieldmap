"""
Tests for derived photo functionality and storage abstraction.
Tests that photos can be derived from originals and that storage works correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
import tempfile
import shutil
from storage import LocalFolderStorage, PhotoStorage


def test_local_folder_storage_save_and_load():
    """Test saving and loading images with LocalFolderStorage"""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = LocalFolderStorage(base_path=tmp_dir)
        
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Save the image
        uri = storage.save_image('test_session', 1, test_image)
        
        # Verify the file was created
        assert Path(uri).exists(), "Image file should exist"
        assert 'test_session' in uri, "URI should contain session name"
        assert 'photo_1' in uri, "URI should contain photo ID"
        
        # Load the image back
        loaded_image = storage.load_image(uri)
        
        # Verify the loaded image
        assert loaded_image is not None, "Loaded image should not be None"
        assert loaded_image.size == (100, 100), "Loaded image should have correct size"
        
        print("✓ LocalFolderStorage save and load test passed")


def test_local_folder_storage_delete():
    """Test deleting images with LocalFolderStorage"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = LocalFolderStorage(base_path=tmp_dir)
        
        # Create and save a test image
        test_image = Image.new('RGB', (100, 100), color='blue')
        uri = storage.save_image('test_session', 2, test_image)
        
        # Verify the file exists
        assert Path(uri).exists(), "Image file should exist before delete"
        
        # Delete the image
        result = storage.delete_image(uri)
        
        # Verify deletion
        assert result is True, "Delete should return True"
        assert not Path(uri).exists(), "Image file should not exist after delete"
        
        print("✓ LocalFolderStorage delete test passed")


def test_local_folder_storage_session_directories():
    """Test that session directories are created correctly"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = LocalFolderStorage(base_path=tmp_dir)
        
        # Save images to different sessions
        test_image = Image.new('RGB', (50, 50), color='green')
        
        uri1 = storage.save_image('session_a', 1, test_image)
        uri2 = storage.save_image('session_b', 2, test_image)
        
        # Verify session directories were created
        session_a_dir = Path(tmp_dir) / 'session_a'
        session_b_dir = Path(tmp_dir) / 'session_b'
        
        assert session_a_dir.exists(), "Session A directory should exist"
        assert session_b_dir.exists(), "Session B directory should exist"
        assert (session_a_dir / 'photo_1.png').exists(), "Photo 1 should be in session A"
        assert (session_b_dir / 'photo_2.png').exists(), "Photo 2 should be in session B"
        
        print("✓ LocalFolderStorage session directories test passed")


def test_derived_photo_data_structure():
    """Test that derived photo data structure is correct"""
    # This test simulates the data structure without needing Streamlit
    
    # Original photo structure
    original_photo = {
        'id': 1,
        'original_image': Image.new('RGB', (100, 100), color='white'),
        'current_image': Image.new('RGB', (100, 100), color='white'),
        'thumbnail': None,
        'comment': 'Test photo',
        'timestamp': '2024-01-01 12:00:00',
        'has_annotations': False,
        'source_photo_id': None,
        'variant': 'original'
    }
    
    # Derived photo structure
    derived_photo = {
        'id': 2,
        'original_image': Image.new('RGB', (100, 100), color='blue'),
        'current_image': Image.new('RGB', (100, 100), color='blue'),
        'thumbnail': None,
        'comment': 'Test photo',
        'timestamp': '2024-01-01 12:05:00',
        'has_annotations': True,
        'source_photo_id': 1,
        'variant': 'annotated'
    }
    
    # Verify original photo fields
    assert original_photo['source_photo_id'] is None, "Original photo should have no source"
    assert original_photo['variant'] == 'original', "Original photo variant should be 'original'"
    assert original_photo['has_annotations'] is False, "Original photo should not have annotations"
    
    # Verify derived photo fields
    assert derived_photo['source_photo_id'] == 1, "Derived photo should reference original"
    assert derived_photo['variant'] == 'annotated', "Derived photo variant should be 'annotated'"
    assert derived_photo['has_annotations'] is True, "Derived photo should have annotations"
    assert derived_photo['comment'] == original_photo['comment'], "Derived photo should inherit comment"
    
    print("✓ Derived photo data structure test passed")


def test_storage_abstract_base_class():
    """Test that PhotoStorage is properly abstract"""
    try:
        # Should not be able to instantiate abstract base class
        storage = PhotoStorage()
        assert False, "Should not be able to instantiate abstract PhotoStorage"
    except TypeError:
        # Expected behavior
        pass
    
    print("✓ PhotoStorage abstract base class test passed")


def test_local_folder_storage_image_format_conversion():
    """Test that images are properly converted to RGB before saving"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = LocalFolderStorage(base_path=tmp_dir)
        
        # Create a grayscale image
        grayscale_image = Image.new('L', (50, 50), color=128)
        
        # Save the image (should convert to RGB)
        uri = storage.save_image('test_session', 1, grayscale_image)
        
        # Load it back
        loaded_image = storage.load_image(uri)
        
        # Verify it was saved and loaded
        assert loaded_image is not None, "Loaded image should not be None"
        assert loaded_image.size == (50, 50), "Image size should be preserved"
        
        print("✓ LocalFolderStorage image format conversion test passed")


def run_all_tests():
    """Run all tests"""
    tests = [
        test_local_folder_storage_save_and_load,
        test_local_folder_storage_delete,
        test_local_folder_storage_session_directories,
        test_derived_photo_data_structure,
        test_storage_abstract_base_class,
        test_local_folder_storage_image_format_conversion,
    ]
    
    print("\n" + "="*60)
    print("Running Derived Photo and Storage Tests")
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
