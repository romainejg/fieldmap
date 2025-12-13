# Fieldmap App Features Overview

## Application Structure

```
┌─────────────────────────────────────────────┐
│  📸 Fieldmap - Cadaver Lab                  │
│  Photo Annotation & Documentation System    │
│                                             │
│  ┌─────────────┐                            │
│  │ ☰ Sidebar  │  🗂️ Session Management     │
│  │            │                             │
│  │ Create New │  ➕ Create New Session      │
│  │ Session    │     [Session Name Input]    │
│  │            │     [Create Button]         │
│  │ Current    │                             │
│  │ Session:   │  Current Session:           │
│  │ [Dropdown] │  Default ▼                  │
│  │            │                             │
│  │ Photos: 0  │  Photos in Session: 0       │
│  │ Total: 0   │  Total Photos: 0            │
│  │            │                             │
│  │ 📊 Export  │  [Export to Excel]          │
│  └────────────┘  [Download Excel File]      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Main Content Area                          │
│                                             │
│  ┌─────────────┬─────────────┐             │
│  │ 📷 Camera   │ 🖼️ Gallery  │             │
│  └─────────────┴─────────────┘             │
│                                             │
│  CAMERA TAB:                                │
│  ┌─────────────────────────────────────┐   │
│  │ 📍 Active Session: Default          │   │
│  ├─────────────────────────────────────┤   │
│  │ [Take a photo]                      │   │
│  │  📷 Click to activate camera        │   │
│  ├─────────────────────────────────────┤   │
│  │ Or Upload from Device               │   │
│  │  [Choose an image] 📁               │   │
│  ├─────────────────────────────────────┤   │
│  │ Preview:                            │   │
│  │  [Photo Preview Area]               │   │
│  ├─────────────────────────────────────┤   │
│  │ Add a comment (optional):           │   │
│  │  [Text Area]                        │   │
│  ├─────────────────────────────────────┤   │
│  │ Add to session:                     │   │
│  │  [Session Dropdown ▼]               │   │
│  ├─────────────────────────────────────┤   │
│  │  [💾 Save Photo]                    │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  GALLERY TAB:                               │
│  ┌─────────────────────────────────────┐   │
│  │ View Session: [All Sessions ▼]      │   │
│  ├─────────────────────────────────────┤   │
│  │ 3 photo(s) found                    │   │
│  ├─────────────────────────────────────┤   │
│  │ ┌─────────────────────────────────┐ │   │
│  │ │ Session Badge: Default          │ │   │
│  │ │ Photo ID: 1 | Time: 2024-...    │ │   │
│  │ ├─────────────┬───────────────────┤ │   │
│  │ │             │ Comment:          │ │   │
│  │ │   [Photo]   │ Test photo        │ │   │
│  │ │             │                   │ │   │
│  │ │             │ Annotations:      │ │   │
│  │ │             │ • Note 1 (time)   │ │   │
│  │ ├─────────────┴───────────────────┤ │   │
│  │ │ ⚙️ Actions for Photo 1          │ │   │
│  │ │  [Edit Comment]                 │ │   │
│  │ │  [Update Comment]               │ │   │
│  │ │  [Add Annotation]               │ │   │
│  │ │  Move to: [Session ▼]           │ │   │
│  │ │  [📦 Move] [🗑️ Delete]          │ │   │
│  │ └─────────────────────────────────┘ │   │
│  │                                     │   │
│  │ [Additional photos...]              │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Key Features

### 1. Session Management
- **Create Sessions**: Organize photos by experiment, procedure, or date
- **Switch Sessions**: Easily change active session
- **Statistics**: View photo counts per session

### 2. Photo Capture
- **Mobile Camera**: Direct integration with device camera
- **File Upload**: Alternative upload from device storage
- **Auto-Save**: Photos save automatically to current session
- **Immediate Annotation**: Add notes or draw right after capture

### 3. Photo Organization
- **Gallery View**: Browse all photos or filter by session
- **Quick Move**: Easily reorganize photos between sessions with dedicated controls
- **Click for Details**: View full details and manage each photo
- **Delete Photos**: Remove unwanted images

### 4. Annotations
- **Comments**: Add descriptive text to each photo
- **Multiple Annotations**: Add timestamped notes
- **Edit Anytime**: Update comments as needed

### 5. Data Export
- **Excel Format**: Export all data to Excel
- **Complete Information**: Includes all metadata
- **Timestamped Files**: Unique filenames for each export

## Mobile Optimization

### Touch-Friendly Interface
- Large buttons for easy tapping
- Responsive layout for different screen sizes
- Collapsed sidebar to maximize viewing area

### Camera Integration
- Uses device's native camera
- Instant preview of captured photos
- Direct save to selected session

### Data Management
- Session-based organization
- Easy photo management
- Quick export functionality

## Workflow Example

1. **Start Session**
   ```
   Open App → Create Session "Procedure_123" → Set as Active
   ```

2. **Capture Photos**
   ```
   Camera Tab → Take Photo → Auto-saved! → Add Comment/Draw → Organize
   ```

3. **Annotate**
   ```
   Gallery Tab → Select Photo → Add Annotations → Update
   ```

4. **Export**
   ```
   Sidebar → Export to Excel → Download File
   ```

## Data Structure

Each photo contains:
- Unique ID
- Image data
- Timestamp (creation time)
- Comment (description)
- Annotations (list with timestamps)
- Session (organizational category)

## Excel Export Format

| Session | Photo ID | Timestamp | Comment | Annotations | Annotation Count |
|---------|----------|-----------|---------|-------------|------------------|
| Default | 1 | 2024-... | Test | Note 1 (time) | 1 |
| Proc_A  | 2 | 2024-... | Sample | Note 2; Note 3 | 2 |

## Technical Details

- **Framework**: Streamlit (mobile-optimized)
- **Image Format**: PNG/JPEG support
- **Max Upload**: 200MB per image
- **Storage**: Browser session (temporary)
- **Export**: Excel (.xlsx) format

## Security Features

- XSRF protection enabled
- Secure dependencies (no known vulnerabilities)
- File size limits enforced
- Input validation on all forms

---

**Note**: Remember to export data regularly as session data is temporary!
