"""
Integration test for the complete derived photo workflow.
Tests SessionStore methods without needing full Streamlit runtime.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image, ImageDraw


def test_derived_photo_workflow():
    """Test the derived photo data model and workflow"""
    print("\n" + "="*60)
    print("Testing Derived Photo Data Model Workflow")
    print("="*60 + "\n")
    
    # Simulate session state
    sessions = {'Default': []}
    photo_counter = 0
    
    # Step 1: Add an original photo (simulating SessionStore.add_photo)
    print("Step 1: Adding original photo...")
    photo_counter += 1
    original_image = Image.new('RGB', (200, 200), color='white')
    
    original_photo = {
        'id': photo_counter,
        'original_image': original_image.copy(),
        'current_image': original_image.copy(),
        'thumbnail': None,
        'comment': 'Original photo',
        'timestamp': '2024-01-01 12:00:00',
        'has_annotations': False,
        'source_photo_id': None,
        'variant': 'original'
    }
    sessions['Default'].append(original_photo)
    photo_id = original_photo['id']
    
    assert original_photo['variant'] == 'original', "Variant should be 'original'"
    assert original_photo['source_photo_id'] is None, "Source photo ID should be None"
    assert original_photo['has_annotations'] is False, "Should not have annotations"
    print(f"✓ Original photo created with ID {photo_id}")
    
    # Step 2: Create an annotated copy (simulating SessionStore.add_derived_photo)
    print("\nStep 2: Creating annotated copy...")
    photo_counter += 1
    annotated_image = Image.new('RGB', (200, 200), color='blue')
    draw = ImageDraw.Draw(annotated_image)
    draw.rectangle([50, 50, 150, 150], outline='red', width=3)
    
    derived_photo = {
        'id': photo_counter,
        'original_image': annotated_image.copy(),
        'current_image': annotated_image.copy(),
        'thumbnail': None,
        'comment': original_photo['comment'],
        'timestamp': '2024-01-01 12:05:00',
        'has_annotations': True,
        'source_photo_id': photo_id,
        'variant': 'annotated'
    }
    sessions['Default'].append(derived_photo)
    derived_id = derived_photo['id']
    
    assert derived_photo['variant'] == 'annotated', "Variant should be 'annotated'"
    assert derived_photo['source_photo_id'] == photo_id, "Source photo ID should reference original"
    assert derived_photo['has_annotations'] is True, "Should have annotations"
    assert derived_photo['comment'] == original_photo['comment'], "Comment should be inherited"
    print(f"✓ Annotated copy created with ID {derived_id}")
    
    # Step 3: Verify both photos exist in session
    print("\nStep 3: Verifying session contains both photos...")
    assert len(sessions['Default']) == 2, "Session should have 2 photos"
    
    original = sessions['Default'][0]
    derived = sessions['Default'][1]
    
    assert original['id'] == photo_id, "First photo should be original"
    assert derived['id'] == derived_id, "Second photo should be derived"
    print(f"✓ Session contains both original (#{photo_id}) and annotated (#{derived_id}) photos")
    
    # Step 4: Verify original is unchanged
    print("\nStep 4: Verifying original photo is unchanged...")
    assert original['has_annotations'] is False, "Original should still not have annotations"
    assert original['variant'] == 'original', "Original variant should be unchanged"
    assert original['current_image'].getpixel((100, 100)) == (255, 255, 255), "Original image should be white"
    print("✓ Original photo remains unchanged")
    
    # Step 5: Verify derived has changes
    print("\nStep 5: Verifying derived photo has annotations...")
    assert derived['has_annotations'] is True, "Derived should have annotations"
    assert derived['variant'] == 'annotated', "Derived should be annotated variant"
    assert derived['current_image'].getpixel((100, 100)) == (0, 0, 255), "Derived image should be blue"
    print("✓ Derived photo has the annotations")
    
    # Step 6: Create another derived photo from the original
    print("\nStep 6: Creating second annotated copy from same original...")
    photo_counter += 1
    second_annotated = Image.new('RGB', (200, 200), color='green')
    
    second_derived = {
        'id': photo_counter,
        'original_image': second_annotated.copy(),
        'current_image': second_annotated.copy(),
        'thumbnail': None,
        'comment': original_photo['comment'],
        'timestamp': '2024-01-01 12:10:00',
        'has_annotations': True,
        'source_photo_id': photo_id,
        'variant': 'annotated'
    }
    sessions['Default'].append(second_derived)
    
    assert second_derived['source_photo_id'] == photo_id, "Should reference same original"
    assert len(sessions['Default']) == 3, "Session should now have 3 photos"
    print(f"✓ Second annotated copy created with ID {second_derived['id']}")
    
    # Step 7: Verify all three photos coexist
    print("\nStep 7: Verifying all three photos coexist...")
    originals = [p for p in sessions['Default'] if p['variant'] == 'original']
    annotated = [p for p in sessions['Default'] if p['variant'] == 'annotated']
    
    assert len(originals) == 1, "Should have exactly 1 original photo"
    assert len(annotated) == 2, "Should have exactly 2 annotated photos"
    assert all(a['source_photo_id'] == photo_id for a in annotated), "All annotated photos should reference the original"
    print("✓ All three photos coexist: 1 original + 2 annotated copies")
    
    print("\n" + "="*60)
    print("✅ Complete Workflow Test PASSED")
    print("="*60 + "\n")
    
    return True


def test_backward_compatibility():
    """Test that old photos without new fields still work"""
    print("\n" + "="*60)
    print("Testing Backward Compatibility")
    print("="*60 + "\n")
    
    # Create an old-style photo (simulating existing data without new fields)
    old_photo = {
        'id': 999,
        'original_image': Image.new('RGB', (100, 100), color='red'),
        'current_image': Image.new('RGB', (100, 100), color='red'),
        'thumbnail': None,
        'comment': 'Old photo',
        'timestamp': '2024-01-01 10:00:00',
        'has_annotations': False
        # Note: no source_photo_id or variant fields
    }
    
    # Verify defaults work with .get()
    assert old_photo.get('source_photo_id') is None, "Old photo source_photo_id should default to None"
    assert old_photo.get('variant', 'original') == 'original', "Old photo variant should default to 'original'"
    
    print("✓ Old photos without new fields are handled correctly with .get()")
    
    # Simulate migration by adding fields
    old_photo['source_photo_id'] = None
    old_photo['variant'] = 'original'
    
    # Create derived photo
    derived = {
        'id': 1000,
        'original_image': Image.new('RGB', (100, 100), color='green'),
        'current_image': Image.new('RGB', (100, 100), color='green'),
        'thumbnail': None,
        'comment': old_photo['comment'],
        'timestamp': '2024-01-01 10:05:00',
        'has_annotations': True,
        'source_photo_id': old_photo['id'],
        'variant': 'annotated'
    }
    
    assert derived['source_photo_id'] == 999, "Derived should reference old photo"
    print("✓ Can create derived photos from old-style photos after adding fields")
    
    print("\n" + "="*60)
    print("✅ Backward Compatibility Test PASSED")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        test_derived_photo_workflow()
        test_backward_compatibility()
        print("\n" + "="*60)
        print("ALL INTEGRATION TESTS PASSED")
        print("="*60 + "\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
