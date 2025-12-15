# Implementation Summary: Derived Photos and Storage Abstraction

This document summarizes the changes made to implement derived photo functionality and storage abstraction.

## Changes Made

### 1. Data Model Updates (SessionStore in app.py)

#### New Photo Fields
- `source_photo_id`: References the original photo ID for derived photos (None for originals)
- `variant`: Either "original" or "annotated" to distinguish photo types

#### New Method: add_derived_photo()
Creates a new photo derived from an existing photo without modifying the original.

**Signature:**
```python
def add_derived_photo(self, base_photo_id: int, session_name: str, image: Image.Image, comment=None) -> int
```

**Behavior:**
- Creates a new photo entry with unique ID
- Sets `source_photo_id` to reference the base photo
- Sets `variant` to "annotated"
- Sets `has_annotations` to True
- Inherits comment from base photo if not provided
- Returns the new photo ID

### 2. Editor Save Behavior Changes

#### FieldmapPage (lines 432-457)
**Before:**
```python
last_photo['current_image'] = edited_image
last_photo['has_annotations'] = True
```

**After:**
```python
new_photo_id = self.session_store.add_derived_photo(
    base_photo_id=last_photo['id'],
    session_name=self.session_store.current_session,
    image=edited_image,
    comment=last_photo['comment']
)
st.session_state.last_saved_photo_id = new_photo_id
```

**Result:** Original photo remains unchanged; new annotated copy is created.

#### GalleryPage (lines 696-722)
Similar changes to gallery editor - creates derived photo instead of modifying original.

### 3. Gallery UI Simplification

#### Removed
- Separate collapsible sections for photo selection
- Always-visible detail panel below draggable board

#### Added
- Click-to-expand detail view using `st.expander()`
- Direct thumbnail grid per session
- "📝" emoji badge for annotated photos in button labels
- Source photo reference in detail view

#### Updated CSS
- Fixed hover to only change `box-shadow` (not size)
- Tile dimensions remain constant (100px x 100px)

#### State Management
- Changed from `selected_photo_id`/`selected_photo_session` to single `gallery_selected` dict
- Consistent close behavior clears selection and reruns

### 4. Storage Abstraction Layer (storage.py)

#### PhotoStorage Abstract Base Class
Defines interface for storage backends:
- `save_image(session_name, photo_id, pil_image) -> uri`
- `load_image(uri) -> Image`
- `delete_image(uri) -> bool`

#### LocalFolderStorage Implementation
- Stores photos as PNG in `./data/<session_name>/photo_<id>.png`
- Creates session directories automatically
- Handles RGB conversion before saving
- Returns file path as URI

#### GooglePhotosStorage Placeholder
- Raises NotImplementedError
- Ready for future implementation

### 5. Backward Compatibility

#### Existing Photos
Old photos without `source_photo_id` or `variant` fields still work:
- Code uses `.get('source_photo_id')` which returns None for old photos
- Code uses `.get('variant', 'original')` which defaults to "original"

#### Legacy Annotations
Photos with `has_annotations=True` but no `source_photo_id`:
- Still display with before/after view
- Can still be reset using "Reset Annotations" button
- New edits create derived photos going forward

### 6. Test Coverage

#### test_derived_photos.py
- LocalFolderStorage save/load/delete
- Session directory creation
- Image format conversion
- Abstract base class validation
- Data structure correctness

#### test_integration.py
- Complete workflow: add photo → create derived → verify
- Multiple derived photos from same original
- Backward compatibility with old photo format
- Field inheritance and relationships

#### Existing Tests
- All existing tests still pass (test_photo_editor_component.py)

## User Experience Changes

### Taking and Editing Photos (Fieldmap Page)
1. User takes photo → saved as original (ID: 1)
2. User edits photo → saved as new annotated copy (ID: 2)
3. "Last Photo" section now shows the annotated copy (ID: 2)
4. Original photo (ID: 1) remains in session unchanged
5. Both photos appear in Gallery

### Gallery Workflow
1. User sees draggable board with all photos
2. Annotated photos show "📝" badge in labels
3. User clicks a photo tile → detail expander opens below
4. Detail view shows:
   - Photo type (Original or 📝 Edited)
   - For edited: "Derived from Photo #X"
   - Full image, metadata, comment editing
   - Edit/Move/Delete actions
5. User clicks "✕ Close Details" → expander closes
6. User edits a photo → new derived copy created (doesn't modify existing)

## Files Modified

- `app.py`: Data model, editor handlers, gallery UI
- `.gitignore`: Added `data/` folder

## Files Added

- `storage.py`: Storage abstraction layer
- `test_derived_photos.py`: Storage and data model tests
- `test_integration.py`: End-to-end workflow tests
- `STORAGE_README.md`: Storage module documentation
- `IMPLEMENTATION_SUMMARY.md`: This file

## Migration Notes

### For Existing Data
No migration required. The code handles old photos gracefully using `.get()` with defaults.

### For Future Storage Integration
To enable persistent storage:
1. Initialize `LocalFolderStorage` in SessionStore
2. Optionally save images to disk in `add_photo()` and `add_derived_photo()`
3. Store URIs in photo data
4. Load from URI when displaying

This can be done incrementally without breaking existing functionality.

## Configuration (Future)

A configuration option could toggle storage backends:

```python
# config.py (future)
STORAGE_BACKEND = "memory"  # or "local" or "google_photos"
STORAGE_PATH = "./data"  # for local storage

# In SessionStore
if config.STORAGE_BACKEND == "local":
    self.storage = LocalFolderStorage(config.STORAGE_PATH)
else:
    self.storage = None  # in-memory only
```

## Performance Considerations

### In-Memory (Current)
- Fast: No disk I/O
- Limited: All photos in RAM
- Not persistent: Lost on refresh

### With LocalFolderStorage (Optional Future)
- Persistent: Survives refresh
- Scalable: Not limited by RAM
- Slightly slower: Disk I/O overhead

### Optimization Strategy
- Keep thumbnails in memory for gallery
- Load full images on-demand
- Use PIL thumbnail for efficient preview generation
- Cache recently viewed photos

## Security Considerations

### Local Storage
- Images stored as files in `./data/`
- Ensure proper file permissions
- Add to `.gitignore` to prevent committing user data

### Google Photos (Future)
- Requires OAuth2 authentication
- Store credentials securely (not in git)
- Respect user privacy and data ownership
- Handle API rate limits

## Next Steps (Not Implemented Yet)

1. **Optional Persistent Storage Toggle**
   - Add config flag to enable LocalFolderStorage
   - Update SessionStore to optionally persist images
   - Maintain backward compatibility

2. **Google Photos Integration**
   - Implement GooglePhotosStorage class
   - Handle OAuth2 flow
   - Sync photos to/from Google Photos
   - Display cloud sync status

3. **Export Improvements**
   - Include derived photo relationships in Excel export
   - Add "Source Photo" column for annotated photos
   - Option to export with/without annotations

4. **UI Enhancements**
   - Visual lineage view (show original → derived chain)
   - Batch operations on photos
   - Search/filter by variant type
